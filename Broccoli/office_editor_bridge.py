"""Bridge between Broccoli's editor and a bundled office-editing component (Word / Excel / PowerPoint).

The component is a folder of static web files that Broccoli ships unchanged (office_editor/site,
described by office_editor/manifest.json; refreshed as a whole by office_editor_update.py). Nothing
in Broccoli knows how that component works except one small adapter class in this file. To replace
the component with another one: add an adapter for it, name the adapter in manifest.json, done.

Three layers:
  OfficeEditorAdapter   everything specific to one component: which headers its files need, the
                        page that hosts it, how to tell it "open these bytes" / "give me the file".
  OfficeSiteServer      a file server on 127.0.0.1 (random port) for the component's files, plus a
                        private channel per view: document bytes in, saved bytes out, events.
  OfficeEditorView      the Qt widget the editor shows. Five actions only: start (construct),
                        open_bytes, save, the dirtyChanged signal, set_readonly.

The server and the adapter need no Qt; only OfficeEditorView does (imported on first use).
"""
import fnmatch
import http.server
import json
import mimetypes
import os
import posixpath
import secrets
import socketserver
import sys
import threading
import urllib.parse

OFFICE_EDITOR_EXTS = ('.docx', '.xlsx', '.pptx')
_CHANNEL_PREFIX = '/__broccoli_office/'
_MAX_SAVE_BYTES = 512 * 1024 * 1024


# ── adapters ─────────────────────────────────────────────────────────────────────────────────
class OfficeEditorAdapter:
    """What Broccoli needs to know about one office-editing component."""
    name = ''
    # file extension -> the component's own name for that format when saving
    save_formats = {}

    def response_headers(self, path: str) -> dict:
        """Extra HTTP headers for one of the component's files (path starts with '/')."""
        return {}

    def content_type(self, path: str):
        """A content type the file's extension does not give, or None."""
        return None

    def host_page(self, token: str, locale: str, dark: bool) -> str:
        """The page loaded into the view. It must define window.__office with open(docId, fileName,
        readonly), save(requestId, format), setReadonly(flag), and report through the channel:
        POST {prefix}evt/{token} with JSON {type: ready|opened|dirty|saved|error, ...} and
        POST {prefix}save/{token}/{requestId} with the saved file's bytes.

        Optional (a component that cannot do one of them leaves it out; the view then answers
        "nothing" and Broccoli simply does not offer that feature):
          selection()        -> {kind: docx|xlsx|pptx, text, page (1-based page or slide), sheet,
                                 range ('B2:C5'), cell ('B2'), drawings (count of selected pictures
                                 and shapes)} — what the user has selected right now
          setMenu(items)     Broccoli's own entries for the component's right-click menu, added to
                             the component's entries (never replacing them). items: [{id, text}] or
                             {separator: true}. A click is reported as {type: 'menu', item: id,
                             selection: selection()}.
          goTo(target)       -> bool. target: {slide: n} | {sheet, cell} | {text, occurrence}
          runScript(id, source)  run `source` (the body of a function, in the component's own
                             scripting language — see script_guide) on the open document and
                             report {type: 'script', id, ok, value | error, changed}"""
        raise NotImplementedError

    def locale_for(self, language: str) -> str:
        return 'en'

    def startup_scripts(self) -> list:
        """JavaScript run in every frame of the view before the component's own code."""
        return []

    def script_guide(self) -> str:
        """For a model that writes scripts for runScript: what the scripting language is and what
        a script may do. '' = this component runs no scripts."""
        return ''

    def script_start(self, kind: str) -> str:
        """…and where to start in a 'docx' / 'xlsx' / 'pptx' document (entry points, units)."""
        return ''


