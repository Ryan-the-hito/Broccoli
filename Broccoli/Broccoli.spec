# -*- mode: python ; coding: utf-8 -*-
# Broccoli.app — build from this folder with the project's PyInstaller:
#     /Users/ryanshen/Documents/A-workingfilewithp3.11/.venv/bin/pyinstaller --noconfirm Broccoli.spec
#
# Everything the app needs sits next to this spec (checked 2026-10-26, Broccoli_26new-337):
#   Broccoli.py (= Broccoli_26new.py), browser_use_worker.py, computer_use_worker.py,
#   computer_use_display.py, computer_use_experience.py, smooth_widgets.py,
#   the images / icons / default .txt files below, vendor/ (xterm + mermaid.min.js),
#   i18n/*.qm (Chinese / Japanese UI), MathJax-2.7.1/ (formulas in the Agent conversation).
# A missing one stops the build (REQUIRED below) instead of shipping an app without it.

import os
import re
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

SPEC_DIR = Path(SPECPATH)

os.makedirs(os.path.join(SPECPATH, 'build', 'Broccoli'), exist_ok=True)

block_cipher = None

# The version is the app's own (VERSION = '…' in Broccoli.py): the bundle, its Info.plist and the
# in-app updater never disagree. Raise it there before a release.
_version = re.search(r"^VERSION\s*=\s*['\"]([^'\"]+)['\"]",
                     (SPEC_DIR / 'Broccoli.py').read_text(encoding='utf-8'), re.M)
if not _version:
    raise RuntimeError('VERSION = "…" was not found in Broccoli.py')
__version__ = _version.group(1)

# Claude Code sessions go through claude_agent_sdk. It first runs the Claude CLI bundled inside
# the SDK (~240 MB, arm64) — what the app uses when run from source — and only otherwise looks for
# an installed `claude` (~/.npm-global/bin, ~/.local/bin, /usr/local/bin …).
# True: ship it (the packaged app behaves like the source). False: rely on the installed CLI.
INCLUDE_CLAUDE_CLI = True

REQUIRED = [
    'Broccoli.py', 'browser_use_worker.py', 'computer_use_worker.py',
    'computer_use_display.py', 'computer_use_experience.py', 'smooth_widgets.py',
    'Broccolimen.icns', 'Broccolidsk.icns', 'Broccolimen.png',
    'plus2.png', 'set2.png', 'transfer2.png', 'list.png',
    'wechat50.png', 'wechat20.png', 'wechat10.png', 'wechat5.png',
    'alipay50.png', 'alipay20.png', 'alipay10.png', 'alipay5.png',
    'api.txt', 'api2.txt', 'bear.txt', 'output.txt', 'which.txt', 'command.txt', 'history.txt',
    'wp.txt', 'third.txt', 'timeout.txt', 'showref.txt', 'modelnow.txt', 'UI_short.txt', 'showhide.txt',
    'vendor/xterm/xterm.js', 'vendor/xterm/xterm.css', 'vendor/xterm/addon-fit.js', 'vendor/mermaid.min.js',
    'i18n/broccoli_zh_CN.qm', 'i18n/broccoli_ja_JP.qm',
    'MathJax-2.7.1/MathJax.js', 'MathJax-2.7.1/config/TeX-MML-AM_CHTML.js',
]
_missing = [name for name in REQUIRED if not (SPEC_DIR / name).is_file()]
if _missing:
    raise RuntimeError('Missing next to Broccoli.spec: ' + ', '.join(_missing))


def folder_datas(folder, target=None, skip=(), only_suffixes=None):
    """Every file of a folder next to this spec, keeping its layout; without .DS_Store,
    __pycache__ and the relative sub-folders in `skip`."""
    base = SPEC_DIR / folder
    target = Path(target or folder)
    out = []
    for root, dirs, files in os.walk(base):
        rel = Path(root).relative_to(base)
        dirs[:] = sorted(d for d in dirs if d != '__pycache__' and (rel / d).as_posix() not in skip)
        for name in sorted(files):
            if name == '.DS_Store' or (only_suffixes and not name.endswith(only_suffixes)):
                continue
            out.append((str(Path(root) / name), str(target / rel)))
    return out


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
    # imported inside functions / try blocks (the static scan usually finds them; listed to be sure)
    'smooth_widgets',
    'charset_normalizer',        # the editor's file-encoding detection
    'objc', 'AppKit', 'Foundation', 'CoreFoundation', 'Quartz', 'Vision', 'UserNotifications',
    # Computer Use worker helpers (imported lazily inside the worker):
    'computer_use_display',
    'computer_use_experience',
    *collect_submodules('claude_agent_sdk'),
    *collect_submodules('mcp'),
    *browser_automation_hiddenimports,
]

