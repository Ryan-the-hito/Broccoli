#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt6.QtWidgets import (QWidget, QPushButton, QApplication,
                             QLabel, QHBoxLayout, QVBoxLayout,
                             QSystemTrayIcon, QMenu, QDialog, QLineEdit, QTextEdit, QPlainTextEdit, QFileDialog)
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