class RanutsDocumentAdapter(OfficeEditorAdapter):
    """ranuts/document: the ONLYOFFICE web editors + the x2t converter compiled to WebAssembly,
    all static files. Embedding contract (its docs/embed-api.md): the editor page runs in an
    iframe with ?embed=1 and talks to its parent with window.postMessage {id, type, payload}:
    document:open-buffer / document:save / document:set-readonly in, document:ready / opened /
    saved / dirty-changed / error out."""
    name = 'ranuts-document'
    save_formats = {'.docx': 'DOCX', '.xlsx': 'XLSX', '.pptx': 'PPTX'}
    _LOCALES = {'zh': 'zh-CN', 'ja': 'ja', 'ko': 'ko', 'de': 'de', 'es': 'es'}

    def response_headers(self, path: str) -> dict:
        # the same rules as the component's own server file (sws.toml in its container image)
        headers = {
            'Cache-Control': 'no-cache',
            'Cross-Origin-Opener-Policy': 'same-origin',
            'Cross-Origin-Embedder-Policy': 'require-corp',
        }
        if path == '/sdkjs/common/wasm/x2t/x2t.wasm.br':
            # the image stores gzip bytes under the .br name (its build re-encodes for plain http)
            headers['Content-Encoding'] = 'gzip'
        return headers

    def content_type(self, path: str):
        if path.startswith('/fonts/') and '.' not in posixpath.basename(path):
            return 'font/ttf'
        if path.endswith('.mjs'):
            return 'text/javascript; charset=utf-8'
        if path.endswith('.wasm.br'):
            return 'application/octet-stream'
        return None

    def locale_for(self, language: str) -> str:
        code = str(language or '').strip().lower().replace('_', '-')
        return self._LOCALES.get(code.split('-')[0], 'en')

    def startup_scripts(self) -> list:
        # The component keeps its files in a service worker cache so that a web browser can use it
        # without a network. Here its files are on this Mac already, and in this view the worker
        # never takes control: the component then waits 15 seconds for it before it opens a
        # document (measured 2026-11-11: 15.3 s with the worker, 0.3 s without). Without
        # navigator.serviceWorker it skips that step, as it does in any browser that has none.
        return ['try{delete Navigator.prototype.serviceWorker;}catch(e){}']

    def script_start(self, kind: str) -> str:
        return {
            'docx': ('var doc = Api.GetDocument();  // ApiDocument\n'
                     'doc.GetElementsCount(), doc.GetElement(i) (ApiParagraph / ApiTable), doc.Push(element), '
                     'doc.GetFinalSection() (page size, margins, header / footer), doc.GetAllDrawingObjects(), '
                     'Api.CreateParagraph(), Api.CreateRun(), Api.CreateTable(cols, rows), '
                     'Api.CreateImage(src, widthEmu, heightEmu), paragraph.AddDrawing(drawing).\n'
                     'Units: drawings in EMU (36000 = 1 mm), spacing / indents / margins in twips (1440 = 1 inch), '
                     'font size in half-points.'),
            'xlsx': ('var sheet = Api.GetActiveSheet();  // ApiWorksheet; also Api.GetSheet("name"), Api.GetSheets(), Api.AddSheet("name")\n'
                     'sheet.GetRange("A1:B5") (ApiRange): SetValue, GetValue, SetBold, SetFontColor, SetFillColor, '
                     'SetNumberFormat, SetAlignHorizontal, SetBorders, Merge, SetColumnWidth, AutoFit; '
                     'sheet.AddChart(dataRef, bRow, type, style, widthEmu, heightEmu, fromCol, colOffset, fromRow, rowOffset), '
                     'sheet.AddImage(src, widthEmu, heightEmu, fromCol, colOffset, fromRow, rowOffset), '
                     'sheet.SetName, sheet.FormatAsTable, Api.CreateColorFromRGB(r, g, b).'),
            'pptx': ('var deck = Api.GetPresentation();  // ApiPresentation\n'
                     'deck.GetSlidesCount(), deck.GetSlideByIndex(i) (0-based, ApiSlide), deck.GetCurrentSlide(), '
                     'deck.AddSlide(Api.CreateSlide()), slide.GetAllDrawings() / GetAllShapes() / GetAllImages() / '
                     'GetAllCharts() (in the order of the layout list), slide.AddObject(drawing), slide.RemoveAllObjects(), '
                     'slide.SetBackground(fill), slide.Delete(), slide.MoveTo(pos); drawing.SetPosition(xEmu, yEmu), '
                     'drawing.SetSize(wEmu, hEmu), drawing.Delete(); shape.GetDocContent() (text: GetElement(i) is an '
                     'ApiParagraph); Api.CreateShape(type, wEmu, hEmu, fill, stroke), Api.CreateImage(src, wEmu, hEmu), '
                     'Api.CreateChart(...), Api.CreateTable(cols, rows); fills: Api.CreateSolidFill(Api.CreateRGBColor(r, g, b)), '
                     'Api.CreateBlipFill(src, "stretch" | "tile"), Api.CreateLinearGradientFill(...), Api.CreateNoFill(); '
                     'Api.CreateStroke(widthEmu, fill).\nUnits: EMU (36000 = 1 mm; a 16:9 slide is 12192000 x 6858000).'),
        }.get(kind, '')

    def script_guide(self) -> str:
        return ('The script is JavaScript for the ONLYOFFICE "Office JavaScript API" (the API of ONLYOFFICE macros, '
                'plugins and Document Builder%s). It is the BODY of a function: the '
                'global object `Api` is given, statements run synchronously, and `return value;` hands a value back '
                '(a string, a number, or anything JSON can hold). No DOM, no network, no files.\n'
                'Not sure a method exists in this version? Ask the document: `return Methods(Api);` or '
                '`return Methods(Api.GetPresentation().GetSlideByIndex(0));` lists the method names of any API object. '
                'A script that only reads (returns something, changes nothing) needs no approval.'
                % ((', version ' + self.editors_version) if self.editors_version else '',))

    editors_version = ''

    def host_page(self, token: str, locale: str, dark: bool) -> str:
        config = json.dumps({'token': token, 'prefix': _CHANNEL_PREFIX, 'locale': locale,
                             'theme': 'dark' if dark else 'light'})
        return _RANUTS_HOST_PAGE.replace('__CONFIG__', config)


