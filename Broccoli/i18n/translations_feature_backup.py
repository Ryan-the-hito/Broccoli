# -*- coding: utf-8 -*-
"""Translations for the 2026-10-28 change: terminal command backups copied on a worker thread,
no copy for read-only commands, reuse of an unchanged earlier copy, size cap (Settings ›
Automatic approval). Loaded by i18n/gen_ts.py (one table per feature)."""

FEATURE_TRANSLATIONS = {
    # plan step title while the copy runs (shown through _tr(title))
    'Backing up before the command': ('命令执行前正在备份', 'コマンド実行前にバックアップ中'),
    # status line in the run preview
    'Backing up files before the command…': ('正在备份命令要改动的文件…', 'コマンドが変更するファイルをバックアップ中…'),
    # approval dialog, under "Backup:"
    'Too large to back up automatically (more than {size}). Approve to run without a backup.': (
        '太大，无法自动备份（超过 {size}）。批准则不备份直接运行。',
        '大きすぎるため自動でバックアップできません（{size} 超）。承認するとバックアップなしで実行します。'),
    'The backup failed ({error}). Approve to run without a backup.': (
        '备份失败（{error}）。批准则不备份直接运行。',
        'バックアップに失敗しました（{error}）。承認するとバックアップなしで実行します。'),
    # Settings › General › Automatic approval
    'Largest backup (MB)': ('备份上限（MB）', 'バックアップ上限（MB）'),
    'Bigger than this, nothing is copied: the command asks for your approval instead and says why. '
    'Read-only commands are never copied; a folder copied earlier in the same task and unchanged '
    'since is not copied again. Default 500 MB.': (
        '超过这个大小就不复制：这条命令改为请你批准，并说明原因。只读命令从不复制；同一个任务里'
        '先前复制过、之后没变的文件夹不会再复制。默认 500 MB。',
        'これより大きい場合はコピーしません。代わりにコマンドが理由を添えて承認を求めます。読み取り専用の'
        'コマンドはコピーしません。同じタスク内で以前コピーし、その後変わっていないフォルダは再コピーしません。'
        '既定は 500 MB。'),
}

# passed to _tr() through a variable (plan step titles are stored in English)
FEATURE_EXTRA_SOURCE_STRINGS = [
    'Backing up before the command',
]
