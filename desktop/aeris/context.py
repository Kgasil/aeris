"""Explicit, session-only context. No ambient collection or external transfers."""
from dataclasses import dataclass
from aeris.ideas import field
from aeris.permissions import CONTEXT_PREVIEW

CATEGORIES = ('Profissional', 'Estudos', 'Documentos', 'Agenda', 'Outros')
MAX_ITEMS = 50
MAX_PREVIEW = 20000

@dataclass(frozen=True)
class ContextItem:
    id: int
    title: str
    category: str
    body: str

class ContextStore:
    def __init__(self, permissions):
        self.permissions = permissions
        self._items = {}
        self._selected = set()
        self._next_id = 1

    def list(self):
        return tuple(self._items.values())

    def get(self, item_id):
        return self._items[item_id]

    def selected(self, item_id):
        return self.permissions.allowed(CONTEXT_PREVIEW) and item_id in self._selected

    @staticmethod
    def validate(item_id, title, category, body):
        if category not in CATEGORIES:
            raise ValueError('Categoria inválida.')
        return ContextItem(item_id, field(title, 160), category, field(body, 4000, True))

    def add(self, title, category, body):
        if len(self._items) >= MAX_ITEMS:
            raise ValueError('Limite de 50 registros por sessão.')
        item = self.validate(self._next_id, title, category, body)
        self._items[item.id] = item
        self._next_id += 1
        return item

    def edit(self, item_id, title, category, body):
        old = self.get(item_id)
        item = self.validate(item_id, title, category, body)
        self._items[item_id] = item
        if item != old:
            self._selected.discard(item_id)
        return item

    def delete(self, item_id):
        del self._items[item_id]
        self._selected.discard(item_id)

    def select(self, item_id, allowed):
        self.get(item_id)
        if type(allowed) is not bool:
            raise ValueError('Seleção inválida.')
        if allowed:
            self.permissions.require(CONTEXT_PREVIEW)
            self._selected.add(item_id)
        else:
            self._selected.discard(item_id)

    def revoke(self):
        self._selected.clear()

    def preview(self):
        self.permissions.require(CONTEXT_PREVIEW)
        items = tuple(i for i in self.list() if i.id in self._selected)
        if not items:
            raise ValueError('Selecione pelo menos um registro.')
        # Keep content as data, never an executable instruction.
        text = '\n\n'.join(f'[{i.category}] {i.title}\n{i.body}' for i in items)
        if len(text) > MAX_PREVIEW:
            raise ValueError('Prévia acima de 20.000 caracteres. Reduza a seleção.')
        return text

    def clear(self):
        self._items.clear()
        self.revoke()