_RANUTS_HOST_PAGE = r'''<!doctype html>
<html><head><meta charset="utf-8"><title>Office</title>
<style>html,body{margin:0;height:100%;overflow:hidden;background:transparent}
iframe{position:absolute;inset:0;width:100%;height:100%;border:0}</style></head>
<body><script>
(function () {
  const C = __CONFIG__;
  const origin = window.location.origin;
  try { localStorage.setItem('ran-theme', C.theme); } catch (e) {}
  const frame = document.createElement('iframe');
  frame.allow = 'clipboard-read; clipboard-write';
  frame.src = '/editor.html?embed=1&locale=' + encodeURIComponent(C.locale) +
              '&embedOrigin=' + encodeURIComponent(origin);
  document.body.appendChild(frame);
  let ready = false, seq = 0, probe = null;

  function report(type, data) {
    const body = JSON.stringify(Object.assign({type: type}, data || {}));
    fetch(C.prefix + 'evt/' + C.token, {method: 'POST', body: body, keepalive: true}).catch(function () {});
  }
  function post(type, payload, id) {
    frame.contentWindow.postMessage({id: id || ('b' + (++seq)), type: type, payload: payload || {}}, origin);
  }
  function markReady() {
    if (ready) return;
    ready = true;
    if (probe) { clearInterval(probe); probe = null; }
    report('ready');
  }
  window.addEventListener('message', async function (event) {
    if (event.origin !== origin || event.source !== frame.contentWindow) return;
    const d = event.data || {};
    if (typeof d.type !== 'string' || d.type.indexOf('document:') !== 0) return;
    const p = d.payload || {};
    if (d.type === 'document:ready' || d.type === 'document:state') { markReady(); return; }
    if (d.type === 'document:opened') { markReady(); hookSoon(); report('opened', {id: d.id || ''}); return; }
    if (d.type === 'document:dirty-changed') { report('dirty', {dirty: !!p.dirty}); return; }
    if (d.type === 'document:error') { report('error', {id: d.id || '', message: String(p.message || '')}); return; }
    if (d.type === 'document:saved') {
      try {
        const response = await fetch(C.prefix + 'save/' + C.token + '/' + encodeURIComponent(d.id || ''),
                                     {method: 'POST', body: p.file});
        if (!response.ok) throw new Error('HTTP ' + response.status);
        report('saved', {id: d.id || '', size: p.file ? p.file.size : 0});
      } catch (e) {
        report('error', {id: d.id || '', message: 'could not hand over the saved file: ' + e});
      }
    }
  });
  // ── selection, right-click entries, go to a place ──────────────────────────────────────────
  // The editors (ONLYOFFICE) run in a frame of the component's page, on this same origin. Their
  // programming interface is the object `editor` (documents, slides) or `Asc.editor` (sheets).
  const GUID = 'asc.{broccoli-0000-0000-0000-000000000001}';
  let menuItems = [];
  function editorApi() {
    try {
      const outer = frame.contentWindow;
      for (let i = 0; i < outer.frames.length; i++) {
        try {
          const w = outer.frames[i];
          const a = w.editor || (w.Asc && w.Asc.editor);
          if (a && typeof a.asc_GetSelectedText === 'function') return {w: w, a: a};
        } catch (e) {}
      }
    } catch (e) {}
    return null;
  }
  function kindOf(w) { return w.SSE ? 'xlsx' : (w.PE ? 'pptx' : 'docx'); }
  function selection() {
    const found = editorApi();
    if (!found) return {};
    const a = found.a, out = {kind: kindOf(found.w)};
    try { out.text = String(a.asc_GetSelectedText() || '').slice(0, 20000); } catch (e) { out.text = ''; }
    try { out.drawings = Number(a.asc_getSelectedDrawingObjectsCount ? a.asc_getSelectedDrawingObjectsCount() : 0) || 0; } catch (e) {}
    try {
      if (out.kind === 'xlsx') {
        out.sheet = String(a.asc_getWorksheetName(a.asc_getActiveWorksheetIndex()));
        out.range = String(a.asc_getActiveRangeStr(1, false, true) || '').replace(/\$/g, '');
        out.cell = String(a.asc_getActiveRangeStr(1, true, true) || '').replace(/\$/g, '');
      } else {
        out.page = Number(a.getCurrentPage()) + 1;
      }
    } catch (e) {}
    return out;
  }
  function hook() {
    // Add Broccoli's entries through the component's own "a plugin adds entries to the
    // right-click menu" path: when its menu opens it asks the editor which plugins want to add
    // something; the answer is given here, and a click on one of ours is reported to Broccoli.
    const found = editorApi();
    if (!found) return false;
    const a = found.a;
    if (a.__broccoliMenu) return true;
    if (typeof a.onPluginContextMenuShow !== 'function' || typeof a.onPluginAddContextMenuItem !== 'function' ||
        typeof a.onPluginContextMenuItemClick !== 'function') return true;      // this component has no such path
    const show = a.onPluginContextMenuShow, click = a.onPluginContextMenuItemClick;
    a.onPluginContextMenuShow = function () {
      const result = show.apply(this, arguments);
      if (!menuItems.length) return result;
      try {
        if (!this.contextMenuPlugins) {
          this.contextMenuPlugins = {items: {}, itemsCount: 0, processItems: {}, processItemsCount: 0};
        }
        this.onPluginAddContextMenuItem({guid: GUID, items: menuItems});
      } catch (e) {}
      return false;
    };
    a.onPluginContextMenuItemClick = function (guid, id) {
      if (guid === GUID) { report('menu', {item: String(id), selection: selection()}); return; }
      return click.apply(this, arguments);
    };
    a.__broccoliMenu = true;
    return true;
  }
  function hookSoon() {
    let tries = 0;
    const timer = setInterval(function () { if (hook() || ++tries > 100) clearInterval(timer); }, 200);
  }
  function goTo(target) {
    const found = editorApi();
    if (!found || !target) return false;
    const a = found.a, kind = kindOf(found.w);
    try {
      if (kind === 'pptx' && target.slide) { a.goToPage(Number(target.slide) - 1); return true; }
      if (kind === 'xlsx' && target.cell) {
        const sheet = String(target.sheet || '');
        const name = sheet ? "'" + sheet.replace(/'/g, "''") + "'!" : '';
        a.asc_findCell(name + String(target.cell));
        return true;
      }
      if (kind === 'docx' && target.text) {
        const doc = a.WordControl && a.WordControl.m_oLogicDocument;
        if (doc && doc.MoveCursorToStartOfDocument) doc.MoveCursorToStartOfDocument();
        let ok = false;
        for (let n = Math.max(1, Number(target.occurrence) || 1); n > 0; n--) {
          ok = !!a.pluginMethod_SearchNext({searchString: String(target.text), matchCase: true}, true);
          if (!ok) break;
        }
        return ok;
      }
    } catch (e) {}
    return false;
  }
  // Run a script on the open document the way the component runs a macro or a plugin command:
  // its "before a script" step, its guarded evaluation (the script gets `Api` and nothing of the
  // page), its "after a script" step (recalculate, redraw, wait for pictures to load).
  function runScript(id, source) {
    function answer(data) { report('script', Object.assign({id: String(id)}, data)); }
    const found = editorApi();
    if (!found) { answer({ok: false, error: 'the document is not open'}); return; }
    const a = found.a, w = found.w;
    if (!w.AscCommon || typeof w.AscCommon.safePluginEval !== 'function' ||
        typeof a._beforeEvalCommand !== 'function' || typeof a._afterEvalCommand !== 'function') {
      answer({ok: false, error: 'this editing component cannot run scripts'}); return;
    }
    try { new w.Function(String(source)); }
    catch (e) { answer({ok: false, error: 'SyntaxError: ' + (e && e.message ? e.message : e)}); return; }
    const history = w.AscCommon.History;
    const mark = history ? [history.Index, history.Points ? history.Points.length : 0] : null;
    const code = '(function () {\n' +
      'var Methods = function (o) { var names = {}; for (var p = o; p && p !== Object.prototype; p = Object.getPrototypeOf(p)) {' +
      ' Object.getOwnPropertyNames(p).forEach(function (k) { try { if (/^[A-Z]/.test(k) && typeof o[k] === "function") names[k] = 1; } catch (e) {} }); }' +
      ' return Object.keys(names).sort().join(", "); };\n' +
      'var __text = function (v) { if (v === undefined || v === null) return ""; if (typeof v === "string") return v;' +
      ' try { var j = JSON.stringify(v); if (j !== undefined) return j; } catch (e) {} return String(v); };\n' +
      'try { return JSON.stringify({ok: true, value: __text((function () {\n' + String(source) + '\n})()).slice(0, 60000)}); }\n' +
      'catch (e) { return JSON.stringify({ok: false, error: String(e && e.message ? (e.name || "Error") + ": " + e.message : e)}); }\n' +
      '})()';
    let done = false;
    function finish(raw) {
      if (done) return;
      done = true;
      let result = null;
      try { result = JSON.parse(raw); } catch (e) {}
      if (!result || typeof result !== 'object') result = {ok: false, error: 'the script could not be run'};
      let changed = true;
      try { if (mark && history) changed = history.Index !== mark[0] || (history.Points ? history.Points.length : 0) !== mark[1]; } catch (e) {}
      result.changed = !!changed;
      answer(result);
    }
    try {
      a._beforeEvalCommand();
      const raw = w.AscCommon.safePluginEval(code);
      a._afterEvalCommand(function () {
        a.evalCommand = false;
        try { if (a.onEndBuilderScript) a.onEndBuilderScript(function () {}); } catch (e) {}
        finish(raw);
      });
      setTimeout(function () { finish(raw); }, 20000);
    } catch (e) {
      finish(JSON.stringify({ok: false, error: String(e)}));
    }
  }
  frame.addEventListener('load', function () {
    // the component announces itself once; ask for its state until it answers, in case that
    // announcement was sent before this page listened
    probe = setInterval(function () { if (!ready) post('document:get-state'); }, 400);
  });
  window.__office = {
    open: async function (docId, fileName, readonly) {
      try {
        const response = await fetch(C.prefix + 'doc/' + C.token + '/' + encodeURIComponent(docId));
        if (!response.ok) throw new Error('HTTP ' + response.status);
        const buffer = await response.arrayBuffer();
        post('document:open-buffer', {fileName: fileName, buffer: buffer, readonly: !!readonly}, 'open:' + docId);
      } catch (e) {
        report('error', {id: 'open:' + docId, message: 'could not read the document: ' + e});
      }
    },
    save: function (requestId, format) { post('document:save', {targetExt: format}, 'save:' + requestId); },
    setReadonly: function (flag) { post('document:set-readonly', {readonly: !!flag}); },
    selection: selection,
    setMenu: function (items) { menuItems = Array.isArray(items) ? items : []; hook(); },
    goTo: goTo,
    runScript: runScript,
  };
})();
</script></body></html>
'''

