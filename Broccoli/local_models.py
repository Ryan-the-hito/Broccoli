"""Local models for Broccoli — 2026-11-16.

Plan: editor_handoff/PLAN_20261116_语音输入与本地模型.md (step 3)

The models that run on this Mac are reached the same way as every other model in Broccoli: as an
ordinary profile (endpoint + key + model name). LocalModelsServer is the endpoint — a small
OpenAI-shaped server inside Broccoli, on 127.0.0.1 only, behind a key made up on this Mac:

    GET  /v1/models
    POST /v1/chat/completions        model "apple-intelligence": the Mac's own language model
    POST /v1/audio/transcriptions    model "apple-speech": the Mac's own speech recognizer

Both are answered by the bundled helper voice_input/BroccoliVoice (Swift: FoundationModels and
SpeechAnalyzer, macOS 26+), one helper run per request. Nothing leaves this Mac.

No Qt and nothing of Broccoli's main file in here. The server runs on its own threads.
"""
from __future__ import annotations

import json
import os
import secrets
import socket
import subprocess
import tempfile
import threading
import time
import uuid
from email.parser import BytesParser
from email.policy import HTTP
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APPLE_SPEECH_MODEL = 'apple-speech'
APPLE_INTELLIGENCE_MODEL = 'apple-intelligence'
LOCAL_MODELS_HOST = '127.0.0.1'
LOCAL_MODELS_MAX_BODY = 512 * 1024 * 1024     # an audio file to transcribe
CHAT_TIMEOUT_SECONDS = 600
TRANSCRIBE_TIMEOUT_SECONDS = 3600

# the built-in models, in the order the Local models page lists them
#   kind: 'speech' | 'chat';  check_key / ready_value: where the helper's --check says it can run
LOCAL_MODEL_CATALOG = (
    {'id': APPLE_SPEECH_MODEL, 'name': 'Apple Speech', 'kind': 'speech', 'builtin': True},
    {'id': APPLE_INTELLIGENCE_MODEL, 'name': 'Apple Intelligence', 'kind': 'chat', 'builtin': True},
)

# "language" of a transcription request (ISO 639-1, as the OpenAI API has it) → the locale to listen in
LOCALE_BY_LANGUAGE_CODE = {
    'zh': 'zh-CN', 'en': 'en-US', 'ja': 'ja-JP', 'ko': 'ko-KR', 'fr': 'fr-FR', 'de': 'de-DE',
    'es': 'es-ES', 'it': 'it-IT', 'pt': 'pt-BR', 'ru': 'ru-RU', 'yue': 'yue-CN',
}


def local_model_state(model_id: str, check: dict) -> str:
    """What the helper's --check answer means for one built-in model:
    'ready' | 'unsupported' (this Mac / this macOS cannot) | 'not_enabled' (Apple Intelligence is
    switched off) | 'not_ready' (still downloading)."""
    check = check if isinstance(check, dict) else {}
    if not check:
        return 'unsupported'
    if model_id == APPLE_SPEECH_MODEL:
        return 'ready' if check.get('available') else 'unsupported'
    if model_id == APPLE_INTELLIGENCE_MODEL:
        state = str(check.get('language_model', '') or '')
        if state == 'available':
            return 'ready'
        return state if state in ('not_enabled', 'not_ready') else 'unsupported'
    return 'unsupported'


def load_state(path: str) -> dict:
    """{'port': int, 'key': str} as saved ({} when there is none yet)."""
    try:
        with open(path, encoding='utf-8') as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    try:
        port = int(data.get('port', 0) or 0)
    except (TypeError, ValueError):
        port = 0
    key = str(data.get('key', '') or '')
    return {'port': port, 'key': key} if 0 < port < 65536 and key else {}


