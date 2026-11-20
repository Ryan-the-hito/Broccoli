"""Voice input (dictation) for Broccoli — 2026-11-16.

Plan: editor_handoff/PLAN_20261116_语音输入与本地模型.md

One listening = one VoiceInputSession: it starts the dictation helper (voice_input/BroccoliVoice,
Apple's on-device recognizer), which opens the microphone and reports text as it hears it:
"partial" text may still change, "final" text will not. DictationIntoEdit puts both into a
QPlainTextEdit at the caret; the text that may still change is drawn grey (an extra selection:
the document itself only ever holds plain text). VoiceInputController is what a microphone
button talks to: toggle() starts a listening or stops it.

Nothing here blocks the UI thread: the helper is a QProcess read through signals, and
voice_helper_check() is meant for a worker thread. Errors are codes ('microphone_denied', …);
the window that shows them translates them.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import threading

from PyQt6.QtCore import QObject, QProcess, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import QTextEdit

VOICE_HELPER_NAME = 'BroccoliVoice'
VOICE_HELPER_STOP_GRACE_MS = 4000     # after "stop": time for the last words to be finalized
VOICE_PARTIAL_GREY_LIGHT = '#8E8E93'
VOICE_PARTIAL_GREY_DARK = '#98989D'

# Settings → Languages key (language_alias_key) → the locale to listen in
VOICE_LOCALE_BY_LANGUAGE_KEY = {
    'english': 'en-US', 'chinese': 'zh-CN', 'japanese': 'ja-JP', 'korean': 'ko-KR', 'french': 'fr-FR',
    'german': 'de-DE', 'spanish': 'es-ES', 'italian': 'it-IT', 'portuguese': 'pt-BR', 'russian': 'ru-RU',
}

# every code the helper or this module can report (the UI keeps one translated sentence each)
VOICE_ERROR_CODES = (
    'helper_missing',            # the helper program is not there (macOS older than 26, or a broken install)
    'helper_crashed',
    'speech_unavailable',        # this Mac has no on-device recognizer
    'language_unsupported',
    'language_download_failed',
    'microphone_denied', 'microphone_restricted', 'microphone_not_asked',
    'input_device_missing', 'input_device_unusable', 'audio_format_unavailable',
    'recognition_failed',
    'recording_not_saved',       # a recording that was to be kept could not be written to disk
    'system_audio_denied',       # the user did not allow recording what the Mac plays
    'system_audio_unavailable',  # the Mac's own sound could not be opened
)

# where a listening takes its sound from: the microphone, or what this Mac is playing (2026-11-19:
# the other side of an online meeting comes out of the Mac, not into the microphone)
VOICE_SOURCE_MICROPHONE = ''
VOICE_SOURCE_SYSTEM = 'system'


def voice_output_kind(helper_path: str, timeout: float = 5.0) -> str:
    """Where this Mac's sound comes out right now: 'speaker', 'headphones' or 'unknown' (also when
    the helper cannot say). A fraction of a second, but still: call it from a worker thread."""
    if not helper_path or not os.path.isfile(helper_path):
        return 'unknown'
    try:
        done = subprocess.run([helper_path, '--output'], capture_output=True, timeout=timeout,
                              stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return 'unknown'
    for line in done.stdout.decode('utf-8', 'replace').splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict) and item.get('type') == 'output':
            kind = str(item.get('kind', '') or '')
            return kind if kind in ('speaker', 'headphones') else 'unknown'
    return 'unknown'


def voice_helper_check(helper_path: str, timeout: float = 15.0) -> dict:
    """What this Mac can do, from the helper's --check: {'available', 'supported_locales',
    'installed_locales', 'microphone', 'devices': [{'id', 'name'}], 'default_device'}; {} when
    the helper cannot run. Takes up to a second or two: call it from a worker thread."""
    if not helper_path or not os.path.isfile(helper_path):
        return {}
    try:
        done = subprocess.run([helper_path, '--check'], capture_output=True, timeout=timeout,
                              stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return {}
    for line in done.stdout.decode('utf-8', 'replace').splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict) and item.get('type') == 'check':
            return item
    return {}


_CJK = '\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff'
_CJK_PUNCT = '，。！？、；：）」』】》'
_SPACE_BEFORE_CJK_PUNCT = re.compile('[ \u3000]+(?=[' + _CJK_PUNCT + '])')
_SPACE_BETWEEN_CJK = re.compile('(?<=[' + _CJK + _CJK_PUNCT + '])[ \u3000]+(?=[' + _CJK + '])')


def tidy_dictated_text(text: str) -> str:
    """The recognizer's text without the stray spaces it leaves inside Chinese / Japanese
    ("页面 ，然后" → "页面，然后"). Spaces around Latin words and digits stay."""
    text = str(text or '')
    text = _SPACE_BEFORE_CJK_PUNCT.sub('', text)
    return _SPACE_BETWEEN_CJK.sub('', text)


def best_voice_locale(wanted: str, supported) -> str:
    """The supported locale closest to `wanted` ('zh', 'zh-Hans', 'zh_CN', 'ja', 'en-GB'…);
    '' when the language is not supported at all."""
    supported = [str(item) for item in (supported or [])]
    wanted = str(wanted or '').replace('_', '-').strip()
    if not wanted:
        return ''
    lowered = {item.lower(): item for item in supported}
    if wanted.lower() in lowered:
        return lowered[wanted.lower()]
    parts = wanted.split('-')
    language = parts[0].lower()
    script_region = {'hans': 'CN', 'hant': 'TW'}
    region = ''
    for part in parts[1:]:
        if part.lower() in script_region:
            region = script_region[part.lower()]
        elif len(part) == 2:
            region = part.upper()
    if region and f'{language}-{region}'.lower() in lowered:
        return lowered[f'{language}-{region}'.lower()]
    preferred = {'zh': 'zh-CN', 'en': 'en-US', 'ja': 'ja-JP', 'ko': 'ko-KR', 'yue': 'yue-CN',
                 'pt': 'pt-BR', 'es': 'es-ES', 'fr': 'fr-FR', 'de': 'de-DE'}.get(language, '')
    if preferred.lower() in lowered:
        return lowered[preferred.lower()]
    for item in supported:
        if item.lower().split('-')[0] == language:
            return item
    return ''


class VoiceInputSession(QObject):
    """One listening, from start() to `finished`."""
    ready = pyqtSignal()                 # the microphone is open
    partial = pyqtSignal(str)            # text that may still change
    final = pyqtSignal(str)              # text that will not change any more
    level = pyqtSignal(float)            # loudness 0–1, about 15 a second
    tone = pyqtSignal(float)             # how high the voice is, 0–1, with each loudness
    asset = pyqtSignal(str, float)       # ('downloading', 0–1) / ('ready', 1.0): the language's model
    failed = pyqtSignal(str, str)        # (code from VOICE_ERROR_CODES, detail for the log)
    finished = pyqtSignal()              # always the last signal, exactly once

    def __init__(self, helper_path: str, locale: str, device: str = '', audio_file: str = '', save_path: str = '',
                 parent=None, source: str = VOICE_SOURCE_MICROPHONE):
        super().__init__(parent)
        self._source = str(source or '')           # VOICE_SOURCE_SYSTEM: what the Mac plays, not the microphone
        self._helper_path = str(helper_path or '')
        self._locale = str(locale or '')
        self._device = str(device or '')
        self._audio_file = str(audio_file or '')   # tests: recognize a file instead of the microphone
        self._save_path = str(save_path or '')     # the sound is also kept in this file (a .caf)
        self.saved_path = ''                       # … where it really is, once it is being written
        self._process = None
        self._buffer = b''
        self._stopping = False
        self._done = False
        self._failed = False
        self._kill_timer = QTimer(self)
        self._kill_timer.setSingleShot(True)
        self._kill_timer.timeout.connect(self._kill)

    def is_running(self) -> bool:
        return self._process is not None and not self._done

    def is_stopping(self) -> bool:
        return self._stopping and not self._done

    def start(self):
        if self._process is not None:
            return
        if not self._helper_path or not os.path.isfile(self._helper_path):
            self._fail('helper_missing', self._helper_path)
            self._finish()
            return
        args = ['--locale', self._locale]
        if self._source == VOICE_SOURCE_SYSTEM:
            args += ['--system']
        elif self._device:
            args += ['--device', self._device]
        if self._audio_file:
            args += ['--file', self._audio_file]
            if self._save_path:        # (tests: the "recording" is the file that was listened to)
                try:
                    done = subprocess.run(['/usr/bin/afconvert', '-f', 'caff', '-d', 'LEI16@16000', '-c', '1',
                                           self._audio_file, self._save_path], capture_output=True)
                    if done.returncode == 0:
                        self.saved_path = self._save_path
                except OSError:
                    pass
        elif self._save_path:
            args += ['--save', self._save_path]
        process = self._process = QProcess(self)
        process.setProgram(self._helper_path)
        process.setArguments(args)
        process.readyReadStandardOutput.connect(self._read)
        process.finished.connect(self._on_process_finished)
        process.errorOccurred.connect(self._on_process_error)
        process.start()

    def stop(self):
        """Stop listening; the last words still arrive as `final` before `finished`."""
        if self._process is None or self._done or self._stopping:
            return
        self._stopping = True
        if self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.write(b'stop\n')
            self._process.closeWriteChannel()
        self._kill_timer.start(VOICE_HELPER_STOP_GRACE_MS)

    def cancel(self):
        """Stop at once; whatever was not final yet is dropped."""
        if self._process is None or self._done:
            return
        self._stopping = True
        self._kill()

    def _kill(self):
        if self._process is not None and self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.kill()

    def _fail(self, code: str, detail: str = ''):
        if self._failed:
            return
        self._failed = True
        self.failed.emit(code if code in VOICE_ERROR_CODES else 'recognition_failed', str(detail or ''))

    def _finish(self):
        if self._done:
            return
        self._done = True
        self._kill_timer.stop()
        self.finished.emit()

    def _read(self):
        if self._process is None:
            return
        self._buffer += bytes(self._process.readAllStandardOutput())
        while b'\n' in self._buffer:
            line, self._buffer = self._buffer.split(b'\n', 1)
            try:
                item = json.loads(line.decode('utf-8', 'replace'))
            except ValueError:
                continue
            if isinstance(item, dict):
                self._handle(item)

    def _handle(self, item: dict):
        kind = item.get('type')
        if kind == 'partial':
            self.partial.emit(tidy_dictated_text(item.get('text', '')))
        elif kind == 'final':
            self.final.emit(tidy_dictated_text(item.get('text', '')))
        elif kind == 'level':
            try:
                self.level.emit(max(0.0, min(1.0, float(item.get('value', 0) or 0))))
                if 'tone' in item:
                    self.tone.emit(max(0.0, min(1.0, float(item.get('tone', 0) or 0))))
            except (TypeError, ValueError):
                pass
        elif kind == 'ready':
            self.ready.emit()
        elif kind == 'saving':
            self.saved_path = str(item.get('path', '') or '')
        elif kind == 'asset':
            state = str(item.get('state', '') or '')
            try:
                progress = float(item.get('progress', 1.0 if state == 'ready' else 0.0) or 0.0)
            except (TypeError, ValueError):
                progress = 0.0
            self.asset.emit(state, max(0.0, min(1.0, progress)))
        elif kind == 'error':
            self._fail(str(item.get('code', '') or ''), str(item.get('detail', '') or ''))

    def _on_process_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self._fail('helper_missing', self._helper_path)
            self._finish()

    def _on_process_finished(self, exit_code, exit_status):
        self._read()
        crashed = exit_status == QProcess.ExitStatus.CrashExit or exit_code != 0
        if crashed and not self._stopping:
            self._fail('helper_crashed', f'exit {exit_code}')
        self._finish()


def _u16(text: str) -> bytes:
    return str(text or '').encode('utf-16-le', 'surrogatepass')


def _edit_between(old: str, new: str):
    """Where `new` differs from `old`, in the positions Qt uses (UTF-16 units):
    (start, old_end, new_end) — old[start:old_end] became new[start:new_end]."""
    a, b = _u16(old), _u16(new)
    limit = min(len(a), len(b))
    start = 0
    while start + 2 <= limit and a[start:start + 2] == b[start:start + 2]:
        start += 2
    tail = 0
    while tail + 2 <= limit - start and a[len(a) - tail - 2:len(a) - tail] == b[len(b) - tail - 2:len(b) - tail]:
        tail += 2
    return start // 2, (len(a) - tail) // 2, (len(b) - tail) // 2


def voice_partial_selections(edit, dark: bool = False) -> list:
    """The grey "may still change" stretch of a text box, as extra selections ([] when it has
    none). Whoever sets extra selections on a box that can be dictated into adds these."""
    span = getattr(edit, '_voice_partial_range', None)
    if not span or span[1] <= span[0]:
        return []
    document = edit.document()
    last = max(0, document.characterCount() - 1)
    cursor = QTextCursor(document)
    cursor.setPosition(max(0, min(span[0], last)))
    cursor.setPosition(max(0, min(span[1], last)), QTextCursor.MoveMode.KeepAnchor)
    fmt = QTextCharFormat()
    fmt.setForeground(QColor(VOICE_PARTIAL_GREY_DARK if dark else VOICE_PARTIAL_GREY_LIGHT))
    selection = QTextEdit.ExtraSelection()
    selection.cursor = cursor
    selection.format = fmt
    return [selection]


class LocalVoiceSession(QObject):
    """One listening with a speech model Broccoli runs itself (local_speech.py) — the same
    signals as VoiceInputSession, so everything that uses a session works with either. The helper
    only listens (--capture: the sound itself comes down its stdout); the cutting into sentences
    and the recognizing happen in local_speech.LocalDictation, on its own threads."""
    ready = pyqtSignal()
    partial = pyqtSignal(str)
    final = pyqtSignal(str)
    level = pyqtSignal(float)
    tone = pyqtSignal(float)
    asset = pyqtSignal(str, float)       # (never sent: the model is on disk already)
    failed = pyqtSignal(str, str)
    finished = pyqtSignal()

    def __init__(self, helper_path: str, engine, model_id: str, language: str = '', device: str = '',
                 audio_file: str = '', partial_seconds=1.0, save_path: str = '', parent=None,
                 source: str = VOICE_SOURCE_MICROPHONE):
        super().__init__(parent)
        self._source = str(source or '')           # VOICE_SOURCE_SYSTEM: what the Mac plays, not the microphone
        self._save_path = str(save_path or '')     # the sound is also kept in this file (a .wav)
        self.saved_path = ''
        self._helper_path = str(helper_path or '')
        self._engine = engine
        self._model_id = str(model_id or '')
        self._language = str(language or '')
        self._device = str(device or '')
        self._audio_file = str(audio_file or '')
        self._partial_seconds = partial_seconds
        self.paced = False              # tests: the sound file is sent at the speed it was spoken
        self._process = None
        self._dictation = None
        self._failed = False
        self._done = False
        self._stopping = False
        self._lock = threading.Lock()

    def is_running(self) -> bool:
        return self._process is not None and not self._done

    def _fail(self, code: str, detail: str = ''):
        with self._lock:
            if self._failed:
                return
            self._failed = True
        self.failed.emit(code if code in VOICE_ERROR_CODES else 'recognition_failed', str(detail or ''))

    def _finish(self):
        with self._lock:
            if self._done:
                return
            self._done = True
        self.finished.emit()

    def start(self):
        if self._process is not None:
            return
        if not self._helper_path or not os.path.isfile(self._helper_path):
            self._fail('helper_missing', self._helper_path)
            self._finish()
            return
        import local_speech
        args = [self._helper_path, '--capture']
        if self._source == VOICE_SOURCE_SYSTEM:
            args += ['--system']
        elif self._device:
            args += ['--device', self._device]
        if self._audio_file:
            args += ['--file', self._audio_file] + (['--pace'] if self.paced else [])
        try:
            process = self._process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                                       stderr=subprocess.PIPE)
        except OSError as error:
            self._fail('helper_missing', str(error))
            self._finish()
            return

        def notes():                        # the helper's JSON lines (stderr): ready, errors
            for line in process.stderr:
                try:
                    item = json.loads(line.decode('utf-8', 'replace'))
                except ValueError:
                    continue
                if item.get('type') == 'ready':
                    self.ready.emit()
                elif item.get('type') == 'error':
                    self._fail(str(item.get('code', '') or ''), str(item.get('detail', '') or ''))
        threading.Thread(target=notes, name='voice-capture-notes', daemon=True).start()

        def preload():                      # the model loads while the first words are spoken
            try:
                self._engine.recognizer(self._model_id, self._language)
            except Exception:
                pass
        threading.Thread(target=preload, name='voice-model-preload', daemon=True).start()

        keep = None
        if self._save_path:
            try:
                import wave
                keep = wave.open(self._save_path, 'wb')
                keep.setnchannels(1)
                keep.setsampwidth(2)
                keep.setframerate(16000)
                self.saved_path = self._save_path
            except OSError as error:
                keep = None
                self._fail('recording_not_saved', str(error))

        def sound():
            try:
                while True:
                    block = process.stdout.read(1600)       # 0.05 s of sound
                    if not block:
                        break
                    if keep is not None:
                        try:
                            keep.writeframesraw(block)
                        except OSError:
                            pass
                    yield block
            finally:
                if keep is not None:
                    try:
                        keep.close()                        # (writes the length into the file's header)
                    except OSError:
                        pass
                if process.poll() is None:
                    process.kill()
                process.wait()

        def done():
            if process.returncode not in (0, None) and not self._stopping:
                self._fail('helper_crashed', f'exit {process.returncode}')
            self._finish()
        self._dictation = local_speech.LocalDictation(
            self._engine, self._model_id, self._language, sound,
            on_partial=lambda text: self.partial.emit(tidy_dictated_text(text)),
            on_final=lambda text: self.final.emit(tidy_dictated_text(text)),
            on_level=self.level.emit, on_tone=self.tone.emit, on_done=done,
            on_error=lambda code, detail: self._fail(code, detail),
            partial_seconds=self._partial_seconds)
        self._dictation.start()

    def stop(self):
        """Stop listening; the sentence being spoken is still finished and reported."""
        if self._process is None or self._done or self._stopping:
            return
        self._stopping = True
        try:
            self._process.stdin.write(b'stop\n')
            self._process.stdin.close()         # the helper stops, its sound ends, the last words follow
        except (OSError, ValueError):
            pass

    def cancel(self):
        if self._process is None or self._done:
            return
        self._stopping = True
        if self._dictation is not None:
            self._dictation.cancel()
        try:
            self._process.kill()
        except OSError:
            pass


class DictationIntoEdit(QObject):
    """Writes what a VoiceInputSession hears into a text box, at the caret it had when the
    listening began: final text stays, the still-changing text after it is replaced each time
    it changes and is drawn grey.

    `editor_for` is the box, or a function returning the box in use right now (Broccoli's
    prompt is two mirrored boxes: the one in the bar and the popup above it). Places are kept
    as numbers and re-found against the box's text before every write, so typing elsewhere in
    the box, or the two boxes copying each other's text, does not misplace the words. A box
    that was emptied meanwhile (the prompt was sent) ends the listening."""

    def __init__(self, editor_for, session: VoiceInputSession, dark_for=None, refresh_highlight=None, parent=None):
        super().__init__(parent)
        self._editor_for = editor_for if callable(editor_for) else (lambda: editor_for)
        self._session = session
        self._dark_for = dark_for or (lambda: False)
        self._refresh_highlight = refresh_highlight
        edit = self._editor_for()
        self._start = self._end = edit.textCursor().selectionEnd()
        self._origin = self._start      # where this dictation's first word went
        self._marking_all = False       # the whole dictation is drawn grey (it is being tidied)
        self._last_doc = edit.toPlainText()
        self._edits = [edit]
        self._wrote_any = False
        self._first_write = True
        self._over = False
        self._touched = False           # the user edited inside the dictated text
        session.partial.connect(lambda text: self._write(text, final=False))
        session.final.connect(lambda text: self._write(text, final=True))
        session.finished.connect(self._on_finished)

    def wrote_any(self) -> bool:
        return self._wrote_any

    def box_was_emptied(self) -> bool:
        """The box held dictated text and is empty now (sent or cleared)."""
        return bool(self._last_doc) and self._wrote_any and not self._editor_for().toPlainText()

    def _mark(self, edit):
        if edit not in self._edits:
            self._edits.append(edit)
        first = self._origin if self._marking_all else self._start
        span = (first, self._end) if self._end > first else None
        for item in self._edits:
            try:
                item._voice_partial_range = span
            except RuntimeError:      # the box is gone
                continue
        if self._refresh_highlight is not None:
            self._refresh_highlight()
        else:
            for item in self._edits:
                try:
                    item.setExtraSelections(voice_partial_selections(item, bool(self._dark_for())))
                except RuntimeError:
                    continue

    def _reconcile(self, current: str) -> bool:
        """Move the remembered place to where it is in `current`; False = stop writing."""
        if current == self._last_doc:
            return True
        if not current and self._last_doc and self._wrote_any:
            return False                                   # emptied: the prompt was sent
        at, old_end, new_end = _edit_between(self._last_doc, current)
        delta = new_end - old_end
        if old_end <= self._origin:                        # changed before this dictation
            self._origin += delta
            self._start += delta
            self._end += delta
        elif old_end <= self._start:                       # changed inside what was already final
            self._start += delta
            self._end += delta
            self._touched = True
        elif at >= self._end:                              # changed after it
            pass
        else:                                              # the grey text itself was edited: keep
            self._start = self._end = max(at, new_end)     # it as typed, go on after it
            self._touched = True
        return True

    def _joined(self, current: str, text: str) -> str:
        """`text`, with one space before it when it would otherwise run into a Latin word."""
        if not text:
            return text
        before = _u16(current)[max(0, self._start - 1) * 2:self._start * 2].decode('utf-16-le', 'replace')
        if not before or before == '\n':
            return text.lstrip()
        if before.isascii() and before.isalnum() and text[0].isascii() and text[0].isalnum():
            return ' ' + text
        return text

    def _write(self, text: str, final: bool):
        if self._over:
            return
        edit = self._editor_for()
        current = edit.toPlainText()
        if not self._reconcile(current):
            self._over = True
            self._session.cancel()
            return
        cursor = QTextCursor(edit.document())
        last = max(0, edit.document().characterCount() - 1)
        cursor.setPosition(max(0, min(self._start, last)))
        cursor.setPosition(max(0, min(self._end, last)), QTextCursor.MoveMode.KeepAnchor)
        self._start = cursor.selectionStart()
        if self._first_write:
            cursor.beginEditBlock()            # one undo takes the whole dictation back
            self._first_write = False
        else:
            cursor.joinPreviousEditBlock()
        cursor.insertText(self._joined(current, text))
        cursor.endEditBlock()
        self._end = cursor.position()
        if final:
            self._start = self._end
        self._wrote_any = self._wrote_any or bool(text)
        caret = QTextCursor(edit.document())
        caret.setPosition(self._end)
        edit.setTextCursor(caret)
        edit.ensureCursorVisible()
        self._last_doc = edit.toPlainText()    # after the box's own listeners ran (mirroring)
        self._mark(edit)

    def _on_finished(self):
        # whatever is still grey was heard but never made final: the words stay as they are
        self._over = True
        self._start = self._end
        self._mark(self._editor_for())

    # ── the whole dictation, once the listening is over (for the tidy-up pass) ──
    def dictated_text(self) -> str:
        """Everything this dictation put into the box ('' when the user edited inside it, the box
        was emptied, or nothing was said)."""
        edit = self._editor_for()
        current = edit.toPlainText()
        if not self._wrote_any or not self._reconcile(current) or self._touched:
            return ''
        self._last_doc = current
        return _u16(current)[self._origin * 2:self._end * 2].decode('utf-16-le', 'replace')

    def mark_all(self, on: bool):
        """Draw the whole dictation grey (it may still change: it is being tidied) / stop."""
        self._marking_all = bool(on)
        self._mark(self._editor_for())

    def replace_dictated(self, raw: str, tidy: str) -> bool:
        """Put `tidy` where the dictation `raw` is — only if it still stands there untouched."""
        if not tidy or tidy == raw or self.dictated_text() != raw or not raw:
            return False
        edit = self._editor_for()
        cursor = QTextCursor(edit.document())
        cursor.setPosition(self._origin)
        cursor.setPosition(self._end, QTextCursor.MoveMode.KeepAnchor)
        caret_at_end = edit.textCursor().position() == self._end
        cursor.beginEditBlock()             # its own undo step: one undo brings the words as heard back
        cursor.insertText(tidy)
        cursor.endEditBlock()
        self._start = self._end = cursor.position()
        if caret_at_end:
            caret = QTextCursor(edit.document())
            caret.setPosition(self._end)
            edit.setTextCursor(caret)
            edit.ensureCursorVisible()
        self._last_doc = edit.toPlainText()
        self._mark(edit)
        return True


class VoiceInputController(QObject):
    """What a microphone button talks to. toggle(): start listening / stop. One listening at a
    time; the words go into the box `editor_for()` returns."""
    state_changed = pyqtSignal(str)     # 'idle' | 'starting' | 'listening' | 'stopping' | 'tidying'
    tidied = pyqtSignal(bool)           # the tidy-up pass ended: True = the text was replaced
    _tidy_done = pyqtSignal(object, str, str)   # worker thread → GUI thread: (token, raw, tidy)
    failed = pyqtSignal(str)            # a code from VOICE_ERROR_CODES
    level = pyqtSignal(float)
    tone = pyqtSignal(float)            # how high the voice is, 0–1 (not every kind of session tells)
    asset = pyqtSignal(str, float)      # the language's model: ('downloading', 0–1) / ('ready', 1.0)

    def __init__(self, helper_path_for, locale_for, editor_for, device_for=None, dark_for=None,
                 refresh_highlight=None, tidy_for=None, session_for=None, parent=None):
        super().__init__(parent)
        # session_for(controller) → a session of its own (a downloaded model: LocalVoiceSession), or
        # None for the Mac's own recognizer (VoiceInputSession)
        self._session_for = session_for
        # tidy_for() → None (no tidy-up pass) or a function text -> tidied text, run on a worker
        # thread once the listening is over; its answer replaces the dictation if that still stands
        self._tidy_for = tidy_for
        self._tidy_token = None
        self._cancelled = False
        self.audio_file = ''            # tests: listen to a file instead of the microphone
        self.save_path = ''             # the next listening is also kept as a sound file here
        self.saved_path = ''            # where the last listening's sound was kept ('' = it was not)
        self._tidy_done.connect(self._on_tidy_done)
        self._helper_path_for = helper_path_for
        self._locale_for = locale_for
        self._editor_for = editor_for
        self._device_for = device_for or (lambda: '')
        self._dark_for = dark_for
        self._refresh_highlight = refresh_highlight
        self._session = None
        self._writer = None
        self._state = 'idle'
        self._watch = QTimer(self)          # the box emptied while listening = it was sent: stop
        self._watch.setInterval(300)
        self._watch.timeout.connect(self._check_box)

    def state(self) -> str:
        return self._state

    def session(self):
        """The listening going on right now (None when there is none)."""
        return self._session

    def _set_state(self, state: str):
        if state != self._state:
            self._state = state
            self.state_changed.emit(state)

    def toggle(self):
        if self._state == 'idle':
            self.start()
        elif self._state in ('starting', 'listening'):
            self.stop()
        elif self._state == 'tidying':
            self.cancel()               # keep the words as they were heard

    def start(self):
        if self._state != 'idle':
            return
        session = None
        if self._session_for is not None:
            try:
                session = self._session_for(self)
            except Exception:
                session = None
        if session is None:
            session = VoiceInputSession(
                str(self._helper_path_for() or ''), str(self._locale_for() or ''), str(self._device_for() or ''),
                audio_file=self.audio_file, save_path=self.save_path, parent=self)
        self._session = session
        self.saved_path = ''
        self._writer = DictationIntoEdit(self._editor_for, session, self._dark_for, self._refresh_highlight, parent=self)
        session.ready.connect(lambda: self._state == 'starting' and self._set_state('listening'))
        session.level.connect(self.level)
        if getattr(session, 'tone', None) is not None:
            session.tone.connect(self.tone)
        session.asset.connect(self.asset)
        session.failed.connect(lambda code, _detail: self.failed.emit(code))
        session.finished.connect(lambda finished=session: self._on_finished(finished))
        self._cancelled = False
        self._set_state('starting')
        self._watch.start()
        session.start()

    def stop(self):
        if self._session is not None and self._state in ('starting', 'listening'):
            self._set_state('stopping')
            self._session.stop()

    def cancel(self):
        if self._session is not None:
            self._cancelled = True
            self._session.cancel()
        elif self._state == 'tidying':
            self._end_tidy(False)

    def _check_box(self):
        if self._writer is not None and self._writer.box_was_emptied():
            self.cancel()

    def _on_finished(self, session):
        if session is not self._session:
            return
        self.saved_path = str(getattr(session, 'saved_path', '') or '')
        self._session = None
        writer = self._writer
        session.deleteLater()
        tidy = None
        raw = ''
        if writer is not None and not session._failed and not self._cancelled:
            # (only after an ordinary end: not when it was cancelled or the box was sent)
            try:
                tidy = self._tidy_for() if self._tidy_for is not None else None
            except Exception:
                tidy = None
            raw = writer.dictated_text() if tidy is not None else ''
        if tidy is None or not raw.strip():
            self._watch.stop()
            self._writer = None
            self._set_state('idle')
            return
        token = self._tidy_token = object()
        writer.mark_all(True)
        self._set_state('tidying')
        done = self._tidy_done

        def work():
            try:
                result = str(tidy(raw) or '')
            except Exception:
                result = ''
            try:
                done.emit(token, raw, result)
            except RuntimeError:
                pass
        threading.Thread(target=work, name='voice-input-tidy', daemon=True).start()

    def _on_tidy_done(self, token, raw: str, tidy: str):
        if token is not self._tidy_token or self._state != 'tidying':
            return                      # cancelled meanwhile: the words stay as heard
        replaced = False
        if self._writer is not None:
            try:
                replaced = self._writer.replace_dictated(raw, tidy)
            except RuntimeError:        # the box is gone
                replaced = False
        self._end_tidy(replaced)

    def _end_tidy(self, replaced: bool):
        self._tidy_token = None
        self._watch.stop()
        writer, self._writer = self._writer, None
        if writer is not None:
            try:
                writer.mark_all(False)
            except RuntimeError:
                pass
            writer.deleteLater()
        self._set_state('idle')
        self.tidied.emit(bool(replaced))
