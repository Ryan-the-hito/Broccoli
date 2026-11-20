"""Downloadable speech models for Broccoli — 2026-11-16.

Plan: editor_handoff/PLAN_20261116_语音输入与本地模型.md (steps 4 and 6)

The speech models Broccoli runs itself (Qwen3-ASR, SenseVoice, Whisper), all through one runtime
(sherpa-onnx). Three parts:

  SPEECH_MODELS + ModelStore   what can be downloaded, where it is kept, downloading (resumable,
                               cancellable) and deleting
  SpeechEngine                 loads a model the first time it is needed, keeps it for a while,
                               turns sound into text; transcribes sound files
  LocalDictation               one listening: sound comes in as it is spoken, is cut into
                               sentences at the pauses, each sentence is recognized when it ends
                               ("final") and, while it is still being spoken, about once a second
                               ("partial": text that may still change)

No Qt and nothing of Broccoli's main file in here. Everything slow runs on threads of its own;
the recognizer itself runs outside Python's lock (onnxruntime).
"""
from __future__ import annotations

import json
import math
import os
import queue
import shutil
import subprocess
import tarfile
import tempfile
import threading
import time
import urllib.error
import urllib.request
import wave

SAMPLE_RATE = 16000
_RELEASES = 'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/'

# The models offered on the Local models page, in its order.
#   archive      the file on the runtime's own release page (tar.bz2); folder = what it unpacks to
#   download_mb  size of the download; disk_mb = size once unpacked
#   language     'auto' = the model hears which language is spoken; 'given' = it must be told
SPEECH_MODELS = (
    {'id': 'qwen3-asr-0.6b', 'name': 'Qwen3-ASR 0.6B', 'kind': 'qwen3', 'language': 'auto',
     'archive': 'sherpa-onnx-qwen3-asr-0.6B-int8-2026-03-25.tar.bz2',
     'folder': 'sherpa-onnx-qwen3-asr-0.6B-int8-2026-03-25', 'download_mb': 838, 'disk_mb': 972,
     'licence': 'Apache-2.0'},
    {'id': 'sensevoice-small', 'name': 'SenseVoice Small', 'kind': 'sense_voice', 'language': 'auto',
     'archive': 'sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17.tar.bz2',
     'folder': 'sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17', 'download_mb': 155, 'disk_mb': 242,
     'licence': 'FunASR Model Open Source License'},
    {'id': 'whisper-turbo', 'name': 'Whisper large-v3-turbo', 'kind': 'whisper', 'language': 'given',
     'archive': 'sherpa-onnx-whisper-turbo.tar.bz2',
     'folder': 'sherpa-onnx-whisper-turbo', 'download_mb': 538, 'disk_mb': 1040,
     'licence': 'MIT'},
)
_BY_ID = {entry['id']: entry for entry in SPEECH_MODELS}

# the files a model cannot do without (checked before it counts as installed)
_NEEDED = {
    'qwen3': ('conv_frontend.onnx', 'encoder.int8.onnx', 'decoder.int8.onnx', 'tokenizer'),
    'sense_voice': ('model.int8.onnx', 'tokens.txt'),
    'whisper': ('turbo-encoder.int8.onnx', 'turbo-decoder.int8.onnx', 'turbo-tokens.txt'),
}
WHISPER_LANGUAGES = {'zh', 'en', 'ja', 'ko', 'fr', 'de', 'es', 'it', 'pt', 'ru', 'yue'}


def speech_model(model_id: str) -> dict | None:
    return _BY_ID.get(str(model_id or ''))


def runtime_available() -> bool:
    try:
        import sherpa_onnx  # noqa: F401
        import numpy  # noqa: F401
        return True
    except Exception:
        return False


class DownloadCancelled(Exception):
    pass


