# -*- coding: utf-8 -*-
"""Translations for the 2026-10-30 change: browsing old answers while one is generating
(Transfer during a run, the bottom status line) and Settings › General › Completion alerts
(a sound with the agent notifications, a reminder in Reminders).
Loaded by i18n/gen_ts.py (one table per feature)."""

FEATURE_TRANSLATIONS = {
    # The bottom status line while browsing old answers
    'waiting for your approval': ('等你批准', '承認待ち'),
    '{count} characters written': ('已写 {count} 字', '{count} 文字まで作成'),
    'step {n}/{total}: {title}': ('第 {n}/{total} 步：{title}', 'ステップ {n}/{total}：{title}'),
    'working': ('处理中', '処理中'),
    '⏳ Answering “{question}” · {detail} · click here to go back': (
        '⏳ 正在回答「{question}」· {detail} · 点这里返回',
        '⏳ 回答中「{question}」· {detail} · クリックで戻る'),
    '✅ The new answer is ready · click here to see it': (
        '✅ 新回答已完成 · 点这里查看', '✅ 新しい回答ができました · クリックで表示'),
    '⏳ The agent stopped and is waiting for you · click here to see it': (
        '⏳ Agent 停下来等你处理 · 点这里查看', '⏳ Agent が止まってあなたを待っています · クリックで表示'),
    '⚠️ Not finished · click here to see it': ('⚠️ 没有完成 · 点这里查看', '⚠️ 完了しませんでした · クリックで表示'),
    'Stopped · click here to see it': ('已停止 · 点这里查看', '停止しました · クリックで表示'),

    # Settings › General › Completion alerts
    'Completion alerts': ('完成提醒', '完了通知'),
    'How Broccoli lets you know when an agent finishes.': (
        'Agent 跑完时，Broccoli 怎么提醒你。', 'Agent が終わったときの知らせ方です。'),
    'Play a sound with completion notifications': ('完成提醒带声音', '完了通知で音を鳴らす'),
    'The notifications for “answer ready”, “run failed” and “waiting for you” use the system '
    'notification sound. Focus modes keep them silent.': (
        '"回答已完成""运行失败""等你处理"这三种通知使用系统的通知声音；专注模式下不响。',
        '「回答ができました」「失敗しました」「あなたを待っています」の通知でシステムの通知音を鳴らします。'
        '集中モード中は鳴りません。'),
    'Open Notification Settings': ('打开通知设置', '通知設定を開く'),
    'Add a reminder in Reminders when an agent finishes': (
        'Agent 完成时在"提醒事项"里加一条', 'Agent が終わったらリマインダーに追加'),
    'It goes into the list “Broccoli” in iCloud and rings a minute later, so your iPhone, iPad and '
    'Watch get it too. It does not ring if you have already looked at the conversation on the Mac, '
    'and it is ticked off by itself a day later. Questions sent from the iPhone Shortcut have their '
    'own reminder and get no second one.': (
        '加到 iCloud 里的"Broccoli"列表，1 分钟后响，iPhone、iPad、手表都会收到。'
        '在 Mac 上已经看过这个对话的就不响；一天后自动打勾。'
        '从 iPhone 捷径发来的问题另有提醒，不会重复。',
        'iCloud のリスト「Broccoli」に追加され、1 分後に通知されるので、iPhone・iPad・Watch にも届きます。'
        'Mac でその会話をすでに見ていれば通知されず、1 日後に自動で完了になります。'
        'iPhone のショートカットから送った質問には別のリマインダーがあるので、重複しません。'),
    'Open Automation Settings': ('打开自动化设置', 'オートメーション設定を開く'),
    'Notifications for Broccoli are turned off in System Settings, so there is no sound either.': (
        '系统设置里关掉了 Broccoli 的通知，所以也不会有声音。',
        'システム設定で Broccoli の通知がオフになっているため、音も鳴りません。'),
    'macOS has turned off the sound for Broccoli’s notifications.': (
        'macOS 关掉了 Broccoli 的通知声音。', 'macOS で Broccoli の通知音がオフになっています。'),
    'Checking access to Reminders…': ('正在确认能否使用"提醒事项"…', 'リマインダーを使えるか確認しています…'),
    'Reminders is ready.': ('"提醒事项"可以用了。', 'リマインダーを使えます。'),
    'Broccoli is not allowed to use Reminders.': (
        'Broccoli 没有权限使用"提醒事项"。', 'Broccoli にリマインダーを使う許可がありません。'),
    'Reminders did not answer just now; Broccoli tries again when an agent finishes.': (
        '"提醒事项"刚才没有回应；Agent 完成时会再试。',
        'リマインダーから応答がありませんでした。Agent が終わったときにもう一度試します。'),

    # The reminder itself and the one-time warning
    'Open it in Broccoli on the Mac “{mac}”.': (
        '在 Mac「{mac}」上的 Broccoli 里查看。', 'Mac「{mac}」の Broccoli で開いてください。'),
    'Broccoli is not allowed to use Reminders, so finished agents get no reminder. '
    'Allow it in System Settings → Privacy & Security → Automation, or turn the '
    'reminder off in Settings → Completion alerts.': (
        'Broccoli 没有权限使用"提醒事项"，所以 Agent 完成时不会加提醒。'
        '请在 系统设置 → 隐私与安全性 → 自动化 里允许，或者在 设置 → 完成提醒 里关掉这个提醒。',
        'Broccoli にリマインダーを使う許可がないため、Agent が終わってもリマインダーは追加されません。'
        'システム設定 → プライバシーとセキュリティ → オートメーション で許可するか、'
        '設定 → 完了通知 でこのリマインダーをオフにしてください。'),
}
