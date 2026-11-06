# 2026-10-28 任务胶囊：流式生成、长对话分段、分享窗口里的进度 / 失败原因 / 重试。
FEATURE_TRANSLATIONS = {
    # 进度（分享窗口生成中显示）
    'Preparing the conversation…': ('正在整理对话…', '会話を整理しています…'),
    'Generating Task Capsule…': ('正在生成任务胶囊…', 'タスクカプセルを生成しています…'),
    'Long conversation: writing notes for {total} sections first.': (
        '对话较长：先分 {total} 段写段落笔记。',
        '会話が長いため、まず {total} 区間に分けてメモを作成します。'),
    'Section notes done: {done} of {total}': ('段落笔记已完成：{done} / {total}', '区間メモ完了：{done} / {total}'),
    '{count} sections reused from the cache': ('{count} 段直接用了缓存', '{count} 区間はキャッシュを再利用'),
    'Combining section notes: {done} of {total}': ('正在合并段落笔记：{done} / {total}', '区間メモを統合中：{done} / {total}'),
    'Writing the Task Capsule from {total} section notes…': (
        '正在根据 {total} 段笔记写任务胶囊…', '{total} 区間のメモからタスクカプセルを作成しています…'),
    '{count} characters received': ('已收到 {count} 字', '{count} 文字受信済み'),
    'Closing this window cancels the generation.': ('关闭此窗口会取消生成。', 'このウィンドウを閉じると生成を中止します。'),
    # 失败原因 + 建议
    'The model did not finish in time (limits: {seconds} seconds without any data, {minutes} minutes per request).': (
        '模型没有在限定时间内完成（上限：{seconds} 秒没有收到任何数据，或单次请求超过 {minutes} 分钟）。',
        'モデルが時間内に完了しませんでした（上限：データが {seconds} 秒届かない、または 1 回のリクエストが {minutes} 分を超える）。'),
    'Press Retry. If it keeps timing out, choose a faster model or raise the profile timeout in Settings.': (
        '请按“重试”。如果一直超时，请在设置里换一个更快的模型，或调高该配置的超时时间。',
        '「再試行」を押してください。タイムアウトが続く場合は、設定でより速いモデルを選ぶか、プロファイルのタイムアウトを長くしてください。'),
    'The conversation is too long for this model.': ('对话太长，超出了这个模型能处理的长度。', '会話が長すぎて、このモデルでは処理できません。'),
    'Choose a model with a larger context window in Settings, then press Retry.': (
        '请在设置里换一个上下文更长的模型，然后按“重试”。',
        '設定でコンテキストの長いモデルを選んでから「再試行」を押してください。'),
    'Set up an API profile in Settings, then press Retry.': (
        '请先在设置里配置 API，然后按“重试”。',
        '設定で API プロファイルを設定してから「再試行」を押してください。'),
    'Press Retry. If the answer stays empty, try another model.': (
        '请按“重试”。如果还是没有内容，请换一个模型。',
        '「再試行」を押してください。それでも空の場合は別のモデルをお試しください。'),
    'Task Capsule generation was cancelled.': ('任务胶囊生成已取消。', 'タスクカプセルの生成を中止しました。'),
    'Press Retry to start again.': ('按“重试”重新开始。', '「再試行」を押すともう一度始めます。'),
    'Check the network connection and the API profile, then press Retry.': (
        '请检查网络连接和 API 配置，然后按“重试”。',
        'ネットワーク接続と API プロファイルを確認してから「再試行」を押してください。'),
    'Details:': ('详情：', '詳細：'),
}

FEATURE_EXTRA_SOURCE_STRINGS = []