class ModelStore:
    """The downloaded models on disk: <root>/models/<id>/… ; downloads in <root>/downloads/."""

    def __init__(self, root: str):
        self.root = str(root)
        self._lock = threading.Lock()
        self._downloads = {}        # id → {'cancel': Event, 'done': int, 'total': int, 'state': str, 'error': str}

    def model_dir(self, model_id: str) -> str:
        return os.path.join(self.root, 'models', str(model_id))

    def is_installed(self, model_id: str) -> bool:
        entry = speech_model(model_id)
        if entry is None:
            return False
        base = self.model_dir(model_id)
        return all(os.path.exists(os.path.join(base, name)) for name in _NEEDED[entry['kind']])

    def installed(self) -> list:
        return [entry['id'] for entry in SPEECH_MODELS if self.is_installed(entry['id'])]

    def delete(self, model_id: str) -> None:
        if speech_model(model_id) is None:
            return
        self.cancel_download(model_id)
        shutil.rmtree(self.model_dir(model_id), ignore_errors=True)
        for name in (self._part_path(model_id),):
            try:
                os.remove(name)
            except OSError:
                pass

    # ── downloading ──
    def _part_path(self, model_id: str) -> str:
        return os.path.join(self.root, 'downloads', f'{model_id}.part')

    def download_state(self, model_id: str) -> dict:
        """{'state': 'idle' | 'downloading' | 'unpacking' | 'failed', 'done', 'total', 'error'}"""
        with self._lock:
            job = self._downloads.get(model_id)
            if job is None:
                return {'state': 'idle', 'done': 0, 'total': 0, 'error': ''}
            return {key: job[key] for key in ('state', 'done', 'total', 'error')}

    def cancel_download(self, model_id: str) -> None:
        with self._lock:
            job = self._downloads.get(model_id)
        if job is not None:
            job['cancel'].set()

    def start_download(self, model_id: str, on_change=None, url: str = '') -> bool:
        """Starts (or goes on with) the download on a thread of its own; on_change(model_id) is
        called from that thread whenever download_state() has news. False = unknown model, already
        installed, or already downloading."""
        entry = speech_model(model_id)
        if entry is None or self.is_installed(model_id):
            return False
        with self._lock:
            job = self._downloads.get(model_id)
            if job is not None and job['state'] in ('downloading', 'unpacking'):
                return False
            job = self._downloads[model_id] = {'cancel': threading.Event(), 'done': 0, 'total': 0,
                                               'state': 'downloading', 'error': ''}
        tell = (lambda: on_change(model_id)) if on_change else (lambda: None)

        def work():
            try:
                self._download(entry, job, tell, url or _RELEASES + entry['archive'])
                with self._lock:
                    self._downloads.pop(model_id, None)
            except DownloadCancelled:
                with self._lock:
                    self._downloads.pop(model_id, None)     # the part file stays: the next start goes on from it
            except Exception as error:
                job['state'], job['error'] = 'failed', str(error)[:300]
            tell()
        threading.Thread(target=work, name=f'speech-model-download-{model_id}', daemon=True).start()
        return True

    def _download(self, entry: dict, job: dict, tell, url: str) -> None:
        part = self._part_path(entry['id'])
        os.makedirs(os.path.dirname(part), exist_ok=True)
        have = os.path.getsize(part) if os.path.exists(part) else 0
        request = urllib.request.Request(url, headers={'User-Agent': 'Broccoli'})
        if have:
            request.add_header('Range', f'bytes={have}-')
        try:
            response = urllib.request.urlopen(request, timeout=30)
        except urllib.error.HTTPError as error:
            if error.code != 416:       # 416: the part file already is the whole file
                raise
            response = None
        if response is not None:
            resumed = response.status == 206
            if have and not resumed:
                have = 0                # the server sent the whole file again
            length = int(response.headers.get('Content-Length', 0) or 0)
            job['total'] = have + length if length else 0
            job['done'] = have
            tell()
            last = time.monotonic()
            with open(part, 'ab' if resumed else 'wb') as out:
                while True:
                    if job['cancel'].is_set():
                        raise DownloadCancelled()
                    block = response.read(256 * 1024)
                    if not block:
                        break
                    out.write(block)
                    job['done'] += len(block)
                    if time.monotonic() - last >= 0.3:
                        last = time.monotonic()
                        tell()
            if job['total'] and job['done'] < job['total']:
                raise OSError('The download ended early. Start it again to go on.')
        job['state'] = 'unpacking'
        tell()
        staging = tempfile.mkdtemp(prefix=f'{entry["id"]}-', dir=os.path.dirname(part))
        try:
            with tarfile.open(part, 'r:bz2') as archive:
                for member in archive:
                    if job['cancel'].is_set():
                        raise DownloadCancelled()
                    if '/test_wavs/' in '/' + member.name:      # sample recordings: not needed
                        continue
                    archive.extract(member, staging, filter='data')
            unpacked = os.path.join(staging, entry['folder'])
            if not all(os.path.exists(os.path.join(unpacked, name)) for name in _NEEDED[entry['kind']]):
                try:
                    os.remove(part)     # not worth going on from: the next start downloads it afresh
                except OSError:
                    pass
                raise OSError('The downloaded model is incomplete.')
            target = self.model_dir(entry['id'])
            shutil.rmtree(target, ignore_errors=True)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            os.replace(unpacked, target)
        except (tarfile.TarError, EOFError) as error:
            try:
                os.remove(part)         # a broken archive is not worth going on from
            except OSError:
                pass
            raise OSError(f'The downloaded file is damaged ({error}). Download it again.')
        finally:
            shutil.rmtree(staging, ignore_errors=True)
        try:
            os.remove(part)
        except OSError:
            pass


