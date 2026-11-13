# -*- mode: python ; coding: utf-8 -*-
# Broccoli.app — build from this folder with the project's PyInstaller:
#     /Users/ryanshen/Documents/A-workingfilewithp3.11/.venv/bin/pyinstaller --noconfirm Broccoli.spec
#
# Everything the app needs sits next to this spec (checked 2026-10-26, Broccoli_26new-337):
#   Broccoli.py (= Broccoli_26new.py), browser_use_worker.py, computer_use_worker.py,
#   broccoli_python.py (2026-11-12: the app's own Python for the code runner — see "BroccoliPython" below),
#   computer_use_display.py, computer_use_experience.py, smooth_widgets.py,
#   the images / icons / default .txt files below, vendor/ (xterm + mermaid.min.js),
#   i18n/*.qm (Chinese / Japanese UI), MathJax-2.7.1/ (formulas in the Agent conversation),
#   open_connector/ (2026-10-29: the built-in Open Connector server — Settings › Connected apps),
#   codexbar/ (2026-10-30: CodexBar's command-line build for the usage bars — Settings › Usage),
#   agentsview/ (2026-10-31: reads the AI sessions on this Mac for the AI tasks column — Settings › AI tasks),
#   office_editor/ + office_editor_bridge.py + office_files.py (2026-11-11: Word / Excel / PowerPoint in
#   the editor — see "Office editor" below),
#   cli_proxy/ (2026-11-12: CLIProxyAPI for subscription sign-ins — Settings › Models › Subscriptions).
# A missing one stops the build (REQUIRED below) instead of shipping an app without it.
# (Last synced from the source folder 2026-11-13, Broccoli_26new-464 = 2.0.18; Open Connector v1.10.0,
#  CodexBar v0.84.0, agentsview v0.47.0, CLIProxyAPI v8.0.69, Office editor v0.0.9 — all the latest
#  releases on 2026-11-13; claude-agent-sdk 0.2.181 (Claude Code 2.1.323), openai-codex-cli-bin 0.169.0
#  (Codex 0.169.0). Built with
#  PyInstaller 6.22.3 + hooks-contrib 2026.10: PyMuPDF 2.x and charset-normalizer 3.5 need its hooks.)
#
# BroccoliPython (2026-11-12): a fourth program in Contents/MacOS, built from broccoli_python.py like
# the two workers and sharing their libraries. It reads a command line like python3 and is what
# Settings › General › Code runners uses for Python in the packaged app (the main program is not a
# Python command: started with "-I -c <code>" it is a second Broccoli that leaves at once, status 0,
# no output). It can import everything the app ships (numpy, pandas, requests, openpyxl …) and the
# whole standard library (standard_library_modules() below adds what the app itself never imports).
# Nothing extra to sign: it is signed with the app, like the workers.
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
# CLIProxyAPI (2026-11-12): cli_proxy/ is refreshed with external_update.py (update cli_proxy
# --copy-to <this folder>): official release, checksum, licence check (MIT), test run. Its single
# executable goes into Contents/Frameworks/cli_proxy (the app looks in sys._MEIPASS/cli_proxy). Sign
# it like agentsview (a Go program too):
#     codesign --force --options runtime --timestamp --entitlements entitlements.plist \
#         --sign "Developer ID Application: <your name> (<team id>)" \
#         dist/Broccoli.app/Contents/Frameworks/cli_proxy/cli-proxy-api
# Its settings and sign-ins live in the user's data folder (CLIProxy/).
#
# Office editor (2026-11-11): office_editor/ is the bundled office-editing component (ranuts/document
# = the ONLYOFFICE web editors + their converter as WebAssembly, AGPL-3.0, ~530 MB of static files).
# It is refreshed as a whole with the source folder's external_update.py (update office_editor
# --copy-to <this folder>): the release's container image is read from the registry, checked, test-run
# (open + save a Word, an Excel and a PowerPoint file with the network blocked) and only then put in
# place; nothing inside office_editor/site is ever edited (corrections live in manifest.json "fixups").
# All of it ships as data in sys._MEIPASS/office_editor: nothing in it is an executable, so there is
# nothing extra to sign. office_editor_bridge.py (the local file server + the one adapter class that
# knows this component) and office_files.py (text view of .docx / .xlsx / .pptx for the AI edit flow;
# needs python-docx, openpyxl, python-pptx, lxml) are plain modules next to Broccoli.py. Without the
# folder the app still runs: office files then open in the Reader only.
#
# Claude CLI (INCLUDE_CLAUDE_CLI): also a JavaScript engine; Anthropic ships it signed with allow-jit,
# so once re-signed it needs the same entitlements or it may not start:
#     codesign --force --options runtime --timestamp --entitlements entitlements.plist \
#         --sign "Developer ID Application: <your name> (<team id>)" \
#         dist/Broccoli.app/Contents/Frameworks/claude_agent_sdk/_bundled/claude
#
# Codex (INCLUDE_CODEX_CLI, 2026-11-10): OpenAI's native programs from the PyPI package
# openai-codex-cli-bin, signed by OpenAI with hardened runtime; codex and codex-code-mode-host use
# allow-jit + allow-unsigned-executable-memory (in entitlements.plist), so give all four the same:
#     for f in bin/codex bin/codex-code-mode-host bin/codex-exec-server codex-path/rg; do
#       codesign --force --options runtime --timestamp --entitlements entitlements.plist \
#         --sign "Developer ID Application: <your name> (<team id>)" \
#         "dist/Broccoli.app/Contents/Frameworks/codex_cli_bin/$f"; done
#
# QtWebEngine placeholder version (2026-11-07; put in by the end of this spec, the reason is there):
# a tiny do-nothing library that `codesign --deep` on the app does NOT reach. Sign it with the same
# identity (no entitlements: it never runs):
#     codesign --force --options runtime --timestamp \
#         --sign "Developer ID Application: <your name> (<team id>)" \
#         dist/Broccoli.app/Contents/Frameworks/PyQt6/Qt6/lib/QtWebEngineCore.framework/Versions/Resources
#
# Order: these (Codex: four files) first, the app last (signing anything inside afterwards breaks the app's
# signature). Signing the app with --deep re-signs the first four as well (not the placeholder): give
# that command the same --options runtime --timestamp --entitlements entitlements.plist, or they
# lose JIT. Check before notarizing: codesign --verify --deep --strict dist/Broccoli.app (silent = good).

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

