# -*- coding: utf-8 -*-
"""Translations for the models of a conversation / group (2026-11-09; style book 5.7.4,
editor_handoff/PLAN_20261109_对话专属模型.md). Loaded by i18n/gen_ts.py (one table per feature)."""

FEATURE_TRANSLATIONS = {
    # where it opens
    '🧠 Models': ('🧠 模型', '🧠 モデル'),
    'Models…': ('模型…', 'モデル…'),
    # the two kinds of agent
    'Main agent': ('主 Agent', 'メインエージェント'),
    'Sub agent': ('小 Agent', 'サブエージェント'),
    'The plan steps that only write text use it; a tool with no model of its own uses it too. Empty = Default chat.': (
        '计划里只写文字的步骤用它；没设模型的工具也用它。不选 = 用默认聊天。',
        '文章だけを書く計画のステップが使います。モデル未設定のツールもこれを使います。空欄 = 既定のチャット。'),
    # a dropdown that follows the layer below
    'Follow default': ('跟随默认', '既定に従う'),
    'Follow Settings: {model}': ('跟随设置：{model}', '設定に従う：{model}'),
    'Follow group: {model}': ('跟随分组：{model}', 'グループに従う：{model}'),
    'Follow Default chat: {model}': ('跟随默认聊天：{model}', '既定のチャットに従う：{model}'),
    'Follow Sub agent: {model}': ('跟随小 Agent：{model}', 'サブエージェントに従う：{model}'),
    'Follow Planner / Router: {model}': ('跟随规划器：{model}', 'プランナーに従う：{model}'),
    'Follow Browser Use: {model}': ('跟随 Browser Use：{model}', 'Browser Use に従う：{model}'),
    '(not on this Mac)': ('（这台 Mac 没有）', '（この Mac にはありません）'),
    # the map's hover tag
    'From: this conversation': ('来自：这个对话', '設定元：この会話'),
    'From: group “{name}”': ('来自：分组「{name}」', '設定元：グループ「{name}」'),
    'From: this group': ('来自：这个分组', '設定元：このグループ'),
    'From: Settings': ('来自：设置', '設定元：設定'),
    'Not on this Mac: {name}': ('这台 Mac 没有：{name}', 'この Mac にはありません：{name}'),
    'Blocked here, uses {model}': ('在这里被屏蔽，会用 {model}', 'ここでは使用不可、{model} を使います'),
    'Also does: {steps}': ('也做：{steps}', 'ほかにも担当：{steps}'),
    # the panel
    'applies from the next question': ('下一问起生效', '次の質問から反映'),
    'Follow defaults for all': ('全部跟随默认', 'すべて既定に従う'),
    'Follow defaults': ('跟随默认', '既定に従う'),
    'In a group: follow the group; otherwise follow Settings.': (
        '在分组里时跟随分组，不在时跟随设置。', 'グループ内ではグループに、それ以外は設定に従います。'),
    'Clear every model this conversation chose itself? It then follows its group, or Settings.': (
        '清掉这个对话自己选的所有模型？之后跟随它所在的分组或设置。',
        'この会話が自分で選んだモデルをすべて消しますか？以後はグループか設定に従います。'),
    # the group dialog's Models page
    'Follow Settings for all': ('全部跟随设置', 'すべて設定に従う'),
    'Follow Settings': ('跟随设置', '設定に従う'),
    "Clear every model this group chose? Its conversations then follow Settings (a conversation's own choices stay).": (
        '清掉这个分组选的所有模型？组里的对话之后跟随设置（对话自己选的不变）。',
        'このグループが選んだモデルをすべて消しますか？会話は以後、設定に従います（会話自身の選択はそのまま）。'),
}
