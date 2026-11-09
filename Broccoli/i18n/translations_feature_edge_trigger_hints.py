# -*- coding: utf-8 -*-
"""Translations for the 2026-11-07 change: the main window's hidden trigger strips show a glass strip and a
name tag on hover (style book 5.1.5), with a switch in Settings › Window & startup. The tag texts reuse the
panels' own names where they exist (Generated outputs, Question branches, History, '{name} history');
"Command history" / "Favorite commands" follow the panels' search fields (搜索命令历史 / 搜索收藏的命令).
Loaded by i18n/gen_ts.py (one table per feature)."""

FEATURE_TRANSLATIONS = {
    'Favorites': ('收藏', 'お気に入り'),
    'Links': ('链接', 'リンク'),
    'Settings': ('设置', '設定'),
    'Favorite commands': ('收藏的命令', 'お気に入りコマンド'),
    'Command history': ('命令历史', 'コマンド履歴'),
    'Show the web prompt box': ('显示网页提问框', 'ウェブページの質問欄を表示'),
    'Hide the web prompt box': ('收起网页提问框', 'ウェブページの質問欄を隠す'),
    'Show where you can click when the pointer rests on an edge': (
        '鼠标停在边缘时提示可以点的地方', '端にポインタを置くと、クリックできる場所を表示'),
    'The main window opens History, Links, Settings and more from strips along its edges. With this on, '
    'resting the pointer on one shows the strip in glass and a small label with what it opens.': (
        '主窗口边缘有几条可以点的地方，点了会打开历史、链接、设置等。打开这一项后，鼠标停在上面会显示一块玻璃长条'
        '和一个小标签，写明点了打开什么。',
        'メインウィンドウの端にある帯から、履歴・リンク・設定などを開けます。オンにすると、帯にポインタを置いたとき'
        'に帯がガラスで表示され、何が開くかを小さなラベルで示します。'),
}
