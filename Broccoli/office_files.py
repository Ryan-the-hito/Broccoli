"""Word / Excel / PowerPoint files as plain text lines, and text edits written back into the file.

Broccoli's editor, its AI edit flow, its history and its diffs all work on text. For an office
file that text is a "text view" of the document, one line per unit:

  Word        one line per paragraph ("# Heading", "- list item", plain text) and one line per
              table row ("| cell | cell |")
  Excel       "## Sheet: <name>" then one line per filled cell: "B7: =SUM(B2:B6)"
  PowerPoint  "## Slide <n>" then one line per paragraph of each text box: "[Title 1] text"

    office_text(data, kind)                    -> the text view of a file's bytes
    office_apply_text(data, kind, new_text)    -> (new bytes, the text view they give, error)

office_apply_text compares the file's text view with new_text and changes only what differs:
the paragraphs / cells / text boxes of changed lines, added and removed lines. Everything else in
the file (formatting, pictures, charts, styles, parts this code does not know) stays as it is —
Word and PowerPoint files are changed inside their own XML, Excel files cell by cell.

The result is always checked: the new file's text view must be exactly the text asked for (after
harmless tidying such as slide renumbering and cell order). If it is not, nothing is returned but
an explanation of the first line that cannot be written, so a caller never writes a file whose
content differs from what was approved.

No Qt, no Broccoli imports: usable and testable on its own.
"""
import copy
import datetime
import difflib
import io
import os
import re
import zipfile

OFFICE_KINDS = {'.docx': 'docx', '.xlsx': 'xlsx', '.pptx': 'pptx'}
BREAK = '<br>'
IMAGE_TOKEN = '{{image}}'
FIELD_TOKEN = '{{field}}'


class OfficeTextError(Exception):
    """A text edit that cannot be written into the document (the message is for the model)."""


def office_kind(path) -> str:
    return OFFICE_KINDS.get(os.path.splitext(str(path or ''))[1].lower(), '')


def office_text(data: bytes, kind: str) -> str:
    if kind == 'docx':
        return _docx_text(data)
    if kind == 'xlsx':
        return _xlsx_text(data)
    if kind == 'pptx':
        return _pptx_text(data)
    raise OfficeTextError('unknown office file kind: %r' % (kind,))


def office_apply_text(data: bytes, kind: str, new_text: str):
    """(new_bytes, final_text, '') — or (None, None, why) when new_text cannot be written."""
    new_text = str(new_text or '').replace('\r\n', '\n').replace('\r', '\n')
    try:
        if kind == 'docx':
            new_data, wanted = _docx_apply(data, new_text)
        elif kind == 'xlsx':
            new_data, wanted = _xlsx_apply(data, new_text)
        elif kind == 'pptx':
            new_data, wanted = _pptx_apply(data, new_text)
        else:
            return None, None, 'unknown office file kind: %r' % (kind,)
        final = office_text(new_data, kind)
    except OfficeTextError as exc:
        return None, None, str(exc)
    except Exception as exc:   # a document this code does not understand: never write a guess
        return None, None, 'this document could not be changed as text (%s: %s)' % (type(exc).__name__, exc)
    if final != wanted:
        return None, None, _first_difference(wanted, final)
    return new_data, final, ''


def office_text_guide(kind: str) -> str:
    """How the text view of this kind of file is written (for the model's instructions)."""
    if kind == 'docx':
        return ('This is the text view of a Word document: one line per paragraph. "# " … "######### " start '
                'headings, "- " a bullet item, "1. " a numbered item (two spaces of indent per list level), '
                'a line of "| cell | cell |" is one table row. %s is a line break inside a paragraph, %s a '
                'picture (keep it to keep the picture). Edit, add or remove lines; formatting of unchanged '
                'text is kept. A table row must keep its number of cells.' % (BREAK, IMAGE_TOKEN))
    if kind == 'xlsx':
        return ('This is the text view of an Excel workbook: "## Sheet: <name>" then one line per filled '
                'cell, "<cell>: <content>", e.g. "B7: =SUM(B2:B6)". A content starting with "=" is a formula; '
                'a number is a number; TRUE / FALSE; anything else is text (start it with \' to force text, '
                'e.g. \'007). Change a line to change a cell, add a line for a new cell, delete a line to '
                'empty a cell. Sheets cannot be added, removed or renamed here.')
    if kind == 'pptx':
        return ('This is the text view of a PowerPoint file: "## Slide <n>" then one line per paragraph, '
                '"[<text box name>] text". Change a line to change that paragraph; add a line with the name '
                'of a text box of that slide to add a paragraph to it; delete lines to remove paragraphs. '
                'Add a "## Slide" line (with lines for its text boxes, named like those of the slide before '
                'it) to add a slide with the same layout as the slide before it; delete a "## Slide" line and '
                'its lines to remove that slide. Positions, sizes and pictures cannot be changed here.')
    return ''


def _first_difference(wanted: str, final: str) -> str:
    a, b = wanted.split('\n'), final.split('\n')
    for index in range(max(len(a), len(b))):
        left = a[index] if index < len(a) else None
        right = b[index] if index < len(b) else None
        if left != right:
            if left is None:
                return ('the document would hold an extra line %d: %r. Nothing was written.' % (index + 1, right))
            if right is None:
                return ('line %d (%r) cannot be written into this document as it is. Nothing was written.'
                        % (index + 1, left[:160]))
            return ('line %d cannot be written as it is: asked for %r, the document would hold %r. '
                    'Nothing was written.' % (index + 1, left[:160], right[:160]))
    return 'the document would not hold the text asked for. Nothing was written.'


# ══ shared: replacing a paragraph's text while keeping the formatting of what does not change ══
class _Seg:
    """A stretch of a paragraph's text: a run (el), a fixed thing that cannot hold other text
    (a picture, a field), or the boundary between two paragraphs of a table cell (pbreak)."""
    __slots__ = ('el', 'text', 'fixed', 'pbreak')

    def __init__(self, el, text, fixed=False, pbreak=None):
        self.el, self.text, self.fixed, self.pbreak = el, text, fixed, pbreak


_ATOM_RE = re.compile('(%s)' % '|'.join(re.escape(t) for t in (IMAGE_TOKEN, FIELD_TOKEN, BREAK)))


def _atoms(text: str) -> list:
    """The text as single characters, with a picture / field / break mark as one unit each."""
    atoms = []
    for piece in _ATOM_RE.split(text):
        if not piece:
            continue
        if _ATOM_RE.fullmatch(piece):
            atoms.append(piece)
        else:
            atoms.extend(piece)
    return atoms


def _replace_text(segs, new_text, ops):
    """Turn the text of `segs` (their texts joined) into new_text. Only the stretches that differ
    are touched (found by comparing the two texts): text that stays keeps its own run, replaced
    text takes the formatting of what it replaces, inserted text that of the character before it.
    A picture / field mark that is still in new_text is never touched.
    ops: set_text(el, text), remove(el), new_run(after_seg_or_None, like_seg_or_None) -> el,
    merge(pbreak)."""
    old_text = ''.join(seg.text for seg in segs)
    if old_text == new_text:
        return
    spans, position = [], 0
    for seg in segs:
        spans.append((position, position + len(seg.text)))
        position += len(seg.text)
    old_atoms, new_atoms = _atoms(old_text), _atoms(new_text)
    old_offsets, new_offsets = [0], [0]
    for atom in old_atoms:
        old_offsets.append(old_offsets[-1] + len(atom))
    for atom in new_atoms:
        new_offsets.append(new_offsets[-1] + len(atom))
    edits = [[] for _ in segs]      # per seg: (local start, local end, replacement)
    additions = []                  # (seg to put a new run after, text)

    def writable(index):
        return not segs[index].fixed and segs[index].pbreak is None

    matcher = difflib.SequenceMatcher(None, old_atoms, new_atoms, autojunk=False)
    for tag, a1, a2, b1, b2 in reversed(matcher.get_opcodes()):
        if tag == 'equal':
            continue
        i1, i2 = old_offsets[a1], old_offsets[a2]
        middle = new_text[new_offsets[b1]:new_offsets[b2]]
        host = None
        if middle:
            if i2 > i1:      # replaced text: the run of the first replaced character
                host = next((k for k in range(len(segs)) if writable(k) and spans[k][0] <= i1 < spans[k][1]), None)
            if host is None:  # the run of the character before
                host = next((k for k in range(len(segs)) if writable(k) and spans[k][0] < i1 <= spans[k][1]), None)
            if host is None:  # the run starting here
                host = next((k for k in range(len(segs)) if writable(k) and spans[k][0] == i1 < spans[k][1]), None)
            if host is None:  # an empty run sitting exactly here
                host = next((k for k in range(len(segs)) if writable(k) and spans[k][0] == i1 == spans[k][1]), None)
        placed = False
        for k in range(len(segs)):
            start, stop = spans[k]
            low, high = max(i1, start), min(i2, stop)
            if low < high:
                edits[k].append((low - start, high - start, middle if k == host and not placed else ''))
                placed = placed or k == host
        if middle and host is not None and not placed:
            start = spans[host][0]
            edits[host].append((i1 - start, i1 - start, middle))
            placed = True
        if middle and not placed:
            before = None
            for k in range(len(segs)):
                if spans[k][1] <= i1:
                    before = segs[k]
            additions.append((before, middle))
    like = next((seg for seg in segs if not seg.fixed and seg.pbreak is None), None)
    for before, middle in additions:
        ops.set_text(ops.new_run(before, like), middle)
    for seg, changes in zip(segs, edits):
        if not changes:
            continue
        result = seg.text
        for start, stop, replacement in sorted(changes, key=lambda item: (item[0], item[1]), reverse=True):
            result = result[:start] + replacement + result[stop:]
        if result == seg.text:
            continue
        if seg.pbreak is not None:
            if result:
                raise OfficeTextError('a paragraph boundary inside a table cell cannot be edited in part')
            ops.merge(seg.pbreak)
        elif seg.fixed:
            if result:
                raise OfficeTextError('text cannot be written inside %s' % seg.text)
            ops.remove(seg.el)
        else:
            ops.set_text(seg.el, result)


# ══ Word ══════════════════════════════════════════════════════════════════════════════════
_W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
_XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'


def _w(tag: str) -> str:
    return '{%s}%s' % (_W, tag)