def _wave_data(path: str) -> bytes:
    """The samples of a WAVE file. (Read by hand: for some sources afconvert writes the "extensible"
    kind of header, which Python's wave module refuses — the samples are what was asked for all the same.)"""
    with open(path, 'rb') as handle:
        data = handle.read()
    if data[:4] != b'RIFF' or data[8:12] != b'WAVE':
        raise ValueError('unreadable sound file')
    at = 12
    while at + 8 <= len(data):
        name, size = data[at:at + 4], int.from_bytes(data[at + 4:at + 8], 'little')
        if name == b'data':
            body = data[at + 8:at + 8 + size]
            return body[:len(body) - len(body) % 2]
        at += 8 + size + (size & 1)
    raise ValueError('unreadable sound file')


def read_sound_file(path: str):
    """Any sound file macOS can read → float32 samples at 16 kHz, one channel."""
    import numpy as np
    handle, converted = tempfile.mkstemp(prefix='broccoli_speech_', suffix='.wav')
    os.close(handle)
    try:
        done = subprocess.run(['/usr/bin/afconvert', '-f', 'WAVE', '-d', f'LEI16@{SAMPLE_RATE}', '-c', '1', path, converted],
                              capture_output=True)
        if done.returncode != 0:
            raise ValueError('unreadable sound file')
        return np.frombuffer(_wave_data(converted), dtype='<i2').astype('float32') / 32768.0
    finally:
        try:
            os.remove(converted)
        except OSError:
            pass


