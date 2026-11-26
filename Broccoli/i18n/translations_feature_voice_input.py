# -*- coding: utf-8 -*-
"""Translations for voice input (2026-11-16; the microphone buttons of the prompt bars).
Loaded by i18n/gen_ts.py (one table per feature)."""

FEATURE_TRANSLATIONS = {
    'Voice input': ('语音输入', '音声入力'),
    'Stop': ('停止', '停止'),
    'Downloading the speech model for this language… {percent}%': (
        '正在下载这种语言的语音模型… {percent}%',
        'この言語の音声モデルをダウンロード中… {percent}%'),
    'Voice input is not available on this Mac. It needs macOS 26 or later.': (
        '这台 Mac 不能用语音输入，需要 macOS 26 或更新的系统。',
        'この Mac では音声入力を使えません。macOS 26 以降が必要です。'),
    'This Mac cannot recognize speech on the device.': (
        '这台 Mac 不支持在本机识别语音。',
        'この Mac はデバイス上での音声認識に対応していません。'),
    'Voice input does not support this language. Put a supported language first in Settings → Languages.': (
        '语音输入不支持这种语言。请在 设置 → Languages 里把一种支持的语言放到第一个。',
        '音声入力はこの言語に対応していません。設定 → Languages で対応している言語を先頭にしてください。'),
    'The speech model for this language could not be downloaded. Check the network and try again.': (
        '这种语言的语音模型没能下载下来。请检查网络后再试。',
        'この言語の音声モデルをダウンロードできませんでした。ネットワークを確認して、もう一度お試しください。'),
    'Broccoli may not use the microphone. Allow it in System Settings → Privacy & Security → Microphone.': (
        'Broccoli 没有使用麦克风的权限。请在 系统设置 → 隐私与安全性 → 麦克风 里允许。',
        'Broccoli にマイクの使用が許可されていません。システム設定 → プライバシーとセキュリティ → マイク で許可してください。'),
    'The microphone could not be opened.': ('麦克风打不开。', 'マイクを開けませんでした。'),
    'Voice input stopped because of an error.': ('语音输入因为出错停止了。', 'エラーのため音声入力を停止しました。'),
    # Settings › General › Voice input
    'Speak instead of typing: which microphone listens, and in which language.': (
        '用说话代替打字：用哪个麦克风听、听哪种语言。',
        '入力の代わりに話す：どのマイクで、どの言語を聞き取るか。'),
    'Microphone': ('麦克风', 'マイク'),
    'Language': ('语言', '言語'),
    'Automatic': ('自动', '自動'),
    'Follow the system': ('跟随系统', 'システムに合わせる'),
    '{name} (not connected)': ('{name}（没有接上）', '{name}（未接続）'),
    'Open Microphone Settings': ('打开麦克风设置', 'マイクの設定を開く'),
    'Click the microphone at the right of a prompt box and speak; click again to stop. What you say is '
    'turned into text on this Mac, in one language at a time. “Automatic” listens in the first language '
    'of Settings → Languages.': (
        '点输入框右边的麦克风就可以说话，再点一下停止。你说的话在这台 Mac 上转成文字，一次只听一种语言。'
        '“自动”听的是 设置 → Languages 里排第一的语言。',
        '入力欄の右にあるマイクをクリックして話し、もう一度クリックすると止まります。話した内容はこの Mac 上で'
        '文字になり、一度に聞き取れる言語は 1 つです。「自動」は 設定 → Languages の先頭の言語で聞き取ります。'),
    # Settings › Models › Local models (2026-11-16)
    'Local models': ('本地模型', 'ローカルモデル'),
    'Models that run on this Mac: what is there, and their profiles.': (
        '在这台 Mac 上运行的模型：有哪些，以及它们的配置。',
        'この Mac 上で動くモデル：何があるか、そのプロファイル。'),
    'These models run on this Mac: what you say or write to them does not leave it. A model that is '
    'ready is used through an ordinary profile — choose it on the Model roles page like any other. '
    'The ones built into macOS get their profile by themselves.': (
        '这些模型在这台 Mac 上运行：你对它们说的、写的都不会离开这台 Mac。就绪的模型通过一个普通的配置来用，'
        '和别的配置一样在“模型分工”页里选。macOS 自带的模型会自动建好配置。',
        'これらのモデルはこの Mac 上で動きます。話した内容や書いた内容がこの Mac の外に出ることはありません。'
        '準備ができたモデルは通常のプロファイルとして使い、ほかと同じように「モデルの役割」ページで選びます。'
        'macOS に内蔵のモデルにはプロファイルが自動で作られます。'),
    'Add as profile': ('添加为配置', 'プロファイルとして追加'),
    'Ready · profile “{name}”': ('已就绪 · 配置“{name}”', '準備完了 · プロファイル「{name}」'),
    'Ready · no profile yet': ('已就绪 · 还没有配置', '準備完了 · プロファイル未作成'),
    'Apple Intelligence is turned off in System Settings': (
        'Apple 智能在系统设置里没有打开', 'システム設定で Apple Intelligence がオフになっています'),
    'macOS is still downloading it': ('macOS 还在下载它', 'macOS がまだダウンロード中です'),
    'Not available on this Mac': ('这台 Mac 不支持', 'この Mac では使えません'),
    'The models on this Mac could not be started.': ('这台 Mac 上的模型没能启动。', 'この Mac 上のモデルを起動できませんでした。'),
    'This profile is a model on this Mac: it runs on the device.': (
        '这个配置是这台 Mac 上的模型：直接在本机运行。', 'このプロファイルはこの Mac 上のモデルです。デバイス上で動きます。'),
    'On-device': ('本机运行', 'デバイス上で実行'),
    # the tidy-up pass (2026-11-16)
    'Tidy what was heard with the default chat model': ('识别完再用默认的对话模型整理一遍', '聞き取った内容を既定のチャットモデルで整える'),
    'When you stop, the text is sent once to the model selected for chat, which removes filler words '
    'and fixes punctuation and obvious mis-hearings; it then replaces what was heard (undo brings that '
    'back). With an on-line model the text leaves this Mac; the recording never does.': (
        '停下以后，文字会发给当前选中的对话模型一次，由它去掉口头语、改好标点和明显听错的字，然后替换掉刚才听到的内容'
        '（撤销可以变回原样）。用联网的模型时，这段文字会离开这台 Mac；录音永远不会。',
        '止めたあと、テキストを選択中のチャットモデルに一度だけ送り、つなぎ言葉を除いて句読点や明らかな聞き間違いを直し、'
        '聞き取った内容と置き換えます（取り消すと元に戻ります）。オンラインのモデルではテキストがこの Mac の外に出ます。'
        '録音が外に出ることはありません。'),
    'Tidying what you said… Click to keep it as it is.': ('正在整理你说的话… 点一下保持原样。', '話した内容を整えています… クリックするとそのまま残します。'),
    # downloadable speech models (2026-11-16)
    "A downloaded speech model listens instead of the one built into macOS when its profile comes first in the "
    "“Speech to text” row of the Model roles page. Downloads come from the model runtime's release page and can be "
    "stopped and gone on with later.": (
        '下载的语音模型，只要它的配置排在“模型分工”页“语音转文字”那一行的第一个，就由它代替 macOS 自带的来听。'
        '模型从运行库的发布页下载，可以中途停下、以后接着下。',
        'ダウンロードした音声モデルは、そのプロファイルが「モデルの役割」ページの「音声文字起こし」行の先頭にあるとき、'
        'macOS 内蔵のものに代わって聞き取ります。モデルはランタイムのリリースページからダウンロードされ、'
        '途中で止めて、あとで続きから再開できます。'),
    'Delete “{name}” from this Mac? It can be downloaded again.': (
        '把“{name}”从这台 Mac 上删除？以后可以重新下载。', '「{name}」をこの Mac から削除しますか？あとで再度ダウンロードできます。'),
    'Download': ('下载', 'ダウンロード'),
    'Stop download': ('停止下载', 'ダウンロードを中止'),
    'Downloading… {percent}%': ('下载中… {percent}%', 'ダウンロード中… {percent}%'),
    'Not downloaded': ('没有下载', '未ダウンロード'),
    'Unpacking…': ('解压中…', '展開中…'),
    'The download failed. Start it again to go on.': ('下载失败了。再点一次下载可以接着下。', 'ダウンロードに失敗しました。もう一度開始すると続きから再開します。'),
    # the circle's recording: the card above it, the remembered text box, the clipboard (2026-11-16)
    'Listening…': ('正在听…', '聞き取り中…'),
    'Nothing was heard.': ('什么都没听到。', '何も聞き取れませんでした。'),
    'Tidying what you said…': ('正在整理你说的话…', '話した内容を整えています…'),
    '→ Clipboard': ('→ 剪贴板', '→ クリップボード'),
    '→ {app}': ('→ {app}', '→ {app}'),
    '→ {app}…': ('→ {app}…', '→ {app}…'),
    '✓ Typed into {app}': ('✓ 已填入 {app}', '✓ {app} に入力しました'),
    '✓ Typed into {app} · copied': ('✓ 已填入 {app} · 已复制', '✓ {app} に入力しました · コピー済み'),
    'Could not type into {app}. Copied: paste with ⌘V.': (
        '没能填进 {app}。已复制，按 ⌘V 粘贴。', '{app} に入力できませんでした。コピー済みです。⌘V で貼り付けてください。'),
    'Sent to {app}. Not there? Paste with ⌘V.': ('已发给 {app}。没出现的话按 ⌘V 粘贴。', '{app} に送りました。入っていなければ ⌘V で貼り付けてください。'),
    'Copied: paste with ⌘V.': ('已复制，按 ⌘V 粘贴。', 'コピーしました。⌘V で貼り付けてください。'),
    'Also copy what the circle heard to the clipboard': ('小圆点听到的内容同时复制到剪贴板', '丸ボタンで聞き取った内容をクリップボードにもコピーする'),
    'Hold the circle for half a second and speak: what you say is typed into the text box that had '
    'the keyboard when you began, in whatever app, even if you have moved on by then. Where an app '
    'does not allow that, the words are on the clipboard.': (
        '按住小圆点半秒再说话：你说的话会填进开始时正在打字的那个输入框，不管它在哪个软件里，'
        '即使这时你已经去做别的了。有的软件不允许这样填，这时内容在剪贴板里。',
        '丸ボタンを 0.5 秒押したまま話すと、話し始めたときにキーボードが向いていた入力欄に、どのアプリでも、'
        'そのあと別の作業に移っていても入力されます。それを許可しないアプリでは、内容はクリップボードに入ります。'),
    # the user's own tidy instructions
    "Broccoli's own": ('Broccoli 自带的', 'Broccoli 標準'),
    'My instructions': ('我的提示词', '自分の指示'),
    'Tidy instructions (the ticked one is used)': ('整理用的提示词（用打勾的那一条）', '整え方の指示（チェックを付けたものを使用）'),
    "Your own instructions replace Broccoli's way of tidying. The dictated text is added after them, "
    "and the model is still told to answer with the rewritten text only.": (
        '你自己的提示词会代替 Broccoli 自带的整理方式。听到的文字会接在它后面，并且仍然会要求模型只回整理好的文字。',
        '自分の指示は Broccoli 標準の整え方の代わりに使われます。聞き取ったテキストはその後ろに付けられ、'
        'モデルには引き続き、整えたテキストだけを返すよう伝えます。'),
    'How the dictated text should be rewritten, in your own words. For example: “Turn it into a '
    'polite e-mail in Japanese.”': (
        '用你自己的话写：听到的文字要怎么改写。例如：“改写成一封礼貌的日文邮件。”',
        '聞き取ったテキストをどう書き直すかを自分の言葉で。例：「丁寧な日本語のメールにしてください。」'),
    # the other way to record with the circle (2026-11-16)
    'Long press on the circle': ('长按小圆点', '丸ボタンの長押し'),
    'Hold while speaking, let go to end': ('按住说话，松手结束', '押している間だけ聞き取る'),
    'Let go and keep speaking, click to end': ('松手后继续听，再点一下结束', '離しても聞き取りを続け、クリックで終了'),
    'click the circle to stop': ('再点一下小圆点结束', '丸ボタンをクリックで終了'),
    # the sound before a downloaded model hears it (2026-11-21): three switches
    'Sound for the downloaded speech models': ('下载的语音模型：听之前先处理声音', 'ダウンロードした音声モデル：聞き取る前の音の処理'),
    'Find the speech with a voice detector': ('用人声检测找出说话的部分', '音声検出で話している部分を見つける'),
    'Make quiet sound louder': ('把小的声音放大', '小さい音を大きくする'),
    'Remove noise such as typing': ('去掉键盘声之类的杂音', 'キーボードの音などの雑音を取り除く'),
    'These work on the sound before Qwen3, SenseVoice or Whisper hears it; Apple Speech listens by itself '
    'and is not changed. The voice detector hears quiet and far-away voices that a loudness threshold '
    'misses. Removing noise helps when you type while you speak; it needs the voice detector, and it '
    'can cost a little accuracy on clean sound. A saved recording keeps the sound as the microphone '
    'gave it.': (
        '这三项是在 Qwen3、SenseVoice、Whisper 听之前先处理声音；Apple Speech 自己听，不受影响。人声检测能听出只看音量会漏掉的小声和远处的说话声。'
        '去杂音在边说边打字时有用；它要和人声检测一起开，对本来就干净的声音可能略微影响准确度。保存下来的录音仍是麦克风原样的声音。',
        'これらは Qwen3・SenseVoice・Whisper が聞き取る前の音に働きます。Apple Speech は自分で聞き取るため、影響を受けません。音声検出は、音量だけでは拾えない小さな声や遠くの声を聞き取ります。'
        '雑音の除去は、話しながらキーを打つときに役立ちます。音声検出と一緒に使う必要があり、もともときれいな音では精度が少し下がることがあります。保存される録音は、マイクが拾ったままの音です。'),
    # the language and the model choosers on the circle's card (2026-11-21; at once, for all of it: 2026-11-22)
    'The language you speak. A change is used at once: what you have said so far is heard again in it.': (
        '你说的语言。换了马上生效：已经说过的话也会按新的语言重新听一遍。',
        '話す言語。変更はすぐに使われ、それまでに話した内容も新しい言語で聞き直されます。'),
    'The speech model that listens. A change is used at once: what you have said so far is heard '
    'again by it.': (
        '用来听写的语音模型。换了马上生效：已经说过的话也会用新的模型重新听一遍。',
        '聞き取りに使う音声モデル。変更はすぐに使われ、それまでに話した内容も新しいモデルで聞き直されます。'),
    'Hearing what you said again with the new choice…': (
        '正在按新的选择重新听你说过的话…',
        '新しい設定で、話した内容を聞き直しています…'),
    'Could not switch: {reason}': ('没能切换：{reason}', '切り替えられませんでした：{reason}'),
    # dictations in the history; groups made automatically (2026-11-16)
    'Dictation': ('听写', '音声入力'),
    'Translation': ('翻译', '翻訳'),
    'Keep what the circle heard in the history (group “Dictation”)': (
        '把小圆点听到的内容留在历史记录里（分组“听写”）', '丸ボタンで聞き取った内容を履歴に残す（グループ「音声入力」）'),
    # the voice input shortcut; all shortcuts on one page; the small question marks (2026-11-16)
    'Record Voice input shortcut': ('录制语音输入快捷键', '音声入力のショートカットを記録'),
    # 2026-11-17: three voice shortcuts, and a key pressed twice as a shortcut
    'Record Circle voice shortcut': ('录制小圆点语音快捷键', '丸ボタン音声のショートカットを記録'),
    # 2026-11-17: the tidy chooser on the circle's card, and the corrections Broccoli learns
    'Tidy: {name}': ('整理：{name}', '整形：{name}'),
    'No tidy-up': ('不整理', '整形しない'),
    'How the words are tidied when this recording ends': ('这次录音结束后用哪种方式整理文字', 'この録音が終わったあと、文字をどう整形するか'),
    'Learned corrections (heard → meant)': ('学到的改正（听到的 → 你的意思）', '学習した修正（聞こえた語 → 意図した語）'),
    'When you change a dictated word in Broccoli\'s prompt box before sending, Broccoli remembers the change '
    'and makes it by itself next time, in every app, without asking a model. Names from the Wiki and what '
    'you asked Broccoli to remember also go along with the tidy-up.': (
        '你在 Broccoli 的输入框里把听写出来的词改掉再发送时，Broccoli 会记住这处改动，下次自己改，在所有软件里都生效，不用问模型。整理时还会带上 Wiki 里的名字和你让 Broccoli 记住的内容。',
        'Broccoli の入力欄で、音声入力された語を送信前に直すと、Broccoli はその修正を覚え、次からはどのアプリでもモデルに尋ねずに自分で直します。整形のときは、Wiki の名前や Broccoli に覚えさせた内容も一緒に渡されます。'),
    # 2026-11-17: a shortcut's Control / Option / Shift / Command can be tied to one side of the keyboard
    'Left {key}': ('左{key}', '左{key}'),
    'Right {key}': ('右{key}', '右{key}'),
    'Which side of the keyboard counts for {keys}?': ('这个快捷键里的 {keys} 认键盘的哪一侧？', 'このショートカットの {keys} は、キーボードのどちら側を使いますか？'),
    'You pressed the left one.': ('你刚才按的是左边的。', 'いま押したのは左側のキーです。'),
    'You pressed the right one.': ('你刚才按的是右边的。', 'いま押したのは右側のキーです。'),
    'You pressed keys on both sides.': ('你刚才左右两边的键都按了。', 'いま左右両方のキーを押しました。'),
    'The keyboard has these keys on the left and on the right. This shortcut can answer to both, '
    'or only to the ones on one side.': (
        '这些键在键盘左边和右边各有一个。这个快捷键可以两边都认，也可以只认其中一边的。',
        'これらのキーはキーボードの左右に 1 つずつあります。このショートカットは両方で使えるようにも、片側だけにもできます。'),
    'Either side': ('左右都行', '左右どちらでも'),
    'Left only': ('只认左边', '左側だけ'),
    'Right only': ('只认右边', '右側だけ'),
    'Two shortcuts use the same keys: one for either side and one for one side only. '
    'Give them different keys, or different sides.': (
        '有两个快捷键用了同样的键：一个左右都认，一个只认一边。请给它们不同的键，或者分到不同的两边。',
        '2 つのショートカットが同じキーを使っています（片方は左右どちらでも、もう片方は片側だけ）。別のキーにするか、左右を分けてください。'),
    'Record Prompt voice shortcut': ('录制输入框语音快捷键', '入力欄音声のショートカットを記録'),
    'Record Recording shortcut': ('录制长录音快捷键', '録音のショートカットを記録'),
    'Press it to start listening and again to stop. The words go into the text box you are typing in, '
    'in any app, by way of the round button.': (
        '按一下开始听，再按一下停止。文字填进你正在打字的输入框（任何软件里），通过小圆点完成。',
        '押すと聞き取りを始め、もう一度押すと止まります。文字は、いま入力しているテキスト欄（どのアプリでも）に丸ボタン経由で入ります。'),
    'Press it to start listening and again to stop. The words go into Broccoli\'s own prompt box. With no '
    'prompt box on screen, the nearest one comes out first: the round button\'s input box, or the main window.': (
        '按一下开始听，再按一下停止。文字写进 Broccoli 自己的输入框。屏幕上没有输入框时，先把最近的那个叫出来：小圆点的输入框，或者主窗口。',
        '押すと聞き取りを始め、もう一度押すと止まります。文字は Broccoli 自身の入力欄に入ります。入力欄が画面にないときは、いちばん近いもの（丸ボタンの入力欄、またはメインウインドウ）を先に出します。'),
    'Press it to start a recording that is kept (sound and text become a conversation of their own) and '
    'again to stop. The same as a long press on the microphone mark of the Agent prompt box.': (
        '按一下开始一段会保存的录音（声音和文字会成为一条单独的对话），再按一下结束。和长按 Agent 输入框的麦克风标记一样。',
        '押すと保存される録音を始め（音声と文字が 1 つの会話になります）、もう一度押すと終わります。Agent 入力欄のマイクの印を長押しするのと同じです。'),
    'Voice input shortcut must be different from the other shortcuts.': (
        '语音输入快捷键不能和其他快捷键相同。', '音声入力のショートカットは、ほかのショートカットと別のものにしてください。'),
    "Press it to start listening and again to stop. With Broccoli's window in front the words go into its prompt box; "
    "anywhere else they go into the text box you are typing in.": (
        '按一下开始听，再按一下停。Broccoli 的窗口在最前面时，字进它的输入框；在别处时，字进你正在打字的那个输入框。',
        '押すと聞き取りを始め、もう一度押すと止まります。Broccoli のウインドウが前面にあるときはその入力欄に、'
        'それ以外では入力中のテキスト欄に入ります。'),
    "Shows Broccoli's main window, or puts it away.": ('显示或收起 Broccoli 的主窗口。', 'Broccoli のメインウインドウを表示／しまいます。'),
    'Takes a screenshot of the same place as the last one.': ('在和上次相同的位置截一张图。', '前回と同じ場所のスクリーンショットを撮ります。'),
    'Opens the screenshot tool to pick a part of the screen.': ('打开截图工具，框选屏幕的一部分。', 'スクリーンショットツールを開いて、画面の一部を選びます。'),
    'Brings the main window out from the screen edge it hides at, or sends it back.': (
        '把藏在屏幕边上的主窗口叫出来，或者送回去。', '画面の端に隠れているメインウインドウを出す／戻します。'),
    'Shows or hides the round button while the main window is open.': ('主窗口开着时，显示或隐藏最小化圆按钮。', 'メインウインドウを開いている間、丸ボタンを表示／非表示にします。'),
    'Opens the column of AI tasks at the pointer; press it again to close it.': (
        '在鼠标旁打开 AI 任务列，再按一下关闭。', 'ポインタのそばに AI タスクの列を開きます。もう一度押すと閉じます。'),
    "Opens this layer of the round button's grid.": ('打开最小化圆按钮九宫格的这一层。', '丸ボタンのグリッドのこの層を開きます。'),
    'Its shortcut is set on the “Shortcuts & tools” page. Press it to open the column at the pointer; press it again to close it.': (
        '它的快捷键在“快捷键与工具”页里设置。按一下在鼠标旁打开任务列，再按一下关闭。',
        'ショートカットは「ショートカットとツール」ページで設定します。押すとポインタのそばに列を開き、もう一度押すと閉じます。'),
    # recordings that are kept; sound files → text; dragging words out of the card (2026-11-17)
    'Recording': ('录音', '録音'),
    'Transcript': ('转写', '文字起こし'),
    'Recording… Click to stop and keep it.': ('正在录音… 点一下停止并保存。', '録音中… クリックで停止して保存します。'),
    '● Recording {time}': ('● 正在录音 {time}', '● 録音中 {time}'),
    'To text': ('转成文字', '文字にする'),
    'Turn what is said in this file into text, as a conversation of its own.': (
        '把这个文件里说的话转成文字，单独存成一条对话。', 'このファイルの音声を文字にして、ひとつの会話として保存します。'),
    'This file could not be turned into text.': ('这个文件没能转成文字。', 'このファイルを文字にできませんでした。'),
    'No speech-to-text model is chosen. Pick one in Settings → Models → Model roles (“Speech to text”).': (
        '还没有选语音转文字的模型。请在 设置 → 模型 → 模型分工 的“语音转文字”那一行选一个。',
        '音声文字起こしのモデルが選ばれていません。設定 → モデル → モデルの役割 の「音声文字起こし」で選んでください。'),
    'Copy (drag it to put the whole text somewhere)': ('复制（按住拖出去 = 把整段文字拖到别处）', 'コピー（ドラッグすると全文をほかの場所へ）'),
    # a recording also listens to what the Mac plays (2026-11-19)
    'Me:': ('我：', '自分：'),
    'Them:': ('对方：', '相手：'),
    'microphone only': ('只有麦克风', 'マイクのみ'),
    'System sound only': ('只录系统声音', 'システムの音だけ'),
    'Record both': ('两个都录', '両方録音'),
    'Only the microphone was recorded.': ('这次只录到了麦克风。', '今回はマイクだけが録音されました。'),
    'Broccoli may not record the sound this Mac plays. Allow it in System Settings → Privacy & Security → '
    'Screen & System Audio Recording (“System Audio Recording Only”).': (
        'Broccoli 没有权限录这台 Mac 播放的声音。请在 系统设置 → 隐私与安全性 → 屏幕与系统音频录制 里的“仅系统音频录制”中允许它。',
        'Broccoli はこの Mac が再生する音を録音できません。システム設定 → プライバシーとセキュリティ → 画面とシステムオーディオ録音 の'
        '「システムオーディオ録音のみ」で許可してください。'),
    'The sound this Mac plays could not be recorded.': ('这台 Mac 播放的声音没能录下来。', 'この Mac が再生する音を録音できませんでした。'),
    'This Mac’s sound is coming out of its speakers, so the microphone also hears the other side. '
    'If both are recorded, some of their words may appear a second time under “Me”.\n\n'
    'System sound only: the other side is recorded cleanly; your own voice is not recorded.\n'
    'Record both: your voice is recorded too, with some of their words repeated.\n\n'
    'With headphones this does not happen.': (
        '这台 Mac 的声音正从扬声器放出来，麦克风也会听到对方的声音。两个都录的话，对方的一些话可能会在“我”下面再出现一遍。\n\n'
        '只录系统声音：对方的话录得干净，但你自己说的话不会被录下来。\n'
        '两个都录：你说的话也会录下来，但对方的话会有一些重复。\n\n'
        '戴耳机就不会有这个问题。',
        'この Mac の音はスピーカーから出ているため、マイクにも相手の声が入ります。両方録音すると、相手の言葉の一部が「自分」の下にもう一度出ることがあります。\n\n'
        'システムの音だけ：相手の声はきれいに録音されますが、自分の声は録音されません。\n'
        '両方録音：自分の声も録音されますが、相手の言葉が一部重複します。\n\n'
        'ヘッドホンを使えばこの問題は起きません。'),
    "Don't Insert": ('不插入', '挿入しない'),
    'Insert After All': ('还是插入', 'やはり挿入'),
    'Keep listening, but do not put the words into the app in front (another app that follows the live transcript still gets them)': ('继续听，但不把字打进前台的软件（订阅实时转写的软件照样收得到）', '聞き取りは続けますが、手前のアプリには入力しません（リアルタイム文字起こしを受け取るアプリには届きます）'),
    '→ Nowhere: only heard': ('→ 不插入：只听写', '→ 入力しない：聞き取りのみ'),
    'Not inserted: only heard (kept in the dictation history)': ('没有插入：只听写了（已存进听写记录）', '入力していません：聞き取りのみ（音声入力の履歴に保存）'),
    # 2026-11-22: the dictated words on the circle's card can be edited (style book 5.1.18)
    'Done editing (⌘↩)': ('改好了（⌘↩）', '編集を終える（⌘↩）'),
    'Editing: press ✓ when done. Broccoli learns from what you change.': ('正在修改：改好按 ✓。Broccoli 会从你的修改里学习。', '編集中：終わったら ✓ を押してください。Broccoli は直した内容から学びます。'),
    'Press ✓ when it reads right.': ('改对了就按 ✓。', '正しくなったら ✓ を押してください。'),
    'Press ✓ when it reads right: then it goes into {app}.': ('改对了就按 ✓，然后填进 {app}。', '正しくなったら ✓ を押してください。{app} に入力します。'),
    'Press ✓ when it reads right: then it is copied.': ('改对了就按 ✓，然后复制到剪贴板。', '正しくなったら ✓ を押してください。クリップボードにコピーします。'),
    'Learned: {pairs}': ('学到了：{pairs}', '学習しました：{pairs}'),
    'Kept as it was.': ('保持原样。', '元のままにしました。'),
    'Copied as you changed it.': ('已按你改的复制。', '直した内容でコピーしました。'),
    'Kept as you changed it.': ('已按你改的保存。', '直した内容で保存しました。'),
    'Copied as you changed it. {app} still has the words as they were.': ('已按你改的复制。{app} 里的字没有改。', '直した内容でコピーしました。{app} の文字は元のままです。'),
    'Kept as you changed it. {app} still has the words as they were.': ('已按你改的保存。{app} 里的字没有改。', '直した内容で保存しました。{app} の文字は元のままです。'),
}
