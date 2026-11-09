# -*- coding: utf-8 -*-
"""Translations for the 2026-11-09 multi-task coordination (the coordinator above the conversations,
the write gate, the shared pool; editor_handoff/PLAN_20261109_多任务统筹_写入通道.md).
Loaded by i18n/gen_ts.py (one table per feature)."""

FEATURE_TRANSLATIONS = {
    # the plan panel: a conversation the coordinator holds
    'Waiting: “{title}” is changing {files}': ('等待：「{title}」正在改 {files}', '待機中：「{title}」が {files} を変更中'),
    'Waiting for “{title}” to finish': ('等「{title}」做完', '「{title}」の完了待ち'),
    'the screen': ('屏幕', '画面'),
    'Re-planning: another conversation is changing what this plan relies on': (
        '重新规划：另一个对话正在改这份计划要用的东西', '再計画：この計画が頼る部分を別の会話が変更中です'),
    # a request handed to another running conversation
    'Added from the conversation “{title}” (Broccoli’s coordinator handed it over): {note}': (
        '来自对话「{title}」（Broccoli 的总调度转交过来）：{note}',
        '会話「{title}」から（Broccoli の総合調整が引き継ぎ）：{note}'),
    'Broccoli’s coordinator added a request from “{title}”.': (
        'Broccoli 的总调度加进来一个来自「{title}」的要求。', 'Broccoli の総合調整が「{title}」からの依頼を追加しました。'),
    # a held task starts with what the others did
    'Done before this task (in other conversations):': ('这个任务之前已经做完的（在别的对话里）：',
                                                         'このタスクの前に（別の会話で）済んだこと：'),
    'Files this task changes: {files}': ('这个任务要改的文件：{files}', 'このタスクが変更するファイル：{files}'),
    # the Agent's file tools (status lines)
    'Reading a file': ('正在读文件', 'ファイルを読んでいます'),
    'Changing a file': ('正在改文件', 'ファイルを変更しています'),
    'Reading what other tasks are doing': ('正在看别的任务在做什么', 'ほかのタスクの状況を確認しています'),
    # the write gate says why it did not write
    'Not written: “{name}” is being changed by another conversation right now.': (
        '没有写入：「{name}」正被另一个对话修改。', '書き込みませんでした：「{name}」は別の会話が変更中です。'),
    'Not written: “{name}” is being written by something else right now.': (
        '没有写入：「{name}」正在被别的操作写入。', '書き込みませんでした：「{name}」は別の処理が書き込み中です。'),
    '“{name}” was changed by someone else at the same place, so this change was not written. '
    'It will be redone from the current text.': (
        '「{name}」的同一处刚被别人改过，所以这次没有写入，会按现在的内容重做。',
        '「{name}」の同じ箇所が別の変更で書き換えられたため、今回の変更は書き込みませんでした。現在の内容からやり直します。'),
    '“{name}” no longer contains the text the AI wanted to change, so nothing was written.': (
        '「{name}」里已经没有 AI 要改的那段文字了，所以什么都没写。',
        '「{name}」には AI が変更しようとした文字がもうないため、何も書き込みませんでした。'),
    '“{name}” was changed by someone else, so it was not deleted.': (
        '「{name}」被别人改过了，所以没有删除。', '「{name}」は別の変更で書き換えられたため、削除しませんでした。'),
    # the editor's own save while a task writes the file
    '“{name}” is being changed by a running task right now, so it was not saved. Try again in a moment.': (
        '「{name}」正被一个运行中的任务修改，所以没有保存。请稍后再试。',
        '「{name}」は実行中のタスクが変更中のため、保存しませんでした。少し待ってからもう一度お試しください。'),
    # the editor's "fix"
    'Sent to a new conversation': ('已交给一个新对话', '新しい会話に送りました'),
    # Claude Code / Codex: Broccoli writes their changes
    '⏸ **Approve?** — {who} proposes these changes; Broccoli writes them (a copy of each file is kept first):': (
        '⏸ **是否批准？** — {who} 提出了下面这些修改，由 Broccoli 来写（写之前每个文件都会留一份原样）：',
        '⏸ **承認しますか？** — {who} が次の変更を提案しています。書き込むのは Broccoli です（書き込む前に各ファイルの元の内容を保存します）：'),
    '- Change: {path}': ('- 修改：{path}', '- 変更：{path}'),
    '- New file: {path}': ('- 新文件：{path}', '- 新しいファイル：{path}'),
    '- Delete: {path}': ('- 删除：{path}', '- 削除：{path}'),
    'Broccoli wrote {n} change(s); Claude Code is checking them…': (
        'Broccoli 写好了 {n} 处修改，Claude Code 正在检查…', 'Broccoli が {n} 件の変更を書き込みました。Claude Code が確認中…'),
    'Broccoli wrote {n} change(s); Codex is checking them…': (
        'Broccoli 写好了 {n} 处修改，Codex 正在检查…', 'Broccoli が {n} 件の変更を書き込みました。Codex が確認中…'),
    '[Broccoli wrote these files for Claude Code: {files}]': (
        '［Broccoli 替 Claude Code 写了这些文件：{files}］', '［Broccoli が Claude Code の代わりに書き込んだファイル：{files}］'),
    '[Broccoli wrote these files for Codex: {files}]': (
        '［Broccoli 替 Codex 写了这些文件：{files}］', '［Broccoli が Codex の代わりに書き込んだファイル：{files}］'),
    # group settings: what a watched file does
    "When a watched file changes, the model reads the change (with the instruction, if you wrote one) and splits it "
    "into tasks: each task is its own conversation in this group. They run at the same time unless they change the "
    "same files or one needs another's result — then they wait for each other. What the tasks write is not taken as "
    "a new change; a change you make while they run is picked up when they are done. Tasks stop at approvals unless "
    "Automatic approval is on.": (
        '被监听的文件一改动，模型就读这次改了什么（有说明就连说明一起），拆成几个任务：每个任务是这个分组里的一个对话。'
        '它们同时进行，除非要改同一个文件，或者一个要用另一个的结果——那样就互相等。任务自己写进去的内容不算新的改动；'
        '任务进行时你改的内容，会在它们做完后接着处理。除非开了自动批准，任务遇到批准会停下来等你。',
        '監視中のファイルが変わると、モデルが変更内容（説明があればそれも）を読んでタスクに分けます。各タスクはこのグループの'
        '会話の一つです。同じファイルを変更する場合や、ほかのタスクの結果が必要な場合を除き、同時に進みます（その場合は'
        '互いに待ちます）。タスク自身が書き込んだ内容は新しい変更として扱いません。タスクの実行中にあなたが加えた変更は、'
        'それらが終わってから処理します。自動承認がオフなら、タスクは承認のところで止まって待ちます。'),
    # ── the shared pool through the coordinator + the overview in the plan panel (snapshot 419) ──
    # status lines of the Agent's task board
    'Asking another task through the coordinator': ('正在通过总调度问另一个任务', '総合調整を通じてほかのタスクに質問しています'),
    'Answering another task through the coordinator': ('正在通过总调度回答另一个任务', '総合調整を通じてほかのタスクに回答しています'),
    'Telling the coordinator which files come next': ('正在告诉总调度接下来要改哪些文件', '次に変更するファイルを総合調整に伝えています'),
    # the plan list: a short reason in the row
    'waits for “{title}”': ('等「{title}」', '「{title}」待ち'),
    # the overview: sections and rows
    'In use': ('占用中', '使用中'),
    'Recent changes': ('最近改动', '最近の変更'),
    'Coordinator log': ('总调度记录', '総合調整の記録'),
    'No file is in use': ('没有文件被占用', '使用中のファイルはありません'),
    'No changes yet': ('还没有改动', 'まだ変更はありません'),
    'Nothing yet': ('还没有记录', 'まだ記録はありません'),
    'you': ('你', 'あなた'),
    'a task of another user': ('另一位用户的任务', 'ほかのユーザーのタスク'),
    'outside Broccoli': ('Broccoli 之外', 'Broccoli の外'),
    'deleted': ('已删除', '削除'),
    'renamed': ('已改名', '名前変更'),
    'new file': ('新文件', '新しいファイル'),
    'undone': ('已撤销', '取り消し済み'),
    'Being changed by “{title}”': ('正在被「{title}」修改', '「{title}」が変更中'),
    'Step {n}: {goal}': ('第 {n} 步：{goal}', 'ステップ {n}：{goal}'),
    'Waiting for it: {titles}': ('在等它的：{titles}', 'これを待っている：{titles}'),
    'Changed at {time} by {who}': ('{time} 由{who}修改', '{time} に{who}が変更'),
    # the coordinator log
    '“{a}” waits for “{b}” ({files})': ('「{a}」在等「{b}」（{files}）', '「{a}」が「{b}」を待っています（{files}）'),
    '“{a}” started after waiting {s} s': ('「{a}」等了 {s} 秒后开始', '「{a}」が {s} 秒待ってから開始'),
    'Coordinator decided for “{a}”: {decision}': ('总调度为「{a}」决定：{decision}', '総合調整が「{a}」について判断：{decision}'),
    'wait': ('排队等', '待つ'),
    'run alongside': ('一起跑', '並行して実行'),
    'hand over': ('并进对方', '相手に引き継ぐ'),
    'drop as a duplicate': ('重复了，取消', '重複のため取り消し'),
    're-plan': ('重新规划', '再計画'),
    '“{a}” gave back {files}': ('「{a}」放出了 {files}', '「{a}」が {files} を解放'),
    '“{a}” asked “{b}”: {question}': ('「{a}」问「{b}」：{question}', '「{a}」が「{b}」に質問：{question}'),
    '“{a}” answered “{b}”: {answer}': ('「{a}」回答「{b}」：{answer}', '「{a}」が「{b}」に回答：{answer}'),
    'Coordinator answered “{a}” from what it knows about “{b}”': (
        '总调度按它掌握的「{b}」的情况回答了「{a}」', '総合調整が「{b}」について把握している内容で「{a}」に回答'),
    '“{a}” reserved {files}': ('「{a}」预约了 {files}', '「{a}」が {files} を予約'),
    '“{a}” is next in line for {file} after “{b}”': ('「{a}」排在「{b}」后面等 {file}', '「{a}」が「{b}」の次に {file} を待っています'),
    '{files} passed to “{a}” (it asked for them)': ('{files} 交给了「{a}」（它先要的）', '{files} を「{a}」に渡しました（先に依頼したため）'),
    # the right-click menu and undoing one change
    'Undo This Change': ('撤销这次改动', 'この変更を取り消す'),
    'Show Whole Change': ('看完整改动', '変更全体を表示'),
    'Undo': ('撤销', '取り消す'),
    'Undo this change to “{name}”?': ('撤销对「{name}」的这次改动？', '「{name}」へのこの変更を取り消しますか？'),
    'Only this change ({time}) is taken back; what was changed later elsewhere in the file stays. A copy of the file is '
    'kept first.': ('只撤这一次（{time}）的改动；之后在文件别处的改动保留。撤之前会先留一份文件原样。',
                    'この変更（{time}）だけを取り消します。その後ファイルのほかの場所で行われた変更はそのまま残ります。取り消す前にファイルのコピーを保存します。'),
    '“{name}” is being changed by “{title}” right now. Undo the change when that task is done.': (
        '「{name}」正被「{title}」修改。等那个任务做完再撤销。', '「{name}」は「{title}」が変更中です。そのタスクが終わってから取り消してください。'),
    'Not undone': ('没有撤销', '取り消していません'),
    '“{name}” could not be changed back: {why}': ('「{name}」没能改回去：{why}', '「{name}」を元に戻せませんでした：{why}'),
    'The change could not be undone.': ('这次改动没能撤销。', 'この変更を取り消せませんでした。'),
    'This change cannot be undone.': ('这次改动不能撤销。', 'この変更は取り消せません。'),
    'This change is no longer in the record.': ('记录里已经没有这次改动了。', 'この変更は記録に残っていません。'),
    '“{name}” was renamed or moved again since, so this change cannot be undone.': (
        '「{name}」之后又被改名或挪动了，所以这次改动不能撤销。', '「{name}」はその後また名前変更か移動されたため、この変更は取り消せません。'),
    '“{name}” exists again, so it was not put back.': ('「{name}」又有了，所以没有放回去。', '「{name}」がまた存在するため、戻しませんでした。'),
    'No copy of “{name}” was kept, so this change cannot be undone.': (
        '没有留「{name}」的副本，所以这次改动不能撤销。', '「{name}」のコピーが残っていないため、この変更は取り消せません。'),
    '“{name}” no longer exists, so this change cannot be undone.': (
        '「{name}」已经不在了，所以这次改动不能撤销。', '「{name}」がもう存在しないため、この変更は取り消せません。'),
    '“{name}” is not a text file.': ('「{name}」不是文本文件。', '「{name}」はテキストファイルではありません。'),
    '“{name}” was changed again since, and the text right after this change was not kept, so it cannot be undone on '
    'its own.': ('「{name}」之后又被改过，而这次改动刚做完时的内容没有留下，所以没法单独撤销这一次。',
                 '「{name}」はその後また変更され、この変更直後の内容が残っていないため、この変更だけを取り消すことはできません。'),
    '“{name}” was changed since it was created, so it was not deleted.': (
        '「{name}」新建之后又被改过，所以没有删除。', '「{name}」は作成後に変更されたため、削除しませんでした。'),
    '“{name}” was changed again at the same place since, so this change was not undone.': (
        '「{name}」的同一处之后又被改过，所以这次改动没有撤销。', '「{name}」の同じ箇所がその後また変更されたため、この変更は取り消していません。'),
}
