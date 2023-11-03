#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt6.QtWidgets import (QWidget, QPushButton, QApplication,
                             QLabel, QHBoxLayout, QVBoxLayout,
                             QSystemTrayIcon, QMenu, QDialog,
                             QLineEdit, QTextEdit, QPlainTextEdit, QFileDialog, QComboBox, QMenuBar, QFrame, QCheckBox)
from PyQt6.QtCore import Qt, QRect, QPropertyAnimation
from PyQt6.QtGui import QAction, QIcon, QColor
import PyQt6.QtGui
import codecs
import os
from pathlib import Path
import webbrowser
import openai
import markdown2
import datetime
import re
import subprocess
import signal
import httpx
import asyncio
import json
import jieba
from transformers import GPT2Tokenizer
import csv
import numpy as np
import pandas as pd
import time
import docx2txt
import requests
import pyautogui
from bs4 import BeautifulSoup
import html2text
import urllib3
import logging

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

BasePath = '/Applications/Broccoli.app/Contents/Resources/'
# BasePath = '' # test

# Create the icon
icon = QIcon("/Applications/Broccoli.app/Contents/Resources/Broccolimen.icns")

# Create the tray
tray = QSystemTrayIcon()
tray.setIcon(icon)
tray.setVisible(True)

# Create the menu
menu = QMenu()

action3 = QAction("🥦 Start Broccoli!")
menu.addAction(action3)

action5 = QAction("🖇️️ Open a chat history")
menu.addAction(action5)

action6 = QAction("📂️ Chat with a file")
action6.setCheckable(True)
menu.addAction(action6)

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

# create a system menu
btna4 = QAction("&Pin!")
btna4.setCheckable(True)
btna5 = QAction("&Ask!")
sysmenu = QMenuBar()
file_menu = sysmenu.addMenu("&Actions")
file_menu.addAction(btna4)
file_menu.addAction(btna5)


