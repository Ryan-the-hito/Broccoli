"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['Broccoli.py']
DATA_FILES = ['Broccolimen.icns', 'Broccolidsk.icns', 'Broccolimen.png', 'wechat50.png', 'wechat20.png', 
              'wechat10.png', 'wechat5.png', 'alipay50.png', 'alipay20.png', 
              'alipay10.png', 'alipay5.png', 'api.txt', 'output.txt', 'which.txt']
OPTIONS = {'iconfile': 'Broccolidsk.icns',
           'packages': ['PyQt6', 'openai', 'markdown2', 'codecs', 'revChatGPT', 'transformers', 'pyperclip'],
           'plist': {
            'CFBundleShortVersionString': '0.1.5',
            'LSUIElement': True,
            },
           }

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    author='Ryan-the-hito',
    version='0.1.5'
)
