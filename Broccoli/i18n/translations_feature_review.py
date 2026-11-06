# -*- coding: utf-8 -*-
"""Translations for the 2026-10-30 change: every Agent command, Claude Code / Codex request and MCP
call is reviewed by a separate model before it is approved; approval windows follow Settings ›
Languages. Loaded by i18n/gen_ts.py (one table per feature)."""

FEATURE_TRANSLATIONS = {
    # status line while the review runs
    'Reviewing the command…': ('正在审核这条命令…', 'コマンドを審査中…'),
    # the review's explanation when it could not be done / the one program rule
    'The review could not be completed ({error}), so you decide.': (
        '审核没能完成（{error}），所以由你来决定。',
        '審査を完了できませんでした（{error}）。判断はあなたにお任せします。'),
    'It asks for administrator rights (sudo and the like): Broccoli never runs that without you.': (
        '它要用管理员权限（sudo 之类）：这种命令 Broccoli 从不在你不在场时运行。',
        '管理者権限（sudo など）を使おうとしています。Broccoli はあなたの確認なしにこれを実行しません。'),
    # Settings › General › Automatic approval
    'For tasks that run while nobody is at the screen. What the review below finds fine runs without '
    'asking, after a copy of what it changes: Agent commands, what it hands to Codex / Claude Code, MCP '
    'tool calls; editor edits and Computer Use too. Always asked: administrator rights (sudo), erasing a '
    'disk, system files, sending anything off this Mac.': (
        '用于没人看着屏幕时运行的任务。下面的审核认为没问题的，先复制一份它要改动的东西，然后不问你直接运行：'
        'Agent 的命令、交给 Codex / Claude Code 的操作、MCP 工具调用；编辑器改动和电脑操作也一样。'
        '一定会问你的：管理员权限（sudo）、抹掉磁盘、改系统文件、往这台 Mac 外发送任何东西。',
        '画面の前に誰もいない間に動くタスク向けです。下の審査で問題なしとされたものは、変更対象をコピーしてから'
        '確認なしで実行します：エージェントのコマンド、Codex / Claude Code に任せる操作、MCP ツール呼び出し、'
        'エディタの編集とコンピュータ操作も同様です。必ず確認するもの：管理者権限（sudo）、ディスクの消去、'
        'システムファイル、この Mac の外への送信。'),
    'The files the review names are copied into the backup folder first, one folder per conversation '
    '(manifest.json says where each came from); with this switch off, after you click Allow. Clicks, typing '
    'and what is sent elsewhere cannot be copied: every review is a line in the conversation\'s log.jsonl. '
    'Tasks from your iPhone or another Mac are handled the same way.': (
        '审核列出的文件会先复制到备份文件夹，每段对话一个文件夹（manifest.json 写着每个文件原来在哪）；'
        '这个开关关着时，在你点"允许"之后才复制。点击、输入和发到别处的东西无法复制：每次审核都会记进这段对话的 '
        'log.jsonl。从 iPhone 或别的 Mac 发来的任务也一样处理。',
        '審査が挙げたファイルは、まずバックアップフォルダにコピーします（会話ごとに 1 フォルダ。manifest.json に'
        '元の場所が書かれています）。このスイッチがオフのときは「許可」を押した後にコピーします。クリック、入力、'
        '外部に送るものはコピーできません。審査はすべて会話の log.jsonl に 1 行ずつ記録されます。iPhone や別の Mac '
        'から届いたタスクも同じように扱います。'),
    'Review model': ('审核模型', '審査モデル'),
    'Automatic': ('自动', '自動'),
    'Reviews every command first, switch on or off: should it be done this way, how risky, what exactly '
    'it changes. The approval window shows its explanation. Automatic: the planner\'s model, or a chat '
    'model other than the one that wrote the command.': (
        '不管开关开没开，都先审核每条命令：该不该这样做、有多危险、具体会改什么。批准窗口里显示的就是它写的说明。'
        '选"自动"时用规划器的模型，或者和写命令的不同的聊天模型。',
        'スイッチのオン・オフに関係なく、まずすべてのコマンドを審査します：このやり方でよいか、どれだけ危険か、'
        '具体的に何が変わるか。承認ウィンドウにはこの説明が表示されます。「自動」ではプランナーのモデル、または'
        'コマンドを書いたものとは別のチャットモデルを使います。'),
    # plan step title (stored in English, shown through _tr(title))
    'Sent back by the review': ('被审核退回', '審査で差し戻し'),
}

# passed to _tr() through a variable (plan step titles are stored in English)
FEATURE_EXTRA_SOURCE_STRINGS = [
    'Sent back by the review',
]