# @Codex runs the Codex OpenAI ships in its PyPI package openai-codex-cli-bin (module codex_cli_bin:
# bin/codex + helpers, ~400 MB arm64, Apache-2.0) first, and only otherwise an installed `codex`
# (Ryan 2026-11-10: both Agent targets use the bundled copies). The app looks for it where the
# package's own bundled_codex_path() points: <package>/bin/codex beside codex-package.json.
INCLUDE_CODEX_CLI = True

REQUIRED = [
    'Broccoli.py', 'browser_use_worker.py', 'computer_use_worker.py', 'broccoli_python.py',
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
    # 2026-11-07: from v1.9.9 on LICENSE.txt is "Apache 2.0 with OOMOL conditions" and points at the
    # full Apache 2.0 text, shipped beside it
    'open_connector/LICENSE-APACHE-2.0.txt',
    # 2026-10-30: CodexBar's command-line build (usage bars), its plug-in bundle and licences
    'codexbar/CodexBarCLI', 'codexbar/manifest.json', 'codexbar/LICENSE.txt', 'codexbar/THIRD_PARTY_NOTICES',
    'codexbar/VERSION', 'codexbar/CodexBar_CodexBarCore.bundle/Contents/Info.plist',
    # 2026-10-31: agentsview (AI tasks column), what it was taken from and its licence
    'agentsview/agentsview', 'agentsview/manifest.json', 'agentsview/LICENSE.txt',
    # 2026-11-12: CLIProxyAPI (subscription sign-ins), what it was taken from and its licence (MIT)
    'cli_proxy/cli-proxy-api', 'cli_proxy/manifest.json', 'cli_proxy/LICENSE.txt',
    # 2026-11-10: the bundled Codex's licence (Apache-2.0) and notice, from openai/codex rust-v0.167.0
    # (2026-11-13: byte-identical in rust-v0.169.0, the bundled version now)
    'codex_cli/LICENSE.txt', 'codex_cli/NOTICE.txt',
    # 2026-11-11: Word / Excel / PowerPoint in the editor — the two modules, the component, what it
    # was taken from and its licence (AGPL-3.0) and notice
    'office_files.py', 'office_editor_bridge.py',
    'office_editor/manifest.json', 'office_editor/LICENSE.txt', 'office_editor/NOTICE.txt',
    'office_editor/site/editor.html', 'office_editor/site/sdkjs/common/AllFonts.js',
    'office_editor/site/sdkjs/common/wasm/x2t/x2t.wasm.br',
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

# BroccoliPython runs code the models write, so it gets the whole standard library, not only the
# part the app happens to import (shelve, wave, filecmp, graphlib, cProfile, imaplib … were missing).
# Left out: what needs Tcl/Tk, the test suites, the installers, and site (a packaged Python has none).
STDLIB_NOT_SHIPPED = {
    'tkinter', '_tkinter', 'turtle', 'turtledemo', 'idlelib',
    'test', 'lib2to3', 'distutils', 'ensurepip', 'venv',
    'site', 'sitecustomize', 'usercustomize',
    'antigravity', 'this', '__hello__', '__phello__',
}


def standard_library_modules():
    """Every module of this Python's standard library that exists on this Mac, packages with all
    their modules (read from disk, nothing is imported)."""
    import importlib.util
    import sys

    names = []
    for name in sorted(sys.stdlib_module_names):
        if name in STDLIB_NOT_SHIPPED or name.startswith(('_test', '_xx', 'xx', '_ctypes_test')):
            continue
        try:
            found = importlib.util.find_spec(name)
        except Exception:
            found = None
        if found is None:
            continue
        names.append(name)
        for location in (found.submodule_search_locations or []):
            for root, dirs, files in os.walk(location):
                dirs[:] = sorted(d for d in dirs if d not in ('__pycache__', 'test', 'tests', 'idle_test')
                                 and os.path.isfile(os.path.join(root, d, '__init__.py')))
                prefix = '.'.join((name, *Path(root).relative_to(location).parts))
                if root != location:
                    names.append(prefix)
                names.extend(f'{prefix}.{f[:-3]}' for f in sorted(files)
                             if f.endswith('.py') and f not in ('__init__.py', '__main__.py'))
    return names


common_hiddenimports = [
    *standard_library_modules(),
    'PyQt6.QtWebEngineWidgets',
    'PyQt6.QtWebEngineCore',
    'PyQt6.QtWebChannel',        # 2026-10-28: the terminal tab talks to xterm through it
    'PyQt6.QtPdf',               # 2026-11-10: PyQt6 6.12 ships it as its own package (PyQt6-Pdf)
    'pymupdf',                   # 2026-11-10: PyMuPDF 2.x; the old name 'fitz' is no longer used
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
    # 2026-11-13 sync (427–462): reading other apps' windows for the circle's scan, file thumbnails
    # for its tray, and the password-locked model-profile files
    'ApplicationServices', 'QuickLookThumbnailing',
    'cryptography.exceptions', 'cryptography.hazmat.primitives.ciphers.aead',
    'cryptography.hazmat.primitives.kdf.scrypt',
    # Computer Use worker helpers (imported lazily inside the worker):
    'computer_use_display',
    'computer_use_experience',
    *collect_submodules('claude_agent_sdk'),
    'codex_cli_bin',             # 2026-11-10: finds the bundled Codex (bundled_codex_path)
    # 2026-11-11: office files in the editor (imported inside try blocks in Broccoli.py)
    'office_files', 'office_editor_bridge', 'docx', 'pptx', 'openpyxl', 'lxml.etree',
    'openpyxl.formula.translate', 'openpyxl.styles.numbers', 'openpyxl.utils.datetime',
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
    ('open_connector/LICENSE-APACHE-2.0.txt', 'open_connector'),
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
    # CLIProxyAPI (subscription sign-ins): what it was taken from (the settings page shows its
    # version) and its licence
    ('cli_proxy/manifest.json', 'cli_proxy'),
    ('cli_proxy/LICENSE.txt', 'cli_proxy'),
    # the bundled Codex: its licence and notice beside it
    ('codex_cli/LICENSE.txt', 'codex_cli_bin'),
    ('codex_cli/NOTICE.txt', 'codex_cli_bin'),
    # the office-editing component, whole (the app looks in sys._MEIPASS/office_editor); the copy
    # kept for a rollback (site.previous) and an interrupted update's work folder stay behind
    *[item for item in folder_datas('office_editor')
      if not Path(item[1]).as_posix().startswith(('office_editor/site.previous', 'office_editor/update_'))],
    # python-docx / python-pptx read their blank templates from their package folders
    *collect_data_files('docx'),
    *collect_data_files('pptx'),
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

codex_cli_binaries, codex_cli_datas = [], []
if INCLUDE_CODEX_CLI:
    import codex_cli_bin as _codex_cli_bin
    _codex_dir = Path(_codex_cli_bin.__file__).parent
    _codex_files = ['bin/codex', 'bin/codex-code-mode-host', 'bin/codex-exec-server', 'codex-path/rg']
    _codex_missing = [f for f in _codex_files + ['codex-package.json'] if not (_codex_dir / f).is_file()]
    if _codex_missing:
        raise RuntimeError(f'INCLUDE_CODEX_CLI is on but {_codex_dir} lacks: ' + ', '.join(_codex_missing))
    # same layout as the package: bundled_codex_path() needs codex-package.json beside bin/
    codex_cli_binaries = [(str(_codex_dir / f), 'codex_cli_bin/' + os.path.dirname(f)) for f in _codex_files]
    codex_cli_datas = [(str(_codex_dir / 'codex-package.json'), 'codex_cli_bin')]

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
# CLIProxyAPI (2026-11-12, subscription sign-ins — Settings › Models › Subscriptions): an executable in
# sys._MEIPASS/cli_proxy (cli_proxy_binary_path); not UPX-compressed
CLI_PROXY_BINARY = 'cli-proxy-api'
cli_proxy_binaries = [(str(SPEC_DIR / 'cli_proxy' / CLI_PROXY_BINARY), 'cli_proxy')]


# QtWebEngine's stray "version" in the BUILD environment (2026-11-09; the build failed with
# "QtWebEngine placeholder: … already exists"). Running Broccoli from source lets Chromium create the
# same empty QtWebEngineCore.framework/Versions/Resources inside the venv's PyQt6 (the reason is at
# the end of this spec). PyInstaller's Qt hook takes the LAST name in Versions/ as the framework's
# version — "Resources" sorts after "A" — and puts QtWebEngine's helper app and its resources (65 MB)
# under Versions/Resources instead of Versions/A, where the framework's links point: the packaged
# app's web pages would not work. An EMPTY extra folder there holds nothing (Chromium makes it again
# whenever it likes) and is removed before the analysis; anything else stops the build.
import PyQt6 as _pyqt6
_webengine_versions = Path(_pyqt6.__file__).parent / 'Qt6' / 'lib' / 'QtWebEngineCore.framework' / 'Versions'
if _webengine_versions.is_dir():
    # (the wheel ships only Versions/A; PyInstaller makes Versions/Current itself)
    for _entry in sorted(_webengine_versions.iterdir()):
        if _entry.name != 'Current' and _entry.is_dir() and not _entry.is_symlink() and not any(_entry.iterdir()):
            _entry.rmdir()
            print('Removed an empty stray QtWebEngine version folder from the build environment:', _entry)
    _versions_left = sorted(e.name for e in _webengine_versions.iterdir() if e.name != 'Current')
    if len(_versions_left) != 1:
        raise RuntimeError(f'{_webengine_versions} holds {_versions_left}, not one version: PyInstaller would '
                           'package QtWebEngine under the last one. Remove the one that is not part of PyQt6 '
                           '(PyQt6 ships "A") and build again.')

# Minimum macOS (2026-11-10): the one Qt's own libraries are built for (Qt 6.12: 14.4; 6.10 was 13),
# read from QtCore at build time, so a Mac that is too old says so instead of the app crashing at start.
import subprocess as _subprocess
_qtcore = Path(_pyqt6.__file__).parent / 'Qt6' / 'lib' / 'QtCore.framework' / 'Versions' / 'A' / 'QtCore'
_minos = re.search(r'^\s*minos\s+([0-9.]+)', _subprocess.run(['otool', '-l', str(_qtcore)], check=True,
                                                               capture_output=True, text=True).stdout, re.M)
if not _minos:
    raise RuntimeError(f'Cannot read the minimum macOS of {_qtcore}')
QT_MINIMUM_MACOS = _minos.group(1)
print('Minimum macOS (from Qt):', QT_MINIMUM_MACOS)

a = Analysis(
    ['Broccoli.py', 'browser_use_worker.py', 'computer_use_worker.py', 'broccoli_python.py'],
    pathex=[str(SPEC_DIR)],
    binaries=(claude_cli_binaries + codex_cli_binaries + open_connector_binaries + codexbar_binaries
              + agentsview_binaries + cli_proxy_binaries),
    datas=resource_datas + codex_cli_datas,
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
python_scripts = runtime_scripts + [script for script in a.scripts if script[0] == 'broccoli_python']

if len(main_scripts) != len(runtime_scripts) + 1:
    raise RuntimeError('Broccoli entry script was not found in PyInstaller analysis output.')
if len(worker_scripts) != len(runtime_scripts) + 1:
    raise RuntimeError('Browser Use worker entry script was not found in PyInstaller analysis output.')
if len(cua_worker_scripts) != len(runtime_scripts) + 1:
    raise RuntimeError('Computer Use worker entry script was not found in PyInstaller analysis output.')
if len(python_scripts) != len(runtime_scripts) + 1:
    raise RuntimeError('BroccoliPython entry script was not found in PyInstaller analysis output.')

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
# The app's own Python for the code runner — the main app resolves it as a sibling executable named
# exactly 'BroccoliPython' (see bundled_python_runner_path()).
python_exe = EXE(
    pyz,
    python_scripts,
    [],
    exclude_binaries=True,
    name='BroccoliPython',
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
    python_exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[OPEN_CONNECTOR_BINARY, CODEXBAR_BINARY, AGENTSVIEW_BINARY, CLI_PROXY_BINARY,
                 'claude', 'codex', 'codex-code-mode-host', 'codex-exec-server', 'rg'],
    name='Broccoli',
)
app = BUNDLE(
    coll,
    name='Broccoli.app',
    icon='Broccolidsk.icns',
    # the in-app updater accepts only a bundle with exactly this identifier (BROCCOLI_UPDATE_BUNDLE_ID =
    # BROCCOLI_BUNDLE_ID in Broccoli.py). Reverse-DNS like Raspberry's since 2026-11-07 (was 'Broccoli'):
    # an app with the old id updates to the first build with this one by hand, once; macOS asks again
    # for its permissions (Accessibility, Screen Recording, Automation …), which belong to the bundle id.
    bundle_identifier='com.ryanthehito.broccoli',
    version=__version__,
    info_plist={
        'CFBundleShortVersionString': __version__,
        'CFBundleVersion': __version__,
        # as the installed app has it (the console workers made PyInstaller set it): Broccoli shows
        # or hides its own Dock icon at run time
        'LSBackgroundOnly': True,
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': QT_MINIMUM_MACOS,
        # Apple Notes and other apps are driven through osascript (macOS asks the user once)
        'NSAppleEventsUsageDescription': 'Broccoli reads and writes your Apple Notes and Reminders and controls other apps when you ask it to.',
    },
)

# QtWebEngine placeholder version (2026-11-07). Without it the installed app's signature breaks the
# first time a page in Broccoli's web view asks for the camera / microphone list (claude.ai does,
# a few seconds after loading): Chromium then starts its video-capture helper, the only web helper
# that runs WITHOUT a sandbox on macOS, and while starting it creates an empty
# QtWebEngineCore.framework/Versions/Resources (Chromium's guess of the locales folder, made before
# Qt tells it the real one; sandboxed helpers try too but may not write). Everything in Versions/
# counts as a framework version and an empty folder is never a valid one, so the app then fails
# `codesign --verify` with "embedded framework contains modified or invalid version".
# Fix: ship that folder as a tiny but complete version: a do-nothing library + the framework's own
# Info.plist. Chromium finds it already there and writes nothing; signed with the same Developer ID
# it is a valid version. Nothing ever loads it. Sign it first (notes at the top of this spec).
# Pre-creating an EMPTY folder or a symlink does not work (tested: invalid version / unsealed).
QTWEBENGINE_PLACEHOLDER_SOURCE = 'void broccoli_qtwebengine_placeholder_version(void) {}\n'


def add_qtwebengine_placeholder_version(bundle_path):
    import shutil
    import subprocess
    import tempfile

    framework = os.path.join(bundle_path, 'Contents', 'Frameworks', 'PyQt6', 'Qt6', 'lib',
                             'QtWebEngineCore.framework')
    real_binary = os.path.join(framework, 'Versions', 'A', 'QtWebEngineCore')
    real_info = os.path.join(framework, 'Versions', 'A', 'Resources', 'Info.plist')
    placeholder = os.path.join(framework, 'Versions', 'Resources')
    for needed in (real_binary, real_info):
        if not os.path.isfile(needed):
            raise RuntimeError(f'QtWebEngine placeholder: {needed} is missing')
    # QtWebEngine itself must sit in Versions/A (where the framework's links point), not elsewhere
    for needed in (os.path.join(framework, 'Versions', 'A', 'Helpers', 'QtWebEngineProcess.app'),
                   os.path.join(framework, 'Versions', 'A', 'Resources', 'qtwebengine_resources.pak')):
        if not os.path.exists(needed):
            raise RuntimeError(
                f'QtWebEngine was packaged in the wrong place: {needed} is missing'
                + (f' (it went to {placeholder}: an extra folder in the build environment\'s '
                   'QtWebEngineCore.framework/Versions — see the check before Analysis)'
                   if os.path.isdir(placeholder) else '') + '. Build again.')
    if os.path.lexists(placeholder):
        raise RuntimeError(f'QtWebEngine placeholder: {placeholder} already exists')

    # the same architectures and minimum macOS as the real library
    archs = subprocess.run(['lipo', '-archs', real_binary], check=True, capture_output=True,
                           text=True).stdout.split()
    minos = re.search(r'^\s*minos\s+([0-9.]+)',
                      subprocess.run(['otool', '-l', real_binary], check=True, capture_output=True,
                                     text=True).stdout, re.M)
    if not archs or not minos:
        raise RuntimeError('QtWebEngine placeholder: cannot read the architecture / minimum macOS of '
                           + real_binary)

    os.makedirs(os.path.join(placeholder, 'Resources'))
    with tempfile.TemporaryDirectory() as tmp:
        source = os.path.join(tmp, 'placeholder.c')
        with open(source, 'w', encoding='utf-8') as fh:
            fh.write(QTWEBENGINE_PLACEHOLDER_SOURCE)
        command = ['xcrun', 'clang', '-dynamiclib']
        for arch in archs:
            command += ['-arch', arch]
        command += [f'-mmacosx-version-min={minos.group(1)}',
                    '-install_name', '@rpath/QtWebEngineCore.framework/Versions/Resources/QtWebEngineCore',
                    '-o', os.path.join(placeholder, 'QtWebEngineCore'), source]
        result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        shutil.rmtree(placeholder, ignore_errors=True)
        raise RuntimeError('QtWebEngine placeholder: clang failed (it needs the Xcode Command Line '
                           'Tools: xcode-select --install)\n' + result.stderr)
    shutil.copy2(real_info, os.path.join(placeholder, 'Resources', 'Info.plist'))
    print('QtWebEngine placeholder version added:', placeholder)
    print('  sign it with your Developer ID BEFORE signing the app (notes at the top of Broccoli.spec)')


add_qtwebengine_placeholder_version(app.name)
