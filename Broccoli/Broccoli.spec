# -*- mode: python ; coding: utf-8 -*-
# Broccoli.app — build from this folder with the project's PyInstaller:
#     /Users/ryanshen/Documents/A-workingfilewithp3.11/.venv/bin/pyinstaller --noconfirm Broccoli.spec
#
# Everything the app needs sits next to this spec (checked 2026-10-26, Broccoli_26new-337):
#   Broccoli.py (= Broccoli_26new.py), browser_use_worker.py, computer_use_worker.py,
#   computer_use_display.py, computer_use_experience.py, smooth_widgets.py,
#   the images / icons / default .txt files below, vendor/ (xterm + mermaid.min.js),
#   i18n/*.qm (Chinese / Japanese UI), MathJax-2.7.1/ (formulas in the Agent conversation),
#   open_connector/ (2026-10-29: the built-in Open Connector server — Settings › Connected apps),
#   codexbar/ (2026-10-30: CodexBar's command-line build for the usage bars — Settings › Usage),
#   agentsview/ (2026-10-31: reads the AI sessions on this Mac for the AI tasks column — Settings › AI tasks).
# A missing one stops the build (REQUIRED below) instead of shipping an app without it.
# (Last synced from the source folder 2026-11-02, Broccoli_26new-374.)
#
# Open Connector: open_connector/ is refreshed from the source folder's open_connector_update.py
# (official release build, checksum, licence check, test run). The server goes into
# Contents/Frameworks/open_connector as an executable. SIGN IT LIKE THE APP, with the same
# entitlements.plist (allow-jit …): it is a JavaScript engine and runs much faster with JIT —
#     codesign --force --options runtime --timestamp --entitlements entitlements.plist \
#         --sign "Developer ID Application: <your name> (<team id>)" \
#         dist/Broccoli.app/Contents/Frameworks/open_connector/open-connector-darwin-arm64
# then sign the app as usual (an app signed with --deep re-signs it the same way) and notarize.
#
# CodexBar: codexbar/ is refreshed with the source folder's external_update.py (update codexbar
# --copy-to <this folder>): official release, checksum, licence check (MIT), test run. Its
# CodexBarCLI goes into Contents/Frameworks/codexbar as an executable and must find its plug-in
# bundle CodexBar_CodexBarCore.bundle beside it (shipped as data, linked in next to it). Sign it
# like Open Connector:
#     codesign --force --options runtime --timestamp --entitlements entitlements.plist \
#         --sign "Developer ID Application: <your name> (<team id>)" \
#         dist/Broccoli.app/Contents/Frameworks/codexbar/CodexBarCLI
# It is the only CodexBar the app uses (no CodexBar app needed); its settings live in
# ~/BroccoliAppPath/CodexBar/config.json.
#
# agentsview: agentsview/ is refreshed with external_update.py (update agentsview --copy-to <this
# folder>): official release, checksum, licence check (MIT), test run. Its single executable goes
# into Contents/Frameworks/agentsview (the app looks in sys._MEIPASS/agentsview). Sign it like the
# others (it is a Go program and needs no JIT, the entitlements do no harm):
#     codesign --force --options runtime --timestamp --entitlements entitlements.plist \
#         --sign "Developer ID Application: <your name> (<team id>)" \
#         dist/Broccoli.app/Contents/Frameworks/agentsview/agentsview
# Its data lives in ~/BroccoliAppPath/AgentsView.
#
# Claude CLI (INCLUDE_CLAUDE_CLI): also a JavaScript engine; Anthropic ships it signed with allow-jit,
# so once re-signed it needs the same entitlements or it may not start:
#     codesign --force --options runtime --timestamp --entitlements entitlements.plist \
#         --sign "Developer ID Application: <your name> (<team id>)" \
#         dist/Broccoli.app/Contents/Frameworks/claude_agent_sdk/_bundled/claude
#
# Order: these four first, the app last (signing anything inside afterwards breaks the app's
# signature). Signing the app with --deep re-signs them as well: give that command the same
# --options runtime --timestamp --entitlements entitlements.plist, or they lose JIT.

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
    # 2026-10-28: the terminal tab's wide characters, renderers and clickable links
    'vendor/xterm/addon-unicode11.js', 'vendor/xterm/addon-webgl.js', 'vendor/xterm/addon-canvas.js',
    'vendor/xterm/addon-web-links.js',
    'i18n/broccoli_zh_CN.qm', 'i18n/broccoli_ja_JP.qm',
    'MathJax-2.7.1/MathJax.js', 'MathJax-2.7.1/config/TeX-MML-AM_CHTML.js',
    # 2026-10-29: the built-in Open Connector server, what it was taken from and its licence
    'open_connector/open-connector-darwin-arm64', 'open_connector/manifest.json',
    'open_connector/LICENSE.txt', 'open_connector/NOTICE.md',
    # 2026-10-30: CodexBar's command-line build (usage bars), its plug-in bundle and licences
    'codexbar/CodexBarCLI', 'codexbar/manifest.json', 'codexbar/LICENSE.txt', 'codexbar/THIRD_PARTY_NOTICES',
    'codexbar/VERSION', 'codexbar/CodexBar_CodexBarCore.bundle/Contents/Info.plist',
    # 2026-10-31: agentsview (AI tasks column), what it was taken from and its licence
    'agentsview/agentsview', 'agentsview/manifest.json', 'agentsview/LICENSE.txt',
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
    'PyQt6.QtWebChannel',        # 2026-10-28: the terminal tab talks to xterm through it
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
    'Security',                  # 2026-10-29: Open Connector's key and tokens live in the keychain
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
    # what the bundled Open Connector server was taken from (version, checksum) and its licence
    ('open_connector/manifest.json', 'open_connector'),
    ('open_connector/LICENSE.txt', 'open_connector'),
    ('open_connector/NOTICE.md', 'open_connector'),
    # CodexBar (usage bars): what it was taken from, its licences, and the plug-in bundle the
    # command-line build loads from beside itself
    ('codexbar/manifest.json', 'codexbar'),
    ('codexbar/LICENSE.txt', 'codexbar'),
    ('codexbar/THIRD_PARTY_NOTICES', 'codexbar'),
    ('codexbar/VERSION', 'codexbar'),
    *folder_datas('codexbar/CodexBar_CodexBarCore.bundle'),
    # agentsview (AI tasks column): what it was taken from (the settings page shows its version)
    # and its licence
    ('agentsview/manifest.json', 'agentsview'),
    ('agentsview/LICENSE.txt', 'agentsview'),
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

