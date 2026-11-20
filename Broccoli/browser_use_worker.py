import asyncio
import json
import os
import sys
import traceback


RESULT_PREFIX = '__BROCCOLI_BROWSER_USE_RESULT__'
PROGRESS_PREFIX = '__BROCCOLI_BROWSER_USE_PROGRESS__'

DEFAULT_LLM_TIMEOUT = 120
DEFAULT_STEP_TIMEOUT = 180
DEFAULT_MAX_FAILURES = 3
DEFAULT_OVERALL_TIMEOUT = 1800

EXTRACTED_TAIL_ITEMS = 12
EXTRACTED_ITEM_CHARS = 1600

# 官方 Fast Agent 模板的提速提示词（flash 档随 flash_mode 一起注入）。
SPEED_PROMPT = (
    'Speed optimization instructions:\n'
    '- Be extremely concise and direct in your responses\n'
    '- Get to the goal as quickly as possible\n'
    '- Use multi-action sequences whenever possible to reduce steps'
)


# This worker is written for the 0.13 library. 1.0 is a different program (the model writes Python
# instead of choosing page actions; 24 of the 36 calls made here do not exist there — checked
# 2026-11-18), so on any other series the task stops at once with a sentence that says why, instead
# of failing somewhere in the middle. Raise this only together with the code below.
SUPPORTED_LIBRARY_SERIES = '0.13.'


def _library_version():
    try:
        from importlib.metadata import version
        return str(version('browser-use') or '')
    except Exception:
        return ''   # not known (no package record): do not guess, let the import decide


def _library_problem(found):
    """'' when the installed library is the supported series (or its version is not known)."""
    found = str(found or '').strip()
    if not found or found.startswith(SUPPORTED_LIBRARY_SERIES):
        return ''
    return (f'Browser Use library {found} is installed, but Broccoli works with {SUPPORTED_LIBRARY_SERIES}x only '
            f'(last one: 0.13.14). Put it back with: pip install "browser-use==0.13.14"')


def _speed_mode(cfg):
    mode = str(cfg.get('speed_mode') or 'standard').strip().lower()
    return mode if mode in ('standard', 'no_thinking', 'flash') else 'standard'


def _history_items(cfg):
    try:
        number = int(cfg.get('max_history_items') or 0)
    except (TypeError, ValueError):
        return 0
    # 库断言 max_history_items 必须 >5；0/负数=不限。
    return number if number >= 6 else 0


def _first_balanced_json(text):
    """从文本中截取第一个括号配平的完整 JSON 对象；找不到返回 None。"""
    text = str(text or '')
    start = text.find('{')
    if start < 0:
        return None
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        ch = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    return None


def _install_tolerant_output_parsing():
    """给 AgentOutput 解析加兜底：正常解析失败时剪掉首尾多余字符重试。

    真机实锤（2026-08-24）：中转返回的内容是"一个完整 JSON 对象 + 拖尾字符"，
    pydantic 报 trailing characters，步骤连续失败三次即被库强制 done，
    表现为"打开页面看一眼就宣布干不了"。先按原样解析保持零行为变化，
    失败才走修剪重试。"""
    try:
        from browser_use.agent.views import AgentOutput
        original = AgentOutput.model_validate_json.__func__

        @classmethod
        def tolerant(cls, json_data, **kwargs):
            try:
                return original(cls, json_data, **kwargs)
            except Exception:
                text = json_data.decode('utf-8', 'ignore') if isinstance(json_data, (bytes, bytearray)) else str(json_data)
                trimmed = _first_balanced_json(text)
                if trimmed and trimmed != text:
                    return original(cls, trimmed, **kwargs)
                raise

        AgentOutput.model_validate_json = tolerant
    except Exception:
        pass


def _apply_search_engine(engine):
    """把库内置 search 动作的默认引擎改成用户设置的值。

    库的 SearchAction 把 engine 默认写死为 duckduckgo，参数描述还教模型
    "默认用 duckduckgo"；模型不填该参数时选引擎的是这个默认值而不是模型。
    在创建 Agent 之前改掉字段默认值和描述，模型看到的工具说明书随之更新。
    """
    engine = str(engine or '').strip().lower()
    if engine not in ('google', 'bing', 'duckduckgo'):
        return
    try:
        from browser_use.tools.views import SearchAction
        field = SearchAction.model_fields.get('engine')
        if field is None:
            return
        field.default = engine
        field.description = (
            f'Options: duckduckgo, google, bing. Always use {engine} '
            'unless the task explicitly names a different engine.'
        )

        # 硬矫正：模型显式写别的引擎（如照抄日记里的 duckduckgo）也在解析时
        # 强制改回设置值。post-init 钩子需同时登记 __pydantic_post_init__ 并
        # 重建核心校验器才会被 pydantic v2 调用。
        def _pin_engine(self, _context=None, _engine=engine):
            if str(getattr(self, 'engine', '') or '').strip().lower() != _engine:
                object.__setattr__(self, 'engine', _engine)

        SearchAction.model_post_init = _pin_engine
        SearchAction.__pydantic_post_init__ = 'model_post_init'
        SearchAction.model_rebuild(force=True)
    except Exception:
        pass


def _vision_value(mode):
    mode = str(mode or 'auto').lower()
    if mode == 'on':
        return True
    if mode == 'off':
        return False
    return 'auto'


def _cancel_requested(cfg):
    cancel_path = str(cfg.get('cancel_path') or '').strip()
    return bool(cancel_path and os.path.exists(cancel_path))