class window_about(QWidget):  # 增加说明页面(About)
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):  # 说明页面内信息
        self.setUpMainWindow()
        self.resize(400, 410)
        self.center()
        self.setWindowTitle('About')
        self.setFocus()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    def setUpMainWindow(self):
        widg1 = QWidget()
        l1 = QLabel(self)
        png = PyQt6.QtGui.QPixmap('/Applications/Broccoli.app/Contents/Resources/Broccolimen.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
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
        lbl1 = QLabel('Version 1.1.5', self)
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
        lbl3 = QLabel('本软件开源，感谢您的喜爱！', self)
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

        bt7 = QPushButton('Buy me a cup of coffee☕', self)
        bt7.setMaximumHeight(20)
        bt7.setMinimumWidth(215)
        bt7.clicked.connect(self.coffee)

        widg8_5 = QWidget()
        blay8_5 = QHBoxLayout()
        blay8_5.setContentsMargins(0, 0, 0, 0)
        blay8_5.addStretch()
        blay8_5.addWidget(bt7)
        blay8_5.addStretch()
        widg8_5.setLayout(blay8_5)

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
        main_h_box.addWidget(widg8_5)
        main_h_box.addWidget(widg9)
        main_h_box.addWidget(widg10)
        main_h_box.addStretch()
        self.setLayout(main_h_box)

    def intro(self):
        webbrowser.open('https://github.com/Ryan-the-hito/Ryan-the-hito')

    def homepage(self):
        webbrowser.open('https://github.com/Ryan-the-hito/Broccoli')

    def coffee(self):
        webbrowser.open('https://www.buymeacoffee.com/ryanthehito')

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
        png = PyQt6.QtGui.QPixmap('/Applications/Broccoli.app/Contents/Resources/wechat5.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
        l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
        l1.setMaximumSize(160, 240)
        l1.setScaledContents(True)
        l2 = QLabel(self)
        png = PyQt6.QtGui.QPixmap('/Applications/Broccoli.app/Contents/Resources/alipay5.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
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
        bt2 = QPushButton('Neither one above? Buy me a coffee~', self)
        bt2.setMaximumHeight(20)
        bt2.setMinimumWidth(260)
        bt2.clicked.connect(self.coffee)
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

    def coffee(self):
        webbrowser.open('https://www.buymeacoffee.com/ryanthehito')

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
        png = PyQt6.QtGui.QPixmap('/Applications/Broccoli.app/Contents/Resources/wechat10.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
        l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
        l1.setMaximumSize(160, 240)
        l1.setScaledContents(True)
        l2 = QLabel(self)
        png = PyQt6.QtGui.QPixmap('/Applications/Broccoli.app/Contents/Resources/alipay10.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
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
        bt2 = QPushButton('Neither one above? Buy me a coffee~', self)
        bt2.setMaximumHeight(20)
        bt2.setMinimumWidth(260)
        bt2.clicked.connect(self.coffee)
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

    def coffee(self):
        webbrowser.open('https://www.buymeacoffee.com/ryanthehito')

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
        png = PyQt6.QtGui.QPixmap('/Applications/Broccoli.app/Contents/Resources/wechat20.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
        l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
        l1.setMaximumSize(160, 240)
        l1.setScaledContents(True)
        l2 = QLabel(self)
        png = PyQt6.QtGui.QPixmap('/Applications/Broccoli.app/Contents/Resources/alipay20.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
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
        bt2 = QPushButton('Neither one above? Buy me a coffee~', self)
        bt2.setMaximumHeight(20)
        bt2.setMinimumWidth(260)
        bt2.clicked.connect(self.coffee)
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

    def coffee(self):
        webbrowser.open('https://www.buymeacoffee.com/ryanthehito')

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
        png = PyQt6.QtGui.QPixmap('/Applications/Broccoli.app/Contents/Resources/wechat50.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
        l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
        l1.setMaximumSize(160, 240)
        l1.setScaledContents(True)
        l2 = QLabel(self)
        png = PyQt6.QtGui.QPixmap('/Applications/Broccoli.app/Contents/Resources/alipay50.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
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
        bt2 = QPushButton('Neither one above? Buy me a coffee~', self)
        bt2.setMaximumHeight(20)
        bt2.setMinimumWidth(260)
        bt2.clicked.connect(self.coffee)
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

    def coffee(self):
        webbrowser.open('https://www.buymeacoffee.com/ryanthehito')

    def cancel(self):  # 设置取消键的功能
        self.close()


class window_update(QWidget):  # 增加更新页面（Check for Updates）
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):  # 说明页面内信息

        self.lbl = QLabel('Current Version: v1.1.5', self)
        self.lbl.move(30, 45)

        lbl0 = QLabel('Download Update:', self)
        lbl0.move(30, 75)

        lbl1 = QLabel('Latest Version:', self)
        lbl1.move(30, 15)

        self.lbl2 = QLabel('', self)
        self.lbl2.move(122, 15)

        bt1 = QPushButton('Github', self)
        bt1.setFixedWidth(120)
        bt1.clicked.connect(self.upd)
        bt1.move(150, 75)

        bt2 = QPushButton('Baidu Net Disk', self)
        bt2.setFixedWidth(120)
        bt2.clicked.connect(self.upd2)
        bt2.move(150, 105)

        self.resize(300, 150)
        self.center()
        self.setWindowTitle('Broccoli Updates')
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
        self.checkupdate()

    def checkupdate(self):
        targetURL = 'https://github.com/Ryan-the-hito/Broccoli/releases'
        try:
            # Fetch the HTML content from the URL
            urllib3.disable_warnings()
            logging.captureWarnings(True)
            s = requests.session()
            s.keep_alive = False  # 关闭多余连接
            response = s.get(targetURL, verify=False)
            response.encoding = 'utf-8'
            html_content = response.text
            # Parse the HTML using BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")
            # Remove all images from the parsed HTML
            for img in soup.find_all("img"):
                img.decompose()
            # Convert the parsed HTML to plain text using html2text
            text_maker = html2text.HTML2Text()
            text_maker.ignore_links = True
            text_maker.ignore_images = True
            plain_text = text_maker.handle(str(soup))
            # Convert the plain text to UTF-8
            plain_text_utf8 = plain_text.encode(response.encoding).decode("utf-8")

            for i in range(10):
                plain_text_utf8 = plain_text_utf8.replace('\n\n\n\n', '\n\n')
                plain_text_utf8 = plain_text_utf8.replace('\n\n\n', '\n\n')
                plain_text_utf8 = plain_text_utf8.replace('   ', ' ')
                plain_text_utf8 = plain_text_utf8.replace('  ', ' ')

            pattern2 = re.compile(r'(v\d+\.\d+\.\d+)\sLatest')
            result = pattern2.findall(plain_text_utf8)
            result = ''.join(result)
            nowversion = self.lbl.text().replace('Current Version: ', '')
            if result == nowversion:
                alertupdate = result + '. You are up to date!'
                self.lbl2.setText(alertupdate)
                self.lbl2.adjustSize()
            else:
                alertupdate = result + ' is ready!'
                self.lbl2.setText(alertupdate)
                self.lbl2.adjustSize()
        except:
            alertupdate = 'No Intrenet'
            self.lbl2.setText(alertupdate)
            self.lbl2.adjustSize()


class TimeoutException(Exception):
    pass


class MyWidget(QWidget):  # 主窗口
    def __init__(self):
        super().__init__()
        self.initUI()
        self.dragPosition = None

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(500, 830)

        home_dir = str(Path.home())
        tarname1 = "BroccoliAppPath"
        self.fulldir1 = os.path.join(home_dir, tarname1)
        if not os.path.exists(self.fulldir1):
            os.mkdir(self.fulldir1)

        tarname4 = "Local"
        self.Local = os.path.join(self.fulldir1, tarname4)
        if not os.path.exists(self.Local):
            os.mkdir(self.Local)

        tarname5 = "Index"
        self.Index = os.path.join(self.fulldir1, tarname5)
        if not os.path.exists(self.Index):
            os.mkdir(self.Index)

        tarname7 = "Embed"
        self.Embed = os.path.join(self.fulldir1, tarname7)
        if not os.path.exists(self.Embed):
            os.mkdir(self.Embed)

        tarname3 = "lang.txt"
        fulldir3 = os.path.join(self.fulldir1, tarname3)
        if not os.path.exists(fulldir3):
            with open(fulldir3, 'a', encoding='utf-8') as f0:
                f0.write('')

        tarname4 = "model.txt"
        fulldir4 = os.path.join(self.fulldir1, tarname4)
        if not os.path.exists(fulldir4):
            with open(fulldir4, 'a', encoding='utf-8') as f0:
                f0.write('')

        self.btn_00 = QPushButton('', self)
        self.btn_00.clicked.connect(self.pin_a_tab)
        self.btn_00.setFixedHeight(10)
        self.btn_00.setFixedWidth(500)
        self.i = 1

        self.real1 = QTextEdit(self)
        self.real1.setReadOnly(True)
        self.real1.setFixedSize(460, 630)

        self.text1 = QPlainTextEdit(self)
        self.text1.setReadOnly(False)
        self.text1.setObjectName('edit')
        self.text1.setFixedSize(360, 85)
        self.text1.setPlaceholderText('Your prompts here...')

        self.btn_sub1 = QPushButton('🔺 Send', self)
        self.btn_sub1.clicked.connect(self.SendX)
        self.btn_sub1.setFixedSize(80, 20)
        self.btn_sub1.setShortcut("Ctrl+Return")

        self.btn_sub4 = QPushButton('🔹 Again', self)
        self.btn_sub4.clicked.connect(self.AgainX)
        self.btn_sub4.setFixedSize(80, 20)

        btn_sub2 = QPushButton('🔸 Clear', self)
        btn_sub2.clicked.connect(self.ClearX)
        btn_sub2.setFixedSize(80, 20)

        btn_sub3 = QPushButton('🔻 Save', self)
        btn_sub3.clicked.connect(self.ExportX)
        btn_sub3.setFixedSize(80, 20)

        self.widget0 = QComboBox(self)
        self.widget0.setCurrentIndex(0)
        self.widget0.addItems(['Chat and ask', 'Command (AppleScript)', 'Translate', 'Polish', 'Summarize', 'Grammatically analyze', 'Explain code', 'Customize'])
        self.widget0.currentIndexChanged.connect(self.ModeX)
        self.widget0.setMaximumWidth(370)

        self.widget1 = QComboBox(self)
        self.widget1.setCurrentIndex(0)
        langs = codecs.open(fulldir3, 'r', encoding='utf-8').read()
        fulllanglist = []
        langs_list = ['English', '中文', '日本語']
        if langs != '':
            langs_list = langs.split('\n')
            while '' in langs_list:
                langs_list.remove('')
            for i in range(len(langs_list)):
                fulllanglist.append(langs_list[i])
        if langs == '':
            for i in range(len(langs_list)):
                fulllanglist.append(langs_list[i])
        self.widget1.addItems(langs_list)
        self.widget1.setVisible(False)
        self.widget1.currentIndexChanged.connect(self.TranslateX)

        self.lbl1 = QLabel('▶', self)
        self.lbl1.setVisible(False)

        self.widget2 = QComboBox(self)
        self.widget2.setCurrentIndex(0)
        currentlang = self.widget1.currentText()
        while currentlang in langs_list:
            langs_list.remove(currentlang)
        self.widget2.addItems(langs_list)
        self.widget2.setVisible(False)

        self.widget3 = QComboBox(self)
        self.widget3.setCurrentIndex(0)
        self.widget3.addItems(['Context: None', 'Banana', 'Strawberry', 'Orange', 'All'])
        self.widget3.setVisible(False)  # cancel this setting at the end.

        self.widget4 = QComboBox(self)
        self.widget4.setCurrentIndex(0)
        self.widget4.addItems(fulllanglist)
        self.widget4.setVisible(False)
        self.widget4.setFixedWidth(170)

        self.widget5 = QComboBox(self)
        self.widget5.setCurrentIndex(0)
        home_dir = str(Path.home())
        tarname1 = "BroccoliAppPath"
        fulldir1 = os.path.join(home_dir, tarname1)
        if not os.path.exists(fulldir1):
            os.mkdir(fulldir1)
        tarname2 = "CustomPrompt.txt"
        fulldir2 = os.path.join(fulldir1, tarname2)
        if not os.path.exists(fulldir2):
            with open(fulldir2, 'a', encoding='utf-8') as f0:
                f0.write('')
        customprompt = codecs.open(fulldir2, 'r', encoding='utf-8').read()
        promptlist = customprompt.split('---')
        while '' in promptlist:
            promptlist.remove('')
        itemlist = []
        for i in range(len(promptlist)):
            itemlist.append(promptlist[i].split('|><|')[0].replace('<|', '').replace('\n', ''))
        if itemlist != []:
            self.widget5.addItems(itemlist)
        if itemlist == []:
            self.widget5.addItems(['No customized prompts, please add one in Settings'])
        self.widget5.setVisible(False)
        self.widget5.setFixedWidth(170)
        self.widget5.currentIndexChanged.connect(self.CustomChange)

        self.btn_sub5 = QPushButton('Run command', self)
        self.btn_sub5.clicked.connect(self.RunCommand)
        self.btn_sub5.setFixedSize(150, 20)
        self.btn_sub5.setVisible(False)

        self.te0 = QTextEdit(self)
        self.te0.setVisible(False)
        self.te0.setFixedSize(460, 310)
        self.te0.textChanged.connect(self.ChangeCmd)

        self.btn_sub6 = QPushButton('~New', self)
        self.btn_sub6.clicked.connect(self.openfronnew)
        self.btn_sub6.setFixedSize(70, 20)
        self.btn_sub6.setVisible(False)

        self.btn_sub7 = QPushButton('~Input', self)
        self.btn_sub7.clicked.connect(self.openfrominput)
        self.btn_sub7.setFixedSize(70, 20)
        self.btn_sub7.setVisible(False)

        self.btn_sub8 = QPushButton('~Old', self)
        self.btn_sub8.clicked.connect(self.openfronold)
        self.btn_sub8.setFixedSize(70, 20)
        self.btn_sub8.setVisible(False)

        self.btn0_1 = QPushButton('', self)
        self.btn0_1.setFixedSize(25, 25)
        self.btn0_1.setStyleSheet('''
                QPushButton{
                border: transparent;
                background-color: transparent;
                border-image: url(/Applications/Broccoli.app/Contents/Resources/set2.png);
                }
                QPushButton:pressed{
                border: 1px outset grey;
                background-color: #0085FF;
                border-radius: 4px;
                padding: 1px;
                color: #FFFFFF
                }
                ''')
        self.btn0_1.move(345, 780)

        self.btn0_2 = QPushButton('', self)
        self.btn0_2.setFixedSize(25, 25)
        self.btn0_2.setStyleSheet('''
                        QPushButton{
                        border: transparent;
                        background-color: transparent;
                        border-image: url(/Applications/Broccoli.app/Contents/Resources/transfer2.png);
                        }
                        QPushButton:pressed{
                        border: 1px outset grey;
                        background-color: #0085FF;
                        border-radius: 4px;
                        padding: 1px;
                        color: #FFFFFF
                        }
                        ''')
        self.btn0_2.move(315, 780)

        qw1 = QWidget()
        vbox1 = QVBoxLayout()
        vbox1.setContentsMargins(0, 0, 0, 0)
        vbox1.addStretch()
        vbox1.addWidget(self.btn_sub1)
        vbox1.addWidget(self.btn_sub4)
        vbox1.addWidget(btn_sub2)
        vbox1.addWidget(btn_sub3)
        qw1.setLayout(vbox1)

        qw1_3 = QWidget()
        vbox1_3 = QHBoxLayout()
        vbox1_3.setContentsMargins(0, 0, 0, 0)
        vbox1_3.addWidget(self.widget0)
        vbox1_3.addWidget(self.widget1)
        vbox1_3.addWidget(self.lbl1)
        vbox1_3.addWidget(self.widget2)
        vbox1_3.addWidget(self.widget3)
        vbox1_3.addWidget(self.widget4)
        vbox1_3.addWidget(self.widget5)
        vbox1_3.addWidget(self.btn_sub5)
        vbox1_3.addWidget(self.btn_sub6)
        vbox1_3.addWidget(self.btn_sub7)
        vbox1_3.addWidget(self.btn_sub8)
        qw1_3.setLayout(vbox1_3)

        qw2 = QWidget()
        vbox2 = QVBoxLayout()
        vbox2.setContentsMargins(0, 0, 0, 0)
        vbox2.addWidget(qw1_3)
        vbox2.addStretch()
        vbox2.addWidget(self.text1)
        qw2.setLayout(vbox2)

        qw2_1 = QWidget()
        vbox2_1 = QHBoxLayout()
        vbox2_1.setContentsMargins(0, 0, 0, 0)
        vbox2_1.addWidget(qw2)
        vbox2_1.addWidget(qw1)
        qw2_1.setLayout(vbox2_1)

        self.qw3 = QWidget()
        vbox3 = QVBoxLayout()
        vbox3.setContentsMargins(20, 20, 20, 20)
        vbox3.addWidget(self.real1)
        vbox3.addWidget(self.te0)
        vbox3.addStretch()
        vbox3.addWidget(qw2_1)
        self.qw3.setLayout(vbox3)
        self.qw3.setObjectName("Main")

        vbox3 = QVBoxLayout()
        vbox3.setContentsMargins(0, 0, 0, 0)
        vbox3.addWidget(self.btn_00)
        vbox3.addWidget(self.qw3)
        self.setLayout(vbox3)
        self.activate()
        self.assigntoall()
        self.btn0_1.raise_()
        self.btn0_2.raise_()
        self.trans = 0

    def move_window(self, width, height):
        animation = QPropertyAnimation(self, b"geometry", self)
        animation.setDuration(250)
        new_pos = QRect(width, height, self.width(), self.height())
        animation.setEndValue(new_pos)
        animation.start()
        self.i += 1

    def move_window2(self, width, height):
        animation = QPropertyAnimation(self, b"geometry", self)
        animation.setDuration(400)
        new_pos = QRect(width, height, self.width(), self.height())
        animation.setEndValue(new_pos)
        animation.start()

    def assigntoall(self):
        cmd = """osascript -e '''
on run
    tell application "System Events" to set activeApp to "Broccoli"
    tell application "System Events" to tell UI element activeApp of list 1 of process "Dock"
        perform action "AXShowMenu"
        click menu item "Options" of menu 1
        click menu item "All Desktops" of menu 1 of menu item "Options" of menu 1
    end tell
end run'''"""
        try:
            os.system(cmd)
        except Exception as e:
            pass

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragPosition = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if self.dragPosition is None:
            return
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.dragPosition)

    def timeout_handler(self, signum, frame):
        raise TimeoutException("Timeout")

    def SendX(self):
        self.btn_sub1.setDisabled(True)
        self.btn_sub4.setDisabled(True)
        modelnow = codecs.open('/Applications/Broccoli.app/Contents/Resources/modelnow.txt', 'r', encoding='utf-8').read()
        Which = codecs.open('/Applications/Broccoli.app/Contents/Resources/which.txt', 'r', encoding='utf-8').read()
        if not action6.isChecked() or (action6.isChecked() and self.widget0.currentIndex() != 0):
            if Which == '0':
                if self.text1.toPlainText() == '':
                    a = subprocess.check_output('pbpaste', env={'LANG': 'en_US.UTF-8'}).decode('utf-8')
                    self.text1.setPlainText(a)
                QuesText = self.text1.toPlainText()
                QuesText = QuesText.lstrip('\n')
                QuesText = QuesText.replace('\n', '\n\n\t')
                QuesText = QuesText.replace('\n\n\t\n\n\t', '\n\n\t')
                self.LastQ = str(self.text1.toPlainText())
                AccountGPT = codecs.open('/Applications/Broccoli.app/Contents/Resources/api.txt', 'r', encoding='utf-8').read()
                if AccountGPT != '' and self.text1.toPlainText() != '':
                    QApplication.processEvents()
                    QApplication.restoreOverrideCursor()
                    self.text1.setReadOnly(True)
                    md = '- Q: ' + QuesText + '\n\n'
                    with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a', encoding='utf-8') as f1:
                        f1.write(md)
                    PromText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read()
                    newhtml = self.md2html(PromText)
                    self.real1.setHtml(newhtml)
                    self.real1.ensureCursorVisible()  # 游标可用
                    cursor = self.real1.textCursor()  # 设置游标
                    pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    self.real1.setTextCursor(cursor)  # 滚动到游标位置
                    QApplication.processEvents()
                    QApplication.restoreOverrideCursor()
                    timeout = 60
                    timeset = codecs.open('/Applications/Broccoli.app/Contents/Resources/timeout.txt', 'r',
                                          encoding='utf-8').read()
                    if timeset != '':
                        timeout = int(timeset)
                    signal.signal(signal.SIGALRM, self.timeout_handler)
                    signal.alarm(timeout)  # set timer to 15 seconds
                    try:
                        openai.api_key = AccountGPT
                        history = ''
                        showhistory = codecs.open('/Applications/Broccoli.app/Contents/Resources/history.txt', 'r',
                                              encoding='utf-8').read()
                        if showhistory == '1':
                            history = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read().replace('- A: ', '').replace('- Q: ', '')
                        prompt = str(self.text1.toPlainText())
                        reststr = history + '---' + prompt
                        tokenizer = GPT2Tokenizer.from_pretrained('EleutherAI/gpt-neo-2.7B')
                        A = tokenizer.encode(reststr, add_special_tokens=True)
                        totaltoken = codecs.open('/Applications/Broccoli.app/Contents/Resources/total.txt', 'r',
                                               encoding='utf-8').read()
                        maxtoken = codecs.open('/Applications/Broccoli.app/Contents/Resources/max.txt', 'r',
                                    encoding='utf-8').read()
                        prompttoken = int(totaltoken) - int(maxtoken)
                        while len(A) >= prompttoken:
                            AllList = reststr.split('---')
                            while '' in AllList:
                                AllList.remove('')
                            while '\n\n' in AllList:
                                AllList.remove('\n\n')
                            del AllList[0]
                            reststr = '---'.join(AllList)
                            A = tokenizer.encode(reststr, add_special_tokens=True)
                            continue
                        if self.widget0.currentIndex() == 0:
                            prompt = reststr
                        if self.widget0.currentIndex() == 1:
                            prompt = f"""Reply only the Applescript to fullfill this command. Don’t reply any other explanations. Before the code starts, write "「「START」」" and write "「「END」」” after it ends. Don't reply with method that needs further information and revision. Command: {str(self.text1.toPlainText())}. """
                        if self.widget0.currentIndex() == 2:
                            prompt = f"""You are a translation engine that can only translate text and cannot interpret it. Translate this text from {self.widget1.currentText()} to {self.widget2.currentText()}. Don’t reply any other explanations. Before the translated text starts, write "「「START」」" and write "「「END」」” after it ends. Text: {str(self.text1.toPlainText())}. """
                        if self.widget0.currentIndex() == 3:
                            prompt = f"""Revise the text in {self.widget4.currentText()} to remove grammar mistakes and make it more clear, concise, and coherent. Don’t reply any other explanations. Before the text starts, write "「「START」」" and write "「「END」」” after it ends. Text: {str(self.text1.toPlainText())}. """
                        if self.widget0.currentIndex() == 4:
                            prompt = f"""You are a text summarizer, you can only summarize the text, don't interpret it. Summarize this text in {self.widget4.currentText()} to make it shorter, logical and clear. Don’t reply any other explanations. Before the text starts, write "「「START」」" and write "「「END」」” after it ends. Text: {str(self.text1.toPlainText())}. """
                        if self.widget0.currentIndex() == 5:
                            prompt = f"""You are an expert in semantics and grammar, teaching me how to learn. Please explain in {self.widget4.currentText()} the meaning of every word in the text above and the meaning and the grammar structure of the text. If a word is part of an idiom, please explain the idiom and provide a few examples in {self.widget4.currentText()} with similar meanings, along with their explanations. Before the text starts, write "「「START」」" and write "「「END」」” after it ends. Text: {str(self.text1.toPlainText())}. """
                        if self.widget0.currentIndex() == 6:
                            prompt = f"""You are a code explanation engine, you can only explain the code, do not interpret or translate it. Also, please report any bugs you find in the code to the author of the code. Must repeat in {self.widget4.currentText()}. Before the text starts, write "「「START」」" and write "「「END」」” after it ends. Code: {str(self.text1.toPlainText())}. """

                        tutr = 0.5
                        temp = codecs.open('/Applications/Broccoli.app/Contents/Resources/temp.txt', 'r',
                                           encoding='utf-8').read()
                        if temp != '':
                            tutr = float(temp)

                        maxt = 1024
                        if maxtoken != '':
                            maxt = int(maxtoken)

                        completion = openai.ChatCompletion.create(
                            model=modelnow,
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=maxt,
                            n=1,
                            stop=None,
                            temperature=tutr,
                        )
                        message = completion.choices[0].message["content"].strip()
                        QApplication.processEvents()
                        QApplication.restoreOverrideCursor()
                        if self.widget0.currentIndex() == 0 or self.widget0.currentIndex() == 7:
                            message = message.lstrip('\n')
                            message = message.replace('\n', '\n\n\t')
                            message = message.replace('\n\n\t\n\n\t', '\n\n\t')
                            message = '\n\t' + message
                            QApplication.processEvents()
                            QApplication.restoreOverrideCursor()
                        if self.widget0.currentIndex() == 1:
                            pattern = re.compile(r'「「START」」([\s\S]*?)「「END」」')
                            result = pattern.findall(message)
                            ResultEnd = ''.join(result)
                            with open('/Applications/Broccoli.app/Contents/Resources/command.txt', 'w', encoding='utf-8') as f0:
                                f0.write(ResultEnd)
                            message = "Your command is:" + '\n\t' + ResultEnd
                            self.te0.setText(ResultEnd)
                        if self.widget0.currentIndex() == 2 or self.widget0.currentIndex() == 3 or \
                                self.widget0.currentIndex() == 4 or self.widget0.currentIndex() == 5 or \
                                self.widget0.currentIndex() == 6:
                            pattern = re.compile(r'「「START」」([\s\S]*?)「「END」」')
                            result = pattern.findall(message)
                            ResultEnd = ''.join(result)
                            ResultEnd = ResultEnd.encode('utf-8').decode('utf-8', 'ignore')
                            uid = os.getuid()
                            env = os.environ.copy()
                            env['__CF_USER_TEXT_ENCODING'] = f'{uid}:0x8000100:0x8000100'
                            p = subprocess.Popen(['pbcopy', 'w'], stdin=subprocess.PIPE, env=env)
                            p.communicate(input=ResultEnd.encode('utf-8'))
                            message = ResultEnd
                            message = message.lstrip('\n')
                            message = message.replace('\n', '\n\n\t')
                            message = message.replace('\n\n\t\n\n\t', '\n\n\t')
                            message = '\n\t' + message

                        EndMess = '- A: ' + message + '\n\n---\n\n'
                        with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a', encoding='utf-8') as f1:
                            f1.write(EndMess)
                        ProcessText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read()
                        midhtml = self.md2html(ProcessText)
                        self.real1.setHtml(midhtml)
                        self.real1.ensureCursorVisible()  # 游标可用
                        cursor = self.real1.textCursor()  # 设置游标
                        pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                        cursor.setPosition(pos)  # 游标位置设置为尾部
                        self.real1.setTextCursor(cursor)  # 滚动到游标位置
                        QApplication.processEvents()
                        QApplication.restoreOverrideCursor()

                        self.text1.clear()
                    except TimeoutException:
                        with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a', encoding='utf-8') as f1:
                            f1.write('- A: Timed out, please try again!' + '\n\n---\n\n')
                        AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read()
                        endhtml = self.md2html(AllText)
                        self.real1.setHtml(endhtml)
                        self.real1.ensureCursorVisible()  # 游标可用
                        cursor = self.real1.textCursor()  # 设置游标
                        pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                        cursor.setPosition(pos)  # 游标位置设置为尾部
                        self.real1.setTextCursor(cursor)  # 滚动到游标位置
                        self.text1.setPlainText(self.LastQ)
                    except Exception as e:
                        with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a', encoding='utf-8') as f1:
                            f1.write('- A: Error, please try again!' + str(e) + '\n\n---\n\n')
                        AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read()
                        endhtml = self.md2html(AllText)
                        self.real1.setHtml(endhtml)
                        self.real1.ensureCursorVisible()  # 游标可用
                        cursor = self.real1.textCursor()  # 设置游标
                        pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                        cursor.setPosition(pos)  # 游标位置设置为尾部
                        self.real1.setTextCursor(cursor)  # 滚动到游标位置
                        self.text1.setPlainText(self.LastQ)
                    signal.alarm(0)  # reset timer
                    self.text1.setReadOnly(False)
                if AccountGPT == '':
                    self.real1.setText('You should set your accounts in Settings.')
            if Which == '1':
                if self.text1.toPlainText() == '':
                    a = subprocess.check_output('pbpaste', env={'LANG': 'en_US.UTF-8'}).decode('utf-8')
                    self.text1.setPlainText(a)
                QuesText = self.text1.toPlainText()
                QuesText = QuesText.lstrip('\n')
                QuesText = QuesText.replace('\n', '\n\n\t')
                QuesText = QuesText.replace('\n\n\t\n\n\t', '\n\n\t')
                self.LastQ = str(self.text1.toPlainText())
                AccountGPT = codecs.open('/Applications/Broccoli.app/Contents/Resources/api.txt', 'r', encoding='utf-8').read()
                if AccountGPT != '' and self.text1.toPlainText() != '':
                    self.text1.setReadOnly(True)
                    md = '- Q: ' + QuesText + '\n\n'
                    with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a', encoding='utf-8') as f1:
                        f1.write(md)
                    PromText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read()
                    newhtml = self.md2html(PromText)
                    self.real1.setHtml(newhtml)
                    self.real1.ensureCursorVisible()  # 游标可用
                    cursor = self.real1.textCursor()  # 设置游标
                    pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    self.real1.setTextCursor(cursor)  # 滚动到游标位置
                    timeout = 60
                    timeset = codecs.open('/Applications/Broccoli.app/Contents/Resources/timeout.txt', 'r',
                                          encoding='utf-8').read()
                    if timeset != '':
                        timeout = int(timeset)
                    signal.signal(signal.SIGALRM, self.timeout_handler)
                    signal.alarm(timeout)  # set timer to 15 seconds
                    # Set up your API key
                    ENDPOINT = 'https://api.openai.com/v1/chat/completions'
                    api2 = codecs.open('/Applications/Broccoli.app/Contents/Resources/api2.txt', 'r',
                                       encoding='utf-8').read()
                    bear = codecs.open('/Applications/Broccoli.app/Contents/Resources/bear.txt', 'r',
                                       encoding='utf-8').read()
                    thirdp = codecs.open('/Applications/Broccoli.app/Contents/Resources/third.txt', 'r',
                                       encoding='utf-8').read()
                    if bear != '' and api2 != '' and thirdp == '1':
                        ENDPOINT = bear + '/v1/chat/completions'
                        AccountGPT = api2
                    HEADERS = {"Authorization": f"Bearer {AccountGPT}"}
                    totaltoken = codecs.open('/Applications/Broccoli.app/Contents/Resources/total.txt', 'r',
                                             encoding='utf-8').read()
                    maxtoken = codecs.open('/Applications/Broccoli.app/Contents/Resources/max.txt', 'r',
                                           encoding='utf-8').read()
                    prompttoken = int(totaltoken) - int(maxtoken)
                    try:
                        async def chat_gpt(message, conversation_history=None, tokens_limit=prompttoken):
                            if conversation_history is None:
                                conversation_history = []

                            conversation_history.append({"role": "user", "content": message})

                            input_text = "".join([f"{msg['role']}:{msg['content']}\n" for msg in conversation_history])

                            # Truncate or shorten the input text if it exceeds the token limit
                            encoded_input_text = input_text.encode("utf-8")
                            while len(encoded_input_text) > tokens_limit:
                                conversation_history.pop(0)
                                input_text = "".join([f"{msg['role']}:{msg['content']}\n" for msg in conversation_history])
                                encoded_input_text = input_text.encode("utf-8")

                            tutr = 0.5
                            temp = codecs.open('/Applications/Broccoli.app/Contents/Resources/temp.txt', 'r',
                                               encoding='utf-8').read()
                            if temp != '':
                                tutr = float(temp)

                            maxt = 1024
                            if maxtoken != '':
                                maxt = int(maxtoken)

                            # Set up the API call data
                            data = {
                                "model": modelnow,
                                "messages": [{"role": "user", "content": input_text}],
                                "max_tokens": maxt,
                                "temperature": tutr,
                                "n": 1,
                                "stop": None,
                            }

                            # Make the API call asynchronously
                            async with httpx.AsyncClient() as client:
                                response = await client.post(ENDPOINT, json=data, headers=HEADERS, timeout=60.0)

                            # Process the API response
                            if response.status_code == 200:
                                response_data = response.json()
                                chat_output = response_data["choices"][0]["message"]["content"].strip()
                                return chat_output
                            else:
                                raise Exception(f"API call failed with status code {response.status_code}: {response.text}")

                        async def main():
                            conversation_history = []
                            prompt = str(self.text1.toPlainText())
                            if self.widget0.currentIndex() == 0:
                                ori_history = [{"role": "user", "content": "Hey."}, {"role": "assistant", "content": "Hello! I'm happy to help you."}]
                                conversation_history = ori_history
                                showhistory = codecs.open('/Applications/Broccoli.app/Contents/Resources/history.txt', 'r',
                                                      encoding='utf-8').read()
                                if showhistory == '1':
                                    try:
                                        history = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read().replace('"', '').replace(
                                            '- Q: ', '''{"role": "user", "content": "''').\
                                            replace('- A: ', '''"}✡{"role": "assistant", "content": "''')\
                                            .replace('---', '''"}✡''').replace('\n', '').replace('\t', '').rstrip()
                                        historylist = history.split('✡')
                                        while '' in historylist:
                                            historylist.remove('')
                                        for hili in historylist:
                                            my_dict = json.loads(hili)
                                            conversation_history.append(my_dict)
                                    except Exception as e:
                                        pass
                            if self.widget0.currentIndex() == 1:
                                prompt = f"""Reply only the Applescript to fullfill this command. Don’t reply any other explanations. Before the code starts, write "「「START」」" and write "「「END」」” after it ends. Don't reply with method that needs further information and revision. Command: {str(self.text1.toPlainText())}. """
                            if self.widget0.currentIndex() == 2:
                                prompt = f"""You are a translation engine that can only translate text and cannot interpret it. Translate this text from {self.widget1.currentText()} to {self.widget2.currentText()}. Don’t reply any other explanations. Before the translated text starts, write "「「START」」" and write "「「END」」” after it ends. Text: {str(self.text1.toPlainText())}. """
                            if self.widget0.currentIndex() == 3:
                                prompt = f"""Revise the text in {self.widget4.currentText()} to remove grammar mistakes and make it more clear, concise, and coherent. Don’t reply any other explanations. Before the text starts, write "「「START」」" and write "「「END」」” after it ends. Text: {str(self.text1.toPlainText())}. """
                            if self.widget0.currentIndex() == 4:
                                prompt = f"""You are a text summarizer, you can only summarize the text, don't interpret it. Summarize this text in {self.widget4.currentText()} to make it shorter, logical and clear. Don’t reply any other explanations. Before the text starts, write "「「START」」" and write "「「END」」” after it ends. Text: {str(self.text1.toPlainText())}. """
                            if self.widget0.currentIndex() == 5:
                                prompt = f"""You are an expert in semantics and grammar, teaching me how to learn. Please explain in {self.widget4.currentText()} the meaning of every word in the text above and the meaning and the grammar structure of the text. If a word is part of an idiom, please explain the idiom and provide a few examples in {self.widget4.currentText()} with similar meanings, along with their explanations. Before the text starts, write "「「START」」" and write "「「END」」” after it ends. Text: {str(self.text1.toPlainText())}. """
                            if self.widget0.currentIndex() == 6:
                                prompt = f"""You are a code explanation engine, you can only explain the code, do not interpret or translate it. Also, please report any bugs you find in the code to the author of the code. Must repeat in {self.widget4.currentText()}. Before the text starts, write "「「START」」" and write "「「END」」” after it ends. Code: {str(self.text1.toPlainText())}. """

                            response = await chat_gpt(prompt, conversation_history)
                            message = response.lstrip('assistant:').strip()
                            if self.widget0.currentIndex() == 0 or self.widget0.currentIndex() == 7:
                                message = message.lstrip('\n')
                                message = message.replace('\n', '\n\n\t')
                                message = message.replace('\n\n\t\n\n\t', '\n\n\t')
                                message = '\n\t' + message
                                QApplication.processEvents()
                                QApplication.restoreOverrideCursor()
                            if self.widget0.currentIndex() == 1:
                                pattern = re.compile(r'「「START」」([\s\S]*?)「「END」」')
                                result = pattern.findall(message)
                                ResultEnd = ''.join(result)
                                with open('/Applications/Broccoli.app/Contents/Resources/command.txt', 'w', encoding='utf-8') as f0:
                                    f0.write(ResultEnd)
                                message = "Your command is:" + '\n\t' + ResultEnd
                                self.te0.setText(ResultEnd)
                            if self.widget0.currentIndex() == 2 or self.widget0.currentIndex() == 3 or \
                                    self.widget0.currentIndex() == 4 or self.widget0.currentIndex() == 5 or \
                                    self.widget0.currentIndex() == 6:
                                pattern = re.compile(r'「「START」」([\s\S]*?)「「END」」')
                                result = pattern.findall(message)
                                ResultEnd = ''.join(result)
                                ResultEnd = ResultEnd.encode('utf-8').decode('utf-8', 'ignore')
                                uid = os.getuid()
                                env = os.environ.copy()
                                env['__CF_USER_TEXT_ENCODING'] = f'{uid}:0x8000100:0x8000100'
                                p = subprocess.Popen(['pbcopy', 'w'], stdin=subprocess.PIPE, env=env)
                                p.communicate(input=ResultEnd.encode('utf-8'))
                                message = ResultEnd
                                message = message.lstrip('\n')
                                message = message.replace('\n', '\n\n\t')
                                message = message.replace('\n\n\t\n\n\t', '\n\n\t')
                                message = '\n\t' + message

                            EndMess = '- A: ' + message + '\n\n---\n\n'
                            with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a', encoding='utf-8') as f1:
                                f1.write(EndMess)
                            ProcessText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read()
                            midhtml = self.md2html(ProcessText)
                            self.real1.setHtml(midhtml)
                            self.real1.ensureCursorVisible()  # 游标可用
                            cursor = self.real1.textCursor()  # 设置游标
                            pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                            cursor.setPosition(pos)  # 游标位置设置为尾部
                            self.real1.setTextCursor(cursor)  # 滚动到游标位置
                            QApplication.processEvents()
                            QApplication.restoreOverrideCursor()
                            self.text1.clear()
                        asyncio.run(main())
                    except TimeoutException:
                        with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a', encoding='utf-8') as f1:
                            f1.write('- A: Timed out, please try again!' + '\n\n---\n\n')
                        AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read()
                        endhtml = self.md2html(AllText)
                        self.real1.setHtml(endhtml)
                        self.real1.ensureCursorVisible()  # 游标可用
                        cursor = self.real1.textCursor()  # 设置游标
                        pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                        cursor.setPosition(pos)  # 游标位置设置为尾部
                        self.real1.setTextCursor(cursor)  # 滚动到游标位置
                        self.text1.setPlainText(self.LastQ)
                    except Exception as e:
                        with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a', encoding='utf-8') as f1:
                            f1.write('- A: Error, please try again!' + str(e) + '\n\n---\n\n')
                        AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read()
                        endhtml = self.md2html(AllText)
                        self.real1.setHtml(endhtml)
                        self.real1.ensureCursorVisible()  # 游标可用
                        cursor = self.real1.textCursor()  # 设置游标
                        pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                        cursor.setPosition(pos)  # 游标位置设置为尾部
                        self.real1.setTextCursor(cursor)  # 滚动到游标位置
                        self.text1.setPlainText(self.LastQ)
                    signal.alarm(0)  # reset timer
                    self.text1.setReadOnly(False)
                if AccountGPT == '':
                    self.real1.setText('You should set your accounts in Settings.')
        if action6.isChecked() and self.widget0.currentIndex() == 0:
            COMPLETIONS_MODEL = modelnow
            EMBEDDING_MODEL = "text-embedding-ada-002"
            AccountGPT = codecs.open('/Applications/Broccoli.app/Contents/Resources/api.txt', 'r', encoding='utf-8').read()
            api2 = codecs.open('/Applications/Broccoli.app/Contents/Resources/api2.txt', 'r',
                               encoding='utf-8').read()
            bear = codecs.open('/Applications/Broccoli.app/Contents/Resources/bear.txt', 'r',
                               encoding='utf-8').read()
            thirdp = codecs.open('/Applications/Broccoli.app/Contents/Resources/third.txt', 'r',
                                 encoding='utf-8').read()
            openai.api_key = AccountGPT
            TEMP = float(codecs.open('/Applications/Broccoli.app/Contents/Resources/temp.txt', 'r', encoding='utf-8').read())
            MAXT = int(codecs.open('/Applications/Broccoli.app/Contents/Resources/max.txt', 'r', encoding='utf-8').read())
            chatwith = codecs.open("/Applications/Broccoli.app/Contents/Resources/title.txt", 'r', encoding='utf-8').read() + '.csv'
            if self.text1.toPlainText() != '' and TEMP != '' and MAXT != '' and chatwith != '':
                chatpath1 = os.path.join(self.Index, chatwith)
                chatpath2 = os.path.join(self.Embed, chatwith)
                df = pd.read_csv(chatpath1)
                df = df.set_index(["title", "heading"])
                df.sample(1)

                def get_embedding(text: str, model: str = EMBEDDING_MODEL) -> list[float]:
                    if AccountGPT != '' and thirdp == '0':
                        result = openai.Embedding.create(
                            model=model,
                            input=text
                        )
                        time.sleep(0.5)
                        return result["data"][0]["embedding"]
                    if AccountGPT == '' or (bear != '' and api2 != '' and thirdp == '1'):
                        ENDPOINT = bear + '/v1/embeddings'
                        HEADERS = {"Authorization": f"Bearer {api2}"}
                        data = {
                            "model": model,
                            "input": text,
                        }
                        response = requests.post(ENDPOINT, json=data, headers=HEADERS, timeout=60.0)
                        if response.status_code == 200:
                            response_data = response.json()
                            chat_output = response_data["data"][0]["embedding"]
                            time.sleep(0.5)
                            return chat_output
                        else:
                            raise Exception(f"API call failed with status code {response.status_code}: {response.text}")

                def load_embeddings(fname: str) -> dict[tuple[str, str], list[float]]:
                    df = pd.read_csv(fname, header=0)
                    max_dim = max([int(c) for c in df.columns if c != "title" and c != "heading"])
                    return {
                        (r.title, r.heading): [r[str(i)] for i in range(max_dim + 1)] for _, r in df.iterrows()
                    }

                document_embeddings = load_embeddings(chatpath2)

                def vector_similarity(x: list[float], y: list[float]) -> float:
                    return np.dot(np.array(x), np.array(y))

                def order_document_sections_by_query_similarity(query: str, contexts: dict[(str, str), np.array]) -> \
                list[
                    (float, (str, str))]:
                    query_embedding = get_embedding(query)

                    document_similarities = sorted([
                        (vector_similarity(query_embedding, doc_embedding), doc_index) for doc_index, doc_embedding in
                        contexts.items()
                    ], reverse=True)

                    return document_similarities

                MAX_SECTION_LEN = MAXT
                SEPARATOR = "\n* "

                tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
                separator_len = len(tokenizer.encode(SEPARATOR))

                def construct_prompt(question: str, context_embeddings: dict, df: pd.DataFrame) -> str:
                    most_relevant_document_sections = order_document_sections_by_query_similarity(question,
                                                                                                  context_embeddings)

                    chosen_sections = []
                    chosen_sections_len = 0
                    chosen_sections_indexes = []

                    for _, section_index in most_relevant_document_sections:
                        # Add contexts until we run out of space.
                        document_section = df.loc[section_index]

                        chosen_sections_len += document_section.tokens + separator_len
                        if (chosen_sections_len > MAX_SECTION_LEN).any():
                            break

                        chosen_sections.append(SEPARATOR + document_section.content.replace("\n", " "))
                        chosen_sections_indexes.append(str(section_index))

                    header = """Answer the question as truthfully as possible using the provided context, and if the answer is not contained within the text below, say "I don't know."\n\nContext:\n"""

                    with open('/Applications/Broccoli.app/Contents/Resources/ref.txt', 'w', encoding='utf-8') as f0:
                        f0.write("\t**Refrences:**" + "".join(str(chosen_sections)).replace('[', '').replace(']', '').replace("'", '').replace('\\n', '').replace('*', '\n\n\t- '))

                    return header + "".join(str(chosen_sections)) + "\n\n Q: " + question + "\n A:"

                def answer_query_with_context(
                        query: str,
                        df: pd.DataFrame,
                        document_embeddings: dict[(str, str), np.array],
                        show_prompt: bool = False
                ) -> str:
                    prompt = construct_prompt(
                        query,
                        document_embeddings,
                        df
                    )

                    if show_prompt:
                        print(prompt)

                    response = openai.ChatCompletion.create(
                        model=COMPLETIONS_MODEL,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=TEMP,
                        max_tokens=MAXT,
                    )

                    return response.choices[0].message["content"].strip('\n')

                self.LastQ = str(self.text1.toPlainText())
                QApplication.processEvents()
                QApplication.restoreOverrideCursor()
                self.text1.setReadOnly(True)
                md = '- Q: ' + self.text1.toPlainText() + '\n\n'
                with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a', encoding='utf-8') as f1:
                    f1.write(md)
                PromText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read()
                newhtml = self.md2html(PromText)
                self.real1.setHtml(newhtml)
                self.real1.ensureCursorVisible()  # 游标可用
                cursor = self.real1.textCursor()  # 设置游标
                pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                cursor.setPosition(pos)  # 游标位置设置为尾部
                self.real1.setTextCursor(cursor)  # 滚动到游标位置
                timeout = 60
                timeset = codecs.open('/Applications/Broccoli.app/Contents/Resources/timeout.txt', 'r',
                                      encoding='utf-8').read()
                if timeset != '':
                    timeout = int(timeset)
                signal.signal(signal.SIGALRM, self.timeout_handler)
                signal.alarm(timeout)
                Which = codecs.open('/Applications/Broccoli.app/Contents/Resources/which.txt', 'r', encoding='utf-8').read()
                if Which == '0' and AccountGPT != '':
                    try:
                        query = self.text1.toPlainText()
                        message = answer_query_with_context(query, df, document_embeddings)
                        message = message.lstrip('\n')
                        message = message.replace('\n', '\n\n\t')
                        message = message.replace('\n\n\t\n\n\t', '\n\n\t')
                        message = '\n\t' + message
                        ref = ''
                        showref = codecs.open('/Applications/Broccoli.app/Contents/Resources/showref.txt', 'r', encoding='utf-8').read()
                        if showref == '1':
                            ref = codecs.open('/Applications/Broccoli.app/Contents/Resources/ref.txt', 'r', encoding='utf-8').read()
                        EndMess = '- A: ' + message + '\n\n' + ref + '\n\n---\n\n'
                        with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a', encoding='utf-8') as f1:
                            f1.write(EndMess)
                        AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read()
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
                    except TimeoutException:
                        with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a', encoding='utf-8') as f1:
                            f1.write('- A: Timed out, please try again!' + '\n\n---\n\n')
                        AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read()
                        endhtml = self.md2html(AllText)
                        self.real1.setHtml(endhtml)
                        self.real1.ensureCursorVisible()  # 游标可用
                        cursor = self.real1.textCursor()  # 设置游标
                        pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                        cursor.setPosition(pos)  # 游标位置设置为尾部
                        self.real1.setTextCursor(cursor)  # 滚动到游标位置
                        self.text1.setPlainText(self.LastQ)
                    except Exception as e:
                        with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a', encoding='utf-8') as f1:
                            f1.write('- A: Error, please try again!' + str(e) + '\n\n---\n\n')
                        AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read()
                        endhtml = self.md2html(AllText)
                        self.real1.setHtml(endhtml)
                        self.real1.ensureCursorVisible()  # 游标可用
                        cursor = self.real1.textCursor()  # 设置游标
                        pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                        cursor.setPosition(pos)  # 游标位置设置为尾部
                        self.real1.setTextCursor(cursor)  # 滚动到游标位置
                        self.text1.setPlainText(self.LastQ)
                if Which == '1':
                    ENDPOINT = 'https://api.openai.com/v1/chat/completions'
                    api2 = codecs.open('/Applications/Broccoli.app/Contents/Resources/api2.txt', 'r',
                                       encoding='utf-8').read()
                    bear = codecs.open('/Applications/Broccoli.app/Contents/Resources/bear.txt', 'r',
                                       encoding='utf-8').read()
                    thirdp = codecs.open('/Applications/Broccoli.app/Contents/Resources/third.txt', 'r',
                                         encoding='utf-8').read()
                    if AccountGPT == '' and bear != '' and api2 != '':
                        ENDPOINT = bear + '/v1/chat/completions'
                        AccountGPT = api2
                    if bear != '' and api2 != '' and thirdp == '1':
                        ENDPOINT = bear + '/v1/chat/completions'
                        AccountGPT = api2
                    HEADERS = {"Authorization": f"Bearer {AccountGPT}"}

                    async def answer_query(
                            query: str,
                            df: pd.DataFrame,
                            document_embeddings: dict[(str, str), np.array],
                            show_prompt: bool = False
                    ) -> str:
                        prompt = construct_prompt(
                            query,
                            document_embeddings,
                            df
                        )

                        if show_prompt:
                            print(prompt)

                        ori_history = [{"role": "user", "content": "Hey."},
                                       {"role": "assistant", "content": "Hello! I'm happy to help you."}]
                        conversation_history = ori_history
                        try:
                            response = await chat_gpt(prompt, conversation_history)
                            message = response.lstrip('assistant:').strip()
                            return message
                        except Exception as e:
                            pass

                    async def chat_gpt(message, conversation_history=None, tokens_limit=4000):
                        if conversation_history is None:
                            conversation_history = []

                        conversation_history.append({"role": "user", "content": message})

                        input_text = "".join([f"{msg['role']}:{msg['content']}\n" for msg in conversation_history])

                        # Truncate or shorten the input text if it exceeds the token limit
                        encoded_input_text = input_text.encode("utf-8")
                        while len(encoded_input_text) > tokens_limit:
                            conversation_history.pop(0)
                            input_text = "".join(
                                [f"{msg['role']}:{msg['content']}\n" for msg in conversation_history])
                            encoded_input_text = input_text.encode("utf-8")

                        # Set up the API call data
                        data = {
                            "model": modelnow,
                            "messages": [{"role": "user", "content": input_text}],
                            "max_tokens": MAXT,
                            "temperature": TEMP,
                            "n": 1,
                            "stop": None,
                        }

                        # Make the API call asynchronously
                        async with httpx.AsyncClient() as client:
                            response = await client.post(ENDPOINT, json=data, headers=HEADERS, timeout=60.0)

                        # Process the API response
                        if response.status_code == 200:
                            response_data = response.json()
                            chat_output = response_data["choices"][0]["message"]["content"].strip()
                            return chat_output
                        else:
                            raise Exception(
                                f"API call failed with status code {response.status_code}: {response.text}")

                    try:
                        query = self.text1.toPlainText()
                        message = asyncio.run(answer_query(query, df, document_embeddings))
                        message = message.lstrip('\n')
                        message = message.replace('\n', '\n\n\t')
                        message = message.replace('\n\n\t\n\n\t', '\n\n\t')
                        message = '\n\t' + message
                        ref = ''
                        showref = codecs.open('/Applications/Broccoli.app/Contents/Resources/showref.txt', 'r',
                                              encoding='utf-8').read()
                        if showref == '1':
                            ref = codecs.open('/Applications/Broccoli.app/Contents/Resources/ref.txt', 'r',
                                          encoding='utf-8').read()
                        EndMess = '- A: ' + message + '\n\n' + ref + '\n\n---\n\n'
                        with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a', encoding='utf-8') as f1:
                            f1.write(EndMess)
                        AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read()
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
                    except TimeoutException:
                        with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a', encoding='utf-8') as f1:
                            f1.write('- A: Timed out, please try again!' + '\n\n---\n\n')
                        AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read()
                        endhtml = self.md2html(AllText)
                        self.real1.setHtml(endhtml)
                        self.real1.ensureCursorVisible()  # 游标可用
                        cursor = self.real1.textCursor()  # 设置游标
                        pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                        cursor.setPosition(pos)  # 游标位置设置为尾部
                        self.real1.setTextCursor(cursor)  # 滚动到游标位置
                        self.text1.setPlainText(self.LastQ)
                    except Exception as e:
                        with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a', encoding='utf-8') as f1:
                            f1.write('- A: Error, please try again!' + str(e) + '\n\n---\n\n')
                        AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read()
                        endhtml = self.md2html(AllText)
                        self.real1.setHtml(endhtml)
                        self.real1.ensureCursorVisible()  # 游标可用
                        cursor = self.real1.textCursor()  # 设置游标
                        pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                        cursor.setPosition(pos)  # 游标位置设置为尾部
                        self.real1.setTextCursor(cursor)  # 滚动到游标位置
                        self.text1.setPlainText(self.LastQ)
                signal.alarm(0)  # reset timer
                self.text1.setReadOnly(False)
        self.btn_sub1.setDisabled(False)
        self.btn_sub4.setDisabled(False)

    def ClearX(self):
        self.text1.clear()
        self.text1.setReadOnly(False)
        self.real1.clear()
        self.te0.clear()
        with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'w', encoding='utf-8') as f1:
            f1.write('')

    def ExportX(self):
        home_dir = str(Path.home())
        fj = QFileDialog.getExistingDirectory(self, 'Open', home_dir)
        if fj != '':
            ConText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read()
            ISOTIMEFORMAT = '%Y%m%d %H-%M-%S-%f'
            theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
            tarname = theTime + " GPToutput.md"
            fulldir = os.path.join(fj, tarname)
            with open(fulldir, 'w', encoding='utf-8') as f1:
                f1.write(ConText)

    def ModeX(self, i):
        home_dir = str(Path.home())
        tarname1 = "BroccoliAppPath"
        self.fulldir1 = os.path.join(home_dir, tarname1)
        tarname3 = "lang.txt"
        fulldir3 = os.path.join(self.fulldir1, tarname3)
        langs = codecs.open(fulldir3, 'r', encoding='utf-8').read()
        fulllanglist = []
        langs_list = ['English', '中文', '日本語']
        if langs != '':
            langs_list = langs.split('\n')
            while '' in langs_list:
                langs_list.remove('')
            for x in range(len(langs_list)):
                fulllanglist.append(langs_list[x])
        if langs == '':
            for x in range(len(langs_list)):
                fulllanglist.append(langs_list[x])
        if i == 0:
            self.widget1.setVisible(False)
            self.widget2.setVisible(False)
            #self.widget3.setVisible(True)
            self.widget3.setVisible(False)
            self.lbl1.setVisible(False)
            self.widget4.setVisible(False)
            self.widget5.setVisible(False)
            self.btn_sub5.setVisible(False)
            self.te0.setVisible(False)
            self.real1.setFixedSize(460, 630)
            if action6.isChecked():
                self.te0.clear()
                self.te0.setVisible(True)
                self.btn_sub6.setVisible(True)
                self.btn_sub7.setVisible(True)
                self.btn_sub8.setVisible(True)
                self.real1.setFixedSize(460, 310)
                self.te0.setFixedSize(460, 310)
        if i != 0:
            self.te0.setVisible(False)
            self.btn_sub6.setVisible(False)
            self.btn_sub7.setVisible(False)
            self.btn_sub8.setVisible(False)
            self.real1.setFixedSize(460, 630)
        if i == 1:
            self.widget1.setVisible(False)
            self.widget2.setVisible(False)
            self.widget3.setVisible(False)
            self.lbl1.setVisible(False)
            self.widget4.setVisible(False)
            self.widget5.setVisible(False)
            self.btn_sub5.setVisible(True)
            self.te0.setVisible(True)
            self.real1.setFixedSize(460, 310)
            self.te0.setFixedSize(460, 310)
            self.te0.clear()
        if i == 2:
            self.widget1.setVisible(True)
            self.widget2.setVisible(True)
            self.widget3.setVisible(False)
            self.lbl1.setVisible(True)
            self.widget4.setVisible(False)
            self.widget5.setVisible(False)
            self.btn_sub5.setVisible(False)
            self.te0.setVisible(False)
            self.real1.setFixedSize(460, 630)
            # renew 1
            self.widget1.clear()
            self.widget1.addItems(langs_list)
        if i == 3:
            self.widget1.setVisible(False)
            self.widget2.setVisible(False)
            self.widget3.setVisible(False)
            self.lbl1.setVisible(True)
            self.widget4.setVisible(True)
            self.widget5.setVisible(False)
            self.btn_sub5.setVisible(False)
            self.te0.setVisible(False)
            self.real1.setFixedSize(460, 630)
            # renew 4
            self.widget4.clear()
            self.widget4.addItems(fulllanglist)
        if i == 4:
            self.widget1.setVisible(False)
            self.widget2.setVisible(False)
            self.widget3.setVisible(False)
            self.lbl1.setVisible(True)
            self.widget4.setVisible(True)
            self.widget5.setVisible(False)
            self.btn_sub5.setVisible(False)
            self.te0.setVisible(False)
            self.real1.setFixedSize(460, 630)
            # renew 4
            self.widget4.clear()
            self.widget4.addItems(fulllanglist)
        if i == 5:
            self.widget1.setVisible(False)
            self.widget2.setVisible(False)
            self.widget3.setVisible(False)
            self.lbl1.setVisible(True)
            self.widget4.setVisible(True)
            self.widget5.setVisible(False)
            self.btn_sub5.setVisible(False)
            self.te0.setVisible(False)
            self.real1.setFixedSize(460, 630)
            # renew 4
            self.widget4.clear()
            self.widget4.addItems(fulllanglist)
        if i == 6:
            self.widget1.setVisible(False)
            self.widget2.setVisible(False)
            self.widget3.setVisible(False)
            self.lbl1.setVisible(True)
            self.widget4.setVisible(True)
            self.widget5.setVisible(False)
            self.btn_sub5.setVisible(False)
            self.te0.setVisible(False)
            self.real1.setFixedSize(460, 630)
            # renew 4
            self.widget4.clear()
            self.widget4.addItems(fulllanglist)
        if i == 7:
            self.widget1.setVisible(False)
            self.widget2.setVisible(False)
            self.widget3.setVisible(False)
            self.lbl1.setVisible(True)
            self.widget4.setVisible(False)
            self.btn_sub5.setVisible(False)
            self.te0.setVisible(False)
            self.real1.setFixedSize(460, 630)
            self.widget5.setVisible(True)
            self.widget5.clear()
            home_dir = str(Path.home())
            tarname1 = "BroccoliAppPath"
            fulldir1 = os.path.join(home_dir, tarname1)
            if not os.path.exists(fulldir1):
                os.mkdir(fulldir1)
            tarname2 = "CustomPrompt.txt"
            fulldir2 = os.path.join(fulldir1, tarname2)
            if not os.path.exists(fulldir2):
                with open(fulldir2, 'a', encoding='utf-8') as f0:
                    f0.write('')
            customprompt = codecs.open(fulldir2, 'r', encoding='utf-8').read()
            promptlist = customprompt.split('---')
            while '' in promptlist:
                promptlist.remove('')
            itemlist = []
            for i in range(len(promptlist)):
                itemlist.append(promptlist[i].split('|><|')[0].replace('<|', '').replace('\n', ''))
            if itemlist != []:
                self.widget5.addItems(itemlist)
            if itemlist == []:
                self.widget5.addItems(['No customized prompts, please add one in Settings'])

    def AgainX(self):
        self.btn_sub1.setDisabled(True)
        self.btn_sub4.setDisabled(True)
        AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read()
        if AllText != '':
            AllList = AllText.split('---')
            while '\n\n' in AllList:
                AllList.remove('\n\n')
            pattern = re.compile(r'- Q: ([\s\S]*?)\n\n- A')
            result = pattern.findall(AllList[-1])
            ResultEnd = ''.join(result).replace('\t', '').lstrip('\n').rstrip('\n')
            self.text1.setPlainText(ResultEnd)
            self.SendX()
        self.btn_sub1.setDisabled(False)
        self.btn_sub4.setDisabled(False)

    def TranslateX(self):
        home_dir = str(Path.home())
        tarname1 = "BroccoliAppPath"
        fulldir1 = os.path.join(home_dir, tarname1)
        tarname3 = "lang.txt"
        fulldir3 = os.path.join(fulldir1, tarname3)
        currentlang = self.widget1.currentText()
        self.widget2.clear()
        langs = codecs.open(fulldir3, 'r', encoding='utf-8').read()
        if langs != '':
            langs_list = langs.split('\n')
            while '' in langs_list:
                langs_list.remove('')
            while currentlang in langs_list:
                langs_list.remove(currentlang)
            self.widget2.addItems(langs_list)
            self.widget2.setCurrentIndex(0)
        if langs == '':
            langs_list = ['English', '中文', '日本語']
            while currentlang in langs_list:
                langs_list.remove(currentlang)
            self.widget2.addItems(langs_list)
            self.widget2.setCurrentIndex(0)

    def CustomChange(self, i):
        home_dir = str(Path.home())
        tarname1 = "BroccoliAppPath"
        fulldir1 = os.path.join(home_dir, tarname1)
        if not os.path.exists(fulldir1):
            os.mkdir(fulldir1)
        tarname2 = "CustomPrompt.txt"
        fulldir2 = os.path.join(fulldir1, tarname2)
        if not os.path.exists(fulldir2):
            with open(fulldir2, 'a', encoding='utf-8') as f0:
                f0.write('')
        customprompt = codecs.open(fulldir2, 'r', encoding='utf-8').read()
        promptlist = customprompt.split('---')
        while '' in promptlist:
            promptlist.remove('')
        itemlist = []
        for n in range(len(promptlist)):
            itemlist.append(promptlist[n].split('|><|')[1].replace('|>', ''))
        if itemlist != []:
            try:
                self.text1.clear()
                self.text1.setPlainText(itemlist[i])
            except Exception as e:
                self.text1.clear()
                self.text1.setPlainText(e)

    def RunCommand(self):
        comm = codecs.open('/Applications/Broccoli.app/Contents/Resources/command.txt', 'r', encoding='utf-8').read()
        try:
            subprocess.call(['osascript', '-e', comm])
        except:
            pass

    def ChangeCmd(self):
        changed_cmd = self.te0.toPlainText()
        with open('/Applications/Broccoli.app/Contents/Resources/command.txt', 'w', encoding='utf-8') as f0:
            f0.write(changed_cmd)

    def OpenHistory(self):
        home_dir = str(Path.home())
        fj = QFileDialog.getOpenFileName(self, "Open File", home_dir, "Markdown Files (*.md)")
        if fj[0] != '':
            str_fj = ''.join(fj)
            str_fj = str_fj.replace('Markdown Files (*.md)', '')
            if "GPToutput.md" in str_fj:
                text_his = codecs.open(str_fj, 'r', encoding='utf-8').read()
                with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'w', encoding='utf-8') as f0:
                    f0.write(text_his)
                midhtml = self.md2html(text_his)
                self.real1.setHtml(midhtml)
                self.real1.ensureCursorVisible()  # 游标可用
                cursor = self.real1.textCursor()  # 设置游标
                pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                cursor.setPosition(pos)  # 游标位置设置为尾部
                self.real1.setTextCursor(cursor)  # 滚动到游标位置
        if not btna4.isChecked():
            self.pin_a_tab()

    def chatfilemode(self):
        if action6.isChecked() and self.widget0.currentIndex() == 0:
            self.te0.clear()
            self.te0.setVisible(True)
            self.btn_sub6.setVisible(True)
            self.btn_sub7.setVisible(True)
            self.btn_sub8.setVisible(True)
            self.real1.setFixedSize(460, 310)
            self.te0.setFixedSize(460, 310)
        if not action6.isChecked():
            self.te0.setVisible(False)
            self.btn_sub6.setVisible(False)
            self.btn_sub7.setVisible(False)
            self.btn_sub8.setVisible(False)
            self.real1.setFixedSize(460, 630)

    def openfronnew(self):
        home_dir = str(Path.home())
        fj = QFileDialog.getOpenFileName(self, "Open File", home_dir, "Text Files (*.txt);;Word Documents (*.docx *.DOCX)")
        if fj[0] != '':
            # copy to Local file
            str_fj = fj[0]
            text_his = ''
            if "Text" in fj[1]:
                text_his = codecs.open(str_fj, 'r', encoding='utf-8').read()
            if "Word" in fj[1]:
                text_his = docx2txt.process(str_fj)
            self.te0.setText(text_his)
            contlist = str_fj.split('/')
            cont = contlist[len(contlist) - 1].replace('.txt', '')
            contfull = cont + '.txt'
            tarname = os.path.join(self.Local, contfull)
            if not os.path.exists(tarname):
                with open(tarname, 'a', encoding='utf-8') as f0:
                    f0.write('')
            with open('/Applications/Broccoli.app/Contents/Resources/title.txt', 'w', encoding='utf-8') as f0:
                f0.write('')

            plain_list = self.te0.toPlainText().split('\n')
            while '' in plain_list:
                plain_list.remove('')
            for i in range(len(plain_list)):
                aj = jieba.cut(plain_list[i], cut_all=False)
                paj = '/'.join(aj)
                saj = paj.split('/')
                if len(saj) > 200:
                    times = int(len(saj) / 200) + 1
                    temp = ''
                    tm = 1
                    if tm == 1:
                        ter = saj[0:199]
                        tarstr = ' '.join(ter) + '✡'
                        temp = temp + tarstr
                        tm += 1
                    while 1 < tm <= times - 1:
                        ter = saj[(tm - 1)*200 - 1:tm*200 - 1]
                        tarstr = ' '.join(ter) + '✡'
                        temp = temp + tarstr
                        tm += 1
                    if tm == times:
                        ter = saj[(tm - 1)*200 - 1:]
                        tarstr = ' '.join(ter) + '✡'
                        temp = temp + tarstr
                    plain_list[i] = temp
            for n in range(len(plain_list)):
                plain_list[n] = self.default_clean(self.cleanlinebreak(plain_list[n]))
            plain_list = list(filter(None, plain_list))
            end_text = '✡'.join(plain_list)
            end_text = end_text.replace('✡✡', '✡')
            for i in range(10):
                end_text = end_text.replace('   ', ' ')
                end_text = end_text.replace('  ', ' ')
            end_text = end_text.replace('\n', '')
            end_text = end_text.replace('✡', '\n\n')
            self.te0.setText(end_text)
            with open(tarname, 'w', encoding='utf-8') as f0:
                f0.write(end_text)
            # produce Index.csv
            csv_line = end_text.replace(',', ';').split('\n\n')
            while '' in csv_line:
                csv_line.remove('')
            allline = len(csv_line)
            for x in range(len(csv_line)):
                csv_line[x] = "A" + ',' + str(x) + ',' + csv_line[x]
            csvtext = '\n'.join(csv_line)
            csvtext = 'title,heading,content\n' + csvtext
            csv_endtar = cont + '.csv'
            csv_tarname = os.path.join(self.Index, csv_endtar)
            with open(csv_tarname, 'w', encoding='utf-8') as f0:
                f0.write(csvtext)
            tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
            # 打开 CSV 文件并读取数据
            with open(csv_tarname, mode='r', encoding='utf-8') as csv_file:
                csv_reader = csv.reader(csv_file)
                rows = list(csv_reader)
            # 在数据中添加新列
            header = rows[0]
            header.append('tokens')
            for row in rows[1:]:
                tar = row[-1]
                A = tokenizer.encode(tar, add_special_tokens=True)
                if len(A) <= 1024:
                    row.append(str(len(A)))
                else:
                    row.append(str(1024))
            # 将更新后的数据写回 CSV 文件
            with open(csv_tarname, mode='w', newline='', encoding='utf-8') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(header)
                csv_writer.writerows(rows[1:])
            # delete those which are too long
            cleanlong = codecs.open(csv_tarname, 'r', encoding='utf-8').read()
            cleanlong = cleanlong.replace('\r', '')
            cleanlong_list = cleanlong.split('\n')
            while '' in cleanlong_list:
                cleanlong_list.remove('')
            del cleanlong_list[0]
            lostlist = []
            for f in range(len(cleanlong_list)):
                pattern = re.compile(r',(\d+)$')
                result = pattern.findall(cleanlong_list[f])
                if result != []:
                    realnum = int(''.join(result))
                    if realnum >= 1024:
                        lostlist.append(cleanlong_list[f])
            reallist = list(set(cleanlong_list) - set(lostlist))
            realcsv = '\n'.join(reallist)
            realcsv = 'title,heading,content,tokens\n' + realcsv
            with open(csv_tarname, 'w', encoding='utf-8') as f0:
                f0.write(realcsv)
            # produce Embed.csv
            AccountGPT = codecs.open('/Applications/Broccoli.app/Contents/Resources/api.txt', 'r',
                                     encoding='utf-8').read()
            api2 = codecs.open('/Applications/Broccoli.app/Contents/Resources/api2.txt', 'r',
                               encoding='utf-8').read()
            bear = codecs.open('/Applications/Broccoli.app/Contents/Resources/bear.txt', 'r',
                               encoding='utf-8').read()
            thirdp = codecs.open('/Applications/Broccoli.app/Contents/Resources/third.txt', 'r',
                                 encoding='utf-8').read()
            if AccountGPT != '' and thirdp == '0':
                SUCC = 0
                tarnamecsv = csv_tarname
                embedcsv = os.path.join(self.Embed, csv_endtar)
                try:
                    with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a',
                              encoding='utf-8') as f1:
                        f1.write(f'- Q: Please embed {tarname}.\n\n- A: ')
                    AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r',
                                          encoding='utf-8').read()
                    endhtml = self.md2html(AllText)
                    self.real1.setHtml(endhtml)
                    self.real1.ensureCursorVisible()  # 游标可用
                    cursor = self.real1.textCursor()  # 设置游标
                    pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    self.real1.setTextCursor(cursor)  # 滚动到游标位置

                    # midindex to embed
                    EMBEDDING_MODEL = "text-embedding-ada-002"
                    openai.api_key = AccountGPT
                    df = pd.read_csv(tarnamecsv)
                    df = df.set_index(["title", "heading"])
                    df.sample(1)
                    with open('/Applications/Broccoli.app/Contents/Resources/prog.txt', 'w', encoding='utf-8') as f0:
                        f0.write('')

                    def get_embedding(text: str, model: str = EMBEDDING_MODEL, nowline=0, allline=allline) -> list[float]:
                        result = openai.Embedding.create(
                            model=model,
                            input=text
                        )
                        QApplication.processEvents()
                        QApplication.restoreOverrideCursor()
                        with open('/Applications/Broccoli.app/Contents/Resources/prog.txt', 'a', encoding='utf-8') as f0:
                            f0.write('1\n')
                        prog = codecs.open('/Applications/Broccoli.app/Contents/Resources/prog.txt', 'r', encoding='utf-8').read()
                        proglist = prog.split('\n')
                        while '' in proglist:
                            proglist.remove('')
                        nowline += len(proglist)
                        prognum = str(int(nowline / allline * 100)) + '%'
                        with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a',
                                  encoding='utf-8') as f1:
                            f1.write(f'{prognum}...')
                        AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r',
                                              encoding='utf-8').read()
                        endhtml = self.md2html(AllText)
                        self.real1.setHtml(endhtml)
                        self.real1.ensureCursorVisible()  # 游标可用
                        cursor = self.real1.textCursor()  # 设置游标
                        pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                        cursor.setPosition(pos)  # 游标位置设置为尾部
                        self.real1.setTextCursor(cursor)  # 滚动到游标位置
                        time.sleep(0.5)
                        return result["data"][0]["embedding"]

                    df["embedding"] = df.content.apply(lambda x: get_embedding(x, EMBEDDING_MODEL))
                    df.to_csv('/Applications/Broccoli.app/Contents/Resources/with_embeddings.csv')
                    with open('/Applications/Broccoli.app/Contents/Resources/with_embeddings.csv', 'r', encoding='utf-8') as input_file:
                        reader = csv.reader(input_file)
                        # 获取 CSV 文件的标题行
                        header = next(reader)
                        # 获取要删除的列的索引
                        column_to_delete_index = header.index('tokens')
                        # 创建一个新的 CSV 文件，并写入标题行
                        with open('/Applications/Broccoli.app/Contents/Resources/with_embeddings2.csv', 'w', newline='', encoding='utf-8') as output_file:
                            writer = csv.writer(output_file)
                            writer.writerow([h for h in header if h != 'tokens'])
                            # 遍历 CSV 文件的每一行，并删除要删除的列
                            for row in reader:
                                del row[column_to_delete_index]
                                writer.writerow(row)
                    cf = codecs.open('/Applications/Broccoli.app/Contents/Resources/with_embeddings2.csv', 'r', encoding='utf-8').read()
                    cf = cf.replace('[', '')
                    cf = cf.replace(']', '')
                    cf = cf.replace('"', '')
                    cfline = cf.split('\n')
                    lenline = []
                    for i in range(len(cfline)):
                        lenline.append(len(cfline[i].split(',')) - 3)
                    lenline.sort()
                    num = lenline[-1]
                    listnum = []
                    for r in range(num):
                        listnum.append(r)
                    for m in range(len(listnum)):
                        listnum[m] = str(listnum[m])
                    liststr = ','.join(listnum)
                    del cfline[0]
                    cfstr = '\n'.join(cfline)
                    cfstr = 'title,heading,content,' + liststr + '\n' + cfstr
                    with open('/Applications/Broccoli.app/Contents/Resources/with_embeddings3.csv', 'w', encoding='utf-8') as f0:
                        f0.write(cfstr)
                    # 读取 CSV 文件
                    with open('/Applications/Broccoli.app/Contents/Resources/with_embeddings3.csv', 'r', encoding='utf-8') as input_file:
                        reader = csv.reader(input_file)
                        # 获取 CSV 文件的标题行
                        header = next(reader)
                        # 获取要删除的列的索引
                        column_to_delete_index = header.index('content')
                        # 创建一个新的 CSV 文件，并写入标题行
                        with open(embedcsv, 'w', newline='', encoding='utf-8') as output_file:
                            writer = csv.writer(output_file)
                            writer.writerow([h for h in header if h != 'content'])
                            # 遍历 CSV 文件的每一行，并删除要删除的列
                            for row in reader:
                                del row[column_to_delete_index]
                                writer.writerow(row)
                    SUCC = 1
                except Exception as e:
                    SUCC = 0
                    with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a', encoding='utf-8') as f1:
                        f1.write(f'- Q: Please embed {contfull}.\n\n- A: Error! {str(e)} Please try again!' + '\n\n---\n\n')
                    AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read()
                    endhtml = self.md2html(AllText)
                    self.real1.setHtml(endhtml)
                    self.real1.ensureCursorVisible()  # 游标可用
                    cursor = self.real1.textCursor()  # 设置游标
                    pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    self.real1.setTextCursor(cursor)  # 滚动到游标位置
                # display
                if SUCC == 1:
                    with open('/Applications/Broccoli.app/Contents/Resources/title.txt', 'w', encoding='utf-8') as f0:
                        f0.write(cont)
                    with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a', encoding='utf-8') as f1:
                        f1.write(f'\n\n\t**Done!**' + '\n\n---\n\n')
                    AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r',
                                          encoding='utf-8').read()
                    endhtml = self.md2html(AllText)
                    self.real1.setHtml(endhtml)
                    self.real1.ensureCursorVisible()  # 游标可用
                    cursor = self.real1.textCursor()  # 设置游标
                    pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    self.real1.setTextCursor(cursor)  # 滚动到游标位置
            if bear != '' and api2 != '' and thirdp == '1':
                ENDPOINT = bear + '/v1/embeddings'
                AccountGPT = api2
                HEADERS = {"Authorization": f"Bearer {AccountGPT}"}
                SUCC = 0
                tarnamecsv = csv_tarname
                embedcsv = os.path.join(self.Embed, csv_endtar)
                try:
                    with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a',
                              encoding='utf-8') as f1:
                        f1.write(f'- Q: Please embed {tarname}.\n\n- A: ')
                    AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r',
                                          encoding='utf-8').read()
                    endhtml = self.md2html(AllText)
                    self.real1.setHtml(endhtml)
                    self.real1.ensureCursorVisible()  # 游标可用
                    cursor = self.real1.textCursor()  # 设置游标
                    pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    self.real1.setTextCursor(cursor)  # 滚动到游标位置

                    # midindex to embed
                    EMBEDDING_MODEL = "text-embedding-ada-002"
                    openai.api_key = AccountGPT
                    df = pd.read_csv(tarnamecsv)
                    df = df.set_index(["title", "heading"])
                    df.sample(1)
                    with open('/Applications/Broccoli.app/Contents/Resources/prog.txt', 'w', encoding='utf-8') as f0:
                        f0.write('')

                    def get_embedding(text: str, model: str = EMBEDDING_MODEL, nowline=0, allline=allline) -> list[
                        float]:
                        data = {
                            "model": model,
                            "input": text,
                        }
                        response = requests.post(ENDPOINT, json=data, headers=HEADERS, timeout=60.0)

                        with open('/Applications/Broccoli.app/Contents/Resources/prog.txt', 'a',
                                  encoding='utf-8') as f0:
                            f0.write('1\n')
                        prog = codecs.open('/Applications/Broccoli.app/Contents/Resources/prog.txt', 'r',
                                           encoding='utf-8').read()
                        proglist = prog.split('\n')
                        while '' in proglist:
                            proglist.remove('')
                        nowline += len(proglist)
                        prognum = str(int(nowline / allline * 100)) + '%'
                        with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a',
                                  encoding='utf-8') as f1:
                            f1.write(f'{prognum}...')
                        AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r',
                                              encoding='utf-8').read()
                        endhtml = self.md2html(AllText)
                        self.real1.setHtml(endhtml)
                        self.real1.ensureCursorVisible()  # 游标可用
                        cursor = self.real1.textCursor()  # 设置游标
                        pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                        cursor.setPosition(pos)  # 游标位置设置为尾部
                        self.real1.setTextCursor(cursor)  # 滚动到游标位置
                        time.sleep(0.5)
                        # Process the API response
                        if response.status_code == 200:
                            response_data = response.json()
                            chat_output = response_data["data"][0]["embedding"]
                            return chat_output
                        else:
                            raise Exception(f"API call failed with status code {response.status_code}: {response.text}")

                    df["embedding"] = df.content.apply(lambda x: get_embedding(x, EMBEDDING_MODEL))
                    df.to_csv('/Applications/Broccoli.app/Contents/Resources/with_embeddings.csv')
                    with open('/Applications/Broccoli.app/Contents/Resources/with_embeddings.csv', 'r',
                              encoding='utf-8') as input_file:
                        reader = csv.reader(input_file)
                        # 获取 CSV 文件的标题行
                        header = next(reader)
                        # 获取要删除的列的索引
                        column_to_delete_index = header.index('tokens')
                        # 创建一个新的 CSV 文件，并写入标题行
                        with open('/Applications/Broccoli.app/Contents/Resources/with_embeddings2.csv', 'w', newline='',
                                  encoding='utf-8') as output_file:
                            writer = csv.writer(output_file)
                            writer.writerow([h for h in header if h != 'tokens'])
                            # 遍历 CSV 文件的每一行，并删除要删除的列
                            for row in reader:
                                del row[column_to_delete_index]
                                writer.writerow(row)
                    cf = codecs.open('/Applications/Broccoli.app/Contents/Resources/with_embeddings2.csv', 'r',
                                     encoding='utf-8').read()
                    cf = cf.replace('[', '')
                    cf = cf.replace(']', '')
                    cf = cf.replace('"', '')
                    cfline = cf.split('\n')
                    lenline = []
                    for i in range(len(cfline)):
                        lenline.append(len(cfline[i].split(',')) - 3)
                    lenline.sort()
                    num = lenline[-1]
                    listnum = []
                    for r in range(num):
                        listnum.append(r)
                    for m in range(len(listnum)):
                        listnum[m] = str(listnum[m])
                    liststr = ','.join(listnum)
                    del cfline[0]
                    cfstr = '\n'.join(cfline)
                    cfstr = 'title,heading,content,' + liststr + '\n' + cfstr
                    with open('/Applications/Broccoli.app/Contents/Resources/with_embeddings3.csv', 'w',
                              encoding='utf-8') as f0:
                        f0.write(cfstr)
                    # 读取 CSV 文件
                    with open('/Applications/Broccoli.app/Contents/Resources/with_embeddings3.csv', 'r',
                              encoding='utf-8') as input_file:
                        reader = csv.reader(input_file)
                        # 获取 CSV 文件的标题行
                        header = next(reader)
                        # 获取要删除的列的索引
                        column_to_delete_index = header.index('content')
                        # 创建一个新的 CSV 文件，并写入标题行
                        with open(embedcsv, 'w', newline='', encoding='utf-8') as output_file:
                            writer = csv.writer(output_file)
                            writer.writerow([h for h in header if h != 'content'])
                            # 遍历 CSV 文件的每一行，并删除要删除的列
                            for row in reader:
                                del row[column_to_delete_index]
                                writer.writerow(row)
                    SUCC = 1
                except Exception as e:
                    SUCC = 0
                    with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a', encoding='utf-8') as f1:
                        f1.write(
                            f'- Q: Please embed {contfull}.\n\n- A: Error! {str(e)} Please try again!' + '\n\n---\n\n')
                    AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r',
                                          encoding='utf-8').read()
                    endhtml = self.md2html(AllText)
                    self.real1.setHtml(endhtml)
                    self.real1.ensureCursorVisible()  # 游标可用
                    cursor = self.real1.textCursor()  # 设置游标
                    pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    self.real1.setTextCursor(cursor)  # 滚动到游标位置
                # display
                if SUCC == 1:
                    with open('/Applications/Broccoli.app/Contents/Resources/title.txt', 'w', encoding='utf-8') as f0:
                        f0.write(cont)
                    with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a', encoding='utf-8') as f1:
                        f1.write(f'\n\n\t**Done!**' + '\n\n---\n\n')
                    AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r',
                                          encoding='utf-8').read()
                    endhtml = self.md2html(AllText)
                    self.real1.setHtml(endhtml)
                    self.real1.ensureCursorVisible()  # 游标可用
                    cursor = self.real1.textCursor()  # 设置游标
                    pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    self.real1.setTextCursor(cursor)  # 滚动到游标位置

    def openfronold(self):
        fj = QFileDialog.getOpenFileName(self, "Open File", self.Local, "Text Files (*.txt)")
        if fj[0] != '' and 'Local' in fj[0]:
            # display in widget
            str_fj = ''.join(fj)
            str_fj = str_fj.replace('Text Files (*.txt)', '')
            text_his = codecs.open(str_fj, 'r', encoding='utf-8').read()
            self.te0.setText(text_his)
            # save title
            contlist = str_fj.split('/')
            cont = contlist[len(contlist) - 1].replace('.txt', '')
            contfull = cont + '.txt'
            tarname = os.path.join(self.Local, contfull)
            if not os.path.exists(tarname):
                with open(tarname, 'a', encoding='utf-8') as f0:
                    f0.write('')
            with open('/Applications/Broccoli.app/Contents/Resources/title.txt', 'w', encoding='utf-8') as f0:
                f0.write(cont)
            # display
            with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a', encoding='utf-8') as f1:
                f1.write(f'- Q: Please embed {contfull}.\n\n- A: Done!' + '\n\n---\n\n')
            AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r',
                                  encoding='utf-8').read()
            endhtml = self.md2html(AllText)
            self.real1.setHtml(endhtml)
            self.real1.ensureCursorVisible()  # 游标可用
            cursor = self.real1.textCursor()  # 设置游标
            pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
            cursor.setPosition(pos)  # 游标位置设置为尾部
            self.real1.setTextCursor(cursor)  # 滚动到游标位置

    def openfrominput(self):
        if self.te0.toPlainText() != '':
            # save to Local
            ISOTIMEFORMAT = '%Y%m%d %H-%M-%S-%f'
            theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
            tarname = theTime + " GPTinput.txt"
            fulldir = os.path.join(self.Local, tarname)
            with open(fulldir, 'w', encoding='utf-8') as f1:
                f1.write(self.te0.toPlainText())
            # save the title
            with open('/Applications/Broccoli.app/Contents/Resources/title.txt', 'w', encoding='utf-8') as f0:
                f0.write('')

            plain_list = self.te0.toPlainText().split('\n')
            while '' in plain_list:
                plain_list.remove('')
            for i in range(len(plain_list)):
                aj = jieba.cut(plain_list[i], cut_all=False)
                paj = '/'.join(aj)
                saj = paj.split('/')
                if len(saj) > 200:
                    times = int(len(saj) / 200) + 1
                    temp = ''
                    tm = 1
                    if tm == 1:
                        ter = saj[0:199]
                        tarstr = ' '.join(ter) + '✡'
                        temp = temp + tarstr
                        tm += 1
                    while 1 < tm <= times - 1:
                        ter = saj[(tm - 1) * 200 - 1:tm * 200 - 1]
                        tarstr = ' '.join(ter) + '✡'
                        temp = temp + tarstr
                        tm += 1
                    if tm == times:
                        ter = saj[(tm - 1) * 200 - 1:]
                        tarstr = ' '.join(ter) + '✡'
                        temp = temp + tarstr
                    plain_list[i] = temp
            for n in range(len(plain_list)):
                plain_list[n] = self.default_clean(self.cleanlinebreak(plain_list[n]))
            plain_list = list(filter(None, plain_list))
            end_text = '✡'.join(plain_list)
            end_text = end_text.replace('✡✡', '✡')
            for i in range(10):
                end_text = end_text.replace('   ', ' ')
                end_text = end_text.replace('  ', ' ')
            end_text = end_text.replace('\n', '')
            end_text = end_text.replace('✡', '\n\n')
            self.te0.setText(end_text)
            with open(fulldir, 'w', encoding='utf-8') as f0:
                f0.write(end_text)
            # produce Index.csv
            csv_line = end_text.replace(',', ';').split('\n\n')
            while '' in csv_line:
                csv_line.remove('')
            allline = len(csv_line)
            for x in range(len(csv_line)):
                csv_line[x] = "A" + ',' + str(x) + ',' + csv_line[x]
            csvtext = '\n'.join(csv_line)
            csvtext = 'title,heading,content\n' + csvtext
            csv_endtar = tarname.replace('.txt', '') + '.csv'
            csv_tarname = os.path.join(self.Index, csv_endtar)
            with open(csv_tarname, 'w', encoding='utf-8') as f0:
                f0.write(csvtext)
            tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
            # 打开 CSV 文件并读取数据
            with open(csv_tarname, mode='r', encoding='utf-8') as csv_file:
                csv_reader = csv.reader(csv_file)
                rows = list(csv_reader)
            # 在数据中添加新列
            header = rows[0]
            header.append('tokens')
            for row in rows[1:]:
                tar = row[-1]
                A = tokenizer.encode(tar, add_special_tokens=True)
                if len(A) <= 1024:
                    row.append(str(len(A)))
                else:
                    row.append(str(1024))
            # 将更新后的数据写回 CSV 文件
            with open(csv_tarname, mode='w', newline='', encoding='utf-8') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(header)
                csv_writer.writerows(rows[1:])
            # delete those which are too long
            cleanlong = codecs.open(csv_tarname, 'r', encoding='utf-8').read()
            cleanlong = cleanlong.replace('\r', '')
            cleanlong_list = cleanlong.split('\n')
            while '' in cleanlong_list:
                cleanlong_list.remove('')
            del cleanlong_list[0]
            lostlist = []
            for f in range(len(cleanlong_list)):
                pattern = re.compile(r',(\d+)$')
                result = pattern.findall(cleanlong_list[f])
                if result != []:
                    realnum = int(''.join(result))
                    if realnum >= 1024:
                        lostlist.append(cleanlong_list[f])
            reallist = list(set(cleanlong_list) - set(lostlist))
            realcsv = '\n'.join(reallist)
            realcsv = 'title,heading,content,tokens\n' + realcsv
            with open(csv_tarname, 'w', encoding='utf-8') as f0:
                f0.write(realcsv)
            # produce Embed.csv
            AccountGPT = codecs.open('/Applications/Broccoli.app/Contents/Resources/api.txt', 'r',
                                     encoding='utf-8').read()
            api2 = codecs.open('/Applications/Broccoli.app/Contents/Resources/api2.txt', 'r',
                               encoding='utf-8').read()
            bear = codecs.open('/Applications/Broccoli.app/Contents/Resources/bear.txt', 'r',
                               encoding='utf-8').read()
            thirdp = codecs.open('/Applications/Broccoli.app/Contents/Resources/third.txt', 'r',
                                 encoding='utf-8').read()
            if AccountGPT != '' and thirdp == '0':
                SUCC = 0
                tarnamecsv = csv_tarname
                embedcsv = os.path.join(self.Embed, csv_endtar)
                try:
                    with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a',
                              encoding='utf-8') as f1:
                        f1.write(f'- Q: Please embed {tarname}.\n\n- A: ')
                    AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r',
                                          encoding='utf-8').read()
                    endhtml = self.md2html(AllText)
                    self.real1.setHtml(endhtml)
                    self.real1.ensureCursorVisible()  # 游标可用
                    cursor = self.real1.textCursor()  # 设置游标
                    pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    self.real1.setTextCursor(cursor)  # 滚动到游标位置

                    # midindex to embed
                    EMBEDDING_MODEL = "text-embedding-ada-002"
                    openai.api_key = AccountGPT
                    df = pd.read_csv(tarnamecsv)
                    df = df.set_index(["title", "heading"])
                    df.sample(1)
                    with open('/Applications/Broccoli.app/Contents/Resources/prog.txt', 'w', encoding='utf-8') as f0:
                        f0.write('')

                    def get_embedding(text: str, model: str = EMBEDDING_MODEL, nowline=0, allline=allline) -> list[float]:
                        result = openai.Embedding.create(
                            model=model,
                            input=text
                        )
                        QApplication.processEvents()
                        QApplication.restoreOverrideCursor()
                        with open('/Applications/Broccoli.app/Contents/Resources/prog.txt', 'a', encoding='utf-8') as f0:
                            f0.write('1\n')
                        prog = codecs.open('/Applications/Broccoli.app/Contents/Resources/prog.txt', 'r', encoding='utf-8').read()
                        proglist = prog.split('\n')
                        while '' in proglist:
                            proglist.remove('')
                        nowline += len(proglist)
                        prognum = str(int(nowline / allline * 100)) + '%'
                        with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a',
                                  encoding='utf-8') as f1:
                            f1.write(f'{prognum}...')
                        AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r',
                                              encoding='utf-8').read()
                        endhtml = self.md2html(AllText)
                        self.real1.setHtml(endhtml)
                        self.real1.ensureCursorVisible()  # 游标可用
                        cursor = self.real1.textCursor()  # 设置游标
                        pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                        cursor.setPosition(pos)  # 游标位置设置为尾部
                        self.real1.setTextCursor(cursor)  # 滚动到游标位置
                        time.sleep(0.5)
                        return result["data"][0]["embedding"]

                    df["embedding"] = df.content.apply(lambda x: get_embedding(x, EMBEDDING_MODEL))
                    df.to_csv('/Applications/Broccoli.app/Contents/Resources/with_embeddings.csv')
                    with open('/Applications/Broccoli.app/Contents/Resources/with_embeddings.csv', 'r',
                              encoding='utf-8') as input_file:
                        reader = csv.reader(input_file)
                        # 获取 CSV 文件的标题行
                        header = next(reader)
                        # 获取要删除的列的索引
                        column_to_delete_index = header.index('tokens')
                        # 创建一个新的 CSV 文件，并写入标题行
                        with open('/Applications/Broccoli.app/Contents/Resources/with_embeddings2.csv', 'w',
                                  newline='', encoding='utf-8') as output_file:
                            writer = csv.writer(output_file)
                            writer.writerow([h for h in header if h != 'tokens'])
                            # 遍历 CSV 文件的每一行，并删除要删除的列
                            for row in reader:
                                del row[column_to_delete_index]
                                writer.writerow(row)
                    cf = codecs.open('/Applications/Broccoli.app/Contents/Resources/with_embeddings2.csv', 'r',
                                     encoding='utf-8').read()
                    cf = cf.replace('[', '')
                    cf = cf.replace(']', '')
                    cf = cf.replace('"', '')
                    cfline = cf.split('\n')
                    lenline = []
                    for i in range(len(cfline)):
                        lenline.append(len(cfline[i].split(',')) - 3)
                    lenline.sort()
                    num = lenline[-1]
                    listnum = []
                    for r in range(num):
                        listnum.append(r)
                    for m in range(len(listnum)):
                        listnum[m] = str(listnum[m])
                    liststr = ','.join(listnum)
                    del cfline[0]
                    cfstr = '\n'.join(cfline)
                    cfstr = 'title,heading,content,' + liststr + '\n' + cfstr
                    with open('/Applications/Broccoli.app/Contents/Resources/with_embeddings3.csv', 'w',
                              encoding='utf-8') as f0:
                        f0.write(cfstr)
                    # 读取 CSV 文件
                    with open('/Applications/Broccoli.app/Contents/Resources/with_embeddings3.csv', 'r',
                              encoding='utf-8') as input_file:
                        reader = csv.reader(input_file)
                        # 获取 CSV 文件的标题行
                        header = next(reader)
                        # 获取要删除的列的索引
                        column_to_delete_index = header.index('content')
                        # 创建一个新的 CSV 文件，并写入标题行
                        with open(embedcsv, 'w', newline='', encoding='utf-8') as output_file:
                            writer = csv.writer(output_file)
                            writer.writerow([h for h in header if h != 'content'])
                            # 遍历 CSV 文件的每一行，并删除要删除的列
                            for row in reader:
                                del row[column_to_delete_index]
                                writer.writerow(row)
                    SUCC = 1
                except Exception as e:
                    SUCC = 0
                    with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a',
                              encoding='utf-8') as f1:
                        f1.write(
                            f'- Q: Please embed {tarname}.\n\n- A: Error! {str(e)} Please try again!' + '\n\n---\n\n')
                    AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r',
                                          encoding='utf-8').read()
                    endhtml = self.md2html(AllText)
                    self.real1.setHtml(endhtml)
                    self.real1.ensureCursorVisible()  # 游标可用
                    cursor = self.real1.textCursor()  # 设置游标
                    pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    self.real1.setTextCursor(cursor)  # 滚动到游标位置
                # display
                if SUCC == 1:
                    with open('/Applications/Broccoli.app/Contents/Resources/title.txt', 'w', encoding='utf-8') as f0:
                        f0.write(tarname.replace('.txt', ''))
                    with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a',
                              encoding='utf-8') as f1:
                        f1.write(f'\n\n\t**Done!**' + '\n\n---\n\n')
                    AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r',
                                          encoding='utf-8').read()
                    endhtml = self.md2html(AllText)
                    self.real1.setHtml(endhtml)
                    self.real1.ensureCursorVisible()  # 游标可用
                    cursor = self.real1.textCursor()  # 设置游标
                    pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    self.real1.setTextCursor(cursor)  # 滚动到游标位置
            if bear != '' and api2 != '' and thirdp == '1':
                ENDPOINT = bear + '/v1/embeddings'
                AccountGPT = api2
                HEADERS = {"Authorization": f"Bearer {AccountGPT}"}
                SUCC = 0
                tarnamecsv = csv_tarname
                embedcsv = os.path.join(self.Embed, csv_endtar)
                try:
                    with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a',
                              encoding='utf-8') as f1:
                        f1.write(f'- Q: Please embed {tarname}.\n\n- A: ')
                    AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r',
                                          encoding='utf-8').read()
                    endhtml = self.md2html(AllText)
                    self.real1.setHtml(endhtml)
                    self.real1.ensureCursorVisible()  # 游标可用
                    cursor = self.real1.textCursor()  # 设置游标
                    pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    self.real1.setTextCursor(cursor)  # 滚动到游标位置

                    # midindex to embed
                    EMBEDDING_MODEL = "text-embedding-ada-002"
                    openai.api_key = AccountGPT
                    df = pd.read_csv(tarnamecsv)
                    df = df.set_index(["title", "heading"])
                    df.sample(1)
                    with open('/Applications/Broccoli.app/Contents/Resources/prog.txt', 'w', encoding='utf-8') as f0:
                        f0.write('')

                    def get_embedding(text: str, model: str = EMBEDDING_MODEL, nowline=0, allline=allline) -> list[
                        float]:
                        data = {
                            "model": model,
                            "input": text,
                        }
                        response = requests.post(ENDPOINT, json=data, headers=HEADERS, timeout=60.0)

                        with open('/Applications/Broccoli.app/Contents/Resources/prog.txt', 'a',
                                  encoding='utf-8') as f0:
                            f0.write('1\n')
                        prog = codecs.open('/Applications/Broccoli.app/Contents/Resources/prog.txt', 'r',
                                           encoding='utf-8').read()
                        proglist = prog.split('\n')
                        while '' in proglist:
                            proglist.remove('')
                        nowline += len(proglist)
                        prognum = str(int(nowline / allline * 100)) + '%'
                        with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a',
                                  encoding='utf-8') as f1:
                            f1.write(f'{prognum}...')
                        AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r',
                                              encoding='utf-8').read()
                        endhtml = self.md2html(AllText)
                        self.real1.setHtml(endhtml)
                        self.real1.ensureCursorVisible()  # 游标可用
                        cursor = self.real1.textCursor()  # 设置游标
                        pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                        cursor.setPosition(pos)  # 游标位置设置为尾部
                        self.real1.setTextCursor(cursor)  # 滚动到游标位置
                        time.sleep(0.5)
                        # Process the API response
                        if response.status_code == 200:
                            response_data = response.json()
                            chat_output = response_data["data"][0]["embedding"]
                            return chat_output
                        else:
                            raise Exception(f"API call failed with status code {response.status_code}: {response.text}")

                    df["embedding"] = df.content.apply(lambda x: get_embedding(x, EMBEDDING_MODEL))
                    df.to_csv('/Applications/Broccoli.app/Contents/Resources/with_embeddings.csv')
                    with open('/Applications/Broccoli.app/Contents/Resources/with_embeddings.csv', 'r',
                              encoding='utf-8') as input_file:
                        reader = csv.reader(input_file)
                        # 获取 CSV 文件的标题行
                        header = next(reader)
                        # 获取要删除的列的索引
                        column_to_delete_index = header.index('tokens')
                        # 创建一个新的 CSV 文件，并写入标题行
                        with open('/Applications/Broccoli.app/Contents/Resources/with_embeddings2.csv', 'w', newline='',
                                  encoding='utf-8') as output_file:
                            writer = csv.writer(output_file)
                            writer.writerow([h for h in header if h != 'tokens'])
                            # 遍历 CSV 文件的每一行，并删除要删除的列
                            for row in reader:
                                del row[column_to_delete_index]
                                writer.writerow(row)
                    cf = codecs.open('/Applications/Broccoli.app/Contents/Resources/with_embeddings2.csv', 'r',
                                     encoding='utf-8').read()
                    cf = cf.replace('[', '')
                    cf = cf.replace(']', '')
                    cf = cf.replace('"', '')
                    cfline = cf.split('\n')
                    lenline = []
                    for i in range(len(cfline)):
                        lenline.append(len(cfline[i].split(',')) - 3)
                    lenline.sort()
                    num = lenline[-1]
                    listnum = []
                    for r in range(num):
                        listnum.append(r)
                    for m in range(len(listnum)):
                        listnum[m] = str(listnum[m])
                    liststr = ','.join(listnum)
                    del cfline[0]
                    cfstr = '\n'.join(cfline)
                    cfstr = 'title,heading,content,' + liststr + '\n' + cfstr
                    with open('/Applications/Broccoli.app/Contents/Resources/with_embeddings3.csv', 'w',
                              encoding='utf-8') as f0:
                        f0.write(cfstr)
                    # 读取 CSV 文件
                    with open('/Applications/Broccoli.app/Contents/Resources/with_embeddings3.csv', 'r',
                              encoding='utf-8') as input_file:
                        reader = csv.reader(input_file)
                        # 获取 CSV 文件的标题行
                        header = next(reader)
                        # 获取要删除的列的索引
                        column_to_delete_index = header.index('content')
                        # 创建一个新的 CSV 文件，并写入标题行
                        with open(embedcsv, 'w', newline='', encoding='utf-8') as output_file:
                            writer = csv.writer(output_file)
                            writer.writerow([h for h in header if h != 'content'])
                            # 遍历 CSV 文件的每一行，并删除要删除的列
                            for row in reader:
                                del row[column_to_delete_index]
                                writer.writerow(row)
                    SUCC = 1
                except Exception as e:
                    SUCC = 0
                    with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a',
                              encoding='utf-8') as f1:
                        f1.write(
                            f'- Q: Please embed {tarname}.\n\n- A: Error! {str(e)} Please try again!' + '\n\n---\n\n')
                    AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r',
                                          encoding='utf-8').read()
                    endhtml = self.md2html(AllText)
                    self.real1.setHtml(endhtml)
                    self.real1.ensureCursorVisible()  # 游标可用
                    cursor = self.real1.textCursor()  # 设置游标
                    pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    self.real1.setTextCursor(cursor)  # 滚动到游标位置
                # display
                if SUCC == 1:
                    with open('/Applications/Broccoli.app/Contents/Resources/title.txt', 'w', encoding='utf-8') as f0:
                        f0.write(tarname.replace('.txt', ''))
                    with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'a',
                              encoding='utf-8') as f1:
                        f1.write(f'\n\n\t**Done!**' + '\n\n---\n\n')
                    AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r',
                                          encoding='utf-8').read()
                    endhtml = self.md2html(AllText)
                    self.real1.setHtml(endhtml)
                    self.real1.ensureCursorVisible()  # 游标可用
                    cursor = self.real1.textCursor()  # 设置游标
                    pos = len(self.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    self.real1.setTextCursor(cursor)  # 滚动到游标位置

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

    def pin_a_tab(self):
        SCREEN_WEIGHT = int(self.screen().availableGeometry().width())
        SCREEN_HEIGHT = int(self.screen().availableGeometry().height())
        x_center = 0
        y_center = 0
        if self.i % 2 == 1:
            btna4.setChecked(True)
            self.btn_00.setText('')
            self.btn_00.setFixedHeight(10)
            self.btn_00.setFixedWidth(500)
            self.btn_00.setStyleSheet('''
                        border: 1px outset grey;
                        background-color: #0085FF;
                        border-radius: 4px;
                        padding: 1px;
                        color: #FFFFFF''')
            self.qw3.setVisible(True)
            self.setFixedSize(500, 830)
            x_center = int((SCREEN_WEIGHT / 2) + (self.width() / 2))
            y_center = int((SCREEN_HEIGHT - self.height()) // 4 * 3)
        if self.i % 2 == 0:
            btna4.setChecked(False)
            self.btn_00.setText('🥦')
            self.btn_00.setFixedSize(50, 50)
            self.btn_00.setStyleSheet('''
                        border: 1px outset grey;
                        background-color: #FFFFFF;
                        border-radius: 25px;
                        padding: 1px;
                        color: #000000''')
            self.qw3.setVisible(False)
            self.setFixedSize(50, 50)
            x_center = int(SCREEN_WEIGHT - 50)
            y_center = int(SCREEN_HEIGHT - 50)

        self.move_window(x_center, y_center)
        self.show()

    def cleanlinebreak(self, a):  # 设置清除断行的基本代码块
        for i in range(10):
            a = a.replace('\r', ' ')
            a = a.replace('\n', ' ')
        a = a.replace('   ', ' ')
        a = a.replace('  ', ' ')
        return a

    def default_clean(self, a):  # 最基本功能块
        # 【共同块】不管是全中文/全英文/中英混排，都需要清除的不规范的符号与排版
        # 清除文档排版符号
        a = a.replace('\t', '')

        # 清除连续空格（如连续两个和三个空格）
        for i in range(10):
            a = a.replace('   ', ' ')
            a = a.replace('  ', ' ')
            a = a.replace('，，，', '，')
            a = a.replace('，，', '，')
            a = a.replace(',,,', ',')
            a = a.replace(',,', ',')

        # 清除那些引用标记（括号内为纯数字），如圈圈数字和方括号引用，同时由于方括号和六角括号混用较多，清理前后不搭的情况中的引用符号
        a = re.sub(r"\{(\s)*(\d+\s)*(\d)*?\}|\[(\s)*(\d+\s)*(\d)*?\]|〔(\s)*(\d+\s)*(\d)*?〕|﹝(\s)*(\d+\s)*(\d)*?﹞", "", a)
        a = re.sub(r"\[(\s)*(\d+\s)*(\d)*?〕|\[(\s)*(\d+\s)*(\d)*?﹞|〔(\s)*(\d+\s)*(\d)*?\]|〔(\s)*(\d+\s)*(\d)*?﹞|﹝(\s)*(\d+\s)*(\d)*?\]|﹝(\s)*(\d+\s)*(\d)*?〕", "", a)
        a = re.sub(r"（(\s)*(\d+\s)*(\d)*?）|\[(\s)*(\d+\s)*(\d)*?）|（(\s)*(\d+\s)*(\d)*?\]|（(\s)*(\d+\s)*(\d)*?】|【(\s)*(\d+\s)*(\d)*?）", "", a)
        a = re.sub(r"\((\s)*(\d+\s)*(\d)*?〕|\((\s)*(\d+\s)*(\d)*?﹞|〔(\s)*(\d+\s)*(\d)*?\)|﹝(\s)*(\d+\s)*(\d)*?\)|\((\s)*(\d+\s)*(\d)*?\)|\[(\s)*(\d+\s)*(\d)*?\)|\((\s)*(\d+\s)*(\d)*?\]", "", a)
        a = re.sub(u'\u24EA|[\u2460-\u2473]|[\u3251-\u325F]|[\u32B1-\u32BF]|[\u2776-\u277F]|\u24FF|[\u24EB-\u24F4]',
                   "", a)
        a = re.sub(r"\<(\s)*(\d+\s)*(\d)*?\>|\《(\s)*(\d+\s)*(\d)*?\》|\〈(\s)*(\d+\s)*(\d)*?\〉|\＜(\s)*(\d+\s)*(\d)*?\＞", "", a)
        a = re.sub(r"\<(\s)*(\d+\s)*(\d)*?\》|\<(\s)*(\d+\s)*(\d)*?\〉|\<(\s)*(\d+\s)*(\d)*?\＞",
                   "", a)
        a = re.sub(r"\《(\s)*(\d+\s)*(\d)*?\>|\《(\s)*(\d+\s)*(\d)*?\〉|\《(\s)*(\d+\s)*(\d)*?\＞",
                   "", a)
        a = re.sub(r"\〈(\s)*(\d+\s)*(\d)*?\>|\〈(\s)*(\d+\s)*(\d)*?\》|\〈(\s)*(\d+\s)*(\d)*?\＞",
                   "", a)
        a = re.sub(r"\＜(\s)*(\d+\s)*(\d)*?\>|\＜(\s)*(\d+\s)*(\d)*?\》|\＜(\s)*(\d+\s)*(\d)*?\〉",
                   "", a)
        a = a.replace('◎', '')
        a = a.replace('®', '')
        a = a.replace('*', '')

        # 错误标点纠正：将奇怪的弯引号换为正常的弯引号，为下面执行弯引号与直引号的清除提供条件
        a = a.replace('〞', '”')
        a = a.replace('〝', '“')

        # 错误标点纠正：将角分符号（′）替换为弯引号（若需要使用角分符号则不运行此条）
        a = a.replace('′', "’")
        # 错误标点纠正：将角秒符号（″）替换为弯引号（若需要使用角秒符号则不运行此条）
        a = a.replace('″', '”')

        # 错误标点纠正1（两个同向单引号变成一个双引号<前>，改为前后弯双引号）
        pattern = re.compile(r'‘‘(.*?)”')
        result = pattern.findall(a)
        for i in result:
            a = a.replace('‘‘{}”'.format(i), '“{}”'.format(i))

        # 错误标点纠正2（两个同向单引号变成一个双引号<后>，改为前后弯双引号）
        p1 = r"(?<=“).+?(?=’’)"
        pattern1 = re.compile(p1)
        result = pattern1.findall(a)
        for i in result:
            a = a.replace('“{}’’'.format(i), '“{}”'.format(i))

        # 错误标点纠正3（前后两个单引号变成一组双引号）
        pattern = re.compile(r'‘‘(.*?)’’')
        result = pattern.findall(a)
        for i in result:
            a = a.replace('‘‘{}’’'.format(i), '“{}”'.format(i))

        # 错误标点纠正4（两个同向双引号去掉一个<前>）
        pattern = re.compile(r'““(.*?)”')
        result = pattern.findall(a)
        for i in result:
            a = a.replace('““{}”'.format(i), '“{}”'.format(i))

        # 错误标点纠正5（两个同向双引号去掉一个<后>）
        p1 = r"(?<=“).+?(?=””)"
        pattern1 = re.compile(p1)
        result = pattern1.findall(a)
        for i in result:
            a = a.replace('“{}””'.format(i), '“{}”'.format(i))

        # 错误标点纠正6（两组双引号变成一组双引号）
        pattern = re.compile(r'““(.*?)””')
        result = pattern.findall(a)
        for i in result:
            a = a.replace('““{}””'.format(i), '“{}”'.format(i))

        # 错误标点纠正7（前直单引号<前>，后弯双引号<后>，改为前后弯双引号）
        pattern = re.compile(r"'(.*?)”")
        result = pattern.findall(a)
        for i in result:
            a = a.replace("'{}”".format(i), '“{}”'.format(i))

        # 错误标点纠正8（前直双引号<前>，后弯双引号<后>，改为前后弯双引号）
        pattern = re.compile(r'"(.*?)”')
        result = pattern.findall(a)
        for i in result:
            a = a.replace('"{}”'.format(i), '“{}”'.format(i))

        # 错误标点纠正9（前弯双引号<前>，后直单引号<后>，改为前后弯双引号）
        p1 = r"(?<=“).+?(?=')"
        pattern1 = re.compile(p1)
        result = pattern1.findall(a)
        for i in result:
            a = a.replace("“{}'".format(i), '“{}”'.format(i))

        # 错误标点纠正10（前弯双引号<前>，后直双引号<后>，改为前后弯双引号）
        p1 = r'(?<=“).+?(?=")'
        pattern1 = re.compile(p1)
        result = pattern1.findall(a)
        for i in result:
            a = a.replace('“{}"'.format(i), '“{}”'.format(i))

        # 将成对的直双引号改为成对的弯双引号
        pattern = re.compile(r'"(.*?)"')
        result = pattern.findall(a)
        for i in result:
            a = a.replace('"{}"'.format(i), '“{}”'.format(i))

        # 将成对的直单引号改为成对的弯单引号
        pattern = re.compile(r"'(.*?)'")
        result = pattern.findall(a)
        for i in result:
            a = a.replace("'{}'".format(i), "‘{}’".format(i))

        # 对文段进行再次多余部分的清洗
        # 错误标点纠正1（两个同向单引号变成一个双引号<前>，改为前后弯双引号）
        pattern = re.compile(r'‘‘(.*?)”')
        result = pattern.findall(a)
        for i in result:
            a = a.replace('‘‘{}”'.format(i), '“{}”'.format(i))

        # 错误标点纠正2（两个同向单引号变成一个双引号<后>，改为前后弯双引号）
        p1 = r"(?<=“).+?(?=’’)"
        pattern1 = re.compile(p1)
        result = pattern1.findall(a)
        for i in result:
            a = a.replace('“{}’’'.format(i), '“{}”'.format(i))

        # 错误标点纠正3（前后两个单引号变成一组双引号）
        pattern = re.compile(r'‘‘(.*?)’’')
        result = pattern.findall(a)
        for i in result:
            a = a.replace('‘‘{}’’'.format(i), '“{}”'.format(i))

        # 错误标点纠正4（两个同向双引号去掉一个<前>）
        pattern = re.compile(r'““(.*?)”')
        result = pattern.findall(a)
        for i in result:
            a = a.replace('““{}”'.format(i), '“{}”'.format(i))

        # 错误标点纠正5（两个同向双引号去掉一个<后>）
        p1 = r"(?<=“).+?(?=””)"
        pattern1 = re.compile(p1)
        result = pattern1.findall(a)
        for i in result:
            a = a.replace('“{}””'.format(i), '“{}”'.format(i))

        # 错误标点纠正6（两组双引号变成一组双引号）
        pattern = re.compile(r'““(.*?)””')
        result = pattern.findall(a)
        for i in result:
            a = a.replace('““{}””'.format(i), '“{}”'.format(i))

        # 将单独的单双直引号替换为空(清除剩余的直引号)
        a = a.replace("'", '')
        a = a.replace('"', '')

        # 【判断块】判断文段是全中文、全英文还是中英混排。
        def containenglish(str0):  # 判断是否包含英文字母
            import re
            return bool(re.search('[a-zA-Zａ-ｚＡ-Ｚ]', str0))

        def is_contain_chinese(check_str):  # 判断是否包含中文字
            for ch in check_str:
                if u'\u4e00' <= ch <= u'\u9fff':
                    return True
            return False

        def is_contain_num(str0):  # 判断是否包含数字
            import re
            return bool(re.search('[0-9０-９]', str0))

        def is_contain_symbol(keyword):
            if re.search(r"\W", keyword):
                return True
            else:
                return False

        if is_contain_num(str(a)) and not containenglish(str(a)) and not is_contain_chinese(str(a)):
            # 【全数块】清除数字中的空格，将全角数字转为半角数字
            a = a.replace(' ', '')

            def is_Qnumber(uchar):
                """判断一个unicode是否是全角数字"""
                if uchar >= u'\uff10' and uchar <= u'\uff19':
                    return True
                else:
                    return False

            def Q2B(uchar):
                """单个字符 全角转半角"""
                inside_code = ord(uchar)
                if inside_code == 0x3000:
                    inside_code = 0x0020
                else:
                    inside_code -= 0xfee0
                if inside_code < 0x0020 or inside_code > 0x7e:  # 转完之后不是半角字符返回原来的字符
                    return uchar
                return chr(inside_code)

            def stringpartQ2B(ustring):
                """把字符串中数字全角转半角"""
                return "".join(
                    [Q2B(uchar) if is_Qnumber(uchar) else uchar for uchar in ustring])

            a = stringpartQ2B(a)

            # 对全数字文段的货币符号、百分号和度数这三个符号进行专门处理
            i = 0
            while i <= len(a) - 1:
                if a[i] == '¥' and not is_contain_symbol(str(a[i - 1])):
                    a = list(a)
                    a.insert(i, ' ')
                    a = ''.join(a)
                    i = i + 2
                    continue
                if a[i] == '$' and not is_contain_symbol(str(a[i - 1])):
                    a = list(a)
                    a.insert(i, ' ')
                    a = ''.join(a)
                    i = i + 2
                    continue
                if a[i] == "%":
                    if a[i - 1] == ' ':
                        a = list(a)
                        del a[i - 1]
                        a = ''.join(a)
                        i = i - 1
                        continue
                    else:
                        a = list(a)
                        a.insert(i + 1, ' ')
                        a = ''.join(a)
                        i = i + 2
                        continue
                if a[i] == "°":
                    if a[i - 1] == ' ':
                        a = list(a)
                        del a[i - 1]
                        a = ''.join(a)
                        i = i - 1
                        continue
                    else:
                        a = list(a)
                        a.insert(i + 1, ' ')
                        a = ''.join(a)
                        i = i + 2
                        continue
                else:
                    i = i + 1
                    continue

            a = a.replace('  ', ' ')
            return a

        elif not containenglish(str(a)) and is_contain_chinese(str(a)):
            # 【中（数）块】
            # 去除不必要的中英文符号及空格
            a = a.replace('*', '')
            a = a.replace(' ', '')
            a = a.replace('#', '')
            a = a.replace('^', '')
            a = a.replace('~', '')
            a = a.replace('～', '')

            # 修改一些排版中常见的符号错误
            a = a.replace('。。', '。')
            a = a.replace('。。。', '……')
            a = a.replace('—', "——")
            a = a.replace('一一', "——")
            # Black Circle, Katakana Middle Dot, Bullet, Bullet Operator 替换为标准中间点（U+00B7 MIDDLE DOT）
            a = a.replace('●', "·")
            a = a.replace('・', "·")
            a = a.replace('•', "·")
            a = a.replace('∙', "·")
            # U+2027 HYPHENATION POINT 替换为中间点（U+00B7 MIDDLE DOT）
            a = a.replace('‧', "·")
            # 加重符号、乘号、点号替换为中间点（U+00B7 MIDDLE DOT）【如果使用乘号，应使用叉号乘，慎用点乘】
            a = a.replace('•', "·")
            a = a.replace('·', "·")
            a = a.replace('▪', "·")
            # Phoenician Word Separator (U+1091F) to middle dot
            a = a.replace('𐤟', "·")
            for i in range(10):
                a = a.replace('————————', "——")
                a = a.replace('——————', "——")
                a = a.replace('————', "——")

            # 将中文和数字混排中的全角数字转为半角数字，不改变标点的全半角情况
            def is_Qnumber(uchar):
                """判断一个unicode是否是全角数字"""
                if uchar >= u'\uff10' and uchar <= u'\uff19':
                    return True
                else:
                    return False

            def Q2B(uchar):
                """单个字符 全角转半角"""
                inside_code = ord(uchar)
                if inside_code == 0x3000:
                    inside_code = 0x0020
                else:
                    inside_code -= 0xfee0
                if inside_code < 0x0020 or inside_code > 0x7e:  # 转完之后不是半角字符返回原来的字符
                    return uchar
                return chr(inside_code)

            def stringpartQ2B(ustring):
                """把字符串中数字全角转半角"""
                return "".join(
                    [Q2B(uchar) if is_Qnumber(uchar) else uchar for uchar in ustring])

            a = stringpartQ2B(a)

            # 给中文和数字的混排增加空格
            def find_this(q, i):
                result = q[i]
                return result

            def find_next(q, i):
                result = q[i + 1]
                return result

            i = 0
            while i >= 0 and i < len(a) - 1:
                if is_contain_chinese(str(find_this(a, i))) and is_contain_num(str(find_next(a, i))):  # 从中文转数字
                    a = list(a)
                    a.insert(i + 1, ' ')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_next(a, i))) and is_contain_num(str(find_this(a, i))):  # 从数字转中文
                    a = list(a)
                    a.insert(i + 1, ' ')
                    a = ''.join(a)
                    i = i + 1
                    continue
                else:
                    i = i + 1
                    continue

            # 将常用英文标点转换为中文标点
            def E_trans_to_C(string):
                E_pun = u',.;:!?[]()<>'
                C_pun = u'，。；：！？【】（）《》'
                table = {ord(f): ord(t) for f, t in zip(E_pun, C_pun)}
                return string.translate(table)

            a = E_trans_to_C(str(a))

            # 对特殊数字符号进行处理
            i = 0
            while i <= len(a) - 1:
                if a[i] == '¥' and not is_contain_symbol(str(a[i - 1])):
                    a = list(a)
                    a.insert(i, ' ')
                    a = ''.join(a)
                    i = i + 2
                    continue
                if a[i] == '$' and not is_contain_symbol(str(a[i - 1])):
                    a = list(a)
                    a.insert(i, ' ')
                    a = ''.join(a)
                    i = i + 2
                    continue
                if a[i] == "%":
                    if a[i - 1] == ' ':
                        a = list(a)
                        del a[i - 1]
                        a = ''.join(a)
                        i = i - 1
                        continue
                    else:
                        a = list(a)
                        a.insert(i + 1, ' ')
                        a = ''.join(a)
                        i = i + 2
                        continue
                if a[i] == "°":
                    if a[i - 1] == ' ':
                        a = list(a)
                        del a[i - 1]
                        a = ''.join(a)
                        i = i - 1
                        continue
                    else:
                        a = list(a)
                        a.insert(i + 1, ' ')
                        a = ''.join(a)
                        i = i + 2
                        continue
                else:
                    i = i + 1
                    continue

            a = a.replace('  ', ' ')
            return a

        elif containenglish(str(a)) and not is_contain_chinese(str(a)):
            # 【英（数）块】给英文和数字混排的情况增加空格
            def find_this(q, i):
                result = q[i]
                return result

            def find_next(q, i):
                result = q[i + 1]
                return result

            i = 0
            while i >= 0 and i < len(a) - 1:
                if is_contain_num(str(find_this(a, i))) and containenglish(str(find_next(a, i))):  # 从数字转英文
                    a = list(a)
                    a.insert(i + 1, ' ')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_num(str(find_next(a, i))) and containenglish(str(find_this(a, i))):  # 从英文转数字
                    a = list(a)
                    a.insert(i + 1, ' ')
                    a = ''.join(a)
                    i = i + 1
                    continue
                else:
                    i = i + 1
                    continue

            # 将全角英文字符和数字转为半角英文和半角数字
            def is_Qnumber(uchar):
                """判断一个unicode是否是全角数字"""
                if uchar >= u'\uff10' and uchar <= u'\uff19':
                    return True
                else:
                    return False

            def is_Qalphabet(uchar):
                """判断一个unicode是否是全角英文字母"""
                if (uchar >= u'\uff21' and uchar <= u'\uff3a') or (uchar >= u'\uff41' and uchar <= u'\uff5a'):
                    return True
                else:
                    return False

            def Q2B(uchar):
                """单个字符 全角转半角"""
                inside_code = ord(uchar)
                if inside_code == 0x3000:
                    inside_code = 0x0020
                else:
                    inside_code -= 0xfee0
                if inside_code < 0x0020 or inside_code > 0x7e:  # 转完之后不是半角字符返回原来的字符
                    return uchar
                return chr(inside_code)

            def stringpartQ2B(ustring):
                """把字符串中字母和数字全角转半角"""
                return "".join(
                    [Q2B(uchar) if is_Qnumber(uchar) or is_Qalphabet(uchar) else uchar for uchar in ustring])

            a = stringpartQ2B(a)

            # 将文段中的中文符号转换为英文符号
            def C_trans_to_E(string):
                E_pun = u',.;:!?[]()<>'
                C_pun = u'，。；：！？【】（）《》'
                table = {ord(f): ord(t) for f, t in zip(C_pun, E_pun)}
                return string.translate(table)

            a = C_trans_to_E(str(a))

            # One Dot Leader (U+2024) to full stop (U+002E) （句号）
            a = a.replace('․', ".")

            # 清除英文标点符号前面的空格（,.;:?!）
            a = list(a)
            i = 0
            while i >= 0 and i < len(a) - 1:
                if a[i] == ',':
                    if a[i - 1] == ' ':
                        del a[i - 1]
                        continue
                    else:
                        i = i + 1
                        continue
                if a[i] == '.':
                    if a[i - 1] == ' ':
                        del a[i - 1]
                        continue
                    else:
                        i = i + 1
                        continue
                if a[i] == ';':
                    if a[i - 1] == ' ':
                        del a[i - 1]
                        continue
                    else:
                        i = i + 1
                        continue
                if a[i] == ':':
                    if a[i - 1] == ' ':
                        del a[i - 1]
                        continue
                    else:
                        i = i + 1
                        continue
                if a[i] == '?':
                    if a[i - 1] == ' ':
                        del a[i - 1]
                        continue
                    else:
                        i = i + 1
                        continue
                if a[i] == '!':
                    if a[i - 1] == ' ':
                        del a[i - 1]
                        continue
                    else:
                        i = i + 1
                        continue
                else:
                    i = i + 1
                    continue
            a = ''.join(a)

            # 对全数字文段的货币符号、百分号和度数这三个符号进行专门处理
            i = 0
            while i <= len(a) - 1:
                if a[i] == '¥' and not is_contain_symbol(str(a[i - 1])):
                    a = list(a)
                    a.insert(i, ' ')
                    a = ''.join(a)
                    i = i + 2
                    continue
                if a[i] == '$' and not is_contain_symbol(str(a[i - 1])):
                    a = list(a)
                    a.insert(i, ' ')
                    a = ''.join(a)
                    i = i + 2
                    continue
                if a[i] == "%":
                    if a[i - 1] == ' ':
                        a = list(a)
                        del a[i - 1]
                        a = ''.join(a)
                        i = i - 1
                        continue
                    else:
                        a = list(a)
                        a.insert(i + 1, ' ')
                        a = ''.join(a)
                        i = i + 2
                        continue
                if a[i] == "°":
                    if a[i - 1] == ' ':
                        a = list(a)
                        del a[i - 1]
                        a = ''.join(a)
                        i = i - 1
                        continue
                    else:
                        a = list(a)
                        a.insert(i + 1, ' ')
                        a = ''.join(a)
                        i = i + 2
                        continue
                else:
                    i = i + 1
                    continue

            a = a.replace('  ', ' ')
            return a

        elif containenglish(str(a)) and is_contain_chinese(str(a)) or \
                containenglish(str(a)) and is_contain_chinese(str(a)) and is_contain_num(str(a)):
            # 【中英（数）混排块】识别中英文字符，对英文字符保留空格，对中文字符去掉空格。标点默认使用原文标点，以中文为主（默认使用情况为在中文中引用英文）。
            def find_this(q, i):
                result = q[i]
                return result

            def find_pre(q, i):
                result = q[i - 1]
                return result

            def find_next(q, i):
                result = q[i + 1]
                return result

            def find_pre2(q, i):
                result = q[i - 2]
                return result

            def find_next2(q, i):
                result = q[i + 2]
                return result

            def find_next3(q, i):
                result = q[i + 3]
                return result

            # 首先来一遍此一后一的精准筛查
            i = 0
            while i >= 0 and i < len(a) - 1:
                if is_contain_chinese(str(find_this(a, i))) and containenglish(str(find_next(a, i))):  # 从中文转英文
                    a = list(a)
                    a.insert(i + 1, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_this(a, i))) and is_contain_num(str(find_next(a, i))):  # 从中文转数字
                    a = list(a)
                    a.insert(i + 1, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_next(a, i))) and is_contain_num(str(find_this(a, i))):  # 从数字转中文
                    a = list(a)
                    a.insert(i + 1, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_num(str(find_this(a, i))) and containenglish(str(find_next(a, i))):  # 从数字转英文
                    a = list(a)
                    a.insert(i + 1, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_num(str(find_next(a, i))) and containenglish(str(find_this(a, i))):  # 从英文转数字
                    a = list(a)
                    a.insert(i + 1, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_next(a, i))) and containenglish(str(find_this(a, i))):  # 从英文转中文
                    a = list(a)
                    a.insert(i + 1, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                else:
                    i = i + 1
                    continue

            # 再进行前一后一的插入
            i = 1
            while i > 0 and i < len(a) - 1:
                if is_contain_chinese(str(find_pre(a, i))) and containenglish(str(find_next(a, i))):  # 从中文转英文
                    a = list(a)
                    a.insert(i + 1, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_pre(a, i))) and is_contain_num(str(find_next(a, i))):  # 从中文转数字
                    a = list(a)
                    a.insert(i + 1, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_next(a, i))) and is_contain_num(str(find_pre(a, i))):  # 从数字转中文
                    a = list(a)
                    a.insert(i + 1, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_num(str(find_pre(a, i))) and containenglish(str(find_next(a, i))):  # 从数字转英文
                    a = list(a)
                    a.insert(i + 1, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_num(str(find_next(a, i))) and containenglish(str(find_pre(a, i))):  # 从英文转数字
                    a = list(a)
                    a.insert(i + 1, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_next(a, i))) and containenglish(str(find_pre(a, i))):  # 从英文转中文
                    a = list(a)
                    a.insert(i + 1, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                else:
                    i = i + 1
                    continue

            # 进行前一后二的筛查
            i = 1
            while i > 0 and i < len(a) - 2:
                if is_contain_chinese(str(find_pre(a, i))) and containenglish(str(find_next2(a, i))):  # 从中文转英文
                    a = list(a)
                    a.insert(i + 2, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_pre(a, i))) and is_contain_num(str(find_next2(a, i))):  # 从中文转数字
                    a = list(a)
                    a.insert(i + 2, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_next2(a, i))) and is_contain_num(str(find_pre(a, i))):  # 从数字转中文
                    a = list(a)
                    a.insert(i + 2, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_num(str(find_pre(a, i))) and containenglish(str(find_next2(a, i))):  # 从数字转英文
                    a = list(a)
                    a.insert(i + 2, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_num(str(find_next2(a, i))) and containenglish(str(find_pre(a, i))):  # 从英文转数字
                    a = list(a)
                    a.insert(i + 2, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_next2(a, i))) and containenglish(str(find_pre(a, i))):  # 从英文转中文
                    a = list(a)
                    a.insert(i + 2, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                else:
                    i = i + 1
                    continue

            # 再进行前二后二的筛查
            i = 1
            while i > 0 and i < len(a) - 2:
                if is_contain_chinese(str(find_pre2(a, i))) and containenglish(str(find_next2(a, i))):  # 从中文转英文
                    a = list(a)
                    a.insert(i + 2, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_pre2(a, i))) and is_contain_num(str(find_next2(a, i))):  # 从中文转数字
                    a = list(a)
                    a.insert(i + 2, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_next2(a, i))) and is_contain_num(str(find_pre2(a, i))):  # 从数字转中文
                    a = list(a)
                    a.insert(i + 2, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_num(str(find_pre2(a, i))) and containenglish(str(find_next2(a, i))):  # 从数字转英文
                    a = list(a)
                    a.insert(i + 2, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_num(str(find_next2(a, i))) and containenglish(str(find_pre2(a, i))):  # 从英文转数字
                    a = list(a)
                    a.insert(i + 2, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_next2(a, i))) and containenglish(str(find_pre2(a, i))):  # 从英文转中文
                    a = list(a)
                    a.insert(i + 2, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                else:
                    i = i + 1
                    continue

            # 最后进行一次前二后三的检查，这个比较少见，只在「武力⋯⋯”(1974」这个情况中存在
            i = 1
            while i > 0 and i < len(a) - 3:
                if is_contain_chinese(str(find_pre2(a, i))) and containenglish(str(find_next3(a, i))):  # 从中文转英文
                    a = list(a)
                    a.insert(i + 3, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_pre2(a, i))) and is_contain_num(str(find_next3(a, i))):  # 从中文转数字
                    a = list(a)
                    a.insert(i + 3, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_next3(a, i))) and is_contain_num(str(find_pre2(a, i))):  # 从数字转中文
                    a = list(a)
                    a.insert(i + 3, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_num(str(find_pre2(a, i))) and containenglish(str(find_next3(a, i))):  # 从数字转英文
                    a = list(a)
                    a.insert(i + 3, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_num(str(find_next3(a, i))) and containenglish(str(find_pre2(a, i))):  # 从英文转数字
                    a = list(a)
                    a.insert(i + 3, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_next3(a, i))) and containenglish(str(find_pre2(a, i))):  # 从英文转中文
                    a = list(a)
                    a.insert(i + 3, '*')
                    a = ''.join(a)
                    i = i + 1
                    continue
                else:
                    i = i + 1
                    continue

            # 将多个*号替换成一个*。
            a = a.replace('*****', "*")
            a = a.replace('****', "*")
            a = a.replace('***', "*")
            a = a.replace("**", "*")

            # 转换为三个列表（考虑在每个星号之后打上顺序，这样成为了列表后每个元素有一个代码i☆
            b = a.split('*')
            i = 0
            while i >= 0 and i <= len(b) - 1:
                b[i] = str(i + 1), '☆', b[i], '*'
                b[i] = ''.join(b[i])
                i = i + 1
                continue

            b_ch = []  # 中文（待清理）
            for i in range(len(b)):
                b_ch.append(b[i])
            c_en = []  # 英文（待清理）
            for i in range(len(b)):
                c_en.append(b[i])
            d_nu = []  # 数字（待清理）
            for i in range(len(b)):
                d_nu.append(b[i])

            # 读取列表元素中☆之后的元素，定义一个函数
            def qingli(k, i):
                x = k[i]
                z = x.index("☆") + 1
                y = x[z: len(x)]
                return y

            # 执行清理
            n = 0
            while n <= len(b_ch) - 1:
                if containenglish(str(qingli(b_ch, n))) or is_contain_num(str(qingli(b_ch, n))):
                    del b_ch[n]  # 中文，除掉英文和数字
                    n = n
                    continue
                else:
                    n = n + 1
                    continue

            n = 0
            while n <= len(c_en) - 1:
                if is_contain_chinese(str(qingli(c_en, n))) or is_contain_num(str(qingli(c_en, n))):
                    del c_en[n]  # 英文，除掉中文和数字
                    n = n
                    continue
                else:
                    n = n + 1
                    continue

            n = 0
            while n <= len(d_nu) - 1:
                if is_contain_chinese(str(qingli(d_nu, n))) or containenglish(str(qingli(d_nu, n))):
                    del d_nu[n]  # 数字，除掉中文和英文
                    n = n
                    continue
                else:
                    n = n + 1
                    continue

            # 【对中文处理】
            zh = ''.join(b_ch)
            # 去除不必要的中英文符号及空格
            zh = zh.replace(' ', '')
            zh = zh.replace('#', '')
            zh = zh.replace('^', '')
            zh = zh.replace('~', '')
            zh = zh.replace('～', '')

            # 修改一些排版中常见的符号错误
            zh = zh.replace('。。', '。')
            zh = zh.replace('。。。', '……')
            zh = zh.replace('—', "——")
            zh = zh.replace('一一', "——")
            # Black Circle, Katakana Middle Dot, Bullet, Bullet Operator 替换为标准中间点（U+00B7 MIDDLE DOT）
            zh = zh.replace('●', "·")
            zh = zh.replace('・', "·")
            zh = zh.replace('•', "·")
            zh = zh.replace('∙', "·")
            # U+2027 HYPHENATION POINT 替换为中间点（U+00B7 MIDDLE DOT）
            zh = zh.replace('‧', "·")
            # 加重符号、乘号、点号替换为中间点（U+00B7 MIDDLE DOT）
            zh = zh.replace('•', "·")
            zh = zh.replace('·', "·")
            zh = zh.replace('▪', "·")
            # Phoenician Word Separator (U+1091F) to middle dot
            zh = zh.replace('𐤟', "·")
            for i in range(10):
                zh = zh.replace('————————', "——")
                zh = zh.replace('——————', "——")
                zh = zh.replace('————', "——")

            # 将常用英文标点转换为中文标点
            def E_trans_to_C(string):
                E_pun = u',.;:!?[]()<>'
                C_pun = u'，。；：！？【】（）《》'
                table = {ord(f): ord(t) for f, t in zip(E_pun, C_pun)}
                return string.translate(table)

            zh = E_trans_to_C(str(zh))

            # 合成待整合的中文列表
            zh_he = zh.split('*')

            def Q2B(uchar):
                """单个字符 全角转半角"""
                inside_code = ord(uchar)
                if inside_code == 0x3000:
                    inside_code = 0x0020
                else:
                    inside_code -= 0xfee0
                if inside_code < 0x0020 or inside_code > 0x7e:  # 转完之后不是半角字符返回原来的字符
                    return uchar
                return chr(inside_code)

            # 【对英文处理】将全角英文字母转为半角英文字母，不改变符号的全半角，标点符号（,.;:?!）前面去空格。
            en = ''.join(c_en)

            def is_Qalphabet(uchar):
                """判断一个unicode是否是全角英文字母"""
                if (uchar >= u'\uff21' and uchar <= u'\uff3a') or (uchar >= u'\uff41' and uchar <= u'\uff5a'):
                    return True
                else:
                    return False

            def stringpartQ2B(ustring):
                """把字符串中字母全角转半角"""
                return "".join([Q2B(uchar) if is_Qalphabet(uchar) else uchar for uchar in ustring])

            en = stringpartQ2B(en)

            # One Dot Leader (U+2024) to full stop (U+002E) （句号）
            en = en.replace('․', ".")

            # 去除标点符号前面的空格
            en = list(en)
            i = 0
            while i >= 0 and i < len(en) - 1:
                if en[i] == ',':
                    if en[i - 1] == ' ':
                        del en[i - 1]
                        continue
                    else:
                        i = i + 1
                        continue
                if en[i] == '.':
                    if en[i - 1] == ' ':
                        del en[i - 1]
                        continue
                    else:
                        i = i + 1
                        continue
                if en[i] == ';':
                    if en[i - 1] == ' ':
                        del en[i - 1]
                        continue
                    else:
                        i = i + 1
                        continue
                if en[i] == ':':
                    if en[i - 1] == ' ':
                        del en[i - 1]
                        continue
                    else:
                        i = i + 1
                        continue
                if en[i] == '?':
                    if en[i - 1] == ' ':
                        del en[i - 1]
                        continue
                    else:
                        i = i + 1
                        continue
                if en[i] == '!':
                    if en[i - 1] == ' ':
                        del en[i - 1]
                        continue
                    else:
                        i = i + 1
                        continue
                else:
                    i = i + 1
                    continue
            en = ''.join(en)

            en_he = en.split('*')

            # 【对数字处理】将全角数字转为半角数字，不改变符号的全半角
            shu = ''.join(d_nu)

            def is_Qnumber(uchar):
                """判断一个unicode是否是全角数字"""
                if uchar >= u'\uff10' and uchar <= u'\uff19':
                    return True
                else:
                    return False

            def stringpartQ2B(ustring):
                """把字符串中数字全角转半角"""
                return "".join(
                    [Q2B(uchar) if is_Qnumber(uchar) else uchar for uchar in ustring])

            shu = stringpartQ2B(shu)

            shu_he = shu.split('*')

            # 合在一起（存在大于10的数变成小于2的问题，后面解决）
            he = zh_he + en_he + shu_he

            # 清掉空以及前面的顺序符号
            n = 0
            while n >= 0 and n <= len(he) - 1:
                if he[n] == '':
                    he.remove('')
                    continue
                else:
                    n = n + 1
                    continue

            he.sort(key=lambda x: int(x.split('☆')[0]))

            m = 0
            while m >= 0 and m <= len(he) - 1:
                f = he[m]
                g = f.index('☆') + 1
                h = f[g: len(f)]
                he[m] = h
                m = m + 1

            # 将列表转化为字符串相连，这里本可以转化成空格，但是这样会因为分割点问题产生问题，故先整体以"空"合并
            zhong = ''.join(he)

            # 解决因为分块不当带来的括号问题（当括号分到英文块的时候没有被处理到），此处默认全部换成中文括号
            zhong = zhong.replace('(', '（')
            zhong = zhong.replace(')', '）')
            zhong = zhong.replace('[', '【')
            zhong = zhong.replace(']', '】')
            zhong = zhong.replace('<', '《')
            zhong = zhong.replace('>', '》')

            # 清除因为分块不当带来的括号、引号、顿号前后的空格
            zhong = list(zhong)
            i = 0
            while i >= 0 and i < len(zhong) - 1:
                if zhong[i] == '（':
                    if zhong[i - 1] == ' ':
                        del zhong[i - 1]
                        continue
                    else:
                        i = i + 1
                        continue
                if zhong[i] == '）':
                    if zhong[i - 1] == ' ':
                        del zhong[i - 1]
                        continue
                    else:
                        i = i + 1
                        continue
                if zhong[i] == '、':
                    if zhong[i - 1] == ' ':
                        del zhong[i - 1]
                        continue
                    else:
                        i = i + 1
                        continue
                if zhong[i] == '“':
                    if zhong[i - 1] == ' ':
                        del zhong[i - 1]
                        continue
                    else:
                        i = i + 1
                        continue
                if zhong[i] == '”':
                    if zhong[i - 1] == ' ':
                        del zhong[i - 1]
                        continue
                    else:
                        i = i + 1
                        continue
                else:
                    i = i + 1
                    continue

            i = 0
            while i >= 0 and i < len(zhong) - 1:
                if zhong[i] == '（':
                    if zhong[i + 1] == ' ':
                        del zhong[i + 1]
                        continue
                    else:
                        i = i + 1
                        continue
                if zhong[i] == '）':
                    if zhong[i + 1] == ' ':
                        del zhong[i + 1]
                        continue
                    else:
                        i = i + 1
                        continue
                if zhong[i] == '、':
                    if zhong[i + 1] == ' ':
                        del zhong[i + 1]
                        continue
                    else:
                        i = i + 1
                        continue
                if zhong[i] == '“':
                    if zhong[i + 1] == ' ':
                        del zhong[i + 1]
                        continue
                    else:
                        i = i + 1
                        continue
                if zhong[i] == '”':
                    if zhong[i + 1] == ' ':
                        del zhong[i + 1]
                        continue
                    else:
                        i = i + 1
                        continue
                else:
                    i = i + 1
                    continue

            zhong = ''.join(zhong)

            # 给中英数三者相邻的文本插入空格，给特定的单位符号前后增减空格（注意，如果是探索，不能等号，如果是全局修改，必须<=）
            i = 0
            while i <= len(zhong) - 1:
                if zhong[i] == '¥' and not is_contain_symbol(str(zhong[i - 1])):
                    zhong = list(zhong)
                    zhong.insert(i, ' ')
                    zhong = ''.join(zhong)
                    i = i + 2
                    continue
                if zhong[i] == '$' and not is_contain_symbol(str(zhong[i - 1])):
                    zhong = list(zhong)
                    zhong.insert(i, ' ')
                    zhong = ''.join(zhong)
                    i = i + 2
                    continue
                if zhong[i] == "%":
                    if zhong[i - 1] == ' ':
                        zhong = list(zhong)
                        del zhong[i - 1]
                        zhong = ''.join(zhong)
                        i = i - 1
                        continue
                    else:
                        zhong = list(zhong)
                        zhong.insert(i + 1, ' ')
                        zhong = ''.join(zhong)
                        i = i + 2
                        continue
                if zhong[i] == "°":
                    if zhong[i - 1] == ' ':
                        zhong = list(zhong)
                        del zhong[i - 1]
                        zhong = ''.join(zhong)
                        i = i - 1
                        continue
                    else:
                        zhong = list(zhong)
                        zhong.insert(i + 1, ' ')
                        zhong = ''.join(zhong)
                        i = i + 2
                        continue
                else:
                    i = i + 1
                    continue

            i = 0
            while i >= 0 and i < len(zhong) - 1:
                if is_contain_chinese(str(find_this(zhong, i))) and containenglish(str(find_next(zhong, i))):  # 从中文转英文
                    zhong = list(zhong)
                    zhong.insert(i + 1, ' ')
                    zhong = ''.join(zhong)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_this(zhong, i))) and is_contain_num(str(find_next(zhong, i))):  # 从中文转数字
                    zhong = list(zhong)
                    zhong.insert(i + 1, ' ')
                    zhong = ''.join(zhong)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_next(zhong, i))) and is_contain_num(str(find_this(zhong, i))):  # 从数字转中文
                    zhong = list(zhong)
                    zhong.insert(i + 1, ' ')
                    zhong = ''.join(zhong)
                    i = i + 1
                    continue
                if is_contain_num(str(find_this(zhong, i))) and containenglish(str(find_next(zhong, i))):  # 从数字转英文
                    zhong = list(zhong)
                    zhong.insert(i + 1, ' ')
                    zhong = ''.join(zhong)
                    i = i + 1
                    continue
                if is_contain_num(str(find_next(zhong, i))) and containenglish(str(find_this(zhong, i))):  # 从英文转数字
                    zhong = list(zhong)
                    zhong.insert(i + 1, ' ')
                    zhong = ''.join(zhong)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_next(zhong, i))) and containenglish(str(find_this(zhong, i))):  # 从英文转中文
                    zhong = list(zhong)
                    zhong.insert(i + 1, ' ')
                    zhong = ''.join(zhong)
                    i = i + 1
                    continue
                else:
                    i = i + 1
                    continue

            # 清除连续空格
            zhong = zhong.replace('  ', ' ')
            return zhong

    def transferview(self):
        self.trans += 1
        AllText = codecs.open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'r', encoding='utf-8').read()
        if self.trans % 2 == 0: # html
            self.real1.setReadOnly(True)
            self.real1.textChanged.disconnect(self.save_text)
            endhtml = self.md2html(AllText)
            self.real1.setHtml(endhtml)
        else: # text
            self.real1.setReadOnly(False)
            self.real1.setText(AllText)
            self.real1.textChanged.connect(self.save_text)

    def save_text(self):
        text = self.real1.toPlainText()
        with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'w', encoding='utf-8') as file:
            file.write(text)

    def center(self):  # 设置窗口居中
        # Get the primary screen's geometry
        screen_geometry = self.screen().availableGeometry()

        # Calculate the centered position
        x_center = int((screen_geometry.width() / 2) + (self.width() / 2))
        y_center = int((screen_geometry.height() - self.height()) // 4 * 3)

        # Move the window to the center position
        self.setGeometry(QRect(x_center, y_center, self.width(), self.height()))

    def keyPressEvent(self, e):  # 当页面显示的时候，按下esc键可关闭窗口
        if e.key() == Qt.Key.Key_Escape.value:
            self.close()

    def activate(self):  # 设置窗口显示
        with open('/Applications/Broccoli.app/Contents/Resources/output.txt', 'w', encoding='utf-8') as f1:
            f1.write('')
        self.setStyleSheet(style_sheet_ori)
        w2.setStyleSheet(style_sheet_ori)
        self.show()
        self.center()
        self.setFocus()
        self.raise_()
        self.activateWindow()
        self.pin_a_tab()
        w2.checkupdate()
        if w2.lbl2.text() != 'No Intrenet' and 'ready' in w2.lbl2.text():
            w2.show()

    def cancel(self):  # 设置取消键的功能
        self.close()


class window4(QWidget):  # Customization settings
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):  # 设置窗口内布局
        self.setUpMainWindow()
        self.setFixedSize(500, 650)
        self.center()
        self.setWindowTitle('Customization settings')
        self.setFocus()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    def setUpMainWindow(self):
        self.widget1 = QComboBox(self)
        self.widget1.setEditable(False)
        defalist = ['API - openai', 'API - httpx']
        self.widget1.addItems(defalist)
        Which = codecs.open('/Applications/Broccoli.app/Contents/Resources/which.txt', 'r', encoding='utf-8').read()
        if Which == '0':
            self.widget1.setCurrentIndex(0)
        if Which == '1':
            self.widget1.setCurrentIndex(1)
        self.widget1.currentIndexChanged.connect(self.IndexChange)

        self.le5 = QLineEdit(self)
        self.le5.setPlaceholderText('Temperature here...(how creative you want it to be: from 0 to 1)')
        temp = codecs.open('/Applications/Broccoli.app/Contents/Resources/temp.txt', 'r', encoding='utf-8').read()
        if temp != '':
            self.le5.setText(temp)
        if temp == '':
            self.le5.setText('0.5')

        self.le6 = QLineEdit(self)
        self.le6.setPlaceholderText('Max tokens here...(1024 by default)')
        max = codecs.open('/Applications/Broccoli.app/Contents/Resources/max.txt', 'r', encoding='utf-8').read()
        if max != '':
            self.le6.setText(max)
        if max == '':
            self.le6.setText('1024')

        self.le8 = QLineEdit(self)
        self.le8.setPlaceholderText('Total tokens of a model here...(4096 by default)')
        total = codecs.open('/Applications/Broccoli.app/Contents/Resources/total.txt', 'r', encoding='utf-8').read()
        if total != '':
            self.le8.setText(total)
        if total == '':
            self.le8.setText('4096')

        self.le7 = QLineEdit(self)
        self.le7.setPlaceholderText('Time out after...seconds')
        max = codecs.open('/Applications/Broccoli.app/Contents/Resources/timeout.txt', 'r', encoding='utf-8').read()
        if max != '':
            self.le7.setText(max)
        if max == '':
            self.le7.setText('60')

        self.checkBox0 = QCheckBox('Show references when chatting with a file', self)
        self.checkBox0.clicked.connect(self.showref)
        showref = codecs.open('/Applications/Broccoli.app/Contents/Resources/showref.txt', 'r', encoding='utf-8').read()
        if showref == '1':
            self.checkBox0.setChecked(True)
        if showref == '0':
            self.checkBox0.setChecked(False)

        self.frame1 = QFrame(self)
        self.frame1.setFrameShape(QFrame.Shape.HLine)
        self.frame1.setFrameShadow(QFrame.Shadow.Sunken)

        self.le1 = QLineEdit(self)
        self.le1.setPlaceholderText("API here...Type anything if you don't have official API...Don't let it empty.")
        Apis = codecs.open('/Applications/Broccoli.app/Contents/Resources/api.txt', 'r', encoding='utf-8').read()
        if Apis != '':
            self.le1.setText(Apis)

        self.checkBox1 = QCheckBox('Third-party:', self)
        self.checkBox1.clicked.connect(self.thirdp)
        thirdp = codecs.open('/Applications/Broccoli.app/Contents/Resources/third.txt', 'r',
                             encoding='utf-8').read()
        if thirdp == '1':
            self.checkBox1.setChecked(True)
        if thirdp == '0':
            self.checkBox1.setChecked(False)

        self.le1_1 = QLineEdit(self)
        self.le1_1.setPlaceholderText('Third-party API here...only for ChatGPT (API - httpx)')
        Apis2 = codecs.open('/Applications/Broccoli.app/Contents/Resources/api2.txt', 'r', encoding='utf-8').read()
        if Apis2 != '':
            self.le1_1.setText(Apis2)

        self.le1_2 = QLineEdit(self)
        self.le1_2.setPlaceholderText('Third-party Endpoint here...only for ChatGPT (API - httpx)')
        bear = codecs.open('/Applications/Broccoli.app/Contents/Resources/bear.txt', 'r', encoding='utf-8').read()
        if bear != '':
            self.le1_2.setText(bear)

        self.frame2 = QFrame(self)
        self.frame2.setFrameShape(QFrame.Shape.HLine)
        self.frame2.setFrameShadow(QFrame.Shadow.Sunken)

        self.te1 = QTextEdit(self)
        home_dir = str(Path.home())
        tarname1 = "BroccoliAppPath"
        fulldir1 = os.path.join(home_dir, tarname1)
        if not os.path.exists(fulldir1):
            os.mkdir(fulldir1)
        tarname2 = "CustomPrompt.txt"
        fulldir2 = os.path.join(fulldir1, tarname2)
        if not os.path.exists(fulldir2):
            with open(fulldir2, 'a', encoding='utf-8') as f0:
                f0.write('')
        cont = codecs.open(fulldir2, 'r', encoding='utf-8').read()
        self.te1.setText(cont)
        self.te1.setPlaceholderText('This is your storage for prompts. Use {text} to represent parameters and "---" to '
                                    'seperate each other. In <|NAME|><|PROMPT|> format.')

        self.te0 = QTextEdit(self)
        tarname3 = "lang.txt"
        fulldir3 = os.path.join(fulldir1, tarname3)
        langs = codecs.open(fulldir3, 'r', encoding='utf-8').read()
        self.te0.setText(langs)
        self.te0.setPlaceholderText('These are languages you want to see in your use. One language name a line, better in original language.')

        self.te2 = QTextEdit(self)
        tarname4 = "model.txt"
        fulldir4 = os.path.join(fulldir1, tarname4)
        models = codecs.open(fulldir4, 'r', encoding='utf-8').read()
        self.te2.setText(models)
        self.te2.setPlaceholderText(
            'These are models you would like to use. One model a line.')

        self.widget2 = QComboBox(self)
        self.widget2.setEditable(False)
        if models == '':
            modellist = ['gpt-3.5-turbo', 'gpt-3.5-turbo-16k', 'gpt-3.5-turbo-0613', 'gpt-3.5-turbo-16k-0613']
            self.widget2.addItems(modellist)
        if models != '':
            modellist = models.split('\n')
            while '' in modellist:
                modellist.remove('')
            self.widget2.addItems(modellist)
        wp = codecs.open('/Applications/Broccoli.app/Contents/Resources/wp.txt', 'r', encoding='utf-8').read()
        self.widget2.setCurrentIndex(int(wp))
        self.widget2.currentIndexChanged.connect(self.IndexChange2)

        self.checkBox2 = QCheckBox('Remember chat history when asking new questions', self)
        self.checkBox2.clicked.connect(self.rememberhistory)
        showhistory = codecs.open('/Applications/Broccoli.app/Contents/Resources/history.txt', 'r', encoding='utf-8').read()
        if showhistory == '1':
            self.checkBox2.setChecked(True)
        if showhistory == '0':
            self.checkBox2.setChecked(False)

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

        self.qw3 = QWidget()
        vbox3 = QHBoxLayout()
        vbox3.setContentsMargins(0, 0, 0, 0)
        vbox3.addWidget(self.le6)
        vbox3.addWidget(self.le8)
        self.qw3.setLayout(vbox3)

        qw4 = QWidget()
        vbox4 = QVBoxLayout()
        vbox4.setContentsMargins(0, 0, 0, 0)
        vbox4.addWidget(self.le1_1)
        vbox4.addWidget(self.le1_2)
        qw4.setLayout(vbox4)

        qw5 = QWidget()
        vbox5 = QVBoxLayout()
        vbox5.setContentsMargins(0, 0, 0, 0)
        vbox5.addWidget(self.checkBox1)
        vbox5.addStretch()
        qw5.setLayout(vbox5)

        self.qw6 = QWidget()
        vbox6 = QHBoxLayout()
        vbox6.setContentsMargins(0, 0, 0, 0)
        vbox6.addWidget(qw5)
        vbox6.addWidget(qw4)
        self.qw6.setLayout(vbox6)

        vbox1 = QVBoxLayout()
        vbox1.setContentsMargins(20, 20, 20, 20)
        vbox1.addWidget(self.widget1)
        vbox1.addWidget(self.widget2)
        vbox1.addWidget(self.le5)
        vbox1.addWidget(self.qw3)
        vbox1.addWidget(self.le7)
        vbox1.addWidget(self.checkBox0)
        vbox1.addWidget(self.checkBox2)
        vbox1.addWidget(self.frame1)
        vbox1.addWidget(self.le1)
        vbox1.addWidget(self.qw6)
        vbox1.addWidget(self.frame2)
        vbox1.addWidget(self.te2)
        vbox1.addWidget(self.te0)
        vbox1.addWidget(self.te1)
        vbox1.addWidget(qw2)
        self.setLayout(vbox1)

        self.le1.setVisible(True)
        self.qw6.setVisible(True)
        if self.widget1.currentIndex() == 0:
            self.qw6.setVisible(False)

    def IndexChange(self, i):
        self.le1.setVisible(True)
        self.qw6.setVisible(True)
        if i == 0:
            with open('/Applications/Broccoli.app/Contents/Resources/which.txt', 'w', encoding='utf-8') as f0:
                f0.write('0')
            self.qw6.setVisible(False)
        if i == 1:
            with open('/Applications/Broccoli.app/Contents/Resources/which.txt', 'w', encoding='utf-8') as f0:
                f0.write('1')

    def IndexChange2(self, h):
        with open('/Applications/Broccoli.app/Contents/Resources/wp.txt', 'w', encoding='utf-8') as f0:
            f0.write(str(h))
        with open('/Applications/Broccoli.app/Contents/Resources/modelnow.txt', 'w', encoding='utf-8') as f0:
            f0.write(self.widget2.itemText(h))

    def SaveAPI(self):
        nowmodel = int(codecs.open('/Applications/Broccoli.app/Contents/Resources/wp.txt', 'r', encoding='utf-8').read())
        with open('/Applications/Broccoli.app/Contents/Resources/api.txt', 'w', encoding='utf-8') as f1:
            f1.write(self.le1.text())
        with open('/Applications/Broccoli.app/Contents/Resources/api2.txt', 'w', encoding='utf-8') as f1:
            f1.write(self.le1_1.text())
        with open('/Applications/Broccoli.app/Contents/Resources/bear.txt', 'w', encoding='utf-8') as f1:
            f1.write(self.le1_2.text())
        with open('/Applications/Broccoli.app/Contents/Resources/temp.txt', 'w', encoding='utf-8') as f1:
            f1.write(self.le5.text())
        with open('/Applications/Broccoli.app/Contents/Resources/max.txt', 'w', encoding='utf-8') as f1:
            f1.write(self.le6.text())
        with open('/Applications/Broccoli.app/Contents/Resources/timeout.txt', 'w', encoding='utf-8') as f1:
            f1.write(self.le7.text())
        with open('/Applications/Broccoli.app/Contents/Resources/total.txt', 'w', encoding='utf-8') as f1:
            f1.write(self.le8.text())
        home_dir = str(Path.home())
        tarname1 = "BroccoliAppPath"
        fulldir1 = os.path.join(home_dir, tarname1)
        if not os.path.exists(fulldir1):
            os.mkdir(fulldir1)
        tarname2 = "CustomPrompt.txt"
        fulldir2 = os.path.join(fulldir1, tarname2)
        with open(fulldir2, 'w', encoding='utf-8') as f0:
            f0.write(self.te1.toPlainText())
        tarname3 = "lang.txt"
        fulldir3 = os.path.join(fulldir1, tarname3)
        with open(fulldir3, 'w', encoding='utf-8') as f0:
            f0.write(self.te0.toPlainText())
        tarname4 = "model.txt"
        fulldir4 = os.path.join(fulldir1, tarname4)
        with open(fulldir4, 'w', encoding='utf-8') as f0:
            f0.write(self.te2.toPlainText())
        self.widget2.clear()
        models = codecs.open(fulldir4, 'r', encoding='utf-8').read()
        if models == '':
            modellist = ['gpt-3.5-turbo', 'gpt-3.5-turbo-16k', 'gpt-3.5-turbo-0613', 'gpt-3.5-turbo-16k-0613']
            self.widget2.addItems(modellist)
        if models != '':
            modellist = models.split('\n')
            while '' in modellist:
                modellist.remove('')
            self.widget2.addItems(modellist)
        self.widget2.setCurrentIndex(nowmodel)
        self.close()

    def thirdp(self):
        if self.checkBox1.isChecked():
            with open('/Applications/Broccoli.app/Contents/Resources/third.txt', 'w', encoding='utf-8') as f0:
                f0.write('1')
        if not self.checkBox1.isChecked():
            with open('/Applications/Broccoli.app/Contents/Resources/third.txt', 'w', encoding='utf-8') as f0:
                f0.write('0')

    def showref(self):
        if self.checkBox0.isChecked():
            with open('/Applications/Broccoli.app/Contents/Resources/showref.txt', 'w', encoding='utf-8') as f0:
                f0.write('1')
        if not self.checkBox0.isChecked():
            with open('/Applications/Broccoli.app/Contents/Resources/showref.txt', 'w', encoding='utf-8') as f0:
                f0.write('0')

    def rememberhistory(self):
        if self.checkBox2.isChecked():
            with open('/Applications/Broccoli.app/Contents/Resources/history.txt', 'w', encoding='utf-8') as f0:
                f0.write('1')
        if not self.checkBox2.isChecked():
            with open('/Applications/Broccoli.app/Contents/Resources/history.txt', 'w', encoding='utf-8') as f0:
                f0.write('0')

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