# the Open Connector server: an executable, next to its manifest (the app looks in
# sys._MEIPASS/open_connector); never UPX-compressed (it carries its JavaScript bundle inside)
OPEN_CONNECTOR_BINARY = 'open-connector-darwin-arm64'
open_connector_binaries = [(str(SPEC_DIR / 'open_connector' / OPEN_CONNECTOR_BINARY), 'open_connector')]
# CodexBar's command-line build (usage bars): an executable in sys._MEIPASS/codexbar; not UPX-compressed
CODEXBAR_BINARY = 'CodexBarCLI'
codexbar_binaries = [(str(SPEC_DIR / 'codexbar' / CODEXBAR_BINARY), 'codexbar')]
# agentsview (AI tasks column): an executable in sys._MEIPASS/agentsview; not UPX-compressed
AGENTSVIEW_BINARY = 'agentsview'
agentsview_binaries = [(str(SPEC_DIR / 'agentsview' / AGENTSVIEW_BINARY), 'agentsview')]


a = Analysis(
    ['Broccoli.py', 'browser_use_worker.py', 'computer_use_worker.py'],
    pathex=[str(SPEC_DIR)],
    binaries=claude_cli_binaries + open_connector_binaries + codexbar_binaries + agentsview_binaries,
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
    upx_exclude=[OPEN_CONNECTOR_BINARY, CODEXBAR_BINARY, AGENTSVIEW_BINARY],
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
        'NSAppleEventsUsageDescription': 'Broccoli reads and writes your Apple Notes and Reminders and controls other apps when you ask it to.',
    },
)
