# -*- coding: utf-8 -*-
"""Translations for the 2026-11-07 change: the 🥦 circle is a window of its own and can stay out while
the main window is open; its grid's middle may stay empty then; a shortcut shows / hides it (style
book 5.1.2 / 5.1.4). Loaded by i18n/gen_ts.py (one table per feature). "Collapsed button" is
最小化圆按钮 / 最小化ボタン, as in translations_feature_collapsed_launcher.py."""

FEATURE_TRANSLATIONS = {
    'Show the collapsed button while the main window is open': (
        '主窗口打开时也显示最小化圆按钮', 'メインウィンドウ表示中も最小化ボタンを表示'),
    'Broccoli in the middle of its grid (main window open)': (
        '主窗口打开时，九宫格中间显示 Broccoli', 'メインウィンドウ表示中、グリッド中央に Broccoli を表示'),
    'Off: the middle of the grid stays empty while the main window is open. With the main window '
    'in the collapsed button, the middle always shows Broccoli.': (
        '关闭后，主窗口打开时九宫格中间留空。主窗口收进最小化圆按钮后，中间始终显示 Broccoli。',
        'オフにすると、メインウィンドウ表示中はグリッドの中央が空になります。メインウィンドウが最小化ボタンに'
        '入っている間は、中央に常に Broccoli が表示されます。'),
    'Record Collapsed button shortcut': ('录制最小化圆按钮快捷键', '最小化ボタンのショートカットを記録'),
    'Collapsed button shortcut must be different from the other shortcuts.': (
        '最小化圆按钮快捷键必须与其他快捷键不同。', '最小化ボタンのショートカットは、他のショートカットと別にしてください。'),
}
