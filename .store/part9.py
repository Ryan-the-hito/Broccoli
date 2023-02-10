class window4(QWidget):  # Customization settings
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):  # 设置窗口内布局
        self.setUpMainWindow()
        self.resize(350, 50)
        self.center()
        self.setWindowTitle('Customization settings')
        self.setFocus()

    def setUpMainWindow(self):
        self.le1 = QLineEdit(self)
        self.le1.setPlaceholderText('API here...')
        Apis = codecs.open('api.txt', 'r', encoding='utf-8').read()
        if Apis != '':
            self.le1.setText(Apis)

        btn_1 = QPushButton('Save', self)
        btn_1.clicked.connect(self.SaveAPI)
        btn_1.setFixedSize(80, 20)

        vbox1 = QHBoxLayout()
        vbox1.setContentsMargins(20, 20, 20, 20)
        vbox1.addWidget(self.le1)
        vbox1.addWidget(btn_1)
        self.setLayout(vbox1)

    def SaveAPI(self):
        with open('api.txt', 'w', encoding='utf-8') as f1:
            f1.write(self.le1.text())
        self.close()

    def center(self):  # 设置窗口居中
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def keyPressEvent(self, e):  # 当页面显示的时候，按下esc键可关闭窗口
        if e.key() == Qt.Key.Key_Escape.value:
            self.close()

    def activate(self):  # 设置窗口显示
        self.show()
        self.setFocus()
        self.raise_()
        self.activateWindow()

    def cancel(self):  # 设置取消键的功能
        self.close()