_W_INLINE_CONTAINERS = {_w(t) for t in ('hyperlink', 'smartTag', 'ins', 'sdt', 'sdtContent', 'fldSimple',
                                        'customXml', 'moveTo', 'dir', 'bdo')}
_W_TEXT_CHILDREN = {_w(t) for t in ('rPr', 't', 'tab', 'br', 'cr', 'noBreakHyphen', 'softHyphen',
                                    'lastRenderedPageBreak')}
_W_PICTURE_CHILDREN = {_w(t) for t in ('drawing', 'pict', 'object')}
_MC_ALTERNATE = '{http://schemas.openxmlformats.org/markup-compatibility/2006}AlternateContent'
_HEADING_RE = re.compile(r'^(?:heading|标题|見出し)\s*([1-9])$', re.IGNORECASE)
_LINE_HEADING_RE = re.compile(r'^(#{1,9}) (.*)$', re.DOTALL)
_LINE_LIST_RE = re.compile(r'^((?:  )*)(- |1\. )(.*)$', re.DOTALL)
_LINE_SPECIAL_RE = re.compile(r'^(?:#{1,9} |(?:  )*(?:- |1\. )|\||\\)')


def _w_run_text(run) -> tuple:
    """(text, fixed) of a w:r."""
    parts, fixed = [], False
    for child in run:
        tag = child.tag
        if tag == _w('t'):
            parts.append(child.text or '')
        elif tag == _w('tab'):
            parts.append('\t')
        elif tag in (_w('br'), _w('cr')):
            if child.get(_w('type')) in ('page', 'column'):
                fixed = True
            else:
                parts.append(BREAK)
        elif tag == _w('noBreakHyphen'):
            parts.append('\u2011')
        elif tag in _W_PICTURE_CHILDREN or tag == _MC_ALTERNATE:
            parts.append(IMAGE_TOKEN)
            fixed = True
        elif tag not in _W_TEXT_CHILDREN:
            fixed = True      # a field, a footnote mark, …: kept as it is
    return ''.join(parts), fixed


def _w_paragraph_segs(paragraph) -> list:
    segs = []

    def walk(element):
        for child in element:
            if child.tag == _w('r'):
                text, fixed = _w_run_text(child)
                if text or not fixed:
                    segs.append(_Seg(child, text, fixed))
            elif child.tag in _W_INLINE_CONTAINERS:
                walk(child)
    walk(paragraph)
    return segs


def _w_set_run_text(run, text: str) -> None:
    for child in list(run):
        if child.tag != _w('rPr'):
            run.remove(child)
    for index, piece in enumerate(re.split('(\t|%s)' % re.escape(BREAK), text)):
        if not piece:
            continue
        if piece == '\t':
            run.append(run.makeelement(_w('tab'), {}))
        elif piece == BREAK:
            run.append(run.makeelement(_w('br'), {}))
        else:
            node = run.makeelement(_w('t'), {})
            node.text = piece
            if piece != piece.strip() or '  ' in piece:
                node.set(_XML_SPACE, 'preserve')
            run.append(node)


class _WordOps:
    def __init__(self, paragraph):
        self.paragraph = paragraph     # where a new run goes when there is none to put it after

    def set_text(self, el, text):
        _w_set_run_text(el, text)

    def remove(self, el):
        el.getparent().remove(el)

    def new_run(self, after, like):
        target = self.paragraph
        run = target.makeelement(_w('r'), {})
        if like is not None and like.el is not None:
            props = like.el.find(_w('rPr'))
            if props is not None:
                run.append(copy.deepcopy(props))
        if after is not None and after.pbreak is not None:
            target = after.pbreak[1]
            after = None
        if after is not None and after.el is not None:
            after.el.addnext(run)
        else:
            props = target.find(_w('pPr'))
            if props is not None:
                props.addnext(run)
            else:
                target.insert(0, run)
        return run

    def merge(self, pbreak):
        first, second = pbreak
        for child in list(second):
            if child.tag != _w('pPr'):
                first.append(child)
        second.getparent().remove(second)


def _w_paragraph_text(paragraph) -> str:
    return ''.join(seg.text for seg in _w_paragraph_segs(paragraph))


def _w_set_paragraph_text(paragraph, text: str) -> None:
    _replace_text(_w_paragraph_segs(paragraph), text, _WordOps(paragraph))


def _w_cell_segs(cell) -> list:
    segs, previous = [], None
    for paragraph in cell.findall(_w('p')):
        if previous is not None:
            segs.append(_Seg(None, BREAK, pbreak=(previous, paragraph)))
        segs.extend(_w_paragraph_segs(paragraph))
        previous = paragraph
    return segs


def _w_cell_text(cell) -> str:
    return ''.join(seg.text for seg in _w_cell_segs(cell)).strip()


def _w_row_cells(row) -> list:
    cells = []
    for child in row:
        if child.tag == _w('tc'):
            cells.append(child)
        elif child.tag == _w('sdt'):
            cells.extend(child.iter(_w('tc')))
    return cells


def _row_line(texts) -> str:
    return '| ' + ' | '.join(str(t).replace('\\', '\\\\').replace('|', '\\|') for t in texts) + ' |'


def _parse_row_line(line: str) -> list:
    body = line.strip()
    if not body.startswith('|'):
        raise OfficeTextError('a table row must start with "|": %r' % line[:80])
    body = body[1:]
    cells, current, index = [], [], 0
    while index < len(body):
        ch = body[index]
        if ch == '\\' and index + 1 < len(body) and body[index + 1] in '\\|':
            current.append(body[index + 1])
            index += 2
            continue
        if ch == '|':
            cells.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
        index += 1
    if ''.join(current).strip():
        cells.append(''.join(current).strip())    # a row written without its closing "|"
    return cells


class _WordDoc:
    def __init__(self, data: bytes):
        import docx
        self.document = docx.Document(io.BytesIO(data))
        self.body = self.document.element.body
        self.style_names = {}
        self.style_numbered = {}
        try:
            for style in self.document.styles.element.iter(_w('style')):
                style_id = style.get(_w('styleId')) or ''
                name = style.find(_w('name'))
                self.style_names[style_id] = (name.get(_w('val')) if name is not None else style_id) or style_id
                self.style_numbered[style_id] = style.find('%s/%s' % (_w('pPr'), _w('numPr'))) is not None
        except Exception:
            pass
        self._number_formats = None

    def save(self) -> bytes:
        out = io.BytesIO()
        self.document.save(out)
        return out.getvalue()

    # blocks: ('p', paragraph) and ('row', tr, tbl), in document order
    def blocks(self) -> list:
        found = []

        def walk(container):
            for child in container:
                if child.tag == _w('p'):
                    found.append(('p', child, None))
                elif child.tag == _w('tbl'):
                    for row in child.iter(_w('tr')):
                        if row.getparent() is child or row.getparent().tag != _w('tbl'):
                            # rows of this table only (not of a table nested in a cell)
                            owner = row.getparent()
                            while owner is not None and owner.tag != _w('tbl'):
                                owner = owner.getparent()
                            if owner is child:
                                found.append(('row', row, child))
                elif child.tag == _w('sdt'):
                    content = child.find(_w('sdtContent'))
                    if content is not None:
                        walk(content)
        walk(self.body)
        return found

    def _list_format(self, paragraph, style_id: str) -> str:
        """'- ' or '1. ' for a list paragraph, '' for others."""
        props = paragraph.find(_w('pPr'))
        num = props.find(_w('numPr')) if props is not None else None
        name = self.style_names.get(style_id, '').lower()
        if num is None and not self.style_numbered.get(style_id) and not name.startswith('list bullet') \
                and not name.startswith('list number'):
            return ''
        if num is not None:
            num_id = num.find(_w('numId'))
            if num_id is not None and num_id.get(_w('val')) == '0':
                return ''       # numbering switched off for this paragraph
            level = num.find(_w('ilvl'))
            fmt = self._number_format(num_id.get(_w('val')) if num_id is not None else '',
                                      level.get(_w('val')) if level is not None else '0')
            if fmt:
                return '- ' if fmt == 'bullet' else '1. '
        if name.startswith('list number'):
            return '1. '
        return '- '

    def _number_format(self, num_id: str, level: str) -> str:
        if self._number_formats is None:
            self._number_formats = {}
            try:
                numbering = self.document.part.numbering_part.element
                abstract = {}
                for item in numbering.iter(_w('abstractNum')):
                    levels = {}
                    for lvl in item.iter(_w('lvl')):
                        fmt = lvl.find(_w('numFmt'))
                        levels[lvl.get(_w('ilvl')) or '0'] = fmt.get(_w('val')) if fmt is not None else ''
                    abstract[item.get(_w('abstractNumId'))] = levels
                for item in numbering.iter(_w('num')):
                    ref = item.find(_w('abstractNumId'))
                    if ref is not None:
                        self._number_formats[item.get(_w('numId'))] = abstract.get(ref.get(_w('val')), {})
            except Exception:
                self._number_formats = {}
        levels = self._number_formats.get(str(num_id), {})
        return levels.get(str(level), levels.get('0', ''))

    def prefix(self, paragraph) -> str:
        props = paragraph.find(_w('pPr'))
        style = props.find(_w('pStyle')) if props is not None else None
        style_id = style.get(_w('val')) if style is not None else ''
        name = self.style_names.get(style_id, style_id)
        match = _HEADING_RE.match(name.strip())
        if match:
            return '#' * int(match.group(1)) + ' '
        if name.strip().lower() == 'title':
            return '# '
        marker = self._list_format(paragraph, style_id)
        if marker:
            num = props.find(_w('numPr')) if props is not None else None
            level = num.find(_w('ilvl')) if num is not None else None
            try:
                depth = int(level.get(_w('val'))) if level is not None else 0
            except (TypeError, ValueError):
                depth = 0
            return '  ' * max(0, min(depth, 8)) + marker
        return ''

    def paragraph_line(self, paragraph) -> str:
        prefix, text = self.prefix(paragraph), _w_paragraph_text(paragraph)
        if not prefix and _LINE_SPECIAL_RE.match(text):
            return '\\' + text
        return prefix + text

    def line_of(self, block) -> str:
        if block[0] == 'p':
            return self.paragraph_line(block[1])
        return _row_line(_w_cell_text(cell) for cell in _w_row_cells(block[1]))

    def text(self) -> str:
        return '\n'.join(self.line_of(block) for block in self.blocks())


