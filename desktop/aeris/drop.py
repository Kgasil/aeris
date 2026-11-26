"""Session-only references; never reads file contents, copies or moves files."""
from dataclasses import dataclass
import os
from pathlib import Path
import stat
from aeris.verify import _local_path, Cancelled
from aeris.organizer import category

MAX_FILES = 100

@dataclass(frozen=True)
class Reference:
    path: str
    size: int
    category: str


def inspect_paths(paths, *, cancelled=lambda:False):
    """Bounded all-or-nothing metadata inspection, rejects links and nonlocal paths."""
    if len(paths)>MAX_FILES: raise ValueError('Selecione até 100 arquivos.')
    results=[]
    for path in paths:
        if cancelled(): raise Cancelled()
        p=_local_path(path)
        if not p.is_absolute() or '..' in p.parts: raise ValueError('Selecione arquivos absolutos em disco local.')
        # Avoid ambiguous clipboard lists and reject directory links on all platforms.
        if any(c in str(p) for c in ('\r','\n','\x00')): raise ValueError('Caminho com caracteres não suportados.')
        for parent in reversed(p.parents):
            st=parent.lstat()
            if not stat.S_ISDIR(st.st_mode) or getattr(st,'st_file_attributes',0)&0x400:
                raise ValueError('Caminhos com links ou pontos de nova análise não são aceitos.')
        st=p.lstat()
        if not stat.S_ISREG(st.st_mode) or getattr(st,'st_file_attributes',0)&0x400:
            raise ValueError('Somente arquivos regulares, sem links ou pontos de nova análise.')
        results.append(Reference(str(p),st.st_size,category(p.name)))
    if cancelled(): raise Cancelled()
    return tuple(results)


class DropStore:
    def __init__(self): self._items={}
    @staticmethod
    def key(path): return os.path.normcase(os.path.normpath(path))
    def list(self): return tuple(self._items.values())
    def add(self, items):
        updated=dict(self._items)
        for item in items: updated[self.key(item.path)]=item
        if len(updated)>MAX_FILES: raise ValueError('Prateleira limitada a 100 arquivos.')
        self._items=updated
    def remove(self, paths):
        for path in paths: self._items.pop(self.key(path),None)
    def clear(self): self._items.clear()
