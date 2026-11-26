"""Bounded session-only clipboard history. Never polls or persists contents."""
from dataclasses import dataclass, replace
from aeris.registry import normalize
from aeris.permissions import READ_CLIPBOARD, WRITE_CLIPBOARD

@dataclass(frozen=True)
class Clip:
    id: int
    text: str
    pinned: bool = False

class ClipboardStore:
    LIMIT = 50
    MAX_TEXT = 20000

    def __init__(self, permissions):
        self.permissions = permissions
        self._items = []
        self._next = 1

    def capture(self, read):
        self.permissions.require(READ_CLIPBOARD)
        text = read()
        if not isinstance(text, str) or not text.strip() or len(text) > self.MAX_TEXT:
            raise ValueError('Capture apenas texto não vazio de até 20.000 caracteres.')
        existing = next((c for c in self._items if c.text == text), None)
        if existing:
            self._items.remove(existing)
            self._items.insert(0, existing)
            return existing
        if len(self._items) >= self.LIMIT:
            index = next((i for i in range(len(self._items)-1, -1, -1) if not self._items[i].pinned), None)
            if index is None:
                raise ValueError('Histórico cheio de itens fixados. Desafixe ou exclua um item.')
            self._items.pop(index)
        item = Clip(self._next, text)
        self._next += 1
        self._items.insert(0, item)
        return item

    def list(self, query=''):
        terms = normalize(query).split()
        return tuple(c for c in sorted(self._items, key=lambda c: not c.pinned)
                     if all(t in normalize(c.text) for t in terms))

    def get(self, item_id):
        return next(c for c in self._items if c.id == item_id)

    def pin(self, item_id):
        item = self.get(item_id)
        self._items[self._items.index(item)] = replace(item, pinned=not item.pinned)

    def delete(self, item_id):
        self._items.remove(self.get(item_id))

    def copy(self, item_id, write):
        self.permissions.require(WRITE_CLIPBOARD)
        write(self.get(item_id).text)

    def clear(self):
        self._items.clear()