def _docx_text(data: bytes) -> str:
    return _WordDoc(data).text()


def _split_paragraph_line(line: str) -> tuple:
    """(prefix, text) of a paragraph line of the text view."""
    match = _LINE_HEADING_RE.match(line)
    if match:
        return match.group(1) + ' ', match.group(2)
    match = _LINE_LIST_RE.match(line)
    if match:
        return match.group(1) + match.group(2), match.group(3)
    if line.startswith('\\'):
        return '', line[1:]
    return '', line


def _docx_apply(data: bytes, new_text: str):
    doc = _WordDoc(data)
    blocks = doc.blocks()
    old_lines = [doc.line_of(block) for block in blocks]
    new_lines = new_text.split('\n')
    if old_lines == new_lines:
        return data, new_text
    if not blocks and new_lines == ['']:
        return data, ''
    modifies, deletes, inserts = [], [], []     # (old index, line) / old index / (anchor index, lines)
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            continue
        olds, news = list(range(i1, i2)), new_lines[j1:j2]
        extra = []
        for offset, line in enumerate(news):
            if offset < len(olds):
                old_kind = blocks[olds[offset]][0]
                new_kind = 'row' if line.startswith('|') else 'p'
                if old_kind == new_kind:
                    modifies.append((olds[offset], line))
                    continue
                deletes.append(olds[offset])
                inserts.append((olds[offset], [line]))
            else:
                extra.append(line)
        deletes.extend(olds[len(news):])
        if extra:
            # after the last old line of this stretch; a pure insertion goes before old line i1
            inserts.append(((olds[-1] if olds else i1 - 1), extra))

    def model_paragraph(prefix: str, near: int):
        """A paragraph of the document with this prefix (nearest first), to copy its look from."""
        order = sorted(range(len(blocks)), key=lambda k: (abs(k - near), k))
        for k in order:
            if blocks[k][0] == 'p' and doc.prefix(blocks[k][1]) == prefix:
                return blocks[k][1]
        return None

    def style_props(prefix: str):
        """Paragraph properties for a prefix from the document's own styles, or None."""
        wanted = None
        marker = prefix.strip()
        if marker.startswith('#'):
            wanted = 'heading %d' % len(marker)
        elif marker == '-':
            wanted = 'list bullet'
        elif marker == '1.':
            wanted = 'list number'
        if wanted is None or prefix.startswith(' '):
            return None
        for style_id, name in doc.style_names.items():
            if name.strip().lower() == wanted:
                props = doc.body.makeelement(_w('pPr'), {})
                style = props.makeelement(_w('pStyle'), {_w('val'): style_id})
                props.append(style)
                return props
        return None

    def set_prefix(paragraph, prefix: str, near: int) -> None:
        if doc.prefix(paragraph) == prefix:
            return
        old_props = paragraph.find(_w('pPr'))
        section = old_props.find(_w('sectPr')) if old_props is not None else None
        model = model_paragraph(prefix, near)
        if model is not None:
            props = copy.deepcopy(model.find(_w('pPr'))) if model.find(_w('pPr')) is not None else None
            if props is not None:
                for child in props.findall(_w('sectPr')):
                    props.remove(child)
        else:
            props = style_props(prefix)
            if props is None and prefix:
                what = ('a heading of level %d' % len(prefix.strip()) if prefix.strip().startswith('#')
                        else 'a list item of this kind')
                raise OfficeTextError('this document has no style for %s and no such paragraph to copy from; '
                                      'write the line without "%s"' % (what, prefix.strip()))
        if old_props is not None:
            paragraph.remove(old_props)
        if props is None and section is not None:
            props = paragraph.makeelement(_w('pPr'), {})
        if props is not None:
            if section is not None:
                props.append(section)
            paragraph.insert(0, props)

    def new_paragraph(line: str, near: int):
        prefix, text = _split_paragraph_line(line)
        paragraph = doc.body.makeelement(_w('p'), {})
        model = model_paragraph(prefix, near)
        if model is not None:
            props = model.find(_w('pPr'))
            if props is not None:
                props = copy.deepcopy(props)
                for child in props.findall(_w('sectPr')):
                    props.remove(child)
                paragraph.append(props)
            run = paragraph.makeelement(_w('r'), {})
            first = next((seg for seg in _w_paragraph_segs(model) if not seg.fixed), None)
            if first is not None and first.el.find(_w('rPr')) is not None:
                run.append(copy.deepcopy(first.el.find(_w('rPr'))))
            paragraph.append(run)
        else:
            set_prefix(paragraph, prefix, near)
        _w_set_paragraph_text(paragraph, text)
        return paragraph

    def set_row(row, line: str) -> None:
        wanted, cells = _parse_row_line(line), _w_row_cells(row)
        if len(wanted) != len(cells):
            raise OfficeTextError('the table row %r has %d cells in the document, the line gives %d'
                                  % (line[:80], len(cells), len(wanted)))
        for cell, text in zip(cells, wanted):
            if _w_cell_text(cell) == text:
                continue
            first = cell.find(_w('p'))
            if first is None:
                first = cell.makeelement(_w('p'), {})
                cell.append(first)
            segs = _w_cell_segs(cell)
            # the cell's text as shown is stripped; write against the unstripped text
            raw = ''.join(seg.text for seg in segs)
            lead = raw[:len(raw) - len(raw.lstrip())]
            trail = raw[len(raw.rstrip()):] if raw.strip() else ''
            _replace_text(segs, lead + text + trail, _WordOps(first))

    def new_row(model_row, line: str):
        row = copy.deepcopy(model_row)
        for cell in _w_row_cells(row):
            paragraphs = cell.findall(_w('p'))
            for extra_paragraph in paragraphs[1:]:
                cell.remove(extra_paragraph)
            for nested in cell.findall(_w('tbl')):
                cell.remove(nested)
            if paragraphs:
                for seg in _w_paragraph_segs(paragraphs[0]):
                    if seg.fixed:
                        seg.el.getparent().remove(seg.el)
                    else:
                        _w_set_run_text(seg.el, '')
        set_row(row, line)
        return row

    def new_table(lines: list):
        rows = [_parse_row_line(line) for line in lines]
        width = len(rows[0])
        if not width or any(len(row) != width for row in rows):
            raise OfficeTextError('the rows of a new table must all have the same number of cells')
        table = doc.document.add_table(rows=len(rows), cols=width)
        for style_id, name in doc.style_names.items():
            if name.strip().lower() == 'table grid':
                try:
                    table.style = doc.document.styles[name]
                except Exception:
                    pass
                break
        element = table._tbl
        element.getparent().remove(element)
        for row, texts in zip(element.iter(_w('tr')), rows):
            for cell, text in zip(_w_row_cells(row), texts):
                _w_set_paragraph_text(cell.find(_w('p')), text)
        return element

    # 1. changed lines
    for index, line in modifies:
        kind, element, _table = blocks[index]
        if kind == 'p':
            prefix, text = _split_paragraph_line(line)
            set_prefix(element, prefix, index)
            _w_set_paragraph_text(element, text)
        else:
            set_row(element, line)

    # 2. added lines (anchors are old blocks, all still in place)
    for anchor, lines in inserts:
        after = blocks[anchor] if anchor >= 0 else None
        following = blocks[anchor + 1] if anchor + 1 < len(blocks) else None
        position = None           # the element new things go after
        index = 0
        while index < len(lines):
            line = lines[index]
            if line.startswith('|'):
                group = [line]
                while index + len(group) < len(lines) and lines[index + len(group)].startswith('|'):
                    group.append(lines[index + len(group)])
                index += len(group)
                if position is not None and position.tag == _w('tr'):
                    for row_line in group:
                        row = new_row(position, row_line)
                        position.addnext(row)
                        position = row
                elif position is None and after is not None and after[0] == 'row':
                    position = after[1]
                    for row_line in group:
                        row = new_row(position, row_line)
                        position.addnext(row)
                        position = row
                elif position is None and following is not None and following[0] == 'row' and (
                        after is None or after[0] != 'row'):
                    first_row = following[1]
                    for row_line in group:
                        first_row.addprevious(new_row(first_row, row_line))
                    position = None
                    after = ('row-before', first_row, following[2])
                else:
                    table = new_table(group)
                    _docx_insert_after(doc, position, after, following, table)
                    position = table
            else:
                index += 1
                if (position is not None and position.tag == _w('tr')) or (
                        position is None and after is not None and after[0] == 'row'
                        and following is not None and following[0] == 'row' and following[2] is after[2]):
                    raise OfficeTextError('a paragraph cannot be put between the rows of a table: %r' % line[:80])
                paragraph = new_paragraph(line, max(anchor, 0))
                _docx_insert_after(doc, position, after, following, paragraph)
                position = paragraph

    # 3. removed lines
    for index in sorted(set(deletes), reverse=True):
        kind, element, table = blocks[index]
        if element.getparent() is None:
            continue
        if kind == 'row':
            element.getparent().remove(element)
            if table.find('.//' + _w('tr')) is None and table.getparent() is not None:
                table.getparent().remove(table)
            continue
        props = element.find(_w('pPr'))
        section = props.find(_w('sectPr')) if props is not None else None
        if section is not None:
            # this paragraph ends a section: hand that over to the paragraph before it
            previous = element.getprevious()
            if previous is None or previous.tag != _w('p'):
                raise OfficeTextError('the paragraph that ends a section cannot be removed')
            target = previous.find(_w('pPr'))
            if target is None:
                target = previous.makeelement(_w('pPr'), {})
                previous.insert(0, target)
            if target.find(_w('sectPr')) is not None:
                raise OfficeTextError('the paragraph that ends a section cannot be removed')
            target.append(section)
        element.getparent().remove(element)
    return doc.save(), new_text


