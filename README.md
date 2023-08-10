# 🥦Broccoli: A Floating Helper on Mac Desktop
![Y5Xt1FR](https://i.imgur.com/Y5Xt1FR.png)

Broccoli is a simple floating helper of GPT. Private APIs needed.

Broccoli 是一个桌面级的 GPT 助手，拥有问答、命令、翻译、润色、总结等多种功能，可以用来储存提示词；也可以快速填入已储存的提示词；可以用来阅读长文本，不限长度；还可以导出对话记录为 Markdown 格式……

## 解决问题

Broccoli 是 2023 年 2 月我花三天时间做的一个小软件，本来是应潮流而做的桌面助手，后来觉得只是对话功能不够，于是增添了其他功能模式，基本上覆盖了大部分“桌面助手”类应用的功能范畴。

目前，桌面级的 GPT 应用存在以下问题：

1. **功能雷同，竞品重复**

   当前，市面上 AI 套壳软件非常多。之前没接触过 Broccoli 的用户可能也会把它当成是一个套壳应用。准确地说，它之前可能是的，只不过不是浏览器套壳，而是一个根据官方文档给出的样例代码去修改和改写得到的应用。但随着此类应用越来越多，与 AI 对话不再是阻碍，如何让技术走出网站、适应各种场景和需求才是难题。所以，Broccoli 陆续加入了很多新鲜的元素。或许 Broccoli 走的有点慢，但它基本上是从工具和使用需求出发的软件。Broccoli 在设计之初的独特功能有两个：第一，Broccoli 很早就有 Command 模式，它能让用户基于需求得到一个 AI 写的 AppleScript，并可在软件内直接运行（需要授予系统权限），写一封邮件并发送，或者在 Safari 内搜索一个特定的内容都不在话下。第二，长文本阅读。大部分阅读文档的服务都是线上订阅制，需要注册账户，每日有一定的问题配额、单次上传文档大小限制、页数限制等等。但 Broccoli 把这一功能转移到了桌面端，而且没有任何限制：所有 Embedings 过程在本地与 OpenAI 之间进行，询问过程也只会发送到 OpenAI 的服务器，不经过任何第三方服务（使用第三方 API 除外）。只要你能顺利进行 Embeddings，多长的文本都可以对答。

2. **UI 类似，功能冲突**

   写完 Broccoli 大约一个月之后，除了维护每日更新，就是能看到各路程序员造出的新鲜套壳。比较突出的雷同就是 UI 设计。第一点是界面上字体设计，很多软件会使用网页样式。Broccoli 在这方面的考虑是希望与本地文本软件连接互通，因此在字体上选择了更接近于文本阅读器的 Times New Roman，并且使用 Markdown 格式，干净整洁地呈现对话。这样也便于导出和在其他软件中接续使用。第二点是浮窗设计，很多桌面版的 AI 助手都采用了类 spotlight 的设计，可以唤出后快速对话，但由于竞品功能类似，唤出所需的快捷键是有限的，因此这种形式可能未必真正能让用户用好功能，反而增加了多余的功能。如果其他软件已经有了这样的功能，秉持着不造轮子的态度，我希望 Broccoli 能搭配着原有的软件产生更好的效果。因此，Broccoli 可以以一个小球的形态悬浮于桌面的右下角，需要用的时候点击即可展开，若需再次最小化，只需点击上方蓝色横条即可。另外，类 spotlight 窗口使浮窗成为软件主窗口的附属品，是一个完全功能的辅助功能，因而存在割裂感。如若无法联通和同步记录，用户随手点击可能导致栏框消失，由此带来的信息流失也容易带来不安定感。Broccoli 主窗口浮窗化避免了这个问题。

3. **产品壁垒，无法迁移**

   在大量的同类竞品中，生成的对话历史常常不容易导出，尤其是对于保留了浏览器样式的软件而言，较少软件提供了这一选项（在早期如此，后期基本上都有此功能）。另一个突出的现象是，阅读长文本的功能大部分依赖线上，但对长文本的 Embeddings 工程文件却无法导出。如果用户删除了历史存储，那么就需要重新操作，这既是浪费算力，也是浪费金钱。导致这些问题的原由是软件通常无意于提供开放的文本信息。同样的一个需求痛点是：用户经常有保存提示词的需要，在特定桌面软件内使用的提示词却只能通过该软件访问，用户无法单独查看。因此，Broccoli 试图提供一个一般的 txt 文档，以便用户查看和修改已保存的提示词。

## 功能亮点

### 本地储存

本软件（Broccoli）的全部可迁移文件都存储在`/Users/[用户名]/BroccoliAppPath`这一文件夹内。

其中，`Local`文件夹储存的是所有经过文本清理之后的长文本，均为 txt 文档，用户在长文本模式下可随时打开这些文档以显示，辅助阅读。

`Index`和`Embed`两个文件夹分别存储了有待经过 Embeddings 处理的文档和经过处理后的文档，和`Local`中的对应，均为 csv 文档，为确保长文档阅读功能正常运行，请勿删除或重命名这些文档，但用户可随时查看这些文档，若今后有其他用途（如使用代码行读取以用于研究等，可避免重复操作），亦可自行备份和迁移。

`CustomPrompt.txt`文档是用户自己保存的提示词库。每一个提示词之间使用`—`隔开，每一组提示词由提示词名称和提示词内容两部分构成，分别在一对`<|``|>`内。如有提取需要，用户可手动复制，亦可以借助上述规则，用正则表达式清理导出。

最后，`lang.txt`是用户在翻译、润色、总结等功能中期望使用的语言。软件默认为中文、英文和日文，用户可根据自己的需要增减语言。建议不要添加太多语言，列表太长可能不易翻找。

### 多模型选择

Broccoli 有七种模型可供选择，可以在 Settings 第一个下拉框中选择合适的模型：

1. GPT-3（openai 模块，需要 API）
2. ChatGPT（openai 模块，需要 API）
3. ChatGPT（revChatGPT.V3 模块，需要 API。注：目前该库已暂停维护。）
4. ChatGPT（revChatGPT.V1 模块，需要 session tokens。注：目前该库已暂停维护。）
5. ChatGPT (httpx 模块，需要 API，支持自定义第三方服务和使用第三方的代理 API)
6. Poe （POE 模块，需要 Quora 的 Formkey 和 Poe 的 Cookies）（这一模型包含了 GPT-4、ChatGPT、Claude、Claude+ 等多个子模型，如有订阅 Poe 可方便调用，且可跨平台同步）
7. EdgeGPT（EdgeGPT 模块，需要导入 cookies.json）

### 储存提示词

在 Settings 界面里，用户可以将喜欢的提示词保存在 Broccoli 中。当模式选项为 Customize 的时候，用户将看到自己曾经收藏的提示词，并轻松切换。如前所述，提示词将以特定的规则保存在本地，用户亦可根据该规则于软件内添加，Broccoli 会将一切改动自动保存到本地。用户可随时在软件外打开、查看、修改。

### AI + AppleScript：AI 一键生成命令并执行

当模式选项为 Command 时，主界面将出现一个新的分屏，在用户输入需求后，AI 将在此分屏内提供可能的 AppleScript 命令。用户可以在此分屏内修改，并点击运行。由此，用户可以通过自然语言命令系统操作。若需要使用此功能，需要在 System Preferences 中给予 Accessibility 权限，如果有访问本地文件的需求，最好提前打开 Full Disk Access。目前这一功能在 macOS 自带软件中效果比较好。

### 在桌面与长文本对话

当用户在 menubar 的下拉栏中开启这一功能后，除了和上一功能一样出现一个分屏之外，主界面 Chat and ask 模式选项还将提供三种 Embeddings 方案，分别是从新 txt 文档中读取、从输入内容读取和从旧有内容读取。如果用户已经将文本整理在 txt 文档中，那么可以选择第一个方案，此后，用户便不再需要重新对这一文档进行重复操作，而是可从旧有文档的文件夹路径中找到该文档，并导入即可。另外，如果没有现成的 txt 文档，用户也可以把所得的文字内容复制粘贴到分屏内，然后点击相应的按钮，即可开始 Embeddings 过程，此后亦可通过打开旧有文档的方式访问这些被加工的文件。当过程结束后，主界面上屏将出现“Done”字样，随后用户即可在提示词框内输入提示语，进行对话。

### 桌面浮窗设计

与类 spotlight 设计不同，Broccoli 注重的不是 UI 与系统设计的相似性或者可取代性，而是软件使用和信息的连续性。在参考了其他浮窗设计后，Broccoli 在窗口展开时与 Strawberry 以及 Tomato（两个我之前写的软件）保持了类似的条形按钮设计，同时将缩小后的窗口改为圆形图标，既一目了然，又不干扰桌面的日常活动。

## 界面一览

### 新版本

1. 主界面

<p align="center">
  <img src="https://i.imgur.com/ryxqfrE.png" width=240 />
  <img src="https://i.imgur.com/IT1BA4J.png" width=240 />
</p>

2. 设置界面

<p align="center">
  <img src="https://i.imgur.com/8YtaXZq.png" width=240 />
  <img src="https://i.imgur.com/ujWrHxu.png" width=240 />
</p>

3. 最小化动画

![scaling](https://github.com/Ryan-the-hito/Broccoli/blob/main/img/scale-ori.gif)

### 旧版本

<p align="center">
  <img src="https://i.imgur.com/q5vkJru.png" width=240 />
</p>

![example](https://github.com/Ryan-the-hito/Broccoli/blob/main/img/My%20Movie%203.gif)

## 环境要求

- MacOS（测试环境为 MacOS 12.6.5）
- M1、M2 芯片
- 网络环境自理 

## 下载安装

1. 从 [Releases](https://github.com/Ryan-the-hito/Broccoli/releases) 中点击最新发布的内容，下载 zip 档。另，Broccoli.Keyword.to.Script.alfredworkflow 是与 Alfred 适配的快捷键方案，用于唤醒和最小化 Broccoli，实现与点击相同的效果。如果事先安装并购买了 Alfred 的用户可以在 workflow 里面配置这一文件，设置用户想要的全局快捷键。
2. 下载到本地之后解压。
3. 将解压好的 app 档拖入 Finder 的 Application 文件夹。
4. 启动 Broccoli
5. 弹出获取 Accessibility（辅助功能）的弹窗，如下图示意。请在 System Preferences 里面允许。如果在软件列表里面没有出现 Broccoli，请手动添加并为其打勾。

<p align="center">
  <img src="https://i.imgur.com/Lyudory.png" width=440 />
</p>

6. 弹出控制 System Events 的弹窗，如下图所示，请允许。
	
<p align="center">
  	<img src="https://i.imgur.com/mpOMyhD.png" width=340 />
</p>

7. 第一次打开 Broccoli 后，桌面会显示如下窗口，同时 Menubar 内会出现 Broccoli 的图标（如果是有刘海的机型，请留意是否因刘海遮挡而无法显示）。

<p align="center">
  	<img src="https://i.imgur.com/P2VlOmj.png" width=240 />
    <img src="https://i.imgur.com/wC1ncFe.png" width=240 />
</p>

8. 关于更新：请在 GitHub 或者百度网盘上下载最新版的软件，然后以相同的方式拖入 Application 文件夹后覆盖原有文件。之后应重新打开 System Preferences，在 Accessibility（辅助功能）的部分，选中 Broccoli，点击减号，然后再点击加号，重新添加授权一次。之后回到软件内，重新配置 api key 和 session tokens 等。已经添加的语言和提示词会永久保存，不必担心，api 等信息将随软件被替换而重置。

## 使用说明

1. **软件界面说明**：如下图所示，展示了两种基本的界面布局及主要功能键。打开软件后第一次显示的界面即如下。其中 Send 按键有快捷键 cmd+return。

<p align="center">
  <img src="https://i.imgur.com/7DcH9sq.png" width=340 />
  <img src="https://i.imgur.com/LuIt0Wp.png" width=340 />
</p>

2. **配置密钥**：在设置窗口中**首先**选择自己需要的模型。
- GPT-3（使用 openai 模块，需要 API）

<p align="center">
  	<img src="https://i.imgur.com/XghIOs6.png" width=340 />
</p>

- ChatGPT（使用 openai 模块，需要 API。）
  同上。
- ChatGPT（使用 revChatGPT.V3 模块，需要 API。注：目前该库已暂停维护。）
  同上。
- ChatGPT（使用 httpx 模块，需要 API——同上，不再在下图中标出，支持自定义第三方服务和使用第三方的代理 API，如下图所示配置。）注意：在填写 endpoint 的时候，不要把诸如“/v1/chat/completions”的部分写上去，请只填写对应的地址即可，如“https://api.openai.com”、“https://oa.apiXXX.net”。我自己用的是 [API2D ](https://api2d.com)的第三方密钥。

<p align="center">
  <img src="https://i.imgur.com/LXMOdIA.png" width=340 />
</p>

- Poe （POE 模块，需要 Quora 的 Formkey 和 Poe 的 Cookies）（这一模型包含了 GPT-4、ChatGPT、Claude、Claude+ 等多个子模型，如有订阅 Poe 可方便调用，且可跨平台同步）
	- 关于 Formkey：先登录 Quora.com（得有个帐号），然后右键查看 Page Source（一般的浏览器都行），然后搜索“Formkey”，把查到的这一串密钥填入相应位置。
	- 关于 Cookies：登录 Quora.com，然后右键点击 Inspect，在上方选择 Cookie Editor，然后找到名为“m-b”的 Cookies，把这一串字符复制出来，在对应的文本框中，先填入“m-b=”，然后再将这一串字符粘贴于其后。

<p align="center">
  <img src="https://i.imgur.com/qmmhtvv.png" width=340 />
</p>
<p align="center">
  <img src="https://i.imgur.com/z5ioGrZ.png" width=340 />
</p>
<p align="center">
  <img src="https://i.imgur.com/FwLmEnD.png" width=340 />
</p>

- ChatGPT（revChatGPT.V1 模块，需要 session tokens。注：目前该库已暂停维护。）
  首先在浏览器里面登录 ChatGPT，然后点击界面上的按钮，用刚才登录的浏览器打开，找到 session tokens，把这一长串内容复制出来，填进左边的文本框内，保存即可。

<p align="center">
  <img src="https://i.imgur.com/T6RfQI9.png" width=340 />
</p>

<p align="center">
  <img src="https://i.imgur.com/j9UNF3C.png" width=340 />
</p>

- EdgeGPT（EdgeGPT 模块，需要导入 cookies.json）
  - 在 Edge 中登录 bing 帐号，然后下载[插件](https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm)。
  - 打开 bing.com。
  - 点击插件，选择“Export”，导出为“Export as JSON”。
  - 在设置界面内点击 Add cookies.json，选择刚才保存的文件即可。

<p align="center">
  <img src="https://i.imgur.com/8AFzBgO.png" width=340 />
</p>

3. **文本对话模式**：当在 menubar 的下拉菜单中选择了“Chat with a file”模式后，软件主界面将如下图所示。可以在设置界面内选择或取消“Show references when chatting with a file”。若选上，则在阅读长文本并给出回答后，Broccoli 将继续给出 AI 作答所依据的文段。界面上，三个按钮分别对应三种不同读取文本的方式，分别是从新文档导入、从文本框输入和打开已经处理过的旧文档。而从新文档导入可以读取 txt 和 word 文档，只需在文件选取器中选择对应的格式即可。

<p align="center">
  <img src="https://i.imgur.com/zaWDBNV.png" width=340 />
  <img src="https://i.imgur.com/kfl5QS2.png" width=340 />
</p>

4. **翻译、润色、总结等功能**：
   在主界面模式选项中可以选择多种内置功能，也可以选择并保存自己的提示词。
   
   如果在 Broccoli 的界面下可以使用 command+enter（回车键），相当于“send”按键的快捷方式。
   
   此外，如果需要从外部导入一大段话，例如翻译或者润色功能，当用户复制一段话之后，可以不用粘贴到文本框中再触发“send”，而是可以选择好模式后直接点击“send”，这意味着，当文本框为空时，Broccoli 会读取剪贴板，自动将剪贴板中的内容作为提示词。
   
   最后，在翻译、润色、总结、语法解释、代码解析模式中，Broccoli 在给出回答后都会将当前的答案复制到剪贴板里，这样设计将方便用户在如此情境下的使用，不必再回到软件中选中复制。

- Chat and ask：聊天、对话、与长文本对答。
- Command (AppleScript)：生成 AppleScript，并一键执行。
- Translate：用户可以选择在任意语言之间互译转换。预置三种语言，用户可以在设置页面内自行添加语言名称，并最好以源语形式，一行一个，保存刷新主界面，即可选择最新添加的语言。
- Polish：润色文本。用户可以选择润色为何种语言。
- Summarize：总结文段。用户可输入一段不超过字符限制（默认为 1024 tokens）的文段，请 AI 帮助总结为更短的文段，提炼大意和逻辑。更可以选择目标语言。
- Grammatically analyze：可以选择以目标语言解释一个句子或者文段。AI 将从一个语法老师的角度给出分析。
- Explain code：以自定义的目标语言解释输入的代码，并且反馈是否可能存在错误。
- Customize：自定义选项，包含所有用户在设置界面内填入保存的提示词。提示词将遵循一定的格式，以`---`为分隔，每组提示词包含名称和内容两个部分，各被囊括在一对`<|`和`|>`中。以下是一个样例。

```
<|名称 1|><|内容 1……|>
---
<|名称 2|><|内容 2……|>
```

5. **导入历史对话**：在 menubar 的下拉栏里面也可以选择“Open a chat history”，这样可以将之前导出的历史记录重新导入，继续之前的历史对话。（注：在使用不依赖 api 的模型时，因受其平台历史记录影响，可能无法准确记忆历史记录。）

## 注意事项

1. 更新之后请重新给软件赋予权限。
2. 更新之后请重新配置软件内的 api 等密钥。

## 证书信息

GPL-3.0 license

## 特别致谢

1. [Qt](https://github.com/qt)
2. [acheong08/ChatGPT](https://github.com/acheong08/ChatGPT)
3. [acheong08/EdgeGPT](https://github.com/acheong08/EdgeGPT)
4. [vaibhavk97/Poe](https://github.com/vaibhavk97/Poe)
5. [openai-translator/openai-translator](https://github.com/yetone/openai-translator)

## 支持作者

<p align="center">
  <img src="https://i.imgur.com/OHHJD4y.png" width=240 />
  <img src="https://i.imgur.com/6XiKMAK.png" width=240 />
</p>
