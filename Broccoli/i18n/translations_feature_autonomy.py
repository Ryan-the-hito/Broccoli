# Autonomous mode (2026-10-28): plan → run → judge rounds until done, blocked or a limit.
FEATURE_TRANSLATIONS = {
    'Autonomous mode': ('全自动模式', '全自動モード'),
    'Round {n}': ('第 {n} 轮', '第 {n} ラウンド'),
    'Checking the result against the task contract (round {n})': (
        '正在按任务合同核对结果（第 {n} 轮）',
        'タスクの契約に照らして結果を確認しています（第 {n} ラウンド）'),
    'Autonomous round {n}: planning the next steps': (
        '全自动第 {n} 轮：正在规划下一步',
        '全自動 第 {n} ラウンド：次の手順を計画しています'),
    'You are using the computer: Computer Use waits until you stop.': (
        '你正在使用电脑：电脑操作会等你停下来再开始。',
        'コンピュータを使用中です：操作が止まるまでコンピュータ操作は待機します。'),
    'Waiting for you — {title}': ('等你处理 — {title}', 'あなたの対応待ち — {title}'),
    "Run this group's conversations autonomously": (
        '本组对话全自动运行',
        'このグループの会話を全自動で実行する'),
    "They carry a task through to the end on their own: every action is approved automatically "
    "(after a backup), and they stop only for what needs you, such as a password. A conversation's "
    "own switch (right-click its tag) wins over this.": (
        '对话会自己把任务做到底：每个动作都先备份再自动批准，只有需要你的时候（比如输入密码）才停下。'
        '对话自己的开关（右键点它的标签）优先于这里。',
        '会話はタスクを最後まで自分で進めます：すべての操作はバックアップ後に自動で承認され、'
        'パスワードなどあなたが必要なときだけ止まります。会話ごとのスイッチ（タグを右クリック）がこちらより優先されます。'),
    'Run every conversation autonomously': ('所有对话都全自动运行', 'すべての会話を全自動で実行する'),
    "An autonomous conversation carries a task through to the end: it plans, runs the steps, checks "
    "the result against what you asked for, and goes another round until it is done — every action "
    "approved automatically after a backup. It stops only for what needs you (a password, a payment, "
    "something physical) and then notifies you; your next message continues the task. A group's "
    "setting or a conversation's own switch (right-click its tag) wins over this. Tasks from another "
    "device run autonomously only when their conversation or group is switched on here.": (
        '全自动的对话会把任务做到底：自己规划、执行步骤、按你的要求核对结果，没做完就再来一轮——'
        '每个动作都先备份再自动批准。只有需要你的时候（输入密码、付款、需要动手的操作）才会停下并通知你；'
        '你回复后接着做同一个任务。分组的设置或对话自己的开关（右键点它的标签）优先于这里。'
        '从其他设备发来的任务，只有在这台 Mac 上为它的对话或分组打开时才会全自动运行。',
        '全自動の会話はタスクを最後までやり遂げます：自分で計画し、手順を実行し、依頼内容と照らして結果を確認し、'
        '終わるまで次のラウンドに進みます——すべての操作はバックアップ後に自動で承認されます。'
        'あなたが必要なとき（パスワード、支払い、物理的な操作）だけ止まって通知し、返信すると同じタスクを続けます。'
        'グループの設定や会話ごとのスイッチ（タグを右クリック）がこちらより優先されます。'
        '他のデバイスから送られたタスクは、このMacでその会話かグループをオンにしたときだけ全自動で実行されます。'),
}

FEATURE_EXTRA_SOURCE_STRINGS = []