class SpeechEngine:
    """Loads a downloaded model when it is first needed and keeps it until it has not been used
    for `idle_seconds` (a model takes a second or two to load and up to a few GB of memory)."""

    def __init__(self, store: ModelStore, idle_seconds: float = 600.0, threads: int = 4):
        self.store = store
        self._idle_seconds = float(idle_seconds)
        self._threads = int(threads)
        self._lock = threading.Lock()
        self._loaded = {}           # (model id, language) → [recognizer, last used]
        self._use = threading.Lock()    # one recognition at a time (they would only slow each other)

    def loaded(self) -> list:
        with self._lock:
            return sorted(key[0] for key in self._loaded)

    def unload(self, model_id: str = '') -> None:
        with self._lock:
            for key in [key for key in self._loaded if not model_id or key[0] == model_id]:
                del self._loaded[key]

    def _drop_idle(self):
        now = time.monotonic()
        with self._lock:
            for key in [key for key, item in self._loaded.items() if now - item[1] > self._idle_seconds]:
                del self._loaded[key]

    def recognizer(self, model_id: str, language: str = ''):
        entry = speech_model(model_id)
        if entry is None or not self.store.is_installed(model_id):
            raise LookupError(f'speech model not installed: {model_id}')
        language = str(language or '').lower().split('-')[0]
        key = (model_id, language if entry['language'] == 'given' else '')
        self._drop_idle()
        with self._lock:
            item = self._loaded.get(key)
            if item is not None:
                item[1] = time.monotonic()
                return item[0]
        import sherpa_onnx
        base = self.store.model_dir(model_id)

        def at(name):
            return os.path.join(base, name)
        if entry['kind'] == 'qwen3':
            made = sherpa_onnx.OfflineRecognizer.from_qwen3_asr(
                conv_frontend=at('conv_frontend.onnx'), encoder=at('encoder.int8.onnx'),
                decoder=at('decoder.int8.onnx'), tokenizer=at('tokenizer'), num_threads=self._threads)
        elif entry['kind'] == 'sense_voice':
            made = sherpa_onnx.OfflineRecognizer.from_sense_voice(
                model=at('model.int8.onnx'), tokens=at('tokens.txt'), num_threads=self._threads, use_itn=True)
        else:
            made = sherpa_onnx.OfflineRecognizer.from_whisper(
                encoder=at('turbo-encoder.int8.onnx'), decoder=at('turbo-decoder.int8.onnx'),
                tokens=at('turbo-tokens.txt'), num_threads=self._threads,
                language=key[1] if key[1] in WHISPER_LANGUAGES else 'en', task='transcribe')
        with self._lock:
            self._loaded[key] = [made, time.monotonic()]
        return made

    def recognize(self, model_id: str, samples, language: str = '') -> str:
        recognizer = self.recognizer(model_id, language)
        with self._use:
            stream = recognizer.create_stream()
            stream.accept_waveform(SAMPLE_RATE, samples)
            recognizer.decode_stream(stream)
            return str(stream.result.text or '').strip()

    def transcribe_file(self, model_id: str, path: str, language: str = '') -> str:
        """A whole sound file: cut at the pauses (the models are made for sentences, not hours),
        each piece recognized, the texts joined."""
        samples = read_sound_file(path)
        pieces = []
        for start, end in cut_at_pauses(samples):
            text = self.recognize(model_id, samples[start:end], language)
            if text:
                pieces.append(text)
        return join_sentences(pieces)


def join_sentences(pieces) -> str:
    out = ''
    for piece in pieces:
        piece = str(piece or '').strip()
        if not piece:
            continue
        if out and out[-1].isascii() and piece[0].isascii() and not out[-1].isspace():
            out += ' '              # Latin text: a space between sentences; Chinese / Japanese: none
        out += piece
    return out


# ── cutting sound into sentences at the pauses ───────────────────────────────────────────────
FRAME_SECONDS = 0.03
FRAME = int(SAMPLE_RATE * FRAME_SECONDS)


def _frame_loudness(samples):
    import numpy as np
    count = len(samples) // FRAME
    if count <= 0:
        return np.zeros(0, dtype='float32')
    frames = samples[:count * FRAME].reshape(count, FRAME)
    return np.sqrt(np.mean(frames * frames, axis=1))