ADAPTERS = {RanutsDocumentAdapter.name: RanutsDocumentAdapter}


# ── the component on disk ────────────────────────────────────────────────────────────────────
class OfficeComponent:
    """A component folder: <folder>/site (its files, untouched) + <folder>/manifest.json."""

    def __init__(self, folder: str, manifest: dict, adapter: OfficeEditorAdapter):
        self.folder = folder
        self.site_dir = os.path.join(folder, 'site')
        self.manifest = manifest
        self.adapter = adapter
        self.fixups = [f for f in (manifest.get('fixups') or []) if isinstance(f, dict)]

    @property
    def version(self) -> str:
        return str(self.manifest.get('version', '') or '')


def load_component(folder: str, site_dir: str = ''):
    """The component in `folder`, or (None, reason) when it is absent or not usable.
    site_dir: another copy of the component's files (the updater tests a download with it)."""
    manifest_path = os.path.join(folder, 'manifest.json')
    try:
        with open(manifest_path, encoding='utf-8') as handle:
            manifest = json.load(handle)
    except (OSError, ValueError) as exc:
        return None, f'no usable manifest.json ({exc})'
    if not isinstance(manifest, dict):
        return None, 'manifest.json is not an object'
    adapter_class = ADAPTERS.get(str(manifest.get('adapter', '') or ''))
    if adapter_class is None:
        return None, f'no adapter named {manifest.get("adapter")!r}'
    component = OfficeComponent(folder, manifest, adapter_class())
    if site_dir:
        component.site_dir = site_dir
    component.adapter.editors_version = str(manifest.get('editors_version', '') or '')
    entry = str(manifest.get('entry', '') or 'editor.html')
    if not os.path.isfile(os.path.join(component.site_dir, entry)):
        return None, f'the component files are missing ({entry})'
    return component, ''


