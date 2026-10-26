#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate Qt Linguist .ts files for Broccoli's UI translation.

The app wraps every user-visible English string with _tr('...') which resolves
through QCoreApplication.translate('Broccoli', text). pylupdate6 cannot follow
that wrapper, so this script IS the extractor: it reads the _tr() literals out
of Broccoli_26new.py with ast, joins them with the TRANSLATIONS table below and
emits i18n/broccoli_zh_CN.ts + i18n/broccoli_ja_JP.ts. A source string missing
from the table is emitted as type="unfinished" (the UI then falls back to the
English source text — nothing breaks).

Usage:
    python3 i18n/gen_ts.py            # regenerate the two .ts files
    lrelease i18n/broccoli_zh_CN.ts   # compile to .qm (repeat for ja_JP)
"""
import ast
import os
import sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, '..', 'Broccoli_26new.py')
CONTEXT = 'Broccoli'

# Strings translated through a VARIABLE (_tr(label)) rather than a literal, so
# the ast extractor cannot see them. Keep in sync with the source tables noted.
EXTRA_SOURCE_STRINGS = [
    # SPECIALIZED_CAPABILITIES labels — Models page rows (table stays English
    # at the source because the engine writes these labels into records).
    'Task reasoning', 'Web search', 'Text to speech', 'Speech to text',
    'Image generation', 'Video generation', 'Video to text', 'Terminal command',
    # ICLOUD_FEATURE_FLAG_SPECS labels + tooltips — Settings page 3 rows
    # (passed to _tr() through variables; keep in sync with the spec table).
    'Keep every conversation field on save',
    'Crash-safe conversation saves',
    'Collision-proof conversation IDs',
    'Only one Broccoli per data folder',
    'Keep caches out of conversation records',
    'Task ledger (crash recovery)',
    'Single task-completion path',
    'Rename-safe conversation identity',
    'Connect devices through iCloud',
    'Send a new conversation to another device',
    'Move existing conversations between devices',
    'Control tasks running on other devices',
    'Apple Notes mirror + iPhone Shortcuts',
    'One history across all devices',
    'Approve high-risk actions remotely (not recommended)',
]

# {english_source: (zh_CN, ja_JP)} — placeholders like {v} / %d must survive.
TRANSLATIONS = {
    # ---- Move & Send UI (R4a/R4b) ----
    '🎛️ Move to': ('🎛️ Move to', '🎛️ Move to'),
    '🎛️ Move to failed': ('🎛️ Move to 失败', '🎛️ Move to 失敗'),
    'Remote device': ('远程设备', 'リモートデバイス'),
    'Choose the device that will own and run this new conversation.': (
        '选择将拥有并运行这段新对话的设备。',
        'この新しい会話を所有して実行するデバイスを選んでください。'),
    'Existing-conversation ownership migration is disabled.': (
        '已有对话的所有权迁移当前已关闭。',
        '既存会話の所有権移動は現在無効です。'),
    'Migrating conversation; waiting for the target to verify every asset.': (
        '正在迁移对话；等待目标设备校验全部资源。',
        '会話を移動中。ターゲットが全アセットを検証するのを待っています。'),
    'Migration blocked': ('迁移被阻止', '移動はブロックされました'),
    'Conversation moved to {device}. It now lives and runs there.': (
        '对话已迁移到 {device}，之后都在那台设备上保存和运行。',
        '会話を {device} に移動しました。今後はそちらで保存・実行されます。'),
    '{device} rejected the migration ({reason}). The conversation stays on this Mac.': (
        '{device} 拒绝了这次迁移（{reason}）。对话仍留在这台 Mac 上。',
        '{device} が移動を拒否しました（{reason}）。会話はこの Mac に残ります。'),
    '{device} did not answer in time, so the migration was cancelled. The conversation stays on this Mac.': (
        '{device} 没有及时回应，迁移已取消。对话仍留在这台 Mac 上。',
        '{device} から時間内に応答がなかったため、移動をキャンセルしました。会話はこの Mac に残ります。'),
    # ---- iCloud remote tasks: status card, picker, errors (codes worded here) ----
    'Moving request…': ('正在发送请求…', 'リクエストを送信中…'),
    'Waiting for target device…': ('正在等待目标设备…', '送信先デバイスを待っています…'),
    'Running remotely…': ('正在远程运行…', 'リモートで実行中…'),
    'Syncing answer…': ('正在同步回答…', '回答を同期中…'),
    'Remote answer synced': ('远程回答已同步', 'リモートの回答を同期しました'),
    'Queued on the target device; it runs after the current task there…': (
        '已在目标设备上排队，等它那边当前的任务结束后运行…',
        '送信先デバイスで順番待ちです。向こうの現在のタスクが終わると実行されます…'),
    'Cancellation requested; waiting for target confirmation…': (
        '已请求取消，正在等待目标设备确认…', 'キャンセルを依頼しました。送信先デバイスの確認を待っています…'),
    'Remote task cancelled': ('远程任务已取消', 'リモートタスクをキャンセルしました'),
    'Remote task needs reconciliation': ('远程任务需要人工核对', 'リモートタスクは確認が必要です'),
    'Remote task failed': ('远程任务失败', 'リモートタスクが失敗しました'),
    'online': ('在线', 'オンライン'),
    'offline': ('离线', 'オフライン'),
    'not responding': ('无响应', '応答なし'),
    'shutting down': ('正在退出', '終了中'),
    'busy': ('忙碌', 'ビジー'),
    'active attempt': ('正在运行的任务', '実行中のタスク'),
    'pending approval': ('待处理的批准', '保留中の承認'),
    'dirty editor buffer': ('编辑器里有未保存的修改', 'エディタの未保存の変更'),
    'iCloud remote tasks are turned off.': ('iCloud 远程任务已关闭。', 'iCloud リモートタスクはオフです。'),
    'Type a question or add an attachment first.': ('请先输入问题或添加附件。', '先に質問を入力するか、添付ファイルを追加してください。'),
    'Remote tasks are turned off on {device}.': ('{device} 上的远程任务已关闭。', '{device} ではリモートタスクがオフです。'),
    'This conversation has no owner device to continue on.': (
        '这段对话没有可以接着运行的所属设备。', 'この会話には続きを実行する所有デバイスがありません。'),
    'This Mac owns the conversation; it runs here.': ('这段对话归这台 Mac，会在这里运行。', 'この会話はこの Mac のものなので、ここで実行されます。'),
    'An attachment could not be read: {name}': ('无法读取附件：{name}', '添付ファイルを読み込めません：{name}'),
    'Could not write to iCloud Drive: {detail}': ('无法写入 iCloud 云盘：{detail}', 'iCloud Drive に書き込めませんでした：{detail}'),
    '{device} refused the task.': ('{device} 拒绝了这个任务。', '{device} がタスクを拒否しました。'),
    '{device} reported a failure without details.': ('{device} 报告失败，但没有给出细节。', '{device} から失敗の報告がありましたが、詳細はありません。'),
    '{device} did not pick up the request within {minutes} minutes (asleep, offline, or iCloud is not syncing). The request has expired and will not run later.': (
        '{device} 在 {minutes} 分钟内没有接收请求（可能在睡眠、离线，或 iCloud 没有同步）。请求已过期，之后也不会再执行。',
        '{device} が {minutes} 分以内にリクエストを受け取りませんでした（スリープ中、オフライン、または iCloud が同期していない可能性があります）。リクエストは期限切れで、後から実行されることはありません。'),
    '{device} quit while running this task.': ('{device} 在运行这个任务时退出了。', '{device} はこのタスクの実行中に終了しました。'),
    'Lost contact with {device}: no response for {minutes} minutes. If it finishes later, the answer will appear in History.': (
        '与 {device} 失去联系：已经 {minutes} 分钟没有回应。如果它之后跑完，回答会出现在历史记录里。',
        '{device} との接続が途切れました：{minutes} 分間応答がありません。後で完了した場合、回答は履歴に表示されます。'),
    'Cancellation requested; waiting for {device} to confirm.': ('已请求取消，正在等待 {device} 确认。', 'キャンセルを依頼しました。{device} の確認を待っています。'),
    'The request expired before {device} picked it up.': ('请求在 {device} 接收之前就过期了。', '{device} が受け取る前にリクエストの期限が切れました。'),
    'Interrupted: Broccoli on {device} quit or restarted before the task finished.': (
        '已中断：{device} 上的 Broccoli 在任务完成前退出或重启了。',
        '中断されました：タスクが終わる前に {device} の Broccoli が終了または再起動しました。'),
    '{device} does not support this kind of task.': ('{device} 不支持这类任务。', '{device} はこの種類のタスクに対応していません。'),
    '{device} refused a malformed new-conversation request.': ('{device} 拒绝了一个格式不对的新对话请求。', '{device} は形式が正しくない新規会話リクエストを拒否しました。'),
    'The conversation is not available on {device}.': ('{device} 上没有这段对话。', 'この会話は {device} にありません。'),
    '{device} no longer owns the conversation; it moved to another device.': (
        '这段对话已不归 {device}，它已经搬到别的设备上了。', 'この会話はもう {device} のものではありません。別のデバイスに移動しました。'),
    'Remote tasks are not ready on {device} yet; try again in a moment.': (
        '{device} 上的远程任务还没准备好，请稍后再试。', '{device} のリモートタスクはまだ準備ができていません。少し待ってから再試行してください。'),
    'No response for {minutes} min. A request will wait up to {limit} min, then expire.': (
        '已经 {minutes} 分钟没有回应。请求最多等待 {limit} 分钟，之后过期。',
        '{minutes} 分間応答がありません。リクエストは最大 {limit} 分待ってから期限切れになります。'),
    'Default Profile will be used': ('将使用默认 Profile', 'デフォルトの Profile を使います'),
    'Default Profile is running on the target device.': ('目标设备正在用默认 Profile 运行。', '送信先デバイスはデフォルトの Profile で実行しています。'),
    'The copy here was not the newest; the device answered on its latest version.': (
        '这里的副本不是最新的；目标设备是在它最新的内容上回答的。', 'ここのコピーは最新ではありませんでした。デバイスは最新の内容に基づいて回答しました。'),
    '{count} more queued here; they are sent after this answer.': (
        '这里还有 {count} 条在排队，会在这个回答之后发送。', 'ここでさらに {count} 件が順番待ちです。この回答の後に送信されます。'),
    'Migration blocked by {blockers}.': ('无法迁移：{blockers}。', '移動できません：{blockers}。'),
    'A file of this conversation is missing: {name}': ('这段对话缺少一个文件：{name}', 'この会話のファイルが見つかりません：{name}'),
    'The conversation to move could not be found.': ('找不到要迁移的对话。', '移動する会話が見つかりません。'),
    'Only the device that owns this conversation can move it.': ('只有拥有这段对话的设备才能迁移它。', 'この会話を移動できるのは、所有しているデバイスだけです。'),
    'Choose another device as the destination.': ('请选择另一台设备作为目标。', '移動先には別のデバイスを選んでください。'),
    'Another move of this conversation is already in progress.': ('这段对话已经有另一次迁移在进行。', 'この会話は別の移動がすでに進行中です。'),
    'Saving the conversation took too long; try the move again.': ('保存对话用时过长，请重新迁移。', '会話の保存に時間がかかりすぎました。もう一度移動してください。'),
    'The conversation changed after the move started; cancel it and try again.': (
        '迁移开始后对话又有改动，请取消后重试。', '移動の開始後に会話が変更されました。キャンセルしてやり直してください。'),
    'The saved state of this move is damaged; cancel it and try again.': (
        '这次迁移保存的状态已损坏，请取消后重试。', 'この移動の保存状態が壊れています。キャンセルしてやり直してください。'),
    'This Mac already owns the conversation.': ('这段对话已经归这台 Mac。', 'この会話はすでにこの Mac のものです。'),
    'The conversation already lives on that device.': ('这段对话已经在那台设备上了。', 'この会話はすでにそのデバイスにあります。'),
    'This conversation is being moved to another device; changes wait until the move finishes.': (
        '这段对话正在迁移到另一台设备，修改要等迁移完成。', 'この会話は別のデバイスへ移動中です。変更は移動が終わるまで待機します。'),
    'The target device': ('目标设备', '送信先デバイス'),
    'its files did not finish syncing in time': ('它的文件没有及时同步完', 'ファイルの同期が時間内に終わりませんでした'),
    'a file arrived damaged': ('有文件传过来时已损坏', '届いたファイルが壊れていました'),
    'another move of this conversation is in progress': ('这段对话已有另一次迁移在进行', 'この会話の別の移動が進行中です'),
    'the move data did not match': ('迁移数据对不上', '移動データが一致しませんでした'),
    'the conversation changed during the move': ('迁移过程中对话有改动', '移動中に会話が変更されました'),
    'it does not have this conversation': ('它那里没有这段对话', 'その会話を持っていません'),
    'it no longer owns this conversation': ('这段对话已不归它', 'その会話をもう所有していません'),
    'the destination is not valid': ('目标设备无效', '移動先が無効です'),
    'the request expired': ('请求已过期', 'リクエストの期限が切れました'),
    'a file of the conversation is missing there': ('它那里缺少对话的文件', '向こうで会話のファイルが見つかりません'),
    'saving took too long there': ('它那里保存用时过长', '向こうで保存に時間がかかりすぎました'),
    'it could not write to iCloud Drive': ('它无法写入 iCloud 云盘', 'iCloud Drive に書き込めませんでした'),
    'its saved move state is damaged': ('它保存的迁移状态已损坏', '保存された移動状態が壊れています'),
    'it declined': ('它拒绝了', '拒否されました'),
    'Remote conversation': ('远程对话', 'リモートの会話'),
    'Migrated conversation': ('迁移来的对话', '移動してきた会話'),
    'Question': ('问题', '質問'),
    'Answer': ('回答', '回答'),
    # ---- Settings > iCloud remote tasks: switch tooltips (read from ICLOUD_FEATURE_FLAG_SPECS) ----
    'Storage engine: unknown or newly added record fields survive every save. Leave ON. (M1a · BROCCOLI_M1A_SCHEMA)': (
        '存储引擎：记录里未知的或新加的字段在每次保存时都会保留。请保持开启。（M1a · BROCCOLI_M1A_SCHEMA）',
        'ストレージエンジン：未知のフィールドや新しく追加されたフィールドも保存のたびに残ります。オンのままにしてください。（M1a · BROCCOLI_M1A_SCHEMA）'),
    'Storage engine: write to a temporary file, then swap it in atomically, so a crash can never truncate a conversation. Leave ON. (M1a · BROCCOLI_M1A_ATOMIC_WRITE)': (
        '存储引擎：先写入临时文件再整体替换，崩溃也不会把对话写坏一半。请保持开启。（M1a · BROCCOLI_M1A_ATOMIC_WRITE）',
        'ストレージエンジン：一時ファイルに書いてから一度に置き換えるので、クラッシュしても会話が途中で切れることはありません。オンのままにしてください。（M1a · BROCCOLI_M1A_ATOMIC_WRITE）'),
    'Storage engine: new conversations get unique IDs instead of second-precision timestamps that could collide. Leave ON. (M1a · BROCCOLI_M1A_UUID_IDS)': (
        '存储引擎：新对话使用唯一编号，而不是可能撞车的秒级时间戳。请保持开启。（M1a · BROCCOLI_M1A_UUID_IDS）',
        'ストレージエンジン：新しい会話には、重複しうる秒単位のタイムスタンプではなく一意の ID を付けます。オンのままにしてください。（M1a · BROCCOLI_M1A_UUID_IDS）'),
    'Storage engine: a second Broccoli process cannot write the same data folder at the same time. Leave ON. (M1a · BROCCOLI_M1A_SINGLE_INSTANCE)': (
        '存储引擎：第二个 Broccoli 进程不能同时写同一个数据文件夹。请保持开启。（M1a · BROCCOLI_M1A_SINGLE_INSTANCE）',
        'ストレージエンジン：2 つ目の Broccoli プロセスは同じデータフォルダに同時に書き込めません。オンのままにしてください。（M1a · BROCCOLI_M1A_SINGLE_INSTANCE）'),
    'Storage engine: search/render caches live in their own files, so background work never rewrites a conversation. Leave ON. (M1a · BROCCOLI_M1A_DERIVED_STORAGE)': (
        '存储引擎：搜索和渲染缓存放在单独的文件里，后台工作不会重写对话。请保持开启。（M1a · BROCCOLI_M1A_DERIVED_STORAGE）',
        'ストレージエンジン：検索・描画のキャッシュは別ファイルに置くので、バックグラウンド処理が会話を書き換えることはありません。オンのままにしてください。（M1a · BROCCOLI_M1A_DERIVED_STORAGE）'),
    'Storage engine: every run is recorded in a local ledger so tasks, queues and approvals survive a restart. Leave ON. (M1b · BROCCOLI_M1B_SHADOW_TASK_STORE)': (
        '存储引擎：每次运行都记在本机任务账本里，任务、排队和批准在重启后仍然保留。请保持开启。（M1b · BROCCOLI_M1B_SHADOW_TASK_STORE）',
        'ストレージエンジン：実行はすべてローカルの台帳に記録されるので、タスク・キュー・承認は再起動後も残ります。オンのままにしてください。（M1b · BROCCOLI_M1B_SHADOW_TASK_STORE）'),
    'Storage engine: every run finishes through one finalizer, and pending approvals block completion. Leave ON. (M1c · BROCCOLI_M1C_UNIFIED_FINALIZER)': (
        '存储引擎：每次运行都经由同一个收尾流程结束，有未处理的批准时不会算作完成。请保持开启。（M1c · BROCCOLI_M1C_UNIFIED_FINALIZER）',
        'ストレージエンジン：実行はすべて 1 つの終了処理を通り、未処理の承認があると完了になりません。オンのままにしてください。（M1c · BROCCOLI_M1C_UNIFIED_FINALIZER）'),
    'Storage engine: conversations are found by their ID, not their file path, so rename and migration cannot orphan them. Leave ON. (M2 · BROCCOLI_M2_CONVERSATION_RESOLVER)': (
        '存储引擎：按编号而不是文件路径找对话，改名和迁移都不会让它丢失。请保持开启。（M2 · BROCCOLI_M2_CONVERSATION_RESOLVER）',
        'ストレージエンジン：会話はファイルパスではなく ID で探すので、名前変更や移動で迷子になりません。オンのままにしてください。（M2 · BROCCOLI_M2_CONVERSATION_RESOLVER）'),
    'Master switch: register this device in the shared iCloud folder and exchange tasks, events and files with your other Broccolis. Everything below needs this. (M3 · BROCCOLI_M3_TRANSPORT)': (
        '总开关：把这台设备登记到共享的 iCloud 文件夹，与你其他设备上的 Broccoli 交换任务、事件和文件。下面所有功能都依赖它。（M3 · BROCCOLI_M3_TRANSPORT）',
        'マスタースイッチ：このデバイスを共有 iCloud フォルダに登録し、他のデバイスの Broccoli とタスク・イベント・ファイルをやり取りします。以下の機能はすべてこれが必要です。（M3 · BROCCOLI_M3_TRANSPORT）'),
    'Adds “🎛️ Move to” to the Send menu: a brand-new conversation starts and runs on the device you pick. (M4a · BROCCOLI_M4A_MOVE_SEND)': (
        '在发送菜单里加入"🎛️ Move to"：新对话会在你选的设备上开始并运行。（M4a · BROCCOLI_M4A_MOVE_SEND）',
        '送信メニューに「🎛️ Move to」を追加します：新しい会話は選んだデバイスで始まり、実行されます。（M4a · BROCCOLI_M4A_MOVE_SEND）'),
    'A whole conversation — history, branches, files — moves to the device that will run it, and can move back later. (M4b · BROCCOLI_M4B_MIGRATION)': (
        '整段对话（历史、分支、文件）都搬到负责运行它的设备上，之后也能再搬回来。（M4b · BROCCOLI_M4B_MIGRATION）',
        '会話全体（履歴・ブランチ・ファイル）を実行するデバイスへ移動し、後で戻すこともできます。（M4b · BROCCOLI_M4B_MIGRATION）'),
    'Stop, queue, follow-ups and comments reach the executing device as events; it confirms before anything is shown as done. (M5 · BROCCOLI_M5_REMOTE_LIFECYCLE)': (
        '停止、排队、追问和批注都以事件形式送到执行设备；它确认后才会显示为完成。（M5 · BROCCOLI_M5_REMOTE_LIFECYCLE）',
        '停止・キュー・追加質問・コメントはイベントとして実行デバイスに届き、確認されてから完了と表示されます。（M5 · BROCCOLI_M5_REMOTE_LIFECYCLE）'),
    'Tasks sent from an iPhone Shortcut also write their finished answer into Apple Notes for reading on the phone. (M6 · BROCCOLI_M6_NOTES_SHORTCUTS)': (
        '从 iPhone 快捷指令发来的任务，完成后的回答也会写进 Apple 备忘录，方便在手机上阅读。（M6 · BROCCOLI_M6_NOTES_SHORTCUTS）',
        'iPhone のショートカットから送ったタスクは、完成した回答を Apple メモにも書き込み、iPhone で読めるようにします。（M6 · BROCCOLI_M6_NOTES_SHORTCUTS）'),
    'History and search include the cloud conversations of all your devices, each conversation listed once. (M7 · BROCCOLI_M7_UNIFIED_HISTORY)': (
        '历史和搜索包含你所有设备在云端的对话，每段对话只列一次。（M7 · BROCCOLI_M7_UNIFIED_HISTORY）',
        '履歴と検索に全デバイスのクラウド上の会話を含め、各会話は 1 回だけ表示します。（M7 · BROCCOLI_M7_UNIFIED_HISTORY）'),
    'Terminal commands, file edits and MCP writes normally must be approved on the Mac that executes them. Leave OFF unless you know exactly why. (BROCCOLI_REMOTE_HIGH_PRIVILEGE_APPROVAL)': (
        '终端命令、文件修改和 MCP 写操作通常必须在执行它们的那台 Mac 上批准。除非你确切知道为什么，否则请保持关闭。（BROCCOLI_REMOTE_HIGH_PRIVILEGE_APPROVAL）',
        'ターミナルコマンド、ファイル編集、MCP の書き込みは通常、実行する Mac で承認する必要があります。理由がはっきりしない限りオフのままにしてください。（BROCCOLI_REMOTE_HIGH_PRIVILEGE_APPROVAL）'),
    # ---- Follow-ups on a conversation another device owns ----
    'This Mac (move it back here)': ('这台 Mac（搬回来）', 'この Mac（ここへ戻す）'),
    'Copy to this Mac (new conversation)': ('复制到这台 Mac（新对话）', 'この Mac にコピー（新しい会話）'),
    'Ask {device} to move the conversation back here. It moves as soon as nothing is running there; a typed question then runs here.': (
        '请 {device} 把对话搬回这里。它那边没有任务在跑时就会搬；输入框里的问题随后在这里运行。',
        '{device} に会話をここへ戻すよう依頼します。向こうで何も実行していなければすぐ移動し、入力済みの質問はその後ここで実行されます。'),
    'Make an independent copy here. {device} keeps the original; the two no longer sync.': (
        '在这里做一份独立副本。原对话留在 {device}，两份之后不再同步。',
        'ここに独立したコピーを作ります。元の会話は {device} に残り、以後は同期しません。'),
    'This conversation lives on {device}. Where should it live and run?': (
        '这段对话在 {device} 上。要放到哪里、在哪里运行？',
        'この会話は {device} にあります。どこに置いて実行しますか？'),
    'Your question will be sent there as soon as the move completes.': (
        '搬完后会自动把你的问题发过去。',
        '移動が終わり次第、質問を送ります。'),
    'The conversation is back on this Mac. Sending runs here again.': (
        '对话已回到这台 Mac，之后发送都在这里运行。',
        '会話はこの Mac に戻りました。今後の送信はここで実行されます。'),
    '{device} could not move the conversation here ({reason}).': (
        '{device} 没能把对话搬过来（{reason}）。',
        '{device} は会話をここへ移動できませんでした（{reason}）。'),
    '{device} did not move the conversation within an hour, so the request was dropped.': (
        '{device} 一小时内没有搬过来，请求已作废。',
        '{device} が 1 時間以内に移動しなかったため、依頼を取り消しました。'),
    'Asked {device} to move this conversation here. It moves as soon as nothing is running there.': (
        '已请 {device} 把这段对话搬过来。它那边没有任务在跑时就会搬。',
        '{device} にこの会話をここへ移動するよう依頼しました。向こうで何も実行していなければ移動します。'),
    'Your question will run here as soon as it arrives.': (
        '对话一到，你的问题就会在这里运行。',
        '会話が届き次第、質問をここで実行します。'),
    'Runs on another device': ('在另一台设备上运行', '別のデバイスで実行'),
    'This conversation lives on {device}. Turn on iCloud remote tasks in Settings to send it there, or use 🎛️ Move to → Copy to this Mac to continue here.': (
        '这段对话在 {device} 上。请在设置里打开 iCloud 远程任务以发送过去，或用 🎛️ Move to → 复制到这台 Mac 在这里继续。',
        'この会話は {device} にあります。設定で iCloud リモートタスクをオンにして送るか、🎛️ Move to → この Mac にコピー でここで続けてください。'),
    'Runs on {device} — Send goes there': ('在 {device} 上运行 — 发送会送到那里', '{device} で実行 — 送信はそちらへ'),
    'Read-only copy': ('只读副本', '読み取り専用コピー'),
    'This conversation lives on {device}, so changes here are not saved. Use 🎛️ Move to → This Mac to edit it here, or Copy to this Mac for your own copy.': (
        '这段对话在 {device} 上，在这里的修改不会保存。要在这里编辑，请用 🎛️ Move to → 这台 Mac；想要自己的副本，请用"复制到这台 Mac"。',
        'この会話は {device} にあるため、ここでの変更は保存されません。ここで編集するには 🎛️ Move to → この Mac、自分用のコピーには「この Mac にコピー」を使ってください。'),
    'No paired device has published an iCloud registration yet.': (
        '还没有任何已配对设备发布 iCloud 注册信息。',
        'iCloud 登録を公開しているペアリング済みデバイスはまだありません。'),
    'No paired device is available.': ('没有可用的已配对设备。', '利用可能なペアリング済みデバイスがありません。'),
    'Profile: {name}': ('Profile：{name}', 'プロファイル: {name}'),
    'Queue depth: {count}': ('队列深度：{count}', 'キューの深さ: {count}'),
    'This device has no mapping for the current logical agent; its Default Profile will run.': (
        '这台设备没有当前逻辑 Agent 的映射；将使用它的默认 Profile 运行。',
        'このデバイスには現在の論理エージェントのマッピングがないため、デフォルトプロファイルで実行されます。'),
    # ---- iCloud remote tasks (Settings page 3) ----
    'iCloud remote tasks': ('iCloud 远程任务', 'iCloud リモートタスク'),
    'Changes apply immediately. A BROCCOLI_* environment variable overrides its switch.': (
        '更改立即生效。显式设置的 BROCCOLI_* 环境变量会覆盖对应开关。',
        '変更は即座に適用されます。明示的に設定された BROCCOLI_* 環境変数はスイッチより優先されます。'),
    'Storage engine switches…': ('存储引擎开关…', 'ストレージエンジンのスイッチ…'),
    'Hide storage engine switches': ('收起存储引擎开关', 'ストレージエンジンのスイッチを隠す'),
    'Emergency stops for the storage engine. Leave everything ON unless Broccoli itself tells you otherwise.': (
        '存储引擎的急停开关。除非 Broccoli 明确提示，否则请全部保持开启。',
        'ストレージエンジンの緊急停止スイッチです。Broccoli からの指示がない限り、すべてオンのままにしてください。'),
    'Keep every conversation field on save': ('保存时保留全部对话字段', '保存時に会話フィールドをすべて保持'),
    'Crash-safe conversation saves': ('防崩溃的对话保存', 'クラッシュに強い会話保存'),
    'Collision-proof conversation IDs': ('防撞车的对话 ID', '衝突しない会話 ID'),
    'Only one Broccoli per data folder': ('同一数据目录只允许一个 Broccoli', 'データフォルダごとに Broccoli は 1 つだけ'),
    'Keep caches out of conversation records': ('缓存与对话记录分开存放', 'キャッシュを会話レコードから分離'),
    'Task ledger (crash recovery)': ('任务账本（崩溃恢复）', 'タスク台帳（クラッシュ復旧）'),
    'Single task-completion path': ('统一的任务完成通道', '単一のタスク完了パス'),
    'Rename-safe conversation identity': ('改名无忧的对话身份', 'リネームに強い会話 ID'),
    'Connect devices through iCloud': ('通过 iCloud 连接设备', 'iCloud でデバイスを接続'),
    'Send a new conversation to another device': ('把新对话发送到另一台设备', '新しい会話を別のデバイスへ送信'),
    'Move existing conversations between devices': ('在设备间迁移已有对话', '既存の会話をデバイス間で移動'),
    'Control tasks running on other devices': ('控制其他设备上运行的任务', '他のデバイスで実行中のタスクを制御'),
    'Apple Notes mirror + iPhone Shortcuts': ('Apple 备忘录镜像 + iPhone 快捷指令', 'Apple メモのミラー + iPhone ショートカット'),
    'One history across all devices': ('所有设备共用一份历史', '全デバイスで 1 つの履歴'),
    'Approve high-risk actions remotely (not recommended)': ('远程批准高风险操作（不推荐）', '高リスク操作をリモート承認（非推奨）'),
    ' · verified': (' · 已验证', ' · 検証済み'),
    '%s ⚡ Parallel · %d steps run together%s': ('%s ⚡ 并行 · %d 个步骤同时运行%s', '%s ⚡ 並列 · %d ステップを同時実行%s'),
    'API key': ('API 密钥', 'API キー'),
    'Add comment': ('添加评论', 'コメントを追加'),
    'Agent run failed — {title}': ('Agent 运行失败 — {title}', 'Agent の実行に失敗 — {title}'),
    'Always on': ('始终开启', '常にオン'),
    'Answer ready — {title}': ('回答已就绪 — {title}', '回答の準備完了 — {title}'),
    'Auto (probe)': ('自动（探测）', '自動（プローブ）'),
    'Auto send skipped': ('已跳过自动发送', '自動送信をスキップしました'),
    'Auto send skipped ({caller})': ('已跳过自动发送（{caller}）', '自動送信をスキップしました（{caller}）'),
    'Background vision': ('后台视觉', 'バックグラウンドビジョン'),
    'Category': ('类别', 'カテゴリ'),
    'Choose File to Compare': ('选择要对比的文件', '比較するファイルを選択'),
    'Code Name': ('代码名', 'コード名'),
    'Command complete': ('命令完成', 'コマンド完了'),
    'Command finished with exit code {code}': ('命令结束，退出码 {code}', 'コマンド終了（終了コード {code}）'),
    'Command running...': ('命令运行中…', 'コマンド実行中…'),
    'Context files (*);;All files (*)': ('上下文文件 (*);;所有文件 (*)', 'コンテキストファイル (*);;すべてのファイル (*)'),
    'Description': ('说明', '説明'),
    'Discovery failed:\nCommand is empty.': ('发现失败：\n命令为空。', 'ディスカバリー失敗:\nコマンドが空です。'),
    'Discovery failed:\nEndpoint URL is empty.': ('发现失败：\n端点 URL 为空。', 'ディスカバリー失敗:\nエンドポイント URL が空です。'),
    'Edit before copying or sending.': ('复制或发送前可先编辑。', 'コピーまたは送信の前に編集できます。'),
    'Edit before sending.': ('发送前可先编辑。', '送信前に編集できます。'),
    'Edit comment': ('编辑评论', 'コメントを編集'),
    'Edit favorite': ('编辑收藏', 'お気に入りを編集'),
    'Edit favorite command': ('编辑收藏的命令', 'お気に入りコマンドを編集'),
    'Empty answer — selection kept': ('回答为空 — 已保留所选内容', '回答が空です — 選択は保持されました'),
    'Enter a URL below, or press + to open a saved site.': (
        '在下方输入网址，或点 + 打开已保存的站点。', '下に URL を入力するか、+ を押して保存済みサイトを開いてください。'),
    'Executables (*);;All files (*)': ('可执行文件 (*);;所有文件 (*)', '実行ファイル (*);;すべてのファイル (*)'),
    'Extra headers': ('额外请求头', '追加ヘッダー'),
    'File is empty — nothing to scan': ('文件为空 — 无可扫描内容', 'ファイルが空です — スキャン対象がありません'),
    'Generated via the active API profile. Edit before sending.': (
        '由当前 API 配置生成。发送前可先编辑。', '有効な API プロファイルで生成されました。送信前に編集できます。'),
    'Generation complete': ('生成完成', '生成完了'),
    'Generation failed': ('生成失败', '生成に失敗しました'),
    'Image comment': ('图片评论', '画像コメント'),
    'Image file is missing.': ('图片文件缺失。', '画像ファイルが見つかりません。'),
    'JavaScript files (*.js);;All files (*)': ('JavaScript 文件 (*.js);;所有文件 (*)', 'JavaScript ファイル (*.js);;すべてのファイル (*)'),
    'Local Broccoli Memory': ('本地 Broccoli 记忆', 'ローカルの Broccoli メモリ'),
    'Manual / other': ('手动 / 其他', '手動 / その他'),
    'Manual: always inject · ': ('手动：始终注入 · ', '手動: 常に注入 · '),
    'Manual: never inject · ': ('手动：从不注入 · ', '手動: 注入しない · '),
    'Max results': ('最大结果数', '最大結果数'),
    'Mermaid capture returned an empty image.': ('Mermaid 截取返回了空图片。', 'Mermaid のキャプチャが空の画像を返しました。'),
    'Natural Name': ('自然语言名', '自然な名前'),
    'New Tab': ('新标签页', '新しいタブ'),
    'No current flow': ('没有当前流程图', '現在のフローはありません'),
    'No current page messages detected': ('未检测到当前页面消息', '現在のページにメッセージは検出されませんでした'),
    'No image.': ('暂无图片。', '画像がありません。'),
    'No revised flow': ('没有修改后的流程图', '修正後のフローはありません'),
    'Not probed yet (probes after Save)': ('尚未探测（保存后开始探测）', '未プローブ（保存後にプローブします）'),
    'Nothing open yet': ('还没有打开任何页面', 'まだ何も開いていません'),
    'Off': ('关闭', 'オフ'),
    'Online memory source': ('在线记忆来源', 'オンラインメモリソース'),
    'Open Files': ('打开文件', 'ファイルを開く'),
    'PNG Image (*.png)': ('PNG 图片 (*.png)', 'PNG 画像 (*.png)'),
    'Page %d': ('第 %d 页', '%d ページ'),
    'Plan · Idle': ('计划 · 空闲', 'プラン · 待機中'),
    'Plan · {n} active · {done}/{total} steps': ('计划 · {n} 个进行中 · 步骤 {done}/{total}', 'プラン · {n} 件実行中 · ステップ {done}/{total}'),
    'Probe failed; will retry': ('探测失败；将重试', 'プローブ失敗。再試行します'),
    'Probed: not supported': ('探测结果：不支持', 'プローブ結果: 非対応'),
    'Probed: supported ({levels})': ('探测结果：支持（{levels}）', 'プローブ結果: 対応（{levels}）'),
    'Request failed.': ('请求失败。', 'リクエストに失敗しました。'),
    'Save output as': ('输出另存为', '出力を別名で保存'),
    'Save share image': ('保存分享图片', '共有画像を保存'),
    'Select code runner executable': ('选择代码运行器可执行文件', 'コードランナーの実行ファイルを選択'),
    'Select external context file': ('选择外部上下文文件', '外部コンテキストファイルを選択'),
    'Select external context folder': ('选择外部上下文文件夹', '外部コンテキストフォルダを選択'),
    'Select memory file': ('选择记忆文件', 'メモリファイルを選択'),
    'Select userscript': ('选择用户脚本', 'ユーザースクリプトを選択'),
    'Selected display': ('所选显示器', '選択したディスプレイ'),
    'Share Text': ('分享文本', 'テキストを共有'),
    'Sheet %d': ('工作表 %d', 'シート %d'),
    'Shell history': ('Shell 历史', 'シェル履歴'),
    'Slide %d': ('第 %d 张幻灯片', 'スライド %d'),
    'Snapshot · %s': ('快照 · %s', 'スナップショット · %s'),
    'Starting terminal...': ('正在启动终端…', 'ターミナルを起動中…'),
    'Status': ('状态', '状態'),
    'Terminal renderer failed to load': ('终端渲染器加载失败', 'ターミナルのレンダラーを読み込めませんでした'),
    'Text comment': ('文本评论', 'テキストコメント'),
    'Text files (*.txt *.md *.json);;All files (*)': ('文本文件 (*.txt *.md *.json);;所有文件 (*)', 'テキストファイル (*.txt *.md *.json);;すべてのファイル (*)'),
    'The model returned an empty answer.': ('模型返回了空回答。', 'モデルが空の回答を返しました。'),
    'Time comment': ('时间点评论', '時間コメント'),
    'Unavailable — {label} (reconnect or choose another display)': (
        '不可用 — {label}（请重新连接或选择其他显示器）', '利用不可 — {label}（再接続するか別のディスプレイを選択してください）'),
    'Untitled task': ('未命名任务', '無題のタスク'),
    'WebFetch download folder is not set.': ('未设置 WebFetch 下载文件夹。', 'WebFetch のダウンロードフォルダが未設定です。'),
    'this session': ('这个会话', 'このセッション'),
    'watchdog is unavailable.': ('watchdog 不可用。', 'watchdog を利用できません。'),
    '{n} messages detected': ('检测到 {n} 条消息', '{n} 件のメッセージを検出'),
    '{n} outputs · {kind}': ('{n} 个输出 · {kind}', '出力 {n} 件 · {kind}'),
    'Task reasoning': ('任务推理', 'タスク推論'),
    'Web search': ('网页搜索', 'ウェブ検索'),
    'Text to speech': ('文字转语音', 'テキスト読み上げ'),
    'Speech to text': ('语音转文字', '音声文字起こし'),
    'Image generation': ('图像生成', '画像生成'),
    'Video generation': ('视频生成', '動画生成'),
    'Video to text': ('视频转文字', '動画の文字起こし'),
    'Terminal command': ('终端命令', 'ターミナルコマンド'),
    'Default chat': ('默认聊天', '既定のチャット'),
    'Text embedding': ('文本向量', 'テキスト埋め込み'),
    'Planner / Router': ('规划器 / 路由', 'プランナー / ルーター'),
    'Endpoint URL': ('端点 URL', 'エンドポイント URL'),
    'Transport': ('传输方式', 'トランスポート'),
    'Bearer token': ('Bearer 令牌', 'Bearer トークン'),
    'Toolsets': ('工具集', 'ツールセット'),
    'Command': ('命令', 'コマンド'),
    'Args': ('参数', '引数'),
    'Working dir': ('工作目录', '作業ディレクトリ'),
    'Env': ('环境变量', '環境変数'),
    'Destination': ('发送到', '送信先'),
    'Mode': ('模式', 'モード'),
    'Saved profiles': ('已存配置', '保存済みプロファイル'),
    'Endpoint': ('端点', 'エンドポイント'),
    'Timeout (sec)': ('超时（秒）', 'タイムアウト（秒）'),
    'Reasoning effort': ('思考强度', '推論の強さ'),
    'Displayed history max chars': ('界面历史最大字符数', '表示履歴の最大文字数'),
    'Web / Localhost energy mode': ('Web / Localhost 能耗模式', 'Web / Localhost 省エネモード'),
    'Executable': ('可执行文件', '実行ファイル'),
    'Args template': ('参数模板', '引数テンプレート'),
    'Schedule mode': ('调度模式', 'スケジュールモード'),
    'Interval (sec)': ('间隔（秒）', '間隔（秒）'),
    'Completion delay': ('完成后延迟', '完了後の遅延'),
    'Floating window seconds': ('悬浮窗停留秒数', 'フローティング表示秒数'),
    'Profile wait mode': ('配置等待模式', 'プロファイル待機モード'),
    'Max concurrent rounds': ('最大并发轮数', '最大同時ラウンド数'),
    'Image format': ('图片格式', '画像形式'),
    'Max history messages': ('最大历史消息数', '履歴メッセージの最大数'),
    'Max JSON records': ('最大 JSON 记录数', 'JSON レコードの最大数'),
    'Screenshot folder': ('截图文件夹', 'スクリーンショットフォルダ'),
    'Chrome mode': ('Chrome 模式', 'Chrome モード'),
    'CDP URL': ('CDP URL', 'CDP URL'),
    'Chrome executable': ('Chrome 可执行文件', 'Chrome 実行ファイル'),
    'Chrome profile folder': ('Chrome 配置文件夹', 'Chrome プロファイルフォルダ'),
    'Vision': ('视觉', 'ビジョン'),
    'Speed mode': ('速度模式', '速度モード'),
    'Standard (full reasoning)': ('标准（完整推理）', '標準（完全な推論）'),
    'No thinking (faster)': ('无思考（更快）', '思考なし（高速）'),
    'Flash (fastest)': ('极速（最快）', 'フラッシュ（最速）'),
    "No thinking removes the reasoning fields from each step's output. Flash also swaps in a minimal system prompt and shorter page waits (official Fast Agent template).": (
        '无思考档会去掉每步输出里的推理字段。极速档还会换用极简系统提示词并缩短页面等待（官方 Fast Agent 模板）。',
        '思考なしは各ステップの出力から推論フィールドを取り除きます。フラッシュはさらに最小限のシステムプロンプトに切り替え、ページ待機を短縮します（公式 Fast Agent テンプレート）。'),
    'History steps in memory': ('记忆中的历史步数', 'メモリ内の履歴ステップ数'),
    'How many recent steps the browser agent keeps in memory. 0 = unlimited; values 1–5 are raised to 6 (library minimum).': (
        '浏览器代理记忆中保留的最近步骤数。0 = 不限；1–5 会抬到 6（库的最低值）。',
        'ブラウザエージェントがメモリに保持する直近ステップ数。0 = 無制限。1–5 は 6 に引き上げられます（ライブラリの最小値）。'),
    'Task context': ('任务上下文', 'タスクコンテキスト'),
    'Compact (recommended)': ('精简（推荐）', 'コンパクト（推奨）'),
    'Full': ('完整', '完全'),
    'Compact sends the agent a goal-first task brief with tighter background limits; the brief is resent on every step, so smaller means faster. Full keeps the original verbose brief.': (
        '精简档发送“目标置顶”的任务书并收紧背景材料限额；任务书每一步都会重发，越小越快。完整档保持原来的详细任务书。',
        'コンパクトは目標を先頭に置いたタスク指示を送り、背景資料の上限を絞ります。指示は毎ステップ再送されるため、小さいほど高速です。完全は従来の詳細な指示を維持します。'),
    'Search engine': ('搜索引擎', '検索エンジン'),
    'Building the prompt (retrieval, embeddings)…': ('正在构建提示词（检索、嵌入）…', 'プロンプトを構築中（検索・埋め込み）…'),
    'Send to web page': ('发送到网页', 'Web ページへ送信'),
    'Preparing the prompt failed: {error}': ('构建提示词失败：{error}', 'プロンプトの構築に失敗しました：{error}'),
    'Retrieval': ('检索', '検索'),
    'Retrieval similarity thresholds': ('检索相似度门槛', '検索類似度のしきい値'),
    'Saved memory': ('已保存记忆', '保存済みメモリ'),
    'Conversation history': ('对话历史', '会話履歴'),
    'Attachments / fetched pages': ('附件 / 抓取的网页', '添付ファイル / 取得したページ'),
    'External context sources': ('外部上下文源', '外部コンテキストソース'),
    'Cross-conversation history': ('跨对话历史', '会話横断の履歴'),
    'Minimum cosine similarity (0–1) a record must reach to be included as context. 0 = no threshold (top matches are used as ranked). Higher = stricter: fewer but more relevant records.': (
        '一条记录要被纳入上下文所需达到的最低余弦相似度（0–1）。0 = 不设门槛（按排序取最相关的若干条）。数值越高越严格：条数更少但更相关。',
        'コンテキストに含めるために記録が満たすべき最小コサイン類似度（0–1）。0 = しきい値なし（順位どおり上位を使用）。高いほど厳格：件数は減りますがより関連性の高い記録になります。'),
    "Default engine for the browser agent's search action. Pick one that is reachable from your network; unreachable engines make search steps hang and fail.": (
        '浏览器代理搜索动作的默认引擎。请选择你的网络能访问的引擎；访问不了的引擎会让搜索步骤挂死并失败。',
        'ブラウザエージェントの検索アクションの既定エンジン。ネットワークから到達できるものを選んでください。到達できないエンジンは検索ステップの停止と失敗を招きます。'),
    'Driver command': ('驱动命令', 'ドライバコマンド'),
    'Target display': ('目标显示器', 'ターゲットディスプレイ'),
    'Read URL / file': ('读取 URL / 文件', '読み取り URL / ファイル'),
    'Write URL / file': ('写入 URL / 文件', '書き込み URL / ファイル'),
    'Read / Write method': ('读 / 写方式', '読み書き方式'),
    'Rule preset': ('规则预设', 'ルールプリセット'),
    'Added to the task queue': ('已加入任务队列', 'タスクキューに追加しました'),
    'Auto-translate queued…': ('自动翻译已排队…', '自動翻訳をキューに追加…'),
    'Choose a target language first': ('请先选择目标语言', '先に翻訳先の言語を選んでください'),
    'Content changed — re-translation discarded': ('内容已变化 — 已丢弃这次重译', '内容が変わったため再翻訳を破棄しました'),
    'Could not create a conversation': ('无法创建对话', '会話を作成できませんでした'),
    'Could not rasterize the page': ('无法栅格化该页面', 'ページをラスタライズできませんでした'),
    'Could not start (check API settings)': ('无法启动（请检查 API 设置）', '開始できません（API 設定を確認してください）'),
    'Last scan v%s · %d open': ('上次扫描 v%s · %d 个未解决', '前回のスキャン v%s · 未解決 %d 件'),
    'Main window unavailable': ('主窗口不可用', 'メインウィンドウを利用できません'),
    'No scan yet — save a version or press Scan Now': (
        '还没有扫描 — 保存一个版本或点“立即扫描”', 'まだスキャンしていません — バージョンを保存するか「今すぐスキャン」を押してください'),
    'No sync status yet.': ('还没有同步状态。', 'まだ同期状態はありません。'),
    'Nothing to translate': ('没有可翻译的内容', '翻訳する内容がありません'),
    'Page %d — not translated yet': ('第 %d 页 — 尚未翻译', '%d ページ — 未翻訳'),
    'Page %d — translated (cached)%s': ('第 %d 页 — 已翻译（缓存）%s', '%d ページ — 翻訳済み（キャッシュ）%s'),
    'Page %d — translated%s': ('第 %d 页 — 已翻译%s', '%d ページ — 翻訳済み%s'),
    'Queued — one translation at a time': ('已排队 — 一次只翻译一个', 'キューに追加 — 同時に 1 件ずつ翻訳します'),
    'Re-translate failed: %s': ('重译失败：%s', '再翻訳に失敗: %s'),
    'Re-translating the selection…': ('正在重译所选内容…', '選択部分を再翻訳中…'),
    'Recognizing text on the page…': ('正在识别页面文字…', 'ページの文字を認識中…'),
    'Scan failed: %s': ('扫描失败：%s', 'スキャンに失敗: %s'),
    'Scan queued (%d ahead)…': ('扫描已排队（前面还有 %d 个）…', 'スキャンをキューに追加（前に %d 件）…'),
    'Scan queued…': ('扫描已排队…', 'スキャンをキューに追加…'),
    'Selection re-translated': ('所选内容已重译', '選択部分を再翻訳しました'),
    'Sent to main chat': ('已发送到主对话', 'メインチャットに送信しました'),
    'Task queue running': ('任务队列运行中', 'タスクキュー実行中'),
    'The model did not return a valid table': ('模型没有返回有效的表格', 'モデルが有効な表を返しませんでした'),
    'This page has nothing to translate': ('这一页没有可翻译的内容', 'このページに翻訳する内容はありません'),
    'Translating page %d…%s': ('正在翻译第 %d 页…%s', '%d ページを翻訳中…%s'),
    'Translation failed: %s': ('翻译失败：%s', '翻訳に失敗: %s'),
    'Will run right after the current turn': ('将在当前轮结束后立即运行', '現在のターンの直後に実行されます'),
    'unknown error': ('未知错误', '不明なエラー'),
    'Add file': ('添加文件', 'ファイルを追加'),
    'Add to Menu': ('加入菜单', 'メニューに追加'),
    'Add web': ('添加网页', 'ウェブを追加'),
    'Again': ('再来一次', 'もう一度'),
    'Allow once': ('允许一次', '一度だけ許可'),
    'Apply': ('应用', '適用'),
    'Apply model': ('应用模型', 'モデルを適用'),
    'Ask a question, paste some text, or drop in a file to get started.': (
        '提个问题、粘贴一段文字，或拖入一个文件，就可以开始了。',
        '質問をする、テキストを貼り付ける、またはファイルをドロップして始めましょう。'),
    'Browse': ('浏览', '参照'),
    'Buy me a cup of coffee☕': ('请我喝杯咖啡☕', 'コーヒーをご馳走してください☕'),
    'Choose': ('选择', '選択'),
    'Compare': ('对比', '比較'),
    'Copy Text': ('复制文本', 'テキストをコピー'),
    'Debug': ('调试', 'デバッグ'),
    'Discover': ('发现', 'ディスカバー'),
    'Down': ('下移', '下へ'),
    'General': ('通用', '一般'),
    'Github': ('Github', 'Github'),
    'Github Page': ('Github 主页', 'Github ページ'),
    'Hello from Broccoli': ('Broccoli 向你问好', 'Broccoli へようこそ'),
    'Hide': ('隐藏', '隠す'),
    'Import URLs': ('导入网址', 'URL をインポート'),
    'Launch Browser Use Chrome': ('启动 Browser Use Chrome', 'Browser Use Chrome を起動'),
    'Logic Map': ('逻辑图', 'ロジックマップ'),
    'Manage…': ('管理…', '管理…'),
    'Memory': ('记忆', 'メモリ'),
    'Models': ('模型', 'モデル'),
    'Neither one above? Buy me a coffee~': ('上面两个都没有？请我喝杯咖啡吧~', 'どちらも使えない？コーヒーをご馳走してください~'),
    'Open In': ('打开方式', 'アプリで開く'),
    'Open status': ('打开状态页', 'ステータスを開く'),
    'Prompts': ('提示词', 'プロンプト'),
    'Pull now': ('立即拉取', '今すぐプル'),
    'Push now': ('立即推送', '今すぐプッシュ'),
    'Re-dock': ('重新停靠', '再ドッキング'),
    'Re-parse': ('重新解析', '再解析'),
    'Remove': ('移除', '削除'),
    'Restore default': ('恢复默认', '既定に戻す'),
    'Retry': ('重试', '再試行'),
    'Run command': ('运行命令', 'コマンドを実行'),
    'Save & regenerate': ('保存并重新生成', '保存して再生成'),
    'Scan Now': ('立即扫描', '今すぐスキャン'),
    'Skip': ('跳过', 'スキップ'),
    'Run now': ('立即执行', '今すぐ実行'),
    'Hold': ('暂停', '一時停止'),
    'Resume': ('继续', '再開'),
    'Freeze the countdown so you can edit or reorder steps; Resume or Run now continues': (
        '冻结倒计时，让你可以从容编辑或调整步骤顺序；按"继续"或"立即执行"恢复', 'カウントダウンを凍結してステップの編集や並べ替えをゆっくり行えます。「再開」または「今すぐ実行」で続行'),
    'Start the counting-down step immediately': ('不等倒计时，立刻执行这个步骤', 'カウントダウンを待たずにこのステップをすぐ実行'),
    'Share login cookies with parallel browser sessions': ('并行浏览器会话共享登录 Cookie', '並列ブラウザセッションでログイン Cookie を共有'),
    "Copies the managed profile's cookies and local storage into each isolated parallel Chrome, so logged-in sites can be searched by several parallel steps. Turn on after verifying on your machine.": (
        '把受管配置档的 Cookie 和本地存储复制进每个隔离的并行 Chrome，让已登录站点也能由多个并行步骤同时检索。请在本机验证通过后再开启。',
        '管理プロファイルの Cookie とローカルストレージを各独立並列 Chrome にコピーし、ログイン済みサイトを複数の並列ステップで検索できるようにします。お使いの Mac で検証してから有効にしてください。'),
    'Snapshots': ('快照', 'スナップショット'),
    'Stop': ('停止', '停止'),
    'Sync now': ('立即同步', '今すぐ同期'),
    'Test capability': ('测试能力', '機能をテスト'),
    'Thank you!': ('谢谢！', 'ありがとう！'),
    'The Author': ('关于作者', '作者について'),
    'Type': ('类型', '種類'),
    'Up': ('上移', '上へ'),
    'Use "{preview}"': ('使用“{preview}”', '「{preview}」を使用'),
    'Use current URL': ('使用当前网址', '現在の URL を使用'),
    'Verify': ('核验', '検証'),
    '♻️ Transfer': ('♻️ 转移', '♻️ 転送'),
    '➕ Add note': ('➕ 追加指示', '➕ メモを追加'),
    '🌐 Chrome': ('🌐 Chrome', '🌐 Chrome'),
    '🏷️ Tag': ('🏷️ 标签', '🏷️ タグ'),
    '📸 Shot': ('📸 截图', '📸 スクショ'),
    '🔸 New': ('🔸 新对话', '🔸 新規'),
    '🔹 Again': ('🔹 再来一次', '🔹 もう一度'),
    '🔺 Share': ('🔺 分享', '🔺 共有'),
    '🔻 Save': ('🔻 保存', '🔻 保存'),
    '🧾 Queue': ('🧾 排队', '🧾 キュー'),
    '\n\nIt will not use the AI model open in this web page.': (
        '\n\n不会使用当前网页里打开的 AI 模型。',
        '\n\nこのウェブページで開いている AI モデルは使用されません。'),
    ' and synced to ': ('，并已同步到 ', '、次へ同期済み: '),
    '%d/%d entries': ('%d/%d 条', '%d/%d 件'),
    '&Actions': ('操作(&A)', '操作(&A)'),
    '&Pin!': ('钉住(&P)!', 'ピン留め(&P)!'),
    '(empty)': ('（空）', '（空）'),
    '0 outputs': ('0 个输出', '出力 0 件'),
    '5 (max 10)': ('5（最多 10）', '5（最大 10）'),
    '<h2>Broccoli Update</h2>': ('<h2>Broccoli 更新</h2>', '<h2>Broccoli アップデート</h2>'),
    '@{alias} offered editor_edit.json, but its download did not complete. The open file was not changed.': (
        '@{alias} 提供了 editor_edit.json，但下载未完成。打开的文件没有被改动。',
        '@{alias} は editor_edit.json を提示しましたが、ダウンロードが完了しませんでした。開いているファイルは変更されていません。'),
    '@{alias} returned no usable editor_edit. The open file was not changed.': (
        '@{alias} 没有返回可用的 editor_edit。打开的文件没有被改动。',
        '@{alias} は利用可能な editor_edit を返しませんでした。開いているファイルは変更されていません。'),
    '@{alias} sent editor_edit.json, but Broccoli could not import it. The open file was not changed.': (
        '@{alias} 发送了 editor_edit.json，但 Broccoli 无法导入。打开的文件没有被改动。',
        '@{alias} は editor_edit.json を送信しましたが、Broccoli は取り込めませんでした。開いているファイルは変更されていません。'),
    'Auto quality': ('自动质量', '自動品質'),
    'Bug': ('问题', 'バグ'),
    'Chrome must expose a remote debugging endpoint before Browser Use can control it.\n\nCDP URL: {cdp}\n\nBrowser Use profile folder:\n{folder}\n\nBroccoli will launch a separate Chrome window with this profile. Sign in there once; future Browser Use tasks reuse that login state.': (
        'Browser Use 控制 Chrome 之前，Chrome 必须先开放远程调试端点。\n\nCDP URL：{cdp}\n\nBrowser Use 配置文件夹：\n{folder}\n\nBroccoli 会用这个配置启动一个单独的 Chrome 窗口。在里面登录一次，之后的 Browser Use 任务会复用该登录状态。',
        'Browser Use が Chrome を制御するには、先に Chrome がリモートデバッグ用エンドポイントを公開している必要があります。\n\nCDP URL: {cdp}\n\nBrowser Use プロファイルフォルダ:\n{folder}\n\nBroccoli はこのプロファイルで別の Chrome ウィンドウを起動します。一度サインインすれば、以後の Browser Use タスクはそのログイン状態を再利用します。'),
    'Current state': ('当前状态', '現在の状態'),
    'Edit local context source': ('编辑本地上下文来源', 'ローカルコンテキストソースを編集'),
    'History name:': ('历史名称：', '履歴名:'),
    'Name:': ('名称：', '名前:'),
    'Notes / traits': ('备注 / 特点', 'メモ / 特徴'),
    'OK': ('好', 'OK'),
    'Rename history': ('重命名历史', '履歴の名前を変更'),
    'Rename…': ('重命名…', '名前を変更…'),
    'Rules': ('规则', 'ルール'),
    '@{alias} is not running. Open a Codex or Claude Code tab first.': (
        '@{alias} 未在运行。请先打开一个 Codex 或 Claude Code 标签页。',
        '@{alias} は実行されていません。先に Codex または Claude Code のタブを開いてください。'),
    'A Task Capsule is already being generated.': (
        '任务胶囊正在生成中。', 'タスクカプセルは既に生成中です。'),
    'A translation is already running': ('已有一个翻译正在进行', '翻訳が既に実行中です'),
    'AI Name This': ('让 AI 命名', 'AI に命名させる'),
    'API Key': ('API 密钥', 'API キー'),
    'About': ('关于', 'このアプリについて'),
    'Active URL': ('当前 URL', '現在の URL'),
    'Add': ('添加', '追加'),
    'Add & manage profiles': ('添加与管理配置', 'プロファイルの追加と管理'),
    'Add Comment': ('添加评论', 'コメントを追加'),
    'Add Comment to Menu': ('把评论加入菜单', 'コメントをメニューに追加'),
    'Add Time Comment': ('添加时间点评论', '時間コメントを追加'),
    'Add a note for all parallel members…': (
        '给所有并行成员添加一条备注…', '並列メンバー全員へのメモを追加…'),
    'Add note': ('追加指示', 'メモを追加'),
    'Add note to running answer': ('给正在生成的回答追加指示', '実行中の回答にメモを追加'),
    'Add selection to Apple Notes': ('把所选内容存入 Apple 备忘录', '選択部分を Apple メモに追加'),
    'Add selection to Generated outputs': ('把所选内容加入生成输出', '選択部分を生成出力に追加'),
    'Add selection to Terminal favorites': ('把所选内容加入终端收藏', '選択部分をターミナルのお気に入りに追加'),
    'Add selection to a new Apple Note': ('把所选内容存为新的 Apple 备忘录', '選択部分を新しい Apple メモに保存'),
    'Add selection to an Apple Note…': ('把所选内容追加到某条 Apple 备忘录…', '選択部分を既存の Apple メモに追加…'),
    'Add selection to favorites': ('把所选内容加入收藏', '選択部分をお気に入りに追加'),
    'Add to Compare': ('加入对比', '比較に追加'),
    'Add to Task Queue': ('加入任务队列', 'タスクキューに追加'),
    'Added. Fill in the fields and press Save.': (
        '已添加。填写各字段后点击保存。', '追加しました。各欄を入力して保存を押してください。'),
    'Additional instruction for the current answer...': (
        '对当前回答的补充指示…', '現在の回答への追加指示…'),
    'Adopt & Save': ('采纳并保存', '採用して保存'),
    'Advanced': ('高级', '詳細'),
    'Advanced optional headers, one per line.\nAuthorization and read-only headers are generated from the fields above.': (
        '高级可选请求头，每行一个。\nAuthorization 与只读相关请求头会由上方字段自动生成。',
        '詳細設定のオプションヘッダー（1 行に 1 つ）。\nAuthorization と読み取り専用ヘッダーは上の欄から自動生成されます。'),
    'After round completion': ('每轮完成后', 'ラウンド完了後'),
    'Agent': ('智能体', 'エージェント'),
    'Agent CLI history': ('Agent CLI 历史', 'Agent CLI 履歴'),
    'Agent plan': ('Agent 计划', 'Agent プラン'),
    'Agent queue': ('Agent 队列', 'Agent キュー'),
    'Agent saved comments': ('Agent 已存评论', 'Agent 保存済みコメント'),
    'All': ('全部', 'すべて'),
    'All profiles finished': ('所有配置都完成后', 'すべてのプロファイルが完了後'),
    'Allow MCP tools during chat (confirm write / non-read-only calls)': (
        '聊天时允许 MCP 工具（写入/非只读调用需确认）',
        'チャット中に MCP ツールを許可（書き込み系の呼び出しは確認）'),
    'Allow blank prompt with attachments': ('允许只带附件的空提示词', '添付ファイルのみの空プロンプトを許可'),
    'Allowed range: 1–{max}': ('允许范围：1–{max}', '許容範囲: 1–{max}'),
    'Annotation pen color': ('批注画笔颜色', '注釈ペンの色'),
    'Append': ('追加', '追記'),
    'Append /v1': ('自动补 /v1', '/v1 を付加'),
    'Append selection to prompt': ('把所选内容追加到提示词', '選択部分をプロンプトに追記'),
    'Append to current API history': ('追加到当前 API 历史', '現在の API 履歴に追記'),
    'Append to current chat': ('追加到当前对话', '現在のチャットに追記'),
    'Append to permanent memory': ('追加到永久记忆', '永続メモリに追記'),
    'Append to prompt input': ('追加到提示词输入框', 'プロンプト入力欄に追記'),
    'Append to terminal input': ('追加到终端输入框', 'ターミナル入力欄に追記'),
    'Apple Notes': ('Apple 备忘录', 'Apple メモ'),
    'Applies to app (any = all)': ('适用应用（any = 全部）', '対象アプリ（any = すべて）'),
    'Apply experience rules to Computer Use tasks': (
        '将经验规则应用于 Computer Use 任务', '経験ルールを Computer Use タスクに適用'),
    'Approve Computer Use': ('批准 Computer Use', 'Computer Use を承認'),
    'Article': ('文章', '記事'),
    'Ask Localhost': ('问 Localhost', 'Localhost に質問'),
    'Ask Web': ('问 Web', 'Web に質問'),
    'Attachment upload': ('附件上传', '添付ファイルのアップロード'),
    'Auto': ('自动', '自動'),
    'Auto click Send after filling Web / Localhost prompts': (
        '填入 Web / Localhost 提示词后自动点击发送', 'Web / Localhost にプロンプトを入力後、自動で送信をクリック'),
    'Auto quality comes from per-step reviews (goal met / total). Edit the Notes column to record traits; saved immediately.': (
        '自动质量分来自每步复盘（达成目标数 / 总数）。可在备注列记录模型特点，编辑后立即保存。',
        '自動品質はステップごとのレビュー（目標達成 / 総数）から算出されます。Notes 列で特徴を記録でき、編集は即保存されます。'),
    'Auto-detect': ('自动检测', '自動検出'),
    'Auto-hide main window at screen edges': ('主窗口贴屏幕边缘时自动隐藏', 'メインウィンドウを画面端で自動的に隠す'),
    'Auto-learn new rules from task evidence': ('从任务证据中自动学习新规则', 'タスクの証拠から新しいルールを自動学習'),
    'Auto-open last Web / Localhost URLs on launch': (
        '启动时自动打开上次的 Web / Localhost 网址', '起動時に前回の Web / Localhost URL を自動で開く'),
    'Auto-start Codex / Claude Code tabs on launch': (
        '启动时自动开启 Codex / Claude Code 标签页', '起動時に Codex / Claude Code タブを自動開始'),
    'Auto-translate New Pages': ('自动翻译新页面', '新しいページを自動翻訳'),
    'Auto-translate is on — pages translate on flip': (
        '自动翻译已开启 — 翻页即翻译', '自動翻訳オン — ページをめくると翻訳されます'),
    'Available after the diagram milestone': ('图表里程碑完成后可用', 'ダイアグラムのマイルストーン後に利用可能'),
    'Back': ('后退', '戻る'),
    'Back to Current': ('回到当前版本', '現在版に戻る'),
    'Background vision profiles': ('后台视觉配置', 'バックグラウンドビジョンのプロファイル'),
    'Background vision prompt': ('后台视觉提示词', 'バックグラウンドビジョンのプロンプト'),
    'Basic': ('基本', '基本'),
    'Broccoli Ask': ('Broccoli 提问', 'Broccoli に質問'),
    'Broccoli Editor': ('Broccoli 编辑器', 'Broccoli エディタ'),
    'Broccoli Reader': ('Broccoli 阅读器', 'Broccoli リーダー'),
    'Broccoli Translate': ('Broccoli 翻译', 'Broccoli 翻訳'),
    'Broccoli Updates': ('Broccoli 更新', 'Broccoli アップデート'),
    'Broccoli could not launch or connect to the fixed Browser Use Chrome instance. Check the CDP URL port and Chrome profile folder.': (
        'Broccoli 无法启动或连接固定的 Browser Use Chrome 实例。请检查 CDP URL 端口和 Chrome 配置文件夹。',
        'Broccoli は固定の Browser Use Chrome インスタンスを起動または接続できませんでした。CDP URL のポートと Chrome プロファイルフォルダを確認してください。'),
    'Broccoli terminal history': ('Broccoli 终端历史', 'Broccoli ターミナル履歴'),
    'Browser Use': ('Browser Use', 'Browser Use'),
    'Browser Use Chrome': ('Browser Use Chrome', 'Browser Use Chrome'),
    'Browser Use Chrome launched': ('Browser Use Chrome 已启动', 'Browser Use Chrome を起動しました'),
    'Browser Use Chrome unavailable': ('Browser Use Chrome 不可用', 'Browser Use Chrome を利用できません'),
    'Browser Use needs Google Chrome installed. Check the Chrome executable path.': (
        'Browser Use 需要安装 Google Chrome。请检查 Chrome 可执行文件路径。',
        'Browser Use には Google Chrome が必要です。Chrome 実行ファイルのパスを確認してください。'),
    'Browser download folder': ('浏览器下载文件夹', 'ブラウザのダウンロードフォルダ'),
    'Browser userscripts (Web / Localhost)': ('浏览器用户脚本（Web / Localhost）', 'ブラウザのユーザースクリプト（Web / Localhost）'),
    'Browse…': ('浏览…', '参照…'),
    'Cancel': ('取消', 'キャンセル'),
    'Caption': ('备注名', 'キャプション'),
    'Capture Frame': ('截取当前帧', 'フレームをキャプチャ'),
    'Capture the selected area': ('截取所选区域', '選択範囲をキャプチャ'),
    'Chat and ask': ('聊天提问', 'チャットで質問'),
    'Check release:': ('查看发布页：', 'リリースを確認:'),
    'Choose API history...': ('选择 API 历史…', 'API 履歴を選択…'),
    'Choose Application…': ('选择应用程序…', 'アプリケーションを選択…'),
    'Choose a non-default model profile for Compare.': (
        '请为对比选择一个非默认的模型配置。', 'Compare には既定以外のモデルプロファイルを選んでください。'),
    'Choose a non-default model profile for Verify.': (
        '请为核验选择一个非默认的模型配置。', 'Verify には既定以外のモデルプロファイルを選んでください。'),
    'Choose a source to compare': ('选择要对比的来源', '比較するソースを選択'),
    'Choose file…': ('选择文件…', 'ファイルを選択…'),
    'Choose what to share from the current Agent conversation.': (
        '选择要从当前 Agent 对话分享的内容。', '現在の Agent 会話から共有する内容を選んでください。'),
    'Choose what to share from the current Terminal session.': (
        '选择要从当前终端会话分享的内容。', '現在のターミナルセッションから共有する内容を選んでください。'),
    'Chrome CDP not reachable': ('无法连接 Chrome CDP', 'Chrome CDP に接続できません'),
    'Clear attachments after send': ('发送后清空附件', '送信後に添付ファイルをクリア'),
    'Close': ('关闭', '閉じる'),
    'Close Browser Use window after task': ('任务结束后关闭 Browser Use 窗口', 'タスク後に Browser Use ウィンドウを閉じる'),
    'Close main window': ('关闭主窗口', 'メインウィンドウを閉じる'),
    'Close tab': ('关闭标签页', 'タブを閉じる'),
    'Close tag': ('关闭标签', 'タグを閉じる'),
    'Code': ('代码', 'コード'),
    'Code runners': ('代码运行器', 'コードランナー'),
    'Collapse': ('折叠', '折りたたむ'),
    'Cards': ('卡片', 'カード'),
    'Minimize cards': ('收起卡片', 'カードをしまう'),
    'Show the cards again': ('重新显示卡片', 'カードをもう一度表示'),
    'Command (AppleScript)': ('命令（AppleScript）', 'コマンド（AppleScript）'),
    'Comment template': ('评论模板', 'コメントテンプレート'),
    'Comment text': ('评论内容', 'コメント本文'),
    'Comment {index}: {comment}': ('评论 {index}：{comment}', 'コメント {index}: {comment}'),
    'Compare these two': ('对比这两个', 'この 2 つを比較'),
    'Computer Use': ('Computer Use', 'Computer Use'),
    'Computer Use experience rules': ('Computer Use 经验规则', 'Computer Use 経験ルール'),
    'Context': ('上下文', 'コンテキスト'),
    'Conversation deleted': ('对话已删除', '会話を削除しました'),
    'Copy': ('复制', 'コピー'),
    'Copy Bug Summary': ('复制问题摘要', 'バグ概要をコピー'),
    'Copy Code Name': ('复制代码名', 'コード名をコピー'),
    'Copy Image': ('复制图片', '画像をコピー'),
    'Copy resume command': ('复制恢复命令', '再開コマンドをコピー'),
    'Copy transcript path': ('复制记录文件路径', 'トランスクリプトのパスをコピー'),
    'Could not copy file: {exc}': ('无法复制文件：{exc}', 'ファイルをコピーできません: {exc}'),
    'Create and edit your API accounts (endpoint, key, model) here. This page does not select which model to use — choose the default chat, planner, embedding and other roles on the Models page.': (
        '在这里创建和编辑你的 API 账户（端点、密钥、模型）。本页不负责选用哪个模型 — 请到“模型”页选择默认聊天、规划器、向量等角色。',
        'ここで API アカウント（エンドポイント・キー・モデル）を作成・編集します。このページでは使用モデルは選択しません — 既定のチャット、プランナー、埋め込みなどの役割は「モデル」ページで選んでください。'),
    'Cross-send latest replies between selected tabs': (
        '在所选标签页之间互发最新回复', '選択したタブ同士で最新の返信を相互送信'),
    'Current': ('当前', '現在'),
    'Current Agent answer is still running. Stop it before auto-sending another screenshot.': (
        '当前 Agent 回答仍在生成。请先停止，再自动发送新的截图。',
        '現在の Agent の回答が実行中です。停止してから次のスクリーンショットを自動送信してください。'),
    'Current version: v{v}': ('当前版本：v{v}', '現在のバージョン: v{v}'),
    'Custom services': ('自定义服务', 'カスタムサービス'),
    'Custom services (&name, e.g. Ollama web search)': (
        '自定义服务（&名称，例如 Ollama 网页搜索）', 'カスタムサービス（&名前、例: Ollama ウェブ検索）'),
    'Customize': ('自定义', 'カスタマイズ'),
    'Default App': ('默认应用', '既定のアプリ'),
    'Delete': ('删除', '削除'),
    'Delete Comment': ('删除评论', 'コメントを削除'),
    'Delete old dynamic memory after': ('删除动态记忆，早于', '次の期間より古い動的メモリを削除:'),
    'Delete permanently': ('永久删除', '完全に削除'),
    'Delete profile': ('删除配置', 'プロファイルを削除'),
    'Delete session permanently?': ('永久删除该会话？', 'セッションを完全に削除しますか？'),
    'Deleted {name}.': ('已删除 {name}。', '{name} を削除しました。'),
    'Deselect All': ('全部取消选择', 'すべて選択解除'),
    'Discard': ('丢弃', '破棄'),
    'Discovery': ('发现', 'ディスカバリー'),
    'Download failed': ('下载失败', 'ダウンロード失敗'),
    'Edit': ('编辑', '編集'),
    'Edit Comment': ('编辑评论', 'コメントを編集'),
    'Edit MCP HTTP source': ('编辑 MCP HTTP 来源', 'MCP HTTP ソースを編集'),
    'Edit MCP stdio source': ('编辑 MCP stdio 来源', 'MCP stdio ソースを編集'),
    'Edit memory': ('编辑记忆', 'メモリを編集'),
    'Edit step': ('编辑步骤', 'ステップを編集'),
    'Edit the selected online memory rule here.': (
        '在这里编辑选中的在线记忆规则。', '選択したオンラインメモリのルールをここで編集します。'),
    'Edit the selected prompt body here. Use {text} for the input placeholder when needed.': (
        '在这里编辑选中的提示词正文。需要时用 {text} 作为输入占位符。',
        '選択したプロンプト本文をここで編集します。必要に応じて {text} を入力プレースホルダーとして使えます。'),
    'Edit the selected skill. Required frontmatter: name and description.': (
        '编辑选中的技能。frontmatter 必填：name 和 description。',
        '選択したスキルを編集します。frontmatter の必須項目: name と description。'),
    'Editor': ('编辑器', 'エディタ'),
    'Editor edit rejected': ('编辑器修改已拒绝', 'エディタの編集を却下しました'),
    'Editor file unchanged': ('编辑器文件无变化', 'エディタのファイルに変更はありません'),
    'Embed': ('向量化', '埋め込み'),
    'Embedding profile selected. Test to verify retrieval support.': (
        '已选择向量配置。请测试以确认支持检索。', '埋め込みプロファイルを選択しました。テストして検索対応を確認してください。'),
    'Embedding test': ('向量测试', '埋め込みテスト'),
    'Empty text': ('内容为空', 'テキストが空です'),
    'Enable Browser Use slash command': ('启用 Browser Use 斜杠命令', 'Browser Use スラッシュコマンドを有効化'),
    'Enable Computer Use slash command': ('启用 Computer Use 斜杠命令', 'Computer Use スラッシュコマンドを有効化'),
    'Enable background vision': ('启用后台视觉', 'バックグラウンドビジョンを有効化'),
    'Enable code execution for task steps and skills': (
        '为任务步骤和技能启用代码执行', 'タスクステップとスキルのコード実行を有効化'),
    'Enable online memory': ('启用在线记忆', 'オンラインメモリを有効化'),
    'Enable this rule': ('启用该规则', 'このルールを有効化'),
    'Enabled': ('已启用', '有効'),
    'Error': ('错误', 'エラー'),
    'Every': ('每', '間隔:'),
    'Execution timeout seconds': ('执行超时（秒）', '実行タイムアウト（秒）'),
    'Experience rule · {label}': ('经验规则 · {label}', '経験ルール · {label}'),
    'Explain Flow': ('解释流程', 'フローを説明'),
    'Explain This Code': ('解释这段代码', 'このコードを説明'),
    'Explain code': ('解释代码', 'コード説明'),
    'External context / MCP sources': ('外部上下文 / MCP 来源', '外部コンテキスト / MCP ソース'),
    'External context max chars': ('外部上下文最大字符数', '外部コンテキストの最大文字数'),
    'External target request empty': ('外部目标请求为空', '外部ターゲットへのリクエストが空です'),
    'Failed to append selection: {msg}': ('追加所选内容失败：{msg}', '選択部分の追加に失敗しました: {msg}'),
    'Failed to create note: {msg}': ('创建备忘录失败：{msg}', 'メモの作成に失敗しました: {msg}'),
    'Failed to load notes: {msg}': ('加载备忘录失败：{msg}', 'メモの読み込みに失敗しました: {msg}'),
    'Failed to update start on login: {exc}': ('更新“登录时启动”失败：{exc}', 'ログイン時に起動の更新に失敗しました: {exc}'),
    'File changed on disk': ('文件在磁盘上已改动', 'ファイルがディスク上で変更されました'),
    'First profile finished': ('第一个配置完成后', '最初のプロファイルが完了後'),
    'Fix in Main Chat': ('在主对话中修复', 'メインチャットで修正'),
    'Fixed interval': ('固定间隔', '固定間隔'),
    'For more of my works, please visit the homepage.': (
        '想了解我的更多作品，请访问主页。', '他の作品はホームページをご覧ください。'),
    'Forward': ('前进', '進む'),
    'From': ('从', '読み取り元'),
    'From URL': ('来源 URL', '取得元 URL'),
    'From:\n{lang}': ('源语言：\n{lang}', '翻訳元:\n{lang}'),
    'Full Markdown': ('完整 Markdown', '完全な Markdown'),
    'Full-screen screenshot failed. Please try again.': (
        '全屏截图失败。请重试。', '全画面スクリーンショットに失敗しました。もう一度お試しください。'),
    'Function Card': ('函数卡片', '関数カード'),
    'Generate': ('生成', '生成'),
    'Generate Task Capsule via API profile...': ('通过 API 配置生成任务胶囊…', 'API プロファイルでタスクカプセルを生成…'),
    'Generated outputs': ('生成输出', '生成された出力'),
    'Generating Task Capsule in the background.': ('正在后台生成任务胶囊。', 'バックグラウンドでタスクカプセルを生成しています。'),
    'Generating diagram…': ('正在生成图表…', 'ダイアグラムを生成中…'),
    'Google Chrome not found': ('未找到 Google Chrome', 'Google Chrome が見つかりません'),
    'Grammatically analyze': ('语法分析', '文法解析'),
    'Hidden @target page': ('隐藏的 @target 页面', '非表示の @target ページ'),
    'Hide main window': ('隐藏主窗口', 'メインウィンドウを隠す'),
    'History': ('历史', '履歴'),
    'History entries shown': ('历史显示条数', '表示する履歴件数'),
    'Home': ('主页', 'ホーム'),
    'Horizontal Paging': ('横向翻页', '横方向のページめくり'),
    'Hover Compare or Verify to add model branches.': (
        '将鼠标悬停在对比或核验上以添加模型分支。', '比較 / 検証 にマウスを重ねてモデルブランチを追加します。'),
    'How many conversations the History panel renders (newest first). Nothing is deleted and search always scans every conversation. Far right = All.': (
        '历史面板渲染多少条对话（最新在前）。不会删除任何内容，搜索始终扫描全部对话。拖到最右 = 全部。',
        '履歴パネルに表示する会話数（新しい順）。削除は行われず、検索は常に全会話を対象にします。右端 = すべて。'),
    'How many steps of a parallel group run at the same time (1-20, default 5). Higher values finish large groups faster but multiply simultaneous model calls (and Chrome windows for browser steps).': (
        '并行组内同时运行的步骤数（1-20，默认 5）。数值越大，大组完成越快，但同时的模型调用（以及浏览器步骤的 Chrome 窗口）也会成倍增加。',
        '並列グループ内で同時に実行するステップ数（1-20、既定 5）。大きくすると大きなグループは速く終わりますが、同時のモデル呼び出し（ブラウザステップの Chrome ウィンドウも）が倍増します。'),
    'I will write more interesting apps! 🥳': ('我会写出更多有趣的应用！🥳', 'もっと面白いアプリを作ります！🥳'),
    'Idle': ('空闲', '待機中'),
    'If Planner / Router is empty, the default chat profile will be used for planning.': (
        '如果规划器 / 路由为空，将使用默认聊天配置进行规划。',
        'プランナー / ルーターが空の場合、既定のチャットプロファイルでプランニングします。'),
    'Invalid settings': ('设置无效', '設定が無効です'),
    'Jump to Code': ('跳转到代码', 'コードへ移動'),
    'Jump to conversation': ('跳转到对话', '会話へ移動'),
    'Keep background vision history': ('保留后台视觉历史', 'バックグラウンドビジョンの履歴を保持'),
    'Keep the editor window always on top': ('编辑器窗口始终置顶', 'エディタウィンドウを常に手前に表示'),
    'Keep the main window always on top': ('主窗口始终置顶', 'メインウィンドウを常に手前に表示'),
    'Language': ('语言', '言語'),
    'Languages': ('语言列表', '言語'),
    'Large diff — highlighting truncated': ('差异过大 — 高亮已截断', '差分が大きいためハイライトを省略しました'),
    'Latest version:': ('最新版本：', '最新バージョン:'),
    'Launch managed Chrome': ('启动托管 Chrome', '管理された Chrome を起動'),
    'Loading Apple Notes…': ('正在加载 Apple 备忘录…', 'Apple メモを読み込み中…'),
    'Local file': ('本地文件', 'ローカルファイル'),
    'Local file endpoints do not have a web status page.': (
        '本地文件端点没有网页状态页。', 'ローカルファイルのエンドポイントにはウェブ状態ページがありません。'),
    'Local folder': ('本地文件夹', 'ローカルフォルダ'),
    'Localhost': ('本地服务', 'ローカルサービス'),
    'Localhost URLs': ('Localhost 网址', 'Localhost の URL'),
    'Lossless WebP': ('无损 WebP', '可逆圧縮 WebP'),
    'MCP HTTP endpoint': ('MCP HTTP 端点', 'MCP HTTP エンドポイント'),
    'MCP stdio server': ('MCP stdio 服务器', 'MCP stdio サーバー'),
    'Mark as Feature (not a bug)': ('标记为特性（不是 bug）', '仕様としてマーク（バグではない）'),
    'Max parallel steps': ('最大并行步骤数', '最大並列ステップ数'),
    'Memory endpoints': ('记忆端点', 'メモリエンドポイント'),
    'Memory notes': ('记忆笔记', 'メモリノート'),
    'Model': ('模型', 'モデル'),
    'Model quality profile': ('模型质量档案', 'モデル品質プロファイル'),
    'Modify': ('修改', '変更'),
    'More languages': ('更多语言', 'その他の言語'),
    'Move Left': ('左移', '左へ移動'),
    'Move Right': ('右移', '右へ移動'),
    'Name': ('名称', '名前'),
    'Name and endpoint are required.': ('名称和端点为必填。', '名前とエンドポイントは必須です。'),
    'Name is what the "+" menu on the Web / Localhost pill bar shows. Changes apply after Save.': (
        '名称即 Web / Localhost 标签条“+”菜单中显示的内容。保存后生效。',
        '名前は Web / Localhost バーの「+」メニューに表示されます。変更は保存後に反映されます。'),
    'Native shortcut listener is not ready. Check Accessibility/Input Monitoring permissions for Broccoli.': (
        '原生快捷键监听尚未就绪。请检查 Broccoli 的辅助功能/输入监控权限。',
        'ネイティブショートカットリスナーが準備できていません。Broccoli のアクセシビリティ/入力監視の権限を確認してください。'),
    'New': ('新', '新'),
    'New API history': ('新建 API 历史', '新しい API 履歴'),
    'New Claude Code': ('新建 Claude Code', '新しい Claude Code'),
    'New Claude TUI': ('新建 Claude TUI', '新しい Claude TUI'),
    'New Codex': ('新建 Codex', '新しい Codex'),
    'New MCP HTTP source': ('新建 MCP HTTP 来源', '新しい MCP HTTP ソース'),
    'New MCP stdio source': ('新建 MCP stdio 来源', '新しい MCP stdio ソース'),
    'New Terminal': ('新建终端', '新しいターミナル'),
    'New URL…': ('新建网址…', '新しい URL…'),
    'New note "{title}" created in Apple Notes.': (
        '已在 Apple 备忘录中创建新备忘录“{title}”。', 'Apple メモに新しいメモ「{title}」を作成しました。'),
    'New profile': ('新建配置', '新しいプロファイル'),
    'Next instruction to run after the current answer...': (
        '当前回答结束后要执行的下一条指示…', '現在の回答の後に実行する次の指示…'),
    'Next tab': ('下一个标签页', '次のタブ'),
    'No Web tab URLs were found.': ('没有找到 Web 标签页网址。', 'Web タブの URL が見つかりませんでした。'),
    'No active API profile is configured.': ('没有配置可用的 API 配置。', '有効な API プロファイルが設定されていません。'),
    'No active Web, Localhost, or Terminal target is registered as @{alias}.': (
        '没有名为 @{alias} 的活动 Web、Localhost 或终端目标。',
        '@{alias} として登録された有効な Web・Localhost・ターミナルのターゲットはありません。'),
    'No available screen found for capturing.': ('没有可用于截图的屏幕。', 'キャプチャできる画面が見つかりません。'),
    'No current page conversation text was detected.': (
        '未检测到当前页面的对话文本。', '現在のページに会話テキストが検出されませんでした。'),
    'No customized prompts, please add one in Settings': (
        '暂无自定义提示词，请到设置中添加', 'カスタムプロンプトがありません。設定で追加してください'),
    'No embedding profile selected. Retrieval will fall back to keywords.': (
        '未选择向量配置。检索将回退为关键词匹配。', '埋め込みプロファイル未選択。検索はキーワード方式にフォールバックします。'),
    'No executable was found for language: {lang}': (
        '未找到该语言的可执行程序：{lang}', '言語 {lang} の実行ファイルが見つかりませんでした'),
    'No file': ('无文件', 'ファイルなし'),
    'No file open': ('未打开文件', 'ファイルが開かれていません'),
    'No generated output for this conversation yet.': (
        '此对话还没有生成输出。', 'この会話にはまだ生成された出力がありません。'),
    'No generated output yet': ('还没有生成输出', 'まだ生成された出力はありません'),
    'No hidden @target page exists yet. Run an @target once, then turn this option on.': (
        '还没有隐藏的 @target 页面。先运行一次 @target，再开启此选项。',
        '非表示の @target ページはまだありません。@target を一度実行してからこのオプションを有効にしてください。'),
    'No image yet.': ('还没有图片。', 'まだ画像はありません。'),
    'No imported pages detected yet.': ('尚未检测到导入的页面。', 'インポートされたページはまだ検出されていません。'),
    'No online memory source selected.': ('未选择在线记忆来源。', 'オンラインメモリのソースが選択されていません。'),
    'No previous screenshot region found. Take one region screenshot first.': (
        '没有上一次的截图区域。请先做一次区域截图。', '前回のスクリーンショット領域がありません。先に領域スクリーンショットを 1 回撮ってください。'),
    'No profile': ('没有配置', 'プロファイルなし'),
    'No running Agent answer to add a note to.': (
        '没有正在生成的 Agent 回答可以追加指示。', 'メモを追加できる実行中の Agent 回答がありません。'),
    'No saved questions in the current conversation yet.': (
        '当前对话还没有已保存的问题。', '現在の会話に保存済みの質問はまだありません。'),
    'No text was detected in the selected tabs.': (
        '所选标签页中未检测到文本。', '選択したタブでテキストが検出されませんでした。'),
    'Non-OpenAI REST services, referenced as &name in specialized capability selectors.\nWeb search shape: POST {endpoint}/api/web_search with Bearer key (e.g. endpoint https://ollama.com, key from ollama.com/settings/keys).': (
        '非 OpenAI 的 REST 服务，在专项能力选择器中以 &名称 引用。\n网页搜索格式：POST {endpoint}/api/web_search，附 Bearer 密钥（例如端点 https://ollama.com，密钥来自 ollama.com/settings/keys）。',
        'OpenAI 以外の REST サービス。専用能力セレクタで &名前 として参照します。\nウェブ検索形式: POST {endpoint}/api/web_search（Bearer キー付き。例: エンドポイント https://ollama.com、キーは ollama.com/settings/keys から）。'),
    'Not enough text was detected in the selected tabs.': (
        '所选标签页中检测到的文本不足。', '選択したタブで検出されたテキストが不足しています。'),
    'Object Card': ('对象卡片', 'オブジェクトカード'),
    'Off by default. When on, consecutive INDEPENDENT research / generation steps in a plan run at the same time. Terminal and browser steps are never auto-grouped.': (
        '默认关闭。开启后，计划中连续且相互独立的研究/生成步骤会同时运行。终端和浏览器步骤永远不会被自动编组。',
        '既定はオフ。オンにすると、プラン内の連続する独立したリサーチ/生成ステップが同時に実行されます。ターミナルとブラウザのステップは自動グループ化されません。'),
    "Off by default. When on, parallel steps run up to 3 rounds each, post sourced facts to a shared board, see each other's findings, and the board digest feeds the next step. Costs roughly 2-3x more model calls per parallel group.": (
        '默认关闭。开启后，并行步骤各自最多跑 3 轮，把带来源的事实发布到共享板，互相看到对方的发现，板上摘要会输入下一步。每个并行组的模型调用量约为 2-3 倍。',
        '既定はオフ。オンにすると、並列ステップは各 3 ラウンドまで実行し、出典付きの事実を共有ボードに投稿して互いの発見を参照し、ボードの要約が次のステップに渡ります。並列グループあたりのモデル呼び出しは約 2〜3 倍になります。'),
    'Old': ('旧', '旧'),
    'On by default. While the editor is open, its open files (current, incl. unsaved text) are attached to @web / @localhost / @terminal requests so those targets can propose edits. Turn off if you do not want editor files leaving for unrelated @ requests.': (
        '默认开启。编辑器打开期间，其打开的文件（当前内容，含未保存文本）会附加到 @web / @localhost / @terminal 请求中，便于这些目标提出修改。若不希望编辑器文件随无关的 @ 请求外发，请关闭。',
        '既定はオン。エディタを開いている間、開いているファイル（未保存の内容を含む現在のテキスト）が @web / @localhost / @terminal リクエストに添付され、編集の提案を受けられます。無関係な @ リクエストにエディタのファイルを送りたくない場合はオフにしてください。'),
    'Online Memory Source': ('在线记忆来源', 'オンラインメモリソース'),
    'Online memory': ('在线记忆', 'オンラインメモリ'),
    'Open All Attachments in Editor': ('在编辑器中打开全部附件', 'すべての添付ファイルをエディタで開く'),
    'Open All In Browser': ('在浏览器中打开全部', 'すべてブラウザで開く'),
    'Open Detail': ('打开详情', '詳細を開く'),
    'Open each task in a new Chrome tab/window': (
        '每个任务在新的 Chrome 标签页/窗口中打开', '各タスクを新しい Chrome タブ/ウィンドウで開く'),
    'Open in Editor': ('在编辑器中打开', 'エディタで開く'),
    'Open in Reader': ('在阅读器中打开', 'リーダーで開く'),
    'Open in new tab': ('在新标签页中打开', '新しいタブで開く'),
    'Open in the editor window': ('在编辑器窗口中打开', 'エディタウィンドウで開く'),
    'Open or start an Agent conversation before adding a queued prompt.': (
        '请先打开或开始一个 Agent 对话，再添加排队提示词。',
        'キューにプロンプトを追加する前に、Agent の会話を開くか開始してください。'),
    'Optional environment variables, one per line:\nKEY=value\nGITHUB_PERSONAL_ACCESS_TOKEN=...': (
        '可选环境变量，每行一个：\nKEY=value\nGITHUB_PERSONAL_ACCESS_TOKEN=...',
        '任意の環境変数（1 行に 1 つ）:\nKEY=value\nGITHUB_PERSONAL_ACCESS_TOKEN=...'),
    'Optional shortcut': ('可选快捷键', '任意のショートカット'),
    'Optional working directory': ('可选工作目录', '任意の作業ディレクトリ'),
    'Optional. Leave empty, then click Discover.': (
        '可选。留空后点击“发现”。', '任意。空のままにして Discover をクリックしてください。'),
    'PDF attachment: max pages (All = no limit)': (
        'PDF 附件：最大页数（全部 = 不限）', 'PDF 添付: 最大ページ数（すべて = 無制限）'),
    'Parallel fact board': ('并行事实板', '並列ファクトボード'),
    'Permanent memory': ('永久记忆', '永続メモリ'),
    'Persistent memory about the user, preferences, background, and long-term facts.': (
        '关于用户、偏好、背景和长期事实的持久记忆。', 'ユーザー・好み・背景・長期的な事実に関する永続メモリ。'),
    'Pin window position': ('固定窗口位置', 'ウィンドウ位置を固定'),
    'Plan': ('计划', 'プラン'),
    'Polish': ('润色', '推敲'),
    'Prefer displayed history if short': ('对话较短时优先使用界面上显示的历史', '短い場合は表示中の履歴を優先'),
    'Press shortcut...': ('请按下快捷键…', 'ショートカットを押してください…'),
    'Previous command is still running...': ('上一条命令仍在运行…', '前のコマンドがまだ実行中です…'),
    'Previous tab': ('上一个标签页', '前のタブ'),
    'Profile name': ('配置名称', 'プロファイル名'),
    'Profile sources:\n': ('配置来源：\n', 'プロファイルのソース:\n'),
    'Profile sources: none': ('配置来源：无', 'プロファイルのソース: なし'),
    'Prompt body': ('提示词正文', 'プロンプト本文'),
    'Prompt this web page...': ('向这个网页提问…', 'このウェブページにプロンプトを送る…'),
    'Prompt used by the background vision observer.': (
        '后台视觉观察器使用的提示词。', 'バックグラウンドビジョンの観察者が使うプロンプト。'),
    'Question branches': ('问题分支', '質問ブランチ'),
    'Queue': ('排队', 'キュー'),
    'Queue is available while this Agent conversation is running.': (
        '排队功能仅在该 Agent 对话运行时可用。', 'キューはこの Agent 会話の実行中に利用できます。'),
    'Queued prompts': ('排队中的提示词', 'キューに入ったプロンプト'),
    'Quit': ('退出', '終了'),
    'Re-translate This Sentence': ('重新翻译这句', 'この文を再翻訳'),
    'Read-only': ('只读', '読み取り専用'),
    'Reading {i}/{n}: {label}...': ('正在读取 {i}/{n}：{label}…', '読み込み中 {i}/{n}: {label}…'),
    'Record Edge show/hide shortcut': ('录制“贴边显示/隐藏”快捷键', '画面端の表示/非表示ショートカットを記録'),
    'Record Main window shortcut': ('录制主窗口快捷键', 'メインウィンドウのショートカットを記録'),
    'Record Same-position shot shortcut': ('录制同位置截图快捷键', '同位置スクリーンショットのショートカットを記録'),
    'Record Screenshot shortcut': ('录制截图快捷键', 'スクリーンショットのショートカットを記録'),
    'Refine This Step': ('细化这一步', 'このステップを詳細化'),
    'Refresh': ('刷新', '再読み込み'),
    'Regenerate': ('重新生成', '再生成'),
    'Reload': ('重新载入', '再読み込み'),
    'Remember chat history': ('记住聊天历史', 'チャット履歴を記憶'),
    'Remove branch': ('移除分支', 'ブランチを削除'),
    'Remove from Compare': ('从对比中移除', '比較から削除'),
    'Remove this saved comment from the menu': ('从菜单中移除这条已存评论', 'この保存済みコメントをメニューから削除'),
    'Reopen': ('重新打开', '再オープン'),
    'Replace': ('替换', '置き換え'),
    'Replace prompt input': ('替换提示词输入框内容', 'プロンプト入力欄を置き換え'),
    'Replace prompt with selection': ('用所选内容替换提示词', '選択部分でプロンプトを置き換え'),
    'Replace terminal input': ('替换终端输入框内容', 'ターミナル入力欄を置き換え'),
    'Resolved': ('已解决', '解決済み'),
    'Resume edge auto-hide': ('恢复贴边自动隐藏', '画面端の自動非表示を再開'),
    'Reveal in Finder': ('在访达中显示', 'Finder に表示'),
    'Revert ALL open files to before this turn': ('把所有打开的文件回退到本轮之前', '開いている全ファイルをこのターン前に戻す'),
    'Revert to this version': ('回退到此版本', 'このバージョンに戻す'),
    'Revise': ('修订', '修正'),
    'Role: {role} · URL: {url}': ('角色：{role} · URL：{url}', 'ロール: {role} · URL: {url}'),
    'Rule (natural language)': ('规则（自然语言）', 'ルール（自然言語）'),
    'Rules distilled from real task evidence (builtin / auto-learned / user-taught). Double-click a row to edit; edits recompile in the background and never block the UI. Rules guide the automation model and tune worker parameters; safety gates always stay on.': (
        '从真实任务证据中提炼的规则（内置 / 自动学习 / 用户教授）。双击一行可编辑；编辑在后台重新编译，绝不阻塞界面。规则用于引导自动化模型并调整工作进程参数；安全闸始终开启。',
        '実際のタスク証拠から抽出したルール（ビルトイン / 自動学習 / ユーザー指定）。行をダブルクリックで編集。編集はバックグラウンドで再コンパイルされ、UI をブロックしません。ルールは自動化モデルを導き、ワーカーのパラメータを調整します。安全ゲートは常に有効です。'),
    'Run a shell command...': ('运行一条 shell 命令…', 'シェルコマンドを実行…'),
    'Run independent steps in parallel automatically': ('自动并行运行相互独立的步骤', '独立したステップを自動的に並列実行'),
    'Same-position screenshot': ('同位置截图', '同位置スクリーンショット'),
    'Save': ('保存', '保存'),
    'Save As': ('另存为', '別名で保存'),
    'Save As…': ('另存为…', '別名で保存…'),
    'Save current page to API history': ('把当前页面存入 API 历史', '現在のページを API 履歴に保存'),
    'Save profile (keep Settings open)': ('保存配置（保持设置打开）', 'プロファイルを保存（設定は開いたまま）'),
    'Save screenshots locally': ('在本地保存截图', 'スクリーンショットをローカルに保存'),
    'Saved': ('已保存', '保存済み'),
    'Saved Comments': ('已存评论', '保存済みコメント'),
    'Saved prompts': ('已存提示词', '保存済みプロンプト'),
    'Saved {name}.': ('已保存 {name}。', '{name} を保存しました。'),
    'Screenshot': ('截图', 'スクリーンショット'),
    'Screenshot failed. Please try again.': ('截图失败。请重试。', 'スクリーンショットに失敗しました。もう一度お試しください。'),
    'Screenshot was added to Terminal attachments. Terminal does not support auto-send.': (
        '截图已加入终端附件。终端不支持自动发送。',
        'スクリーンショットをターミナルの添付に追加しました。ターミナルは自動送信に対応していません。'),
    'Search': ('搜索', '検索'),
    'Search command history': ('搜索命令历史', 'コマンド履歴を検索'),
    'Search favorite commands': ('搜索收藏的命令', 'お気に入りコマンドを検索'),
    'Search favorites': ('搜索收藏', 'お気に入りを検索'),
    'Search history': ('搜索历史', '履歴を検索'),
    'Search links': ('搜索链接', 'リンクを検索'),
    'Search notes': ('搜索备忘录', 'メモを検索'),
    'Search sessions': ('搜索会话', 'セッションを検索'),
    'Select All': ('全选', 'すべて選択'),
    'Selection appended to "{title}".': ('所选内容已追加到“{title}”。', '選択部分を「{title}」に追加しました。'),
    'Send open editor files to @web / @terminal targets': (
        '把编辑器打开的文件发送给 @web / @terminal 目标', 'エディタで開いているファイルを @web / @terminal ターゲットに送る'),
    "Send selected tabs' latest replies here": ('把所选标签页的最新回复发到这里', '選択したタブの最新返信をここに送る'),
    'Set an Agent API profile in Settings before running queued prompts.': (
        '运行排队提示词前，请先在设置中指定 Agent 的 API 配置。',
        'キューのプロンプトを実行する前に、設定で Agent の API プロファイルを指定してください。'),
    'Set as Default for This File Type': ('设为此文件类型的默认方式', 'このファイル形式の既定に設定'),
    'Set as Edit Target': ('设为编辑目标', '編集ターゲットに設定'),
    'Share': ('分享', '共有'),
    'Share Full Markdown...': ('分享完整 Markdown…', '完全な Markdown を共有…'),
    'Share a live fact board between parallel steps': ('在并行步骤间共享实时事实板', '並列ステップ間でライブのファクトボードを共有'),
    'Share as Image': ('以图片形式分享', '画像として共有'),
    'Shared fact board · ': ('共享事实板 · ', '共有ファクトボード · '),
    'Shell history (~/.zsh_history)': ('Shell 历史（~/.zsh_history）', 'シェル履歴（~/.zsh_history）'),
    'Shortcut unavailable': ('快捷键不可用', 'ショートカットを利用できません'),
    'Show Translation Panel': ('显示翻译面板', '翻訳パネルを表示'),
    'Show floating vision window': ('显示悬浮视觉窗口', 'フローティングビジョンウィンドウを表示'),
    'Show in Logic Map': ('在逻辑图中显示', 'ロジックマップに表示'),
    'Show retrieved refs': ('显示检索到的引用', '取得した参照を表示'),
    'Skill body': ('技能正文', 'スキル本文'),
    'Skills': ('技能', 'スキル'),
    'Skip retrieval when blank prompt is sent': ('发送空提示词时跳过检索', '空プロンプト送信時は検索をスキップ'),
    'Slash task empty': ('斜杠任务为空', 'スラッシュタスクが空です'),
    'Snooze hidden pages when idle': ('空闲时暂停隐藏页面', 'アイドル時に非表示ページを休止'),
    'Start Broccoli on login': ('登录时启动 Broccoli', 'ログイン時に Broccoli を起動'),
    'Start new Agent conversation first': ('先开启新的 Agent 对话', '先に新しい Agent 会話を開始'),
    'Start on login': ('登录时启动', 'ログイン時に起動'),
    'Step review pause': ('步骤复核停顿', 'ステップレビューの一時停止'),
    'Steps': ('步骤', 'ステップ'),
    'Steps (natural language)': ('步骤（自然语言）', 'ステップ（自然言語）'),
    'Stop edge auto-hide': ('停止贴边自动隐藏', '画面端の自動非表示を停止'),
    'Strictness': ('严格度', '厳格さ'),
    'Summarize': ('总结', '要約'),
    'Sync current web conversation to API': ('把当前网页对话同步到 API', '現在のウェブ会話を API に同期'),
    'Sync failed: no source returned memory text.': (
        '同步失败：没有来源返回记忆文本。', '同期失敗: メモリテキストを返したソースがありません。'),
    'Sync failed: no source selected.': ('同步失败：未选择来源。', '同期失敗: ソースが選択されていません。'),
    'Sync failed: no target selected.': ('同步失败：未选择目标。', '同期失敗: ターゲットが選択されていません。'),
    'Take screenshot': ('截图', 'スクリーンショットを撮る'),
    'Target language': ('目标语言', '翻訳先の言語'),
    'Task Capsule': ('任务胶囊', 'タスクカプセル'),
    'Task Capsule generation returned an invalid result.': (
        '任务胶囊生成返回了无效结果。', 'タスクカプセルの生成が無効な結果を返しました。'),
    'Task Capsule generation returned empty output.': (
        '任务胶囊生成返回了空输出。', 'タスクカプセルの生成結果が空でした。'),
    'Terminal': ('终端', 'ターミナル'),
    'Terminal @ target not running': ('终端 @ 目标未在运行', 'ターミナルの @ ターゲットが実行されていません'),
    'Terminal shell mode': ('终端 shell 模式', 'ターミナルのシェルモード'),
    'Test': ('测试', 'テスト'),
    'Testing…': ('测试中…', 'テスト中…'),
    'TextEdit': ('文本编辑', 'テキストエディット'),
    'Thank you for your kind support! 😊': ('感谢您的支持！😊', 'ご支援ありがとうございます！😊'),
    'Thank you for your support!': ('感谢您的支持！', 'ご支援ありがとうございます！'),
    'Thanks for your love.': ('感谢您的喜爱。', 'ご愛顧ありがとうございます。'),
    'The browser could not finish downloading {name}.': (
        '浏览器未能完成下载：{name}。', 'ブラウザは {name} のダウンロードを完了できませんでした。'),
    'The current tab does not support attachment auto-send.': (
        '当前标签页不支持附件自动发送。', '現在のタブは添付ファイルの自動送信に対応していません。'),
    'The fixed Browser Use Chrome instance is already reachable. Open or select the page you want, then run a /browser use task.': (
        '固定的 Browser Use Chrome 实例已可连接。打开或选中你需要的页面，然后运行 /browser use 任务。',
        '固定の Browser Use Chrome インスタンスには既に接続できます。目的のページを開くか選択して、/browser use タスクを実行してください。'),
    'The language setting will apply after Broccoli restarts.': (
        '语言设置将在 Broccoli 重启后生效。', '言語設定は Broccoli の再起動後に適用されます。'),
    'The previous screenshot region is outside the current screen layout.': (
        '上一次的截图区域在当前屏幕布局之外。', '前回のスクリーンショット領域は現在の画面レイアウトの外にあります。'),
    'The queued conversation file could not be found.': (
        '找不到排队对话的文件。', 'キューに入れた会話ファイルが見つかりません。'),
    'The web page did not confirm that the attachment was added. The attachment was kept in Broccoli.': (
        '网页没有确认附件已添加。附件仍保留在 Broccoli 中。',
        'ウェブページは添付ファイルの追加を確認しませんでした。添付ファイルは Broccoli に保持されています。'),
    'There is no conversation content to summarize.': ('没有可总结的对话内容。', '要約できる会話内容がありません。'),
    'There is no conversation markdown to share.': ('没有可分享的对话 Markdown。', '共有できる会話の Markdown がありません。'),
    'There is no saved profile to delete.': ('没有可删除的已存配置。', '削除できる保存済みプロファイルがありません。'),
    'There is no terminal text to share.': ('没有可分享的终端文本。', '共有できるターミナルのテキストがありません。'),
    'There is no text to send.': ('没有可发送的文本。', '送信できるテキストがありません。'),
    'Thinking…': ('思考中…', '考え中…'),
    'This app is open-sourced.': ('本应用已开源。', 'このアプリはオープンソースです。'),
    'This cached page was discarded after being idle. Run the @target once to reload it, then reveal it.': (
        '这个缓存页面因闲置已被丢弃。请先运行一次 @target 重新加载，再显示它。',
        'このキャッシュページはアイドル状態のため破棄されました。@target を一度実行して再読み込みしてから表示してください。'),
    'This conversation has been deleted.': ('该对话已被删除。', 'この会話は削除されました。'),
    'This permanently deletes the session transcript from disk and removes it from history. This cannot be undone.\n\n': (
        '这会从磁盘上永久删除该会话记录，并将其从历史中移除。此操作无法撤销。\n\n',
        'セッションのトランスクリプトをディスクから完全に削除し、履歴からも取り除きます。この操作は元に戻せません。\n\n'),
    'To': ('到', '書き込み先'),
    'To URL': ('目标 URL', '送信先 URL'),
    'To:\n{lang}': ('目标语言：\n{lang}', '翻訳先:\n{lang}'),
    'Translate': ('翻译', '翻訳'),
    'Translate the selected area': ('翻译所选区域', '選択範囲を翻訳'),
    'Type a message...': ('输入消息…', 'メッセージを入力…'),
    'Type a request after @{alias}.': ('请在 @{alias} 后输入请求内容。', '@{alias} の後にリクエストを入力してください。'),
    'Type a task after {command}.': ('请在 {command} 后输入任务内容。', '{command} の後にタスクを入力してください。'),
    'Type terminal input...': ('输入终端内容…', 'ターミナル入力…'),
    'URL': ('URL', 'URL'),
    'Unknown @ target': ('未知的 @ 目标', '不明な @ ターゲット'),
    'Unpin window position': ('取消固定窗口位置', 'ウィンドウ位置の固定を解除'),
    'Unset Edit Target': ('取消编辑目标', '編集ターゲットを解除'),
    'Update linked API history': ('更新已关联的 API 历史', 'リンク済み API 履歴を更新'),
    'Use Launch system Chrome for the most reliable setup. Broccoli uses this dedicated profile folder; sign in there once, then later Browser Use tasks reuse that login state.': (
        '最稳妥的设置是使用“启动系统 Chrome”。Broccoli 使用这个专用配置文件夹；在里面登录一次，之后的 Browser Use 任务会复用该登录状态。',
        '最も確実なのは「システムの Chrome を起動」を使う設定です。Broccoli はこの専用プロファイルフォルダを使用します。一度サインインすれば、以後の Browser Use タスクはそのログイン状態を再利用します。'),
    'Use as context for the next message': ('用作下一条消息的上下文', '次のメッセージのコンテキストとして使用'),
    'Use bash instead': ('改用 bash', '代わりに bash を使用'),
    'Use embedding for Generated outputs used as context': (
        '用作上下文的生成输出使用向量检索', 'コンテキストとして使う生成出力に埋め込みを使用'),
    'Use embedding for WebFetch page content': ('WebFetch 页面内容使用向量检索', 'WebFetch のページ内容に埋め込みを使用'),
    'Use embedding for external context when long': ('外部上下文过长时使用向量检索', '外部コンテキストが長い場合は埋め込みを使用'),
    'Use external context / MCP sources': ('使用外部上下文 / MCP 来源', '外部コンテキスト / MCP ソースを使用'),
    'Use memory retrieval': ('使用记忆检索', 'メモリ検索を使用'),
    'Use this Chrome window to open pages, sign in, and prepare background tabs. When "Open each task in a new Chrome tab/window" is off, Browser Use will continue from this instance.': (
        '用这个 Chrome 窗口打开页面、登录并准备后台标签页。当“每个任务在新的 Chrome 标签页/窗口中打开”关闭时，Browser Use 会从这个实例继续。',
        'この Chrome ウィンドウでページを開き、サインインし、バックグラウンドタブを準備してください。「各タスクを新しい Chrome タブ/ウィンドウで開く」がオフの場合、Browser Use はこのインスタンスから続行します。'),
    'Uses the external CuaDriver.app in standalone mode. Broccoli only displays installation guidance and never runs the installer. Target display limits window selection; it does not move or launch windows there. If no matching window exists, the task stops instead of controlling another screen.': (
        '以独立模式使用外部 CuaDriver.app。Broccoli 只显示安装指引，绝不会运行安装器。目标显示器只限制窗口选择范围；不会把窗口移动或启动到那里。若没有匹配的窗口，任务会停止，而不是去控制另一块屏幕。',
        '外部の CuaDriver.app をスタンドアロンモードで使用します。Broccoli はインストール手順を表示するだけで、インストーラは実行しません。ターゲットディスプレイはウィンドウ選択を制限するもので、ウィンドウの移動や起動は行いません。一致するウィンドウがなければ、別の画面を操作せずタスクは停止します。'),
    'VS Code': ('VS Code', 'VS Code'),
    'Version {v}': ('版本 {v}', 'バージョン {v}'),
    'Vertical Paging': ('纵向翻页', '縦方向のページめくり'),
    'Viewing v%d (read-only)': ('正在查看 v%d（只读）', 'v%d を表示中（読み取り専用）'),
    'Web': ('网页', 'ウェブ'),
    'Web URLs': ('Web 网址', 'Web の URL'),
    'Web conversation is being captured in the background.': (
        '正在后台捕获网页对话。', 'ウェブ会話をバックグラウンドで取得しています。'),
    'Checking…': ('检查中…', '確認中…'),
    'Capturing the full conversation…': ('正在滚动抓取完整对话…', '会話全体をスクロールして取得しています…'),
    'full page scan ({n} windows)': ('整页扫描（{n} 个窗口）', 'ページ全体スキャン（{n} ウィンドウ）'),
    'Web pages': ('网页', 'ウェブページ'),
    'WebFetch download folder': ('WebFetch 下载文件夹', 'WebFetch のダウンロードフォルダ'),
    'Window & startup': ('窗口与启动', 'ウィンドウと起動'),
    'Your prompts here...': ('在这里输入提示词…', 'ここにプロンプトを入力…'),
    'e.g. ollama-search': ('例如 ollama-search', '例: ollama-search'),
    'hours': ('小时', '時間'),
    'none': ('无', 'なし'),
    '{checked} selected · {total} questions': ('已选 {checked} · 共 {total} 个问题', '{checked} 選択 · 全 {total} 件の質問'),
    '{name} history': ('{name} 历史', '{name} 履歴'),
    '{n} Comments': ('{n} 条评论', 'コメント {n} 件'),
    '{n} active · {done}/{total} steps': ('{n} 个进行中 · 步骤 {done}/{total}', '{n} 件実行中 · ステップ {done}/{total}'),
    '{n} favorite{s}': ('{n} 条收藏', 'お気に入り {n} 件'),
    '{n} item{s} · {label}': ('{n} 项 · {label}', '{n} 件 · {label}'),
    '{n} session{s} · {p}': ('{n} 个会话 · {p}', '{n} セッション · {p}'),
    '{p} pages · {b} batch{es}': ('{p} 页 · {b} 批', '{p} ページ · {b} バッチ'),
    '{title} — coming in a later update': ('{title} — 将在后续更新中提供', '{title} — 今後のアップデートで提供予定'),
    'ℹ️ About': ('ℹ️ 关于', 'ℹ️ このアプリについて'),
    '← Back': ('← 后退', '← 戻る'),
    '→ Forward': ('→ 前进', '→ 進む'),
    '⚙️ Settings': ('⚙️ 设置', '⚙️ 設定'),
    '⛔️ Stop': ('⛔️ 停止', '⛔️ 停止'),
    '📥 Queue': ('📥 排队', '📥 予約'),
    '✓ Service reachable — {n} result{s} for "test".': (
        '✓ 服务可达 — “test”返回 {n} 条结果。', '✓ サービスに接続可能 — 「test」で {n} 件の結果。'),
    '✗ Test failed: {msg}': ('✗ 测试失败：{msg}', '✗ テスト失敗: {msg}'),
    '🌐 Language': ('🌐 语言', '🌐 言語'),
    '🆕 Check for Updates': ('🆕 检查更新', '🆕 アップデートを確認'),
    '👀 Show/Hide dock icon': ('👀 显示/隐藏 Dock 图标', '👀 Dock アイコンを表示/非表示'),
    '👁 Show hidden @target page': ('👁 显示隐藏的 @target 页面', '👁 非表示の @target ページを表示'),
    '🔺 Send': ('🔺 发送', '🔺 送信'),
    '🛠️ Start on login': ('🛠️ 登录时启动', '🛠️ ログイン時に起動'),
    '🥦 Start Broccoli!': ('🥦 启动 Broccoli！', '🥦 Broccoli を起動！'),
    '🪟 Show on all Spaces': ('🪟 在所有空间显示', '🪟 すべてのスペースで表示'),
    # ---- One-click update (window_update) ----
    'Install update:': ('安装更新：', 'アップデート:'),
    'Update Now': ('立即更新', '今すぐ更新'),
    'Connecting…': ('连接中…', '接続中…'),
    'Installing…': ('安装中…', '更新中…'),
    'Downloading… {done} / {total} MB': ('下载中… {done} / {total} MB', 'ダウンロード中… {done} / {total} MB'),
    'Verifying the download…': ('正在校验下载的文件…', 'ダウンロードしたファイルを検証中…'),
    'Opening the installer…': ('正在打开安装包…', 'インストーラを開いています…'),
    'Copying the new version…': ('正在复制新版本…', '新しいバージョンをコピー中…'),
    'Checking the developer signature…': ('正在检查开发者签名…', '開発元の署名を確認中…'),
    'Restarting Broccoli to finish the update…': ('正在重启 Broccoli 以完成更新…', 'アップデートを完了するため Broccoli を再起動しています…'),
    'Broccoli was updated to v{v}.': ('Broccoli 已更新到 v{v}。', 'Broccoli は v{v} にアップデートされました。'),
    'The last update could not be installed ({reason}). Click Update Now to try again.': (
        '上次更新未能安装（{reason}）。点击「立即更新」重试。',
        '前回のアップデートをインストールできませんでした（{reason}）。「今すぐ更新」で再試行してください。'),
    'This release has no installer package.': ('这个版本没有提供安装包。', 'このリリースにはインストーラが含まれていません。'),
    'This release has no installer package; use the Github button.': (
        '这个版本没有提供安装包，请使用 Github 按钮。',
        'このリリースにはインストーラがありません。Github ボタンを使ってください。'),
    'Download canceled.': ('下载已取消。', 'ダウンロードをキャンセルしました。'),
    'Download failed (HTTP {code}).': ('下载失败（HTTP {code}）。', 'ダウンロードに失敗しました（HTTP {code}）。'),
    'Download interrupted: {err}': ('下载中断：{err}', 'ダウンロードが中断されました: {err}'),
    'The download is damaged (checksum mismatch). Please try again.': (
        '下载的文件已损坏（校验值不一致），请重试。',
        'ダウンロードしたファイルが破損しています（チェックサム不一致）。もう一度お試しください。'),
    'Could not open the downloaded installer.': ('无法打开下载的安装包。', 'ダウンロードしたインストーラを開けませんでした。'),
    'The installer does not contain Broccoli.': ('安装包里没有 Broccoli。', 'インストーラに Broccoli が含まれていません。'),
    'Could not copy the new version: {err}': ('无法复制新版本：{err}', '新しいバージョンをコピーできませんでした: {err}'),
    'Could not check the signature: {err}': ('无法检查签名：{err}', '署名を確認できませんでした: {err}'),
    'The update is not signed by the Broccoli developer, so it was not installed.': (
        '这个更新不是 Broccoli 开发者签名的，因此没有安装。',
        'このアップデートは Broccoli の開発元による署名がないため、インストールしませんでした。'),
    'The installer holds an older version (v{v}); nothing was changed.': (
        '安装包里是更旧的版本（v{v}），没有做任何更改。',
        'インストーラの中身は古いバージョン（v{v}）のため、何も変更していません。'),
    'Could not prepare the update: {err}': ('无法准备更新：{err}', 'アップデートを準備できませんでした: {err}'),
    'Update failed: {err}': ('更新失败：{err}', 'アップデートに失敗しました: {err}'),
    "Can't install automatically ({reason}). The installer is open: drag Broccoli into Applications.": (
        '无法自动安装（{reason}）。安装包已打开：请把 Broccoli 拖进「应用程序」。',
        '自動でインストールできません（{reason}）。インストーラを開きました。Broccoli を「アプリケーション」にドラッグしてください。'),
    'automatic install needs macOS': ('自动安装需要 macOS', '自動インストールには macOS が必要です'),
    'Broccoli is not running from an installed app': ('Broccoli 不是从已安装的 App 运行的', 'Broccoli がインストール済みのアプリから起動していません'),
    'macOS is running Broccoli from a temporary copy; move it into Applications first': (
        'macOS 正在从临时副本运行 Broccoli，请先把它移到「应用程序」',
        'macOS が一時コピーから Broccoli を起動しています。先に「アプリケーション」へ移動してください'),
    'no permission to replace {path}': ('没有替换 {path} 的权限', '{path} を置き換える権限がありません'),
    # ---- Settings page titles, page list and search (2026-10-16) ----
    'Jump to a page': (
        '跳转到某一页',
        'ページへ移動'),
    'Search settings': (
        '搜索设置',
        '設定を検索'),
    'No matching settings': (
        '没有匹配的设置',
        '一致する設定はありません'),
    'Window & agent plan': (
        '窗口与 Agent 计划',
        'ウィンドウと Agent プラン'),
    'History & iCloud': (
        '历史与 iCloud',
        '履歴と iCloud'),
    'Retrieval thresholds': (
        '检索门槛',
        '検索のしきい値'),
    'Shortcuts & tools': (
        '快捷键与工具',
        'ショートカットとツール'),
    'Web & files': (
        '网页与文件',
        'Web とファイル'),
    'External context & MCP': (
        '外部上下文与 MCP',
        '外部コンテキストと MCP'),
    'Code execution': (
        '代码执行',
        'コード実行'),
    'Background vision storage': (
        '后台视觉存储',
        'バックグラウンドビジョンの保存'),
    'Web & Localhost URLs': (
        'Web 与 Localhost 网址',
        'Web と Localhost の URL'),
    'Model roles': (
        '模型分工',
        'モデルの役割'),
    'Online memory sync': (
        '在线记忆同步',
        'オンラインメモリ同期'),
    'How the windows behave and start, and how agent plan steps pause and run in parallel.': (
        '窗口的行为与启动方式，以及 Agent 计划步骤的暂停与并行。',
        'ウィンドウの動作と起動、Agent プランのステップの一時停止と並列実行。'),
    'How much conversation history is kept, and iCloud remote task options.': (
        '保留多少对话历史，以及 iCloud 远程任务选项。',
        '会話履歴の保持量と、iCloud リモートタスクのオプション。'),
    'How similar a saved record must be before it is added to a request as context.': (
        '已存记录要多相似，才会作为上下文加入请求。',
        '保存済みレコードを文脈としてリクエストに加えるのに必要な類似度。'),
    'Global keyboard shortcuts, the terminal shell mode and the screenshot annotation pen.': (
        '全局快捷键、终端 shell 模式和截图批注画笔。',
        'グローバルショートカット、ターミナルのシェルモード、スクリーンショットの注釈ペン。'),
    'Web / Localhost sending, embeddings for fetched content, downloads, PDF attachments and userscripts.': (
        'Web / Localhost 发送、抓取内容的向量化、下载、PDF 附件和用户脚本。',
        'Web / Localhost への送信、取得内容の埋め込み、ダウンロード、PDF 添付、ユーザースクリプト。'),
    'Extra context sources and MCP tools that requests can draw on.': (
        '请求可以使用的额外上下文来源和 MCP 工具。',
        'リクエストが利用できる追加のコンテキストソースと MCP ツール。'),
    'Whether the model may run code, and which runner handles each language.': (
        '是否允许模型运行代码，以及每种语言由哪个运行器执行。',
        'モデルにコードの実行を許可するかと、言語ごとのランナー。'),
    'Periodic screenshots analyzed in the background: which models, and how often.': (
        '在后台定时截图并分析：用哪些模型、多久一次。',
        'バックグラウンドで定期的にスクリーンショットを解析：使うモデルと頻度。'),
    'How background vision results and screenshots are kept, and the prompt it uses.': (
        '后台视觉结果与截图的保存方式，以及它使用的提示词。',
        'バックグラウンドビジョンの結果とスクリーンショットの保存方法、使用するプロンプト。'),
    'Let the agent drive a separate Chrome to open pages, click and fill in forms.': (
        '让 Agent 控制一个独立的 Chrome 打开网页、点击和填写表单。',
        'Agent が専用の Chrome を操作して、ページを開き、クリックし、フォームに入力します。'),
    'Let the agent operate desktop apps through CuaDriver.': (
        '让 Agent 通过 CuaDriver 操作桌面应用。',
        'Agent が CuaDriver を通じてデスクトップアプリを操作します。'),
    'Rules learned from past desktop tasks that guide future ones.': (
        '从过往桌面任务中学到、用来指导后续任务的规则。',
        '過去のデスクトップタスクから学び、今後のタスクに活かすルール。'),
    'Reusable comments you can add to a running agent task.': (
        '可以添加到正在运行的 Agent 任务中的常用评论。',
        '実行中の Agent タスクに追加できる再利用可能なコメント。'),
    'The pages listed in the "+" menu of the Web / Localhost bar, and their order.': (
        'Web / Localhost 栏「+」菜单中列出的页面及其顺序。',
        'Web / Localhost バーの「+」メニューに表示されるページとその順序。'),
    'Which profile handles chat, planning, embeddings and each specialized step.': (
        '聊天、规划、向量和各类专项步骤分别由哪个配置处理。',
        'チャット、計画、埋め込み、各専門ステップをどのプロファイルが担当するか。'),
    'How well each model does on agent steps, used when choosing models.': (
        '各模型在 Agent 步骤中的表现，选择模型时参考。',
        '各モデルの Agent ステップでの成績。モデル選択の参考になります。'),
    'Facts about you that every request can use, and how long dynamic memory is kept.': (
        '每次请求都可以使用的关于你的信息，以及动态记忆的保留时长。',
        'すべてのリクエストで使えるあなたに関する情報と、動的メモリの保持期間。'),
    'Copy memory text from source pages to target pages on a schedule.': (
        '按计划把记忆文本从来源页面复制到目标页面。',
        'メモリのテキストを定期的にソースページからターゲットページへコピーします。'),
    'The URLs and files that online memory reads from and writes to.': (
        '在线记忆读取和写入的网址与文件。',
        'オンラインメモリが読み書きする URL とファイル。'),
    'Languages for model-generated content; the first one is your main language.': (
        '模型生成内容使用的语言；第一项是你的主要语言。',
        'モデルが生成する内容の言語。最初の項目がメイン言語です。'),
    'Reusable prompts you can insert; {text} stands for what you type.': (
        '可以插入的常用提示词；{text} 代表你输入的内容。',
        '挿入できる再利用可能なプロンプト。{text} は入力した内容を表します。'),
    'Reusable instructions the agent can run as a step; each needs a name and a description.': (
        'Agent 可以作为步骤运行的可复用指令；每个都需要名称和描述。',
        'Agent がステップとして実行できる再利用可能な指示。それぞれ名前と説明が必要です。'),
    # ---- Conversation reading-position chooser (2026-10-17) ----
    'Back where you left off': ('已回到上次的位置', '前回の位置に戻りました'),
    'Back to top': ('回到顶部', '先頭へ戻る'),
    'Back to bottom': ('回到底部', '末尾へ移動'),
    'Stay here': ('停留在这里', 'このまま'),
    # ---- Generated outputs: edit in place + learn from the edit (2026-10-18) ----
    'Done': ('完成', '完了'),
    'Save your edits; Broccoli learns your preferences from them': (
        '保存修改，Broccoli 会从中学习你的偏好',
        '編集を保存します。Broccoli がそこからあなたの好みを学習します'),
    'Saved · learning from your edits…': ('已保存 · 正在从你的修改中学习…', '保存しました · 編集内容から学習中…'),
    'Learned {n} preference(s) · Settings → Memory': ('已记住 {n} 条偏好 · 设置 → 记忆', '好みを {n} 件記憶しました · 設定 → メモリ'),
    'Saved · nothing general to learn from this edit': (
        '已保存 · 这次修改里没有可总结的通用偏好',
        '保存しました · 今回の編集から一般的な好みは見つかりませんでした'),
    'Saved · no model configured, nothing learned': ('已保存 · 未配置模型，没有学习', '保存しました · モデルが未設定のため学習していません'),
    'Saved · learning failed: {error}': ('已保存 · 学习失败：{error}', '保存しました · 学習に失敗しました：{error}'),
    # ---- Native context menus (2026-10-19) ----
    'Remove Saved Comment': ('删除已保存的评论', '保存したコメントを削除'),
    'Add to Left Tags': ('加到左侧标签', '左のタグに追加'),
    'Deny': ('拒绝', '拒否'),
    'No': ('否', 'いいえ'),
    'Remove from Left Tags': ('从左侧标签移除', '左のタグから外す'),
    'Learned output preferences (from your edits; edit or delete freely)': (
        '成品修改偏好（从你的修改中学到，可直接修改或删除）',
        '成果物の編集から学んだ好み（自由に編集・削除できます）'),
    # 2026-10-26: the editor saves into the original file, in its own encoding
    'Save as UTF-8': ('改用 UTF-8 保存', 'UTF-8 で保存'),
    'Not saved': ('没有保存', '保存されませんでした'),
    '“{name}” is saved as {encoding}, which cannot hold some of the new characters ({chars}). Save it as UTF-8 instead?': (
        '“{name}”是 {encoding} 编码，新加的一些字符（{chars}）存不进这种编码。改用 UTF-8 保存吗？',
        '「{name}」は {encoding} で保存されていて、新しい文字の一部（{chars}）を保存できません。代わりに UTF-8 で保存しますか？'),
    '“{name}” is read-only, so it was not saved.': (
        '“{name}”是只读文件，没有保存。',
        '「{name}」は読み取り専用のため、保存されませんでした。'),
    '“{name}” could not be saved: {reason}': (
        '“{name}”没能保存：{reason}',
        '「{name}」を保存できませんでした：{reason}'),
}


try:
    from translations_audit_20261022 import AUDIT_TRANSLATIONS, AUDIT_EXTRA_SOURCE_STRINGS
except ImportError:  # run from another directory
    sys.path.insert(0, HERE)
    from translations_audit_20261022 import AUDIT_TRANSLATIONS, AUDIT_EXTRA_SOURCE_STRINGS
for _source, _pair in AUDIT_TRANSLATIONS.items():
    TRANSLATIONS.setdefault(_source, _pair)
EXTRA_SOURCE_STRINGS = list(EXTRA_SOURCE_STRINGS) + [s for s in AUDIT_EXTRA_SOURCE_STRINGS if s not in EXTRA_SOURCE_STRINGS]


def _feature_flag_spec_strings(tree):
    """Labels AND tooltips of ICLOUD_FEATURE_FLAG_SPECS, read straight from the
    table (Settings shows both through _tr(variable)). A hand-kept copy here once
    had the labels only, so every tooltip stayed English."""
    values = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, 'id', '') == 'ICLOUD_FEATURE_FLAG_SPECS' for t in node.targets):
            for row in ast.literal_eval(node.value):
                values.update(str(text) for text in row[3:5] if str(text).strip())
    return values


def extract_source_strings():
    tree = ast.parse(open(SOURCE, encoding='utf-8').read())
    values = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == '_tr' and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)):
            values.add(node.args[0].value)
    values.update(EXTRA_SOURCE_STRINGS)
    values.update(_feature_flag_spec_strings(tree))
    return sorted(values)


def emit_ts(path, language, index):
    strings = extract_source_strings()
    out = ['<?xml version="1.0" encoding="utf-8"?>', '<!DOCTYPE TS>',
           '<TS version="2.1" language="%s" sourcelanguage="en_US">' % language,
           '<context>', '    <name>%s</name>' % CONTEXT]
    missing = []
    for source in strings:
        pair = TRANSLATIONS.get(source)
        translation = pair[index] if pair else ''
        out.append('    <message>')
        out.append('        <source>%s</source>' % escape(source))
        if translation:
            out.append('        <translation>%s</translation>' % escape(translation))
        else:
            out.append('        <translation type="unfinished"></translation>')
            missing.append(source)
        out.append('    </message>')
    out.extend(['</context>', '</TS>', ''])
    open(path, 'w', encoding='utf-8').write('\n'.join(out))
    return len(strings), missing


def main():
    total, missing_zh = emit_ts(os.path.join(HERE, 'broccoli_zh_CN.ts'), 'zh_CN', 0)
    _, missing_ja = emit_ts(os.path.join(HERE, 'broccoli_ja_JP.ts'), 'ja_JP', 1)
    stale = sorted(set(TRANSLATIONS) - set(extract_source_strings()))
    print('source strings: %d' % total)
    print('missing zh: %d  missing ja: %d' % (len(missing_zh), len(missing_ja)))
    for item in missing_zh[:20]:
        print('  MISSING:', repr(item))
    if stale:
        print('stale table entries (no longer in source): %d' % len(stale))
        for item in stale[:20]:
            print('  STALE:', repr(item))
    return 1 if missing_zh or missing_ja else 0


if __name__ == '__main__':
    sys.exit(main())
