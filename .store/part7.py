class window_update(QWidget):  # 增加更新页面（Check for Updates）
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):  # 说明页面内信息

        lbl = QLabel('Current Version: 0.0.3', self)
        lbl.move(110, 75)

        lbl0 = QLabel('Check Now:', self)
        lbl0.move(30, 20)

        bt1 = QPushButton('Check Github', self)
        bt1.clicked.connect(self.upd)
        bt1.move(110, 15)

        bt2 = QPushButton('Check Baidu Net Disk', self)
        bt2.clicked.connect(self.upd2)
        bt2.move(110, 45)

        self.resize(300, 110)
        self.center()
        self.setWindowTitle('Check for Updates')
        self.setFocus()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    def upd(self):
        webbrowser.open('https://github.com/Ryan-the-hito/Broccoli/releases')

    def upd2(self):
        webbrowser.open('https://pan.baidu.com/s/1HW0l2ivw5R0byrnauQKeFw?pwd=628n')

    def center(self):  # 设置窗口居中
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def activate(self):  # 设置窗口显示
        self.show()