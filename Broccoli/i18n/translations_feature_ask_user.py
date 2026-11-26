# -*- coding: utf-8 -*-
"""Translations for 2026-11-25: a step asks the person and waits (the question in the conversation, the
plan panel, the notification, another Mac's status card, the iPhone's Note; no answer in time → the
recommended one). Loaded by i18n/gen_ts.py (one table per feature)."""

FEATURE_TRANSLATIONS = {
    'recommended': ('推荐', 'おすすめ'),
    'Recommended: {answer}': ('推荐：{answer}', 'おすすめ：{answer}'),
    'Send a number to choose, or type your answer.': ('发一个数字选对应的项，或者直接打字回答。',
                                                    '番号を送って選ぶか、答えを入力して送信してください。'),
    'Type your answer and send it.': ('在输入框里打字回答再发送。', '入力欄に答えを書いて送信してください。'),
    'No answer by {time}: the recommended answer is used.': ('{time} 前没有回答，就按推荐的继续。',
                                                            '{time} までに答えがなければ、おすすめで進めます。'),
    'A question for you — {title}': ('有个问题等你回答 — {title}', 'あなたへの質問があります — {title}'),
    'Stopped before an answer came.': ('还没回答就停止了。', '答えが来る前に停止しました。'),
    'No answer in time — the recommended answer was used: {answer}': ('到时间没有回答，按推荐继续：{answer}',
                                                                     '時間内に答えがなかったので、おすすめで進めました：{answer}'),
    'Runs by itself — the recommended answer was used: {answer}': ('自动运行中，按推荐继续：{answer}',
                                                                  '自動で実行中のため、おすすめで進めました：{answer}'),
    'Answer: {answer}': ('回答：{answer}', '回答：{answer}'),
    '💬 Reply': ('💬 回答', '💬 回答'),
    'A question from the Mac': ('Mac 上的提问', 'Mac からの質問'),
    'Broccoli on the Mac needs your answer to go on. In the Shortcut, choose this conversation and send '
    'your answer (a number picks that choice). With no answer within 10 minutes it goes on with the '
    'recommended one. The full answer arrives as a separate note.': (
        'Mac 上的 Broccoli 需要你回答才能继续。在快捷指令里选这段对话，把你的回答发过去（发一个数字就是选那一项）。'
        '10 分钟内没有回答，就按推荐的继续。完整的回答会另外发一条备忘录。',
        'Mac の Broccoli が続けるにはあなたの答えが必要です。ショートカットでこの会話を選び、答えを送ってください'
        '（数字を送るとその選択肢になります）。10 分以内に答えがなければ、おすすめで進めます。最終的な回答は別のメモで届きます。'),
    # the built-in skill-creator (2026-11-25)
    'Save the skill "{name}" in Settings › Skills?': ('把技能「{name}」存进 设置 › Skills 吗？', 'スキル「{name}」を 設定 › Skills に保存しますか？'),
    'Not yet': ('先不存', 'まだ保存しない'),
}