# Add note while the task runs (2026-11-07): Broccoli writes every note of the run into
# cfg['live_notes_path']; the ones in cfg['live_notes_skip'] were already in the task.
LIVE_NOTE_LEAD = ('The user added this instruction while you were working. Apply it from now on; '
                  'where it conflicts with the task or earlier instructions, it wins: ')


def _read_live_notes(cfg):
    path = str(cfg.get('live_notes_path') or '').strip()
    if not path:
        return []
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
    except Exception:
        return []
    notes = []
    for item in data if isinstance(data, list) else []:
        if isinstance(item, dict) and str(item.get('id') or '').strip() and str(item.get('text') or '').strip():
            notes.append({'id': str(item['id']).strip(), 'text': str(item['text']).strip()})
    return notes


def _apply_live_notes(cfg, agent_obj, applied):
    """New notes → the agent's task as follow-up user requests (the library's own mechanism; the
    task text goes into every step's prompt). Returns the notes it applied."""
    fresh = [item for item in _read_live_notes(cfg) if item['id'] not in applied]
    used = []
    for item in fresh:
        try:
            agent_obj._message_manager.add_new_task(LIVE_NOTE_LEAD + item['text'])
        except Exception:
            continue   # not applied: Broccoli hands it to a follow-up turn instead
        applied.add(item['id'])
        used.append(item)
    return used


# ── Background mode (2026-11-19): the Chrome window waits in the screen's corner ─────────────
# Broccoli writes the wanted mode into cfg['window_mode_path']:
#   {"background": true, "park": [x, y], "home": [left, top]}
# "park" is the last point of the screen (bottom right). Chrome keeps a 1-point sliver of the
# window there, which is as far off the screen as macOS lets a window go (measured: asking for
# -32000 leaves 261 points showing; hiding the app makes pages think they are hidden). Parked
# windows keep drawing, so pages behave as if they were in view. Nothing about the browser
# itself is changed.
NEEDS_USER_MARK = 'NEEDS_USER:'
NEEDS_USER_RULE = (
    'If you cannot continue without the human user (a sign-in, a captcha or verification code, '
    'a file picker, a site permission prompt, a payment confirmation), do not guess and do not '
    'keep retrying: use the done action with success=false and start its text with '
    '"' + NEEDS_USER_MARK + '" followed by one sentence saying exactly what the user must do in the browser.'
)
WINDOW_PARK_SLACK = 2
WINDOW_CASCADE = 24


def _read_window_mode(cfg):
    path = str(cfg.get('window_mode_path') or '').strip()
    if not path:
        return None
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
        park = [int(data['park'][0]), int(data['park'][1])]
        home = [int(data['home'][0]), int(data['home'][1])]
    except Exception:
        return None
    return {'background': bool(data.get('background')), 'park': park, 'home': home}


def _window_homes_path(cfg):
    return str(cfg.get('window_mode_path') or '').strip() + '.homes'


def _load_window_homes(cfg):
    try:
        with open(_window_homes_path(cfg), 'r', encoding='utf-8') as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_window_homes(cfg, homes):
    try:
        path = _window_homes_path(cfg)
        with open(path + '.tmp', 'w', encoding='utf-8') as handle:
            json.dump(homes, handle)
        os.replace(path + '.tmp', path)
    except Exception:
        pass


def _needs_user_text(text):
    """The sentence after the NEEDS_USER: mark, '' when the text does not carry it."""
    text = str(text or '')
    at = text.find(NEEDS_USER_MARK)
    if at < 0:
        return ''
    rest = text[at + len(NEEDS_USER_MARK):].strip()
    first = rest.splitlines()[0].strip() if rest else ''
    return first or 'The browser needs you.'


async def _apply_window_mode(send, cfg, state, key):
    """Put every Chrome window where the mode says. `send` is a CDP client's .send; `key` tells
    one Chrome from another in the remembered positions. Returns how many windows moved."""
    targets = (await send.Target.getTargets()).get('targetInfos') or []
    windows = {}
    for target in targets:
        if target.get('type') != 'page':
            continue
        try:
            found = await send.Browser.getWindowForTarget(params={'targetId': target['targetId']})
            windows[int(found['windowId'])] = dict(found.get('bounds') or {})
        except Exception:
            continue
    park_x, park_y = state['park']
    homes = None
    moved = 0
    for window_id, bounds in sorted(windows.items()):
        if str(bounds.get('windowState') or 'normal') != 'normal':
            continue   # minimised / full screen: the user put it there
        parked = int(bounds.get('left', 0)) >= park_x - WINDOW_PARK_SLACK
        name = f'{key}:{window_id}'
        if state['background'] and not parked:
            if homes is None:
                homes = _load_window_homes(cfg)
            homes.setdefault(name, [int(bounds.get("left", 0)), int(bounds.get("top", 0))])
            target_bounds = {'left': park_x, 'top': park_y}
        elif not state['background'] and parked:
            if homes is None:
                homes = _load_window_homes(cfg)
            home = homes.pop(name, None)
            if not (isinstance(home, list) and len(home) == 2):
                home = [state['home'][0] + WINDOW_CASCADE * moved, state['home'][1] + WINDOW_CASCADE * moved]
            target_bounds = {'left': int(home[0]), 'top': int(home[1])}
        else:
            continue
        try:
            await send.Browser.setWindowBounds(params={'windowId': window_id, 'bounds': target_bounds})
            moved += 1
        except Exception:
            continue
    if homes is not None:
        _save_window_homes(cfg, homes)
    return moved


