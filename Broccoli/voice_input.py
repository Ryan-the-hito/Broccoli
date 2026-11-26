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
import logging
import os
import re
import shutil
import subprocess
import tempfile
import threading
import wave

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


# Finished sentences, for whoever wants them besides the box they are typed into (2026-11-21: the live
# transcript another program may ask for — LiveTranscriptFeed in the main file). Each tap is called as
# tap(session, text) on the interface thread for every `final` of every session; it must return at once.
FINAL_TAPS = []


def _tell_final_taps(session, text):
    if not getattr(session, 'taps', True):
        return                  # (a recording heard again after a switch: its sentences were told already)
    for tap in list(FINAL_TAPS):
        try:
            tap(session, text)
        except Exception:
            logging.exception('A voice transcript tap failed.')


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
        self.final.connect(lambda text, session=self: _tell_final_taps(session, text))
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


def u16_len(text: str) -> int:
    """The length of `text` in the positions Qt uses (UTF-16 units)."""
    return len(_u16(text)) // 2


def u16_slice(text: str, start: int, end: int) -> str:
    """text[start:end] counted in the positions Qt uses (UTF-16 units)."""
    return _u16(text)[max(0, start) * 2:max(0, end) * 2].decode('utf-16-le', 'surrogatepass')


def suffix_first_edit(old: str, new: str):
    """Where `new` differs from `old`, matched from the END first: (at, removed, inserted text), in
    UTF-16 units. Dictated words grow at the end and the words still being spoken (grey) are the end
    of the text, so a change is put as far from them as it can be: "x|abc" → "xa|abc" is an "a" put in
    after the x (not one put in the grey "abc", which would be read as editing the words being spoken)."""
    a, b = _u16(old), _u16(new)
    limit = min(len(a), len(b))
    tail = 0
    while tail + 2 <= limit and a[len(a) - tail - 2:len(a) - tail] == b[len(b) - tail - 2:len(b) - tail]:
        tail += 2
    start = 0
    while start + 2 <= limit - tail and a[start:start + 2] == b[start:start + 2]:
        start += 2
    inserted = b[start:len(b) - tail].decode('utf-16-le', 'surrogatepass')
    return start // 2, (len(a) - tail - start) // 2, inserted


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
    rewritten = pyqtSignal(str)          # (keep_heard) after a switch: every finished sentence, heard anew
    redoing = pyqtSignal(bool)           # (keep_heard) True while what was said is being heard again

    def __init__(self, helper_path: str, engine, model_id: str, language: str = '', device: str = '',
                 audio_file: str = '', partial_seconds=1.0, save_path: str = '', parent=None,
                 source: str = VOICE_SOURCE_MICROPHONE, keep_heard: bool = False):
        super().__init__(parent)
        self.taps = True
        self._keep_heard = bool(keep_heard)
        self.final.connect(lambda text, session=self: _tell_final_taps(session, text))
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

    def switch(self, model_id: str = '', language=None) -> bool:
        """Another downloaded model and / or language (the choosers on the circle's card). Used at once;
        with keep_heard, what was said so far is heard again and comes as `rewritten` (2026-11-22).
        '' / None = leave as it is. True = something changed."""
        changed = False
        if model_id and str(model_id) != self._model_id:
            self._model_id = str(model_id)
            changed = True
        if language is not None and str(language) != self._language:
            self._language = str(language)
            changed = True
        if changed and self._dictation is not None:
            if self._dictation.switch(self._model_id, self._language) and self._keep_heard:
                self.redoing.emit(True)
        return changed

    def _rewrite(self, text: str):
        self.rewritten.emit(tidy_dictated_text(text))
        self.redoing.emit(False)

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
            partial_seconds=self._partial_seconds, keep_heard=self._keep_heard, on_rewrite=self._rewrite)
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


def join_heard(first: str, second: str) -> str:
    """Two stretches of dictated text as one: a space between them only where Latin writing meets."""
    first, second = str(first or ''), str(second or '')
    if not first.strip():
        return second.lstrip()
    if not second.strip():
        return first
    if second[:1].isspace():
        return first + second
    if first[-1].isascii() and not first[-1].isspace() and second[:1].isascii() and second[:1].isalnum():
        return first + ' ' + second
    return first + second


