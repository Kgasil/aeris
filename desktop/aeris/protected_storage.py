"""Explicit versioned snapshots; production encryption is Windows DPAPI only."""
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
import json
import hashlib
import os
import tempfile
from aeris.dpapi import WindowsDPAPI
from aeris.safe_input import bounded_read, strict_json

MODULES = ('Checklist', 'Ideas', 'Learn', 'Meeting', 'Research', 'Flashcards', 'Reminder')
MAGIC = b'AERIS-STORAGE-1\0'
LIMIT = 8 * 1024 * 1024


def fields(obj, names):
    if type(obj) is not dict or set(obj) != set(names.split()):
        raise ValueError('Estrutura de registro inválida.')
    return obj


def array(value, limit):
    if type(value) is not list or len(value) > limit:
        raise ValueError('Quantidade de registros inválida.')
    return value


def flag(value):
    if type(value) is not bool:
        raise ValueError('Estado de conclusão inválido.')
    return value


def snapshot(module, store):
    if module == 'Checklist':
        return [{'name': n, 'tasks': [{k:v for k,v in asdict(t).items() if k!='id'} for t in store.tasks(n)]} for n in store.names()]
    if module == 'Ideas':
        return [{k:v for k,v in asdict(t).items() if k!='id'} for t in store.list()]
    if module == 'Learn':
        return [{'title': p.title, 'topics': [{k:v for k,v in asdict(t).items() if k!='id'} for t in p.topics]} for p in store.list()]
    if module in ('Meeting', 'Research', 'Flashcards', 'Reminder'):
        records = []
        for item in store.list():
            row = asdict(item); del row['id']
            if module == 'Meeting': row['actions'] = list(row['actions'])
            if module == 'Flashcards': row['due'] = item.due.isoformat()
            records.append(row)
        return records
    raise ValueError('Módulo não suportado.')


def rebuild(module, records, *, clock=None):
    """Validate through public store APIs; IDs are local and regenerated."""
    if module == 'Checklist':
        from aeris.checklist import ChecklistStore, MAX_LISTS, MAX_TASKS
        store = ChecklistStore()
        for row in array(records, MAX_LISTS):
            row = fields(row, 'name tasks'); name = store.create(row['name'])
            for t in array(row['tasks'], MAX_TASKS):
                t = fields(t, 'title priority done')
                task = store.add(name, t['title'], t['priority'])
                if flag(t['done']): store.toggle(name, task.id)
    elif module == 'Ideas':
        from aeris.ideas import IdeasStore, MAX_IDEAS
        store = IdeasStore()
        for row in array(records, MAX_IDEAS):
            store.add(**fields(row, 'title category body status'))
    elif module == 'Learn':
        from aeris.learn import LearnStore, MAX_PLANS, MAX_TOPICS
        store = LearnStore()
        for row in array(records, MAX_PLANS):
            row = fields(row, 'title topics'); plan = store.create(row['title'])
            for t in array(row['topics'], MAX_TOPICS):
                t = fields(t, 'title minutes done')
                topic = store.add(plan.id, t['title'], t['minutes'])
                if flag(t['done']): store.toggle(plan.id, topic.id)
    elif module == 'Meeting':
        from aeris.meeting import MeetingStore, Action, MAX_MEETINGS, MAX_ACTIONS
        store = MeetingStore()
        for row in array(records, MAX_MEETINGS):
            row = fields(row, 'title day participants agenda notes actions')
            actions = [Action(**fields(a, 'title owner due done')) for a in array(row['actions'], MAX_ACTIONS)]
            store.add(*(row[k] for k in ('title','day','participants','agenda','notes')), actions)
    elif module == 'Research':
        from aeris.research import ResearchStore, MAX_REFERENCES
        store = ResearchStore()
        for row in array(records, MAX_REFERENCES):
            store.add(**fields(row, 'title project kind authors year locator notes state'))
    elif module == 'Flashcards':
        from aeris.flashcards import FlashcardsStore, MAX_CARDS
        store = FlashcardsStore(clock)
        for row in array(records, MAX_CARDS):
            store.restore_card(**fields(row, 'deck question answer due interval reviews'))
    elif module == 'Reminder':
        from aeris.reminder import ReminderStore, MAX_REMINDERS
        store = ReminderStore() if clock is None else ReminderStore(clock)
        for row in array(records, MAX_REMINDERS):
            store.restore_record(**fields(row, 'title due alert state'))
    else:
        raise ValueError('Módulo não suportado.')
    return store


