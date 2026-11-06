# -*- coding: utf-8 -*-
"""Translations for the 2026-10-30 change: usage bars above the blue strip, read from CodexBar
(one colored bar per AI subscription, red from 80 %; Settings › General › Usage).
Loaded by i18n/gen_ts.py (one table per feature)."""

FEATURE_TRANSLATIONS = {
    # Settings › General › Usage
    'Usage': ('用量', '使用量'),
    'Bars above the window showing how much of each AI subscription is used (from CodexBar).': (
        '窗口上方的用量条：每个 AI 订阅用了多少（数据来自 CodexBar）。',
        'ウインドウ上部のバーで、各 AI サブスクリプションの使用量を表示します（CodexBar から取得）。'),
    'Show usage bars above the window': ('在窗口上方显示用量条', 'ウインドウ上部に使用量バーを表示'),
    'One bar per AI subscription above the blue strip: how much of it is used, read from CodexBar '
    'every 5 minutes while the window is open. Each provider has its own color; from 80 % its bar '
    'turns red. Hover a bar for the details, click it to come here.': (
        '蓝条上方每个 AI 订阅一根条，显示已经用了多少；窗口开着时每 5 分钟从 CodexBar 读一次。'
        '每家有自己的颜色，用到 80% 起整根条变红。鼠标停在条上看详情，点一下回到这一页。',
        '青いバーの上に AI サブスクリプションごとに 1 本のバーを表示し、使用量を示します。ウインドウが開いている間、'
        '5 分ごとに CodexBar から読み取ります。プロバイダごとに色が決まっていて、80% に達するとバー全体が赤になります。'
        'バーにポインタを置くと詳細、クリックするとこのページを開きます。'),
    'Bar {n}': ('第 {n} 条', 'バー {n}'),
    '(none)': ('（无）', '（なし）'),
    'Usage bar color': ('用量条颜色', '使用量バーの色'),
    'This color is too close to the red that marks a bar at 80 % or more, so it could not tell you '
    'when a provider is nearly used up. Choose another one.': (
        '这个颜色和"用到 80% 以上"的红色太像，到时候就看不出哪家快用完了。请换一个颜色。',
        'この色は「80% 以上」を示す赤に近すぎるため、使い切りそうなときに見分けられません。別の色を選んでください。'),
    'Window': ('窗口', '期間'),
    'Automatic (the fuller one)': ('自动（显示用得更多的那个）', '自動（使用率の高いほう）'),
    '5 hours': ('5 小时', '5 時間'),
    'Weekly': ('每周', '毎週'),
    'Show': ('显示', '表示'),
    'Always': ('一直显示', '常に表示'),
    'Only when one is close to its limit': ('有一家快用完时', 'どれかが上限に近いときだけ'),
    'When the mouse is over the blue strip': ('鼠标停在蓝条上时', '青いバーにポインタを置いたとき'),
    'There is no daily quota: providers count a 5-hour window and a weekly one. Automatic shows the '
    'fuller of the two, marked 5h or wk. A provider without the chosen window shows the one it has. '
    'Without a choice above, the first providers CodexBar has turned on are shown.': (
        '没有"每日"额度：各家算的是 5 小时窗口和每周窗口。"自动"显示两个里用得更多的那个，并标上 5h 或"周"。'
        '某家没有你选的那种窗口时，显示它有的那个。上面一个都不选时，显示 CodexBar 里开着的前几家。',
        '「1 日あたり」の上限はありません。各プロバイダは 5 時間の枠と毎週の枠で数えます。「自動」は使用率の高いほうを'
        '表示し、5h または「週」の印を付けます。選んだ枠がないプロバイダは、持っている枠を表示します。上で何も選ばない'
        'ときは、CodexBar でオンになっている最初のプロバイダを表示します。'),
    'Refresh now': ('立即刷新', '今すぐ更新'),
    'Reading…': ('正在读取…', '読み取り中…'),
    'Not read yet.': ('还没读过。', 'まだ読み取っていません。'),
    'Built in: CodexBar {version} by Peter Steinberger · licence: {licence}': (
        '自带：CodexBar {version}，作者 Peter Steinberger · 许可证：{licence}',
        '内蔵：CodexBar {version}（作者 Peter Steinberger）· ライセンス：{licence}'),
    'Reading with the CodexBar built into Broccoli ({version}). Turn providers on and sign in under Usage '
    'providers, the next page.': (
        '正在用 Broccoli 内置的 CodexBar（{version}）读取。开关供应商、登录，在下一页"Usage providers"里。',
        'Broccoli 内蔵の CodexBar（{version}）で読み取っています。プロバイダのオン／オフとサインインは次のページ'
        '「Usage providers」で行います。'),
    'This copy of Broccoli does not include CodexBar.': ('这个 Broccoli 没有内置 CodexBar。', 'この Broccoli には CodexBar が含まれていません。'),
    'Turn it on and sign in under Settings › General › Usage providers.': (
        '到 设置 › General ›「Usage providers」里打开它并登录。',
        '設定 › General ›「Usage providers」でオンにしてサインインしてください。'),
    # Settings › General › Usage providers
    'Usage providers': ('用量供应商', '使用量プロバイダ'),
    'Turn on the providers the usage bars read, and sign them in (built-in CodexBar).': (
        '打开用量条要读的供应商，并在这里登录（内置 CodexBar）。',
        '使用量バーが読み取るプロバイダをオンにして、サインインします（内蔵 CodexBar）。'),
    'Every provider the built-in CodexBar can read; nothing else to install. Turn on the ones you use: those '
    'signed in through a command-line tool on this Mac (Codex, Claude Code, Gemini CLI…) need nothing more; '
    'for an API provider save its key; for one you use in a browser, import the sign-in.': (
        '内置 CodexBar 能读的全部供应商，不用另外安装任何东西。打开你在用的那几家：用本机已登录的命令行工具的'
        '（Codex、Claude Code、Gemini CLI…）什么都不用做；按量付费的 API 填上 key；在浏览器里用的，导入浏览器的登录。',
        '内蔵 CodexBar が読み取れるすべてのプロバイダです。ほかに何もインストールする必要はありません。使っているものを'
        'オンにしてください。この Mac でサインイン済みのコマンドラインツール（Codex、Claude Code、Gemini CLI…）を使う'
        'ものはそのままで構いません。API のプロバイダはキーを保存し、ブラウザで使うものはサインインを取り込みます。'),
    'Search providers': ('搜索供应商', 'プロバイダを検索'),
    'Provider': ('供应商', 'プロバイダ'),
    'Reading': ('读数', '使用量'),
    'No reading': ('没读到', '読み取れず'),
    'Turn on': ('打开', 'オンにする'),
    'Turn off': ('关闭', 'オフにする'),
    'Sign in: {name}': ('登录：{name}', 'サインイン：{name}'),
    'Select one provider to sign it in.': ('选中一家供应商，就可以给它登录。', 'サインインするプロバイダを 1 つ選んでください。'),
    'Import sign-in from browser': ('从浏览器导入登录', 'ブラウザからサインインを取り込む'),
    "macOS asks once whether CodexBar may read the browser's saved sign-ins: click Always Allow. "
    'For Safari, Broccoli needs Full Disk Access (System Settings › Privacy & Security).': (
        'macOS 会问一次是否允许 CodexBar 读取浏览器保存的登录，点"始终允许"。Safari 的话，要给 Broccoli'
        '"完全磁盘访问权限"（系统设置 › 隐私与安全性）。',
        'CodexBar がブラウザに保存されたサインイン情報を読むことを許可するか、macOS が一度だけ確認します。「常に許可」を'
        'クリックしてください。Safari の場合は、Broccoli に「フルディスクアクセス」が必要です（システム設定 › '
        'プライバシーとセキュリティ）。'),
    'Save key': ('保存 key', 'キーを保存'),
    'Remove key': ('删除 key', 'キーを削除'),
    "Importing the sign-in for {name}… If macOS asks whether CodexBar may use the browser's saved data, "
    'click Always Allow.': (
        '正在导入 {name} 的登录… 如果 macOS 问是否允许 CodexBar 使用浏览器保存的数据，点"始终允许"。',
        '{name} のサインインを取り込んでいます… CodexBar がブラウザの保存データを使うことを macOS が確認してきたら、'
        '「常に許可」をクリックしてください。'),
    'Working on {names}…': ('正在处理 {names}…', '{names} を処理しています…'),
    '{name}: done.': ('{name}：好了。', '{name}：完了しました。'),
    '{name}: done — {line}': ('{name}：好了，{line}', '{name}：完了 — {line}'),
    '{name}: done, but nothing could be read yet — {reason}': (
        '{name}：设好了，但还读不到 — {reason}', '{name}：設定しましたが、まだ読み取れません — {reason}'),
    '{name}: did not work — {reason}': ('{name}：没成功 — {reason}', '{name}：うまくいきませんでした — {reason}'),
    # hover text of a bar / a provider's paragraph on the page
    '{window}: {percent}% used · resets {time}': ('{window}：已用 {percent}%，{time} 重置', '{window}：{percent}% 使用 · {time} にリセット'),
    '{window}: {percent}% used': ('{window}：已用 {percent}%', '{window}：{percent}% 使用'),
    '{window}: no reading': ('{window}：没有读数', '{window}：データなし'),
    '{days} d {hours} h left': ('还有 {days} 天 {hours} 小时', 'あと {days} 日 {hours} 時間'),
    '{hours} h {minutes} min left': ('还有 {hours} 小时 {minutes} 分', 'あと {hours} 時間 {minutes} 分'),
    '{minutes} min left': ('还有 {minutes} 分', 'あと {minutes} 分'),
    '{hours} hours': ('{hours} 小时', '{hours} 時間'),
    '{minutes} minutes': ('{minutes} 分钟', '{minutes} 分'),
    'Other': ('其他', 'その他'),
    'Could not read it just now: {reason}': ('刚才没读到：{reason}', 'さきほど読み取れませんでした：{reason}'),
    'No reading yet.': ('还没有读数。', 'まだデータがありません。'),
    'Updated just now': ('刚刚更新', 'たった今更新'),
    'Updated {minutes} min ago': ('{minutes} 分钟前更新', '{minutes} 分前に更新'),
    'Updated {hours} h ago': ('{hours} 小时前更新', '{hours} 時間前に更新'),
    # the small mark after a bar's percentage: which window it shows
    '{hours}h': ('{hours}h', '{hours}h'),
    'wk': ('周', '週'),
}
