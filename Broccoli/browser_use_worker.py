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
    return metadata


async def main():
    cfg = json.load(sys.stdin)
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
            'api_key': api_key,
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
    try:
        if _cancel_requested(cfg):
            _emit_cancelled()
            return

        browser = Browser(**browser_kwargs)
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
            return _cancel_requested(cfg)

        async def on_step_begin(agent_obj):
            # 每步开始（模型调用之前）触发：把"启动浏览器"和"第 N 步思考中"
            # 在进度里分开——此前两者都挤在 Browser worker starting 一个标签下。
            step_number = 0
            try:
                step_number = int(getattr(agent_obj.state, 'n_steps', 0) or 0)
            except Exception:
                pass
            _emit_progress({'step': step_number, 'actions': ['thinking…'], 'url': ''})

        def on_new_step(browser_state_summary, agent_output, step_number):
            actions = []
            try:
                for action in (getattr(agent_output, 'action', None) or []):
                    dumped = action.model_dump(exclude_none=True) if hasattr(action, 'model_dump') else None
                    if isinstance(dumped, dict) and dumped:
                        actions.append(str(next(iter(dumped.keys()))))
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
        if extend_bits:
            agent_kwargs['extend_system_message'] = '\n\n'.join(extend_bits)
        history_items = _history_items(cfg)
        if history_items:
            agent_kwargs['max_history_items'] = history_items
        agent = Agent(
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
            **agent_kwargs,
        )
        _emit_progress({'step': 0, 'actions': ['starting'], 'url': ''})
        run_error = ''
        timed_out = False
        history = None
        try:
            history = await asyncio.wait_for(
                agent.run(
                    max_steps=_positive_int(cfg.get('max_steps'), 30),
                    on_step_start=on_step_begin,
                ),
                timeout=overall_timeout,
            )
        except InterruptedError:
            _emit_cancelled()
            return
        except asyncio.TimeoutError:
            timed_out = True
        except Exception as exc:
            run_error = str(exc).strip() or exc.__class__.__name__
        if _cancel_requested(cfg):
            _emit_cancelled()
            return
        # 无论正常结束、报错还是整体超时，都从（可能不完整的）history 里
        # 抢救已收集的内容——URL、动作、每步提取的页面文本。
        collected = _collect_history(history if history is not None else getattr(agent, 'history', None))
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