def save_state(path: str, state: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp = f'{path}.{os.getpid()}.tmp'
    with open(temp, 'w', encoding='utf-8') as handle:
        json.dump({'port': int(state['port']), 'key': str(state['key'])}, handle)
    os.chmod(temp, 0o600)       # the key opens the models to whoever reads it
    os.replace(temp, path)


def base_url(port: int) -> str:
    return f'http://{LOCAL_MODELS_HOST}:{int(port)}'


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind((LOCAL_MODELS_HOST, 0))
        return int(probe.getsockname()[1])


class _HelperError(Exception):
    def __init__(self, code: str, detail: str = ''):
        super().__init__(code)
        self.code = code
        self.detail = detail


def _error_status(code: str):
    """(HTTP status, OpenAI-style error code, message) for a helper error code."""
    if code == 'context_too_long':
        return 400, 'context_length_exceeded', ('This conversation is too long for the model on this Mac. '
                                                'Start a new conversation or use another model.')
    if code == 'refused':
        return 400, 'content_filter', 'The model on this Mac declined to answer this.'
    if code == 'model_unavailable':
        return 503, 'model_unavailable', 'Apple Intelligence is not available on this Mac right now.'
    if code == 'helper_missing':
        return 503, 'model_unavailable', 'This copy of Broccoli has no on-device models (they need macOS 26 or later).'
    if code == 'language_unsupported':
        return 400, 'language_unsupported', 'The speech recognizer on this Mac does not support this language.'
    if code == 'language_download_failed':
        return 503, 'language_download_failed', 'The speech model for this language could not be downloaded.'
    if code == 'model_not_downloaded':
        return 404, 'model_not_found', 'This speech model is not downloaded on this Mac (Settings › Models › Local models).'
    if code == 'speech_unavailable':
        return 503, 'model_unavailable', 'This Mac cannot recognize speech on the device.'
    return 500, code or 'local_model_failed', 'The model on this Mac could not finish this request.'


class LocalModelsServer:
    """The endpoint of the local profiles. start() once; port and key stay the same across
    restarts (saved in `state_path`) so the profiles keep pointing at it."""

    def __init__(self, helper_path_for, locale_for, state_path: str, speech_models_for=None, speech_transcribe=None):
        self._helper_path_for = helper_path_for      # () -> path of BroccoliVoice ('' = none)
        self._locale_for = locale_for                # () -> locale for a transcription that names no language
        # the downloaded speech models (local_speech.py): () -> their ids, and
        # (model id, sound file, language) -> text; LookupError = not downloaded
        self._speech_models_for = speech_models_for or (lambda: [])
        self._speech_transcribe = speech_transcribe
        self._state_path = state_path
        self._server = None
        self._thread = None
        self.port = 0
        self.key = ''
        self.previous_port = 0      # the saved port, when it was taken and another had to be used

    def is_running(self) -> bool:
        return self._server is not None

    def base_url(self) -> str:
        return base_url(self.port) if self.port else ''

    def start(self) -> bool:
        """True when it is serving. The saved port is used again; taken → a new one (the caller
        re-points the profiles: see previous_port)."""
        if self._server is not None:
            return True
        state = load_state(self._state_path)
        key = state.get('key') or secrets.token_urlsafe(32)
        candidates = [state['port']] if state.get('port') else []
        candidates.append(0)
        for port in candidates:
            try:
                server = ThreadingHTTPServer((LOCAL_MODELS_HOST, port or _free_port()), _Handler)
            except OSError:
                continue
            server.daemon_threads = True
            server.owner = self
            self._server = server
            self.port = int(server.server_address[1])
            self.key = key
            if state.get('port') and state['port'] != self.port:
                self.previous_port = int(state['port'])
            if state.get('port') != self.port or state.get('key') != key:
                save_state(self._state_path, {'port': self.port, 'key': key})
            self._thread = threading.Thread(target=server.serve_forever, name='local-models-server', daemon=True)
            self._thread.start()
            return True
        return False

    def stop(self):
        server, self._server = self._server, None
        if server is not None:
            server.shutdown()
            server.server_close()

    # ── the helper ──
    def _helper(self) -> str:
        path = str(self._helper_path_for() or '')
        if not path or not os.path.isfile(path):
            raise _HelperError('helper_missing')
        return path

    def chat_events(self, request: dict):
        """The helper's events for one chat request, as they come: ('delta', text) …; raises
        _HelperError. The caller closes the generator to end the helper early."""
        payload = {'messages': request.get('messages') or []}
        for key in ('temperature', 'max_tokens', 'max_completion_tokens'):
            if isinstance(request.get(key), (int, float)) and not isinstance(request.get(key), bool):
                payload[key] = request[key]
        process = subprocess.Popen([self._helper(), '--chat'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL)
        killer = threading.Timer(CHAT_TIMEOUT_SECONDS, process.kill)
        killer.daemon = True
        killer.start()
        try:
            process.stdin.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
            process.stdin.close()
            done = False
            for line in process.stdout:
                try:
                    item = json.loads(line.decode('utf-8', 'replace'))
                except ValueError:
                    continue
                kind = item.get('type')
                if kind in ('delta', 'replace'):
                    yield kind, str(item.get('text', '') or '')
                elif kind == 'error':
                    raise _HelperError(str(item.get('code', '') or 'chat_failed'), str(item.get('detail', '') or ''))
                elif kind == 'done':
                    done = True
            if not done:
                raise _HelperError('chat_failed', 'the helper ended early')
        finally:
            killer.cancel()
            if process.poll() is None:
                process.kill()
            process.wait()

    def model_ids(self) -> list:
        try:
            extra = [str(item) for item in self._speech_models_for()]
        except Exception:
            extra = []
        return [entry['id'] for entry in LOCAL_MODEL_CATALOG] + extra

    def transcribe(self, audio_path: str, language: str = '', model: str = '') -> str:
        language = str(language or '').strip().replace('_', '-')
        if model and model != APPLE_SPEECH_MODEL and self._speech_transcribe is not None:
            # a downloaded model; it is told the language only when the request (or Settings) names one
            spoken = language or str(self._locale_for() or '')
            try:
                return self._speech_transcribe(model, audio_path, spoken.split('-')[0].lower())
            except LookupError:
                raise _HelperError('model_not_downloaded', model)
            except ValueError:
                raise _HelperError('recognition_failed', 'unreadable sound file')
        locale = LOCALE_BY_LANGUAGE_CODE.get(language.lower(), language) or str(self._locale_for() or 'en-US')
        try:
            done = subprocess.run([self._helper(), '--locale', locale, '--file', audio_path], capture_output=True,
                                  stdin=subprocess.DEVNULL, timeout=TRANSCRIBE_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            raise _HelperError('recognition_failed', 'timed out')
        pieces = []
        for line in done.stdout.decode('utf-8', 'replace').splitlines():
            try:
                item = json.loads(line)
            except ValueError:
                continue
            if item.get('type') == 'final':
                pieces.append(str(item.get('text', '') or ''))
            elif item.get('type') == 'error':
                raise _HelperError(str(item.get('code', '') or 'recognition_failed'), str(item.get('detail', '') or ''))
        text = ''.join(pieces).strip()
        try:
            from voice_input import tidy_dictated_text     # no stray spaces inside Chinese / Japanese
            text = tidy_dictated_text(text)
        except Exception:
            pass
        return text


class _Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    server_version = 'BroccoliLocalModels'

    def log_message(self, format, *args):     # quiet: Broccoli's own log has what matters
        pass

    # ── plumbing ──
    def _send_json(self, status: int, body: dict):
        data = json.dumps(body, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_error(self, status: int, code: str, message: str):
        self._send_json(status, {'error': {'message': message, 'type': 'invalid_request_error' if status < 500 else 'server_error',
                                           'code': code}})

    def _send_helper_error(self, error: _HelperError):
        status, code, message = _error_status(error.code)
        self._send_error(status, code, message)

    def _allowed(self) -> bool:
        owner = self.server.owner
        given = str(self.headers.get('Authorization', '') or '')
        if given.startswith('Bearer ') and secrets.compare_digest(given[7:].strip(), owner.key):
            return True
        self._send_error(401, 'invalid_api_key', 'Wrong key for the models on this Mac.')
        return False

    def _body(self):
        try:
            length = int(self.headers.get('Content-Length', '0') or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > LOCAL_MODELS_MAX_BODY:
            return None
        return self.rfile.read(length)

    def _route(self) -> str:
        path = self.path.split('?', 1)[0].rstrip('/')
        return path[3:] if path.startswith('/v1/') else path     # with or without the /v1

    # ── routes ──
    def do_GET(self):
        if not self._allowed():
            return
        if self._route() == '/models':
            now = int(time.time())
            self._send_json(200, {'object': 'list', 'data': [
                {'id': model_id, 'object': 'model', 'created': now, 'owned_by': 'this-mac'}
                for model_id in self.server.owner.model_ids()]})
            return
        self._send_error(404, 'not_found', 'No such address.')

    def do_POST(self):
        if not self._allowed():
            return
        route = self._route()
        if route == '/chat/completions':
            self._chat()
        elif route == '/audio/transcriptions':
            self._transcribe()
        else:
            self._body()
            self._send_error(404, 'not_found', 'No such address.')

    def _chat(self):
        raw = self._body()
        try:
            request = json.loads(raw.decode('utf-8')) if raw else None
        except (ValueError, UnicodeDecodeError):
            request = None
        if not isinstance(request, dict) or not isinstance(request.get('messages'), list):
            self._send_error(400, 'bad_request', 'The request has no messages.')
            return
        owner = self.server.owner
        model = str(request.get('model', '') or APPLE_INTELLIGENCE_MODEL)
        ident = 'chatcmpl-' + uuid.uuid4().hex
        created = int(time.time())
        events = owner.chat_events(request)
        if not request.get('stream'):
            text = ''
            try:
                for kind, piece in events:
                    text = text + piece if kind == 'delta' else piece
            except _HelperError as error:
                self._send_helper_error(error)
                return
            self._send_json(200, {
                'id': ident, 'object': 'chat.completion', 'created': created, 'model': model,
                'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': text}, 'finish_reason': 'stop'}],
                'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}})
            return

        def chunk(delta: dict, finish=None, extra=None) -> bytes:
            body = {'id': ident, 'object': 'chat.completion.chunk', 'created': created, 'model': model,
                    'choices': [{'index': 0, 'delta': delta, 'finish_reason': finish}]}
            if extra:
                body.update(extra)
            return b'data: ' + json.dumps(body, ensure_ascii=False).encode('utf-8') + b'\n\n'

        # the first event decides between an error answer and a stream
        try:
            first = next(events, None)
        except _HelperError as error:
            self._send_helper_error(error)
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'close')
        self.end_headers()
        self.close_connection = True
        try:
            self.wfile.write(chunk({'role': 'assistant', 'content': ''}))
            sent = ''
            pending = [first] if first is not None else []
            try:
                while True:
                    item = pending.pop() if pending else next(events, None)
                    if item is None:
                        break
                    kind, piece = item
                    if kind == 'replace':       # the model rewrote what it had said: send what is new
                        piece = piece[len(sent):] if piece.startswith(sent) else ''
                    if piece:
                        sent += piece
                        self.wfile.write(chunk({'content': piece}))
                        self.wfile.flush()
                finish = 'stop'
            except _HelperError as error:
                _status, code, message = _error_status(error.code)
                self.wfile.write(b'data: ' + json.dumps({'error': {'message': message, 'code': code}}).encode('utf-8') + b'\n\n')
                finish = 'stop'
            self.wfile.write(chunk({}, finish))
            if isinstance(request.get('stream_options'), dict) and request['stream_options'].get('include_usage'):
                self.wfile.write(b'data: ' + json.dumps({
                    'id': ident, 'object': 'chat.completion.chunk', 'created': created, 'model': model, 'choices': [],
                    'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}}).encode('utf-8') + b'\n\n')
            self.wfile.write(b'data: [DONE]\n\n')
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass                                # the asker went away (Stop): the helper ends with the generator
        finally:
            events.close()

    def _transcribe(self):
        raw = self._body()
        content_type = str(self.headers.get('Content-Type', '') or '')
        if not raw or 'multipart/form-data' not in content_type:
            self._send_error(400, 'bad_request', 'Send the audio as multipart/form-data with a "file" part.')
            return
        message = BytesParser(policy=HTTP).parsebytes(
            b'Content-Type: ' + content_type.encode('latin-1') + b'\r\nMIME-Version: 1.0\r\n\r\n' + raw)
        fields, audio, filename = {}, None, ''
        for part in message.iter_parts():
            name = part.get_param('name', header='content-disposition')
            if name == 'file':
                audio = part.get_payload(decode=True)
                filename = str(part.get_filename() or '')
            elif name:
                value = part.get_payload(decode=True)
                fields[str(name)] = value.decode('utf-8', 'replace').strip() if value is not None else ''
        if not audio:
            self._send_error(400, 'bad_request', 'The request has no audio file.')
            return
        suffix = os.path.splitext(filename)[1][:10] or '.wav'
        handle, path = tempfile.mkstemp(prefix='broccoli_local_audio_', suffix=suffix)
        try:
            with os.fdopen(handle, 'wb') as out:
                out.write(audio)
            text = self.server.owner.transcribe(path, fields.get('language', ''), fields.get('model', ''))
        except _HelperError as error:
            if error.code == 'recognition_failed':
                self._send_error(400, 'audio_unreadable',
                                 'The audio could not be read on this Mac (try m4a, mp3, wav, aiff, flac or caf).')
            else:
                self._send_helper_error(error)
            return
        finally:
            try:
                os.remove(path)
            except OSError:
                pass
        if fields.get('response_format', 'json') == 'text':
            data = (text + '\n').encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self._send_json(200, {'text': text})