async def _window_command(cfg):
    """Broccoli's own call (no task): move the windows of the Chrome at cfg['cdp_url']."""
    import urllib.request
    from cdp_use import CDPClient
    state = _read_window_mode(cfg)
    if state is None:
        return {'ok': False, 'error': 'no window mode'}
    base = str(cfg.get('cdp_url') or '').strip().rstrip('/')
    with urllib.request.urlopen(base + '/json/version', timeout=3) as response:
        socket_url = json.load(response)['webSocketDebuggerUrl']
    client = CDPClient(socket_url)
    await client.start()
    try:
        moved = await asyncio.wait_for(_apply_window_mode(client.send, cfg, state, _window_key(base)), timeout=8)
    finally:
        await client.stop()
    return {'ok': True, 'moved': moved}


def _window_key(cdp_url):
    """The port of a CDP address: one running Chrome = one port."""
    text = str(cdp_url or '')
    digits = ''
    for part in text.replace('/', ':').split(':'):
        if part.isdigit():
            digits = part
    return digits or 'chrome'


# ── A window of its own in a shared Chrome (2026-11-19) ──────────────────────────────────────
# Browser steps work in ONE Chrome (one sign-in). The rule (Ryan, 2026-11-19: "并行任务在同一个实例的
# 多个窗口里…一个任务里后面多加了要求你多建页面。新的对话有了你就锁定一个没有 agent 占用的窗口，0 窗口你
# 就建一个窗口"):
#   · one task = one window. A task that starts locks an agent window nobody is using and opens a
#     new tab in it; when there is none, it makes a new window. The lock holds until the task ends;
#     the window then stays, free for the next task.
#   · more pages inside one task = more tabs in ITS window.
#   · the task works only in its own window: it sees only its own tabs, and whenever it is found
#     somewhere else (the library picks a tab by itself after a restart or when a tab closes) it is
#     brought back before the next step.
# The table of agent windows is the file <window_mode_path>.agent:
#   {chrome port: {"windows": {window id: [pids of the task using it]}}}
# Chrome puts a new tab into the window that was active last, so "new tab in window W" is: make W
# the active one, create the tab, check where it landed — all while holding the table's lock, so
# two tasks cannot interleave. A tab that still landed elsewhere is closed again.
# Empty tabs are not left lying around: the library animates every about:blank tab it finds when a
# task starts, and with about ten of them its start-up never finishes (measured on 0.13.14: 6 are
# fine, 10 hang; 25 real pages are fine). So a task that locks a free window uses an empty tab that
# is already there instead of opening another, and spare empty tabs in free windows are closed.
WINDOW_TABLE_WAIT_SECONDS = 20.0


def _pid_alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except Exception:
        return False


class _WindowTable:
    """`async with _WindowTable(cfg) as table:` — the table of agent windows, locked for this task
    until the block ends (other tasks wait). `table.data` is saved when the block ends."""

    def __init__(self, cfg):
        self.path = str(cfg.get('window_mode_path') or '').strip() + '.agent'
        self.handle = None
        self.data = {}

    async def __aenter__(self):
        import fcntl
        self.handle = open(self.path, 'a+', encoding='utf-8')
        waited = 0.0
        while True:
            try:
                fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if waited >= WINDOW_TABLE_WAIT_SECONDS:
                    self.handle.close()
                    self.handle = None
                    raise
                await asyncio.sleep(0.05)
                waited += 0.05
        self.handle.seek(0)
        try:
            data = json.loads(self.handle.read() or '{}')
        except Exception:
            data = {}
        self.data = data if isinstance(data, dict) else {}
        return self

    def windows(self, key):
        """{window id: [pids]} of one Chrome, as stored (anything else in the file counts as none)."""
        entry = self.data.get(key)
        stored = entry.get('windows') if isinstance(entry, dict) else None
        result = {}
        for window_id, users in (stored.items() if isinstance(stored, dict) else []):
            try:
                result[int(window_id)] = [int(pid) for pid in (users or [])]
            except Exception:
                continue
        return result

    def set_windows(self, key, windows):
        self.data[key] = {'windows': {str(window_id): list(users) for window_id, users in windows.items()}}

    async def __aexit__(self, *_exc):
        if self.handle is None:
            return False
        try:
            self.handle.seek(0)
            self.handle.truncate()
            json.dump(self.data, self.handle)
            self.handle.flush()
        finally:
            self.handle.close()   # closing releases the lock
            self.handle = None
        return False


async def _windows_of(send):
    """{window id: [page target ids]} of that Chrome."""
    windows = {}
    for target in (await send.Target.getTargets()).get('targetInfos') or []:
        if target.get('type') != 'page':
            continue
        try:
            found = await send.Browser.getWindowForTarget(params={'targetId': target['targetId']})
            windows.setdefault(int(found['windowId']), []).append(target['targetId'])
        except Exception:
            continue
    return windows


async def _blank_tabs(send):
    """The page targets that are still an empty about:blank."""
    return {target['targetId'] for target in (await send.Target.getTargets()).get('targetInfos') or []
            if target.get('type') == 'page' and str(target.get('url') or '') in ('', 'about:blank')}


async def _window_of_target(send, target_id):
    try:
        found = await send.Browser.getWindowForTarget(params={'targetId': target_id})
        return int(found['windowId'])
    except Exception:
        return 0


async def _tab_in_window(send, create, window_id, window_targets, url='about:blank'):
    """A new tab in exactly that window; '' when Chrome put it somewhere else (then it is closed
    again). Call only while holding the table's lock."""
    try:
        await send.Target.activateTarget(params={'targetId': window_targets[-1]})
        target = await create(url)
    except Exception:
        return ''
    if await _window_of_target(send, target) == int(window_id):
        return target
    try:
        await send.Target.closeTarget(params={'targetId': target})
    except Exception:
        pass
    return ''