# ── the local file server ────────────────────────────────────────────────────────────────────
class _Session:
    def __init__(self, on_event, on_saved):
        self.on_event = on_event      # (dict) -> None, called on a server thread
        self.on_saved = on_saved      # (request_id, bytes) -> None, called on a server thread
        self.documents = {}           # doc id -> bytes, handed out once
        self.page = ''


class _ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address):
        # the page dropping a connection (a reload, a closed view) is not an error worth a trace
        if isinstance(sys.exc_info()[1], (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)):
            return
        super().handle_error(request, client_address)


class OfficeSiteServer:
    """Serves one component's files on 127.0.0.1 and carries each view's private channel.
    The component's files are public; a document only travels under the view's random token."""

    def __init__(self, component: OfficeComponent):
        self.component = component
        self._sessions = {}
        self._lock = threading.Lock()
        self._fixup_cache = {}
        self.fixup_report = {}        # path -> 'applied' | 'not needed any more'
        self._httpd = _ThreadingServer(('127.0.0.1', 0), self._make_handler())
        self.port = self._httpd.server_address[1]
        self.origin = f'http://127.0.0.1:{self.port}'
        self._thread = threading.Thread(target=self._httpd.serve_forever, name='office-site-server',
                                        daemon=True)
        self._thread.start()

    def stop(self) -> None:
        try:
            self._httpd.shutdown()
            self._httpd.server_close()
        except Exception:
            pass

    # sessions (one per view)
    def open_session(self, on_event, on_saved, locale: str = 'en', dark: bool = False) -> str:
        token = secrets.token_hex(16)
        session = _Session(on_event, on_saved)
        session.page = self.component.adapter.host_page(token, locale, dark)
        with self._lock:
            self._sessions[token] = session
        return token

    def close_session(self, token: str) -> None:
        with self._lock:
            self._sessions.pop(token, None)

    def host_url(self, token: str) -> str:
        return f'{self.origin}{_CHANNEL_PREFIX}host/{token}'

    def offer_document(self, token: str, data: bytes) -> str:
        doc_id = secrets.token_hex(8)
        with self._lock:
            session = self._sessions.get(token)
            if session is None:
                return ''
            session.documents.clear()     # one document per view at a time
            session.documents[doc_id] = bytes(data)
        return doc_id

    def _session(self, token: str):
        with self._lock:
            return self._sessions.get(token)

    # the component's files, with the manifest's corrections applied while serving
    def _fixed_bytes(self, rel_path: str, full_path: str):
        """The file's bytes when a manifest fixup applies to it, else None (serve it as it is).
        A fixup is {path, find, replace, note}: it only applies while `find` is still in the file,
        so it switches itself off once the component's authors correct the file."""
        wanted = [f for f in self.component.fixups if str(f.get('path', '')) == rel_path]
        if not wanted:
            return None
        try:
            stamp = os.stat(full_path)
            key = (stamp.st_mtime_ns, stamp.st_size)
            cached = self._fixup_cache.get(rel_path)
            if cached and cached[0] == key:
                return cached[1]
            with open(full_path, 'rb') as handle:
                data = handle.read()
        except OSError:
            return None
        changed = False
        for fixup in wanted:
            find = str(fixup.get('find', '')).encode('utf-8')
            replace = str(fixup.get('replace', '')).encode('utf-8')
            if find and find in data:
                data = data.replace(find, replace)
                changed = True
        self.fixup_report[rel_path] = 'applied' if changed else 'not needed any more'
        result = data if changed else None
        self._fixup_cache[rel_path] = (key, result)
        return result

    def _make_handler(self):
        server = self
        adapter = self.component.adapter
        site_dir = os.path.realpath(self.component.site_dir)

        class Handler(http.server.SimpleHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'

            def log_message(self, *args):
                pass

            def _host_ok(self) -> bool:
                # only this machine, by address: a page elsewhere cannot reach it through a name
                return self.headers.get('Host', '') in (f'127.0.0.1:{server.port}',)

            def _plain(self, code: int, body: bytes = b'', content_type: str = 'text/plain; charset=utf-8',
                       extra: dict = None):
                self.send_response(code)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Cache-Control', 'no-store')
                for key, value in (extra or {}).items():
                    self.send_header(key, value)
                http.server.BaseHTTPRequestHandler.end_headers(self)
                if body and self.command != 'HEAD':
                    self.wfile.write(body)

            def _clean_path(self) -> str:
                path = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
                return posixpath.normpath(path) if path != '/' else '/'

            def translate_path(self, path):
                clean = self._clean_path()
                if clean in ('/', '.'):
                    clean = '/index.html'
                full = os.path.realpath(os.path.join(site_dir, clean.lstrip('/')))
                if full != site_dir and not full.startswith(site_dir + os.sep):
                    return os.path.join(site_dir, '__outside__')
                return full

            def guess_type(self, path):
                rel = '/' + os.path.relpath(path, site_dir).replace(os.sep, '/')
                return adapter.content_type(rel) or mimetypes.guess_type(path)[0] or 'application/octet-stream'

            def end_headers(self):
                for key, value in adapter.response_headers(self._clean_path()).items():
                    self.send_header(key, value)
                super().end_headers()

            def list_directory(self, path):
                self._plain(404, b'not found')
                return None

            def do_GET(self):
                if not self._host_ok():
                    return self._plain(403, b'forbidden')
                clean = self._clean_path()
                if clean.startswith(_CHANNEL_PREFIX):
                    return self._channel_get(clean[len(_CHANNEL_PREFIX):])
                full = self.translate_path(self.path)
                if os.path.isfile(full):
                    fixed = server._fixed_bytes(clean, full)
                    if fixed is not None:
                        return self._plain(200, fixed, self.guess_type(full), adapter.response_headers(clean))
                return super().do_GET()

            def do_HEAD(self):
                if not self._host_ok():
                    return self._plain(403)
                return super().do_HEAD()

            def _channel_get(self, rest: str):
                parts = rest.split('/')
                session = server._session(parts[1]) if len(parts) >= 2 else None
                if session is None:
                    return self._plain(404, b'not found')
                if parts[0] == 'host' and len(parts) == 2:
                    return self._plain(200, session.page.encode('utf-8'), 'text/html; charset=utf-8',
                                       adapter.response_headers('/'))
                if parts[0] == 'doc' and len(parts) == 3:
                    with server._lock:
                        data = session.documents.pop(parts[2], None)
                    if data is None:
                        return self._plain(404, b'not found')
                    return self._plain(200, data, 'application/octet-stream', adapter.response_headers('/'))
                return self._plain(404, b'not found')

            def do_POST(self):
                if not self._host_ok():
                    return self._plain(403, b'forbidden')
                clean = self._clean_path()
                # a page of another site must not be able to post here
                origin = self.headers.get('Origin', '')
                if not clean.startswith(_CHANNEL_PREFIX) or (origin and origin != server.origin):
                    return self._plain(404, b'not found')
                parts = clean[len(_CHANNEL_PREFIX):].split('/')
                session = server._session(parts[1]) if len(parts) >= 2 else None
                try:
                    length = int(self.headers.get('Content-Length', '') or -1)
                except ValueError:
                    length = -1
                if session is None or length < 0 or length > _MAX_SAVE_BYTES:
                    return self._plain(404, b'not found')
                body = self.rfile.read(length) if length else b''
                try:
                    if parts[0] == 'evt' and len(parts) == 2:
                        event = json.loads(body.decode('utf-8'))
                        if isinstance(event, dict):
                            session.on_event(event)
                    elif parts[0] == 'save' and len(parts) == 3:
                        session.on_saved(parts[2], body)
                    else:
                        return self._plain(404, b'not found')
                except Exception:
                    return self._plain(400, b'bad request')
                return self._plain(204)

        return Handler


_SERVERS = {}
_SERVERS_LOCK = threading.Lock()


def server_for(component: OfficeComponent) -> OfficeSiteServer:
    """One server per component folder for the life of the program (started on first use)."""
    key = os.path.realpath(component.site_dir)
    with _SERVERS_LOCK:
        server = _SERVERS.get(key)
        if server is None:
            server = OfficeSiteServer(component)
            _SERVERS[key] = server
        return server


def stop_all_servers() -> None:
    with _SERVERS_LOCK:
        servers = list(_SERVERS.values())
        _SERVERS.clear()
    for server in servers:
        server.stop()


# ── the Qt view ──────────────────────────────────────────────────────────────────────────────
_QT = {}


def _json_object(value) -> dict:
    try:
        data = json.loads(value) if isinstance(value, str) else value
    except ValueError:
        data = None
    return data if isinstance(data, dict) else {}


def _qt():
    """The Qt classes, built on first use (so the server part works without Qt)."""
    if _QT:
        return _QT
    from PyQt6.QtCore import QObject, QTimer, QUrl, Qt, pyqtSignal
    from PyQt6.QtWidgets import QVBoxLayout, QWidget
    from PyQt6.QtWebEngineCore import (QWebEnginePage, QWebEngineProfile, QWebEngineScript,
                                       QWebEngineSettings, QWebEngineUrlRequestInterceptor)
    from PyQt6.QtWebEngineWidgets import QWebEngineView

    class _LocalOnly(QWebEngineUrlRequestInterceptor):
        """The component may only talk to Broccoli's own server: no network, no statistics."""

        def __init__(self, parent=None):
            super().__init__(parent)
            self.blocked = []

        def interceptRequest(self, info):
            url = info.requestUrl()
            if url.scheme() in ('http', 'https', 'ws', 'wss') and url.host() != '127.0.0.1':
                if len(self.blocked) < 200:
                    self.blocked.append(url.toString()[:200])
                info.block(True)

    class _Page(QWebEnginePage):
        def __init__(self, profile, origin, parent=None):
            super().__init__(profile, parent)
            self._origin = origin
            self.console_errors = []

        def acceptNavigationRequest(self, url, kind, is_main_frame):
            # the view shows the component and nothing else
            return url.toString().startswith(self._origin + '/') or url.scheme() in ('about', 'blob', 'data')

        def createWindow(self, kind):
            return None

        def javaScriptConsoleMessage(self, level, message, line, source):
            if level == QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
                if len(self.console_errors) < 100:
                    self.console_errors.append(str(message)[:300])

    class OfficeEditorView(QWidget):
        """Shows one office document in the bundled component and lets the user edit it.

        open_bytes(file_name, data)  show this document (replaces the one shown)
        save()                       ask for the edited file; `saved(bytes)` or `saveFailed(text)` follows
        dirtyChanged(bool)           the user has / has no unsaved changes
        set_readonly(flag)
        """
        ready = pyqtSignal()
        opened = pyqtSignal()
        dirtyChanged = pyqtSignal(bool)
        saved = pyqtSignal(bytes)
        saveFailed = pyqtSignal(str)
        failed = pyqtSignal(str)
        menuAction = pyqtSignal(str, dict)   # one of Broccoli's right-click entries, the selection
        _event = pyqtSignal(dict)            # server thread -> GUI thread
        _saved_bytes = pyqtSignal(str, bytes)

        SAVE_TIMEOUT_MS = 120000
        OPEN_TIMEOUT_MS = 180000

        def __init__(self, component, language='en', dark=False, parent=None):
            super().__init__(parent)
            self.component = component
            self._server = server_for(component)
            self._is_ready = False
            self._dirty = False
            self._file_name = ''
            self._pending_open = None        # (file_name, data, readonly) until the component is ready
            self._open_id = ''
            self._save_id = ''
            self._save_seq = 0
            self._save_data = {}
            self._readonly = False
            self._menu_items = []
            self._script_seq = 0
            self._script_waiting = {}        # id -> (callback, timer)
            self._event.connect(self._on_event, Qt.ConnectionType.QueuedConnection)
            self._saved_bytes.connect(self._on_saved_bytes, Qt.ConnectionType.QueuedConnection)
            self._token = self._server.open_session(
                self._event.emit, self._saved_bytes.emit,
                locale=component.adapter.locale_for(language), dark=bool(dark))

            # its own in-memory profile: nothing of the component outlives the program, so an
            # updated component is never mixed with files cached from the previous one
            self._profile = QWebEngineProfile()      # no parent: it must outlive its page (see shutdown)
            self.interceptor = _LocalOnly(self._profile)
            self._profile.setUrlRequestInterceptor(self.interceptor)
            self._profile.downloadRequested.connect(lambda item: item.cancel())
            for index, source in enumerate(component.adapter.startup_scripts()):
                script = QWebEngineScript()
                script.setName('office-startup-%d' % index)
                script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
                script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
                script.setRunsOnSubFrames(True)
                script.setSourceCode(source)
                self._profile.scripts().insert(script)
            self.page = _Page(self._profile, self._server.origin, None)
            settings = self.page.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanPaste, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            self.web = QWebEngineView(self)
            self.web.setPage(self.page)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.web)
            self._open_timer = QTimer(self)
            self._open_timer.setSingleShot(True)
            self._open_timer.timeout.connect(self._on_open_timeout)
            self._save_timer = QTimer(self)
            self._save_timer.setSingleShot(True)
            self._save_timer.timeout.connect(self._on_save_timeout)
            self.page.load(QUrl(self._server.host_url(self._token)))

        # state
        def is_ready(self) -> bool:
            return self._is_ready

        def is_dirty(self) -> bool:
            return self._dirty

        def is_busy(self) -> bool:
            return bool(self._open_id or self._save_id or self._pending_open)

        def file_name(self) -> str:
            return self._file_name

        # actions
        def open_bytes(self, file_name: str, data: bytes, readonly: bool = False) -> None:
            self._file_name = str(file_name or '')
            self._readonly = bool(readonly)
            self._set_dirty(False)
            if not self._is_ready:
                self._pending_open = (self._file_name, bytes(data), self._readonly)
                self._open_timer.start(self.OPEN_TIMEOUT_MS)
                return
            self._pending_open = None
            if self._token is None:
                return
            doc_id = self._server.offer_document(self._token, data)
            self._open_id = 'open:' + doc_id
            self._open_timer.start(self.OPEN_TIMEOUT_MS)
            self.page.runJavaScript('window.__office.open(%s, %s, %s)' % (
                json.dumps(doc_id), json.dumps(self._file_name), 'true' if self._readonly else 'false'))

        def save(self) -> bool:
            """Ask the component for the edited file. False when it cannot be asked right now."""
            if (self._token is None or not self._is_ready or self._open_id or self._save_id
                    or not self._file_name):
                return False
            extension = os.path.splitext(self._file_name)[1].lower()
            target = self.component.adapter.save_formats.get(extension)
            if not target:
                return False
            self._save_seq += 1
            request = 's%d' % self._save_seq
            self._save_id = 'save:' + request
            self._save_timer.start(self.SAVE_TIMEOUT_MS)
            self.page.runJavaScript('window.__office.save(%s, %s)' % (json.dumps(request), json.dumps(target)))
            return True

        def set_readonly(self, flag: bool) -> None:
            self._readonly = bool(flag)
            if self._is_ready and self._token is not None:
                self.page.runJavaScript('window.__office.setReadonly(%s)' % ('true' if flag else 'false'))

        def set_menu_items(self, items) -> None:
            """Broccoli's entries for the component's right-click menu: [{'id', 'text'}] and
            {'separator': True}. They are added to the component's own entries."""
            self._menu_items = [dict(item) for item in (items or []) if isinstance(item, dict)]
            self._push_menu()

        def _push_menu(self) -> None:
            if self._is_ready and self._token is not None:
                self.page.runJavaScript(
                    'window.__office.setMenu && window.__office.setMenu(%s)' % json.dumps(self._menu_items))

        def fetch_selection(self, callback) -> None:
            """callback(dict): what is selected in the document now ({} when the component cannot tell)."""
            if not self._is_ready or self._token is None:
                callback({})
                return
            self.page.runJavaScript(
                'JSON.stringify(window.__office.selection ? window.__office.selection() : {})',
                lambda value: callback(_json_object(value)))

        def go_to(self, target: dict, callback=None) -> None:
            """Show a place of the document: {'slide': n} | {'sheet', 'cell'} | {'text', 'occurrence'}."""
            if not self._is_ready or self._token is None:
                if callback:
                    callback(False)
                return
            self.page.runJavaScript(
                '!!(window.__office.goTo && window.__office.goTo(%s))' % json.dumps(dict(target or {})),
                (lambda value: callback(bool(value))) if callback else (lambda value: None))

        def run_script(self, source: str, callback, timeout_ms: int = 40000) -> None:
            """Run `source` (see the adapter's script_guide) on the open document.
            callback({'ok': bool, 'value': str, 'error': str, 'changed': bool}) — changed: the
            script changed the document (which is now unsaved in this view, the file untouched)."""
            if not self._is_ready or self._token is None or self._open_id:
                callback({'ok': False, 'error': 'the document is not open', 'changed': False})
                return
            self._script_seq += 1
            ident = 'x%d' % self._script_seq
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda i=ident: self._script_done(
                i, {'ok': False, 'error': 'the script did not finish in time', 'changed': True}))
            self._script_waiting[ident] = (callback, timer)
            timer.start(int(timeout_ms))
            self.page.runJavaScript(
                'window.__office.runScript ? window.__office.runScript(%s, %s) : null'
                % (json.dumps(ident), json.dumps(str(source or ''))),
                lambda _value, i=ident: None)

        def _script_done(self, ident: str, result: dict) -> None:
            waiting = self._script_waiting.pop(ident, None)
            if waiting is None:
                return
            callback, timer = waiting
            timer.stop()
            timer.deleteLater()
            callback({'ok': bool(result.get('ok')), 'value': str(result.get('value') or ''),
                      'error': str(result.get('error') or ''), 'changed': bool(result.get('changed'))})

        def shutdown(self) -> None:
            """Call before the view is deleted. The page has to go before its profile, or Qt crashes."""
            if self._token is None:
                return
            self._server.close_session(self._token)
            self._token = None
            self._open_timer.stop()
            self._save_timer.stop()
            page, profile = self.page, self._profile
            try:
                self.web.setPage(None)
            except Exception:
                pass
            page.deleteLater()
            profile.deleteLater()            # queued after the page's deletion

        # events from the component
        def _set_dirty(self, flag: bool) -> None:
            flag = bool(flag)
            if flag != self._dirty:
                self._dirty = flag
                self.dirtyChanged.emit(flag)

        def _on_event(self, event: dict) -> None:
            kind = str(event.get('type', ''))
            ident = str(event.get('id', ''))
            if kind == 'ready':
                if not self._is_ready:
                    self._is_ready = True
                    self.ready.emit()
                    self._push_menu()
                    if self._pending_open:
                        name, data, readonly = self._pending_open
                        self.open_bytes(name, data, readonly)
            elif kind == 'opened':
                if not self._open_id or ident == self._open_id:
                    self._open_id = ''
                    self._open_timer.stop()
                    self._set_dirty(False)
                    self.opened.emit()
            elif kind == 'dirty':
                if not self._open_id:
                    self._set_dirty(bool(event.get('dirty')))
            elif kind == 'saved':
                if ident == self._save_id:
                    data = self._save_data.pop(ident, None)
                    self._save_id = ''
                    self._save_timer.stop()
                    if data:
                        self._set_dirty(False)
                        self.saved.emit(data)
                    else:
                        self.saveFailed.emit('the component returned an empty file')
            elif kind == 'script':
                self._script_done(ident, event)
            elif kind == 'menu':
                selection = event.get('selection')
                self.menuAction.emit(str(event.get('item', '')), selection if isinstance(selection, dict) else {})
            elif kind == 'error':
                message = str(event.get('message', '') or 'unknown error')
                if self._save_id and ident == self._save_id:
                    self._save_id = ''
                    self._save_timer.stop()
                    self._save_data.pop(ident, None)
                    self.saveFailed.emit(message)
                elif self._open_id and (ident == self._open_id or not ident):
                    self._open_id = ''
                    self._open_timer.stop()
                    self.failed.emit(message)
                else:
                    self.failed.emit(message)

        def _on_saved_bytes(self, request: str, data: bytes) -> None:
            # arrives before the 'saved' event (the page posts the file first, then reports)
            if request == self._save_id:
                self._save_data[request] = bytes(data)

        def _on_open_timeout(self) -> None:
            if self._open_id or self._pending_open:
                self._open_id = ''
                self._pending_open = None
                self.failed.emit('the document did not open in time')

        def _on_save_timeout(self) -> None:
            if self._save_id:
                self._save_data.pop(self._save_id, None)
                self._save_id = ''
                self.saveFailed.emit('the edited file did not come back in time')

    _QT['OfficeEditorView'] = OfficeEditorView
    return _QT


def OfficeEditorView(component, language='en', dark=False, parent=None):
    """Build the view (see the class of the same name inside _qt())."""
    return _qt()['OfficeEditorView'](component, language=language, dark=dark, parent=parent)
