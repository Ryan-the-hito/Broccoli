# -*- coding: utf-8 -*-
"""Translations for the 2026-11-09 change: while an @target (Claude Code, Codex, a web AI) works,
the Agent output area is headed with its own name instead of "Running MCP tools...".
Loaded by i18n/gen_ts.py (one table per feature)."""

FEATURE_TRANSLATIONS = {
    # heading above the status lines, e.g. "Running @claude..."
    'Running @{alias}...': ('@{alias} 运行中...', '@{alias} を実行中...'),
    # the same when the target has no name
    'Running the @ target...': ('@ 目标运行中...', '@ ターゲットを実行中...'),
}