def _docx_insert_after(doc, position, after, following, element) -> None:
    """Put a new paragraph / table after `position` (something just inserted), else after the old
    block `after`, else before the old block `following`, else at the end of the body."""
    if position is not None:
        target = position
        if target.tag == _w('tr'):
            while target.tag != _w('tbl'):
                target = target.getparent()
        target.addnext(element)
        return
    if after is not None and after[0] in ('p', 'row'):
        target = after[1] if after[0] == 'p' else after[2]
        target.addnext(element)
        return
    if after is not None and after[0] == 'row-before':
        after[2].addprevious(element)
        return
    if following is not None:
        target = following[1] if following[0] == 'p' else following[2]
        target.addprevious(element)
        return
    section = doc.body.find(_w('sectPr'))
    if section is not None:
        section.addprevious(element)
    else:
        doc.body.append(element)


# ══ PowerPoint ════════════════════════════════════════════════════════════════════════════
_A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
_SLIDE_RE = re.compile(r'^## Slide\b.*$')
_PPT_LINE_RE = re.compile(r'^\[([^\]]*)\] ?(.*)$', re.DOTALL)
NOTES_KEY = 'Notes'


def _a(tag: str) -> str:
    return '{%s}%s' % (_A, tag)


def _a_paragraph_segs(paragraph) -> list:
    segs = []
    for child in paragraph:
        if child.tag == _a('r'):
            node = child.find(_a('t'))
            segs.append(_Seg(child, (node.text or '') if node is not None else ''))
        elif child.tag == _a('br'):
            segs.append(_Seg(child, BREAK, fixed=True))
        elif child.tag == _a('fld'):
            segs.append(_Seg(child, FIELD_TOKEN, fixed=True))
    return segs


class _SlideOps:
    def __init__(self, paragraph):
        self.paragraph = paragraph

    def set_text(self, el, text):
        # a line break typed into the text becomes a real break element
        pieces = text.split(BREAK)
        node = el.find(_a('t'))
        if node is None:
            node = el.makeelement(_a('t'), {})
            el.append(node)
        node.text = pieces[0]
        current = el
        for piece in pieces[1:]:
            brk = el.makeelement(_a('br'), {})
            current.addnext(brk)
            run = copy.deepcopy(el)
            run.find(_a('t')).text = piece
            brk.addnext(run)
            current = run

    def remove(self, el):
        el.getparent().remove(el)

    def new_run(self, after, like):
        run = self.paragraph.makeelement(_a('r'), {})
        if like is not None and like.el.find(_a('rPr')) is not None:
            run.append(copy.deepcopy(like.el.find(_a('rPr'))))
        else:
            end_props = self.paragraph.find(_a('endParaRPr'))
            if end_props is not None:      # an empty placeholder keeps its look here
                props = copy.deepcopy(end_props)
                props.tag = _a('rPr')
                run.append(props)
        run.append(run.makeelement(_a('t'), {}))
        if after is not None and after.el is not None:
            after.el.addnext(run)
        else:
            props = self.paragraph.find(_a('pPr'))
            if props is not None:
                props.addnext(run)
            else:
                self.paragraph.insert(0, run)
        return run

    def merge(self, pbreak):
        raise OfficeTextError('paragraphs cannot be merged here')


def _a_paragraph_text(paragraph) -> str:
    return ''.join(seg.text for seg in _a_paragraph_segs(paragraph))


def _a_set_paragraph_text(paragraph, text: str) -> None:
    _replace_text(_a_paragraph_segs(paragraph), text, _SlideOps(paragraph))


class _Deck:
    def __init__(self, data: bytes):
        import pptx
        self.presentation = pptx.Presentation(io.BytesIO(data))

    def save(self) -> bytes:
        out = io.BytesIO()
        self.presentation.save(out)
        return out.getvalue()

    @staticmethod
    def _walk_shapes(shapes):
        for shape in shapes:
            if getattr(shape, 'shape_type', None) == 6 and hasattr(shape, 'shapes'):     # a group
                yield from _Deck._walk_shapes(shape.shapes)
            else:
                yield shape

    def boxes(self, slide) -> list:
        """[(key, txBody element, is_placeholder)] — every text holder of a slide, in order: text
        boxes and placeholders, each table cell, then the speaker notes."""
        found, used = [], {}

        def key_for(name: str) -> str:
            base = (name or 'Text').replace('[', '(').replace(']', ')').replace('\n', ' ').strip() or 'Text'
            used[base] = used.get(base, 0) + 1
            return base if used[base] == 1 else '%s#%d' % (base, used[base])

        for shape in self._walk_shapes(slide.shapes):
            try:
                if getattr(shape, 'has_table', False) and shape.has_table:
                    name = key_for(shape.name)
                    for r, row in enumerate(shape.table.rows):
                        for c, cell in enumerate(row.cells):
                            body = cell._tc.find(_a('txBody'))
                            if body is not None:
                                found.append(('%s R%dC%d' % (name, r + 1, c + 1), body, False))
                elif getattr(shape, 'has_text_frame', False) and shape.has_text_frame:
                    found.append((key_for(shape.name), shape.text_frame._txBody, bool(shape.is_placeholder)))
            except Exception:
                continue
        try:
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame is not None:
                frame = slide.notes_slide.notes_text_frame
                if frame.text.strip():
                    found.append((NOTES_KEY, frame._txBody, False))
        except Exception:
            pass
        return found

    def units(self) -> list:
        """The text view as a list: ('slide', slide) and ('p', key, a:p element, slide index)."""
        result = []
        for index, slide in enumerate(self.presentation.slides):
            result.append(('slide', slide, None, index))
            for key, body, placeholder in self.boxes(slide):
                paragraphs = body.findall(_a('p'))
                if any(_a_paragraph_text(p) for p in paragraphs) or (placeholder and paragraphs):
                    if not any(_a_paragraph_text(p) for p in paragraphs):
                        paragraphs = paragraphs[:1]       # an empty placeholder: one empty line
                    for paragraph in paragraphs:
                        result.append(('p', key, paragraph, index))
        return result

    @staticmethod
    def line_of(unit, number=None) -> str:
        if unit[0] == 'slide':
            return '## Slide %d' % (unit[3] + 1 if number is None else number)
        text = _a_paragraph_text(unit[2])
        return '[%s] %s' % (unit[1], text) if text else '[%s] ' % unit[1]

    def text(self) -> str:
        return '\n'.join(self.line_of(unit) for unit in self.units())


def _pptx_text(data: bytes) -> str:
    return _Deck(data).text()


def _pptx_tidy(text: str) -> str:
    """Number the slide lines 1, 2, 3 … (so an added or removed slide needs no renumbering)."""
    lines, number = [], 0
    for line in text.split('\n'):
        if _SLIDE_RE.match(line):
            number += 1
            lines.append('## Slide %d' % number)
        else:
            match = _PPT_LINE_RE.match(line)
            if match and not match.group(2):
                line = '[%s] ' % match.group(1)
            lines.append(line)
    return '\n'.join(lines)


def _pptx_blocks(lines: list) -> list:
    """[(slide line, [its paragraph lines])] of a text view."""
    blocks = []
    for number, line in enumerate(lines):
        if _SLIDE_RE.match(line):
            blocks.append((line, []))
        elif not blocks:
            raise OfficeTextError('the first line must be "## Slide 1"')
        elif not _PPT_LINE_RE.match(line):
            raise OfficeTextError('line %d is neither "## Slide <n>" nor "[<text box name>] text": %r'
                                  % (number + 1, line[:80]))
        else:
            blocks[-1][1].append(line)
    return blocks