async def _open_own_window(browser, cfg):
    """Start the session and give this task its window in the shared Chrome. Returns the task's
    place {'key', 'windows': {ids}, 'tabs': [target ids, newest last], 'create': the library's own
    tab maker}, or None when it could not be done — the task then runs the ordinary way."""
    try:
        from browser_use.browser.events import SwitchTabEvent
        await browser.start()
        send = browser._cdp_client_root.send
        create = browser._cdp_create_new_page
        key = _window_key(getattr(browser, 'cdp_url', '') or cfg.get('cdp_url'))
        me = os.getpid()
        async with _WindowTable(cfg) as table:
            windows = await _windows_of(send)
            known = {}
            for window_id, users in table.windows(key).items():
                if window_id in windows:      # a window the user closed is forgotten
                    known[window_id] = [pid for pid in users if pid != me and _pid_alive(pid)]
            target, window_id = '', 0
            blank = await _blank_tabs(send)
            free_windows = sorted(window_id for window_id, users in known.items() if not users)
            for free in free_windows[:2]:
                empty = [tab for tab in windows[free] if tab in blank]
                target = empty[-1] if empty else await _tab_in_window(send, create, free, windows[free])
                if target:
                    window_id = free
                    break
            for free in free_windows:         # spare empty tabs in free windows go (never a window's last tab)
                spare = [tab for tab in windows[free] if tab in blank and tab != target]
                if len(spare) == len(windows[free]):
                    spare = spare[1:]
                for tab in spare:
                    try:
                        await send.Target.closeTarget(params={'targetId': tab})
                    except Exception:
                        pass
            if not target:                    # no agent window is free: this task gets a new one
                target = await create('about:blank', new_window=True)
                window_id = await _window_of_target(send, target)
            if not window_id:
                return None
            known[window_id] = [me]
            table.set_windows(key, known)
        await browser.event_bus.dispatch(SwitchTabEvent(target_id=target))
        own = {'key': key, 'windows': {window_id}, 'tabs': [target], 'create': create}
        _keep_task_in_own_window(browser, cfg, own)
        return own
    except Exception:
        return None


def _keep_task_in_own_window(browser, cfg, own):
    """From now on, on this session: a tab the task opens is made in its own window, and the tab
    list it is shown holds only its own tabs. (Set on this one object; the library is not changed.)"""
    create = own['create']
    list_tabs = browser.get_tabs
    me = os.getpid()

    async def create_in_own_window(url='about:blank', background=False, new_window=False):
        send = browser._cdp_client_root.send
        async with _WindowTable(cfg) as table:
            target = ''
            if not new_window:
                windows = await _windows_of(send)
                for window_id in sorted(own['windows']):
                    if windows.get(window_id):
                        target = await _tab_in_window(send, lambda page_url: create(page_url, background=background),
                                                      window_id, windows[window_id], url)
                        if target:
                            break
            if not target:        # asked for a window, or its window is gone: one more window of its own
                target = await create(url, background=background, new_window=True)
                window_id = await _window_of_target(send, target)
                if window_id:
                    own['windows'].add(window_id)
                    known = table.windows(own['key'])
                    known[window_id] = [me]
                    table.set_windows(own['key'], known)
        own['tabs'].append(target)
        return target

    async def own_tabs():
        tabs = await list_tabs()
        try:
            send = browser._cdp_client_root.send
            mine = [tab for tab in tabs if await _window_of_target(send, tab.target_id) in own['windows']]
        except Exception:
            return tabs
        return mine or tabs

    object.__setattr__(browser, '_cdp_create_new_page', create_in_own_window)
    object.__setattr__(browser, 'get_tabs', own_tabs)


async def _return_to_own_window(browser, own):
    """Before a step: when the session is looking at a tab outside the task's window, switch back to
    the task's newest tab (a new one in its window when none is left). True when it had to."""
    from browser_use.browser.events import SwitchTabEvent
    if getattr(browser, '_cdp_client_root', None) is None:
        await browser.start()     # the library let go of the session (it does when a run ends)
    send = browser._cdp_client_root.send
    focus = str(getattr(browser, 'agent_focus_target_id', '') or '')
    if focus and await _window_of_target(send, focus) in own['windows']:
        return False
    windows = await _windows_of(send)
    alive = {target for window_id in own['windows'] for target in windows.get(window_id, [])}
    target = next((tab for tab in reversed(own['tabs']) if tab in alive), '') or next(iter(sorted(alive)), '')
    if not target:
        target = await browser._cdp_create_new_page('about:blank')
    await browser.event_bus.dispatch(SwitchTabEvent(target_id=target))
    return True


async def _leave_own_window(cfg):
    """The task is over: its window is free for the next task (the window and its tabs stay)."""
    me = os.getpid()
    try:
        async with _WindowTable(cfg) as table:
            for key in list(table.data):
                table.set_windows(key, {window_id: [pid for pid in users if pid != me]
                                        for window_id, users in table.windows(key).items()})
    except Exception:
        pass


async def _window_mode_loop(cfg, browser):
    """While a task runs: follow the mode file. A new window lands in the middle of the screen,
    and the menu-bar switch must work mid-task, so this looks once a second."""
    last_background = None
    while True:
        try:
            state = _read_window_mode(cfg)
            client = getattr(browser, '_cdp_client_root', None)
            if state is not None and client is not None:
                # in the foreground nothing needs watching once the windows are back
                if state['background'] or last_background is not False:
                    key = _window_key(getattr(browser, 'cdp_url', '') or cfg.get('cdp_url'))
                    await asyncio.wait_for(_apply_window_mode(client.send, cfg, state, key), timeout=8)
                    last_background = state['background']
        except asyncio.CancelledError:
            raise
        except Exception:
            pass
        await asyncio.sleep(1.0)


