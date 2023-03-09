#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time

import revChatGPT.V1
from PyQt6.QtWidgets import (QWidget, QPushButton, QApplication,
                             QLabel, QHBoxLayout, QVBoxLayout,
                             QSystemTrayIcon, QMenu, QDialog,
                             QLineEdit, QTextEdit, QPlainTextEdit, QFileDialog, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
import PyQt6.QtGui
import codecs
import os
from pathlib import Path
import webbrowser
import openai
import markdown2
import datetime
from revChatGPT.V1 import Chatbot
from revChatGPT.V3 import Chatbot

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

# Create the icon
icon = QIcon("Broccolimen.icns")

# Create the tray
tray = QSystemTrayIcon()
tray.setIcon(icon)
tray.setVisible(True)

# Create the menu
menu = QMenu()

action3 = QAction("🥦 Start Broccoli!")
menu.addAction(action3)

action4 = QAction("⚙️ Settings")
menu.addAction(action4)

menu.addSeparator()

action2 = QAction("🆕 Check for Updates")
menu.addAction(action2)

action1 = QAction("ℹ️ About")
menu.addAction(action1)

menu.addSeparator()

# Add a Quit option to the menu.
quit = QAction("Quit")
quit.triggered.connect(app.quit)
menu.addAction(quit)

# Add the menu to the tray
tray.setContextMenu(menu)


class window_about(QWidget):  # 增加说明页面(About)
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):  # 说明页面内信息
        self.setUpMainWindow()
        self.resize(400, 380)
        self.center()
        self.setWindowTitle('About')
        self.setFocus()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    def setUpMainWindow(self):
        widg1 = QWidget()
        l1 = QLabel(self)
        png = PyQt6.QtGui.QPixmap('Broccolimen.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
        l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
        l1.setMaximumWidth(100)
        l1.setMaximumHeight(100)
        l1.setScaledContents(True)
        blay1 = QHBoxLayout()
        blay1.setContentsMargins(0, 0, 0, 0)
        blay1.addStretch()
        blay1.addWidget(l1)
        blay1.addStretch()
        widg1.setLayout(blay1)

        widg2 = QWidget()
        lbl0 = QLabel('Broccoli', self)
        font = PyQt6.QtGui.QFont()
        font.setFamily("Arial")
        font.setBold(True)
        font.setPointSize(20)
        lbl0.setFont(font)
        blay2 = QHBoxLayout()
        blay2.setContentsMargins(0, 0, 0, 0)
        blay2.addStretch()
        blay2.addWidget(lbl0)
        blay2.addStretch()
        widg2.setLayout(blay2)

        widg3 = QWidget()
        lbl1 = QLabel('Version 0.1.0', self)
        blay3 = QHBoxLayout()
        blay3.setContentsMargins(0, 0, 0, 0)
        blay3.addStretch()
        blay3.addWidget(lbl1)
        blay3.addStretch()
        widg3.setLayout(blay3)

        widg4 = QWidget()
        lbl2 = QLabel('This app is open-sourced.', self)
        blay4 = QHBoxLayout()
        blay4.setContentsMargins(0, 0, 0, 0)
        blay4.addStretch()
        blay4.addWidget(lbl2)
        blay4.addStretch()
        widg4.setLayout(blay4)

        widg5 = QWidget()
        lbl3 = QLabel('本软件开源。', self)
        blay5 = QHBoxLayout()
        blay5.setContentsMargins(0, 0, 0, 0)
        blay5.addStretch()
        blay5.addWidget(lbl3)
        blay5.addStretch()
        widg5.setLayout(blay5)

        widg6 = QWidget()
        lbl4 = QLabel('♥‿♥', self)
        blay6 = QHBoxLayout()
        blay6.setContentsMargins(0, 0, 0, 0)
        blay6.addStretch()
        blay6.addWidget(lbl4)
        blay6.addStretch()
        widg6.setLayout(blay6)

        widg7 = QWidget()
        lbl5 = QLabel('※\(^o^)/※', self)
        blay7 = QHBoxLayout()
        blay7.setContentsMargins(0, 0, 0, 0)
        blay7.addStretch()
        blay7.addWidget(lbl5)
        blay7.addStretch()
        widg7.setLayout(blay7)

        widg8 = QWidget()
        bt1 = QPushButton('The Author', self)
        bt1.setMaximumHeight(20)
        bt1.setMinimumWidth(100)
        bt1.clicked.connect(self.intro)
        bt2 = QPushButton('Github Page', self)
        bt2.setMaximumHeight(20)
        bt2.setMinimumWidth(100)
        bt2.clicked.connect(self.homepage)
        blay8 = QHBoxLayout()
        blay8.setContentsMargins(0, 0, 0, 0)
        blay8.addStretch()
        blay8.addWidget(bt1)
        blay8.addWidget(bt2)
        blay8.addStretch()
        widg8.setLayout(blay8)

        widg9 = QWidget()
        bt3 = QPushButton('🍪\n¥5', self)
        bt3.setMaximumHeight(50)
        bt3.setMinimumHeight(50)
        bt3.setMinimumWidth(50)
        bt3.clicked.connect(self.donate)
        bt4 = QPushButton('🥪\n¥10', self)
        bt4.setMaximumHeight(50)
        bt4.setMinimumHeight(50)
        bt4.setMinimumWidth(50)
        bt4.clicked.connect(self.donate2)
        bt5 = QPushButton('🍜\n¥20', self)
        bt5.setMaximumHeight(50)
        bt5.setMinimumHeight(50)
        bt5.setMinimumWidth(50)
        bt5.clicked.connect(self.donate3)
        bt6 = QPushButton('🍕\n¥50', self)
        bt6.setMaximumHeight(50)
        bt6.setMinimumHeight(50)
        bt6.setMinimumWidth(50)
        bt6.clicked.connect(self.donate4)
        blay9 = QHBoxLayout()
        blay9.setContentsMargins(0, 0, 0, 0)
        blay9.addStretch()
        blay9.addWidget(bt3)
        blay9.addWidget(bt4)
        blay9.addWidget(bt5)
        blay9.addWidget(bt6)
        blay9.addStretch()
        widg9.setLayout(blay9)

        widg10 = QWidget()
        lbl6 = QLabel('© 2023 Ryan-the-hito. All rights reserved.', self)
        blay10 = QHBoxLayout()
        blay10.setContentsMargins(0, 0, 0, 0)
        blay10.addStretch()
        blay10.addWidget(lbl6)
        blay10.addStretch()
        widg10.setLayout(blay10)

        main_h_box = QVBoxLayout()
        main_h_box.addWidget(widg1)
        main_h_box.addWidget(widg2)
        main_h_box.addWidget(widg3)
        main_h_box.addWidget(widg4)
        main_h_box.addWidget(widg5)
        main_h_box.addWidget(widg6)
        main_h_box.addWidget(widg7)
        main_h_box.addWidget(widg8)
        main_h_box.addWidget(widg9)
        main_h_box.addWidget(widg10)
        main_h_box.addStretch()
        self.setLayout(main_h_box)

    def intro(self):
        webbrowser.open('https://github.com/Ryan-the-hito/Ryan-the-hito')

    def homepage(self):
        webbrowser.open('https://github.com/Ryan-the-hito/Broccoli')

    def donate(self):
        dlg = CustomDialog()
        dlg.exec()

    def donate2(self):
        dlg = CustomDialog2()
        dlg.exec()

    def donate3(self):
        dlg = CustomDialog3()
        dlg.exec()

    def donate4(self):
        dlg = CustomDialog4()
        dlg.exec()

    def center(self):  # 设置窗口居中
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def activate(self):  # 设置窗口显示
        self.show()


class CustomDialog(QDialog):  # (About1)
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setUpMainWindow()
        self.setWindowTitle("Thank you for your support!")
        self.center()
        self.resize(400, 390)
        self.setFocus()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    def setUpMainWindow(self):
        widge_all = QWidget()
        l1 = QLabel(self)
        png = PyQt6.QtGui.QPixmap('wechat5.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
        l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
        l1.setMaximumSize(160, 240)
        l1.setScaledContents(True)
        l2 = QLabel(self)
        png = PyQt6.QtGui.QPixmap('alipay5.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
        l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
        l2.setMaximumSize(160, 240)
        l2.setScaledContents(True)
        bk = QHBoxLayout()
        bk.setContentsMargins(0, 0, 0, 0)
        bk.addWidget(l1)
        bk.addWidget(l2)
        widge_all.setLayout(bk)

        m1 = QLabel('Thank you for your kind support! 😊', self)
        m2 = QLabel('I will write more interesting apps! 🥳', self)

        widg_c = QWidget()
        bt1 = QPushButton('Thank you!', self)
        bt1.setMaximumHeight(20)
        bt1.setMinimumWidth(100)
        bt1.clicked.connect(self.cancel)
        bt2 = QPushButton('Donate later~', self)
        bt2.setMaximumHeight(20)
        bt2.setMinimumWidth(100)
        bt2.clicked.connect(self.cancel)
        blay8 = QHBoxLayout()
        blay8.setContentsMargins(0, 0, 0, 0)
        blay8.addStretch()
        blay8.addWidget(bt1)
        blay8.addWidget(bt2)
        blay8.addStretch()
        widg_c.setLayout(blay8)

        self.layout = QVBoxLayout()
        self.layout.addWidget(widge_all)
        self.layout.addWidget(m1)
        self.layout.addWidget(m2)
        self.layout.addStretch()
        self.layout.addWidget(widg_c)
        self.layout.addStretch()
        self.setLayout(self.layout)

    def center(self):  # 设置窗口居中
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def cancel(self):  # 设置取消键的功能
        self.close()


class CustomDialog2(QDialog):  # (About2)
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setUpMainWindow()
        self.setWindowTitle("Thank you for your support!")
        self.center()
        self.resize(400, 390)
        self.setFocus()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    def setUpMainWindow(self):
        widge_all = QWidget()
        l1 = QLabel(self)
        png = PyQt6.QtGui.QPixmap('wechat10.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
        l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
        l1.setMaximumSize(160, 240)
        l1.setScaledContents(True)
        l2 = QLabel(self)
        png = PyQt6.QtGui.QPixmap('alipay10.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
        l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
        l2.setMaximumSize(160, 240)
        l2.setScaledContents(True)
        bk = QHBoxLayout()
        bk.setContentsMargins(0, 0, 0, 0)
        bk.addWidget(l1)
        bk.addWidget(l2)
        widge_all.setLayout(bk)

        m1 = QLabel('Thank you for your kind support! 😊', self)
        m2 = QLabel('I will write more interesting apps! 🥳', self)

        widg_c = QWidget()
        bt1 = QPushButton('Thank you!', self)
        bt1.setMaximumHeight(20)
        bt1.setMinimumWidth(100)
        bt1.clicked.connect(self.cancel)
        bt2 = QPushButton('Donate later~', self)
        bt2.setMaximumHeight(20)
        bt2.setMinimumWidth(100)
        bt2.clicked.connect(self.cancel)
        blay8 = QHBoxLayout()
        blay8.setContentsMargins(0, 0, 0, 0)
        blay8.addStretch()
        blay8.addWidget(bt1)
        blay8.addWidget(bt2)
        blay8.addStretch()
        widg_c.setLayout(blay8)

        self.layout = QVBoxLayout()
        self.layout.addWidget(widge_all)
        self.layout.addWidget(m1)
        self.layout.addWidget(m2)
        self.layout.addStretch()
        self.layout.addWidget(widg_c)
        self.layout.addStretch()
        self.setLayout(self.layout)

    def center(self):  # 设置窗口居中
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def cancel(self):  # 设置取消键的功能
        self.close()


class CustomDialog3(QDialog):  # (About3)
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setUpMainWindow()
        self.setWindowTitle("Thank you for your support!")
        self.center()
        self.resize(400, 390)
        self.setFocus()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    def setUpMainWindow(self):
        widge_all = QWidget()
        l1 = QLabel(self)
        png = PyQt6.QtGui.QPixmap('wechat20.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
        l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
        l1.setMaximumSize(160, 240)
        l1.setScaledContents(True)
        l2 = QLabel(self)
        png = PyQt6.QtGui.QPixmap('alipay20.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
        l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
        l2.setMaximumSize(160, 240)
        l2.setScaledContents(True)
        bk = QHBoxLayout()
        bk.setContentsMargins(0, 0, 0, 0)
        bk.addWidget(l1)
        bk.addWidget(l2)
        widge_all.setLayout(bk)

        m1 = QLabel('Thank you for your kind support! 😊', self)
        m2 = QLabel('I will write more interesting apps! 🥳', self)

        widg_c = QWidget()
        bt1 = QPushButton('Thank you!', self)
        bt1.setMaximumHeight(20)
        bt1.setMinimumWidth(100)
        bt1.clicked.connect(self.cancel)
        bt2 = QPushButton('Donate later~', self)
        bt2.setMaximumHeight(20)
        bt2.setMinimumWidth(100)
        bt2.clicked.connect(self.cancel)
        blay8 = QHBoxLayout()
        blay8.setContentsMargins(0, 0, 0, 0)
        blay8.addStretch()
        blay8.addWidget(bt1)
        blay8.addWidget(bt2)
        blay8.addStretch()
        widg_c.setLayout(blay8)

        self.layout = QVBoxLayout()
        self.layout.addWidget(widge_all)
        self.layout.addWidget(m1)
        self.layout.addWidget(m2)
        self.layout.addStretch()
        self.layout.addWidget(widg_c)
        self.layout.addStretch()
        self.setLayout(self.layout)

    def center(self):  # 设置窗口居中
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def cancel(self):  # 设置取消键的功能
        self.close()


class CustomDialog4(QDialog):  # (About4)
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setUpMainWindow()
        self.setWindowTitle("Thank you for your support!")
        self.center()
        self.resize(400, 390)
        self.setFocus()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    def setUpMainWindow(self):
        widge_all = QWidget()
        l1 = QLabel(self)
        png = PyQt6.QtGui.QPixmap('wechat50.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
        l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
        l1.setMaximumSize(160, 240)
        l1.setScaledContents(True)
        l2 = QLabel(self)
        png = PyQt6.QtGui.QPixmap('alipay50.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
        l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
        l2.setMaximumSize(160, 240)
        l2.setScaledContents(True)
        bk = QHBoxLayout()
        bk.setContentsMargins(0, 0, 0, 0)
        bk.addWidget(l1)
        bk.addWidget(l2)
        widge_all.setLayout(bk)

        m1 = QLabel('Thank you for your kind support! 😊', self)
        m2 = QLabel('I will write more interesting apps! 🥳', self)

        widg_c = QWidget()
        bt1 = QPushButton('Thank you!', self)
        bt1.setMaximumHeight(20)
        bt1.setMinimumWidth(100)
        bt1.clicked.connect(self.cancel)
        bt2 = QPushButton('Donate later~', self)
        bt2.setMaximumHeight(20)
        bt2.setMinimumWidth(100)
        bt2.clicked.connect(self.cancel)
        blay8 = QHBoxLayout()
        blay8.setContentsMargins(0, 0, 0, 0)
        blay8.addStretch()
        blay8.addWidget(bt1)
        blay8.addWidget(bt2)
        blay8.addStretch()
        widg_c.setLayout(blay8)

        self.layout = QVBoxLayout()
        self.layout.addWidget(widge_all)
        self.layout.addWidget(m1)
        self.layout.addWidget(m2)
        self.layout.addStretch()
        self.layout.addWidget(widg_c)
        self.layout.addStretch()
        self.setLayout(self.layout)

    def center(self):  # 设置窗口居中
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def cancel(self):  # 设置取消键的功能
        self.close()


class window_update(QWidget):  # 增加更新页面（Check for Updates）
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):  # 说明页面内信息

        lbl = QLabel('Current Version: 0.1.0', self)
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


class MyWidget(QWidget):  # 主窗口
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.center()
        self.setWindowTitle('GPT bot')
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
        Which = codecs.open('which.txt', 'r', encoding='utf-8').read()
        if Which == '0':
            self.LastQ = str(self.text1.toPlainText())
            AccountGPT = codecs.open('api.txt', 'r', encoding='utf-8').read()
            if AccountGPT != '' and self.text1.toPlainText() != '':
                QApplication.processEvents()
                QApplication.restoreOverrideCursor()
                self.text1.setReadOnly(True)
                md = '- Q: ' + self.text1.toPlainText() + '\n\n'
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
                try:
                    openai.api_key = AccountGPT
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
                    message = message.replace('\n', '\n\n\t')
                    message = message.replace('\n\n\t\n\n\t', '\n\n\t')
                    message = '\n\t' + message
                    QApplication.processEvents()
                    QApplication.restoreOverrideCursor()

                    EndMess = '- A: ' + message + '\n\n---\n\n'
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
                        f1.write('\tError, please try again!' + '\n\n---\n\n')
                    AllText = codecs.open('output.txt', 'r', encoding='utf-8').read()
                    endhtml = self.md2html(AllText)
                    self.real1.setHtml(endhtml)
                    self.real1.ensureCursorVisible()  # 游标可用
                    cursor = self.real1.textCursor()  # 设置游标
                    pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    self.real1.setTextCursor(cursor)  # 滚动到游标位置
                    self.text1.setPlainText(self.LastQ)
                self.text1.setReadOnly(False)
            if AccountGPT == '':
                self.real1.setText('You should set your API in Settings.')
        if Which == '1':
            self.LastQ = str(self.text1.toPlainText())
            AccountGPT = codecs.open('account.txt', 'r', encoding='utf-8').read()
            PassGPT = codecs.open('pass.txt', 'r', encoding='utf-8').read()
            if AccountGPT != '' and PassGPT != '':
                QApplication.processEvents()
                QApplication.restoreOverrideCursor()
                self.text1.setReadOnly(True)
                md = '- Q: ' + self.text1.toPlainText() + '\n\n- A: '
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
                try:
                    prompt = str(self.text1.toPlainText())
                    chatbot = revChatGPT.V1.Chatbot(config={
                        "email": AccountGPT,
                        "password": PassGPT
                    })
                    prev_text = ""
                    for data in chatbot.ask(
                            prompt,
                    ):
                        message = data["message"][len(prev_text):]
                        prev_text = data["message"]
                        with open('output.txt', 'a', encoding='utf-8') as f1:
                            f1.write(message)
                        ProcessText = codecs.open('output.txt', 'r', encoding='utf-8').read()
                        midhtml = self.md2html(ProcessText)
                        self.real1.setHtml(midhtml)
                        self.real1.ensureCursorVisible()  # 游标可用
                        cursor = self.real1.textCursor()  # 设置游标
                        pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                        cursor.setPosition(pos)  # 游标位置设置为尾部
                        self.real1.setTextCursor(cursor)  # 滚动到游标位置
                        QApplication.processEvents()
                        QApplication.restoreOverrideCursor()

                    with open('output.txt', 'a', encoding='utf-8') as f1:
                        f1.write('\n\n')

                    TypeSet = codecs.open('output.txt', 'r', encoding='utf-8').read()
                    TypeSet = TypeSet.replace('- A: \n\t', '- A: ')
                    TypeSet = TypeSet.replace('- A: \n', '- A: ')
                    TypeSet = TypeSet.replace('- A: ', '- A: \n\t')
                    TypeSet = TypeSet.replace('\n', '\n\n\t')
                    TypeSet = TypeSet.replace('\n\n\t\n\n\t', '\n\n\t')
                    TypeSet = TypeSet.replace('\n\n\t\t', '\n\n\t')
                    TypeSet = TypeSet.replace('\n\n\t\n\n\t', '\n\n\t')
                    TypeSet = TypeSet.replace('- A: \n\n\t', '- A: \n\t')
                    TypeSet = TypeSet.replace('\t- A: ', '- A: ')
                    TypeSet = TypeSet.replace('\t- Q: ', '- Q: ')
                    TypeSet = TypeSet.replace('\t---', '---')
                    TypeSet = TypeSet.rstrip('\t')
                    TypeSet = TypeSet + '---\n\n'
                    with open('output.txt', 'w', encoding='utf-8') as f1:
                        f1.write(TypeSet)
                    endhtml = self.md2html(TypeSet)
                    self.real1.setHtml(endhtml)
                    self.real1.ensureCursorVisible()  # 游标可用
                    cursor = self.real1.textCursor()  # 设置游标
                    pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    self.real1.setTextCursor(cursor)  # 滚动到游标位置

                    self.text1.clear()
                except:
                    with open('output.txt', 'a', encoding='utf-8') as f1:
                        f1.write('Error, please try again!' + '\n\n---\n\n')
                    AllText = codecs.open('output.txt', 'r', encoding='utf-8').read()
                    endhtml = self.md2html(AllText)
                    self.real1.setHtml(endhtml)
                    self.real1.ensureCursorVisible()  # 游标可用
                    cursor = self.real1.textCursor()  # 设置游标
                    pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    self.real1.setTextCursor(cursor)  # 滚动到游标位置
                    self.text1.setPlainText(self.LastQ)
                self.text1.setReadOnly(False)
            if AccountGPT == '' or PassGPT == '':
                self.real1.setText('You should set your accounts in Settings.')
        if Which == '2':
            self.LastQ = str(self.text1.toPlainText())
            AccountGPT = codecs.open('api.txt', 'r', encoding='utf-8').read()
            if AccountGPT != '' and self.text1.toPlainText() != '':
                self.text1.setReadOnly(True)
                md = '- Q: ' + self.text1.toPlainText() + '\n\n'
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
                try:
                    EndMess = '- A: '
                    with open('output.txt', 'a', encoding='utf-8') as f1:
                        f1.write(EndMess)
                    chatbot = revChatGPT.V3.Chatbot(api_key=AccountGPT)
                    for data in chatbot.ask(str(self.text1.toPlainText())):
                        with open('output.txt', 'a', encoding='utf-8') as f1:
                            f1.write(data)
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
                    with open('output.txt', 'a', encoding='utf-8') as f1:
                        f1.write('\n\n')
                    AllText = codecs.open('output.txt', 'r', encoding='utf-8').read()
                    AllText = AllText.replace('- A: \n\t', '- A: ')
                    AllText = AllText.replace('- A: \n', '- A: ')
                    AllText = AllText.replace('- A: ', '- A: \n\t')
                    AllText = AllText.replace('\n', '\n\n\t')
                    AllText = AllText.replace('\n\n\t\n\n\t', '\n\n\t')
                    AllText = AllText.replace('\n\n\t\t', '\n\n\t')
                    AllText = AllText.replace('\n\n\t\n\n\t', '\n\n\t')
                    AllText = AllText.replace('- A: \n\n\t', '- A: \n\t')
                    AllText = AllText.replace('\t- A: ', '- A: ')
                    AllText = AllText.replace('\t- Q: ', '- Q: ')
                    AllText = AllText.replace('\t---', '---')
                    AllText = AllText.rstrip('\t')
                    AllText = AllText + '---\n\n'
                    with open('output.txt', 'w', encoding='utf-8') as f1:
                        f1.write(AllText)
                    endhtml = self.md2html(AllText)
                    self.real1.setHtml(endhtml)
                    self.real1.ensureCursorVisible()  # 游标可用
                    cursor = self.real1.textCursor()  # 设置游标
                    pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    self.real1.setTextCursor(cursor)  # 滚动到游标位置
                    self.text1.clear()
                except:
                    with open('output.txt', 'a', encoding='utf-8') as f1:
                        f1.write('\tError, please try again!' + '\n\n---\n\n')
                    AllText = codecs.open('output.txt', 'r', encoding='utf-8').read()
                    endhtml = self.md2html(AllText)
                    self.real1.setHtml(endhtml)
                    self.real1.ensureCursorVisible()  # 游标可用
                    cursor = self.real1.textCursor()  # 设置游标
                    pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    self.real1.setTextCursor(cursor)  # 滚动到游标位置
                    self.text1.setPlainText(self.LastQ)
                self.text1.setReadOnly(False)
            if AccountGPT == '':
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


class window4(QWidget):  # Customization settings
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):  # 设置窗口内布局
        self.setUpMainWindow()
        self.resize(350, 150)
        self.center()
        self.setWindowTitle('Customization settings')
        self.setFocus()

    def setUpMainWindow(self):
        self.widget1 = QComboBox(self)
        #self.widget1.setFixedWidth(70)
        self.widget1.setEditable(False)
        defalist = ['GPT-3 (API)', 'ChatGPT (web)', 'ChatGPT (API)']
        self.widget1.addItems(defalist)
        Which = codecs.open('which.txt', 'r', encoding='utf-8').read()
        if Which == '0':
            self.widget1.setCurrentIndex(0)
        if Which == '1':
            self.widget1.setCurrentIndex(1)
        if Which == '2':
            self.widget1.setCurrentIndex(2)
        self.widget1.currentIndexChanged.connect(self.IndexChange)

        self.le1 = QLineEdit(self)
        self.le1.setPlaceholderText('API here...')
        Apis = codecs.open('api.txt', 'r', encoding='utf-8').read()
        if Apis != '':
            self.le1.setText(Apis)

        self.le2 = QLineEdit(self)
        self.le2.setPlaceholderText('Account here...')
        AccountGPT = codecs.open('account.txt', 'r', encoding='utf-8').read()
        if AccountGPT != '':
            self.le2.setText(AccountGPT)

        self.le3 = QLineEdit(self)
        self.le3.setPlaceholderText('Password here...')
        PassGPT = codecs.open('pass.txt', 'r', encoding='utf-8').read()
        if PassGPT != '':
            self.le3.setText(PassGPT)

        btn_1 = QPushButton('Save', self)
        btn_1.clicked.connect(self.SaveAPI)
        btn_1.setFixedSize(80, 20)

        qw2 = QWidget()
        vbox2 = QHBoxLayout()
        vbox2.setContentsMargins(0, 0, 0, 0)
        vbox2.addStretch()
        vbox2.addWidget(btn_1)
        vbox2.addStretch()
        qw2.setLayout(vbox2)

        vbox1 = QVBoxLayout()
        vbox1.setContentsMargins(20, 20, 20, 20)
        vbox1.addWidget(self.widget1)
        vbox1.addWidget(self.le1)
        vbox1.addWidget(self.le2)
        vbox1.addWidget(self.le3)
        vbox1.addWidget(qw2)
        self.setLayout(vbox1)

    def IndexChange(self, i):
        if i == 0:
            with open('which.txt', 'w', encoding='utf-8') as f0:
                f0.write('0')
        if i == 1:
            with open('which.txt', 'w', encoding='utf-8') as f0:
                f0.write('1')
        if i == 2:
            with open('which.txt', 'w', encoding='utf-8') as f0:
                f0.write('2')

    def SaveAPI(self):
        with open('api.txt', 'w', encoding='utf-8') as f1:
            f1.write(self.le1.text())
        with open('account.txt', 'w', encoding='utf-8') as f1:
            f1.write(self.le2.text())
        with open('pass.txt', 'w', encoding='utf-8') as f1:
            f1.write(self.le3.text())
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


style_sheet_ori = '''
    QTabWidget::pane {
        border: 1px solid #ECECEC;
        background: #ECECEC;
        border-radius: 9px;
}
    QPushButton{
        border: 1px outset grey;
        background-color: #FFFFFF;
        border-radius: 4px;
        padding: 1px;
        color: #000000
}
    QPushButton:pressed{
        border: 1px outset grey;
        background-color: #0085FF;
        border-radius: 4px;
        padding: 1px;
        color: #FFFFFF
}
    QPlainTextEdit{
        border: 1px solid grey;  
        border-radius:4px;
        padding: 1px 5px 1px 3px; 
        background-clip: border;
        background-color: #F3F2EE;
        color: #000000;
        font: 14pt Times New Roman;
}
    QPlainTextEdit#edit{
        border: 1px solid grey;  
        border-radius:4px;
        padding: 1px 5px 1px 3px; 
        background-clip: border;
        background-color: #FFFFFF;
        color: rgb(113, 113, 113);
        font: 14pt Helvetica;
}
    QLineEdit{
        border-radius:4px;
        border: 1px solid gray;
        background-color: #FFFFFF;
}
    QTextEdit{
        border: 1px solid grey;  
        border-radius:4px;
        padding: 1px 5px 1px 3px; 
        background-clip: border;
        background-color: #F3F2EE;
        color: #000000;
        font: 14pt Times New Roman;
}
'''


if __name__ == '__main__':
    w1 = window_about()  # about
    w2 = window_update()  # update
    w3 = MyWidget()
    w4 = window4()
    action1.triggered.connect(w1.activate)
    action2.triggered.connect(w2.activate)
    action3.triggered.connect(w3.activate)
    action4.triggered.connect(w4.activate)
    #action5.triggered.connect(w4.onrunstart)
    app.setStyleSheet(style_sheet_ori)
    app.exec()