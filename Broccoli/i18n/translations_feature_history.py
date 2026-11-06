# -*- coding: utf-8 -*-
"""Translations for History › Archive and Settings › General › Archive & delete history
(2026-10-28). Read by i18n/gen_ts.py (translations_feature_*.py). The shared source 'Delete'
keeps its own translation; the history menu item uses the new source 'Archive'
(zh 归档 — not 存档, the step archive uses that word —, ja アーカイブ)."""

FEATURE_TRANSLATIONS = {
    # history menu
    'Archive': ('归档', 'アーカイブ'),
    # the settings page
    'Archive & delete history': ('归档与彻底删除历史', 'アーカイブと履歴の完全削除'),
    'Archived conversations, and deleting conversations for good to free disk space.': (
        '已归档的对话，以及彻底删除对话来腾出磁盘空间。',
        'アーカイブした会話と、ディスクの空きを作るための会話の完全削除。'),
    'Search conversations': ('搜索对话', '会話を検索'),
    'Archived': ('已归档', 'アーカイブ済み'),
    '30+ days old': ('30 天以前', '30日以上前'),
    '90+ days old': ('90 天以前', '90日以上前'),
    '1+ year old': ('1 年以前', '1年以上前'),
    'Title': ('标题', 'タイトル'),
    'Updated': ('更新日期', '更新日'),
    'Size': ('大小', 'サイズ'),
    'Restore': ('恢复', '復元'),
    'Delete permanently…': ('彻底删除…', '完全に削除…'),
    'Task running': ('任务运行中', 'タスク実行中'),
    'Queued': ('排队中', '待機中'),
    'Running remotely': ('远程运行中', 'リモートで実行中'),
    'Group: {name}': ('分组：{name}', 'グループ：{name}'),
    'Device: {name}': ('设备：{name}', 'デバイス：{name}'),
    'This Mac': ('这台 Mac', 'このMac'),
    'Not fully deleted': ('未删完', '削除しきれず'),
    'In history': ('在历史中', '履歴に表示'),
    'Stop the task first': ('请先停止任务', '先にタスクを停止してください'),
    'Counting…': ('正在统计…', '集計中…'),
    '{archived} archived · {archived_size}  |  {total} on this Mac · {total_size}': (
        '已归档 {archived} 个 · {archived_size}  |  本机共 {total} 个 · {total_size}',
        'アーカイブ済み {archived} 件 · {archived_size}  |  このMacに {total} 件 · {total_size}'),
    '{n} selected · {size}': ('已选 {n} 个 · {size}', '{n} 件選択 · {size}'),
    '{n} restored': ('已恢复 {n} 个', '{n} 件を復元しました'),
    # the delete question (system alert)
    'Delete {n} conversations permanently?': ('彻底删除这 {n} 个对话？', 'この {n} 件の会話を完全に削除しますか？'),
    'Delete this conversation permanently?': ('彻底删除这个对话？', 'この会話を完全に削除しますか？'),
    'This frees {size}. The attachments, run logs and task records go too, and so does the copy '
    'in iCloud — on every device. This cannot be undone.': (
        '将释放 {size}。附件、运行日志和任务记录一起删除，iCloud 里的副本也会删除——所有设备上都不再有。此操作无法撤销。',
        '{size} が空きます。添付ファイル、実行ログ、タスク記録も一緒に削除され、iCloud のコピーも削除されます（すべてのデバイスから）。元に戻せません。'),
    '{size} of it are auto-approve backups. “Delete, keep backups” leaves them in the '
    'backup folder.': (
        '其中 {size} 是自动批准备份。选「删除，保留备份」会把它们留在备份文件夹里。',
        'そのうち {size} は自動承認のバックアップです。「削除（バックアップは残す）」を選ぶとバックアップフォルダに残ります。'),
    'Delete, keep backups': ('删除，保留备份', '削除（バックアップは残す）'),
    # progress / result line
    'Deleting… {done} of {total}': ('正在删除… {done} / {total}', '削除中… {done} / {total}'),
    'Deleted {n} · freed {size}': ('已删除 {n} 个，释放 {size}', '{n} 件を削除 · {size} を解放'),
    '{n} not fully deleted ({reasons}); they stay archived, try again later': (
        '{n} 个没删完（{reasons}），仍保持归档，可稍后再试',
        '{n} 件は削除しきれませんでした（{reasons}）。アーカイブのまま残っています。後でもう一度お試しください'),
    '{n} skipped: a task started': ('{n} 个已跳过：任务开始运行了', '{n} 件をスキップ：タスクが始まりました'),
    'the iCloud copy could not be deleted': ('iCloud 副本删不掉', 'iCloud のコピーを削除できませんでした'),
    'a cached copy could not be deleted': ('缓存副本删不掉', 'キャッシュのコピーを削除できませんでした'),
    'the attachments could not be deleted': ('附件删不掉', '添付ファイルを削除できませんでした'),
    'a search file could not be deleted': ('检索文件删不掉', '検索用ファイルを削除できませんでした'),
    'the auto-approve backups could not be deleted': ('自动批准备份删不掉', '自動承認のバックアップを削除できませんでした'),
    'a run log could not be deleted': ('运行日志删不掉', '実行ログを削除できませんでした'),
    'the task records could not be deleted': ('任务记录删不掉', 'タスク記録を削除できませんでした'),
    'the conversation file could not be deleted': ('对话文件删不掉', '会話ファイルを削除できませんでした'),
    'a reference to it could not be cleared': ('有一处引用没清掉', '参照を一部消せませんでした'),
    'something could not be deleted': ('有内容删不掉', '一部を削除できませんでした'),
}

FEATURE_EXTRA_SOURCE_STRINGS = []
