"""Cofre local: persistência apenas de blob protegido; falhas não apagam dados."""
from dataclasses import asdict, dataclass
from pathlib import Path
import json
import os
import tempfile
from aeris.dpapi import WindowsDPAPI
from aeris.safe_input import bounded_read, strict_json

MAGIC = b'AERIS-VAULT-1\0'
MAX_FILE = 32*1024*1024

@dataclass(frozen=True)
class Entry:
    id: int
    title: str
    body: str

def validate(title, body):
    if type(title) is not str or type(body) is not str or not title.strip() or not body.strip() or len(title)>120 or len(body)>20000:
        raise ValueError('Título e texto obrigatórios (120 e 20.000 caracteres).')

class Vault:
    def __init__(self, path, backend=None):
        self.path = Path(path)
        self.backend = backend if backend is not None else WindowsDPAPI()
        self._entries = None
        self._lease = None

    @property
    def unlocked(self): return self._entries is not None

    def _acquire(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lease = open(self.path.with_suffix('.lock'), 'a+b')
        try:
            if os.name == 'nt':
                import msvcrt
                lease.seek(0); msvcrt.locking(lease.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                # Apenas para testes com backend injetado, não para criptografia real.
                import fcntl
                fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            lease.close(); raise
        self._lease = lease

    def unlock(self):
        if self.unlocked: return
        self._acquire()
        try:
            try:
                raw = bounded_read(self.path, MAX_FILE)
            except FileNotFoundError:
                self._entries = {}; return
            self._entries = self.decode(raw)
        except BaseException:
            self.lock(); raise

    def decode(self, raw):
        if not raw.startswith(MAGIC) or len(raw)>MAX_FILE:
            raise ValueError('Formato de cofre inválido.')
        data = strict_json(self.backend.unprotect(raw[len(MAGIC):]), MAX_FILE)
        if type(data) is not dict or set(data) != {'schema', 'entries'} or type(data['schema']) is not int or data['schema'] != 1 or not isinstance(data.get('entries'), list) or len(data['entries'])>100:
            raise ValueError('Estrutura inválida.')
        entries = {}
        for raw_entry in data['entries']:
            if type(raw_entry) is not dict or set(raw_entry) != {'id','title','body'}:
                raise ValueError('Registro inválido.')
            item = Entry(**raw_entry)
            if type(item.id) is not int or not 1<=item.id<=2**63-1 or item.id in entries:
                raise ValueError('Identificador inválido.')
            validate(item.title, item.body)
            entries[item.id] = item
        return entries

    def lock(self):
        self._entries = None
        if self._lease is not None:
            self._lease.close(); self._lease = None

    def _require(self):
        if not self.unlocked: raise PermissionError('Cofre bloqueado.')
        return self._entries

    def list(self): return tuple(self._require().values())

    def _commit(self, entries):
        self._require()
        data = json.dumps({'schema':1,'entries':[asdict(e) for e in entries.values()]},ensure_ascii=False).encode('utf-8')
        encrypted = MAGIC + self.backend.protect(data)
        if len(encrypted)>MAX_FILE or len(encrypted)<=len(MAGIC): raise ValueError('Cofre excede limite.')
        temp = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.path.parent, prefix='.vault-', delete=False) as f:
                temp = Path(f.name); f.write(encrypted); f.flush(); os.fsync(f.fileno())
            os.replace(temp,self.path)
        finally:
            if temp is not None: temp.unlink(missing_ok=True)
        self._entries = entries

    def save(self,title,body,entry_id=None):
        entries = dict(self._require()); validate(title,body)
        if entry_id is None:
            if len(entries)>=100: raise ValueError('Limite de 100 registros.')
            entry_id = max(entries, default=0)+1
            if entry_id>2**63-1: raise ValueError('Limite de identificadores.')
        elif entry_id not in entries: raise KeyError(entry_id)
        item=Entry(entry_id,title.strip(),body); entries[entry_id]=item
        self._commit(entries); return item

    def delete(self,entry_id):
        entries=dict(self._require()); del entries[entry_id]; self._commit(entries)
