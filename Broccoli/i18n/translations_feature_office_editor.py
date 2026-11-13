# -*- coding: utf-8 -*-
"""Translations for the 2026-11-11 change: Word / Excel / PowerPoint files open in the editor (in the
bundled office component) and the AI edits them through their text view. Loaded by i18n/gen_ts.py
(one table per feature)."""

FEATURE_TRANSLATIONS = {
    'Opening “{name}”…': ('正在打开“{name}”…', '「{name}」を開いています…'),
    '“{name}” could not be read.': ('“{name}”读不出来。', '「{name}」を読み込めませんでした。'),
    'The office editing component is not available.': ('Office 编辑组件不可用。', 'Office 編集コンポーネントを利用できません。'),
    '“{name}” could not be opened here: {reason}': ('“{name}”在这里打不开：{reason}', '「{name}」をここで開けませんでした：{reason}'),
    'The document is not open.': ('文档没有打开。', '文書が開かれていません。'),
    'The document is still opening. Try again in a moment.': ('文档还在打开，请稍后再试。', '文書を開いている途中です。少ししてからもう一度お試しください。'),
    'The document did not come back in time.': ('文档没有及时交回来。', '文書が時間内に戻ってきませんでした。'),
    'the document did not open in time': ('文档没有及时打开', '文書が時間内に開きませんでした'),
    'the edited document did not come back in time': ('改好的文档没有及时交回来', '編集した文書が時間内に戻ってきませんでした'),
    'the editing component returned an empty document': ('编辑组件交回了一份空文档', '編集コンポーネントが空の文書を返しました'),
    'another program changed the file a moment ago': ('另一个程序刚刚改了这个文件', '別のアプリがたった今このファイルを変更しました'),
    'a running task is changing it right now': ('一个正在运行的任务正在改它', '実行中のタスクが変更しているところです'),
    'the file is read-only': ('文件是只读的', 'ファイルは読み取り専用です'),
    'it is open in another app (Word, Excel or PowerPoint) right now. Close it there first.': (
        '它现在正被另一个 App（Word、Excel 或 PowerPoint）打开着。请先在那边关掉。',
        '今ほかのアプリ（Word・Excel・PowerPoint）で開かれています。先にそちらで閉じてください。'),
    '“{name}” is open in another app (Word, Excel or PowerPoint) right now, so it was not saved. Close it there first.': (
        '“{name}”现在正被另一个 App（Word、Excel 或 PowerPoint）打开着，所以没有保存。请先在那边关掉。',
        '「{name}」は今ほかのアプリ（Word・Excel・PowerPoint）で開かれているため、保存しませんでした。先にそちらで閉じてください。'),
    'Unsaved changes': ('有未保存的改动', '未保存の変更'),
    'Save “{name}” first (or reload it) to look at an earlier version.': (
        '要看以前的版本，请先保存“{name}”（或重新载入它）。',
        '以前のバージョンを見るには、先に「{name}」を保存（または再読み込み）してください。'),
    'The unsaved changes of “{name}” could not be saved first ({reason}), so nothing was restored.': (
        '“{name}”里未保存的改动没能先保存下来（{reason}），所以没有还原任何东西。',
        '「{name}」の未保存の変更を先に保存できなかったため（{reason}）、何も復元しませんでした。'),
    '“{name}” has unsaved changes that could not be saved ({reason}), so the AI’s change was not applied. Save the file and send your request again.': (
        '“{name}”里有未保存的改动没能保存下来（{reason}），所以 AI 的修改没有写入。请先保存文件，再发一次请求。',
        '「{name}」の未保存の変更を保存できなかったため（{reason}）、AI の変更は適用しませんでした。ファイルを保存してから、もう一度依頼してください。'),
}