class ProtectedStorage:
    def __init__(self, directory, backend=None):
        self.directory = Path(directory)
        self.backend = backend if backend is not None else WindowsDPAPI()

    def path(self, module):
        if module not in MODULES: raise ValueError('Módulo não suportado.')
        return self.directory / ('storage-' + module.lower() + '.bin')

    @contextmanager
    def lease(self, path):
        self.directory.mkdir(parents=True, exist_ok=True)
        with path.with_suffix('.lock').open('a+b') as f:
            if os.name == 'nt':
                import msvcrt
                f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield

    def decode(self, module, raw):
        self.path(module)  # validate module
        if len(raw)>LIMIT or not raw.startswith(MAGIC): raise ValueError('Arquivo protegido inválido.')
        plain = self.backend.unprotect(raw[len(MAGIC):])
        if len(plain)>LIMIT: raise ValueError('Conteúdo acima do limite.')
        data = fields(strict_json(plain, LIMIT), 'schema module records')
        if type(data['schema']) is not int or data['schema']!=1 or data['module']!=module:
            raise ValueError('Versão ou módulo incompatível.')
        return rebuild(module, data['records'])

    def _load(self, module, path):
        raw=bounded_read(path,LIMIT)
        return self.decode(module,raw)

    def previous_path(self, module):
        return self.path(module).with_suffix('.previous.bin')

    def load_previous(self,module):
        with self.lease(self.path(module)): return self._load(module,self.previous_path(module))

    def delete_previous(self,module):
        with self.lease(self.path(module)): self.previous_path(module).unlink()

    def _atomic(self,path,data):
        temp=None
        try:
            with tempfile.NamedTemporaryFile(dir=self.directory,prefix='.storage-',delete=False) as f:
                temp=Path(f.name); f.write(data); f.flush(); os.fsync(f.fileno())
            os.replace(temp,path)
        finally:
            if temp is not None: temp.unlink(missing_ok=True)

    def export_blob(self,module):
        path=self.path(module)
        with self.lease(path):
            raw=bounded_read(path,LIMIT)
            self.decode(module,raw)
            return raw

    def restore_blob(self,module,raw):
        path=self.path(module)
        with self.lease(path):
            self.decode(module,raw)
            recovery=None
            if path.exists():
                previous=bounded_read(path,LIMIT)
                self.decode(module,previous)
                recovery=self.previous_path(module); self._atomic(recovery,previous)
            self._atomic(path,raw)
            return recovery

    def load(self, module):
        path = self.path(module)
        with self.lease(path): return self._load(module, path)

    def save(self, module, store, *, overwrite=False, keep_previous=False):
        path = self.path(module)
        records = snapshot(module, store)
        rebuild(module, records)
        plain = json.dumps({'schema':1,'module':module,'records':records}, ensure_ascii=False, allow_nan=False).encode('utf-8')
        if len(plain)>LIMIT: raise ValueError('Conteúdo acima do limite.')
        with self.lease(path):
            if path.exists():
                if not overwrite: raise FileExistsError('Já existe uma cópia protegida.')
                self._load(module, path)  # never silently overwrite unreadable data
            encrypted = MAGIC + self.backend.protect(plain)
            if len(encrypted)>LIMIT or len(encrypted)<=len(MAGIC): raise ValueError('Tamanho protegido inválido.')
            if keep_previous and path.exists():
                previous=bounded_read(path,LIMIT)
                self.decode(module,previous)
                self._atomic(self.previous_path(module),previous)
            self._atomic(path,encrypted)

    def _current(self, module, path):
        try:
            raw=bounded_read(path,LIMIT)
        except FileNotFoundError:
            return None, None, None
        store=self.decode(module,raw)
        return hashlib.sha256(raw).digest(), snapshot(module,store), raw

    def baseline(self,module):
        path=self.path(module)
        with self.lease(path):
            token,records,_=self._current(module,path)
            return token,records

    def save_if_current(self,module,store,expected):
        """Compare protected bytes under the same lease used for replacement."""
        path=self.path(module)
        records=snapshot(module,store)
        if not records: raise ValueError('Sessão vazia.')
        rebuild(module,records)
        plain=json.dumps({'schema':1,'module':module,'records':records},ensure_ascii=False,allow_nan=False).encode('utf-8')
        if len(plain)>LIMIT: raise ValueError('Conteúdo acima do limite.')
        with self.lease(path):
            token,_,raw=self._current(module,path)
            if token!=expected: raise ValueError('Cópia alterada externamente.')
            encrypted=MAGIC+self.backend.protect(plain)
            if len(encrypted)>LIMIT or len(encrypted)<=len(MAGIC): raise ValueError('Tamanho protegido inválido.')
            if raw is not None: self._atomic(self.previous_path(module),raw)
            self._atomic(path,encrypted)
            return hashlib.sha256(encrypted).digest()

    def delete(self, module):
        path = self.path(module)
        with self.lease(path): path.unlink()
