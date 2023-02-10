class MyWidget(QWidget):  # 主窗口
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.center()
        self.setWindowTitle('GPT-3 bot')
        self.setFixedSize(500, 810)

        self.real1 = QTextEdit(self)
        self.real1.setReadOnly(True)
        self.real1.setFixedSize(460, 660)

        self.text1 = QPlainTextEdit(self)
        self.text1.setReadOnly(False)
        self.text1.setObjectName('edit')
        self.text1.setFixedSize(360, 100)
        self.text1.setPlaceholderText('Your prompts here...')

        btn_sub1 = QPushButton('🔺 Send', self)
        btn_sub1.clicked.connect(self.SendX)
        btn_sub1.setFixedSize(80, 20)
        btn_sub1.setShortcut("Ctrl+Return")

        btn_sub2 = QPushButton('🔸 Clear', self)
        btn_sub2.clicked.connect(self.ClearX)
        btn_sub2.setFixedSize(80, 20)

        btn_sub3 = QPushButton('🔻 Save', self)
        btn_sub3.clicked.connect(self.ExportX)
        btn_sub3.setFixedSize(80, 20)

        qw1 = QWidget()
        vbox1 = QVBoxLayout()
        vbox1.setContentsMargins(0, 0, 0, 0)
        vbox1.addStretch()
        vbox1.addWidget(btn_sub1)
        vbox1.addWidget(btn_sub2)
        vbox1.addWidget(btn_sub3)
        vbox1.addStretch()
        qw1.setLayout(vbox1)

        qw2 = QWidget()
        vbox2 = QHBoxLayout()
        vbox2.setContentsMargins(0, 0, 0, 0)
        vbox2.addWidget(self.text1)
        vbox2.addStretch()
        vbox2.addWidget(qw1)
        qw2.setLayout(vbox2)

        vbox3 = QVBoxLayout()
        vbox3.setContentsMargins(20, 20, 20, 20)
        vbox3.addStretch()
        vbox3.addWidget(self.real1)
        vbox3.addWidget(qw2)
        vbox3.addStretch()
        self.setLayout(vbox3)

    def SendX(self):
        self.LastQ = str(self.text1.toPlainText())
        Apis = codecs.open('api.txt', 'r', encoding='utf-8').read()
        if Apis != '' and self.text1.toPlainText() != '':
            try:
                QApplication.processEvents()
                QApplication.restoreOverrideCursor()
                self.text1.setReadOnly(True)
                md = '- Q: ' + self.text1.toPlainText() + '\n'
                with open('output.txt', 'a', encoding='utf-8') as f1:
                    f1.write(md)
                PromText = codecs.open('output.txt', 'r', encoding='utf-8').read()
                newhtml = self.md2html(PromText)
                self.real1.setHtml(newhtml)
                self.real1.ensureCursorVisible()  # 游标可用
                cursor = self.real1.textCursor()  # 设置游标
                pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                cursor.setPosition(pos)  # 游标位置设置为尾部
                self.real1.setTextCursor(cursor)  # 滚动到游标位置
                QApplication.processEvents()
                QApplication.restoreOverrideCursor()

                openai.api_key = Apis
                # Generate text with GPT-3
                model_engine = "text-davinci-003"
                prompt = str(self.text1.toPlainText())
                QApplication.processEvents()
                QApplication.restoreOverrideCursor()
                completions = openai.Completion.create(
                    engine=model_engine,
                    prompt=prompt,
                    max_tokens=1024,
                    n=1,
                    stop=None,
                    temperature=0.5,
                )
                QApplication.processEvents()
                QApplication.restoreOverrideCursor()
                message = completions.choices[0].text
                message = message.lstrip('\n')
                message = message.replace('\n', '\n\t')
                message = message.replace('\n\t\n', '\n\n')
                message = '\n\t' + message
                QApplication.processEvents()
                QApplication.restoreOverrideCursor()

                EndMess = '- A: ' + message + '\n'
                with open('output.txt', 'a', encoding='utf-8') as f1:
                    f1.write(EndMess)
                AllText = codecs.open('output.txt', 'r', encoding='utf-8').read()
                endhtml = self.md2html(AllText)
                self.real1.setHtml(endhtml)
                self.real1.ensureCursorVisible()  # 游标可用
                cursor = self.real1.textCursor()  # 设置游标
                pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                cursor.setPosition(pos)  # 游标位置设置为尾部
                self.real1.setTextCursor(cursor)  # 滚动到游标位置
                QApplication.processEvents()
                QApplication.restoreOverrideCursor()
                self.text1.clear()
            except:
                with open('output.txt', 'a', encoding='utf-8') as f1:
                    f1.write('Error, please try again!' + '\n')
                AllText = codecs.open('output.txt', 'r', encoding='utf-8').read()
                endhtml = self.md2html(AllText)
                self.real1.setHtml(endhtml)
                self.text1.setPlainText(self.LastQ)
            self.text1.setReadOnly(False)
        if Apis == '':
            self.real1.setText('You should set your API in Settings.')

    def ClearX(self):
        self.text1.clear()
        self.text1.setReadOnly(False)
        self.real1.clear()
        with open('output.txt', 'w', encoding='utf-8') as f1:
            f1.write('')

    def ExportX(self):
        home_dir = str(Path.home())
        fj = QFileDialog.getExistingDirectory(self, 'Open', home_dir)
        if fj != '':
            ConText = codecs.open('output.txt', 'r', encoding='utf-8').read()
            ISOTIMEFORMAT = '%Y%m%d %H-%M-%S-%f'
            theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
            tarname = theTime + " GPToutput.md"
            fulldir = os.path.join(fj, tarname)
            with open(fulldir, 'w', encoding='utf-8') as f1:
                f1.write(ConText)

    def md2html(self, mdstr):
        extras = ['code-friendly', 'fenced-code-blocks', 'footnotes', 'tables', 'code-color', 'pyshell', 'nofollow',
                  'cuddled-lists', 'header ids', 'nofollow']

        html = """
        <html>
        <head>
        <meta content="text/html; charset=utf-8" http-equiv="content-type" />
        <style>
            .hll { background-color: #ffffcc }
            .c { color: #0099FF; font-style: italic } /* Comment */
            .err { color: #AA0000; background-color: #FFAAAA } /* Error */
            .k { color: #006699; font-weight: bold } /* Keyword */
            .o { color: #555555 } /* Operator */
            .ch { color: #0099FF; font-style: italic } /* Comment.Hashbang */
            .cm { color: #0099FF; font-style: italic } /* Comment.Multiline */
            .cp { color: #009999 } /* Comment.Preproc */
            .cpf { color: #0099FF; font-style: italic } /* Comment.PreprocFile */
            .c1 { color: #0099FF; font-style: italic } /* Comment.Single */
            .cs { color: #0099FF; font-weight: bold; font-style: italic } /* Comment.Special */
            .gd { background-color: #FFCCCC; border: 1px solid #CC0000 } /* Generic.Deleted */
            .ge { font-style: italic } /* Generic.Emph */
            .gr { color: #FF0000 } /* Generic.Error */
            .gh { color: #003300; font-weight: bold } /* Generic.Heading */
            .gi { background-color: #CCFFCC; border: 1px solid #00CC00 } /* Generic.Inserted */
            .go { color: #AAAAAA } /* Generic.Output */
            .gp { color: #000099; font-weight: bold } /* Generic.Prompt */
            .gs { font-weight: bold } /* Generic.Strong */
            .gu { color: #003300; font-weight: bold } /* Generic.Subheading */
            .gt { color: #99CC66 } /* Generic.Traceback */
            .kc { color: #006699; font-weight: bold } /* Keyword.Constant */
            .kd { color: #006699; font-weight: bold } /* Keyword.Declaration */
            .kn { color: #006699; font-weight: bold } /* Keyword.Namespace */
            .kp { color: #006699 } /* Keyword.Pseudo */
            .kr { color: #006699; font-weight: bold } /* Keyword.Reserved */
            .kt { color: #007788; font-weight: bold } /* Keyword.Type */
            .m { color: #FF6600 } /* Literal.Number */
            .s { color: #CC3300 } /* Literal.String */
            .na { color: #330099 } /* Name.Attribute */
            .nb { color: #336666 } /* Name.Builtin */
            .nc { color: #00AA88; font-weight: bold } /* Name.Class */
            .no { color: #336600 } /* Name.Constant */
            .nd { color: #9999FF } /* Name.Decorator */
            .ni { color: #999999; font-weight: bold } /* Name.Entity */
            .ne { color: #CC0000; font-weight: bold } /* Name.Exception */
            .nf { color: #CC00FF } /* Name.Function */
            .nl { color: #9999FF } /* Name.Label */
            .nn { color: #00CCFF; font-weight: bold } /* Name.Namespace */
            .nt { color: #330099; font-weight: bold } /* Name.Tag */
            .nv { color: #003333 } /* Name.Variable */
            .ow { color: #000000; font-weight: bold } /* Operator.Word */
            .w { color: #bbbbbb } /* Text.Whitespace */
            .mb { color: #FF6600 } /* Literal.Number.Bin */
            .mf { color: #FF6600 } /* Literal.Number.Float */
            .mh { color: #FF6600 } /* Literal.Number.Hex */
            .mi { color: #FF6600 } /* Literal.Number.Integer */
            .mo { color: #FF6600 } /* Literal.Number.Oct */
            .sa { color: #CC3300 } /* Literal.String.Affix */
            .sb { color: #CC3300 } /* Literal.String.Backtick */
            .sc { color: #CC3300 } /* Literal.String.Char */
            .dl { color: #CC3300 } /* Literal.String.Delimiter */
            .sd { color: #CC3300; font-style: italic } /* Literal.String.Doc */
            .s2 { color: #CC3300 } /* Literal.String.Double */
            .se { color: #CC3300; font-weight: bold } /* Literal.String.Escape */
            .sh { color: #CC3300 } /* Literal.String.Heredoc */
            .si { color: #AA0000 } /* Literal.String.Interpol */
            .sx { color: #CC3300 } /* Literal.String.Other */
            .sr { color: #33AAAA } /* Literal.String.Regex */
            .s1 { color: #CC3300 } /* Literal.String.Single */
            .ss { color: #FFCC33 } /* Literal.String.Symbol */
            .bp { color: #336666 } /* Name.Builtin.Pseudo */
            .fm { color: #CC00FF } /* Name.Function.Magic */
            .vc { color: #003333 } /* Name.Variable.Class */
            .vg { color: #003333 } /* Name.Variable.Global */
            .vi { color: #003333 } /* Name.Variable.Instance */
            .vm { color: #003333 } /* Name.Variable.Magic */
            .il { color: #FF6600 } /* Literal.Number.Integer.Long */
            table {
                    font-family: verdana,arial,sans-serif;
                    font-size:11px;
                    color:#333333;
                    border-width: 1px;
                    border-color: #999999;
                    border-collapse: collapse;
                    }
            th {
                background:#b5cfd2 url('cell-blue.jpg');
                border-width: 1px;
                padding: 8px;
                border-style: solid;
                border-color: #999999;
                }
            td {
                background:#dcddc0 url('cell-grey.jpg');
                border-width: 1px;
                padding: 8px;
                border-style: solid;
                border-color: #999999;
                }
        </style>
        </head>
        <body>
            %s
        </body>
        </html>
        """
        ret = markdown2.markdown(mdstr, extras=extras)
        return html % ret

    def center(self):  # 设置窗口居中
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def keyPressEvent(self, e):  # 当页面显示的时候，按下esc键可关闭窗口
        if e.key() == Qt.Key.Key_Escape.value:
            self.close()

    def activate(self):  # 设置窗口显示
        with open('output.txt', 'w', encoding='utf-8') as f1:
            f1.write('')
        self.show()
        self.setFocus()
        self.raise_()
        self.activateWindow()

    def cancel(self):  # 设置取消键的功能
        self.close()