class PauseDetector:
    """Says, frame by frame, whether someone is speaking. The quiet level is learned as it goes
    (a fan, a noisy room), so "loud" means clearly above this room's quiet."""

    def __init__(self):
        self.floor = 0.002

    def is_speech(self, loudness: float) -> bool:
        threshold = max(0.006, self.floor * 3.0)
        if loudness < threshold:
            self.floor = self.floor * 0.95 + loudness * 0.05     # quiet: follow it
        else:
            self.floor = self.floor * 0.999 + loudness * 0.001   # speech: drift up very slowly
        return loudness >= threshold


def cut_at_pauses(samples, pause_seconds: float = 0.6, max_seconds: float = 25.0) -> list:
    """[(start, end)] in samples: the stretches of speech, with a little quiet kept around them."""
    detector = PauseDetector()
    loud = [detector.is_speech(float(value)) for value in _frame_loudness(samples)]
    pieces, start, quiet = [], None, 0
    need = int(math.ceil(pause_seconds / FRAME_SECONDS))
    longest = int(max_seconds / FRAME_SECONDS)
    for index, on in enumerate(loud):
        if on:
            start = index if start is None else start
            quiet = 0
        elif start is not None:
            quiet += 1
        if start is not None and (quiet >= need or index - start >= longest):
            pieces.append((start, index - quiet + 1))
            start, quiet = None, 0
    if start is not None:
        pieces.append((start, len(loud) - quiet))
    pad = int(0.2 / FRAME_SECONDS)
    return [(max(0, (a - pad) * FRAME), min(len(samples), (b + pad) * FRAME))
            for a, b in pieces if (b - a) * FRAME_SECONDS >= 0.25]


