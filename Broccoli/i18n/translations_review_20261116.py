# -*- coding: utf-8 -*-
"""Review of 2026-11-16 (Ryan: "翻译有很多问题，你得理解了功能的含义再去翻译，不是字对字的翻译";
"transfer 这个按钮的作用是切换视图啊"; "moveto 就没翻译"). Every entry of the tables was read against
what the string does in the app; the corrected ones are here. gen_ts.py loads this file LAST and
lets it REPLACE the older entries (the other tables only fill gaps). New corrections go here.
Decided terms: ♻️ Transfer = 切换视图 / 表示切替; 🎛️ Move to = 换设备 / 実行先; Agent = 智能体 / エージェント
(小 Agent / 主 Agent stay); quick command = 快捷命令 (快捷指令 is Apple's Shortcuts); Discover (MCP) = 检测 / 検出;
Generated outputs = 成品 / 成果物. Also the strings of the same day's features (🔻 Save's file kinds,
new conversations following the device picked last)."""

REVIEW_TRANSLATIONS = {'Web': ('网页', 'Web'),
 'Crash-safe conversation saves': ('崩溃时也安全的对话保存', 'クラッシュに強い会話保存'),
 'Collision-proof conversation IDs': ('不会重复的对话 ID', '衝突しない会話 ID'),
 'Storage engine: new conversations get unique IDs instead of second-precision timestamps that could collide. Leave ON. (M1a · BROCCOLI_M1A_UUID_IDS)': ('存储引擎：新对话使用唯一编号，而不是可能重复的秒级时间戳。请保持开启。（M1a '
                                                                                                                                                         '· '
                                                                                                                                                         'BROCCOLI_M1A_UUID_IDS）',
                                                                                                                                                         'ストレージエンジン：新しい会話には、重複しうる秒単位のタイムスタンプではなく一意の '
                                                                                                                                                         'ID '
                                                                                                                                                         'を付けます。オンのままにしてください。（M1a '
                                                                                                                                                         '· '
                                                                                                                                                         'BROCCOLI_M1A_UUID_IDS）'),
 'Single task-completion path': ('统一的任务完成通道', 'タスク完了の経路を一本化'),
 'Adds “🎛️ Move to” to the Send menu: a brand-new conversation starts and runs on the device you pick. (M4a · BROCCOLI_M4A_MOVE_SEND)': ('在发送菜单里加入「🎛️ '
                                                                                                                                         '换设备」：新对话会在你选的设备上开始并运行。（M4a '
                                                                                                                                         '· '
                                                                                                                                         'BROCCOLI_M4A_MOVE_SEND）',
                                                                                                                                         '送信メニューに「🎛️ '
                                                                                                                                         '実行先」を追加します：新しい会話は選んだデバイスで始まり、実行されます。（M4a '
                                                                                                                                         '· '
                                                                                                                                         'BROCCOLI_M4A_MOVE_SEND）'),
 'pending approval': ('待处理的批准', '承認待ち'),
 'Default Profile will be used': ('将使用默认配置', 'デフォルトプロファイルを使います'),
 'Default Profile is running on the target device.': ('目标设备正在用默认配置运行。', '送信先デバイスはデフォルトプロファイルで実行しています。'),
 'missing': ('未找到', '見つかりません'),
 'Web search': ('网页搜索', 'Web 検索'),
 'Run a web search step': ('运行网页搜索步骤', 'Web 検索ステップを実行'),
 'No web search was performed in this step: the model set for Web search answered without searching.': ('这一步没有进行网页搜索：为网页搜索设置的模型没有搜索，直接作答了。',
                                                                                                        'このステップでは Web 検索は行われませんでした：Web '
                                                                                                        '検索に設定されたモデルが検索せずに回答しました。'),
 'Cleaner prompt': ('清理提示词', '整理プロンプト'),
 'Merge prompt': ('合并提示词', '統合プロンプト'),
 'It asks for administrator rights (sudo and the like): Broccoli never runs that without you.': ('它要用管理员权限（sudo 之类）：没有你的同意，Broccoli 绝不运行这种命令。',
                                                                                                 '管理者権限（sudo など）を使おうとしています。Broccoli はあなたの確認なしにこれを実行しません。'),
 'You are using the computer: Computer Use waits until you stop.': ('你正在使用电脑：Computer Use 会等你停下来再开始。', 'コンピュータを使用中です：操作が止まるまで Computer Use は待機します。'),
 'Discover': ('检测', '検出'),
 'Discovery': ('检测结果', '検出結果'),
 'Optional. Leave empty, then click Discover.': ('可选。留空后点击“检测”。', '任意。空のままにして「検出」をクリックしてください。'),
 'Discovery failed:\nEndpoint URL is empty.': ('检测失败：\n端点 URL 为空。', '検出失敗:\nエンドポイント URL が空です。'),
 'Discovery failed:\nCommand is empty.': ('检测失败：\n命令为空。', '検出失敗:\nコマンドが空です。'),
 'Discovery failed:\n{error}': ('检测失败：\n{error}', '検出失敗:\n{error}'),
 'Click Discover to read tools, resources, and prompts from this MCP endpoint.': ('点击“检测”读取此 MCP 端点的工具、资源和提示词。',
                                                                                  '「検出」をクリックすると、この MCP エンドポイントのツール・リソース・プロンプトを読み込みます。'),
 'MCP {name}: discovering tools': ('MCP {name}：正在检测工具', 'MCP {name}: ツールを検出中'),
 'Optional working directory': ('可选工作目录', '作業ディレクトリ（任意）'),
 'Optional environment variables, one per line:\nKEY=value\nGITHUB_PERSONAL_ACCESS_TOKEN=...': ('可选环境变量，每行一个：\nKEY=value\nGITHUB_PERSONAL_ACCESS_TOKEN=...',
                                                                                                '環境変数（任意、1 行に 1 つ）:\n'
                                                                                                'KEY=value\n'
                                                                                                'GITHUB_PERSONAL_ACCESS_TOKEN=...'),
 'Key': ('密钥', 'キー'),
 'Turn it on and sign in under Settings › General › Usage providers.': ('到 设置 › 通用 ›「用量供应商」里打开它并登录。', '設定 › 一般 ›「使用量プロバイダ」でオンにしてサインインしてください。'),
 'Ask the Agent': ('问智能体', 'エージェントに質問'),
 'Natural Name': ('自然语言名', '自然言語名'),
 'User': ('用户', 'ユーザー'),
 '{updated} · From {source} · Last ran on {executor} · {status} · Default Profile fallback': ('{updated} · 来自 {source} · 最后运行于 {executor} · {status} · '
                                                                                              '已回退到默认配置',
                                                                                              '{updated} · 送信元 {source} · 最終実行 {executor} · {status} · '
                                                                                              'デフォルトプロファイルにフォールバック'),
 'Checking the result against the task contract (round {n})': ('正在按任务的验收标准核对结果（第 {n} 轮）', 'タスクの達成条件に照らして結果を確認しています（第 {n} ラウンド）'),
 '⏸ **Waiting for your approval** (reply to continue)': ('⏸ **等待你的批准**（回复以继续）', '⏸ **承認を待っています**（返信すると続行します）'),
 'The agent will control the real local desktop through CuaDriver.': ('智能体将通过 CuaDriver 控制本机的真实桌面。', 'エージェントは CuaDriver を通じてこの Mac の実際のデスクトップを操作します。'),
 'Agent cursor: Broccoli shows a separate labelled virtual cursor; it does not move your physical mouse.': ('智能体光标：Broccoli 会显示一个带标签的独立虚拟光标，不会移动你的实体鼠标。',
                                                                                                            'エージェントカーソル：Broccoli '
                                                                                                            'はラベル付きの別の仮想カーソルを表示し、実際のマウスは動かしません。'),
 '🥦 Start Broccoli!': ('🥦 打开 Broccoli！', '🥦 Broccoli を開く！'),
 '🪟 Show on all Spaces': ('🪟 在所有空间显示', '🪟 すべての操作スペースに表示'),
 '[Agent command stopped]': ('[智能体命令已停止]', '[エージェントのコマンドを停止しました]'),
 '[Agent command timed out]': ('[智能体命令超时]', '[エージェントのコマンドがタイムアウトしました]'),
 'Agent Command': ('智能体命令', 'エージェントコマンド'),
 'Append to current chat': ('追加到当前对话', '現在の会話に追加'),
 'New chat with this': ('用它开新对话', 'これで新しい会話'),
 'Ask Web': ('问网页', 'Web に質問'),
 'Ask Localhost': ('问本地服务', 'Localhost に質問'),
 'Add note to running answer': ('给正在生成的回答追加指示', '生成中の回答に追加指示'),
 'Add note': ('追加指示', '追加指示'),
 'Freeze the countdown so you can edit or reorder steps; Resume or Run now continues': ('冻结倒计时，让你可以从容编辑或调整步骤顺序；按「继续」或「立即执行」恢复',
                                                                                        'カウントダウンを凍結してステップの編集や並べ替えをゆっくり行えます。「再開」または「今すぐ実行」で続行'),
 '📌 Board · %d facts · %d disputed · %d proposed': ('📌 事实板 · %d 条事实 · %d 条有争议 · %d 条提议', '📌 ボード · 事実 %d 件 · 異論 %d 件 · 提案 %d 件'),
 'held at {n}s': ('暂停于 {n} 秒', '{n} 秒で一時停止'),
 'Prompt this web page...': ('向这个网页提问…', 'このウェブページに質問…'),
 'Back': ('返回', '戻る'),
 'The question the Agent gets every time': ('每次交给智能体的问题', '毎回エージェントに送る質問'),
 'Unfiled': ('未分类', '未分類'),
 'On a Mac with Broccoli: type your question, then choose 🎛️ Move to › {device}. The answer comes back into the same conversation.': ('在装了 Broccoli 的 Mac '
                                                                                                                                      '上：输入问题，然后选 🎛️ 换设备 › '
                                                                                                                                      '{device}。回答会回到同一个对话里。',
                                                                                                                                      'Broccoli のある Mac '
                                                                                                                                      'では：質問を入力し、🎛️ 実行先 › '
                                                                                                                                      '{device} '
                                                                                                                                      'を選びます。回答は同じ会話に戻ってきます。'),
 'This Mac': ('这台 Mac', 'この Mac'),
 'Modify': ('修改', '編集'),
 'The question could not be sent. Check the Agent settings.': ('问题没能发出去。请检查智能体的设置。', '質問を送信できませんでした。エージェントの設定を確認してください。'),
 '“{name}” exists again, so it was not put back.': ('「{name}」已经又存在了，所以没有放回去。', '「{name}」がまた存在するため、戻しませんでした。'),
 'outside Broccoli': ('Broccoli 以外的程序', 'Broccoli 以外'),
 'Changed at {time} by {who}': ('{time} 修改，修改者：{who}', '{time} に変更：{who}'),
 '“{a}” gave back {files}': ('「{a}」让出了 {files}', '「{a}」が {files} を解放'),
 'History name:': ('对话名称：', '会話名:'),
 'Rename history': ('重命名对话', '会話の名前を変更'),
 'Read: {title} ({chars} characters)': ('已读取：{title}（{chars} 字）', '読み込み済み：{title}（{chars} 文字）'),
 'Generated outputs': ('生成的成品', '生成された成果物'),
 'No generated output yet': ('还没有成品', 'まだ成果物はありません'),
 'No generated output for this conversation yet.': ('此对话还没有成品。', 'この会話にはまだ成果物がありません。'),
 '0 outputs': ('0 个成品', '成果物 0 件'),
 '{n} outputs · {kind}': ('{n} 个成品 · {kind}', '成果物 {n} 件 · {kind}'),
 'Start new Agent conversation first': ('先新建智能体对话', '先に新しいエージェント会話を開始'),
 'From': ('来源', '読み取り元'),
 'To': ('目标', '書き込み先'),
 '🎛️ Move to': ('🎛️ 换设备', '🎛️ 実行先'),
 'Choose the device that will own and run this new conversation.': ('选择这个新对话放在哪台设备上、由哪台设备运行。', 'この新しい会話を置いて実行するデバイスを選んでください。'),
 'Queue depth: {count}': ('排队任务：{count}', '待機中のタスク: {count}'),
 'This device has no mapping for the current logical agent; its Default Profile will run.': ('这台设备没有给当前智能体指定对应的配置，将用它的默认配置运行。',
                                                                                             'このデバイスには現在のエージェントに対応するプロファイルがないため、デフォルトプロファイルで実行されます。'),
 'Profile: {name}': ('配置：{name}', 'プロファイル: {name}'),
 '♻️ Transfer': ('♻️ 切换视图', '♻️ 表示切替'),
 '➕ Add note': ('➕ 追加指示', '➕ 追加指示'),
 '🧾 Queue': ('🧾 排队', '🧾 予約'),
 'Saved Comments': ('常用评论', '保存済みコメント'),
 'Remove this saved comment from the menu': ('从菜单中移除这条常用评论', 'この保存済みコメントをメニューから削除'),
 'Remove Saved Comment': ('删除常用评论', '保存済みコメントを削除'),
 'Mark "{label}"': ('标记为「{label}」', '「{label}」でマーク'),
 'Add selection to Generated outputs': ('把所选内容加入成品', '選択部分を成果物に追加'),
 'Choose what to share from the current Agent conversation.': ('选择要从当前智能体对话分享的内容。', '現在のエージェント会話から共有する内容を選んでください。'),
 'Full Markdown': ('完整 Markdown', 'Markdown 全文'),
 'Generated via the active API profile. Edit before sending.': ('由当前 API 配置生成。发送前可先编辑。', '現在の API プロファイルで生成されました。送信前に編集できます。'),
 'Full Markdown - {title}': ('完整 Markdown - {title}', 'Markdown 全文 - {title}'),
 'No active API profile is configured.': ('还没有设置当前使用的 API 配置。', '使用する API プロファイルが設定されていません。'),
 'Save current page to API history': ('把当前页面存入智能体历史', '現在のページをエージェント履歴に保存'),
 'full page scan ({n} windows)': ('整页扫描（分 {n} 屏）', 'ページ全体をスキャン（{n} 画面分）'),
 'Share Full Markdown...': ('分享完整 Markdown…', 'Markdown 全文を共有…'),
 'New API history': ('存为新的智能体对话', '新しいエージェント会話として保存'),
 'Update linked API history': ('更新已关联的智能体对话', 'リンク済みのエージェント会話を更新'),
 'Append to current API history': ('追加到当前智能体对话', '現在のエージェント会話に追記'),
 'Choose API history...': ('选择智能体对话…', 'エージェント会話を選択…'),
 'Agent run failed — {title}': ('智能体运行失败 — {title}', 'エージェントの実行に失敗 — {title}'),
 'Save output as': ('成品另存为', '成果物を別名で保存'),
 'Broccoli Note': ('Broccoli 备忘录', 'Broccoli メモ'),
 'Edit Quick Command…': ('编辑快捷命令…', 'クイックコマンドを編集…'),
 'New Quick Command…': ('新建快捷命令…', '新しいクイックコマンド…'),
 'Could not run the quick command “{name}”.': ('快捷命令“{name}”没能运行。', 'クイックコマンド「{name}」を実行できませんでした。'),
 'Quick commands': ('快捷命令', 'クイックコマンド'),
 'Save Last Question as Quick Command…': ('把最后一个问题存为快捷命令…', '最後の質問をクイックコマンドに保存…'),
 'Agent task': ('智能体任务', 'エージェントタスク'),
 'Choose a non-default model profile for Compare.': ('请为对比选择一个非默认的模型配置。', '比較には既定以外のモデルプロファイルを選んでください。'),
 'Choose a non-default model profile for Verify.': ('请为核验选择一个非默认的模型配置。', '検証には既定以外のモデルプロファイルを選んでください。'),
 'Broccoli is not allowed to use Reminders, so finished agents get no reminder. Allow it in System Settings → Privacy & Security → Automation, or turn the reminder off in Settings → Completion alerts.': ('Broccoli '
                                                                                                                                                                                                            '没有权限使用“提醒事项”，所以智能体完成时不会加提醒。请在 '
                                                                                                                                                                                                            '系统设置 '
                                                                                                                                                                                                            '→ '
                                                                                                                                                                                                            '隐私与安全性 '
                                                                                                                                                                                                            '→ '
                                                                                                                                                                                                            '自动化 '
                                                                                                                                                                                                            '里允许，或者在 '
                                                                                                                                                                                                            '设置 '
                                                                                                                                                                                                            '→ '
                                                                                                                                                                                                            '完成提醒 '
                                                                                                                                                                                                            '里关掉这个提醒。',
                                                                                                                                                                                                            'Broccoli '
                                                                                                                                                                                                            'にリマインダーを使う許可がないため、エージェントが終わってもリマインダーは追加されません。システム設定 '
                                                                                                                                                                                                            '→ '
                                                                                                                                                                                                            'プライバシーとセキュリティ '
                                                                                                                                                                                                            '→ '
                                                                                                                                                                                                            'オートメーション '
                                                                                                                                                                                                            'で許可するか、設定 '
                                                                                                                                                                                                            '→ '
                                                                                                                                                                                                            '完了通知 '
                                                                                                                                                                                                            'でこのリマインダーをオフにしてください。'),
 'User added a note for the next checkpoint.': ('用户为下一个检查点追加了指示。', 'ユーザーが次のチェックポイント向けに指示を追加しました。'),
 'User note': ('用户追加的指示', 'ユーザーメモ'),
 'No running Agent answer to add a note to.': ('没有正在生成的智能体回答可以追加指示。', '追加指示できる実行中のエージェント回答がありません。'),
 'Open or start an Agent conversation before adding a queued prompt.': ('请先打开或开始一个智能体对话，再添加排队提示词。', 'キューにプロンプトを追加する前に、エージェントの会話を開くか開始してください。'),
 'Queue is available while this Agent conversation is running.': ('排队功能仅在该智能体对话运行时可用。', 'キューはこのエージェント会話の実行中に利用できます。'),
 'Agent queue': ('智能体队列', 'エージェントキュー'),
 'Set an Agent API profile in Settings before running queued prompts.': ('运行排队提示词前，请先在设置中指定智能体的 API 配置。', 'キューのプロンプトを実行する前に、設定でエージェントの API プロファイルを指定してください。'),
 'Launch managed Chrome': ('启动专用 Chrome', '専用の Chrome を起動'),
 'Current Agent answer is still running. Stop it before auto-sending another screenshot.': ('当前智能体回答仍在生成。请先停止，再自动发送新的截图。',
                                                                                            '現在のエージェントの回答が実行中です。停止してから次のスクリーンショットを自動送信してください。'),
 'No window found for this task': ('找不到这个任务的窗口', 'このタスクのウィンドウが見つかりません'),
 'Migrating conversation; waiting for the target to verify every asset.': ('正在迁移对话；等待目标设备校验全部资源。', '会話を移動中。移動先のデバイスがすべてのファイルを確認するのを待っています。'),
 '🎛️ Move to failed': ('🎛️ 换设备失败', '🎛️ 実行先の変更に失敗'),
 'This conversation lives on {device}, so changes here are not saved. Use 🎛️ Move to → This Mac to edit it here, or Copy to this Mac for your own copy.': ('这段对话在 '
                                                                                                                                                           '{device} '
                                                                                                                                                           '上，在这里的修改不会保存。要在这里编辑，请用 '
                                                                                                                                                           '🎛️ '
                                                                                                                                                           '换设备 '
                                                                                                                                                           '→ '
                                                                                                                                                           '这台 '
                                                                                                                                                           'Mac；想要自己的副本，请用“复制到这台 '
                                                                                                                                                           'Mac”。',
                                                                                                                                                           'この会話は '
                                                                                                                                                           '{device} '
                                                                                                                                                           'にあるため、ここでの変更は保存されません。ここで編集するには '
                                                                                                                                                           '🎛️ '
                                                                                                                                                           '実行先 '
                                                                                                                                                           '→ '
                                                                                                                                                           'この '
                                                                                                                                                           'Mac、自分用のコピーには「この '
                                                                                                                                                           'Mac '
                                                                                                                                                           'にコピー」を使ってください。'),
 'This conversation lives on {device}. Turn on iCloud remote tasks in Settings to send it there, or use 🎛️ Move to → Copy to this Mac to continue here.': ('这段对话在 '
                                                                                                                                                           '{device} '
                                                                                                                                                           '上。请在设置里打开 '
                                                                                                                                                           'iCloud '
                                                                                                                                                           '远程任务以发送过去，或用 '
                                                                                                                                                           '🎛️ '
                                                                                                                                                           '换设备 '
                                                                                                                                                           '→ '
                                                                                                                                                           '复制到这台 '
                                                                                                                                                           'Mac '
                                                                                                                                                           '在这里继续。',
                                                                                                                                                           'この会話は '
                                                                                                                                                           '{device} '
                                                                                                                                                           'にあります。設定で '
                                                                                                                                                           'iCloud '
                                                                                                                                                           'リモートタスクをオンにして送るか、🎛️ '
                                                                                                                                                           '実行先 '
                                                                                                                                                           '→ '
                                                                                                                                                           'この '
                                                                                                                                                           'Mac '
                                                                                                                                                           'にコピー '
                                                                                                                                                           'でここで続けてください。'),
 'Broccoli is not allowed to use Reminders, so the iPhone gets no reminder when an answer is ready. The Notes still arrive. Allow it in System Settings → Privacy & Security → Automation, then restart Broccoli, or turn the reminder off in Settings.': ('Broccoli '
                                                                                                                                                                                                                                                           '没有使用「提醒事项」的权限，所以回答好了 '
                                                                                                                                                                                                                                                           'iPhone '
                                                                                                                                                                                                                                                           '收不到提醒，但备忘录照常会写。请在「系统设置 '
                                                                                                                                                                                                                                                           '→ '
                                                                                                                                                                                                                                                           '隐私与安全性 '
                                                                                                                                                                                                                                                           '→ '
                                                                                                                                                                                                                                                           '自动化」里允许，然后重启 '
                                                                                                                                                                                                                                                           'Broccoli；或者在设置里关掉这个提醒。',
                                                                                                                                                                                                                                                           'Broccoli '
                                                                                                                                                                                                                                                           'にリマインダーの使用が許可されていないため、回答ができても '
                                                                                                                                                                                                                                                           'iPhone '
                                                                                                                                                                                                                                                           'にリマインダーが届きません（メモは届きます）。「システム設定 '
                                                                                                                                                                                                                                                           '→ '
                                                                                                                                                                                                                                                           'プライバシーとセキュリティ '
                                                                                                                                                                                                                                                           '→ '
                                                                                                                                                                                                                                                           'オートメーション」で許可してから '
                                                                                                                                                                                                                                                           'Broccoli '
                                                                                                                                                                                                                                                           'を再起動するか、設定でこのリマインダーをオフにしてください。'),
 'Slash task empty': ('斜杠命令后面没有内容', 'スラッシュコマンドの内容が空です'),
 'No active Web, Localhost, or Terminal target is registered as @{alias}.': ('没有名为 @{alias} 的活动网页、本地服务或终端目标。',
                                                                             '@{alias} として登録された有効な Web・Localhost・ターミナルのターゲットはありません。'),
 'Failed to update start on login: {exc}': ('更新“登录时启动”失败：{exc}', '「ログイン時に起動」の更新に失敗しました: {exc}'),
 '{count} characters written': ('已写 {count} 字', '{count} 文字作成済み'),
 '⏳ The agent stopped and is waiting for you · click here to see it': ('⏳ 智能体停下来等你处理 · 点这里查看', '⏳ エージェントが止まってあなたを待っています · クリックで表示'),
 '⚠️ Not finished · the usage ran out · click here to see it': ('⚠️ 没有走完 · 用量用完了 · 点这里查看', '⚠️ 完了しませんでした · 使用量切れ · クリックで表示'),
 'The active profile': ('当前启用的配置', '現在のプロファイル'),
 'Not probed yet (probes after Save)': ('尚未探测（保存后开始探测）', '未確認（保存後に確認します）'),
 'Probed: supported ({levels})': ('探测结果：支持（{levels}）', '確認結果: 対応（{levels}）'),
 'Probed: not supported': ('探测结果：不支持', '確認結果: 非対応'),
 'Probe failed; will retry': ('探测失败；将重试', '確認に失敗。再試行します'),
 'Manual: always inject · ': ('手动：始终带思考强度 · ', '手動: 常に推論の強さを送る · '),
 'Manual: never inject · ': ('手动：从不带思考强度 · ', '手動: 推論の強さを送らない · '),
 'Reasoning effort for planning only; the profile itself is unchanged.': ('只用于规划的思考强度，配置本身不变。', '計画だけに使う推論の強さです。プロファイル自体は変わりません。'),
 "Broccoli closes and opens again as {name}, with {name}'s own settings, memory and conversations.": ('Broccoli 会关闭，再以 {name} 的身份重新打开，用 {name} 自己的设置、记忆和对话。',
                                                                                                      'Broccoli を閉じて {name} として開き直します。{name} '
                                                                                                      '自身の設定・メモリ・会話を使います。'),
 'Same-position screenshot shortcut must be different from the main window shortcut.': ('同位置截图快捷键必须与主窗口快捷键不同。',
                                                                                        '同位置スクリーンショットのショートカットは、メインウィンドウのショートカットと別にしてください。'),
 'New': ('新建', '新規'),
 'Sources': ('来源', '情報源'),
 'Looking for sources on this Mac…': ('正在这台 Mac 上查找来源…', 'この Mac で情報源を探しています…'),
 'Reports are written with the default model, from the questions and answers of that day. They show under the welcome text on the Agent page.': ('报告用默认模型、根据当天的提问和回答来写，显示在智能体页欢迎文字的下面。',
                                                                                                                                                 'レポートはデフォルトのモデルで、その日の質問と回答から作成され、エージェントページの歓迎メッセージの下に表示されます。'),
 'Could not look for sources. Reports use the Agent conversations.': ('没能查找来源，报告只用智能体对话。', '情報源を探せませんでした。レポートはエージェントの会話だけを使います。'),
 'Found on this Mac. Reports read the ticked ones.': ('在这台 Mac 上找到的来源，报告会读勾上的。', 'この Mac で見つかった情報源です。チェックしたものをレポートに使います。'),
 'Their names become other names of “{name}”, and their sources and notes move into it.': ('它们的名字会变成“{name}”的其他叫法，来源和备注也一起并进去。',
                                                                                           'それぞれの名前は「{name}」の別名になり、情報源とメモも移ります。'),
 'No Web tab URLs were found.': ('没有找到网页标签页的网址。', 'Web タブの URL が見つかりませんでした。'),
 'Sync failed: no target selected.': ('同步失败：未选择目标。', '同期失敗: 書き込み先が選択されていません。'),
 '; wrote {ok}/{total} targets': ('；已写入 {ok}/{total} 个目标', '、書き込み先 {ok}/{total} 件に書き込み'),
 '; {count} busy target(s) will be retried': ('；{count} 个忙碌的目标将重试', '、処理中の書き込み先 {count} 件は再試行します'),
 'The notifications for “answer ready”, “run failed” and “waiting for you” use the system notification sound. Focus modes keep them silent.': ('“回答已完成”“运行失败”“等你处理”这三种通知使用系统的通知声音；专注模式下不响。',
                                                                                                                                               '「回答ができました」「失敗しました」「あなたを待っています」の通知でシステムの通知音を鳴らします。集中モード中は鳴りません。'),
 'Add a reminder in Reminders when an agent finishes': ('智能体完成时在“提醒事项”里加一条', 'エージェントが終わったらリマインダーに追加'),
 'It goes into the list “Broccoli” in iCloud and rings a minute later, so your iPhone, iPad and Watch get it too. It does not ring if you have already looked at the conversation on the Mac, and it is ticked off by itself a day later. Questions sent from the iPhone Shortcut have their own reminder and get no second one.': ('加到 '
                                                                                                                                                                                                                                                                                                                                    'iCloud '
                                                                                                                                                                                                                                                                                                                                    '里的“Broccoli”列表，1 '
                                                                                                                                                                                                                                                                                                                                    '分钟后响，iPhone、iPad、手表都会收到。在 '
                                                                                                                                                                                                                                                                                                                                    'Mac '
                                                                                                                                                                                                                                                                                                                                    '上已经看过这个对话的就不响；一天后自动打勾。从 '
                                                                                                                                                                                                                                                                                                                                    'iPhone '
                                                                                                                                                                                                                                                                                                                                    '捷径发来的问题另有提醒，不会重复。',
                                                                                                                                                                                                                                                                                                                                    'iCloud '
                                                                                                                                                                                                                                                                                                                                    'のリスト「Broccoli」に追加され、1 '
                                                                                                                                                                                                                                                                                                                                    '分後に通知されるので、iPhone・iPad・Watch '
                                                                                                                                                                                                                                                                                                                                    'にも届きます。Mac '
                                                                                                                                                                                                                                                                                                                                    'でその会話をすでに見ていれば通知されず、1 '
                                                                                                                                                                                                                                                                                                                                    '日後に自動で完了になります。iPhone '
                                                                                                                                                                                                                                                                                                                                    'のショートカットから送った質問には別のリマインダーがあるので、重複しません。'),
 'A script runs at once, without the AI. A question goes to the Agent as a new conversation; its answer comes out of the collapsed button. New commands go to layer 2 of its grid: rest the pointer on the collapsed button, then scroll in the grid or click its page dots.': ('脚本直接运行，不经过 '
                                                                                                                                                                                                                                                                                'AI。问题会作为一个新对话交给智能体，回答从最小化圆按钮里出来。新指令放在九宫格第 '
                                                                                                                                                                                                                                                                                '2 '
                                                                                                                                                                                                                                                                                '层：鼠标停在最小化圆按钮上，再在九宫格里滚动或点翻页的小点。',
                                                                                                                                                                                                                                                                                'スクリプトは '
                                                                                                                                                                                                                                                                                'AI '
                                                                                                                                                                                                                                                                                'を通さずすぐ実行されます。質問は新しい会話としてエージェントに送られ、答えは最小化ボタンから出てきます。新しいコマンドはグリッドの第 '
                                                                                                                                                                                                                                                                                '2 '
                                                                                                                                                                                                                                                                                '層に入ります：最小化ボタンにポインタを置き、グリッド内でスクロールするかページの点をクリックしてください。'),
 'When Claude Code, Codex or another AI tool on this Mac (in VS Code, a terminal or Broccoli) or Broccoli’s own agent finishes a turn, a column of dots appears beside the pointer: grey = still running, green = done, orange = it waits for you, red = it ended on an error. Point at it to see the tasks; click one to go there. The sound is the one under Completion alerts. The built-in agentsview reads the sessions; nothing leaves this Mac.': ('这台 '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'Mac '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '上的 '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'Claude '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'Code、Codex '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '等 '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'AI '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '工具（在 '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'VS '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'Code、终端或 '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'Broccoli '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '里）或 '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'Broccoli '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '自己的智能体做完一轮时，鼠标旁会出现一列小圆点：灰色 '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '= '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '还在进行，绿色 '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '= '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '做完了，橙色 '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '= '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '在等你，红色 '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '= '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '出错结束。鼠标移上去看是哪些任务，点一个就跳过去。声音用「完成提醒」里的设置。会话由内置的 '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'agentsview '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '读取，数据不离开这台 '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'Mac。',
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'この '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'Mac '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'の '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'Claude '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'Code・Codex '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'などの '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'AI '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'ツール（VS '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'Code、ターミナル、Broccoli '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '内）や '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'Broccoli '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '自身のエージェントが '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '1 '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'ターン終えると、ポインタの横に点が縦に並びます：グレー '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '= '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '実行中、緑 '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '= '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '完了、オレンジ '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '= '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'あなたを待っています、赤 '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          '= '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'エラーで終了。ポインタを乗せるとタスクが見え、クリックでそこへ移動します。音は「完了通知」の設定に従います。セッションは内蔵の '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'agentsview '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'が読み取り、データはこの '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'Mac '
                                                                                                                                                                                                                                                                                                                                                                                                                                                          'から出ません。'),
 'Watched': ('监视', '監視'),
 'Watch': ('监视', '監視する'),
 'Don’t watch': ('不监视', '監視しない'),
 'A provider has the same color here as on the usage bars. Green, grey, orange and red are kept for a task’s state and for a nearly used-up bar.': ('同一家供应商在这里和用量条上是同一个颜色。绿、灰、橙、红留给任务的状态和快用完的用量条。',
                                                                                                                                                    '同じプロバイダはここと使用量バーで同じ色です。緑・グレー・オレンジ・赤はタスクの状態と残りわずかの使用量バー用です。'),
 'Broccoli agent': ('Broccoli 智能体', 'Broccoli エージェント'),
 'Right-drag up could not start: macOS did not let Broccoli listen to the mouse.': ('“右键往上划”没能启用：macOS 不允许 Broccoli 监听鼠标。',
                                                                                    '「右ボタンを押したまま上へ」を開始できませんでした：macOS が Broccoli にマウスの監視を許可しませんでした。'),
 'Checking access to Reminders…': ('正在确认能否使用“提醒事项”…', 'リマインダーを使えるか確認しています…'),
 'Broccoli is not allowed to use Reminders.': ('Broccoli 没有权限使用“提醒事项”。', 'Broccoli にリマインダーを使う許可がありません。'),
 'Reminders is ready.': ('“提醒事项”可以用了。', 'リマインダーを使えます。'),
 'Reminders did not answer just now; Broccoli tries again when an agent finishes.': ('“提醒事项”刚才没有回应；智能体完成时会再试。', 'リマインダーから応答がありませんでした。エージェントが終わったときにもう一度試します。'),
 'There is no daily quota: providers count a 5-hour window and a weekly one. Automatic shows the fuller of the two, marked 5h or wk. A provider without the chosen window shows the one it has. Without a choice above, the first providers CodexBar has turned on are shown.': ('没有“每日”额度：各家算的是 '
                                                                                                                                                                                                                                                                                 '5 '
                                                                                                                                                                                                                                                                                 '小时窗口和每周窗口。“自动”显示两个里用得更多的那个，并标上 '
                                                                                                                                                                                                                                                                                 '5h '
                                                                                                                                                                                                                                                                                 '或“周”。某家没有你选的那种窗口时，显示它有的那个。上面一个都不选时，显示 '
                                                                                                                                                                                                                                                                                 'CodexBar '
                                                                                                                                                                                                                                                                                 '里开着的前几家。',
                                                                                                                                                                                                                                                                                 '「1 '
                                                                                                                                                                                                                                                                                 '日あたり」の上限はありません。各プロバイダは '
                                                                                                                                                                                                                                                                                 '5 '
                                                                                                                                                                                                                                                                                 '時間の枠と毎週の枠で数えます。「自動」は使用率の高いほうを表示し、5h '
                                                                                                                                                                                                                                                                                 'または「週」の印を付けます。選んだ枠がないプロバイダは、持っている枠を表示します。上で何も選ばないときは、CodexBar '
                                                                                                                                                                                                                                                                                 'でオンになっている最初のプロバイダを表示します。'),
 'This color is too close to the red that marks a bar at 80 % or more, so it could not tell you when a provider is nearly used up. Choose another one.': ('这个颜色和“用到 '
                                                                                                                                                          '80% '
                                                                                                                                                          '以上”的红色太像，到时候就看不出哪家快用完了。请换一个颜色。',
                                                                                                                                                          'この色は「80% '
                                                                                                                                                          '以上」を示す赤に近すぎるため、使い切りそうなときに見分けられません。別の色を選んでください。'),
 'Reading with the CodexBar built into Broccoli ({version}). Turn providers on and sign in under Usage providers, the next page.': ('正在用 Broccoli 内置的 '
                                                                                                                                    'CodexBar（{version}）读取。开关供应商、登录，在下一页“用量供应商”里。',
                                                                                                                                    'Broccoli 内蔵の '
                                                                                                                                    'CodexBar（{version}）で読み取っています。プロバイダのオン／オフとサインインは次のページ「使用量プロバイダ」で行います。'),
 "macOS asks once whether CodexBar may read the browser's saved sign-ins: click Always Allow. For Safari, Broccoli needs Full Disk Access (System Settings › Privacy & Security).": ('macOS '
                                                                                                                                                                                     '会问一次是否允许 '
                                                                                                                                                                                     'CodexBar '
                                                                                                                                                                                     '读取浏览器保存的登录，点“始终允许”。Safari '
                                                                                                                                                                                     '的话，要给 '
                                                                                                                                                                                     'Broccoli“完全磁盘访问权限”（系统设置 '
                                                                                                                                                                                     '› '
                                                                                                                                                                                     '隐私与安全性）。',
                                                                                                                                                                                     'CodexBar '
                                                                                                                                                                                     'がブラウザに保存されたサインイン情報を読むことを許可するか、macOS '
                                                                                                                                                                                     'が一度だけ確認します。「常に許可」をクリックしてください。Safari '
                                                                                                                                                                                     'の場合は、Broccoli '
                                                                                                                                                                                     'に「フルディスクアクセス」が必要です（システム設定 '
                                                                                                                                                                                     '› '
                                                                                                                                                                                     'プライバシーとセキュリティ）。'),
 "Importing the sign-in for {name}… If macOS asks whether CodexBar may use the browser's saved data, click Always Allow.": ('正在导入 {name} 的登录… 如果 macOS 问是否允许 '
                                                                                                                            'CodexBar 使用浏览器保存的数据，点“始终允许”。',
                                                                                                                            '{name} のサインインを取り込んでいます… CodexBar '
                                                                                                                            'がブラウザの保存データを使うことを macOS '
                                                                                                                            'が確認してきたら、「常に許可」をクリックしてください。'),
 'For tasks that run while nobody is at the screen. What the review below finds fine runs without asking, after a copy of what it changes: Agent commands, what it hands to Codex / Claude Code, MCP tool calls; editor edits and Computer Use too. Always asked: administrator rights (sudo), erasing a disk, system files, sending anything off this Mac.': ('用于没人看着屏幕时运行的任务。下面的审核认为没问题的，先复制一份它要改动的东西，然后不问你直接运行：智能体的命令、交给 '
                                                                                                                                                                                                                                                                                                                                                               'Codex '
                                                                                                                                                                                                                                                                                                                                                               '/ '
                                                                                                                                                                                                                                                                                                                                                               'Claude '
                                                                                                                                                                                                                                                                                                                                                               'Code '
                                                                                                                                                                                                                                                                                                                                                               '的操作、MCP '
                                                                                                                                                                                                                                                                                                                                                               '工具调用；编辑器改动和电脑操作也一样。一定会问你的：管理员权限（sudo）、抹掉磁盘、改系统文件、往这台 '
                                                                                                                                                                                                                                                                                                                                                               'Mac '
                                                                                                                                                                                                                                                                                                                                                               '外发送任何东西。',
                                                                                                                                                                                                                                                                                                                                                               '画面の前に誰もいない間に動くタスク向けです。下の審査で問題なしとされたものは、変更対象をコピーしてから確認なしで実行します：エージェントのコマンド、Codex '
                                                                                                                                                                                                                                                                                                                                                               '/ '
                                                                                                                                                                                                                                                                                                                                                               'Claude '
                                                                                                                                                                                                                                                                                                                                                               'Code '
                                                                                                                                                                                                                                                                                                                                                               'に任せる操作、MCP '
                                                                                                                                                                                                                                                                                                                                                               'ツール呼び出し、エディタの編集とコンピュータ操作も同様です。必ず確認するもの：管理者権限（sudo）、ディスクの消去、システムファイル、この '
                                                                                                                                                                                                                                                                                                                                                               'Mac '
                                                                                                                                                                                                                                                                                                                                                               'の外への送信。'),
 'Broccoli runs a small proxy on this Mac only. Sign in to a subscription in your browser, and its models can be added as ordinary profiles. The sign-in stays on this Mac. Providers may not allow their subscriptions to be used this way: an account can be limited or closed for it.': ('Broccoli '
                                                                                                                                                                                                                                                                                            '只在这台 '
                                                                                                                                                                                                                                                                                            'Mac '
                                                                                                                                                                                                                                                                                            '上运行一个小代理。在浏览器里登录订阅后，它的模型就能添加为普通的配置。登录信息只留在这台 '
                                                                                                                                                                                                                                                                                            'Mac '
                                                                                                                                                                                                                                                                                            '上。各家服务不一定允许这样使用订阅：账号可能因此被限制或停用。',
                                                                                                                                                                                                                                                                                            'Broccoli '
                                                                                                                                                                                                                                                                                            'はこの '
                                                                                                                                                                                                                                                                                            'Mac '
                                                                                                                                                                                                                                                                                            'の中だけで小さなプロキシを動かします。ブラウザでサブスクリプションにサインインすると、そのモデルを普通のプロファイルとして追加できます。サインイン情報はこの '
                                                                                                                                                                                                                                                                                            'Mac '
                                                                                                                                                                                                                                                                                            'にだけ残ります。この使い方を認めていない事業者もあり、アカウントが制限・停止されることがあります。'),
 'Auto (probe)': ('自动（探测）', '自動（検出）'),
 'After an answer finishes, one short extra request to the same model guesses what you will ask next. It shows in grey in the Agent box: press Return to fill it in, Command+Return to send.': ('回答结束后，向同一个模型多发一次简短请求，猜你下一句会问什么。它以灰字显示在智能体输入框里：按回车填入，按 '
                                                                                                                                                                                                'Command+回车发送。',
                                                                                                                                                                                                '回答が終わると、同じモデルに短いリクエストをもう一度送り、次に聞きそうなことを予測します。エージェントの入力欄にグレーで表示されます。Return '
                                                                                                                                                                                                'キーで入力、Command+Return '
                                                                                                                                                                                                'で送信します。'),
 'Auto-start Codex / Claude Code tabs on launch': ('启动时自动启动 Codex / Claude Code 标签页', '起動時に Codex / Claude Code タブを自動で起動'),
 'Auto-open last Web / Localhost URLs on launch': ('启动时自动打开上次的网页 / 本地服务网址', '起動時に前回の Web / Localhost URL を自動で開く'),
 'Auto click Send after filling Web / Localhost prompts': ('填入网页 / 本地服务提示词后自动点击发送', 'Web / Localhost にプロンプトを入力後、自動で送信をクリック'),
 'Test capability': ('测试是否支持', '機能をテスト'),
 'How many recent steps the browser agent keeps in memory. 0 = unlimited; values 1–5 are raised to 6 (library minimum).': ('浏览器智能体记忆中保留的最近步骤数。0 = 不限；1–5 会抬到 '
                                                                                                                           '6（库的最低值）。',
                                                                                                                           'ブラウザエージェントがメモリに保持する直近ステップ数。0 = '
                                                                                                                           '無制限。1–5 は 6 に引き上げられます（ライブラリの最小値）。'),
 'Full': ('完整', 'フル'),
 'Compact sends the agent a goal-first task brief with tighter background limits; the brief is resent on every step, so smaller means faster. Full keeps the original verbose brief.': ('精简档发送“目标置顶”的任务书并收紧背景材料限额；任务书每一步都会重发，越小越快。完整档保持原来的详细任务书。',
                                                                                                                                                                                        'コンパクトは目標を先頭に置いたタスク指示を送り、背景資料の上限を絞ります。指示は毎ステップ再送されるため、小さいほど高速です。フルは従来の詳細な指示を維持します。'),
 "Default engine for the browser agent's search action. Pick one that is reachable from your network; unreachable engines make search steps hang and fail.": ('浏览器智能体搜索动作的默认引擎。请选择你的网络能访问的引擎；访问不了的引擎会让搜索步骤挂死并失败。',
                                                                                                                                                              'ブラウザエージェントの検索アクションの既定エンジン。ネットワークから到達できるものを選んでください。到達できないエンジンは検索ステップの停止と失敗を招きます。'),
 'Web / Localhost energy mode': ('网页 / 本地服务节能模式', 'Web / Localhost 省エネモード'),
 'Browser userscripts (Web / Localhost)': ('浏览器用户脚本（网页 / 本地服务）', 'ブラウザのユーザースクリプト（Web / Localhost）'),
 'Web URLs': ('网页网址', 'Web の URL'),
 'Localhost URLs': ('本地服务网址', 'Localhost の URL'),
 'Name is what the "+" menu on the Web / Localhost pill bar shows. Changes apply after Save.': ('名称即网页 / 本地服务标签条“+”菜单中显示的内容。保存后生效。',
                                                                                                '名前は Web / Localhost バーの「+」メニューに表示されます。変更は保存後に反映されます。'),
 'Agent plan': ('智能体计划', 'エージェントのプラン'),
 'Step review pause': ('每步执行前停顿', 'ステップ前の待機'),
 'How many conversations the History panel renders (newest first). Nothing is deleted and search always scans every conversation. Far right = All.': ('历史面板显示多少条对话（最新在前）。不会删除任何内容，搜索始终扫描全部对话。拖到最右 '
                                                                                                                                                      '= 全部。',
                                                                                                                                                      '履歴パネルに表示する会話数（新しい順）。削除は行われず、検索は常に全会話を対象にします。右端 '
                                                                                                                                                      '= すべて。'),
 'Window & agent plan': ('窗口与智能体计划', 'ウィンドウとエージェントのプラン'),
 'How the windows behave and start, and how agent plan steps pause and run in parallel.': ('窗口的行为与启动方式，以及智能体计划步骤的暂停与并行。',
                                                                                           'ウィンドウの動作と起動、エージェントのプランのステップの一時停止と並列実行。'),
 'How Broccoli lets you know when an agent finishes.': ('智能体跑完时，Broccoli 怎么提醒你。', 'エージェントが終わったときの知らせ方です。'),
 'Web / Localhost sending, embeddings for fetched content, downloads, PDF attachments and userscripts.': ('网页 / 本地服务的发送、抓取内容的向量化、下载、PDF 附件和用户脚本。',
                                                                                                          'Web / Localhost への送信、取得内容の埋め込み、ダウンロード、PDF '
                                                                                                          '添付、ユーザースクリプト。'),
 'Let the agent drive a separate Chrome to open pages, click and fill in forms.': ('让智能体控制一个独立的 Chrome 打开网页、点击和填写表单。',
                                                                                   'エージェントが専用の Chrome を操作して、ページを開き、クリックし、フォームに入力します。'),
 'Let the agent operate desktop apps through CuaDriver.': ('让智能体通过 CuaDriver 操作桌面应用。', 'エージェントが CuaDriver を通じてデスクトップアプリを操作します。'),
 'Agent saved comments': ('智能体常用评论', 'エージェントの保存済みコメント'),
 'Reusable comments you can add to a running agent task.': ('可以添加到正在运行的智能体任务中的常用评论。', '実行中のエージェントのタスクに追加できる再利用可能なコメント。'),
 'Web & Localhost URLs': ('网页与本地服务网址', 'Web と Localhost の URL'),
 'The pages listed in the "+" menu of the Web / Localhost bar, and their order.': ('网页 / 本地服务栏「+」菜单中列出的页面及其顺序。', 'Web / Localhost バーの「+」メニューに表示されるページとその順序。'),
 "Your own commands for the collapsed button's grid: a script that runs at once, or a question for the Agent.": ('放在最小化圆按钮九宫格里的自定指令：直接运行的脚本，或交给智能体的问题。',
                                                                                                                 '最小化ボタンのグリッドに置く自分のコマンド：すぐ実行するスクリプト、またはエージェントへの質問。'),
 'Auto quality': ('自动评分', '自動評価'),
 'Auto quality comes from per-step reviews (goal met / total). Edit the Notes column to record traits; saved immediately.': ('自动评分来自每步复盘（达成目标数 / '
                                                                                                                             '总数）。可在备注列记录模型特点，编辑后立即保存。',
                                                                                                                             '自動評価はステップごとのレビュー（目標達成 / '
                                                                                                                             '総数）から算出されます。「メモ」列で特徴を記録でき、編集は即保存されます。'),
 'How well each model does on agent steps, used when choosing models.': ('各模型在智能体步骤中的表现，选择模型时参考。', '各モデルのエージェントのステップでの成績。モデル選択の参考になります。'),
 'Models that may not be used at home, at the office or on another network.': ('在家、在公司或其他网络下不能使用的模型。', '自宅・職場・その他のネットワークで使用を禁止するモデル。'),
 'Delete old dynamic memory after': ('动态记忆超过此时间就删除', 'この期間を過ぎた動的メモリを削除:'),
 'Copy memory text from source pages to target pages on a schedule.': ('按计划把记忆文本从来源页面复制到目标页面。', 'メモリのテキストを定期的にコピー元のページからコピー先のページへコピーします。'),
 'Memory endpoints': ('记忆读写位置', 'メモリの読み書き先'),
 'Reusable instructions the agent can run as a step; each needs a name and a description.': ('智能体可以作为步骤运行的可复用指令；每个都需要名称和描述。',
                                                                                             'エージェントがステップとして実行できる再利用可能な指示。それぞれ名前と説明が必要です。'),
 'Finder shows the folder for {name}. Right-click it › Share › Share Folder, choose {name}, set "Only people you invite" and "Can make changes", then send the invitation.': ('访达里已经选中给 '
                                                                                                                                                                              '{name} '
                                                                                                                                                                              '的文件夹。右键它 '
                                                                                                                                                                              '› '
                                                                                                                                                                              '共享 '
                                                                                                                                                                              '› '
                                                                                                                                                                              '共享文件夹，选 '
                                                                                                                                                                              '{name}，设成「仅受邀用户」和「可更改」，然后发出邀请。',
                                                                                                                                                                              'Finder '
                                                                                                                                                                              'で '
                                                                                                                                                                              '{name} '
                                                                                                                                                                              '用のフォルダを選択しました。右クリック '
                                                                                                                                                                              '› '
                                                                                                                                                                              '共有 '
                                                                                                                                                                              '› '
                                                                                                                                                                              'フォルダを共有 '
                                                                                                                                                                              'で '
                                                                                                                                                                              '{name} '
                                                                                                                                                                              'を選び、「参加依頼した人のみ」と「変更可能」にして招待を送ってください。'),
 '“{name}” is being changed by a running task right now, so it was not saved. Try again in a moment.': ('“{name}”正被一个运行中的任务修改，所以没有保存。请稍后再试。',
                                                                                                        '「{name}」は実行中のタスクが変更中のため、保存しませんでした。少し待ってからもう一度お試しください。'),
 'reverted': ('已回退', '取り消し済み'),
 'Article': ('文章', '文章'),
 'Select some text or cells in the document first. For a picture, a chart or the layout, use “Mark” in the bar below.': ('请先在文档里选中一些文字或单元格。要问图片、图表或版式，请用下面工具栏里的“圈选”。',
                                                                                                                         'まず文書内の文字かセルを選択してください。画像・グラフ・レイアウトについては、下のバーの「マーク」を使ってください。'),
 'Change this part of the open document as follows: ': ('请按下面的要求修改打开的文档里的这一部分：', '開いている文書のこの部分を次のように修正してください：'),
 'Mark as Feature (not a bug)': ('标记为设计如此（不是问题）', '仕様としてマーク（バグではない）'),
 'Copy Code Name': ('复制代码名', 'コード上の名前をコピー'),
 'Generating diagram…': ('正在生成示意图…', '図を生成中…'),
 'Available after the diagram milestone': ('示意图里程碑完成后可用', '図のマイルストーン後に利用可能'),
 'Could not save the diagram.': ('无法保存该示意图。', '図を保存できませんでした。'),
 'Could not rasterize the page': ('无法把这一页转成图片', 'ページを画像に変換できませんでした'),
 "No thinking removes the reasoning fields from each step's output. Flash also swaps in a minimal system prompt and shorter page waits (official Fast Agent template).": ('无思考档会去掉每步输出里的推理字段。极速档还会换用极简系统提示词并缩短页面等待（官方 '
                                                                                                                                                                          'Fast '
                                                                                                                                                                          '智能体模板）。',
                                                                                                                                                                          '思考なしは各ステップの出力から推論フィールドを取り除きます。フラッシュはさらに最小限のシステムプロンプトに切り替え、ページ待機を短縮します（公式 '
                                                                                                                                                                          'Fast '
                                                                                                                                                                          'エージェントテンプレート）。'),
 'discovery failed': ('检测失败', '検出失敗'),
 'New quick command': ('新建快捷命令', '新しいクイックコマンド'),
 'Edit quick command': ('编辑快捷命令', 'クイックコマンドを編集'),
 'Delete the quick command “{name}”?': ('删除快捷命令“{name}”？', 'クイックコマンド「{name}」を削除しますか？'),
 'A script runs at once, without the AI. A question goes to the Agent as a new conversation; its answer comes out of the collapsed button. Double-click the collapsed button for layer 2 of its grid, where new commands go; scroll there for the other layers.': ('脚本直接运行，不经过 '
                                                                                                                                                                                                                                                                   'AI。问题会作为一个新对话交给智能体，回答从最小化圆按钮里出来。双击最小化圆按钮打开九宫格第 '
                                                                                                                                                                                                                                                                   '2 '
                                                                                                                                                                                                                                                                   '层，新指令放在那里；在九宫格里滚动可以翻到其他层。',
                                                                                                                                                                                                                                                                   'スクリプトは '
                                                                                                                                                                                                                                                                   'AI '
                                                                                                                                                                                                                                                                   'を通さずすぐ実行されます。質問は新しい会話としてエージェントに送られ、答えは最小化ボタンから出てきます。最小化ボタンをダブルクリックするとグリッドの第 '
                                                                                                                                                                                                                                                                   '2 '
                                                                                                                                                                                                                                                                   '層（新しいコマンドの置き場）が開き、スクロールでほかの層に移れます。'),
 'Week': ('每周', '毎週'),
 'Save conversation as': ('对话另存为', '会話を別名で保存'),
 'Markdown': ('Markdown', 'Markdown'),
 'Word document': ('Word 文档', 'Word 文書'),
 'Plain text': ('纯文本', 'プレーンテキスト'),
 'Could not save the file: {error}': ('无法保存文件：{error}', 'ファイルを保存できませんでした：{error}'),
 'New conversations run on this Mac again, until you pick a device the next time.': ('新对话回到这台 Mac 上运行，直到你下次再选别的设备。', '新しい会話はこの Mac で実行されます。次にデバイスを選ぶまでそのままです。'),
 '{device} is not shared with you any more. Pick a device with 🎛️ Move to.': ('{device} 已经不再共享给你。请用「🎛️ 换设备」重新选一台设备。',
                                                                              '{device} はもう共有されていません。「🎛️ 実行先」でデバイスを選び直してください。'),
 'Send new conversations to the device I picked last with 🎛️ Move to': ('新对话自动发到上次用「🎛️ 换设备」选的设备', '新しい会話を、前回「🎛️ 実行先」で選んだデバイスに自動で送る'),
 'Once you have sent a conversation to another device, every new conversation starts there without asking again. To come back, choose 🎛️ Move to › This Mac.': ('把对话发到另一台设备一次之后，之后每个新对话都直接在那台设备上开始，不用再选。想换回来，选「🎛️ '
                                                                                                                                                                '换设备」›「这台 '
                                                                                                                                                                'Mac」。',
                                                                                                                                                                '一度ほかのデバイスに会話を送ると、それ以降の新しい会話は選び直さなくてもそのデバイスで始まります。戻すには「🎛️ '
                                                                                                                                                                '実行先」›「この '
                                                                                                                                                                'Mac」を選びます。')}

REVIEW_EXTRA_SOURCE_STRINGS = ['Markdown', 'Word document', 'Plain text']   # CONVERSATION_EXPORT_FORMATS names