def _pptx_apply(data: bytes, new_text: str):
    deck = _Deck(data)
    units = deck.units()
    old_lines = [deck.line_of(unit) for unit in units]
    wanted = _pptx_tidy(new_text)
    if '\n'.join(old_lines) == wanted:
        return data, wanted
    slides = list(deck.presentation.slides)
    old_blocks = [[] for _ in slides]          # per old slide: indices of its paragraph units
    for index, unit in enumerate(units):
        if unit[0] == 'p':
            old_blocks[unit[3]].append(index)
    raw_lines = []
    for line in str(new_text).split('\n'):
        match = None if _SLIDE_RE.match(line) else _PPT_LINE_RE.match(line)
        raw_lines.append('[%s] ' % match.group(1) if match and not match.group(2) else line)
    new_blocks = _pptx_blocks(raw_lines)

    # 1. which old slide each block of the new text is: the one it shares the most lines with;
    #    a block sharing none is that numbered slide rewritten (same number, same text boxes) or a new slide
    def shared(old_index, block):
        pool = {}
        for index in old_blocks[old_index]:
            pool[old_lines[index]] = pool.get(old_lines[index], 0) + 1
        count = 0
        for line in block[1]:
            if pool.get(line, 0) > 0:
                pool[line] -= 1
                count += 1
        return count
    pairs = sorted(((shared(o, block), -abs(o - n), o, n) for n, block in enumerate(new_blocks)
                    for o in range(len(slides))), reverse=True)
    assigned, used = [None] * len(new_blocks), set()
    for score, _near, o, n in pairs:
        if score > 0 and assigned[n] is None and o not in used:
            assigned[n] = o
            used.add(o)
    for n, block in enumerate(new_blocks):
        if assigned[n] is not None:
            continue
        number = re.match(r'^## Slide (\d+)\s*$', block[0])
        o = int(number.group(1)) - 1 if number else -1
        if 0 <= o < len(slides) and o not in used:
            keys = {key for key, _body, _ph in deck.boxes(slides[o])} | {NOTES_KEY}
            if all(_PPT_LINE_RE.match(line).group(1) in keys for line in block[1]):
                assigned[n] = o
                used.add(o)

    # 2. new slides: the layout of the slide before, its placeholders named like that slide's
    slide_objects = [None] * len(new_blocks)
    for n in range(len(new_blocks)):
        if assigned[n] is not None:
            slide_objects[n] = slides[assigned[n]]
    for n in range(len(new_blocks)):
        if slide_objects[n] is not None:
            continue
        source = slide_objects[n - 1] if n > 0 else None
        if source is None:
            source = next((s for s in slide_objects if s is not None), slides[0] if slides else None)
        layout = source.slide_layout if source is not None else deck.presentation.slide_layouts[0]
        slide = deck.presentation.slides.add_slide(layout)
        if source is not None:
            names = {}
            for shape in source.placeholders:
                try:
                    names[shape.placeholder_format.idx] = shape.name
                except Exception:
                    continue
            for shape in slide.placeholders:
                try:
                    if shape.placeholder_format.idx in names:
                        shape.name = names[shape.placeholder_format.idx]
                except Exception:
                    continue
        slide_objects[n] = slide

    # 3. the lines of each slide: kept, changed, added, removed
    line_number = 0
    for n, (header, lines) in enumerate(new_blocks):
        line_number += 1
        slide = slide_objects[n]
        old_indices = old_blocks[assigned[n]] if assigned[n] is not None else []
        old_block_lines = [old_lines[index] for index in old_indices]
        kept = [None] * len(lines)           # new line -> old unit index it keeps
        changed = {}
        matcher = difflib.SequenceMatcher(None, old_block_lines, lines, autojunk=False)
        survivors = set()
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for offset in range(i2 - i1):
                    kept[j1 + offset] = old_indices[i1 + offset]
                    survivors.add(old_indices[i1 + offset])
            elif tag == 'replace':
                for offset in range(min(i2 - i1, j2 - j1)):
                    index = old_indices[i1 + offset]
                    match = _PPT_LINE_RE.match(lines[j1 + offset])
                    if match.group(1) == units[index][1]:
                        kept[j1 + offset] = index
                        survivors.add(index)
                        changed[index] = match.group(2)
        for index, text in changed.items():
            _a_set_paragraph_text(units[index][2], text)
        removed = [index for index in old_indices if index not in survivors]
        boxes = {key: body for key, body, _placeholder in deck.boxes(slide)}
        last_in_box, fresh_box = {}, set()
        for offset, line in enumerate(lines):
            match = _PPT_LINE_RE.match(line)
            key, text = match.group(1), match.group(2)
            if kept[offset] is not None:
                last_in_box[key] = units[kept[offset]][2]
                continue
            if key not in boxes:
                if key == NOTES_KEY:
                    frame = slide.notes_slide.notes_text_frame
                    if frame is None:
                        raise OfficeTextError('this slide has no place for notes')
                    boxes[key] = frame._txBody
                else:
                    raise OfficeTextError('line %d: this slide has no text box named "%s" (it has: %s)'
                                          % (line_number + offset + 1, key, ', '.join(sorted(boxes)) or 'none'))
            body = boxes[key]
            previous = last_in_box.get(key)
            existing = body.findall(_a('p'))
            paragraph = None
            if previous is None:
                # a paragraph of this box that is being removed (or its single empty one) is reused
                # for the box's first new line, so that line keeps the paragraph's level and look
                for candidate in existing:
                    owner = next((i for i in removed if units[i][2] is candidate), None)
                    if owner is not None:
                        paragraph = candidate
                        removed.remove(owner)
                        break
                if paragraph is None and key not in fresh_box and existing and not any(
                        _a_paragraph_text(p) for p in existing):
                    paragraph = existing[0]
            if paragraph is None:
                model = previous if previous is not None else (existing[-1] if existing else None)
                paragraph = body.makeelement(_a('p'), {})
                if model is not None:
                    if model.find(_a('pPr')) is not None:
                        paragraph.append(copy.deepcopy(model.find(_a('pPr'))))
                    run = paragraph.makeelement(_a('r'), {})
                    like = next((seg.el for seg in _a_paragraph_segs(model) if not seg.fixed), None)
                    if like is not None and like.find(_a('rPr')) is not None:
                        run.append(copy.deepcopy(like.find(_a('rPr'))))
                    run.append(run.makeelement(_a('t'), {}))
                    paragraph.append(run)
                    if model.find(_a('endParaRPr')) is not None:
                        paragraph.append(copy.deepcopy(model.find(_a('endParaRPr'))))
                if previous is not None:
                    previous.addnext(paragraph)
                elif existing:
                    existing[0].addprevious(paragraph)
                else:
                    body.append(paragraph)
            fresh_box.add(key)
            _a_set_paragraph_text(paragraph, text)
            last_in_box[key] = paragraph
        for index in removed:
            paragraph = units[index][2]
            body = paragraph.getparent()
            if body is None:
                continue
            if len(body.findall(_a('p'))) > 1:
                body.remove(paragraph)
            else:
                _a_set_paragraph_text(paragraph, '')      # a text box always keeps one paragraph
        line_number += len(lines)

    # 4. slide order and removed slides
    id_list = deck.presentation.slides._sldIdLst
    entries = list(id_list)
    entry_of = {id(slide): entry for slide, entry in zip(list(deck.presentation.slides), entries)}
    order = [entry_of[id(slide)] for slide in slide_objects]
    relation = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
    for entry in entries:
        if not any(entry is item for item in order):
            deck.presentation.part.drop_rel(entry.get(relation))
        id_list.remove(entry)
    for entry in order:
        id_list.append(entry)
    return deck.save(), wanted


# ══ Excel ═════════════════════════════════════════════════════════════════════════════════
_S = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
_R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
_PKG_REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
_CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
_SHEET_RE = re.compile(r'^## Sheet: (.*)$')
_CELL_LINE_RE = re.compile(r'^([A-Z]{1,3})([1-9][0-9]{0,6}): ?(.*)$', re.DOTALL)
_NUMBER_RE = re.compile(r'^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$')
_DATE_RE = re.compile(r'^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?$')
_ERRORS = ('#NULL!', '#DIV/0!', '#VALUE!', '#REF!', '#NAME?', '#NUM!', '#N/A', '#GETTING_DATA')


def _s(tag: str) -> str:
    return '{%s}%s' % (_S, tag)


def _column_number(letters: str) -> int:
    number = 0
    for ch in letters:
        number = number * 26 + (ord(ch) - 64)
    return number


def _split_address(address: str) -> tuple:
    match = re.match(r'^\$?([A-Z]{1,3})\$?(\d+)$', address or '')
    if not match:
        raise OfficeTextError('a cell without a usable address (%r): this workbook cannot be edited as text' % address)
    return int(match.group(2)), _column_number(match.group(1))


def _looks_special(text: str) -> bool:
    return bool(text[:1] in ("'", '=') or _NUMBER_RE.match(text) or text in ('TRUE', 'FALSE')
                or _DATE_RE.match(text) or text in _ERRORS or text != text.strip() or not text)


def _escape_cell_text(text: str) -> str:
    return text.replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')


def _unescape_cell_text(text: str) -> str:
    out, index = [], 0
    while index < len(text):
        ch = text[index]
        if ch == '\\' and index + 1 < len(text):
            nxt = text[index + 1]
            out.append({'n': '\n', 'r': '\r', 't': '\t', '\\': '\\'}.get(nxt, '\\' + nxt))
            index += 2
        else:
            out.append(ch)
            index += 1
    return ''.join(out)


def _format_number(raw: str) -> str:
    raw = (raw or '').strip()
    if re.match(r'^[+-]?\d+$', raw):
        return str(int(raw))
    try:
        value = float(raw)
    except ValueError:
        return raw
    if value == int(value) and abs(value) < 1e15:
        return str(int(value))
    return repr(value)


