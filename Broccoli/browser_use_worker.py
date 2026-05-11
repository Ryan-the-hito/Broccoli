import asyncio
import json
import sys
import traceback


RESULT_PREFIX = '__BROCCOLI_BROWSER_USE_RESULT__'


def _vision_value(mode):
    mode = str(mode or 'auto').lower()
    if mode == 'on':
        return True
    if mode == 'off':
        return False
    return 'auto'


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
    timeout = int(cfg.get('timeout') or 60)
    if llm_wrapper == 'anthropic':
        kwargs = {
            'model': model,
            'api_key': api_key,
            'timeout': timeout,
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
        llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=endpoint,
            timeout=timeout,
            temperature=None,
            frequency_penalty=None,
        )
    browser_kwargs = {'headless': False}
    if str(cfg.get('chrome_mode') or '') == 'connect_existing':
        browser_kwargs['cdp_url'] = str(cfg.get('cdp_url') or '').strip()
    else:
        browser_kwargs['executable_path'] = str(cfg.get('chrome_executable') or '').strip()
        browser_kwargs['user_data_dir'] = str(cfg.get('user_data_dir') or '').strip()
        browser_kwargs['keep_alive'] = not bool(cfg.get('close_window_after_task', False))
        browser_kwargs['ignore_default_args'] = ['--extensions-on-chrome-urls']
    browser = None
    try:
        browser = Browser(**browser_kwargs)
        task = str(cfg.get('task') or '').strip()
        if cfg.get('open_new_window', True):
            task = (
                'Start this automation in a new browser tab or window. '
                'Do not reuse unrelated existing tabs unless the user explicitly asks for it. '
            ) + task
        else:
            task = (
                'Use the currently active tab/page in the existing Browser Use Chrome window as the starting point. '
                'Do not open a new tab or navigate away unless the user explicitly asks for it. '
            ) + task
        agent = Agent(
            task=task,
            llm=llm,
            browser=browser,
            use_vision=_vision_value(cfg.get('use_vision')),
            directly_open_url=bool(cfg.get('open_new_window', True)),
        )
        history = await agent.run(max_steps=int(cfg.get('max_steps') or 30))
        final_result = ''
        method = getattr(history, 'final_result', None)
        if callable(method):
            try:
                final_result = str(method() or '').strip()
            except Exception:
                final_result = ''
        urls = []
        action_names = []
        errors = []
        for attr_name, target in (('urls', urls), ('action_names', action_names), ('errors', errors)):
            method = getattr(history, attr_name, None)
            if callable(method):
                try:
                    values = method() or []
                    if isinstance(values, (list, tuple)):
                        target.extend(str(item) for item in values if str(item).strip())
                except Exception:
                    pass
        answer_parts = [final_result or 'Browser Use task completed.']
        if urls:
            answer_parts.append('Visited URLs:\n' + '\n'.join(f'- {url}' for url in urls[-10:]))
        if action_names:
            answer_parts.append('Actions:\n' + ', '.join(action_names[-20:]))
        if errors:
            answer_parts.append('Errors:\n' + '\n'.join(f'- {err}' for err in errors[-5:]))
        print(RESULT_PREFIX + json.dumps({
            'ok': True,
            'answer': '\n\n'.join(answer_parts).strip(),
            'metadata': {
                'urls': urls,
                'action_names': action_names,
                'errors': errors,
                'model': str(cfg.get('model') or ''),
                'max_steps': int(cfg.get('max_steps') or 30),
            },
        }, ensure_ascii=False), flush=True)
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
