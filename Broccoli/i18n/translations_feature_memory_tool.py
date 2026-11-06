# -*- coding: utf-8 -*-
"""Translations for the 2026-11-05 change: a fixed way to remember — the answer's memory tool
(broccoli_memory) and the /remember slash command, both writing only the 📌 section of
permanent memory. Loaded by i18n/gen_ts.py (one table per feature)."""

FEATURE_TRANSLATIONS = {
    # heading of the 📌 section in Settings → Memory
    'Remembered at your request (edit or delete freely)': (
        '你让我记住的（可直接修改或删除）',
        '覚えておくよう頼まれたこと（自由に編集・削除できます）'),
    # the lines under an answer / the /remember reply
    'Saved to permanent memory: {text}': ('已记入永久记忆：{text}', '永続メモリに保存しました：{text}'),
    'Already in permanent memory: {text}': ('永久记忆里已有：{text}', '永続メモリに保存済みです：{text}'),
    'Removed from permanent memory: {text}': ('已从永久记忆删除：{text}', '永続メモリから削除しました：{text}'),
    # status line while the answer uses the tool
    'Updating permanent memory': ('正在更新永久记忆', '永続メモリを更新中'),
    # /remember: slash menu, empty message, save failure
    'Save to permanent memory': ('存进永久记忆', '永続メモリに保存'),
    'Type what to remember after {command}.': ('请在 {command} 后输入要记住的内容。', '{command} の後に覚えておく内容を入力してください。'),
    'Saving to permanent memory failed': ('存入永久记忆失败', '永続メモリへの保存に失敗しました'),
    # /forget: slash menu, empty message, the reply lines, failure
    'Remove from permanent memory': ('从永久记忆删除', '永続メモリから削除'),
    'Type what to forget after {command}.': ('请在 {command} 后输入要删除的内容。', '{command} の後に削除する内容を入力してください。'),
    'Several saved lines match "{text}"; nothing was removed. Send {command} with one whole line:': (
        '有好几条都对得上「{text}」，一条都没删。请用 {command} 加上其中完整的一条：',
        '「{text}」に一致する行が複数あるため、削除していません。{command} の後にどれか 1 行をそのまま入力してください：'),
    'Nothing in the 📌 section matches: {text}': ('📌 小节里没有对得上的：{text}', '📌 セクションに一致する行がありません：{text}'),
    'Your own text in permanent memory can be changed in Settings → Memory.': (
        '永久记忆里你自己写的部分，请在 设置 → 记忆 里修改。',
        '永続メモリのうちご自身で書いた部分は、設定 → メモリ で変更できます。'),
    'Removing from permanent memory failed': ('从永久记忆删除失败', '永続メモリからの削除に失敗しました'),
}
