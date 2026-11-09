# -*- coding: utf-8 -*-
"""Translations for online memory sync (2026-11-09): the source window's empty web area, and the
sync status sentences. The status is stored in English and translated when shown
(online_memory_status_text, table ONLINE_MEMORY_STATUS_TEMPLATES in the main file) — through a
variable, so the templates are listed in FEATURE_EXTRA_SOURCE_STRINGS too.
Loaded by i18n/gen_ts.py (one table per feature)."""

FEATURE_TRANSLATIONS = {
    # the online memory source window (Settings › Memory › Memory endpoints › Open status)
    '(no URL)': ('（没有网址）', '（URL なし）'),
    'No read URL yet. Fill in “Read URL / file” on the Memory endpoints page of Settings.': (
        '还没有读取网址。请在设置的「记忆端点」页填写「读取 URL / 文件」。',
        'まだ読み取り URL がありません。設定の「メモリエンドポイント」ページで「読み取り URL / ファイル」を入力してください。'),
    'No write URL yet. Fill in “Write URL / file” on the Memory endpoints page of Settings.': (
        '还没有写入网址。请在设置的「记忆端点」页填写「写入 URL / 文件」。',
        'まだ書き込み URL がありません。設定の「メモリエンドポイント」ページで「書き込み URL / ファイル」を入力してください。'),
    # sync status sentences (ONLINE_MEMORY_STATUS_TEMPLATES)
    'Cleaning extracted memory...': ('正在清理提取到的记忆…', '抽出したメモリを整理中…'),
    'Merging with local memory...': ('正在与本机记忆合并…', 'ローカルのメモリと統合中…'),
    'Reading memory file...': ('正在读取记忆文件…', 'メモリファイルを読み込み中…'),
    'Writing memory file...': ('正在写入记忆文件…', 'メモリファイルに書き込み中…'),
    'Sending memory part {part}/{total}...': ('正在发送记忆第 {part}/{total} 段…', 'メモリを送信中（{part}/{total}）…'),
    'Opening read URL...': ('正在打开读取网址…', '読み取り URL を開いています…'),
    'Opening write URL...': ('正在打开写入网址…', '書き込み URL を開いています…'),
    'Read skipped: file path is empty.': ('跳过读取：没有填文件路径。', '読み取りをスキップ：ファイルのパスが空です。'),
    'Write skipped: file path is empty.': ('跳过写入：没有填文件路径。', '書き込みをスキップ：ファイルのパスが空です。'),
    'Read skipped: read URL is empty.': ('跳过读取：没有填读取网址。', '読み取りをスキップ：読み取り URL が空です。'),
    'Extracting read page text...': ('正在提取读取页上的文字…', '読み取りページのテキストを抽出中…'),
    'Write skipped: write method is disabled.': ('跳过写入：写入方式已关闭。', '書き込みをスキップ：書き込み方法がオフです。'),
    'Write skipped: write URL is empty.': ('跳过写入：没有填写入网址。', '書き込みをスキップ：書き込み URL が空です。'),
    'Target is busy ({reason}); nothing was sent. Retrying in {minutes} min (attempt {attempt}/{max}).': (
        '目标页正忙（{reason}），什么都没发送。{minutes} 分钟后重试（第 {attempt}/{max} 次）。',
        '書き込み先が処理中です（{reason}）。何も送信していません。{minutes} 分後に再試行します（{attempt}/{max} 回目）。'),
    'Memory exceeds the input limit; sending in {count} parts...': (
        '记忆超过输入框的字数上限，分 {count} 段发送…',
        'メモリが入力の上限を超えているため、{count} 回に分けて送信中…'),
    'This source is already syncing.': ('这个来源正在同步。', 'このソースはすでに同期中です。'),
    'Push skipped: local memory is empty.': ('跳过推送：本机记忆是空的。', 'プッシュをスキップ：ローカルのメモリが空です。'),
    'Cleaner failed, used raw extraction: {error}': (
        '清理失败，改用未清理的提取结果：{error}',
        '整理に失敗したため、抽出したままの内容を使いました：{error}'),
    'Cleaner failed, used raw extraction.': (
        '清理失败，改用未清理的提取结果。',
        '整理に失敗したため、抽出したままの内容を使いました。'),
    'Merge failed, used remote memory: {error}': (
        '合并失败，改用网页上的记忆：{error}',
        '統合に失敗したため、Web 側のメモリを使いました：{error}'),
    'Merge failed, used remote memory.': ('合并失败，改用网页上的记忆。', '統合に失敗したため、Web 側のメモリを使いました。'),
    'Read failed: URL did not load.': ('读取失败：网址没有打开。', '読み取り失敗：URL を読み込めませんでした。'),
    'Read failed: no memory text was extracted.': ('读取失败：没有提取到记忆文字。', '読み取り失敗：メモリのテキストを抽出できませんでした。'),
    'Read failed: chat page did not enable Send ({reason}).': (
        '读取失败：对话页的发送按钮没有亮起（{reason}）。',
        '読み取り失敗：チャットページの送信ボタンが有効になりませんでした（{reason}）。'),
    'Read failed: {error}': ('读取失败：{error}', '読み取り失敗：{error}'),
    'File write complete.': ('文件已写好。', 'ファイルへの書き込みが完了しました。'),
    'File write failed: {error}': ('写入文件失败：{error}', 'ファイルへの書き込み失敗：{error}'),
    'Write skipped: the target stayed busy through {max} retries; nothing was sent.': (
        '跳过写入：目标页重试 {max} 次都还在忙，什么都没发送。',
        '書き込みをスキップ：{max} 回再試行しても書き込み先が処理中のままだったため、何も送信していません。'),
    'Write failed: URL did not load.': ('写入失败：网址没有打开。', '書き込み失敗：URL を読み込めませんでした。'),
    'Write failed: chat page did not enable Send ({reason}).': (
        '写入失败：对话页的发送按钮没有亮起（{reason}）。',
        '書き込み失敗：チャットページの送信ボタンが有効になりませんでした（{reason}）。'),
    'Sending memory to write URL...': ('正在把记忆发到写入网址…', 'メモリを書き込み URL に送信中…'),
    'Pull failed: no memory text was extracted.': ('拉取失败：没有提取到记忆文字。', 'プル失敗：メモリのテキストを抽出できませんでした。'),
    'Asking chat page for memory...': ('正在向对话页要记忆…', 'チャットページにメモリを問い合わせ中…'),
    'Write sent. Check the web page if confirmation is needed.': (
        '已发送写入。如果需要确认，请到网页上看一下。',
        '書き込みを送信しました。確認が必要な場合は Web ページを見てください。'),
    'Pulled to local memory.': ('已拉取到本机记忆。', 'ローカルのメモリにプルしました。'),
    'Waiting for chat response...': ('正在等对话页回答…', 'チャットの返答を待っています…'),
    'Read complete.': ('读取完成。', '読み取り完了。'),
    'Read skipped: the chat page is busy ({reason}); it is read again on the next sync.': (
        '跳过读取：对话页正忙（{reason}），下次同步时再读。',
        '読み取りをスキップ：チャットページが処理中です（{reason}）。次回の同期で読み直します。'),
}