class _Workbook:
    """An .xlsx read and changed directly in its XML parts (everything not touched stays byte for
    byte as it was)."""

    def __init__(self, data: bytes):
        from lxml import etree
        self.etree = etree
        self.data = data
        self.zip = zipfile.ZipFile(io.BytesIO(data))
        self.names = self.zip.namelist()
        self.changed = {}         # part name -> new bytes
        self.removed = set()
        self.workbook_path = self._workbook_path()
        self.workbook = self._xml(self.workbook_path)
        self.rels_path = self._rels_path(self.workbook_path)
        self.rels = self._xml(self.rels_path)
        self.shared = self._shared_strings()
        self.date_styles, self.date_1904 = self._date_styles()
        self.sheets = []          # (name, part path)
        targets = {rel.get('Id'): rel.get('Target') for rel in self.rels}
        for sheet in self.workbook.iter(_s('sheet')):
            target = targets.get(sheet.get('{%s}id' % _R), '')
            if not target:
                continue
            path = target.lstrip('/') if target.startswith('/') else os.path.normpath(
                os.path.join(os.path.dirname(self.workbook_path), target)).replace(os.sep, '/')
            if path in self.names and '/worksheets/' in '/' + path:
                self.sheets.append((sheet.get('name') or '', path))
        self._sheet_xml = {}

    def _xml(self, name: str):
        return self.etree.fromstring(self.zip.read(name))

    def _workbook_path(self) -> str:
        try:
            for rel in self._xml('_rels/.rels'):
                if str(rel.get('Type', '')).endswith('/officeDocument'):
                    return rel.get('Target').lstrip('/')
        except KeyError:
            pass
        return 'xl/workbook.xml'

    @staticmethod
    def _rels_path(part: str) -> str:
        return '%s/_rels/%s.rels' % (os.path.dirname(part), os.path.basename(part))

    def _shared_strings(self) -> list:
        name = next((n for n in self.names if n.lower().endswith('sharedstrings.xml')), None)
        if not name:
            return []
        strings = []
        for item in self._xml(name).iter(_s('si')):
            strings.append(''.join(node.text or '' for node in item.iter(_s('t'))
                                   if node.getparent().tag != _s('rPh')))
        return strings

    def _date_styles(self) -> tuple:
        date_1904 = False
        props = self.workbook.find(_s('workbookPr'))
        if props is not None and props.get('date1904') in ('1', 'true'):
            date_1904 = True
        styles = set()
        name = next((n for n in self.names if n.lower().endswith('xl/styles.xml')), None)
        if not name:
            return styles, date_1904
        try:
            from openpyxl.styles.numbers import BUILTIN_FORMATS, is_date_format
        except Exception:
            return styles, date_1904
        root = self._xml(name)
        custom = {}
        for fmt in root.iter(_s('numFmt')):
            custom[fmt.get('numFmtId')] = fmt.get('formatCode') or ''
        cell_formats = root.find(_s('cellXfs'))
        if cell_formats is None:
            return styles, date_1904
        for index, xf in enumerate(cell_formats.findall(_s('xf'))):
            fmt_id = xf.get('numFmtId') or '0'
            code = custom.get(fmt_id)
            if code is None:
                try:
                    code = BUILTIN_FORMATS.get(int(fmt_id), '')
                except ValueError:
                    code = ''
            try:
                if code and is_date_format(code):
                    styles.add(str(index))
            except Exception:
                pass
        return styles, date_1904

    def sheet(self, path: str):
        if path not in self._sheet_xml:
            self._sheet_xml[path] = self._xml(path)
        return self._sheet_xml[path]

    # reading
    def _date_text(self, raw: str) -> str:
        from openpyxl.utils.datetime import CALENDAR_MAC_1904, CALENDAR_WINDOWS_1900, from_excel
        value = from_excel(float(raw), CALENDAR_MAC_1904 if self.date_1904 else CALENDAR_WINDOWS_1900)
        if isinstance(value, datetime.datetime):
            if value.hour == value.minute == value.second == 0:
                return value.strftime('%Y-%m-%d')
            return value.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(value, datetime.date):
            return value.strftime('%Y-%m-%d')
        return str(value)

    def cell_content(self, cell, shared_formulas: dict) -> str:
        """The content of a c element as written in the text view ('' for an empty cell)."""
        formula = cell.find(_s('f'))
        if formula is not None:
            text = formula.text or ''
            if formula.get('t') == 'shared':
                index = formula.get('si')
                if text:
                    shared_formulas[index] = (text, cell.get('r'))
                elif index in shared_formulas:
                    master, origin = shared_formulas[index]
                    try:
                        from openpyxl.formula.translate import Translator
                        text = Translator('=' + master, origin=origin).translate_formula(cell.get('r'))[1:]
                    except Exception:
                        text = master
            return '=' + text
        kind = cell.get('t') or 'n'
        value = cell.find(_s('v'))
        raw = value.text if value is not None and value.text is not None else ''
        if kind == 'inlineStr':
            inline = cell.find(_s('is'))
            text = ''.join(node.text or '' for node in inline.iter(_s('t'))) if inline is not None else ''
        elif kind == 's':
            try:
                text = self.shared[int(raw)]
            except (ValueError, IndexError):
                text = ''
        elif kind == 'str':
            text = raw
        elif kind == 'b':
            return 'TRUE' if raw.strip() in ('1', 'true') else 'FALSE'
        elif kind == 'e':
            return raw
        else:
            if raw == '':
                return ''
            if cell.get('s') in self.date_styles:
                try:
                    return self._date_text(raw)
                except Exception:
                    pass
            return _format_number(raw)
        if text == '':
            return ''
        escaped = _escape_cell_text(text)
        return ("'" + escaped) if _looks_special(escaped) else escaped

    def sheet_cells(self, path: str) -> dict:
        """{(row, column): (address, content)} of the filled cells of a sheet."""
        cells, shared_formulas = {}, {}
        data = self.sheet(path).find(_s('sheetData'))
        if data is None:
            return cells
        for row in data.findall(_s('row')):
            for cell in row.findall(_s('c')):
                address = cell.get('r')
                content = self.cell_content(cell, shared_formulas)
                if content != '':
                    cells[_split_address(address)] = (address.replace('$', ''), content)
        return cells

    def text(self) -> str:
        lines = []
        for name, path in self.sheets:
            lines.append('## Sheet: ' + name)
            cells = self.sheet_cells(path)
            for key in sorted(cells):
                lines.append('%s: %s' % cells[key])
        return '\n'.join(lines)

    # writing
    def set_cell(self, path: str, address: str, content: str) -> None:
        """content: as in the text view; '' empties the cell."""
        root = self.sheet(path)
        data = root.find(_s('sheetData'))
        if data is None:
            raise OfficeTextError('a sheet without cell data cannot be edited as text')
        row_number, column = _split_address(address)
        row = None
        for candidate in data.findall(_s('row')):
            number = int(candidate.get('r') or 0)
            if number == row_number:
                row = candidate
                break
            if number > row_number:
                if content == '':
                    return
                row = data.makeelement(_s('row'), {'r': str(row_number)})
                candidate.addprevious(row)
                break
        if row is None:
            if content == '':
                return
            row = data.makeelement(_s('row'), {'r': str(row_number)})
            data.append(row)
        cell = None
        for candidate in row.findall(_s('c')):
            position = _split_address(candidate.get('r'))[1]
            if position == column:
                cell = candidate
                break
            if position > column:
                if content == '':
                    return
                cell = row.makeelement(_s('c'), {'r': address})
                candidate.addprevious(cell)
                break
        if cell is None:
            if content == '':
                return
            cell = row.makeelement(_s('c'), {'r': address})
            row.append(cell)
        old_formula = cell.find(_s('f'))
        if old_formula is not None and old_formula.get('t') in ('shared', 'array', 'dataTable'):
            if old_formula.get('t') != 'shared' or old_formula.text:
                raise OfficeTextError('%s holds a %s formula that other cells depend on; it cannot be changed as '
                                      'text' % (address, old_formula.get('t')))
        for child in list(cell):
            if child.tag in (_s('f'), _s('v'), _s('is')):
                cell.remove(child)
        cell.attrib.pop('t', None)

        def add(tag, text=None):
            node = cell.makeelement(_s(tag), {})
            if text is not None:
                node.text = text
            # f, v, is come before any extLst
            ext = cell.find(_s('extLst'))
            if ext is not None:
                ext.addprevious(node)
            else:
                cell.append(node)
            return node

        if content == '':
            if not cell.get('s'):
                row.remove(cell)
            return
        if content.startswith('='):
            add('f', content[1:])
            return
        if content in ('TRUE', 'FALSE'):
            cell.set('t', 'b')
            add('v', '1' if content == 'TRUE' else '0')
            return
        if content in _ERRORS:
            cell.set('t', 'e')
            add('v', content)
            return
        if _NUMBER_RE.match(content):
            if cell.get('s') in self.date_styles:
                raise OfficeTextError('%s is a date cell: write a date as YYYY-MM-DD' % address)
            add('v', _format_number(content))
            return
        date = _DATE_RE.match(content)
        if date:
            if cell.get('s') not in self.date_styles:
                raise OfficeTextError('%s is not a date cell: to store "%s" as text write \'%s'
                                      % (address, content, content))
            from openpyxl.utils.datetime import CALENDAR_MAC_1904, CALENDAR_WINDOWS_1900, to_excel
            parts = [int(g) if g else 0 for g in date.groups()]
            try:
                moment = datetime.datetime(*parts)
            except ValueError:
                raise OfficeTextError('%s: "%s" is not a real date' % (address, content))
            serial = to_excel(moment, CALENDAR_MAC_1904 if self.date_1904 else CALENDAR_WINDOWS_1900)
            add('v', _format_number(repr(float(serial))))
            return
        text = content[1:] if content.startswith("'") else content
        if content.startswith("'") and not _looks_special(text):
            raise OfficeTextError('%s: write "%s" without the leading \'' % (address, text[:60]))
        if cell.get('s') in self.date_styles:
            raise OfficeTextError('%s is a date cell: write a date as YYYY-MM-DD' % address)
        cell.set('t', 'inlineStr')
        holder = add('is')
        node = holder.makeelement(_s('t'), {})
        node.text = _unescape_cell_text(text)
        node.set(_XML_SPACE, 'preserve')
        holder.append(node)

    def forget_calculated_values(self) -> None:
        """After a change the stored results of formulas may be wrong: drop them all, drop the
        calculation order list, and ask whoever opens the file to calculate."""
        for _name, path in self.sheets:
            root = self.sheet(path)
            for cell in root.iter(_s('c')):
                if cell.find(_s('f')) is not None:
                    value = cell.find(_s('v'))
                    if value is not None:
                        cell.remove(value)
                    if cell.get('t') in ('str', 'e', 'b', 'n'):
                        cell.attrib.pop('t', None)
        chain = None
        for rel in list(self.rels):
            if str(rel.get('Type', '')).endswith('/calcChain'):
                chain = os.path.normpath(os.path.join(os.path.dirname(self.workbook_path),
                                                      rel.get('Target'))).replace(os.sep, '/')
                self.rels.remove(rel)
        if chain and chain in self.names:
            self.removed.add(chain)
            types = self._xml('[Content_Types].xml')
            for override in list(types):
                if override.get('PartName') == '/' + chain:
                    types.remove(override)
            self.changed['[Content_Types].xml'] = self._bytes(types)
            self.changed[self.rels_path] = self._bytes(self.rels)
        calc = self.workbook.find(_s('calcPr'))
        if calc is None:
            calc = self.workbook.makeelement(_s('calcPr'), {})
            # calcPr comes after definedNames / before oleSize … : put it right after the sheets
            anchor = self.workbook.find(_s('definedNames'))
            if anchor is None:
                anchor = self.workbook.find(_s('externalReferences'))
            if anchor is None:
                anchor = self.workbook.find(_s('sheets'))
            if anchor is not None:
                anchor.addnext(calc)
            else:
                self.workbook.append(calc)
        calc.set('fullCalcOnLoad', '1')
        self.changed[self.workbook_path] = self._bytes(self.workbook)

    def _bytes(self, root) -> bytes:
        return self.etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)

    def save(self) -> bytes:
        for path, root in self._sheet_xml.items():
            if path in self._touched:
                self.changed[path] = self._bytes(root)
        out = io.BytesIO()
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as target:
            for info in self.zip.infolist():
                if info.filename in self.removed:
                    continue
                payload = self.changed.get(info.filename)
                if payload is None:
                    payload = self.zip.read(info.filename)
                fresh = zipfile.ZipInfo(info.filename, date_time=info.date_time)
                fresh.compress_type = info.compress_type
                fresh.external_attr = info.external_attr
                target.writestr(fresh, payload)
        return out.getvalue()

    _touched = ()


def _xlsx_text(data: bytes) -> str:
    return _Workbook(data).text()


def _xlsx_parse(text: str, sheet_names: list) -> tuple:
    """(per-sheet {(row, col): (address, content)}, the tidied text) of a text view."""
    wanted, current, seen = [], None, []
    for number, line in enumerate(text.split('\n')):
        match = _SHEET_RE.match(line)
        if match:
            current = {}
            wanted.append(current)
            seen.append(match.group(1))
            continue
        if current is None:
            if not line.strip():
                continue
            raise OfficeTextError('line %d comes before any "## Sheet: <name>" line' % (number + 1))
        if not line.strip():
            continue        # blank lines are allowed and dropped
        cell = _CELL_LINE_RE.match(line)
        if not cell:
            raise OfficeTextError('line %d is not "<cell>: <content>" (for example "B7: =SUM(B2:B6)"): %r'
                                  % (number + 1, line[:80]))
        address = cell.group(1) + cell.group(2)
        key = (int(cell.group(2)), _column_number(cell.group(1)))
        if key in current:
            raise OfficeTextError('line %d: %s is given twice in sheet "%s"' % (number + 1, address, seen[-1]))
        if cell.group(3) != '':
            current[key] = (address, cell.group(3))
    if seen != sheet_names:
        raise OfficeTextError('the "## Sheet:" lines must stay as they are, in this order: %s (sheets cannot be '
                              'added, removed, renamed or reordered as text)' % ', '.join(sheet_names))
    lines = []
    for name, cells in zip(sheet_names, wanted):
        lines.append('## Sheet: ' + name)
        for key in sorted(cells):
            lines.append('%s: %s' % cells[key])
    return wanted, '\n'.join(lines)