# ── When the model turns a request down, ask differently instead of failing (2026-11-19) ─────
# Seen with claude-opus-5-5 through the built-in proxy: every step came back "400 … schema: For
# 'integer' type, property 'minimum' is not supported" (it does not accept the forced answer
# format), and once that was out of the way, "claude refusal (reasoning_extraction)" (the
# standard speed asks the model to write out its thinking, which it does not hand over). Three
# such errors and the library ends the task on a blank page. Both are decided by what the model
# answers, not by its name:
#   · forced format turned down → the format goes into the prompt as text; the same step is
#     sent again at once and is not counted as a failure;
#   · thinking turned down → the task starts over without asking for thinking (the "no
#     thinking" speed that Settings already offers). Nothing is done to get the thinking anyway.
FORMAT_TURNED_DOWN_WORDS = ('schema', 'grammar', 'response_format', 'output_config', 'json_schema')


def _format_turned_down(error_text):
    low = str(error_text or '').lower()
    return '400' in low and any(word in low for word in FORMAT_TURNED_DOWN_WORDS)


def _thinking_turned_down(error_text):
    low = str(error_text or '').lower()
    return 'reasoning_extraction' in low or ('refusal' in low and 'reasoning' in low)


def _install_model_fallbacks(llm, state):
    """Wrap llm.ainvoke. `state`: format_as_text / thinking_refused (set here), step (set by the caller)."""
    original = llm.ainvoke

    async def ainvoke(messages, output_format=None, **kwargs):
        try:
            return await original(messages, output_format=output_format, **kwargs)
        except Exception as exc:
            text = str(exc)
            if (output_format is not None and not state.get('format_as_text') and _format_turned_down(text)
                    and hasattr(llm, 'dont_force_structured_output')):
                llm.dont_force_structured_output = True
                llm.add_schema_to_system_prompt = True
                state['format_as_text'] = True
                _emit_progress({'step': int(state.get('step') or 0), 'url': '',
                                'actions': ['the model did not accept the forced answer format; sending it as text']})
                try:
                    return await original(messages, output_format=output_format, **kwargs)
                except Exception as again:
                    if _thinking_turned_down(str(again)):
                        state['thinking_refused'] = True
                    raise
            if _thinking_turned_down(text):
                state['thinking_refused'] = True
            raise

    try:
        llm.ainvoke = ainvoke
    except Exception:
        pass   # a model class that cannot be wrapped keeps the old behaviour


def _positive_int(value, fallback):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return fallback
    return number if number > 0 else fallback


def _emit_progress(payload):
    try:
        print(PROGRESS_PREFIX + json.dumps(payload, ensure_ascii=False), flush=True)
    except Exception:
        pass


def _one_line(value, limit):
    text = ' '.join(str(value or '').split())
    return text if len(text) <= limit else text[:max(0, limit - 1)].rstrip() + '…'


def _describe_element(browser_state_summary, index):
    """Human-readable target of an indexed action: tag + the element's visible text
    (falls back to aria-label / placeholder / title / name / href)."""
    node = None
    try:
        node = browser_state_summary.dom_state.selector_map.get(int(index))
    except Exception:
        node = None
    if node is None:
        return f'[{index}]'
    tag = ''
    try:
        tag = str(node.tag_name or node.node_name or '').lower()
    except Exception:
        tag = ''
    text = ''
    for getter in ('get_meaningful_text_for_llm', 'get_all_children_text'):
        try:
            text = str(getattr(node, getter)() or '').strip()
        except Exception:
            text = ''
        if text:
            break
    if not text:
        attrs = getattr(node, 'attributes', None) or {}
        for key in ('aria-label', 'placeholder', 'title', 'name', 'alt', 'value', 'href'):
            if str(attrs.get(key, '') or '').strip():
                text = str(attrs.get(key))
                break
    text = _one_line(text, 50)
    label = f'<{tag}>' if tag else f'[{index}]'
    return f'{label} “{text}”' if text else label


def _describe_actions(agent_output, browser_state_summary):
    """One short line per action: name + element target + typed/searched text."""
    details = []
    for action in (getattr(agent_output, 'action', None) or []):
        try:
            dumped = action.model_dump(exclude_none=True) if hasattr(action, 'model_dump') else None
        except Exception:
            dumped = None
        if not isinstance(dumped, dict) or not dumped:
            continue
        name, params = next(iter(dumped.items()))
        params = params if isinstance(params, dict) else {}
        bits = [str(name)]
        if params.get('index') is not None:
            bits.append(_describe_element(browser_state_summary, params.get('index')))
        for key in ('text', 'query', 'url', 'keys', 'value'):
            if str(params.get(key, '') or '').strip():
                bits.append(f'“{_one_line(params.get(key), 60)}”')
                break
        if str(name) == 'scroll' and 'down' in params:
            bits.append('down' if params.get('down') else 'up')
        details.append(' '.join(bits))
    return details[:5]


def _emit_result(payload):
    print(RESULT_PREFIX + json.dumps(payload, ensure_ascii=False), flush=True)


def _emit_cancelled():
    _emit_result({
        'ok': True,
        'cancelled': True,
        'answer': 'Browser Use task was stopped.',
        'metadata': {},
    })


async def _close_browser(browser):
    if browser is None:
        return
    for method_name in ('stop', 'close'):
        method = getattr(browser, method_name, None)
        if method is None:
            continue
        try:
            result = method()
            if hasattr(result, '__await__'):
                await result
            return
        except Exception:
            continue


