# Connected apps (2026-10-29): the built-in Open Connector — Settings › Connected apps, its
# console window and its status lines.
FEATURE_TRANSLATIONS = {
    'Connected apps': ('已连接的应用', '連携アプリ'),
    'Let the AI read from and act in the apps you connect, through the built-in Open Connector.': (
        '通过内置的 Open Connector，让 AI 读取你连接的应用，并在里面操作。',
        '内蔵の Open Connector を通じて、連携したアプリを AI が読み取り、操作できるようにします。'),
    'Let the AI use the apps you connect': ('让 AI 使用你连接的应用', '連携したアプリを AI に使わせる'),
    'Broccoli runs Open Connector on this Mac only. Connect an app once — paste its key, or sign in — '
    'and while answering the AI can read from it and act in it: GitHub issues, Notion pages and about a '
    'thousand other apps, plus public sources such as Hacker News or arXiv that need no account. Keys stay '
    'on this Mac, encrypted, with the encryption key in your keychain; the AI never sees them.': (
        'Broccoli 只在这台 Mac 上运行 Open Connector。应用只需连接一次（粘贴它的密钥，或登录一次），之后 AI 回答时'
        '就能读取它、在里面操作：GitHub 的议题、Notion 的页面，以及另外约一千个应用；还有 Hacker News、arXiv '
        '这类不需要账号的公开来源。密钥只留在这台 Mac 上并加密保存，加密用的钥匙存在你的钥匙串里；AI 永远看不到它们。',
        'Broccoli は Open Connector をこの Mac 上だけで動かします。アプリは一度連携するだけ（キーを貼り付けるか、'
        '一度サインインする）で、回答中に AI がそのアプリを読み取り、操作できます。GitHub の Issue、Notion のページ、'
        'ほかにも約 1,000 のアプリ、さらにアカウント不要の Hacker News や arXiv などの公開ソースにも対応します。'
        'キーはこの Mac に暗号化して保存され、暗号化のキーはキーチェーンに入ります。AI がキーを見ることはありません。'),
    'Finding apps and actions runs without asking. An action that changes something — sending, creating, '
    'deleting — asks you first, and "Always" covers only that one action. Apps that use a key or a token '
    'work right away; apps you sign in to on a web page (Gmail, Slack, Google…) need an OAuth app of your '
    'own on this self-hosted connector. Needs "MCP tools" to be on (External context & MCP).': (
        '查找应用和动作不会询问你。会改动东西的动作（发送、创建、删除）会先问你，选“总是允许”也只对那一个动作有效。'
        '用密钥或令牌的应用可以直接用；要在网页上登录的应用（Gmail、Slack、Google 等）在这个本机运行的连接器上，'
        '需要你自己的 OAuth 应用。需要先打开“MCP 工具”（外部上下文与 MCP 页）。',
        'アプリや操作を探すときは確認しません。何かを変更する操作（送信・作成・削除）は先に確認し、「常に許可」も'
        'その操作だけに効きます。キーやトークンを使うアプリはすぐに使えます。Web ページでサインインするアプリ'
        '（Gmail、Slack、Google など）は、このローカルのコネクタでは自分の OAuth アプリが必要です。'
        '「MCP ツール」をオンにしておく必要があります（外部コンテキストと MCP）。'),
    'Open console': ('打开控制台', 'コンソールを開く'),
    'Open Connector {version} by OOMOL · licence: {licence}': (
        'Open Connector {version}（OOMOL）· 许可证：{licence}',
        'Open Connector {version}（OOMOL）· ライセンス：{licence}'),
    'Starting…': ('正在启动…', '起動しています…'),
    'Not running. Turn it on above and click Save.': (
        '没有运行。在上面打开开关，再点保存。',
        '実行していません。上のスイッチをオンにして、保存をクリックしてください。'),
    'Signed in: {apps}': ('已登录：{apps}', 'サインイン済み：{apps}'),
    'No app signed in yet: open the console to connect one. Public sources work already.': (
        '还没有登录任何应用：打开控制台去连接一个。公开来源现在就能用。',
        'まだサインインしているアプリはありません。コンソールを開いて連携してください。公開ソースはすでに使えます。'),
    'Running on this Mac (port {port})': ('正在这台 Mac 上运行（端口 {port}）', 'この Mac で実行中（ポート {port}）'),
    'This Mac · port {port}': ('本机 · 端口 {port}', 'この Mac · ポート {port}'),
    'This copy of Broccoli does not include Open Connector.': (
        '这份 Broccoli 没有包含 Open Connector。',
        'この Broccoli には Open Connector が含まれていません。'),
    'The keychain could not be read, so Open Connector was not started.': (
        '读不到钥匙串，所以没有启动 Open Connector。',
        'キーチェーンを読み取れなかったため、Open Connector を起動しませんでした。'),
    'Open Connector could not be started: {error}': (
        'Open Connector 无法启动：{error}',
        'Open Connector を起動できませんでした：{error}'),
    'Open Connector did not start.': ('Open Connector 没有启动起来。', 'Open Connector が起動しませんでした。'),
    'Open Connector stopped unexpectedly.': ('Open Connector 意外停止了。', 'Open Connector が予期せず停止しました。'),
}