# translated through a variable (_tr(template)), invisible to the _tr('literal') extractor
FEATURE_EXTRA_SOURCE_STRINGS = [
    'Cleaning extracted memory...',
    'Merging with local memory...',
    'Reading memory file...',
    'Writing memory file...',
    'Sending memory part {part}/{total}...',
    'Opening read URL...',
    'Opening write URL...',
    'Read skipped: file path is empty.',
    'Write skipped: file path is empty.',
    'Read skipped: read URL is empty.',
    'Extracting read page text...',
    'Write skipped: write method is disabled.',
    'Write skipped: write URL is empty.',
    'Target is busy ({reason}); nothing was sent. Retrying in {minutes} min (attempt {attempt}/{max}).',
    'Memory exceeds the input limit; sending in {count} parts...',
    'This source is already syncing.',
    'Push skipped: local memory is empty.',
    'Cleaner failed, used raw extraction: {error}',
    'Cleaner failed, used raw extraction.',
    'Merge failed, used remote memory: {error}',
    'Merge failed, used remote memory.',
    'Read failed: URL did not load.',
    'Read failed: no memory text was extracted.',
    'Read failed: chat page did not enable Send ({reason}).',
    'Read failed: {error}',
    'File write complete.',
    'File write failed: {error}',
    'Write skipped: the target stayed busy through {max} retries; nothing was sent.',
    'Write failed: URL did not load.',
    'Write failed: chat page did not enable Send ({reason}).',
    'Sending memory to write URL...',
    'Pull failed: no memory text was extracted.',
    'Asking chat page for memory...',
    'Write sent. Check the web page if confirmation is needed.',
    'Pulled to local memory.',
    'Waiting for chat response...',
    'Read complete.',
    'Read skipped: the chat page is busy ({reason}); it is read again on the next sync.',
]
