# -*- coding: utf-8 -*-
"""Translations for subscription sign-ins (2026-11-12): the bundled CLIProxyAPI and
Settings › Models › Subscriptions. Loaded by i18n/gen_ts.py."""

FEATURE_TRANSLATIONS = {
    'Subscriptions': ('订阅', 'サブスクリプション'),
    'Sign in to an AI subscription and use its models as profiles, without an API key.': (
        '登录 AI 订阅，把它的模型当作配置来用，不需要 API 密钥。',
        'AI のサブスクリプションにサインインして、API キーなしでそのモデルをプロファイルとして使います。'),
    'Broccoli runs a small proxy on this Mac only. Sign in to a subscription in your browser, and its models can be added as ordinary profiles. The sign-in stays on this Mac. Providers may not allow their subscriptions to be used this way: an account can be limited or closed for it.': (
        'Broccoli 只在这台 Mac 上运行一个小代理。在浏览器里登录订阅后，它的模型就能加成普通的配置。登录信息只留在这台 Mac 上。各家服务不一定允许这样使用订阅：账号可能因此被限制或停用。',
        'Broccoli はこの Mac の中だけで小さなプロキシを動かします。ブラウザでサブスクリプションにサインインすると、そのモデルを普通のプロファイルとして追加できます。サインイン情報はこの Mac にだけ残ります。この使い方を認めていない事業者もあり、アカウントが制限・停止されることがあります。'),
    'Subscription': ('订阅', 'サブスクリプション'),
    'Account': ('账号', 'アカウント'),
    'Not signed in': ('未登录', '未サインイン'),
    'Sign in': ('登录', 'サインイン'),
    'Sign out': ('退出登录', 'サインアウト'),
    'Add models…': ('添加模型…', 'モデルを追加…'),
    'Add models as profiles': ('把模型加为配置', 'モデルをプロファイルとして追加'),
    'Move': ('转过来', '移す'),
    'Move VibeProxy profiles here': ('把 VibeProxy 的配置转过来', 'VibeProxy のプロファイルを移す'),
    'Profiles that go through a VibeProxy installed on this Mac (localhost:8317) are pointed at this proxy instead. Sign in to the same subscriptions here first.': (
        '把经过这台 Mac 上已装的 VibeProxy（localhost:8317）的配置，改成走这个代理。请先在这里登录同样的订阅。',
        'この Mac に入っている VibeProxy（localhost:8317）経由のプロファイルを、このプロキシ経由に切り替えます。先にここで同じサブスクリプションにサインインしてください。'),
    'CLIProxyAPI {version} · licence: {licence}': ('CLIProxyAPI {version} · 许可证：{licence}', 'CLIProxyAPI {version} · ライセンス：{licence}'),
    'Not running: it starts when you sign in.': ('没有运行：登录时会自动启动。', '停止中：サインインすると起動します。'),
    'Waiting for the sign-in to {name} in your browser…': ('正在等你在浏览器里登录 {name}…', 'ブラウザでの {name} へのサインインを待っています…'),
    'The sign-in to {name} did not finish.': ('{name} 的登录没有完成。', '{name} へのサインインが完了しませんでした。'),
    'Nobody signed in within {minutes} minutes.': ('{minutes} 分钟内没有完成登录。', '{minutes} 分以内にサインインされませんでした。'),
    'The proxy gave no sign-in page.': ('代理没有给出登录页面。', 'プロキシからサインインページが返されませんでした。'),
    'The proxy listed no models.': ('代理没有列出任何模型。', 'プロキシからモデルが返されませんでした。'),
    'Every model of your sign-ins is a profile already.': ('已登录订阅的模型都已经是配置了。', 'サインイン済みのモデルはすべてプロファイルになっています。'),
    'Sign out of {name} ({account})? Profiles that use its models stop working until you sign in again.': (
        '退出 {name}（{account}）的登录吗？用到它的模型的配置会停用，直到你重新登录。',
        '{name}（{account}）からサインアウトしますか？ そのモデルを使うプロファイルは、もう一度サインインするまで使えません。'),
    "{count} profiles go through VibeProxy (localhost:8317). Point them at Broccoli's own proxy instead? A model works only if you are signed in to its subscription here.": (
        '有 {count} 个配置经过 VibeProxy（localhost:8317）。改成走 Broccoli 自带的代理吗？只有在这里登录了对应订阅的模型才能用。',
        '{count} 個のプロファイルが VibeProxy（localhost:8317）を経由しています。Broccoli 内蔵のプロキシ経由に切り替えますか？ ここで該当のサブスクリプションにサインインしているモデルだけが使えます。'),
    'This copy of Broccoli does not include the subscription proxy.': ('这份 Broccoli 没有带订阅代理。', 'この Broccoli にはサブスクリプション用プロキシが含まれていません。'),
    'Subscription sign-ins need macOS {version} or later.': ('订阅登录需要 macOS {version} 或更高版本。', 'サブスクリプションのサインインには macOS {version} 以降が必要です。'),
    'The subscription proxy could not be started: {error}': ('订阅代理无法启动：{error}', 'サブスクリプション用プロキシを起動できませんでした：{error}'),
    'The subscription proxy did not start.': ('订阅代理没有启动。', 'サブスクリプション用プロキシが起動しませんでした。'),
    'The subscription proxy stopped unexpectedly.': ('订阅代理意外停止了。', 'サブスクリプション用プロキシが予期せず停止しました。'),
    'The subscription proxy is not running.': ('订阅代理没有运行。', 'サブスクリプション用プロキシは動いていません。'),
}