def _xlsx_apply(data: bytes, new_text: str):
    book = _Workbook(data)
    wanted, tidy = _xlsx_parse(new_text, [name for name, _path in book.sheets])
    touched = set()
    for (name, path), cells in zip(book.sheets, wanted):
        current = book.sheet_cells(path)
        for key in sorted(set(current) | set(cells)):
            old = current.get(key)
            new = cells.get(key)
            if old is not None and new is not None and old[1] == new[1]:
                continue
            address = (new or old)[0]
            book.set_cell(path, address, new[1] if new is not None else '')
            touched.add(path)
    if not touched:
        return data, tidy
    book._touched = set(path for _name, path in book.sheets)     # stored results are dropped everywhere
    book.forget_calculated_values()
    return book.save(), tidy


# ── places in the text view ──────────────────────────────────────────────────────────────────
# The editor shows the document itself (in the office component) and keeps this text view beside
# it. These helpers translate between the two: an outline of the text view (the editor's Logic
# Map), "which place of the document is text-view line N" (jump there), and "which text-view lines
# are what the user selected in the document" (so a question to a model can name the place).
_SLIDE_HEAD_RE = re.compile(r'^## Slide (\d+)\s*$')
_SHEET_HEAD_RE = re.compile(r'^## Sheet: (.*)$')
_BOX_LINE_RE = re.compile(r'^\[([^\]]*)\] ?(.*)$', re.DOTALL)
_TOKEN_RE = re.compile(r'\{\{[^{}]*\}\}|<br>')
_A1_RE = re.compile(r'^([A-Z]{0,3})([0-9]{0,7})$')
OUTLINE_LIMIT = 4000


def _short(text: str, limit: int = 60) -> str:
    text = ' '.join(str(text or '').split())
    return text if len(text) <= limit else text[:limit - 1] + '…'


def _plain_piece(line: str) -> str:
    """The longest run of ordinary characters of a text-view line (what a search in the document
    can find): no heading / list mark, no table bars, no {{…}} tokens."""
    line = re.sub(r'^\s{0,3}(#{1,6}\s+|[-*]\s+|\d+[.)]\s+)', '', str(line or ''))
    if line.startswith('|') and line.rstrip().endswith('|'):
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        line = next((c for c in cells if _TOKEN_RE.sub('', c).strip()), '')
    pieces = [p.strip() for p in _TOKEN_RE.split(line)]
    return max(pieces, key=len) if pieces else ''


def _col_number(letters: str) -> int:
    number = 0
    for ch in letters:
        number = number * 26 + (ord(ch) - 64)
    return number


def _range_bounds(text: str):
    """'B2:C5' / 'B2' / 'A:A' / '1:3' -> (col1, row1, col2, row2), None when it is not a range."""
    parts = str(text or '').replace('$', '').upper().split(':')
    if not 1 <= len(parts) <= 2:
        return None
    bounds = []
    for part in parts:
        match = _A1_RE.match(part)
        if not match or not (match.group(1) or match.group(2)):
            return None
        bounds.append((_col_number(match.group(1)) if match.group(1) else 0,
                       int(match.group(2)) if match.group(2) else 0))
    (c1, r1), (c2, r2) = bounds[0], bounds[-1]
    return (min(c1, c2) or 1, min(r1, r2) or 1,
            max(c1, c2) if (c1 and c2) else 10 ** 6, max(r1, r2) if (r1 and r2) else 10 ** 8)


def office_outline(kind: str, text: str) -> list:
    """The document's structure, one entry per part: [{'code_name', 'category', 'line'}] where
    line is a line of the text view (1-based). Word: headings, long paragraphs, tables.
    PowerPoint: one entry per slide (number + title) and its text boxes. Excel: one entry per
    sheet and one per formula (the formula shows which cells it is calculated from)."""
    out, seen = [], set()

    def add(name, category, line):
        name = _short(name, 80)
        if name and name not in seen and len(out) < OUTLINE_LIMIT:
            seen.add(name)
            out.append({'code_name': name, 'category': category, 'line': line})

    lines = str(text or '').split('\n')
    if kind == 'pptx':
        slide, slide_line, first_box, titled, boxes = 0, 0, '', False, []

        def flush():
            if slide:
                add('Slide %d · %s' % (slide, _short(first_box, 50)) if first_box else 'Slide %d' % slide,
                    'Slide', slide_line)
                for name, line in boxes:
                    add('Slide %d · [%s]' % (slide, name), 'Text box', line)
        for number, line in enumerate(lines, 1):
            head = _SLIDE_HEAD_RE.match(line)
            if head:
                flush()
                slide, slide_line, first_box, titled, boxes = int(head.group(1)), number, '', False, []
                continue
            box = _BOX_LINE_RE.match(line) if slide else None
            if box:
                content = _plain_piece(box.group(2))
                is_title = box.group(1).lower().startswith('title')
                if content and (not first_box or (is_title and not titled)):
                    first_box, titled = content, titled or is_title
                if box.group(1) not in [n for n, _l in boxes]:
                    boxes.append((box.group(1), number))
        flush()
        return out
    if kind == 'xlsx':
        sheet = ''
        for number, line in enumerate(lines, 1):
            head = _SHEET_HEAD_RE.match(line)
            if head:
                sheet = head.group(1).strip()
                add(sheet, 'Sheet', number)
                continue
            cell = _CELL_LINE_RE.match(line)
            if cell and cell.group(3).startswith('='):
                add('%s!%s%s %s' % (sheet, cell.group(1), cell.group(2), cell.group(3)), 'Formula', number)
        return out
    # Word
    in_table = False
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        is_row = stripped.startswith('|') and stripped.endswith('|') and len(stripped) > 1
        if is_row:
            if not in_table:
                add('Table · ' + _short(' | '.join(c.strip() for c in stripped.strip('|').split('|')), 60),
                    'Table', number)
            in_table = True
            continue
        in_table = False
        heading = re.match(r'^\s{0,3}#{1,6}\s+(.+?)\s*$', line)
        if heading:
            add(_plain_piece(heading.group(1)) or heading.group(1), 'Heading', number)
        elif len(_plain_piece(line)) > 40:
            add(_plain_piece(line)[:30] + '…', 'Paragraph', number)
    return out


OUTLINE_CATEGORIES = {
    'docx': ['Heading', 'Paragraph', 'Table', 'Person', 'Concept'],
    'pptx': ['Slide', 'Text box', 'Person', 'Concept'],
    'xlsx': ['Sheet', 'Formula', 'Person', 'Concept'],
}


def office_line_target(kind: str, text: str, line: int) -> dict:
    """Where in the document text-view line `line` (1-based) is: {'slide': n} | {'sheet', 'cell'} |
    {'text', 'occurrence'} (Word: a piece of that paragraph and which of its occurrences in the
    document). {} when the line is not a place."""
    lines = str(text or '').split('\n')
    index = max(1, int(line or 1)) - 1
    if index >= len(lines):
        return {}
    if kind == 'pptx':
        for back in range(index, -1, -1):
            head = _SLIDE_HEAD_RE.match(lines[back])
            if head:
                return {'slide': int(head.group(1))}
        return {}
    if kind == 'xlsx':
        cell = _CELL_LINE_RE.match(lines[index])
        for back in range(index, -1, -1):
            head = _SHEET_HEAD_RE.match(lines[back])
            if head:
                return {'sheet': head.group(1).strip(),
                        'cell': (cell.group(1) + cell.group(2)) if cell else 'A1'}
        return {}
    piece = _plain_piece(lines[index])[:60].strip()
    if not piece:
        return {}
    earlier = sum(_TOKEN_RE.sub('', earlier_line).count(piece) for earlier_line in lines[:index])
    return {'text': piece, 'occurrence': earlier + 1}


def office_selection_lines(kind: str, text: str, selection: dict) -> list:
    """The text-view lines (1-based, ascending) that hold what is selected in the document.
    selection: what the editing component reports — {'text', 'page', 'sheet', 'range'}.
    PowerPoint without selected text: the whole current slide. [] when it cannot be told."""
    selection = selection if isinstance(selection, dict) else {}
    lines = str(text or '').split('\n')
    picked = [p.strip() for p in re.split(r'[\r\n\t]+', str(selection.get('text') or '')) if len(p.strip()) >= 2]
    if kind == 'xlsx':
        bounds = _range_bounds(selection.get('range') or selection.get('cell') or '')
        wanted = str(selection.get('sheet') or '').strip()
        if not bounds or not wanted:
            return []
        out, sheet = [], None
        for number, line in enumerate(lines, 1):
            head = _SHEET_HEAD_RE.match(line)
            if head:
                sheet = head.group(1).strip()
                continue
            cell = _CELL_LINE_RE.match(line) if sheet == wanted else None
            if cell and bounds[0] <= _col_number(cell.group(1)) <= bounds[2] \
                    and bounds[1] <= int(cell.group(2)) <= bounds[3]:
                out.append(number)
                if len(out) >= 400:
                    break
        return out
    first, last = 1, len(lines)
    if kind == 'pptx':
        try:
            wanted = int(selection.get('page') or 0)
        except (TypeError, ValueError):
            wanted = 0
        first = last = 0
        for number, line in enumerate(lines, 1):
            head = _SLIDE_HEAD_RE.match(line)
            if head and first:
                break
            if head and int(head.group(1)) == wanted:
                first = number
            if first:
                last = number
        if not first:
            return []
        if not picked:
            return list(range(first, last + 1))
    if not picked:
        return []
    out = []
    for number in range(first, last + 1):
        plain = _TOKEN_RE.sub('', lines[number - 1])
        if plain.strip() and any(p in plain or (len(plain.strip()) >= 6 and plain.strip() in p) for p in picked):
            out.append(number)
    if kind == 'docx' and out:
        # the same words may stand elsewhere too: keep the first unbroken run of lines
        run = [out[0]]
        for number in out[1:]:
            if number - run[-1] > 2:
                break
            run.append(number)
        out = run
    if kind == 'pptx' and not out:
        return list(range(first, last + 1))
    return out


