# -*- coding: utf-8 -*-
"""Translations for the 2026-10-30 change: after an answer finishes, a separate short model call
guesses the next question; it shows in grey in the Agent prompt box, Return fills it in.
Loaded by i18n/gen_ts.py (one table per feature)."""

FEATURE_TRANSLATIONS = {
    # hover text of the Agent prompt box while a suggestion is up
    'Press Return to fill in: {text}': ('按回车填入：{text}', 'Return キーで入力：{text}'),
    # Settings › General page 1
    'Suggest the next question after each answer': ('回答完后预想下一个问题', '回答後に次の質問を予測する'),
    'After an answer finishes, one short extra request to the same model guesses what you will '
    'ask next. It shows in grey in the Agent box: press Return to fill it in, Command+Return to send.': (
        '回答结束后，向同一个模型多发一次简短请求，猜你下一句会问什么。它以灰字显示在 Agent 输入框里：'
        '按回车填入，按 Command+回车发送。',
        '回答が終わると、同じモデルに短いリクエストをもう一度送り、次に聞きそうなことを予測します。'
        'Agent の入力欄にグレーで表示されます。Return キーで入力、Command+Return で送信します。'),
}