class LocalDictation:
    """One listening with a downloaded model.

    `sound()` yields 16-bit little-endian sound at 16 kHz as it is spoken (bytes of any length;
    ending = the listening is over). The callbacks come from this object's own threads:
        on_partial(text)   the sentence being spoken, as far as it is heard — may still change
        on_final(text)     a finished sentence — will not change
        on_level(0–1)      loudness, about 15 a second
        on_done()          always last, once

    A sentence ends at a pause of `pause_seconds`. While one is being spoken, what there is of it
    is recognized again every `partial_seconds` (None = only finished sentences are reported).
    """

    def __init__(self, engine: SpeechEngine, model_id: str, language: str, sound,
                 on_partial=None, on_final=None, on_level=None, on_done=None, on_error=None, on_tone=None,
                 pause_seconds: float = 0.7, partial_seconds: float | None = 1.0, max_seconds: float = 25.0):
        self._engine = engine
        self._model_id = model_id
        self._language = language
        self._sound = sound
        self._on_partial = on_partial or (lambda text: None)
        self._on_final = on_final or (lambda text: None)
        self._on_level = on_level or (lambda value: None)
        self._on_tone = on_tone or (lambda value: None)     # how high the voice is, 0–1, with each loudness
        self._on_done = on_done or (lambda: None)
        self._on_error = on_error or (lambda code, detail: None)
        self._pause_frames = int(math.ceil(pause_seconds / FRAME_SECONDS))
        self._partial_seconds = partial_seconds
        self._max_frames = int(max_seconds / FRAME_SECONDS)
        self._jobs = queue.Queue()
        self._cancelled = threading.Event()
        self._last_final = ''
        self.sentences = 0          # finished sentences so far
        self.partials = 0           # partial texts reported so far
        self._listener = threading.Thread(target=self._listen, name='local-dictation-listen', daemon=True)
        self._worker = threading.Thread(target=self._recognize, name='local-dictation-recognize', daemon=True)

    def start(self):
        self._worker.start()
        self._listener.start()

    def cancel(self):
        """Stop at once: what is not final yet is dropped."""
        self._cancelled.set()

    def join(self, timeout=None):
        self._listener.join(timeout)
        self._worker.join(timeout)

    # ── the listening thread: sound in, sentences out ──
    def _listen(self):
        import numpy as np
        detector = PauseDetector()
        pending = b''
        before = []                 # the last quiet frames: kept so a sentence's first sound is not cut off
        sentence = []               # frames of the sentence being spoken
        quiet = 0
        last_partial = time.monotonic()
        last_level = 0.0
        try:
            for block in self._sound():
                if self._cancelled.is_set():
                    break
                pending += block
                usable = len(pending) - len(pending) % (FRAME * 2)
                if usable <= 0:
                    continue
                samples = np.frombuffer(pending[:usable], dtype='<i2').astype('float32') / 32768.0
                pending = pending[usable:]
                for index in range(0, len(samples), FRAME):
                    frame = samples[index:index + FRAME]
                    loudness = float(np.sqrt(np.mean(frame * frame)))
                    now = time.monotonic()
                    if now - last_level >= 0.066:
                        last_level = now
                        self._on_level(max(0.0, min(1.0, (20 * math.log10(max(loudness, 1e-6)) + 50) / 50)))
                        # about the pitch: zero crossings a second / 2; 90 Hz … 2000 Hz → 0 … 1 (by octave)
                        crossings = int(np.count_nonzero((frame[1:] >= 0) != (frame[:-1] >= 0)))
                        hertz = crossings * SAMPLE_RATE / (2.0 * max(1, len(frame)))
                        self._on_tone(max(0.0, min(1.0, math.log2(max(hertz, 90.0) / 90.0) / math.log2(2000.0 / 90.0))))
                    speaking = detector.is_speech(loudness)
                    if not sentence:
                        if speaking:
                            sentence = before[-7:] + [frame]      # with 0.2 s of what came before
                            quiet = 0
                            last_partial = now
                        else:
                            before.append(frame)
                            del before[:-10]
                        continue
                    sentence.append(frame)
                    quiet = 0 if speaking else quiet + 1
                    if quiet >= self._pause_frames or len(sentence) >= self._max_frames:
                        # without the pause itself (0.2 s of it stays): a long quiet tail makes the
                        # models repeat the last syllables ("settingsttings", SenseVoice, 2026-11-16)
                        keep = len(sentence) - max(0, quiet - 7)
                        self._jobs.put(('final', np.concatenate(sentence[:keep])))
                        sentence, before, quiet = [], [], 0
                    elif self._partial_seconds and now - last_partial >= self._partial_seconds and quiet < 5:
                        last_partial = now
                        self._jobs.put(('partial', np.concatenate(sentence)))
            if sentence and not self._cancelled.is_set() and len(sentence) * FRAME_SECONDS >= 0.25:
                self._jobs.put(('final', np.concatenate(sentence)))     # the last words when it stops
        except Exception as error:
            self._on_error('recognition_failed', str(error)[:300])
        self._jobs.put(('end', None))

    # ── the recognizing thread ──
    def _recognize(self):
        try:
            while True:
                kind, samples = self._jobs.get()
                if kind == 'end':
                    break
                if self._cancelled.is_set():
                    continue
                if kind == 'partial':
                    # behind already (a newer partial or the sentence's end is waiting)? skip this one
                    if not self._jobs.empty():
                        continue
                try:
                    text = self._engine.recognize(self._model_id, samples, self._language)
                except Exception as error:
                    self._on_error('recognition_failed', str(error)[:300])
                    self._cancelled.set()
                    continue
                if self._cancelled.is_set():
                    continue
                if kind == 'partial':
                    if text:
                        self.partials += 1
                        self._on_partial(self._spaced(text))
                else:
                    if text:
                        self.sentences += 1
                        spaced = self._spaced(text)
                        self._last_final = text
                        self._on_final(spaced)
                    else:
                        self._on_partial('')        # a noise, not a sentence: take the grey text away
        finally:
            self._on_done()

    def _spaced(self, text: str) -> str:
        """Latin sentences get a space between them; Chinese / Japanese ones do not."""
        last = self._last_final
        if last and last[-1].isascii() and text[:1].isascii() and not last[-1].isspace():
            return ' ' + text
        return text