class window5(QWidget):  # 小窗口
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setUpMainWindow()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(500, 150)
        self.WEIGHT = int(self.screen().availableGeometry().width())
        self.HEIGHT = int(self.screen().availableGeometry().height())

    def setUpMainWindow(self):
        home_dir = str(Path.home())
        tarname1 = "BroccoliAppPath"
        self.fulldir1 = os.path.join(home_dir, tarname1)
        if not os.path.exists(self.fulldir1):
            os.mkdir(self.fulldir1)
        tarname2 = "CustomPrompt.txt"
        fulldir2 = os.path.join(self.fulldir1, tarname2)
        tarname3 = "lang.txt"
        fulldir3 = os.path.join(self.fulldir1, tarname3)
        if not os.path.exists(fulldir3):
            with open(fulldir3, 'a', encoding='utf-8') as f0:
                f0.write('')
        tarname4 = "model.txt"
        fulldir4 = os.path.join(self.fulldir1, tarname4)
        if not os.path.exists(fulldir4):
            with open(fulldir4, 'a', encoding='utf-8') as f0:
                f0.write('')

        self.ask_text1 = QPlainTextEdit(self)
        self.ask_text1.setReadOnly(False)
        self.ask_text1.setObjectName('edit')
        self.ask_text1.setFixedHeight(70)
        self.ask_text1.setPlaceholderText('Your prompts here...')

        self.ask_btn_0 = QPushButton('🔺 Send', self)
        self.ask_btn_0.setFixedSize(80, 20)
        self.ask_btn_0.clicked.connect(self.bot2send)
        self.ask_btn_0.setShortcut("Ctrl+Return")

        self.ask_widget0 = QComboBox(self)
        self.ask_widget0.setCurrentIndex(0)
        self.ask_widget0.addItems(
            ['Chat and ask', 'Translate', 'Polish', 'Summarize', 'Grammatically analyze',
             'Explain code', 'Customize'])
        self.ask_widget0.currentIndexChanged.connect(self.bot2mode)
        self.ask_widget0.setFixedWidth(370)

        self.ask_widget1 = QComboBox(self)
        self.ask_widget1.setCurrentIndex(0)
        self.ask_widget1.setMaximumWidth(108)
        langs = codecs.open(fulldir3, 'r', encoding='utf-8').read()
        fulllanglist = []
        langs_list = ['English', '中文', '日本語']
        if langs != '':
            langs_list = langs.split('\n')
            while '' in langs_list:
                langs_list.remove('')
            for i in range(len(langs_list)):
                fulllanglist.append(langs_list[i])
        if langs == '':
            for i in range(len(langs_list)):
                fulllanglist.append(langs_list[i])
        self.ask_widget1.addItems(langs_list)
        self.ask_widget1.setVisible(False)
        self.ask_widget1.currentIndexChanged.connect(self.bot2trans)

        self.ask_lbl1 = QLabel('▶', self)
        self.ask_lbl1.setVisible(False)

        self.ask_widget2 = QComboBox(self)
        self.ask_widget2.setCurrentIndex(0)
        self.ask_widget2.setMaximumWidth(108)
        currentlang = self.ask_widget1.currentText()
        while currentlang in langs_list:
            langs_list.remove(currentlang)
        self.ask_widget2.addItems(langs_list)
        self.ask_widget2.setVisible(False)

        self.ask_widget4 = QComboBox(self)
        self.ask_widget4.setCurrentIndex(0)
        self.ask_widget4.addItems(fulllanglist)
        self.ask_widget4.setVisible(False)
        self.ask_widget4.setFixedWidth(170)

        self.ask_widget5 = QComboBox(self)
        self.ask_widget5.setCurrentIndex(0)
        if not os.path.exists(fulldir2):
            with open(fulldir2, 'a', encoding='utf-8') as f0:
                f0.write('')
        customprompt = codecs.open(fulldir2, 'r', encoding='utf-8').read()
        promptlist = customprompt.split('---')
        while '' in promptlist:
            promptlist.remove('')
        itemlist = []
        for i in range(len(promptlist)):
            itemlist.append(promptlist[i].split('|><|')[0].replace('<|', '').replace('\n', ''))
        if itemlist != []:
            self.ask_widget5.addItems(itemlist)
        if itemlist == []:
            self.ask_widget5.addItems(['No customized prompts, please add one in Settings'])
        self.ask_widget5.setVisible(False)
        self.ask_widget5.setFixedWidth(170)
        self.ask_widget5.currentIndexChanged.connect(self.bot2custom)

        self.ask_btn_1 = QPushButton('', self)
        self.ask_btn_1.setFixedSize(25, 25)
        self.ask_btn_1.setStyleSheet('''
            QPushButton{
            border: transparent;
            background-color: transparent;
            border-image: url(/Applications/Broccoli.app/Contents/Resources/set2.png);
            }
            QPushButton:pressed{
            border: 1px outset grey;
            background-color: #0085FF;
            border-radius: 4px;
            padding: 1px;
            color: #FFFFFF
            }
            ''')
        self.ask_btn_1.move(420, 60)
        self.ask_btn_1.clicked.connect(w4.activate)

        self.ask_btn_2 = QPushButton('', self)
        self.ask_btn_2.setFixedSize(25, 25)
        self.ask_btn_2.setStyleSheet('''
            QPushButton{
            border: transparent;
            background-color: transparent;
            border-image: url(/Applications/Broccoli.app/Contents/Resources/close.png);
            }
            QPushButton:pressed{
            border: 1px outset grey;
            background-color: #0085FF;
            border-radius: 4px;
            padding: 1px;
            color: #FFFFFF
            }
            ''')
        self.ask_btn_2.move(450, 60)
        self.ask_btn_2.clicked.connect(self.cancel)

        qa1_3 = QWidget()
        vbox1_3 = QHBoxLayout()
        vbox1_3.setContentsMargins(0, 0, 0, 0)
        vbox1_3.addWidget(self.ask_widget0)
        vbox1_3.addWidget(self.ask_widget1)
        vbox1_3.addStretch()
        vbox1_3.addWidget(self.ask_lbl1)
        vbox1_3.addStretch()
        vbox1_3.addWidget(self.ask_widget2)
        vbox1_3.addWidget(self.ask_widget4)
        vbox1_3.addWidget(self.ask_widget5)
        vbox1_3.addStretch()
        qa1_3.setLayout(vbox1_3)
        qa1_3.setFixedWidth(370)

        qa1_1 = QWidget()
        vbox1_1 = QHBoxLayout()
        vbox1_1.setContentsMargins(0, 0, 0, 0)
        vbox1_1.addWidget(qa1_3)
        vbox1_1.addWidget(self.ask_btn_0)
        qa1_1.setLayout(vbox1_1)

        self.bot2 = QWidget()
        vbox2_1 = QVBoxLayout()
        vbox2_1.setContentsMargins(20, 20, 20, 10)
        vbox2_1.addWidget(self.ask_text1)
        vbox2_1.addWidget(qa1_1)
        self.bot2.setLayout(vbox2_1)
        self.bot2.setObjectName("Main")

        vbox3 = QHBoxLayout()
        vbox3.setContentsMargins(0, 0, 0, 0)
        vbox3.addWidget(self.bot2)
        self.setLayout(vbox3)
        self.ask_btn_1.raise_()
        self.ask_btn_2.raise_()

    def bot2send(self):
        self.ask_btn_0.setDisabled(True)
        modelnow = codecs.open(BasePath + 'modelnow.txt', 'r', encoding='utf-8').read()
        Which = codecs.open(BasePath + 'which.txt', 'r', encoding='utf-8').read()
        if Which == '0':
            if self.ask_text1.toPlainText() == '':
                self.ask_text1.setPlainText("Hello!")
            QuesText = self.ask_text1.toPlainText()
            QuesText = QuesText.lstrip('\n')
            QuesText = QuesText.replace('\n', '\n\n\t')
            QuesText = QuesText.replace('\n\n\t\n\n\t', '\n\n\t')
            self.ask_LastQ = str(self.ask_text1.toPlainText())
            AccountGPT = codecs.open(BasePath + 'api.txt', 'r',
                                     encoding='utf-8').read()
            if AccountGPT != '' and self.ask_text1.toPlainText() != '':
                QApplication.processEvents()
                QApplication.restoreOverrideCursor()
                self.ask_text1.setReadOnly(True)
                md = '- Q: ' + QuesText + '\n\n'
                with open(BasePath + 'output.txt', 'a', encoding='utf-8') as f1:
                    f1.write(md)
                PromText = codecs.open(BasePath + 'output.txt', 'r',
                                       encoding='utf-8').read()
                newhtml = w3.md2html(PromText)
                w3.real1.setHtml(newhtml)
                w3.real1.ensureCursorVisible()  # 游标可用
                cursor = w3.real1.textCursor()  # 设置游标
                pos = len(w3.real1.toPlainText())  # 获取文本尾部的位置
                cursor.setPosition(pos)  # 游标位置设置为尾部
                w3.real1.setTextCursor(cursor)  # 滚动到游标位置
                QApplication.processEvents()
                QApplication.restoreOverrideCursor()
                timeout = 60
                timeset = codecs.open(BasePath + 'timeout.txt', 'r',
                                      encoding='utf-8').read()
                if timeset != '':
                    timeout = int(timeset)
                signal.signal(signal.SIGALRM, w3.timeout_handler)
                signal.alarm(timeout)  # set timer to 15 seconds
                try:
                    openai.api_key = AccountGPT
                    history = ''
                    showhistory = codecs.open(BasePath + 'history.txt', 'r',
                                              encoding='utf-8').read()
                    if showhistory == '1':
                        history = codecs.open(BasePath + 'output.txt', 'r',
                                              encoding='utf-8').read().replace('- A: ', '').replace('- Q: ', '')
                    prompt = str(self.ask_text1.toPlainText())
                    reststr = history + '---' + prompt
                    tokenizer = GPT2Tokenizer.from_pretrained('EleutherAI/gpt-neo-2.7B')
                    A = tokenizer.encode(reststr, add_special_tokens=True)
                    totaltoken = codecs.open(BasePath + 'total.txt', 'r',
                                             encoding='utf-8').read()
                    maxtoken = codecs.open(BasePath + 'max.txt', 'r',
                                           encoding='utf-8').read()
                    prompttoken = int(totaltoken) - int(maxtoken)
                    while len(A) >= prompttoken:
                        AllList = reststr.split('---')
                        while '' in AllList:
                            AllList.remove('')
                        while '\n\n' in AllList:
                            AllList.remove('\n\n')
                        del AllList[0]
                        reststr = '---'.join(AllList)
                        A = tokenizer.encode(reststr, add_special_tokens=True)
                        continue
                    if self.ask_widget0.currentIndex() == 0:
                        prompt = reststr
                    if self.ask_widget0.currentIndex() == 1:
                        prompt = f"""You are a translation engine that can only translate text and cannot interpret it. Translate this text from {self.ask_widget1.currentText()} to {self.ask_widget2.currentText()}. Don’t reply any other explanations. Before the translated text starts, write "「「START」」" and write "「「END」」” after it ends. Text: {str(self.ask_text1.toPlainText())}. """
                    if self.ask_widget0.currentIndex() == 2:
                        prompt = f"""Revise the text in {self.ask_widget4.currentText()} to remove grammar mistakes and make it more clear, concise, and coherent. Don’t reply any other explanations. Before the text starts, write "「「START」」" and write "「「END」」” after it ends. Text: {str(self.ask_text1.toPlainText())}. """
                    if self.ask_widget0.currentIndex() == 3:
                        prompt = f"""You are a text summarizer, you can only summarize the text, don't interpret it. Summarize this text in {self.ask_widget4.currentText()} to make it shorter, logical and clear. Don’t reply any other explanations. Before the text starts, write "「「START」」" and write "「「END」」” after it ends. Text: {str(self.ask_text1.toPlainText())}. """
                    if self.ask_widget0.currentIndex() == 4:
                        prompt = f"""You are an expert in semantics and grammar, teaching me how to learn. Please explain in {self.ask_widget4.currentText()} the meaning of every word in the text above and the meaning and the grammar structure of the text. If a word is part of an idiom, please explain the idiom and provide a few examples in {self.ask_widget4.currentText()} with similar meanings, along with their explanations. Before the text starts, write "「「START」」" and write "「「END」」” after it ends. Text: {str(self.ask_text1.toPlainText())}. """
                    if self.ask_widget0.currentIndex() == 5:
                        prompt = f"""You are a code explanation engine, you can only explain the code, do not interpret or translate it. Also, please report any bugs you find in the code to the author of the code. Must repeat in {self.ask_widget4.currentText()}. Before the text starts, write "「「START」」" and write "「「END」」” after it ends. Code: {str(self.ask_text1.toPlainText())}. """

                    tutr = 0.5
                    temp = codecs.open(BasePath + 'temp.txt', 'r',
                                       encoding='utf-8').read()
                    if temp != '':
                        tutr = float(temp)

                    maxt = 1024
                    if maxtoken != '':
                        maxt = int(maxtoken)

                    completion = openai.ChatCompletion.create(
                        model=modelnow,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=maxt,
                        n=1,
                        stop=None,
                        temperature=tutr,
                    )
                    message = completion.choices[0].message["content"].strip()
                    QApplication.processEvents()
                    QApplication.restoreOverrideCursor()
                    if self.ask_widget0.currentIndex() == 0 or self.ask_widget0.currentIndex() == 6:
                        ResultEnd = message.encode('utf-8').decode('utf-8', 'ignore')
                        uid = os.getuid()
                        env = os.environ.copy()
                        env['__CF_USER_TEXT_ENCODING'] = f'{uid}:0x8000100:0x8000100'
                        p = subprocess.Popen(['pbcopy', 'w'], stdin=subprocess.PIPE, env=env)
                        p.communicate(input=ResultEnd.encode('utf-8'))
                        message = message.lstrip('\n')
                        message = message.replace('\n', '\n\n\t')
                        message = message.replace('\n\n\t\n\n\t', '\n\n\t')
                        message = '\n\t' + message
                        QApplication.processEvents()
                        QApplication.restoreOverrideCursor()
                    if self.ask_widget0.currentIndex() == 1 or self.ask_widget0.currentIndex() == 2 or \
                            self.ask_widget0.currentIndex() == 3 or self.ask_widget0.currentIndex() == 4 or \
                            self.ask_widget0.currentIndex() == 5:
                        pattern = re.compile(r'「「START」」([\s\S]*?)「「END」」')
                        result = pattern.findall(message)
                        ResultEnd = ''.join(result)
                        ResultEnd = ResultEnd.encode('utf-8').decode('utf-8', 'ignore')
                        uid = os.getuid()
                        env = os.environ.copy()
                        env['__CF_USER_TEXT_ENCODING'] = f'{uid}:0x8000100:0x8000100'
                        p = subprocess.Popen(['pbcopy', 'w'], stdin=subprocess.PIPE, env=env)
                        p.communicate(input=ResultEnd.encode('utf-8'))
                        message = ResultEnd
                        message = message.lstrip('\n')
                        message = message.replace('\n', '\n\n\t')
                        message = message.replace('\n\n\t\n\n\t', '\n\n\t')
                        message = '\n\t' + message

                    EndMess = '- A: ' + message + '\n\n---\n\n'
                    with open(BasePath + 'output.txt', 'a',
                              encoding='utf-8') as f1:
                        f1.write(EndMess)
                    ProcessText = codecs.open(BasePath + 'output.txt', 'r',
                                              encoding='utf-8').read()
                    midhtml = w3.md2html(ProcessText)
                    w3.real1.setHtml(midhtml)
                    w3.real1.ensureCursorVisible()  # 游标可用
                    cursor = w3.real1.textCursor()  # 设置游标
                    pos = len(w3.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    w3.real1.setTextCursor(cursor)  # 滚动到游标位置
                    QApplication.processEvents()
                    QApplication.restoreOverrideCursor()

                    self.ask_text1.clear()
                except TimeoutException:
                    with open(BasePath + 'output.txt', 'a',
                              encoding='utf-8') as f1:
                        f1.write('- A: Timed out, please try again!' + '\n\n---\n\n')
                    AllText = codecs.open(BasePath + 'output.txt', 'r',
                                          encoding='utf-8').read()
                    endhtml = w3.md2html(AllText)
                    w3.real1.setHtml(endhtml)
                    w3.real1.ensureCursorVisible()  # 游标可用
                    cursor = w3.real1.textCursor()  # 设置游标
                    pos = len(w3.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    w3.real1.setTextCursor(cursor)  # 滚动到游标位置
                    self.ask_text1.setPlainText(self.ask_LastQ)
                except Exception as e:
                    with open(BasePath + 'output.txt', 'a',
                              encoding='utf-8') as f1:
                        f1.write('- A: Error, please try again!' + str(e) + '\n\n---\n\n')
                    AllText = codecs.open(BasePath + 'output.txt', 'r',
                                          encoding='utf-8').read()
                    endhtml = w3.md2html(AllText)
                    w3.real1.setHtml(endhtml)
                    w3.real1.ensureCursorVisible()  # 游标可用
                    cursor = w3.real1.textCursor()  # 设置游标
                    pos = len(w3.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    w3.real1.setTextCursor(cursor)  # 滚动到游标位置
                    self.ask_text1.setPlainText(self.ask_LastQ)
                signal.alarm(0)  # reset timer
                self.ask_text1.setReadOnly(False)
            if AccountGPT == '':
                w3.real1.setText('You should set your accounts in Settings.')
        if Which == '1':
            if self.ask_text1.toPlainText() == '':
                self.ask_text1.setPlainText("Hello!")
            QuesText = self.ask_text1.toPlainText()
            QuesText = QuesText.lstrip('\n')
            QuesText = QuesText.replace('\n', '\n\n\t')
            QuesText = QuesText.replace('\n\n\t\n\n\t', '\n\n\t')
            self.ask_LastQ = str(self.ask_text1.toPlainText())
            AccountGPT = codecs.open(BasePath + 'api.txt', 'r',
                                     encoding='utf-8').read()
            if AccountGPT != '' and self.ask_text1.toPlainText() != '':
                self.ask_text1.setReadOnly(True)
                md = '- Q: ' + QuesText + '\n\n'
                with open(BasePath + 'output.txt', 'a', encoding='utf-8') as f1:
                    f1.write(md)
                PromText = codecs.open(BasePath + 'output.txt', 'r',
                                       encoding='utf-8').read()
                newhtml = w3.md2html(PromText)
                w3.real1.setHtml(newhtml)
                w3.real1.ensureCursorVisible()  # 游标可用
                cursor = w3.real1.textCursor()  # 设置游标
                pos = len(w3.real1.toPlainText())  # 获取文本尾部的位置
                cursor.setPosition(pos)  # 游标位置设置为尾部
                w3.real1.setTextCursor(cursor)  # 滚动到游标位置
                timeout = 60
                timeset = codecs.open(BasePath + 'timeout.txt', 'r',
                                      encoding='utf-8').read()
                if timeset != '':
                    timeout = int(timeset)
                signal.signal(signal.SIGALRM, w3.timeout_handler)
                signal.alarm(timeout)  # set timer to 15 seconds
                # Set up your API key
                ENDPOINT = 'https://api.openai.com/v1/chat/completions'
                api2 = codecs.open(BasePath + 'api2.txt', 'r',
                                   encoding='utf-8').read()
                bear = codecs.open(BasePath + 'bear.txt', 'r',
                                   encoding='utf-8').read()
                thirdp = codecs.open(BasePath + 'third.txt', 'r',
                                     encoding='utf-8').read()
                if bear != '' and api2 != '' and thirdp == '1':
                    ENDPOINT = bear + '/v1/chat/completions'
                    AccountGPT = api2
                HEADERS = {"Authorization": f"Bearer {AccountGPT}"}
                totaltoken = codecs.open(BasePath + 'total.txt', 'r',
                                         encoding='utf-8').read()
                maxtoken = codecs.open(BasePath + 'max.txt', 'r',
                                       encoding='utf-8').read()
                prompttoken = int(totaltoken) - int(maxtoken)
                try:
                    async def chat_gpt(message, conversation_history=None, tokens_limit=prompttoken):
                        if conversation_history is None:
                            conversation_history = []

                        conversation_history.append({"role": "user", "content": message})

                        input_text = "".join([f"{msg['role']}:{msg['content']}\n" for msg in conversation_history])

                        # Truncate or shorten the input text if it exceeds the token limit
                        encoded_input_text = input_text.encode("utf-8")
                        while len(encoded_input_text) > tokens_limit:
                            conversation_history.pop(0)
                            input_text = "".join(
                                [f"{msg['role']}:{msg['content']}\n" for msg in conversation_history])
                            encoded_input_text = input_text.encode("utf-8")

                        tutr = 0.5
                        temp = codecs.open(BasePath + 'temp.txt', 'r',
                                           encoding='utf-8').read()
                        if temp != '':
                            tutr = float(temp)

                        maxt = 1024
                        if maxtoken != '':
                            maxt = int(maxtoken)

                        # Set up the API call data
                        data = {
                            "model": modelnow,
                            "messages": [{"role": "user", "content": input_text}],
                            "max_tokens": maxt,
                            "temperature": tutr,
                            "n": 1,
                            "stop": None,
                        }

                        # Make the API call asynchronously
                        async with httpx.AsyncClient() as client:
                            response = await client.post(ENDPOINT, json=data, headers=HEADERS, timeout=60.0)

                        # Process the API response
                        if response.status_code == 200:
                            response_data = response.json()
                            chat_output = response_data["choices"][0]["message"]["content"].strip()
                            return chat_output
                        else:
                            raise Exception(
                                f"API call failed with status code {response.status_code}: {response.text}")

                    async def main():
                        conversation_history = []
                        prompt = str(self.ask_text1.toPlainText())
                        if self.ask_widget0.currentIndex() == 0:
                            ori_history = [{"role": "user", "content": "Hey."},
                                           {"role": "assistant", "content": "Hello! I'm happy to help you."}]
                            conversation_history = ori_history
                            showhistory = codecs.open(BasePath + 'history.txt',
                                                      'r',
                                                      encoding='utf-8').read()
                            if showhistory == '1':
                                try:
                                    history = codecs.open(
                                        BasePath + 'output.txt', 'r',
                                        encoding='utf-8').read().replace('"', '').replace(
                                        '- Q: ', '''{"role": "user", "content": "'''). \
                                        replace('- A: ', '''"}✡{"role": "assistant", "content": "''') \
                                        .replace('---', '''"}✡''').replace('\n', '').replace('\t', '').rstrip()
                                    historylist = history.split('✡')
                                    while '' in historylist:
                                        historylist.remove('')
                                    for hili in historylist:
                                        my_dict = json.loads(hili)
                                        conversation_history.append(my_dict)
                                except Exception as e:
                                    pass
                        if self.ask_widget0.currentIndex() == 1:
                            prompt = f"""You are a translation engine that can only translate text and cannot interpret it. Translate this text from {self.ask_widget1.currentText()} to {self.ask_widget2.currentText()}. Don’t reply any other explanations. Before the translated text starts, write "「「START」」" and write "「「END」」” after it ends. Text: {str(self.ask_text1.toPlainText())}. """
                        if self.ask_widget0.currentIndex() == 2:
                            prompt = f"""Revise the text in {self.ask_widget4.currentText()} to remove grammar mistakes and make it more clear, concise, and coherent. Don’t reply any other explanations. Before the text starts, write "「「START」」" and write "「「END」」” after it ends. Text: {str(self.ask_text1.toPlainText())}. """
                        if self.ask_widget0.currentIndex() == 3:
                            prompt = f"""You are a text summarizer, you can only summarize the text, don't interpret it. Summarize this text in {self.ask_widget4.currentText()} to make it shorter, logical and clear. Don’t reply any other explanations. Before the text starts, write "「「START」」" and write "「「END」」” after it ends. Text: {str(self.ask_text1.toPlainText())}. """
                        if self.ask_widget0.currentIndex() == 4:
                            prompt = f"""You are an expert in semantics and grammar, teaching me how to learn. Please explain in {self.ask_widget4.currentText()} the meaning of every word in the text above and the meaning and the grammar structure of the text. If a word is part of an idiom, please explain the idiom and provide a few examples in {self.ask_widget4.currentText()} with similar meanings, along with their explanations. Before the text starts, write "「「START」」" and write "「「END」」” after it ends. Text: {str(self.ask_text1.toPlainText())}. """
                        if self.ask_widget0.currentIndex() == 5:
                            prompt = f"""You are a code explanation engine, you can only explain the code, do not interpret or translate it. Also, please report any bugs you find in the code to the author of the code. Must repeat in {self.ask_widget4.currentText()}. Before the text starts, write "「「START」」" and write "「「END」」” after it ends. Code: {str(self.ask_text1.toPlainText())}. """

                        response = await chat_gpt(prompt, conversation_history)
                        message = response.lstrip('assistant:').strip()
                        if self.ask_widget0.currentIndex() == 0 or self.ask_widget0.currentIndex() == 6:
                            ResultEnd = message.encode('utf-8').decode('utf-8', 'ignore')
                            uid = os.getuid()
                            env = os.environ.copy()
                            env['__CF_USER_TEXT_ENCODING'] = f'{uid}:0x8000100:0x8000100'
                            p = subprocess.Popen(['pbcopy', 'w'], stdin=subprocess.PIPE, env=env)
                            p.communicate(input=ResultEnd.encode('utf-8'))
                            message = message.lstrip('\n')
                            message = message.replace('\n', '\n\n\t')
                            message = message.replace('\n\n\t\n\n\t', '\n\n\t')
                            message = '\n\t' + message
                            QApplication.processEvents()
                            QApplication.restoreOverrideCursor()
                        if self.ask_widget0.currentIndex() == 1 or self.ask_widget0.currentIndex() == 2 or \
                                self.ask_widget0.currentIndex() == 3 or self.ask_widget0.currentIndex() == 4 or \
                                self.ask_widget0.currentIndex() == 5:
                            pattern = re.compile(r'「「START」」([\s\S]*?)「「END」」')
                            result = pattern.findall(message)
                            ResultEnd = ''.join(result)
                            ResultEnd = ResultEnd.encode('utf-8').decode('utf-8', 'ignore')
                            uid = os.getuid()
                            env = os.environ.copy()
                            env['__CF_USER_TEXT_ENCODING'] = f'{uid}:0x8000100:0x8000100'
                            p = subprocess.Popen(['pbcopy', 'w'], stdin=subprocess.PIPE, env=env)
                            p.communicate(input=ResultEnd.encode('utf-8'))
                            message = ResultEnd
                            message = message.lstrip('\n')
                            message = message.replace('\n', '\n\n\t')
                            message = message.replace('\n\n\t\n\n\t', '\n\n\t')
                            message = '\n\t' + message

                        EndMess = '- A: ' + message + '\n\n---\n\n'
                        with open(BasePath + 'output.txt', 'a',
                                  encoding='utf-8') as f1:
                            f1.write(EndMess)
                        ProcessText = codecs.open(BasePath + 'output.txt', 'r',
                                                  encoding='utf-8').read()
                        midhtml = w3.md2html(ProcessText)
                        w3.real1.setHtml(midhtml)
                        w3.real1.ensureCursorVisible()  # 游标可用
                        cursor = w3.real1.textCursor()  # 设置游标
                        pos = len(w3.real1.toPlainText())  # 获取文本尾部的位置
                        cursor.setPosition(pos)  # 游标位置设置为尾部
                        w3.real1.setTextCursor(cursor)  # 滚动到游标位置
                        QApplication.processEvents()
                        QApplication.restoreOverrideCursor()
                        self.ask_text1.clear()

                    asyncio.run(main())
                except TimeoutException:
                    with open(BasePath + 'output.txt', 'a',
                              encoding='utf-8') as f1:
                        f1.write('- A: Timed out, please try again!' + '\n\n---\n\n')
                    AllText = codecs.open(BasePath + 'output.txt', 'r',
                                          encoding='utf-8').read()
                    endhtml = w3.md2html(AllText)
                    w3.real1.setHtml(endhtml)
                    w3.real1.ensureCursorVisible()  # 游标可用
                    cursor = w3.real1.textCursor()  # 设置游标
                    pos = len(w3.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    w3.real1.setTextCursor(cursor)  # 滚动到游标位置
                    self.ask_text1.setPlainText(self.ask_LastQ)
                except Exception as e:
                    with open(BasePath + 'output.txt', 'a',
                              encoding='utf-8') as f1:
                        f1.write('- A: Error, please try again!' + str(e) + '\n\n---\n\n')
                    AllText = codecs.open(BasePath + 'output.txt', 'r',
                                          encoding='utf-8').read()
                    endhtml = w3.md2html(AllText)
                    w3.real1.setHtml(endhtml)
                    w3.real1.ensureCursorVisible()  # 游标可用
                    cursor = w3.real1.textCursor()  # 设置游标
                    pos = len(w3.real1.toPlainText())  # 获取文本尾部的位置
                    cursor.setPosition(pos)  # 游标位置设置为尾部
                    w3.real1.setTextCursor(cursor)  # 滚动到游标位置
                    self.ask_text1.setPlainText(self.ask_LastQ)
                signal.alarm(0)  # reset timer
                self.ask_text1.setReadOnly(False)
            if AccountGPT == '':
                w3.real1.setText('You should set your accounts in Settings.')
        self.ask_btn_0.setDisabled(False)
        self.close()
        applescript = """
            tell application "System Events"
                key code 9 using {command down}
            end tell
        """
        subprocess.call(["osascript", "-e", applescript])

    def bot2mode(self, i):
        home_dir = str(Path.home())
        tarname1 = "BroccoliAppPath"
        self.ask_fulldir1 = os.path.join(home_dir, tarname1)
        tarname3 = "lang.txt"
        fulldir3 = os.path.join(self.ask_fulldir1, tarname3)
        langs = codecs.open(fulldir3, 'r', encoding='utf-8').read()
        fulllanglist = []
        langs_list = ['English', '中文', '日本語']
        if langs != '':
            langs_list = langs.split('\n')
            while '' in langs_list:
                langs_list.remove('')
            for x in range(len(langs_list)):
                fulllanglist.append(langs_list[x])
        if langs == '':
            for x in range(len(langs_list)):
                fulllanglist.append(langs_list[x])
        if i == 0:
            self.ask_widget1.setVisible(False)
            self.ask_widget2.setVisible(False)
            self.ask_lbl1.setVisible(False)
            self.ask_widget4.setVisible(False)
            self.ask_widget5.setVisible(False)
            # length
            self.ask_widget0.setFixedWidth(370)
        if i == 1:
            self.ask_widget1.setVisible(True)
            self.ask_widget2.setVisible(True)
            self.ask_lbl1.setVisible(True)
            self.ask_widget4.setVisible(False)
            self.ask_widget5.setVisible(False)
            # renew 1
            self.ask_widget1.clear()
            self.ask_widget1.addItems(langs_list)
            # length
            self.ask_widget0.setFixedWidth(120)
        if i == 2:
            self.ask_widget1.setVisible(False)
            self.ask_widget2.setVisible(False)
            self.ask_lbl1.setVisible(True)
            self.ask_widget4.setVisible(True)
            self.ask_widget5.setVisible(False)
            # renew 4
            self.ask_widget4.clear()
            self.ask_widget4.addItems(fulllanglist)
            # length
            self.ask_widget0.setFixedWidth(170)
        if i == 3:
            self.ask_widget1.setVisible(False)
            self.ask_widget2.setVisible(False)
            self.ask_lbl1.setVisible(True)
            self.ask_widget4.setVisible(True)
            self.ask_widget5.setVisible(False)
            # renew 4
            self.ask_widget4.clear()
            self.ask_widget4.addItems(fulllanglist)
            # length
            self.ask_widget0.setFixedWidth(170)
        if i == 4:
            self.ask_widget1.setVisible(False)
            self.ask_widget2.setVisible(False)
            self.ask_lbl1.setVisible(True)
            self.ask_widget4.setVisible(True)
            self.ask_widget5.setVisible(False)
            # renew 4
            self.ask_widget4.clear()
            self.ask_widget4.addItems(fulllanglist)
            # length
            self.ask_widget0.setFixedWidth(170)
        if i == 5:
            self.ask_widget1.setVisible(False)
            self.ask_widget2.setVisible(False)
            self.ask_lbl1.setVisible(True)
            self.ask_widget4.setVisible(True)
            self.ask_widget5.setVisible(False)
            # renew 4
            self.ask_widget4.clear()
            self.ask_widget4.addItems(fulllanglist)
            # length
            self.ask_widget0.setFixedWidth(170)
        if i == 6:
            self.ask_widget1.setVisible(False)
            self.ask_widget2.setVisible(False)
            self.ask_lbl1.setVisible(True)
            self.ask_widget4.setVisible(False)
            self.ask_widget5.setVisible(True)
            self.ask_widget5.clear()
            home_dir = str(Path.home())
            tarname1 = "BroccoliAppPath"
            fulldir1 = os.path.join(home_dir, tarname1)
            if not os.path.exists(fulldir1):
                os.mkdir(fulldir1)
            tarname2 = "CustomPrompt.txt"
            fulldir2 = os.path.join(fulldir1, tarname2)
            if not os.path.exists(fulldir2):
                with open(fulldir2, 'a', encoding='utf-8') as f0:
                    f0.write('')
            customprompt = codecs.open(fulldir2, 'r', encoding='utf-8').read()
            promptlist = customprompt.split('---')
            while '' in promptlist:
                promptlist.remove('')
            itemlist = []
            for i in range(len(promptlist)):
                itemlist.append(promptlist[i].split('|><|')[0].replace('<|', '').replace('\n', ''))
            if itemlist != []:
                self.ask_widget5.addItems(itemlist)
            if itemlist == []:
                self.ask_widget5.addItems(['No customized prompts, please add one in Settings'])
            # length
            self.ask_widget0.setFixedWidth(170)

    def bot2trans(self):
        home_dir = str(Path.home())
        tarname1 = "BroccoliAppPath"
        fulldir1 = os.path.join(home_dir, tarname1)
        tarname3 = "lang.txt"
        fulldir3 = os.path.join(fulldir1, tarname3)
        currentlang = self.ask_widget1.currentText()
        self.ask_widget2.clear()
        langs = codecs.open(fulldir3, 'r', encoding='utf-8').read()
        if langs != '':
            langs_list = langs.split('\n')
            while '' in langs_list:
                langs_list.remove('')
            while currentlang in langs_list:
                langs_list.remove(currentlang)
            self.ask_widget2.addItems(langs_list)
            self.ask_widget2.setCurrentIndex(0)
        if langs == '':
            langs_list = ['English', '中文', '日本語']
            while currentlang in langs_list:
                langs_list.remove(currentlang)
            self.ask_widget2.addItems(langs_list)
            self.ask_widget2.setCurrentIndex(0)

    def bot2custom(self, i):
        home_dir = str(Path.home())
        tarname1 = "BroccoliAppPath"
        fulldir1 = os.path.join(home_dir, tarname1)
        if not os.path.exists(fulldir1):
            os.mkdir(fulldir1)
        tarname2 = "CustomPrompt.txt"
        fulldir2 = os.path.join(fulldir1, tarname2)
        if not os.path.exists(fulldir2):
            with open(fulldir2, 'a', encoding='utf-8') as f0:
                f0.write('')
        customprompt = codecs.open(fulldir2, 'r', encoding='utf-8').read()
        promptlist = customprompt.split('---')
        while '' in promptlist:
            promptlist.remove('')
        itemlist = []
        for n in range(len(promptlist)):
            itemlist.append(promptlist[n].split('|><|')[1].replace('|>', ''))
        if itemlist != []:
            try:
                self.ask_text1.clear()
                self.ask_text1.setPlainText(itemlist[i])
            except Exception as e:
                self.ask_text1.clear()
                self.ask_text1.setPlainText(e)

    def activate(self):  # 设置窗口显示
        # # Simulate Command+C shortcut
        applescript = """
            tell application "System Events"
                key code 8 using {command down}
            end tell
        """
        subprocess.call(["osascript", "-e", applescript])

        time.sleep(1)

        # # Copy to plaintext
        a = subprocess.check_output('pbpaste', env={'LANG': 'en_US.UTF-8'}).decode('utf-8')
        self.ask_text1.setPlainText(a)

        x, y = pyautogui.position()
        if x + 500 > self.WEIGHT:
            x = self.WEIGHT - 510
        if y + 150 > self.HEIGHT:
            y = self.HEIGHT - 150
        self.move(x, y)

        self.show()
        self.setFocus()
        self.raise_()
        self.activateWindow()

    def keyPressEvent(self, e):  # 当页面显示的时候，按下esc键可关闭窗口
        if e.key() == Qt.Key.Key_Escape.value:
            self.close()

    def cancel(self):  # 设置取消键的功能
        self.close()


style_sheet_ori = '''
    QTabWidget::pane {
        border: 1px solid #ECECEC;
        background: #ECECEC;
        border-radius: 9px;
}
    QWidget#Main {
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
    w5 = window5()
    w3.setAutoFillBackground(True)
    p = w3.palette()
    p.setColor(w3.backgroundRole(), QColor('#ECECEC'))
    w3.setPalette(p)
    action1.triggered.connect(w1.activate)
    action2.triggered.connect(w2.activate)
    action3.triggered.connect(w3.pin_a_tab)
    action4.triggered.connect(w4.activate)
    action5.triggered.connect(w3.OpenHistory)
    action6.triggered.connect(w3.chatfilemode)
    btna4.triggered.connect(w3.pin_a_tab)
    btna5.triggered.connect(w5.activate)
    w3.btn0_1.clicked.connect(w4.activate)
    w3.btn0_2.clicked.connect(w3.transferview)
    app.setStyleSheet(style_sheet_ori)
    app.exec()