common_excludes = [
    'PyQt5', 'PyQt5_sip', 'PySide2', 'PySide6',
    'torch', 'torchvision', 'torchaudio', 'torchtext', 'torchao',
    'transformers', 'sentence_transformers',
    'tensorflow', 'onnxruntime', 'easyocr', 'cv2',
]

import jieba as _jieba   # its dictionary is loaded from the package folder

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
    ('list.png', '.'),
    (os.path.dirname(_jieba.__file__), 'jieba'),
    # xterm (terminal tab) + mermaid.min.js (editor diagrams)
    *folder_datas('vendor'),
    # UI translations: the app loads sys._MEIPASS/i18n/broccoli_<lang>.qm when frozen
    *folder_datas('i18n', only_suffixes=('.qm',)),
    # formulas in the Agent conversation (config TeX-MML-AM_CHTML = CommonHTML output with the
    # woff web fonts): the 114 MB PNG image fonts and the 20 MB unminified copy are never loaded
    *folder_datas('MathJax-2.7.1', skip=('unpacked', 'fonts/HTML-CSS/TeX/png')),
    *browser_automation_datas,
]

claude_cli_binaries = []
if INCLUDE_CLAUDE_CLI:
    import claude_agent_sdk as _claude_sdk
    _claude_cli = Path(_claude_sdk.__file__).parent / '_bundled' / 'claude'
    if not _claude_cli.is_file():
        raise RuntimeError(f'INCLUDE_CLAUDE_CLI is on but {_claude_cli} is missing')
    # where the SDK looks for it: <package>/_bundled/claude
    claude_cli_binaries.append((str(_claude_cli), 'claude_agent_sdk/_bundled'))


a = Analysis(
    ['Broccoli.py', 'browser_use_worker.py', 'computer_use_worker.py'],
    pathex=[str(SPEC_DIR)],
    binaries=claude_cli_binaries,
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
cua_worker_scripts = runtime_scripts + [script for script in a.scripts if script[0] == 'computer_use_worker']

if len(main_scripts) != len(runtime_scripts) + 1:
    raise RuntimeError('Broccoli entry script was not found in PyInstaller analysis output.')
if len(worker_scripts) != len(runtime_scripts) + 1:
    raise RuntimeError('Browser Use worker entry script was not found in PyInstaller analysis output.')
if len(cua_worker_scripts) != len(runtime_scripts) + 1:
    raise RuntimeError('Computer Use worker entry script was not found in PyInstaller analysis output.')

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
# Computer Use helper — the main app resolves it as a sibling executable named
# exactly 'BroccoliComputerUseWorker' (see computer_use_worker_command()).
cua_worker_exe = EXE(
    pyz,
    cua_worker_scripts,
    [],
    exclude_binaries=True,
    name='BroccoliComputerUseWorker',
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
    cua_worker_exe,
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
    # the in-app updater accepts only a bundle with exactly this identifier (BROCCOLI_UPDATE_BUNDLE_ID)
    bundle_identifier='Broccoli',
    version=__version__,
    info_plist={
        'CFBundleShortVersionString': __version__,
        'CFBundleVersion': __version__,
        # as the installed app has it (the console workers made PyInstaller set it): Broccoli shows
        # or hides its own Dock icon at run time
        'LSBackgroundOnly': True,
        'NSHighResolutionCapable': True,
        # Apple Notes and other apps are driven through osascript (macOS asks the user once)
        'NSAppleEventsUsageDescription': 'Broccoli reads and writes your Apple Notes and controls other apps when you ask it to.',
    },
)
