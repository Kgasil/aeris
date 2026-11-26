"""Bounded, read-only inspection of selected metadata; not a file validator."""
from dataclasses import dataclass
import os
import stat
import struct
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from aeris.verify import _local_path, _open_read, _matches_path, _unchanged, Cancelled

MAX_FILE = 32 * 1024 * 1024
MAX_XML = 128 * 1024
MAX_SEGMENTS = 4096
MAX_FIELDS = 40

@dataclass(frozen=True)
class MetadataResult:
    format: str
    fields: tuple[tuple[str, str], ...]
    notes: tuple[str, ...]


def visible(value):
    return ''.join(c if unicodedata.category(c)[0] != 'C' else ' ' for c in value[:500]).strip()


def add(fields, key, value):
    if len(fields) < MAX_FIELDS:
        fields.append((visible(str(key)), visible(str(value))))


def read_exact(f, n):
    data = f.read(n)
    if len(data) != n: raise ValueError('Estrutura incompleta.')
    return data


def png(f, size, check):
    fields=[]; notes=[]; f.seek(8)
    for i in range(MAX_SEGMENTS):
        check(); n, kind = struct.unpack('>I4s',read_exact(f,8))
        if n > size-f.tell()-4: raise ValueError('Bloco PNG fora dos limites.')
        if i == 0:
            if kind != b'IHDR' or n != 13: raise ValueError('Cabeçalho PNG inválido.')
            w,h=struct.unpack('>II',read_exact(f,n)[:8]); add(fields,'Dimensões',f'{w} × {h}')
        elif kind == b'tEXt' and n <= 8192:
            data=read_exact(f,n); key,sep,value=data.partition(b'\0')
            if sep: add(fields,'Texto PNG: '+key.decode('latin1'),value.decode('latin1'))
        elif kind in (b'zTXt',b'iTXt',b'eXIf',b'tEXt'):
            if 'Blocos de metadados adicionais presentes, não decodificados.' not in notes: notes.append('Blocos de metadados adicionais presentes, não decodificados.')
            f.seek(n,1)
        else: f.seek(n,1)
        read_exact(f,4) # CRC is not validated; this is not a PNG validator.
        if kind == b'IEND':
            if n != 0: raise ValueError('Final PNG inválido.')
            return MetadataResult('PNG',tuple(fields),tuple(notes))
    raise ValueError('Limite de blocos PNG excedido.')


def exif(data, fields, notes):
    t=data[6:]; order={b'II':'<',b'MM':'>'}.get(t[:2])
    if not order or len(t)<8: raise ValueError('EXIF inválido.')
    def u16(off): return struct.unpack_from(order+'H',t,off)[0]
    def u32(off): return struct.unpack_from(order+'I',t,off)[0]
    if u16(2)!=42: raise ValueError('EXIF inválido.')
    seen=set()
    tags={0x010f:'Fabricante',0x0110:'Modelo do dispositivo',0x0131:'Software',0x0132:'Data/hora',0x013b:'Autor',0x010e:'Descrição',0x9003:'Data/hora original',0xa430:'Proprietário da câmera',0xa431:'Número de série do corpo',0xa435:'Número de série da lente'}
    def directory(off, depth=0):
        if off<8 or off in seen or depth>1: raise ValueError('Diretório EXIF inválido.')
        seen.add(off); count=u16(off)
        if count>256 or off+2+12*count+4>len(t): raise ValueError('Diretório EXIF fora dos limites.')
        for i in range(count):
            p=off+2+i*12; tag,typ,num=struct.unpack_from(order+'HHI',t,p)
            if tag==0x8825:
                if 'Referência a diretório GPS presente; coordenadas não decodificadas.' not in notes: notes.append('Referência a diretório GPS presente; coordenadas não decodificadas.')
            elif tag==0x8769 and typ==4 and num==1 and depth==0: directory(u32(p+8),1)
            elif tag in tags and typ==2 and 0<num<=4096:
                pos=p+8 if num<=4 else u32(p+8)
                if pos+num>len(t): raise ValueError('Valor EXIF fora dos limites.')
                add(fields,tags[tag],t[pos:pos+num].split(b'\0',1)[0].decode('ascii','replace'))
    directory(u32(4))


def jpeg(f,size,check):
    fields=[]; notes=[]; f.seek(2)
    for _ in range(MAX_SEGMENTS):
        check()
        if read_exact(f,1)!=b'\xff': raise ValueError('Marcador JPEG inválido.')
        marker=read_exact(f,1)[0]
        # Bound fill bytes independently.
        for _ in range(256):
            if marker!=255: break
            marker=read_exact(f,1)[0]
        if marker in (0xda,0xd9): return MetadataResult('JPEG',tuple(fields),tuple(notes))
        if marker in (0,255,0xd8) or 0xd0<=marker<=0xd7: raise ValueError('Marcador JPEG inesperado.')
        n=struct.unpack('>H',read_exact(f,2))[0]-2
        if n<0 or n>size-f.tell(): raise ValueError('Segmento JPEG fora dos limites.')
        if marker in (0xe1,0xfe) or marker in (0xc0,0xc1,0xc2,0xc3,0xc5,0xc6,0xc7,0xc9,0xca,0xcb,0xcd,0xce,0xcf):
            data=read_exact(f,n)
            if marker==0xe1:
                if data.startswith(b'Exif\0\0'):
                    try: exif(data,fields,notes)
                    except (ValueError,struct.error):
                        if 'EXIF parcialmente inválido ou não suportado.' not in notes: notes.append('EXIF parcialmente inválido ou não suportado.')
                elif 'Segmento APP1 adicional não decodificado.' not in notes: notes.append('Segmento APP1 adicional não decodificado.')
            elif marker==0xfe: add(fields,'Comentário JPEG',data[:500].decode('latin1'))
            elif len(data)>=5:
                h,w=struct.unpack('>HH',data[1:5]); add(fields,'Dimensões',f'{w} × {h}')
        else: f.seek(n,1)
    raise ValueError('Limite de segmentos JPEG excedido.')


