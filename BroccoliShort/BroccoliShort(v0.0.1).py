#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import threading
from PyQt6.QtWidgets import QApplication, QWidget
from pynput import keyboard
import codecs
import subprocess

class Window1(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()
        self.listener_thread = threading.Thread(target=self.start_listener)
        self.listener_thread.start()  # 启动监听器线程

    def initUI(self):
        uishort = codecs.open('/Applications/Broccoli.app/Contents/Resources/UI_short.txt', 'r',
                              encoding='utf-8').read()
        if uishort == '':
            uishort = '<ctrl>+<alt>+b'

        minishort = codecs.open('/Applications/Broccoli.app/Contents/Resources/MINI_short.txt', 'r',
                                encoding='utf-8').read()

        if minishort == '':
            minishort = '<ctrl>+<alt>+m'

        self.hotkey1 = keyboard.HotKey(keyboard.HotKey.parse(uishort), self.on_activate1)
        self.hotkey2 = keyboard.HotKey(keyboard.HotKey.parse(minishort), self.on_activate2)

    def on_activate1(self):
        cmd = """
        on run
  	        tell application "System Events" to tell process "Broccoli"
		        click menu item "Pin!" of menu "Actions" of menu bar item "Actions" of menu bar 1 of application process "Broccoli" of application "System Events"
	        end tell
        end run
        """
        try:
            subprocess.call(['osascript', '-e', cmd])
        except Exception as e:
            pass

    def on_activate2(self):
        cmd = """
        on run
  	        tell application "System Events" to tell process "Broccoli"
		        click menu item "Ask!" of menu "Actions" of menu bar item "Actions" of menu bar 1 of application process "Broccoli" of application "System Events"
	        end tell
        end run
        """
        try:
            subprocess.call(['osascript', '-e', cmd])
        except Exception as e:
            pass

    def start_listener(self):

        def for_canonical(l, f):
            return lambda k: f(l.canonical(k))

        def on_press(key):
            self.hotkey1.press(key)
            self.hotkey2.press(key)

        def on_release(key):
            self.hotkey1.release(key)
            self.hotkey2.release(key)

        with keyboard.Listener(
                on_press=on_press,
                on_release=on_release) as listener:
            listener.join()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w1 = Window1()
    app.exec()
