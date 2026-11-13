# -*- coding: utf-8 -*-
"""Translations for the "no news" reminder (2026-11-12): an AI task that is not finished and
has said nothing for 15 minutes gets a reminder in Reminders. Loaded by i18n/gen_ts.py."""

FEATURE_TRANSLATIONS = {
    '{tool} · no news for {n} minutes': ('{tool} · {n} 分钟没有动静', '{tool} · {n} 分間動きなし'),
    'Last news at {time}.': ('最后一次动静在 {time}。', '最後の動きは {time}。'),
    'In {where}.': ('在 {where}。', '場所：{where}。'),
    '{tool}’s usage did not change in this time either.': (
        '这段时间 {tool} 的用量也没有变化。', 'この間、{tool} の使用量にも変化はありません。'),
    'Seen by Broccoli on the Mac “{mac}”.': (
        '由 Mac“{mac}”上的 Broccoli 看到。', 'Mac「{mac}」の Broccoli が確認しました。'),
    'Remind me when a task has had no news for {n} minutes': (
        '任务 {n} 分钟没有动静时提醒我', 'タスクが {n} 分間動かないときに知らせる'),
    'A task that is not finished and has said nothing for that long gets one reminder in the '
    'Reminders app, so your iPhone and Apple Watch ring too. It is ticked off when the task moves again. '
    'The same goes for a task that has waited {m} minutes for your approval or your answer.': (
        '任务还没结束、却这么久没有任何新内容时，在“提醒事项”里写一条提醒，iPhone 和 Apple Watch 也会响。'
        '任务再有动静时，这条提醒会自动勾掉。任务等你批准或等你回答满 {m} 分钟时也一样。',
        'タスクが終わっていないのにその間何も進まないとき、「リマインダー」に 1 件追加します。iPhone や '
        'Apple Watch でも通知されます。タスクがまた動き出すと、自動的に完了になります。'
        'タスクがあなたの承認や回答を {m} 分待っているときも同じです。'),
    # 2026-11-13: a task that waits for the person
    '{tool} · asked you a question': ('{tool} · 在问你', '{tool} · 質問が来ています'),
    '{tool} · waits for your approval': ('{tool} · 等你批准', '{tool} · 承認待ち'),
    'Waiting since {time}.': ('从 {time} 开始等。', '{time} から待っています。'),
    'Allow it in System Settings → Privacy & Security → Automation.': (
        '请在“系统设置 → 隐私与安全性 → 自动化”里允许。',
        '「システム設定 → プライバシーとセキュリティ → オートメーション」で許可してください。'),
}
