"""Bounded local backups; encrypted payloads never written in clear text."""
import base64
import hashlib
import json
import os
from contextlib import contextmanager, ExitStack
from dataclasses import asdict
from pathlib import Path
import tempfile
from uuid import uuid4
from aeris.safe_input import bounded_read, strict_json
from aeris.permissions import CREATE_BACKUP, RESTORE_BACKUP
from aeris.settings import Appearance
from aeris.vault import Vault, MAGIC, MAX_FILE
from aeris.bookmarks import validate_fields
from aeris.protected_storage import ProtectedStorage, MODULES, MAGIC as STORAGE_MAGIC, LIMIT as STORAGE_LIMIT

TARGETS = {'Vault': 'vault.bin', 'Bookmarks': 'bookmarks.bin'}
MAX_ARCHIVE = 170 * 1024 * 1024

def parse(raw):
    obj = strict_json(raw, MAX_ARCHIVE)
    if not isinstance(obj, dict) or set(obj) != {'format', 'items'} or obj['format'] != 'AERIS-BACKUP-1' or not isinstance(obj['items'], dict):
        raise ValueError('Formato de backup inválido.')
    items = {}
    for name, entry in obj['items'].items():
        if name not in (*TARGETS, *MODULES, 'Aparência') or not isinstance(entry, dict) or set(entry) != {'data','sha256'}:
            raise ValueError('Item desconhecido.')
        if type(entry['data']) is not str or type(entry['sha256']) is not str:
            raise ValueError('Item inválido.')
        limit = 16384 if name == 'Aparência' else STORAGE_LIMIT if name in MODULES else MAX_FILE
        if len(entry['data']) > 4 * ((limit + 2) // 3): raise ValueError('Item acima do limite.')
        data = base64.b64decode(entry['data'], validate=True)
        if hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError('Falha de integridade SHA-256.')
        if name == 'Aparência':
            if len(data)>16384: raise ValueError('Preferências excedem limite.')
            Appearance(**strict_json(data, 16384))
        elif name in MODULES:
            if not data.startswith(STORAGE_MAGIC) or len(data)>STORAGE_LIMIT: raise ValueError('Cópia protegida inválida.')
        elif not data.startswith(MAGIC) or len(data)>MAX_FILE:
            raise ValueError('Blob protegido inválido.')
        items[name] = data
    if not items: raise ValueError('Backup vazio.')
    return items

def create_exclusive(path, data):
    path = Path(path)
    # Do not delete a pre-existing file if opening fails.
    f = path.open('xb')
    try:
        with f:
            f.write(data); f.flush(); os.fsync(f.fileno())
    except BaseException:
        path.unlink(missing_ok=True); raise

def atomic_replace(path, data):
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.restore-', delete=False) as f:
            temp = Path(f.name); f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if temp is not None: temp.unlink(missing_ok=True)

class BackupService:
    def __init__(self, settings, permissions, backend=None):
        self.settings, self.permissions, self.backend = settings, permissions, backend
        self.folder = settings.path.parent

    @contextmanager
    def lease(self, name):
        # Same lease as the live vault, without unlocking/decrypting for export.
        vault = Vault(self.folder / TARGETS[name], self.backend)
        vault._acquire()
        try: yield vault
        finally: vault.lock()

    def create(self, path):
        self.permissions.require(CREATE_BACKUP)
        path = Path(path)
        if path.suffix.lower() != '.aerisbackup': raise ValueError('Use a extensão .aerisbackup.')
        items = {'Aparência': json.dumps(asdict(self.settings.appearance), ensure_ascii=False).encode('utf-8')}
        with ExitStack() as stack:
            for name, filename in TARGETS.items():
                if not (self.folder / filename).exists(): continue
                vault = stack.enter_context(self.lease(name))
                data = bounded_read(vault.path, MAX_FILE)
                if not data.startswith(MAGIC): raise ValueError('Formato protegido inválido.')
                items[name] = data
            for name in MODULES:
                if not (self.folder / ('storage-'+name.lower()+'.bin')).exists(): continue
                storage=ProtectedStorage(self.folder,self.backend)
                items[name]=storage.export_blob(name)
            raw = json.dumps({'format':'AERIS-BACKUP-1','items':{name:{'data':base64.b64encode(data).decode('ascii'),'sha256':hashlib.sha256(data).hexdigest()} for name,data in items.items()}}).encode('utf-8')
            if len(raw)>MAX_ARCHIVE: raise ValueError('Backup excede o limite.')
            self.permissions.require(CREATE_BACKUP)
            create_exclusive(path, raw)
        return tuple(items)

    def inspect(self, path):
        return self.inspect_with_digest(path)[0]

    def inspect_with_digest(self, path):
        self.permissions.require(RESTORE_BACKUP)
        raw = bounded_read(path, MAX_ARCHIVE)
        return tuple(parse(raw)), hashlib.sha256(raw).hexdigest()

    def restore(self, path, name, expected_digest=None):
        self.permissions.require(RESTORE_BACKUP)
        raw = bounded_read(path, MAX_ARCHIVE)
        if expected_digest is not None and hashlib.sha256(raw).hexdigest() != expected_digest:
            raise ValueError('Backup alterado desde a inspeção. Selecione e verifique novamente.')
        data = parse(raw)[name]
        if name == 'Aparência':
            prefs = Appearance(**strict_json(data, 16384))
            self.permissions.require(RESTORE_BACKUP)
            self.settings.set_appearance(prefs)
            return None
        if name in MODULES:
            self.permissions.require(RESTORE_BACKUP)
            return ProtectedStorage(self.folder,self.backend).restore_blob(name,data)
        with self.lease(name) as vault:
            entries = vault.decode(data)  # DPAPI and structural verification BEFORE replacing anything.
            if name == 'Bookmarks':
                seen = set()
                for item in entries.values():
                    obj = strict_json(item.body, 80000)
                    if not isinstance(obj,dict) or set(obj)!= {'category','url'}: raise ValueError('Link inválido.')
                    _,_,url = validate_fields(item.title,obj['category'],obj['url'])
                    if url in seen: raise ValueError('Link duplicado.')
                    seen.add(url)
            self.permissions.require(RESTORE_BACKUP)
            recovery = None
            if vault.path.exists():
                previous = bounded_read(vault.path, MAX_FILE)
                if not previous.startswith(MAGIC): raise ValueError('Arquivo atual não é um blob protegido. Restauração bloqueada.')
                recovery = vault.path.with_name(vault.path.stem+'.recovery-'+uuid4().hex+'.bin')
                create_exclusive(recovery, previous)
            atomic_replace(vault.path, data)
            return recovery