def office(f,check):
    fields=[]; notes=[]
    # Preflight the ordinary ZIP end record, before allocating its directory.
    size=f.seek(0,2); f.seek(max(0,size-65557)); tail=f.read(65557)
    pos=tail.rfind(b'PK\x05\x06')
    if pos<0 or len(tail)-pos<22: raise ValueError('Final ZIP inválido.')
    disk,cd_disk,disk_count,count,cd_size,cd_offset,comment=struct.unpack_from('<4H2IH',tail,pos+4)
    if disk or cd_disk or disk_count!=count or count>10000 or cd_size>2*1024*1024 or cd_offset+cd_size!=size-len(tail)+pos or pos+22+comment!=len(tail):
        raise ValueError('Diretório ZIP fora dos limites ou formato não suportado (incluindo ZIP64).')
    f.seek(0)
    with zipfile.ZipFile(f) as z:
        check(); entries=z.infolist()
        if len(entries)>10000: raise ValueError('Muitas entradas no pacote.')
        names=[e.filename for e in entries]
        formats=[name for name,entry in [('DOCX','word/document.xml'),('XLSX','xl/workbook.xml'),('PPTX','ppt/presentation.xml')] if entry in names]
        if len(formats)!=1 or '[Content_Types].xml' not in names: raise ValueError('Pacote Office não reconhecido.')
        if names.count('docProps/core.xml')>1: raise ValueError('Metadados duplicados no pacote.')
        if 'docProps/core.xml' not in names: return MetadataResult(formats[0],(),('Propriedades principais ausentes.',))
        entry=z.getinfo('docProps/core.xml')
        if entry.file_size>MAX_XML or entry.flag_bits&1: raise ValueError('Metadados Office excedem limite ou estão criptografados.')
        with z.open(entry) as stream: data=stream.read(MAX_XML+1)
        if len(data)>MAX_XML: raise ValueError('Metadados Office excedem limite.')
        check(); text=data.decode('utf-8-sig')
        if '\0' in text or '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper(): raise ValueError('XML com declarações não permitidas.')
        root=ET.fromstring(text)
        cp='http://schemas.openxmlformats.org/package/2006/metadata/core-properties'; dc='http://purl.org/dc/elements/1.1/'; dt='http://purl.org/dc/terms/'
        tags={f'{{{dc}}}creator':'Autor',f'{{{dc}}}title':'Título',f'{{{dc}}}subject':'Assunto',f'{{{dc}}}description':'Descrição',f'{{{cp}}}lastModifiedBy':'Última edição por',f'{{{cp}}}keywords':'Palavras-chave',f'{{{dt}}}created':'Criação',f'{{{dt}}}modified':'Modificação'}
        if root.tag!=f'{{{cp}}}coreProperties': raise ValueError('XML de propriedades não reconhecido.')
        for child in root:
            if child.tag in tags: add(fields,tags[child.tag],child.text or '')
        return MetadataResult(formats[0],tuple(fields),tuple(notes))


def inspect_file(path, *, cancelled=lambda:False):
    def check():
        if cancelled(): raise Cancelled()
    check(); p=_local_path(path); pre=p.lstat()
    if not stat.S_ISREG(pre.st_mode) or getattr(pre,'st_file_attributes',0)&0x400: raise ValueError('Somente arquivos regulares locais.')
    if pre.st_size>MAX_FILE: raise ValueError('Limite de 32 MiB para inspeção.')
    flags=os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NONBLOCK',0)|getattr(os,'O_NOFOLLOW',0)
    with os.fdopen(_open_read(p),'rb') as f:
        initial=os.fstat(f.fileno())
        if not _matches_path(p, pre, f, initial): raise ValueError('Arquivo alterado antes da leitura.')
        magic=f.read(8)
        try:
            if magic==b'\x89PNG\r\n\x1a\n': result=png(f,initial.st_size,check)
            elif magic.startswith(b'\xff\xd8'): result=jpeg(f,initial.st_size,check)
            elif magic.startswith(b'PK\x03\x04'): result=office(f,check)
            else: raise ValueError('Formato não suportado.')
        except (struct.error,zipfile.BadZipFile,ET.ParseError,UnicodeError,NotImplementedError,RuntimeError) as exc:
            raise ValueError('Metadados inválidos ou não suportados.') from exc
        check()
        if not _unchanged(p, pre, f, initial): raise ValueError('Arquivo alterado durante a inspeção.')
    return result