# ── what a document looks like (for a model that changes it by script) ───────────────────────
# The text view holds the words. A script changes everything else too — pictures, shapes,
# positions, fills, charts, page setup — so a model needs to know what is there: a short list
# read from the file itself (independent of the editing component).
_FIELD_TEXT_RE = re.compile(rb'(<a:fld\b[^>]*>.*?<a:t>)[^<]*(</a:t>)', re.DOTALL)
LAYOUT_LIMIT = 60000


def office_package_changes(before: bytes, after: bytes) -> list:
    """The parts (inner files) that differ between two saved documents, ignoring what changes
    by itself between two saves of the same document: the properties part (times) and the shown
    value of fields such as the slide number."""
    def parts(data):
        with zipfile.ZipFile(io.BytesIO(data)) as package:
            return {name: _FIELD_TEXT_RE.sub(rb'\1\2', package.read(name))
                    for name in package.namelist() if not name.startswith('docProps/')}
    try:
        old, new = parts(before), parts(after)
    except Exception:
        return ['?']
    return sorted(name for name in set(old) | set(new) if old.get(name) != new.get(name))


def _mm(emu) -> str:
    try:
        return '%.1f' % (int(emu) / 36000.0)
    except (TypeError, ValueError):
        return '?'


def _pptx_layout(data: bytes, page) -> str:
    import pptx
    from pptx.util import Emu
    deck = pptx.Presentation(io.BytesIO(data))
    slides = list(deck.slides)
    lines = ['Presentation: %d slides, slide size %d x %d EMU (%s x %s mm). Positions and sizes below are '
             'x, y, width, height in EMU (36000 EMU = 1 mm), measured from the slide\'s top left corner.'
             % (len(slides), deck.slide_width, deck.slide_height, _mm(deck.slide_width), _mm(deck.slide_height))]
    wanted = range(len(slides))
    if page:
        if not 1 <= int(page) <= len(slides):
            return lines[0] + '\nThere is no slide %s.' % page
        wanted = [int(page) - 1]

    def describe(shape, depth, counter):
        try:
            kind = str(shape.shape_type).split('.')[-1].split(' ')[0].lower() if shape.shape_type is not None else 'shape'
        except Exception:
            kind = 'shape'
        extra = []
        try:
            if shape.is_placeholder:
                extra.append('placeholder ' + str(shape.placeholder_format.type).split('.')[-1].split(' ')[0].lower())
        except Exception:
            pass
        try:
            if getattr(shape, 'has_chart', False) and shape.has_chart:
                kind = 'chart'
                extra.append(str(shape.chart.chart_type).split('.')[-1].split(' ')[0].lower())
            elif getattr(shape, 'has_table', False) and shape.has_table:
                kind = 'table'
                extra.append('%d rows x %d columns' % (len(shape.table.rows), len(shape.table.columns)))
            elif kind == 'picture':
                extra.append('%s, %d bytes' % (shape.image.content_type, len(shape.image.blob)))
            elif getattr(shape, 'has_text_frame', False) and shape.has_text_frame and shape.text_frame.text.strip():
                extra.append('text “%s”' % _short(shape.text_frame.text, 50))
        except Exception:
            pass
        try:
            if shape.rotation:
                extra.append('rotated %g°' % shape.rotation)
        except Exception:
            pass
        box = ', '.join(str(int(v)) if v is not None else '?' for v in (shape.left, shape.top, shape.width, shape.height))
        index = ''
        if depth == 0:
            index = '%d. ' % counter[0]
            counter[0] += 1
        lines.append('%s- %s[%s] %s — at %s%s' % ('  ' * (depth + 1), index, shape.name, kind, box,
                                                  ('; ' + '; '.join(extra)) if extra else ''))
        if kind == 'group' and hasattr(shape, 'shapes'):
            for inner in shape.shapes:
                describe(inner, depth + 1, counter)

    for index in wanted:
        slide = slides[index]
        try:
            background = 'its own background' if slide._element.find(
                './/{http://schemas.openxmlformats.org/presentationml/2006/main}bg') is not None else 'background from its layout'
        except Exception:
            background = ''
        lines.append('Slide %d — layout “%s”, %s. Its objects, back to front (the number is the index in '
                     'slide.GetAllDrawings()):' % (index + 1, slide.slide_layout.name, background))
        counter = [0]
        for shape in slide.shapes:
            describe(shape, 0, counter)
        if counter[0] == 0:
            lines.append('  (no objects)')
        if sum(len(line) for line in lines) > LAYOUT_LIMIT:
            lines.append('… (cut here; ask for one slide with "page")')
            break
    return '\n'.join(lines)


def _docx_layout(data: bytes) -> str:
    import docx
    document = docx.Document(io.BytesIO(data))
    lines = []
    for number, section in enumerate(document.sections, 1):
        try:
            orientation = 'landscape' if (section.page_width or 0) > (section.page_height or 0) else 'portrait'
            lines.append('Section %d: page %s x %s mm (%s), margins top %s / right %s / bottom %s / left %s mm.' % (
                number, _mm(section.page_width), _mm(section.page_height), orientation,
                _mm(section.top_margin), _mm(section.right_margin), _mm(section.bottom_margin), _mm(section.left_margin)))
            head = ' '.join(p.text for p in section.header.paragraphs).strip()
            foot = ' '.join(p.text for p in section.footer.paragraphs).strip()
            if head or foot:
                lines.append('  header: “%s”; footer: “%s”' % (_short(head, 60), _short(foot, 60)))
        except Exception:
            continue
    body = document.element.body
    lines.append('Body elements in order (the number is the index for Api.GetDocument().GetElement(i)):')
    count = 0
    for element in body.iterchildren():
        tag = element.tag.split('}')[-1]
        if tag == 'p':
            text = ''.join(node.text or '' for node in element.iter(_w('t')))
            style = element.find('%s/%s' % (_w('pPr'), _w('pStyle')))
            pictures = len(list(element.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}blip')))
            drawings = len(list(element.iter(_w('drawing'))))
            notes = []
            if style is not None:
                notes.append('style ' + str(style.get(_w('val'))))
            if pictures:
                notes.append('%d picture(s)' % pictures)
            elif drawings:
                notes.append('%d drawing(s)' % drawings)
            lines.append('  - %d. paragraph%s: “%s”' % (count, (' (' + ', '.join(notes) + ')') if notes else '', _short(text, 60)))
        elif tag == 'tbl':
            rows = element.findall(_w('tr'))
            cells = max((len(row.findall(_w('tc'))) for row in rows), default=0)
            lines.append('  - %d. table: %d rows x %d columns' % (count, len(rows), cells))
        else:
            continue
        count += 1
        if count >= 400 or sum(len(line) for line in lines) > LAYOUT_LIMIT:
            lines.append('  … (more elements follow)')
            break
    return '\n'.join(lines)


def _xlsx_layout(data: bytes, page) -> str:
    import openpyxl
    if len(data) > 30 * 1024 * 1024:
        return 'The workbook is too large to list here; ask the document with a reading script instead.'
    book = openpyxl.load_workbook(io.BytesIO(data))
    lines = ['Workbook: %d sheet(s): %s. Active sheet: %s.' % (
        len(book.sheetnames), ', '.join('“%s”' % name for name in book.sheetnames), book.active.title if book.active else '?')]
    for number, sheet in enumerate(book.worksheets, 1):
        if page and int(page) != number:
            continue
        if not hasattr(sheet, 'dimensions'):
            lines.append('Sheet %d “%s”: a chart sheet.' % (number, sheet.title))
            continue
        lines.append('Sheet %d “%s”: used range %s.' % (number, sheet.title, sheet.dimensions))
        merged = [str(r) for r in sheet.merged_cells.ranges]
        if merged:
            lines.append('  merged cells: %s%s' % (', '.join(merged[:20]), ' …' if len(merged) > 20 else ''))
        if sheet.freeze_panes:
            lines.append('  panes frozen at %s' % sheet.freeze_panes)
        widths = ['%s=%g' % (letter, dim.width) for letter, dim in sorted(sheet.column_dimensions.items())
                  if dim.width and getattr(dim, 'customWidth', True)]
        if widths:
            lines.append('  column widths set: %s%s' % (', '.join(widths[:20]), ' …' if len(widths) > 20 else ''))
        charts = getattr(sheet, '_charts', []) or []
        images = getattr(sheet, '_images', []) or []
        if charts:
            lines.append('  %d chart(s): %s' % (len(charts), ', '.join(type(c).__name__ for c in charts[:10])))
        if images:
            lines.append('  %d picture(s)' % len(images))
        tables = list(getattr(sheet, 'tables', {}).values())
        if tables:
            lines.append('  table(s): %s' % ', '.join('%s %s' % (t.displayName, t.ref) for t in tables[:10]))
        if sheet.conditional_formatting:
            lines.append('  has conditional formatting')
    names = []
    try:
        names = list(book.defined_names.keys())
    except Exception:
        pass
    if names:
        lines.append('Defined names: %s' % ', '.join(names[:30]))
    return '\n'.join(lines)[:LAYOUT_LIMIT]


def office_layout(data: bytes, kind: str, page=None) -> str:
    """What is in the document besides its words, as a short list for a model: slides and the
    objects on them (name, kind, position, size), a Word file's page setup and body elements,
    a workbook's sheets (used range, merged cells, charts, pictures). page: one slide / sheet
    (1-based) instead of all."""
    try:
        page = int(page) if page not in (None, '', 0) else None
    except (TypeError, ValueError):
        page = None
    try:
        if kind == 'pptx':
            return _pptx_layout(data, page)
        if kind == 'docx':
            return _docx_layout(data)
        if kind == 'xlsx':
            return _xlsx_layout(data, page)
    except Exception as exc:
        return 'The layout of this document could not be read (%s).' % exc
    return ''
