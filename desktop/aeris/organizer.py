"""Bounded, read-only inventory of one explicitly selected directory."""
from dataclasses import dataclass
import os
from pathlib import Path
import stat
from aeris.verify import _local_path, Cancelled

MAX_ENTRIES = 2000
CATEGORIES = {
    'Documentos': {'.txt','.md','.pdf','.doc','.docx','.rtf','.odt','.ppt','.pptx','.odp'},
    'Imagens': {'.jpg','.jpeg','.png','.gif','.webp','.bmp','.tif','.tiff','.svg','.heic'},
    'Planilhas e dados': {'.csv','.xlsx','.xls','.ods','.tsv','.json','.parquet'},
    'Compactados': {'.zip','.rar','.7z','.tar','.gz','.bz2','.xz'},
    'Áudio e vídeo': {'.mp3','.wav','.flac','.m4a','.ogg','.mp4','.mov','.mkv','.avi','.webm'},
    'Código': {'.py','.js','.ts','.html','.css','.sql','.java','.rs','.c','.cpp','.ps1','.bat'},
}

def category(name):
    suffix=Path(name).suffix.casefold()
    return next((label for label, extensions in CATEGORIES.items() if suffix in extensions),'Outros')

def safe_name(name):
    # Represent control/format characters visibly; do not reinterpret as paths.
    import unicodedata
    return ''.join(f'\\u{ord(c):04x}' if unicodedata.category(c).startswith('C') else c for c in name)

@dataclass(frozen=True)
class Entry:
    name: str
    category: str
    size: int

@dataclass(frozen=True)
class Inventory:
    files: tuple[Entry,...]
    skipped: int
    truncated: bool
    @property
    def totals(self):
        totals={}
        for item in self.files:
            count,size=totals.get(item.category,(0,0))
            totals[item.category]=(count+1,size+item.size)
        return tuple((key,*totals[key]) for key in (*CATEGORIES,'Outros') if key in totals)

def scan_folder(path, *, cancelled=lambda:False):
    if cancelled(): raise Cancelled()
    p=_local_path(path)
    if not p.is_absolute(): raise ValueError('Selecione uma pasta absoluta em disco local.')
    for part in (*reversed(p.parents),p):
        st=part.lstat()
        if not stat.S_ISDIR(st.st_mode) or getattr(st,'st_file_attributes',0)&0x400:
            raise ValueError('Somente pastas regulares, sem links ou pontos de nova análise.')
    files=[]; skipped=0; truncated=False
    with os.scandir(p) as entries:
        for i,entry in enumerate(entries):
            if cancelled(): raise Cancelled()
            if i>=MAX_ENTRIES:
                truncated=True; break
            try: st=entry.stat(follow_symlinks=False)
            except OSError: skipped+=1; continue
            if not stat.S_ISREG(st.st_mode) or getattr(st,'st_file_attributes',0)&0x400:
                skipped+=1; continue
            files.append(Entry(safe_name(entry.name),category(entry.name),st.st_size))
    if cancelled(): raise Cancelled()
    files.sort(key=lambda e:(e.category,e.name.casefold(),e.name))
    return Inventory(tuple(files),skipped,truncated)
