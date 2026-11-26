"""Base compartilhada de armazenamento volátil e operações CRUD."""
from dataclasses import dataclass
from aeris.registry import normalize

@dataclass(frozen=True)
class Note:
    id: int
    title: str
    body: str

@dataclass(frozen=True)
class Snippet:
    id: int
    title: str
    category: str
    body: str

class SessionStore:
    def __init__(self,on_change=None):
        self._items = {}
        self._next = 1
        self.on_change = on_change or (lambda:None)
    def get(self,item_id): return self._items[item_id]
    def list(self,query='',category=None):
        terms = normalize(query).split()
        return tuple(i for i in self._items.values() if (category is None or getattr(i,'category',None)==category)
                     and all(t in normalize(f'{i.title} {getattr(i,"category", "")} {i.body}') for t in terms))
    def _save(self,title,body,category=None,item_id=None):
        title = title.strip()
        if category is not None: category=category.strip()
        if not title or not body.strip() or category=='': raise ValueError('Preencha todos os campos.')
        if len(title)>120 or len(body)>(20000 if category is not None else 100000) or (category is not None and len(category)>60):
            raise ValueError('Limite de caracteres excedido.')
        if item_id is None:
            if len(self._items)>=100: raise ValueError('Limite de 100 registros por sessão.')
            item_id=self._next; self._next+=1
        elif item_id not in self._items: raise KeyError(item_id)
        item = Note(item_id,title,body) if category is None else Snippet(item_id,title,category,body)
        self._items[item_id]=item
        self.on_change()
        return item
    def delete(self,item_id):
        del self._items[item_id]; self.on_change()
    def clear(self):
        self._items.clear(); self.on_change()

class CaptureStore(SessionStore):
    def save(self,title,body,note_id=None): return self._save(title,body,item_id=note_id)

class SnippetStore(SessionStore):
    def save(self,title,category,body,snippet_id=None): return self._save(title,body,category,snippet_id)
