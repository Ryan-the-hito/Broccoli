# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


os.makedirs(os.path.join(SPECPATH, 'build', 'Broccoli'), exist_ok=True)

block_cipher = None

__version__ = '2.0.7'

browser_automation_hiddenimports = (
    collect_submodules('browser_use')
    + collect_submodules('playwright')
)
browser_automation_datas = (
    collect_data_files('browser_use')
    + collect_data_files('playwright')
)

common_hiddenimports = [
    'PyQt6.QtWebEngineWidgets',
    'PyQt6.QtWebEngineCore',
    'PyQt6.QtPdf',
    'fitz',
    'pdfminer.high_level',
    'PIL.Image',
    'pytesseract',
    'watchdog.observers',
    'watchdog.events',
    'anyio._backends._asyncio',
    *browser_automation_hiddenimports,
]

common_excludes = [
    'PyQt5', 'PyQt5_sip', 'PySide2', 'PySide6',
    'torch', 'torchvision', 'torchaudio', 'torchtext', 'torchao',
    'transformers', 'sentence_transformers',
    'tensorflow', 'onnxruntime', 'easyocr', 'cv2',
]

resource_datas = [
    ('Broccolimen.icns', '.'),
    ('Broccolidsk.icns', '.'),
    ('Broccolimen.png', '.'),
    ('wechat50.png', '.'),
    ('wechat20.png', '.'),
    ('wechat10.png', '.'),
    ('wechat5.png', '.'),
    ('alipay50.png', '.'),
    ('alipay20.png', '.'),
    ('alipay10.png', '.'),
    ('alipay5.png', '.'),
    ('api.txt', '.'),
    ('output.txt', '.'),
    ('which.txt', '.'),
    ('command.txt', '.'),
    ('history.txt', '.'),
    ('wp.txt', '.'),
    ('api2.txt', '.'),
    ('bear.txt', '.'),
    ('third.txt', '.'),
    ('timeout.txt', '.'),
    ('showref.txt', '.'),
    ('set2.png', '.'),
    ('plus2.png', '.'),
    ('modelnow.txt', '.'),
    ('transfer2.png', '.'),
    ('UI_short.txt', '.'),
    ('showhide.txt', '.'),
    ('/Users/ryanshen/Documents/A-workingfilewithp3.11/.venv/lib/python3.11/site-packages/jieba/', 'jieba'),
    *browser_automation_datas,
]


a = Analysis(
    ['Broccoli.py', 'browser_use_worker.py'],
    pathex=['/Users/ryanshen/Downloads/new'],
    binaries=[],
    datas=resource_datas,
    hiddenimports=common_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=common_excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

runtime_scripts = [script for script in a.scripts if script[0].startswith('pyi_rth_')]
main_scripts = runtime_scripts + [script for script in a.scripts if script[0] == 'Broccoli']
worker_scripts = runtime_scripts + [script for script in a.scripts if script[0] == 'browser_use_worker']

if len(main_scripts) != len(runtime_scripts) + 1:
    raise RuntimeError('Broccoli entry script was not found in PyInstaller analysis output.')
if len(worker_scripts) != len(runtime_scripts) + 1:
    raise RuntimeError('Browser Use worker entry script was not found in PyInstaller analysis output.')

exe = EXE(
    pyz,
    main_scripts,
    [],
    exclude_binaries=True,
    name='Broccoli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
worker_exe = EXE(
    pyz,
    worker_scripts,
    [],
    exclude_binaries=True,
    name='BroccoliBrowserUseWorker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    worker_exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Broccoli',
)
app = BUNDLE(
    coll,
    name='Broccoli.app',
    icon='Broccolidsk.icns',
    bundle_identifier=None,
    version=__version__,
)
