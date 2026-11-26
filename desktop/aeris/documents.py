"""Bounded local text preview, not a document renderer or safety scanner."""
from dataclasses import dataclass
import os
import stat
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from aeris.verify import _local_path, _open_read, _matches_path, _unchanged, Cancelled

MAX_FILE = 8 * 1024 * 1024
MAX_TEXT_BYTES = 1024 * 1024
MAX_XML = 1024 * 1024
MAX_PREVIEW = 100_000
MAX_ENTRIES = 2048
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

@dataclass(frozen=True)
class DocumentResult:
    format: str
    text: str
    truncated: bool
    words: int
    lines: int


def _decode(data):
    encoding = 'utf-16' if data.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig'
    try: text = data.decode(encoding)
    except UnicodeError as exc: raise ValueError('Codificação não suportada; use UTF-8 ou UTF-16 com BOM.') from exc
    if '\0' in text: raise ValueError('Conteúdo binário não suportado.')
    return text


def _docx(stream, check):
    with zipfile.ZipFile(stream) as archive:
        entries = archive.infolist()
        if len(entries) > MAX_ENTRIES: raise ValueError('Pacote com entradas demais.')
        names = [entry.filename for entry in entries]
        if len(set(names)) != len(names) or '[Content_Types].xml' not in names or 'word/document.xml' not in names:
            raise ValueError('Pacote DOCX não reconhecido ou ambíguo.')
        entry = archive.getinfo('word/document.xml')
        if entry.file_size > MAX_XML or entry.flag_bits & 1: raise ValueError('XML principal excede o limite ou está criptografado.')
        if entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED): raise ValueError('Compressão não suportada.')
        check()
        with archive.open(entry) as part: data = part.read(MAX_XML+1)
        if len(data)>MAX_XML: raise ValueError('XML principal excede o limite.')
        text = _decode(data)
        if '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper(): raise ValueError('Declarações XML não permitidas.')
        root = ET.fromstring(text)
        if root.tag != W+'document': raise ValueError('Documento Word não reconhecido.')
        body = root.find(W+'body')
        if body is None: raise ValueError('Corpo do documento ausente.')
        paragraphs=[]
        for paragraph in body.iter(W+'p'):
            check()
            chunks=[]
            # Skip embedded nested paragraphs, which are handled independently.
            stack=list(reversed(list(paragraph)))
            while stack:
                element=stack.pop()
                if element.tag in (W+'p', W+'del', W+'moveFrom'): continue
                if element.tag==W+'t': chunks.append(element.text or '')
                elif element.tag==W+'tab': chunks.append('\t')
                elif element.tag in (W+'br',W+'cr'): chunks.append('\n')
                else: stack.extend(reversed(list(element)))
            paragraphs.append(''.join(chunks))
        return '\n'.join(paragraphs)


def extract_file(path, *, cancelled=lambda:False):
    def check():
        if cancelled(): raise Cancelled()
    check(); p=_local_path(path); ext=p.suffix.lower()
    if ext not in ('.txt','.md','.csv','.docx'): raise ValueError('Formato não suportado nesta versão.')
    pre=p.lstat(); limit=MAX_FILE if ext=='.docx' else MAX_TEXT_BYTES
    if not stat.S_ISREG(pre.st_mode) or getattr(pre,'st_file_attributes',0)&0x400: raise ValueError('Somente arquivos regulares locais, sem links.')
    if pre.st_size>limit: raise ValueError('Arquivo excede o limite de leitura.')
    flags=os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NONBLOCK',0)|getattr(os,'O_NOFOLLOW',0)
    with os.fdopen(_open_read(p),'rb') as stream:
        initial=os.fstat(stream.fileno())
        if not _matches_path(p, pre, stream, initial): raise ValueError('Arquivo alterado antes da leitura.')
        try:
            if ext=='.docx': text=_docx(stream,check)
            else:
                data=stream.read(limit+1)
                if len(data)>limit: raise ValueError('Arquivo excede o limite de leitura.')
                text=_decode(data)
        except (zipfile.BadZipFile, ET.ParseError, UnicodeError, RuntimeError, NotImplementedError) as exc:
            raise ValueError('Documento inválido, criptografado ou não suportado.') from exc
        check()
        if not _unchanged(p, pre, stream, initial): raise ValueError('Arquivo alterado durante a leitura.')
    text=text.replace('\r\n','\n').replace('\r','\n')
    truncated=len(text)>MAX_PREVIEW
    # Render controls visibly rather than interpreting bidi / hidden controls.
    preview=''.join(c if c in '\n\t' or unicodedata.category(c) not in ('Cc','Cf') else '\ufffd' for c in text[:MAX_PREVIEW])
    check()
    return DocumentResult(ext[1:].upper(),preview,truncated,len(preview.split()),len(preview.splitlines()))
