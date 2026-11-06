# -*- coding: utf-8 -*-
"""Translations for the 2026-10-31 change: AI tasks — the dots beside the pointer when an AI tool on
this Mac finishes a turn, and Settings › General › AI tasks (style book 5.1.3).
Loaded by i18n/gen_ts.py (one table per feature)."""

FEATURE_TRANSLATIONS = {
    # The capsules
    'just now': ('刚刚', 'たった今'),
    '{n} min ago': ('{n} 分钟前', '{n} 分前'),
    '{n} h ago': ('{n} 小时前', '{n} 時間前'),
    'Broccoli terminal': ('Broccoli 终端', 'Broccoli のターミナル'),
    # USAGE_BAR_PROVIDER_COLOR_NAMES (through a variable, listed in gen_ts EXTRA_SOURCE_STRINGS)
    'Indigo': ('靛蓝', 'インディゴ'),

    # Settings › General › AI tasks
    'AI tasks': ('AI 任务', 'AI タスク'),
    'Dots beside the pointer when an AI tool on this Mac finishes a turn.': (
        '这台 Mac 上的 AI 工具做完一轮时，鼠标旁出现的小圆点。',
        'この Mac の AI ツールが 1 ターン終えたとき、ポインタの横に出る点です。'),
    'Show AI tasks beside the pointer': ('在鼠标旁显示 AI 任务', 'ポインタの横に AI タスクを表示'),
    'When Claude Code, Codex or another AI tool on this Mac (in VS Code, a terminal or Broccoli) or '
    'Broccoli’s own agent finishes a turn, a column of dots appears beside the pointer: grey = still '
    'running, green = done. Point at it to see the tasks; click one to go there. The sound is the '
    'one under Completion alerts. The built-in agentsview reads the sessions; nothing leaves this Mac.': (
        '这台 Mac 上的 Claude Code、Codex 等 AI 工具（在 VS Code、终端或 Broccoli 里）或 Broccoli 自己的 '
        'Agent 做完一轮时，鼠标旁会出现一列小圆点：灰色 = 还在进行，绿色 = 做完了。鼠标移上去看是哪些任务，'
        '点一个就跳过去。声音用「完成提醒」里的设置。会话由内置的 agentsview 读取，数据不离开这台 Mac。',
        'この Mac の Claude Code・Codex などの AI ツール（VS Code、ターミナル、Broccoli 内）や Broccoli 自身の '
        'Agent が 1 ターン終えると、ポインタの横に点が縦に並びます：グレー = 実行中、緑 = 完了。ポインタを'
        '乗せるとタスクが見え、クリックでそこへ移動します。音は「完了通知」の設定に従います。セッションは'
        '内蔵の agentsview が読み取り、データはこの Mac から出ません。'),
    'Tasks shown': ('显示个数', '表示する数'),
    'Shortcut': ('快捷键', 'ショートカット'),
    'Record AI tasks shortcut': ('录制 AI 任务快捷键', 'AI タスクのキーを記録'),
    'Press it to open the column at the pointer; press it again to close it.': (
        '按一下在鼠标处打开这一列，再按一下收起。', '押すとポインタの位置に開き、もう一度押すと閉じます。'),
    'AI tasks shortcut must be different from the other shortcuts.': (
        'AI 任务快捷键不能和其他快捷键相同。', 'AI タスクのショートカットは他のショートカットと別にしてください。'),
    'Tools': ('工具', 'ツール'),
    'Tool': ('工具', 'ツール'),
    'Watched': ('提醒', '通知'),
    'Color': ('颜色', '色'),
    'Yes': ('是', 'はい'),
    'Watch': ('提醒', '通知する'),
    'Don’t watch': ('不提醒', '通知しない'),
    'Broccoli agent': ('Broccoli 的 Agent', 'Broccoli の Agent'),
    'A provider has the same color here as on the usage bars. Green and grey are kept for done and '
    'running, red and orange for a nearly used-up bar.': (
        '同一家供应商在这里和用量条上是同一个颜色。绿色和灰色留给"做完""进行中"，红色和橙色留给快用完的用量条。',
        '同じ提供元はここと使用量バーで同じ色です。緑とグレーは「完了」「実行中」、赤とオレンジは残りわずかの'
        '使用量バー用です。'),
    'Green and grey show whether an AI task is done or still running, so no provider may use them. '
    'Choose another color.': (
        '绿色和灰色用来表示 AI 任务做完了还是还在进行，不能给供应商用。请换一个颜色。',
        '緑とグレーは AI タスクの完了・実行中を表すため、提供元には使えません。別の色を選んでください。'),
    'Off.': ('已关闭。', 'オフです。'),
    'Starting the built-in agentsview {version}. The first start reads every session once (about half a minute).': (
        '正在启动内置的 agentsview {version}。第一次启动会把所有会话读一遍（大约半分钟）。',
        '内蔵の agentsview {version} を起動中です。初回はすべてのセッションを一度読み込みます（約 30 秒）。'),
    'Reading sessions with the built-in agentsview {version}.': (
        '正在用内置的 agentsview {version} 读取会话。', '内蔵の agentsview {version} でセッションを読み取っています。'),
    'This copy of Broccoli has no agentsview.': ('这份 Broccoli 里没有 agentsview。', 'この Broccoli には agentsview が入っていません。'),
    'agentsview could not start: {detail}': ('agentsview 启动失败：{detail}', 'agentsview を起動できませんでした：{detail}'),

    # 2026-11-01: hold the right button and move up
    'Open with the mouse: hold the right button and move up': (
        '用鼠标打开：按住右键往上划', 'マウスで開く：右ボタンを押したまま上へ'),
    'The column opens where you let go. Other right-clicks show their menu on release; '
    'right-button dragging (some games, 3D apps) does not work while this is on.': (
        '这一列在松开的地方展开。其他右键照常弹菜单，只是松开时才出来；开着时，右键拖动（少数游戏、3D 软件会用）不起作用。',
        '離した位置に列が開きます。ほかの右クリックは離したときにメニューが出ます。オンの間は右ボタンのドラッグ'
        '（一部のゲームや 3D アプリ）が使えません。'),
    'Right-drag up could not start: macOS did not let Broccoli listen to the mouse.': (
        '右键往上划没能启动：macOS 不允许 Broccoli 监听鼠标。',
        '右ボタンで上へを開始できませんでした：macOS が Broccoli にマウスの監視を許可しませんでした。'),
}
