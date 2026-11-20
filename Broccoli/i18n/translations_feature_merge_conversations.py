# -*- coding: utf-8 -*-
"""Translations for merging conversations (2026-11-15; History › select several › Merge).
Loaded by i18n/gen_ts.py (one table per feature)."""

FEATURE_TRANSLATIONS = {
    # the line where a merged block starts (style book 5.7.9)
    'From “{title}”': ('来自《{title}》', '「{title}」より'),
    'From “{title}” · {date}': ('来自《{title}》· {date}', '「{title}」より · {date}'),
    # the history list
    'Merge {n} conversations…': ('合并 {n} 个对话…', '{n} 件の会話を統合…'),
    'Merging…': ('正在合并…', '統合中…'),
    # the confirmation and notices
    'Merge conversations': ('合并对话', '会話を統合'),
    'Merge {n} conversations into one?': ('把这 {n} 个对话合并成一个？', 'この {n} 件の会話を 1 つに統合しますか？'),
    'They become one new conversation, in this order (oldest first):\n\n{titles}\n\n'
    'The originals are archived, not deleted. You can restore them in '
    'Settings › General › Archive & delete history.': (
        '它们会变成一个新对话，顺序如下（最早的在前）：\n\n{titles}\n\n'
        '原对话只归档、不删除，可以在 设置 › 通用 ›「归档与彻底删除历史」里恢复。',
        '次の順番（古い順）で 1 つの新しい会話になります：\n\n{titles}\n\n'
        '元の会話はアーカイブされるだけで、削除されません。設定 › 一般 ›「アーカイブと履歴の完全削除」から復元できます。'),
    'One of these conversations is still running, has questions waiting or a remote task. '
    'Merge them when it has finished.': (
        '其中一个对话还在运行、有排队的问题或远程任务。等它结束后再合并。',
        'この中に、実行中・質問が待機中・リモートタスク中の会話があります。終わってから統合してください。'),
    'One of these conversations could not be read.': ('其中一个对话读取不了。', 'この中に読み込めない会話があります。'),
    'The conversations could not be merged. Nothing was changed.': (
        '合并没有成功，什么都没有改动。', '統合できませんでした。何も変更されていません。'),
}
