# -*- coding: utf-8 -*-
"""Translations for the 2026-11-11 change: asking about a part of a Word / Excel / PowerPoint file
open in the editor (Broccoli's entries in the component's right-click menu, Mark Region, the place
of a selection in words). Loaded by i18n/gen_ts.py (one table per feature)."""

FEATURE_TRANSLATIONS = {
    'Explain This': ('解释这一段', 'この部分を説明'),
    'Ask AI to Change This': ('让 AI 修改这里', 'AI にここを修正させる'),
    'Mark': ('圈选', 'マーク'),
    'Back': ('返回', '戻る'),
    'Mark Region': ('圈选', '範囲をマーク'),
    'Circle a part of the document and ask about it': ('在文档上圈出一块，然后就这一块提问', '文書の一部を囲んで、その部分について質問します'),
    'Sheet “{sheet}”, {cells}': ('工作表“{sheet}”，{cells}', 'シート「{sheet}」、{cells}'),
    'Sheet “{sheet}”': ('工作表“{sheet}”', 'シート「{sheet}」'),
    'Slide {n}': ('第 {n} 张幻灯片', 'スライド {n}'),
    'Page {n}': ('第 {n} 页', '{n} ページ'),
    'text view line {n}': ('文字版第 {n} 行', 'テキスト版 {n} 行目'),
    'text view lines {a}–{b}': ('文字版第 {a}–{b} 行', 'テキスト版 {a}–{b} 行目'),
    'Nothing selected': ('没有选中内容', '何も選択されていません'),
    'Select some text or cells in the document first. For a picture, a chart or the layout, use “Mark” in the bar below.': (
        '请先在文档里选中一些文字或格子。要问图片、图表或版式，请用下面工具栏里的“圈选”。',
        'まず文書内の文字かセルを選択してください。画像・グラフ・レイアウトについては、下のバーの「マーク」を使ってください。'),
    'Change this part of the open document as follows: ': ('请把打开的文档里这一部分改成：', '開いている文書のこの部分を次のように修正してください：'),
    'The picture could not be saved: {reason}': ('图片没能保存：{reason}', '画像を保存できませんでした：{reason}'),
    'The attached picture shows the part I circled in {place}': ('附上的图片里圈出的是 {place} 中的这一块', '添付の画像は {place} の中で囲んだ部分です'),
}

# 2026-11-11 (third part): a model changes an open office file by a script (the office tool)
FEATURE_TRANSLATIONS.update({
    'Reading the document layout': ('正在读取文档的版面', '文書のレイアウトを読み込んでいます'),
    'Running a script on the document': ('正在文档上运行脚本', '文書上でスクリプトを実行しています'),
    'Apply': ('应用', '適用'),
    'Deny': ('拒绝', '拒否'),
    '(the AI gave no description)': ('（AI 没有写说明）', '（AI からの説明はありません）'),
    'The AI wants to change this document with a script. It was tried on the open document — the file itself is not changed yet. The editor shows the result now.': (
        'AI 想用一段脚本修改这份文档。脚本已经在打开的文档上试跑过——文件本身还没有改动。编辑器里现在显示的是试跑的结果。',
        'AI がスクリプトでこの文書を変更しようとしています。開いている文書上で試しに実行済みで、ファイル自体はまだ変更されていません。エディタには今その結果が表示されています。'),
    'Lines of the text view that change: {n}': ('文字版里变化的行数：{n}', 'テキスト版で変わる行数：{n}'),
    'Script:': ('脚本：', 'スクリプト：'),
    'Change “{name}”?': ('要修改“{name}”吗？', '「{name}」を変更しますか？'),
    'Before': ('修改前', '変更前'),
    'After': ('修改后', '変更後'),
})

# 2026-11-11 (fourth part): several marks in one question are numbered
FEATURE_TRANSLATIONS.update({
    'Mark {n}': ('标记 {n}', 'マーク {n}'),
    '({mark} is the attached picture with “{mark}” written in its top left corner; the red line on it circles the part I mean, in {place})': (
        '（{mark} 指的是左上角写着“{mark}”的那张附图；图上红线圈出的就是我说的地方，位于 {place}）',
        '（{mark} は、左上に「{mark}」と書かれた添付画像です。画像の赤い線で囲んだ部分が対象で、場所は {place}）'),
})