def _collect_history(history_obj):
    """Read whatever the (possibly partial) agent history offers, defensively."""
    collected = {'final_result': '', 'urls': [], 'action_names': [], 'errors': [], 'extracted': []}
    if history_obj is None:
        return collected
    method = getattr(history_obj, 'final_result', None)
    if callable(method):
        try:
            collected['final_result'] = str(method() or '').strip()
        except Exception:
            pass
    for attr_name, key in (
        ('urls', 'urls'),
        ('action_names', 'action_names'),
        ('errors', 'errors'),
        ('extracted_content', 'extracted'),
    ):
        method = getattr(history_obj, attr_name, None)
        if not callable(method):
            continue
        try:
            values = method() or []
        except Exception:
            continue
        if isinstance(values, (list, tuple)):
            collected[key].extend(str(item) for item in values if item is not None and str(item).strip())
    return collected


def _compose_answer(collected, note=''):
    final_result = collected.get('final_result', '')
    extracted = list(collected.get('extracted') or [])
    # done 动作的最终文本常同时出现在 extracted 里，避免整段重复。
    if final_result and extracted and extracted[-1].strip() == final_result:
        extracted = extracted[:-1]
    parts = []
    if note:
        parts.append(note)
    if final_result:
        parts.append(final_result)
    if extracted:
        tail = extracted[-EXTRACTED_TAIL_ITEMS:]
        clipped = [
            item[:EXTRACTED_ITEM_CHARS] + ('\n[...truncated]' if len(item) > EXTRACTED_ITEM_CHARS else '')
            for item in tail
        ]
        parts.append('Extracted page content (most recent steps first kept last):\n' + '\n---\n'.join(clipped))
    urls = collected.get('urls') or []
    if urls:
        parts.append('Visited URLs:\n' + '\n'.join(f'- {url}' for url in urls[-10:]))
    action_names = collected.get('action_names') or []
    if action_names:
        parts.append('Actions:\n' + ', '.join(action_names[-20:]))
    errors = collected.get('errors') or []
    if errors:
        parts.append('Errors:\n' + '\n'.join(f'- {err}' for err in errors[-5:]))
    return '\n\n'.join(part for part in parts if str(part).strip()).strip()


def _result_metadata(cfg, collected, partial=False, error_text=''):
    metadata = {
        'urls': collected.get('urls') or [],
        'action_names': collected.get('action_names') or [],
        'errors': collected.get('errors') or [],
        'model': str(cfg.get('model') or ''),
        'max_steps': _positive_int(cfg.get('max_steps'), 30),
    }
    if partial:
        metadata['partial'] = True
    if error_text:
        metadata['error'] = error_text
    if cfg.get('_needs_user'):
        metadata['needs_user'] = str(cfg['_needs_user'])
    return metadata