def sound_files_as_one_wav(paths, out_path: str) -> bool:
    """The kept sound of one or more listenings (.caf from Apple Speech, .wav from a downloaded model),
    in order, as one 16 kHz mono 16-bit .wav. Worker thread. False = nothing usable."""
    wrote = False
    folder = os.path.dirname(out_path)
    with wave.open(out_path, 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(16000)
        for index, path in enumerate(paths):
            if not path or not os.path.isfile(path) or os.path.getsize(path) <= 64:
                continue
            plain = os.path.join(folder, f'.part-{index}.wav')
            try:
                done = subprocess.run(['/usr/bin/afconvert', '-f', 'WAVE', '-d', 'LEI16@16000', '-c', '1', path, plain],
                                      capture_output=True, timeout=120)
                if done.returncode != 0 or not os.path.isfile(plain):
                    logging.warning('A kept recording could not be read again: %s', done.stderr[-300:])
                    continue
                with wave.open(plain, 'rb') as part:
                    out.writeframes(part.readframes(part.getnframes()))
                    wrote = True
            except (OSError, wave.Error, subprocess.SubprocessError) as error:
                logging.warning('A kept recording could not be read again: %s', error)
            finally:
                try:
                    os.remove(plain)
                except OSError:
                    pass
    return wrote


class SwitchingVoiceSession(QObject):
    """A listening whose speech model or language may be changed while it goes on — the choosers on the
    circle's card (2026-11-22, Ryan: "只要这个下拉栏变过，我们当前正在输入的这个东西它立马就要变……我现在已经说了这么
    多了，难道我还要把这个东西重说一遍吗"). The change is used at once, for everything:
      · from one downloaded model to another (or another language for it): the same listening goes on
        and hears its own finished sentences again (LocalVoiceSession with keep_heard);
      · to or from Apple Speech, or Apple Speech in another language: a new listening opens; as soon as
        its microphone is open the old one is told to stop (so nothing said in between is lost); all the
        sound kept so far — every listening keeps its sound in a file — is heard again with the new
        choice, and that text takes the place of the words written before.
    The same signals as the other sessions, plus:
        rewritten(text)    every finished word of this recording so far, as the new choice heard it
        redoing(bool)      True while what was said is being heard again
        switch_failed(code)  the new choice could not listen (the old one goes on)

    wanted() → (model id, locale): the choice in the settings right now ('' = Apple Speech).
    make(model id, locale, save path) → a session that is not started yet, keeping its sound there."""
    ready = pyqtSignal()
    partial = pyqtSignal(str)
    final = pyqtSignal(str)
    level = pyqtSignal(float)
    tone = pyqtSignal(float)
    asset = pyqtSignal(str, float)
    failed = pyqtSignal(str, str)
    finished = pyqtSignal()
    rewritten = pyqtSignal(str)
    redoing = pyqtSignal(bool)
    switch_failed = pyqtSignal(str)
    _joined = pyqtSignal(int, str)       # worker → GUI thread: (redo number, the one .wav made of the kept sound)
    _heard = pyqtSignal(int, object)     # worker → GUI thread: (redo number, its text; None = it failed)

    def __init__(self, helper_path: str, wanted, make, engine=None, parent=None):
        super().__init__(parent)
        self.taps = False               # (its sentences are the inner sessions': those tell the taps)
        self._source = VOICE_SOURCE_MICROPHONE
        self.saved_path = ''
        self._helper_path = str(helper_path or '')
        self._wanted = wanted
        self._make = make
        self._engine = engine
        self._folder = ''
        self._made = 0
        self._sessions = {}             # session → {'path', 'spec', 'ready', 'over'}
        self._current = None            # the listening whose words are being written
        self._pending = None            # a new listening that is opening its microphone
        self._old = []                  # listenings told to stop after a switch (their words are not used)
        self._target = None             # the (model, locale) everything is to be heard with
        self._prefix = ''               # the words standing for the sound before the current listening
        self._live = ''                 # the current listening's finished sentences
        self._redo_number = 0
        self._redo_spec = None          # what the redo under way hears with (None = none under way)
        self._redo_wanted = False
        self._redo_shown = False
        self._apple_redo = None
        self._started = False
        self._stopping = False
        self._done = False
        self._failed = False
        self._ready_sent = False
        self._joined.connect(self._on_joined)
        self._heard.connect(self._on_heard)

    # ── the session interface ──
    def is_running(self) -> bool:
        return self._started and not self._done

    def start(self):
        if self._started:
            return
        self._started = True
        try:
            self._folder = tempfile.mkdtemp(prefix='broccoli-voice-')
        except OSError:
            self._folder = ''
        self._target = self._spec_now()
        self._current = self._open(self._target)
        if self._current is None:
            self._failed = True
            self.failed.emit('helper_missing', self._helper_path)
            self._finish()

    def stop(self):
        if self._done or self._stopping:
            return
        self._stopping = True
        if self._pending is not None:
            # stopped while the new choice was still opening: it is not needed for what follows, but
            # what was said is still to be heard with it
            pending, self._pending = self._pending, None
            self._forget(pending)
            pending.cancel()
            current = self._current
            if current is not None and self._sessions[current]['spec'] != self._target:
                self._retire_current()
                current.stop()
        if self._current is not None:
            self._current.stop()
        self._maybe_redo()
        self._maybe_finish()

    def cancel(self):
        if self._done:
            return
        self._stopping = True
        self._redo_number += 1          # (a redo under way is not used)
        self._redo_spec = None
        self._redo_wanted = False
        for session in list(self._sessions):
            try:
                session.cancel()
            except RuntimeError:
                pass
        if self._apple_redo is not None:
            self._apple_redo.cancel()
        self._finish()

    def switch(self, model_id: str = '', language=None) -> bool:
        """A chooser changed the settings: the listening follows them now (the arguments are not
        needed: what the settings say is used). True = something changes."""
        if not self._started or self._done or self._stopping:
            return False
        spec = self._spec_now()
        if spec == self._target:
            return False
        self._target = spec
        if self._pending is not None:
            pending, self._pending = self._pending, None
            self._forget(pending)
            pending.cancel()
        current = self._current
        info = self._sessions.get(current) if current is not None else None
        if info is not None and info['spec'] == spec:
            # back to what is listening already (a switch that had not opened yet was taken back)
            self._redo_wanted = bool(self._old or self._prefix or self._redo_spec is not None)
            self._maybe_redo()
            return True
        if info is not None and info['spec'][0] and spec[0] and hasattr(current, 'switch'):
            # one downloaded model to another: the same listening goes on and hears itself again
            current.switch(spec[0], self._language_of(spec[1]))
            info['spec'] = spec
            if self._old or self._prefix:
                self._redo_wanted = True        # the sound before it is heard again too
            self._maybe_redo()
            return True
        if info is not None and not info['ready']:
            # its microphone is not open yet: nothing was heard by it — the new one takes its place
            self._forget(current)
            current.cancel()
            self._current = self._open(spec)
            if self._old or self._prefix:
                self._redo_wanted = True
            return True
        self._pending = self._open(spec)
        if self._pending is None:
            self.switch_failed.emit('helper_missing')
        return True

    # ── the listenings ──
    def _spec_now(self):
        try:
            model_id, locale = self._wanted()
        except Exception:
            logging.exception('Reading the voice input choice failed.')
            model_id, locale = '', ''
        return str(model_id or ''), str(locale or '')

    @staticmethod
    def _language_of(locale: str) -> str:
        return str(locale or '').split('-')[0].lower()

    def _open(self, spec):
        self._made += 1
        ending = '.wav' if spec[0] else '.caf'
        path = os.path.join(self._folder, f'{self._made}{ending}') if self._folder else ''
        try:
            session = self._make(spec[0], spec[1], path)
        except Exception:
            logging.exception('Opening a listening failed.')
            return None
        if session is None:
            return None
        self._sessions[session] = {'path': path, 'spec': spec, 'ready': False, 'over': False, 'order': self._made}
        session.ready.connect(lambda s=session: self._on_ready(s))
        session.partial.connect(lambda text, s=session: s is self._current and self.partial.emit(text))
        session.final.connect(lambda text, s=session: self._on_final(s, text))
        session.level.connect(lambda value, s=session: s is self._current and self.level.emit(value))
        if getattr(session, 'tone', None) is not None:
            session.tone.connect(lambda value, s=session: s is self._current and self.tone.emit(value))
        session.asset.connect(lambda state, value, s=session: s in (self._current, self._pending)
                              and self.asset.emit(state, value))
        session.failed.connect(lambda code, detail, s=session: self._on_failed(s, code, detail))
        session.finished.connect(lambda s=session: self._on_inner_finished(s))
        if getattr(session, 'rewritten', None) is not None:
            session.rewritten.connect(lambda text, s=session: self._on_inner_rewritten(s, text))
        if getattr(session, 'redoing', None) is not None:
            session.redoing.connect(lambda on, s=session: s is self._current and self.redoing.emit(on))
        session.start()
        return session

    def _forget(self, session):
        info = self._sessions.pop(session, None)
        if info and info['path']:
            try:
                os.remove(info['path'])
            except OSError:
                pass

    def _retire_current(self):
        """The current listening's words are no longer used: its sound is to be heard again."""
        current, self._current = self._current, None
        self._prefix = join_heard(self._prefix, self._live)
        self._live = ''
        if current is not None and not self._sessions[current]['over']:
            self._old.append(current)
        self._redo_wanted = True

    def _on_ready(self, session):
        info = self._sessions.get(session)
        if info is None:
            return
        info['ready'] = True
        if session is self._pending:
            # the new choice listens: the old listening stops (its sound up to now is kept), and
            # everything it heard is heard again with the new choice
            old = self._current
            self._retire_current()
            self._current, self._pending = session, None
            if old is not None and not self._sessions[old]['over']:
                old.stop()
            self._maybe_redo()
        elif session is self._current and not self._ready_sent:
            self._ready_sent = True
            self.ready.emit()

    def _on_final(self, session, text: str):
        if session is not self._current:
            return
        self._live = join_heard(self._live, text)
        self.final.emit(text)

    def _on_inner_rewritten(self, session, text: str):
        if session is not self._current:
            return
        self._live = str(text or '')
        self.rewritten.emit(join_heard(self._prefix, self._live))

    def _on_failed(self, session, code: str, detail: str):
        if session is self._current:
            self._failed = True
            self.failed.emit(code, detail)
        elif session is self._pending:
            # the new choice cannot listen (no such language for Apple Speech, …): the old one goes on
            self._pending = None
            self._forget(session)
            self.switch_failed.emit(code)
        else:
            logging.info('A listening that was being replaced failed: %s %s', code, detail[:200])

    def _on_inner_finished(self, session):
        info = self._sessions.get(session)
        if info is not None:
            info['over'] = True
        if session in self._old:
            self._old.remove(session)
        if session is self._pending:
            self._pending = None
            self._forget(session)
        if session is self._current and not self._stopping:
            self._stopping = True               # (it ended by itself: the whole recording ends)
            if self._pending is not None:
                pending, self._pending = self._pending, None
                self._forget(pending)
                pending.cancel()
            if info is not None and info['spec'] != self._target:
                self._retire_current()          # what it heard is still heard with the new choice
        self._maybe_redo()
        self._maybe_finish()

    # ── hearing the kept sound again ──
    def _maybe_redo(self):
        """Once the listenings that were replaced have stopped (their sound files are complete), all the
        sound before the current listening is heard again with the choice in the settings."""
        if self._done or not self._redo_wanted or self._old or self._redo_spec is not None:
            return
        paths = [info['path'] for session, info in sorted(self._sessions.items(), key=lambda item: item[1]['order'])
                 if session is not self._current and session is not self._pending and info['path']]
        self._redo_wanted = False
        if not paths:
            return
        self._redo_number += 1
        self._redo_spec = self._target
        if not self._redo_shown:
            self._redo_shown = True
            self.redoing.emit(True)
        number, joined = self._redo_number, os.path.join(self._folder, f'redo-{self._redo_number}.wav')
        signal = self._joined

        def work():
            try:
                usable = sound_files_as_one_wav(paths, joined)
            except Exception:
                logging.exception('Joining the kept recordings failed.')
                usable = False
            try:
                signal.emit(number, joined if usable else '')
            except RuntimeError:
                pass
        threading.Thread(target=work, name='voice-redo-join', daemon=True).start()

    def _on_joined(self, number: int, path: str):
        if number != self._redo_number or self._redo_spec is None:
            return
        if not path:
            self._on_heard(number, '')          # (no sound was kept: nothing was said before)
            return
        model_id, locale = self._redo_spec
        if model_id:
            engine = self._engine
            if callable(engine) and not hasattr(engine, 'transcribe_file'):
                engine = engine()               # (given as "the engine, when it is needed")
            signal, language = self._heard, self._language_of(locale)

            def work():
                try:
                    text = engine.transcribe_file(model_id, path, language)
                except Exception:
                    logging.exception('Hearing the kept recording again failed.')
                    text = None
                try:
                    signal.emit(number, text)
                except RuntimeError:
                    pass
            threading.Thread(target=work, name='voice-redo-model', daemon=True).start()
            return
        # Apple Speech hears the file the way it hears the microphone (the helper's --file)
        heard, failed = [], []
        session = self._apple_redo = VoiceInputSession(self._helper_path, locale, audio_file=path, parent=self)
        session.taps = False
        session.final.connect(lambda text: heard.append(text))
        session.failed.connect(lambda code, detail: failed.append(code))
        session.finished.connect(lambda: self._on_heard(number, None if failed else _join_all(heard)))
        session.start()

    def _on_heard(self, number: int, text):
        if number != self._redo_number:
            return
        spec, self._redo_spec = self._redo_spec, None
        self._apple_redo = None
        if text is None:
            logging.warning('What was said could not be heard again with the new choice; the words stay as they were.')
        elif spec == self._target:
            self._prefix = str(text or '')
            self.rewritten.emit(join_heard(self._prefix, self._live))
        else:
            self._redo_wanted = True            # the choice changed again meanwhile: once more
        self._maybe_redo()
        if self._redo_spec is None and not self._redo_wanted and self._redo_shown:
            self._redo_shown = False
            self.redoing.emit(False)
        self._maybe_finish()

    # ── the end ──
    def _maybe_finish(self):
        if self._done or not self._stopping:
            return
        if self._pending is not None or self._old or self._redo_spec is not None or self._redo_wanted:
            return
        if self._current is not None and not self._sessions.get(self._current, {}).get('over', True):
            return
        self._finish()

    def _finish(self):
        if self._done:
            return
        self._done = True
        if self._redo_shown:
            self._redo_shown = False
            self.redoing.emit(False)
        folder, self._folder = self._folder, ''
        if folder:
            shutil.rmtree(folder, ignore_errors=True)
        self.finished.emit()


def _join_all(texts) -> str:
    joined = ''
    for text in texts:
        joined = join_heard(joined, text)
    return joined


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
        if getattr(session, 'rewritten', None) is not None:
            session.rewritten.connect(self._rewrite)
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

    def _rewrite(self, text: str):
        """The model or language was changed while it listened and everything said so far was heard
        again: `text` takes the place of the finished words of this dictation (the grey words being
        spoken stay after it). Not when the user has edited inside them."""
        if self._over:
            return
        edit = self._editor_for()
        current = edit.toPlainText()
        if not self._reconcile(current):
            self._over = True
            self._session.cancel()
            return
        if self._touched:
            return
        text = str(text or '')
        before = _u16(current)[max(0, self._origin - 1) * 2:self._origin * 2].decode('utf-16-le', 'replace')
        if not before or before == '\n':
            text = text.lstrip()
        elif before.isascii() and before.isalnum() and text[:1].isascii() and text[:1].isalnum():
            text = ' ' + text
        old_final = self._start - self._origin
        cursor = QTextCursor(edit.document())
        last = max(0, edit.document().characterCount() - 1)
        cursor.setPosition(max(0, min(self._origin, last)))
        cursor.setPosition(max(0, min(self._start, last)), QTextCursor.MoveMode.KeepAnchor)
        if self._first_write:
            cursor.beginEditBlock()
            self._first_write = False
        else:
            cursor.joinPreviousEditBlock()      # (still the one undo step of the whole dictation)
        cursor.insertText(text)
        cursor.endEditBlock()
        delta = (cursor.position() - self._origin) - old_final
        self._start += delta
        self._end += delta
        self._wrote_any = self._wrote_any or bool(text)
        caret = QTextCursor(edit.document())
        caret.setPosition(max(0, min(self._end, max(0, edit.document().characterCount() - 1))))
        edit.setTextCursor(caret)
        self._last_doc = edit.toPlainText()
        self._mark(edit)

    def _on_finished(self):
        # whatever is still grey was heard but never made final: the words stay as they are
        self._over = True
        self._start = self._end
        self._mark(self._editor_for())

    # ── the user's own edits, told exactly (2026-11-22, the circle's card: "只要他不会去……覆盖我之前的修改，他
    # 也不会去重复在说某句话说两遍") ──
    def final_end(self) -> int:
        """Where the words that will not change any more end (the grey words being spoken follow)."""
        return self._start

    def touched(self) -> bool:
        return self._touched

    def forget_touch(self):
        """The user's edits were all taken back: the words are the recognizer's again (a rewrite after a
        change of model or language, or the tidy-up, may replace them again)."""
        self._touched = False

    def apply_user_edit(self, at: int, removed: int, text: str) -> bool:
        """The user changed `removed` characters at `at` into `text` (UTF-16 units, in the box). Done
        here, with the places moved by exactly that — not found again by comparing the texts, which
        cannot tell "an a put in before the grey abc" from "an a put in inside it" and would then write
        the next words after the wrong place (the words twice). Only in the words that are final: False
        (nothing done) for a change that reaches into the grey words still being spoken."""
        edit = self._editor_for()
        current = edit.toPlainText()
        if not self._over and not self._reconcile(current):
            return False
        at, removed, text = int(at), max(0, int(removed)), str(text or '')
        if not self._over and at + removed > self._start:
            return False                    # (the grey words: they are still being heard)
        cursor = QTextCursor(edit.document())
        last = max(0, edit.document().characterCount() - 1)
        cursor.setPosition(max(0, min(at, last)))
        cursor.setPosition(max(0, min(at + removed, last)), QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText(text)
        delta = u16_len(text) - removed
        if at + removed <= self._origin and at < self._origin:
            self._origin += delta           # before this dictation
            self._start += delta
            self._end += delta
        else:
            # in the final words (an edit right where they end belongs to them: what is said next comes
            # after it, never before it)
            if at < self._origin:
                self._origin = at
            if self._over:
                if at <= self._end:
                    self._end = max(self._origin, self._end + delta)
                self._start = self._end
            else:
                self._start = max(self._origin, self._start + delta)
                self._end = max(self._start, self._end + delta)
            self._touched = True
        self._last_doc = edit.toPlainText()
        self._mark(edit)
        return True

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
                 refresh_highlight=None, tidy_for=None, session_for=None, shadows_for=None, parent=None):
        super().__init__(parent)
        # shadows_for() → more (hidden) boxes that get the same words, written the same way, but never
        # the user's edits: the circle's card keeps "the words as the recognizer gave them" (what a
        # correction is learned against) and "the words as they were before this edit" (Esc) in them
        self._shadows_for = shadows_for
        self._shadow_writers = []
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
        self._shadow_writers = []
        if self._shadows_for is not None:
            for shadow in list(self._shadows_for() or []):
                self._shadow_writers.append(DictationIntoEdit(shadow, session, parent=self))
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
            for shadow in self._shadow_writers:
                try:
                    shadow.deleteLater()
                except RuntimeError:
                    pass
            self._shadow_writers = []
            self._set_state('idle')
            return
        self._tidy_raw = raw
        writer.mark_all(True)
        self._set_state('tidying')
        self._start_tidy(tidy, raw)

    def retidy(self):
        """The tidy-up was changed while it is being done (2026-11-22, Ryan: "只要这个下拉栏变过，我们当前
        正在输入的这个东西它立马就要变"): the pass starts again with the new one — the answer of the
        one under way is not used; with no tidy-up any more, the words stay as heard."""
        if self._state != 'tidying' or self._writer is None:
            return
        try:
            tidy = self._tidy_for() if self._tidy_for is not None else None
        except Exception:
            tidy = None
        if tidy is None:
            self._end_tidy(False)
            return
        self._start_tidy(tidy, getattr(self, '_tidy_raw', ''))

    def _start_tidy(self, tidy, raw: str):
        token = self._tidy_token = object()
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
        if replaced:
            for shadow in self._shadow_writers:
                try:
                    shadow.replace_dictated(raw, tidy)
                except RuntimeError:
                    pass
        self._end_tidy(replaced)

    # ── the user's own edits of the words (the circle's card, 2026-11-22) ──
    def apply_user_edit(self, at: int, removed: int, text: str) -> bool:
        """The user changed the words in the box (UTF-16 units): told to the writer of the dictation
        going on, so it knows exactly where its words are now; with none going on, simply done.
        False = not done (it reached into the grey words that are still being heard)."""
        if self._writer is not None:
            try:
                return self._writer.apply_user_edit(at, removed, text)
            except RuntimeError:
                return False
        try:
            edit = self._editor_for()
            cursor = QTextCursor(edit.document())
            last = max(0, edit.document().characterCount() - 1)
            cursor.setPosition(max(0, min(int(at), last)))
            cursor.setPosition(max(0, min(int(at) + max(0, int(removed)), last)), QTextCursor.MoveMode.KeepAnchor)
            cursor.insertText(str(text or ''))
            return True
        except RuntimeError:
            return False

    def apply_shadow_edit(self, index: int, box, at: int, removed: int, text: str) -> bool:
        """The same as apply_user_edit, in one of the shadow boxes (`index` in shadows_for(); `box` is
        that box, edited directly when no dictation is going on)."""
        if 0 <= index < len(self._shadow_writers):
            try:
                return self._shadow_writers[index].apply_user_edit(at, removed, text)
            except RuntimeError:
                return False
        try:
            cursor = QTextCursor(box.document())
            last = max(0, box.document().characterCount() - 1)
            cursor.setPosition(max(0, min(int(at), last)))
            cursor.setPosition(max(0, min(int(at) + max(0, int(removed)), last)), QTextCursor.MoveMode.KeepAnchor)
            cursor.insertText(str(text or ''))
            return True
        except RuntimeError:
            return False

    def final_end(self):
        """Where the words that will not change any more end in the box (None: nothing is being heard,
        all of it is final)."""
        if self._writer is None or self._state not in ('starting', 'listening', 'stopping'):
            return None
        return self._writer.final_end()

    def edited(self) -> bool:
        """The user has edited inside the words of the dictation going on."""
        return bool(self._writer is not None and self._writer.touched())

    def forget_edits(self):
        """The user's edits were all taken back (the words are the recognizer's again)."""
        if self._writer is not None:
            self._writer.forget_touch()

    def _end_tidy(self, replaced: bool):
        self._tidy_token = None
        self._watch.stop()
        for shadow in self._shadow_writers:
            try:
                shadow.deleteLater()
            except RuntimeError:
                pass
        self._shadow_writers = []
        writer, self._writer = self._writer, None
        if writer is not None:
            try:
                writer.mark_all(False)
            except RuntimeError:
                pass
            writer.deleteLater()
        self._set_state('idle')
        self.tidied.emit(bool(replaced))
