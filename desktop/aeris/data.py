"""Bounded read-only CSV profiling; no formula evaluation or type coercion of source."""
import csv
from dataclasses import dataclass
from decimal import Decimal, localcontext
import io
import os
import re
import stat
from aeris.documents import _decode
from aeris.verify import _local_path, _open_read, _matches_path, _unchanged, Cancelled

MAX_BYTES=1024*1024
MAX_ROWS=5000
MAX_COLUMNS=50
MAX_CELLS=100000
MAX_FIELD=4096
DELIMITERS=(',', ';', '\t')

@dataclass(frozen=True)
class ColumnProfile:
    name: str
    missing: int
    distinct: int
    kind: str
    minimum: Decimal | None
    maximum: Decimal | None
    mean: Decimal | None

@dataclass(frozen=True)
class DataProfile:
    rows: int
    columns: tuple[ColumnProfile,...]
    duplicates: int
    missing: int


def profile_text(text, delimiter=',', decimal_separator='.', *, cancelled=lambda:False):
    def check():
        if cancelled(): raise Cancelled()
    check()
    if delimiter not in DELIMITERS or decimal_separator not in ('.', ','):
        raise ValueError('Separador inválido.')
    if not isinstance(text,str) or len(text)>MAX_BYTES or '\0' in text:
        raise ValueError('Texto inválido ou acima do limite.')
    reader=csv.reader(io.StringIO(text,newline=''),delimiter=delimiter,strict=True)
    try:
        header=next(reader,None)
        if not header or len(header)>MAX_COLUMNS or any(not h.strip() or len(h)>MAX_FIELD for h in header):
            raise ValueError('Cabeçalho obrigatório, com 1 a 50 colunas nomeadas.')
        header=[h.strip() for h in header]
        if len(set(header))!=len(header): raise ValueError('Cabeçalhos duplicados.')
        missing=[0]*len(header); unique=[set() for _ in header]; numeric=[[] for _ in header]; is_numeric=[True]*len(header)
        seen=set(); duplicates=0; count=0
        pattern=re.compile(r'[+-]?(?:[0-9]+(?:'+re.escape(decimal_separator)+r'[0-9]+)?|'+re.escape(decimal_separator)+r'[0-9]+)\Z')
        for row in reader:
            check()
            if len(row)!=len(header): raise ValueError(f'Registro irregular próximo à linha física {reader.line_num}.')
            if any(len(v)>MAX_FIELD for v in row): raise ValueError('Campo excede 4.096 caracteres.')
            count+=1
            if count>MAX_ROWS or count*len(header)>MAX_CELLS: raise ValueError('Limite de linhas ou células excedido; análise descartada.')
            key=tuple(row)
            if key in seen: duplicates+=1
            else: seen.add(key)
            for i,value in enumerate(row):
                trimmed=value.strip()
                if not trimmed: missing[i]+=1; continue
                unique[i].add(value)
                if is_numeric[i]:
                    if len(trimmed)<=32 and pattern.fullmatch(trimmed): numeric[i].append(Decimal(trimmed.replace(decimal_separator,'.')))
                    else: is_numeric[i]=False; numeric[i].clear()
        profiles=[]
        with localcontext() as ctx:
            ctx.prec=40
            for i,name in enumerate(header):
                check(); vals=numeric[i]
                kind='Vazia' if not unique[i] else 'Numérica' if is_numeric[i] else 'Texto/mista'
                profiles.append(ColumnProfile(name,missing[i],len(unique[i]),kind,min(vals) if vals else None,max(vals) if vals else None,sum(vals)/len(vals) if vals else None))
        check(); return DataProfile(count,tuple(profiles),duplicates,sum(missing))
    except csv.Error as exc: raise ValueError('CSV malformado ou campo acima do limite.') from exc


def read_csv_file(path, parser, *, cancelled=lambda:False):
    if cancelled(): raise Cancelled()
    p=_local_path(path)
    if not p.is_absolute() or p.suffix.lower()!='.csv': raise ValueError('Selecione um arquivo CSV local absoluto.')
    for parent in p.parents:
        st=parent.lstat()
        if not stat.S_ISDIR(st.st_mode) or getattr(st,'st_file_attributes',0)&0x400: raise ValueError('Caminho com links não aceito.')
    pre=p.lstat()
    if not stat.S_ISREG(pre.st_mode) or getattr(pre,'st_file_attributes',0)&0x400: raise ValueError('Somente arquivos regulares, sem links.')
    if pre.st_size>MAX_BYTES: raise ValueError('CSV acima de 1 MiB.')
    flags=os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NONBLOCK',0)|getattr(os,'O_NOFOLLOW',0)
    with os.fdopen(_open_read(p),'rb') as stream:
        initial=os.fstat(stream.fileno())
        if not _matches_path(p, pre, stream, initial): raise ValueError('Arquivo alterado antes da leitura.')
        raw=stream.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES: raise ValueError('CSV acima de 1 MiB.')
        if cancelled(): raise Cancelled()
        result=parser(_decode(raw))
        if not _unchanged(p, pre, stream, initial): raise ValueError('Arquivo alterado durante a análise.')
    if cancelled(): raise Cancelled()
    return result


def profile_file(path, delimiter=',', decimal_separator='.', *, cancelled=lambda:False):
    return read_csv_file(path, lambda text: profile_text(text, delimiter, decimal_separator, cancelled=cancelled), cancelled=cancelled)