async def main():
    cfg = json.load(sys.stdin)
    if cfg.get('window_command'):
        try:
            _emit_result(await _window_command(cfg))
        except Exception as exc:
            _emit_result({'ok': False, 'error': str(exc) or exc.__class__.__name__})
        return
    problem = _library_problem(_library_version())
    if problem:
        raise RuntimeError(problem)
    try:
        import browser_use.browser.profile as browser_profile
        browser_profile.get_display_size = lambda: browser_profile.ViewportSize(width=1440, height=900)
        from browser_use import Agent, Browser, ChatAnthropic, ChatGoogle, ChatOpenAI
    except Exception as exc:
        raise RuntimeError('Browser Use is not installed or cannot be imported: ' + str(exc)) from exc

    llm_wrapper = str(cfg.get('llm_wrapper') or 'openai').strip().lower()
    model = str(cfg.get('model') or '').strip()
    api_key = str(cfg.get('api_key') or '').strip()
    endpoint = str(cfg.get('endpoint') or '').strip()
    llm_timeout = _positive_int(cfg.get('llm_timeout'), DEFAULT_LLM_TIMEOUT)
    step_timeout = max(_positive_int(cfg.get('step_timeout'), DEFAULT_STEP_TIMEOUT), llm_timeout + 30)
    max_failures = _positive_int(cfg.get('max_failures'), DEFAULT_MAX_FAILURES)
    overall_timeout = _positive_int(cfg.get('overall_timeout'), DEFAULT_OVERALL_TIMEOUT)
    # HTTP 层超时与库的 llm_timeout 对齐；SDK 自身不再重试（重试交给库的
    # 每步失败机制——那会带着新的页面快照重发，比盲重发同一请求有用）。
    if llm_wrapper == 'anthropic':
        kwargs = {
            'model': model,
            'api_key': api_key,
            'timeout': llm_timeout,
            'max_tokens': 8192,
            'temperature': None,
        }
        if endpoint:
            kwargs['base_url'] = endpoint
        llm = ChatAnthropic(**kwargs)
    elif llm_wrapper == 'google':
        llm = ChatGoogle(
            model=model,
            api_key=api_key,
            temperature=None,
            max_output_tokens=8096,
        )
    else:
        openai_kwargs = {
            'model': model,
            # openai 3 refuses an empty key; a server that needs none ignores this stand-in (2026-11-10)
            'api_key': api_key or 'no-key',
            'base_url': endpoint,
            'timeout': llm_timeout,
            'max_retries': 1,
            'temperature': None,
            'frequency_penalty': None,
        }
        # planner 分配、主进程按能力档案翻译好的思考档；库只对思考型
        # 模型注入该参数，非思考模型自动忽略。
        reasoning_effort = str(cfg.get('reasoning_effort') or '').strip()
        if reasoning_effort:
            openai_kwargs['reasoning_effort'] = reasoning_effort
        llm = ChatOpenAI(**openai_kwargs)
    model_state = {'format_as_text': False, 'thinking_refused': False, 'thinking_on': False, 'step': 0}
    _install_model_fallbacks(llm, model_state)
    speed_mode = _speed_mode(cfg)
    _apply_search_engine(cfg.get('search_engine'))
    _install_tolerant_output_parsing()
    browser_kwargs = {'headless': False}
    if speed_mode == 'flash':
        # 官方 Fast Agent 模板：抓取页面状态前的最短等待从 0.25s 压到 0.1s。
        browser_kwargs['minimum_wait_page_load_time'] = 0.1
    if str(cfg.get('chrome_mode') or '') == 'connect_existing':
        browser_kwargs['cdp_url'] = str(cfg.get('cdp_url') or '').strip()
    else:
        browser_kwargs['executable_path'] = str(cfg.get('chrome_executable') or '').strip()
        browser_kwargs['user_data_dir'] = str(cfg.get('user_data_dir') or '').strip()
        browser_kwargs['keep_alive'] = not bool(cfg.get('close_window_after_task', False))
        browser_kwargs['ignore_default_args'] = ['--extensions-on-chrome-urls']
    browser = None
    window_task = None
    own = None    # this task's window in the shared Chrome (see _open_own_window)
    try:
        if _cancel_requested(cfg):
            _emit_cancelled()
            return

        browser = Browser(**browser_kwargs)
        if cfg.get('own_window') and browser_kwargs.get('cdp_url'):
            own = await _open_own_window(browser, cfg)
        task = str(cfg.get('task') or '').strip()
        stop_instruction = (
            'When the requested objective is complete, when enough information has been gathered, '
            'or when you cannot make useful progress, immediately use the done action and return the final result. '
            'Do not keep exploring after the goal is satisfied. '
        )
        if cfg.get('open_new_window', True):
            task = (
                'Start this automation in a new browser tab or window. '
                'Do not reuse unrelated existing tabs unless the user explicitly asks for it. '
            ) + stop_instruction + task
        else:
            task = (
                'Use the currently active tab/page in the existing Browser Use Chrome window as the starting point. '
                'Do not open a new tab or navigate away unless the user explicitly asks for it. '
            ) + stop_instruction + task

        async def should_stop():
            # also stops a run whose every step would be turned down for asking for thinking
            return _cancel_requested(cfg) or (model_state['thinking_on'] and model_state['thinking_refused'])

        applied_notes = {str(item) for item in (cfg.get('live_notes_skip') or []) if str(item or '').strip()}

        async def on_step_begin(agent_obj):
            # 每步开始（模型调用之前）触发：把"启动浏览器"和"第 N 步思考中"
            # 在进度里分开——此前两者都挤在 Browser worker starting 一个标签下。
            step_number = 0
            try:
                step_number = int(getattr(agent_obj.state, 'n_steps', 0) or 0)
            except Exception:
                pass
            model_state['step'] = step_number
            if own is not None:
                try:
                    await _return_to_own_window(browser, own)
                except Exception:
                    pass
            used = _apply_live_notes(cfg, agent_obj, applied_notes)   # Add note: before this step's model call
            if used:
                _emit_progress({'step': step_number, 'notes_applied': used})
            _emit_progress({'step': step_number, 'actions': ['thinking…'], 'url': ''})

        def on_new_step(browser_state_summary, agent_output, step_number):
            actions = []
            try:
                for action in (getattr(agent_output, 'action', None) or []):
                    dumped = action.model_dump(exclude_none=True) if hasattr(action, 'model_dump') else None
                    if isinstance(dumped, dict) and dumped:
                        actions.append(str(next(iter(dumped.keys()))))
                        done = dumped.get('done')
                        needs = _needs_user_text(done.get('text')) if isinstance(done, dict) else ''
                        if needs:
                            _emit_progress({'step': int(step_number or 0), 'needs_user': needs})
            except Exception:
                pass
            url = ''
            try:
                url = str(getattr(browser_state_summary, 'url', '') or '')
            except Exception:
                pass
            # What the agent is doing and why, for the live step display: element targets,
            # typed/searched text, and the model's own goal / evaluation / thinking.
            try:
                details = _describe_actions(agent_output, browser_state_summary)
            except Exception:
                details = []
            brain = {}
            for key, limit in (('next_goal', 160), ('evaluation_previous_goal', 120), ('thinking', 200)):
                try:
                    brain[key] = _one_line(getattr(agent_output, key, '') or '', limit)
                except Exception:
                    brain[key] = ''
            _emit_progress({
                'step': int(step_number or 0), 'actions': actions[:5], 'url': url[:200],
                'details': details, 'next_goal': brain['next_goal'],
                'evaluation': brain['evaluation_previous_goal'], 'thinking': brain['thinking'],
            })

        # 速度模式（Settings > General > Browser Use）：no_thinking 去掉输出端
        # 思考字段；flash 换极简系统提示词并附加官方提速提示词（flash_mode
        # 在库内自动覆盖 use_thinking）。行动日记条数 0=不限。
        agent_kwargs = {}
        extend_bits = []
        if speed_mode == 'no_thinking':
            agent_kwargs['use_thinking'] = False
        elif speed_mode == 'flash':
            agent_kwargs['flash_mode'] = True
            extend_bits.append(SPEED_PROMPT)
        # 搜索政策进系统提示词（全档位）：默认值改造管不住"绕过搜索动作、
        # 直接导航去搜索站"的路径，这句话管。
        search_engine = str(cfg.get('search_engine') or '').strip().lower()
        if search_engine in ('google', 'bing', 'duckduckgo'):
            extend_bits.append(
                f'Web search policy: always search with {search_engine}. '
                'Never open or use any other search engine site unless the task explicitly names one.'
            )
        extend_bits.append(NEEDS_USER_RULE)
        if extend_bits:
            agent_kwargs['extend_system_message'] = '\n\n'.join(extend_bits)
        history_items = _history_items(cfg)
        if history_items:
            agent_kwargs['max_history_items'] = history_items
        def make_agent(no_thinking):
            kwargs = dict(agent_kwargs)
            if no_thinking:
                kwargs['use_thinking'] = False
            return Agent(
                task=task,
                llm=llm,
                browser=browser,
                use_vision=_vision_value(cfg.get('use_vision')),
                directly_open_url=bool(cfg.get('open_new_window', True)),
                register_new_step_callback=on_new_step,
                register_should_stop_callback=should_stop,
                enable_signal_handler=False,
                llm_timeout=llm_timeout,
                step_timeout=step_timeout,
                max_failures=max_failures,
                # 0.13.x 默认在任务完成后再发一次带最多 10 张截图的"裁判"模型
                # 请求评审成败；结果只写日志，Broccoli 不消费——纯耗时，关掉
                # 以恢复 0.12 行为。
                use_judge=False,
                **kwargs,
            )

        _emit_progress({'step': 0, 'actions': ['starting'], 'url': ''})
        window_task = asyncio.ensure_future(_window_mode_loop(cfg, browser))
        run_error = ''
        timed_out = False
        history = None
        agent = None
        for no_thinking in (False, True):
            if own is not None and no_thinking:
                # the first run let go of the session; the new one would pick a tab by itself
                try:
                    await _return_to_own_window(browser, own)
                except Exception:
                    pass
            agent = make_agent(no_thinking)
            # only the standard speed asks for thinking (no_thinking / flash already do not)
            model_state['thinking_on'] = speed_mode == 'standard' and not no_thinking
            model_state['thinking_refused'] = False
            run_error, timed_out, history, interrupted = '', False, None, False
            try:
                history = await asyncio.wait_for(
                    agent.run(
                        max_steps=_positive_int(cfg.get('max_steps'), 30),
                        on_step_start=on_step_begin,
                    ),
                    timeout=overall_timeout,
                )
            except InterruptedError:
                interrupted = True
            except asyncio.TimeoutError:
                timed_out = True
            except Exception as exc:
                run_error = str(exc).strip() or exc.__class__.__name__
            if (model_state['thinking_on'] and model_state['thinking_refused']
                    and not _cancel_requested(cfg) and not timed_out):
                _emit_progress({'step': 0, 'url': '', 'actions': [
                    'the model does not hand over its thinking; starting again without asking for it']})
                continue
            if interrupted:
                _emit_cancelled()
                return
            break
        if _cancel_requested(cfg):
            _emit_cancelled()
            return
        # 无论正常结束、报错还是整体超时，都从（可能不完整的）history 里
        # 抢救已收集的内容——URL、动作、每步提取的页面文本。
        collected = _collect_history(history if history is not None else getattr(agent, 'history', None))
        needs_user = _needs_user_text(collected['final_result'])
        if needs_user:
            collected['final_result'] = collected['final_result'].replace(NEEDS_USER_MARK, 'Needs you:', 1)
            collected['extracted'] = [str(item).replace(NEEDS_USER_MARK, 'Needs you:') for item in collected['extracted']]
            cfg['_needs_user'] = needs_user
        has_content = bool(
            collected['final_result'] or collected['extracted'] or collected['urls'] or collected['action_names']
        )
        if timed_out:
            note = (
                f'Browser Use hit the overall time limit ({overall_timeout}s) and was stopped. '
                'Partial evidence collected before the stop:'
            )
            _emit_result({
                'ok': True,
                'answer': _compose_answer(collected, note) if has_content
                else f'Browser Use hit the overall time limit ({overall_timeout}s) before collecting any content.',
                'metadata': _result_metadata(cfg, collected, partial=True, error_text='overall timeout'),
            })
            return
        if run_error:
            if has_content:
                note = f'Browser Use run failed: {run_error}\n\nPartial evidence collected before the failure:'
                _emit_result({
                    'ok': True,
                    'answer': _compose_answer(collected, note),
                    'metadata': _result_metadata(cfg, collected, partial=True, error_text=run_error),
                })
                return
            _emit_result({'ok': False, 'error': run_error})
            return
        if has_content:
            note = ''
            if not collected['final_result']:
                note = 'Browser Use finished without an explicit final answer. Evidence collected during the run:'
            _emit_result({
                'ok': True,
                'answer': _compose_answer(collected, note) or 'Browser Use task completed.',
                'metadata': _result_metadata(cfg, collected, partial=not collected['final_result']),
            })
            return
        _emit_result({
            'ok': True,
            'answer': 'Browser Use task completed without capturing any page content.',
            'metadata': _result_metadata(cfg, collected, partial=True),
        })
    finally:
        if window_task is not None:
            window_task.cancel()
        if cfg.get('own_window'):
            await _leave_own_window(cfg)
        if cfg.get('close_window_after_task', False):
            await _close_browser(browser)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as exc:
        print(RESULT_PREFIX + json.dumps({
            'ok': False,
            'error': str(exc),
            'traceback': traceback.format_exc(),
        }, ensure_ascii=False), flush=True)
        sys.exit(1)
