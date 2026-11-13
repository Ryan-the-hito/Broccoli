# -*- coding: utf-8 -*-
"""Translations for the 2026-11-11 change: a plan step that could not do its work says so in the
answer's step block and in the plan rows — a tool with no model in Settings › Models, and a Web
search step whose model answered without searching. (The text the models read stays English.)
Loaded by i18n/gen_ts.py (one table per feature)."""

FEATURE_TRANSLATIONS = {
    # {label} = the tool's name as the Models page shows it, e.g. "Web search"
    'This step did not run: no model is set for {label} (Settings › Models).': (
        '这一步没有执行：{label}没有设置模型（设置 › 模型）。',
        'このステップは実行されませんでした：{label} のモデルが設定されていません（設定 › モデル）。'),
    'No web search was performed in this step: the model set for Web search answered without searching.': (
        '这一步没有进行网页搜索：为网页搜索设置的模型没有搜索，直接作答了。',
        'このステップではウェブ検索は行われませんでした：ウェブ検索に設定されたモデルが検索せずに回答しました。'),
}
