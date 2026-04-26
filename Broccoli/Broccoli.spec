# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

__version__ = '2.0.2'


a = Analysis(
    ['Broccoli.py'],
    pathex=['/Users/ryanshen/Downloads/Broccoli.py'],
    binaries=[],
    datas=[('Broccolimen.icns', '.'), ('Broccolidsk.icns', '.'), ('Broccolimen.png', '.'), ('wechat50.png', '.'), ('wechat20.png', '.'), ('wechat10.png', '.'), ('wechat5.png', '.'), ('alipay50.png', '.'), ('alipay20.png', '.'), ('alipay10.png', '.'), ('alipay5.png', '.'), ('api.txt', '.'), ('output.txt', '.'), ('which.txt', '.'), ('command.txt', '.'), ('history.txt', '.'), ('wp.txt', '.'), ('api2.txt', '.'), ('bear.txt', '.'), ('third.txt', '.'), ('timeout.txt', '.'), ('showref.txt', '.'), ('set2.png', '.'), ('plus2.png', '.'), ('modelnow.txt', '.'), ('transfer2.png', '.'), ('UI_short.txt', '.'), ('showhide.txt', '.'), ('/Users/ryanshen/Documents/A-workingfilewithp3.11/.venv/lib/python3.11/site-packages/jieba/', 'jieba')],
    hiddenimports=[
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
],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt5_sip', 'PySide2', 'PySide6'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
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
coll = COLLECT(
    exe,
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
