"""Optional local OCR, with bounded input and a cancellable external process."""
from dataclasses import dataclass
import io
import os
from pathlib import Path
import stat
import struct
import subprocess
import time
from aeris.verify import _local_path, _open_read, _matches_path, _unchanged, Cancelled
from aeris.metadata import png, jpeg

LANGUAGES = {'Português':'por','English':'eng','Español':'spa'}
MAX_FILE = 8 * 1024 * 1024
MAX_PIXELS = 12_000_000
MAX_TEXT = 100_000
TIMEOUT = 30

@dataclass(frozen=True)
class LensResult:
    text: str
    truncated: bool
    format: str
    width: int
    height: int


def engine_path():
    # Do not search the current directory or arbitrary PATH entries.
    candidates = [Path(os.environ.get('ProgramW6432',os.environ.get('ProgramFiles',r'C:\Program Files')))/'Tesseract-OCR'/'tesseract.exe'] if os.name=='nt' else [Path('/usr/bin/tesseract'),Path('/usr/local/bin/tesseract')]
    for p in candidates:
        if p.is_file(): return p
    raise ValueError('Motor Tesseract opcional não encontrado. Consulte docs/lens.md.')


def read_image(path, check):
    check(); p=_local_path(path); pre=p.lstat()
    if not stat.S_ISREG(pre.st_mode) or getattr(pre,'st_file_attributes',0)&0x400: raise ValueError('Somente imagens regulares locais, sem links.')
    if pre.st_size>MAX_FILE: raise ValueError('Limite de 8 MiB por imagem.')
    flags=os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NONBLOCK',0)|getattr(os,'O_NOFOLLOW',0)
    with os.fdopen(_open_read(p),'rb') as f:
        initial=os.fstat(f.fileno())
        if not _matches_path(p, pre, f, initial): raise ValueError('Imagem alterada antes da leitura.')
        data=f.read(MAX_FILE+1);check()
        if len(data)!=initial.st_size or len(data)>MAX_FILE or not _unchanged(p, pre, f, initial): raise ValueError('Imagem alterada durante a leitura.')
    try:
        if data.startswith(b'\x89PNG\r\n\x1a\n'): result=png(io.BytesIO(data),len(data),check)
        elif data.startswith(b'\xff\xd8'): result=jpeg(io.BytesIO(data),len(data),check)
        else: raise ValueError('Selecione PNG ou JPEG.')
        dims=dict(result.fields).get('Dimensões','').split(' × ')
        w,h=map(int,dims)
    except (ValueError,struct.error) as exc: raise ValueError('Imagem PNG/JPEG inválida ou não suportada.') from exc
    if not 0<w<=12000 or not 0<h<=12000 or w*h>MAX_PIXELS: raise ValueError('Limite de 12 megapixels e 12.000 pixels por dimensão.')
    return data,result.format,w,h


def recognize(path, language, *, cancelled=lambda:False):
    if language not in LANGUAGES: raise ValueError('Idioma não suportado.')
    def check():
        if cancelled(): raise Cancelled()
    check(); exe=engine_path();data,fmt,w,h=read_image(path,check);check()
    env=os.environ.copy();env['OMP_THREAD_LIMIT']='1';env.pop('TESSDATA_PREFIX',None)
    args=[str(exe),'stdin','stdout','-l',LANGUAGES[language],'--psm','3']
    if os.name=='nt':args+=['--tessdata-dir',str(exe.parent/'tessdata')]
    with subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,cwd=exe.parent,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),shell=False) as proc:
        deadline=time.monotonic()+TIMEOUT; payload=data
        try:
            while True:
                check()
                if time.monotonic()>=deadline: raise ValueError('Tempo limite de OCR excedido.')
                try:
                    out,_=proc.communicate(input=payload,timeout=.1);break
                except subprocess.TimeoutExpired:payload=None
            check()
            if proc.returncode:raise ValueError('OCR falhou. Verifique o idioma instalado e a imagem.')
        finally:
            if proc.poll() is None:proc.kill();proc.communicate()
    text=out.decode('utf-8','replace').strip()
    return LensResult(text[:MAX_TEXT],len(text)>MAX_TEXT,fmt,w,h)
