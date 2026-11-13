# -*- coding: utf-8 -*-
"""Translations for the 2026-11-12 changes to the 🥦 circle: Broccoli's own quick commands (style book
5.1.11) and the grid's five layers with the double click and the layer shortcuts (5.1.12). The green
glow (5.1.10) has no words. Loaded by i18n/gen_ts.py (one table per feature)."""

FEATURE_TRANSLATIONS = {
    # the kinds
    'Ask the Agent': ('问 Agent', 'Agent に質問'),
    'AppleScript': ('AppleScript', 'AppleScript'),
    'Shell script': ('Shell 脚本', 'シェルスクリプト'),
    # the dialog
    'New quick command': ('新建快捷指令', '新しいクイックコマンド'),
    'Edit quick command': ('编辑快捷指令', 'クイックコマンドを編集'),
    'Name': ('名称', '名前'),
    'Icon: first letter': ('图标：名字首字', 'アイコン：頭文字'),
    'Layer: automatic': ('层：自动', '層：自動'),
    'Layer {n}': ('第 {n} 层', '第 {n} 層'),
    'Not in the grid': ('不放进九宫格', 'グリッドに置かない'),
    'Send the tray\'s files with the question': ('把托盘里的文件随问题一起发', 'トレイのファイルを質問と一緒に送る'),
    'The question the Agent gets every time': ('每次交给 Agent 的问题', '毎回 Agent に送る質問'),
    'AppleScript: runs at once, without the AI': ('AppleScript：直接运行，不经过 AI', 'AppleScript：AI を通さずすぐ実行'),
    'Shell script: runs at once, without the AI': ('Shell 脚本：直接运行，不经过 AI', 'シェルスクリプト：AI を通さずすぐ実行'),
    # the grid's menus
    'Edit Quick Command…': ('编辑快捷指令…', 'クイックコマンドを編集…'),
    'New Quick Command…': ('新建快捷指令…', '新しいクイックコマンド…'),
    # running, saving
    'Quick commands': ('快捷指令', 'クイックコマンド'),
    'Could not run the quick command “{name}”.': ('快捷指令“{name}”没能运行。', 'クイックコマンド「{name}」を実行できませんでした。'),
    'There is no command yet. Ask for one first.': ('还没有命令。请先让 AI 写一个。', 'まだコマンドがありません。先に AI に作らせてください。'),
    '⚡ Save': ('⚡ 存为指令', '⚡ 保存'),
    'Save Last Question as Quick Command…': ('把最后一个问题存为快捷指令…', '最後の質問をクイックコマンドに保存…'),
    # Settings › Quick commands
    'New…': ('新建…', '新規…'),
    'Edit…': ('编辑…', '編集…'),
    'Run': ('运行', '実行'),
    'Delete the quick command “{name}”?': ('删除快捷指令“{name}”？', 'クイックコマンド「{name}」を削除しますか？'),
    'A script runs at once, without the AI. A question goes to the Agent as a new conversation; '
    'its answer comes out of the collapsed button. Double-click the collapsed button for layer 2 '
    'of its grid, where new commands go; scroll there for the other layers.': (
        '脚本直接运行，不经过 AI。问题会作为一个新对话交给 Agent，回答从最小化圆按钮里出来。双击最小化圆按钮打开九宫格第 2 层，新指令放在那里；在九宫格里滚动可以翻到其他层。',
        'スクリプトは AI を通さずすぐ実行されます。質問は新しい会話として Agent に送られ、答えは最小化ボタンから出てきます。最小化ボタンをダブルクリックするとグリッドの第 2 層（新しいコマンドの置き場）が開き、スクロールでほかの層に移れます。'),
    'Your own commands for the collapsed button\'s grid: a script that runs at once, or a question for the Agent.': (
        '放在最小化圆按钮九宫格里的自定指令：直接运行的脚本，或交给 Agent 的问题。',
        '最小化ボタンのグリッドに置く自分のコマンド：すぐ実行するスクリプト、または Agent への質問。'),
    # the layers
    'Record Grid layer {n} shortcut': ('录制九宫格第 {n} 层快捷键', 'グリッド第 {n} 層のキーを記録'),
    'Grid layer shortcuts must be different from the other shortcuts.': ('九宫格各层的快捷键不能和其他快捷键相同。', 'グリッドの層のショートカットは、ほかのショートカットと別にしてください。'),
    'Double-click the collapsed button for layer 2 of its grid': ('双击最小化圆按钮打开九宫格第 2 层', '最小化ボタンのダブルクリックでグリッドの第 2 層を開く'),
    'On: a single click waits a moment (the system\'s double-click time) before it shows or hides '
    'the main window. Off: a click works at once; open the other layers with their shortcuts or by scrolling in the grid.': (
        '开：单击要稍等一下（系统的双击间隔）才显示或收起主窗口。关：单击立即生效；其他层用各自的快捷键打开，或在九宫格里滚动。',
        'オン：シングルクリックは少し待ってから（システムのダブルクリック間隔）メインウィンドウを表示・非表示にします。オフ：クリックはすぐ効きます。ほかの層はそれぞれのショートカットか、グリッド内のスクロールで開きます。'),
    # the scan (5.1.13): a window without a name
    'Window': ('窗口', 'ウインドウ'),
    'Text read: {n} characters': ('读到正文 {n} 字', '読み取った本文：{n} 文字'),
    'No text read': ('没有读到正文', '本文は読み取れませんでした'),
    'Copy All': ('全部复制', 'すべてコピー'),
    'Double-click the collapsed button to show its last answer again': ('双击最小化圆按钮重新打开上一个回答', '最小化ボタンのダブルクリックで直前の回答をもう一度表示'),
    'On: a single click waits a moment (the system\'s double-click time) before it shows or hides '
    'the main window. Off: a click works at once.': (
        '开：单击要稍等一下（系统的双击间隔）才显示或收起主窗口。关：单击立即生效。',
        'オン：シングルクリックは少し待ってから（システムのダブルクリック間隔）メインウィンドウを表示・非表示にします。オフ：クリックはすぐ効きます。'),
    'A script runs at once, without the AI. A question goes to the Agent as a new conversation; '
    'its answer comes out of the collapsed button. New commands go to layer 2 of its grid: rest the '
    'pointer on the collapsed button, then scroll in the grid or click its page dots.': (
        '脚本直接运行，不经过 AI。问题会作为一个新对话交给 Agent，回答从最小化圆按钮里出来。新指令放在九宫格第 2 层：鼠标停在最小化圆按钮上，再在九宫格里滚动或点页点。',
        'スクリプトは AI を通さずすぐ実行されます。質問は新しい会話として Agent に送られ、答えは最小化ボタンから出てきます。新しいコマンドはグリッドの第 2 層に入ります：最小化ボタンにポインタを置き、グリッド内でスクロールするかページの点をクリックしてください。'),
    # the icons one can pick
    'Bolt': ('闪电', '稲妻'), 'Star': ('星星', '星'), 'Heart': ('爱心', 'ハート'), 'Globe': ('地球', '地球'),
    'News': ('新闻', 'ニュース'), 'Search': ('搜索', '検索'), 'Mail': ('邮件', 'メール'), 'Calendar': ('日历', 'カレンダー'),
    'Clock': ('时钟', '時計'), 'Document': ('文档', '書類'), 'Folder': ('文件夹', 'フォルダ'), 'Terminal': ('终端', 'ターミナル'),
    'Code': ('代码', 'コード'), 'Music': ('音乐', '音楽'), 'Photo': ('照片', '写真'), 'Camera': ('相机', 'カメラ'),
    'Video': ('视频', 'ビデオ'), 'Microphone': ('麦克风', 'マイク'), 'Chat': ('聊天', 'チャット'), 'Phone': ('电话', '電話'),
    'Map': ('地图', '地図'), 'Cart': ('购物车', 'カート'), 'Card': ('银行卡', 'カード'), 'Chart': ('图表', 'グラフ'),
    'Book': ('书', '本'), 'Study': ('学习', '学習'), 'Idea': ('灯泡', 'アイデア'), 'Magic': ('魔法棒', '魔法'),
    'Sparkles': ('闪光', 'きらめき'), 'Gear': ('齿轮', '歯車'), 'Home': ('房子', '家'), 'Person': ('人', '人'),
    'Cloud': ('云', '雲'), 'Sun': ('太阳', '太陽'), 'Moon': ('月亮', '月'), 'Flag': ('旗子', '旗'),
    'Bookmark': ('书签', 'ブックマーク'), 'Tag': ('标签', 'タグ'), 'Send': ('纸飞机', '紙飛行機'), 'Trash': ('废纸篓', 'ゴミ箱'),
    'Lock': ('锁', '鍵'), 'Key': ('钥匙', 'キー'), 'Wi-Fi': ('Wi-Fi', 'Wi-Fi'), 'Computer': ('电脑', 'コンピュータ'),
    'Keyboard': ('键盘', 'キーボード'), 'Printer': ('打印机', 'プリンタ'), 'Game': ('游戏', 'ゲーム'), 'Coffee': ('咖啡', 'コーヒー'),
    'Travel': ('飞机', '飛行機'), 'Tools': ('工具', '工具'),
}

# shown through _tr(variable): the kinds' names and the icons' names
FEATURE_EXTRA_SOURCE_STRINGS = [
    'Ask the Agent', 'AppleScript', 'Shell script',
    'Bolt', 'Star', 'Heart', 'Globe', 'News', 'Search', 'Mail', 'Calendar', 'Clock', 'Document', 'Folder', 'Terminal',
    'Code', 'Music', 'Photo', 'Camera', 'Video', 'Microphone', 'Chat', 'Phone', 'Map', 'Cart', 'Card', 'Chart', 'Book',
    'Study', 'Idea', 'Magic', 'Sparkles', 'Gear', 'Home', 'Person', 'Cloud', 'Sun', 'Moon', 'Flag', 'Bookmark', 'Tag',
    'Send', 'Trash', 'Lock', 'Key', 'Wi-Fi', 'Computer', 'Keyboard', 'Printer', 'Game', 'Coffee', 'Travel', 'Tools',
]
