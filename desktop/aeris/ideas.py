"""Voluntary idea records, bounded, memory only, no ambient collection."""
from dataclasses import dataclass
from aeris.registry import normalize

STATUSES = ('Nova', 'Em desenvolvimento', 'Concluída', 'Arquivada')
MAX_IDEAS = 200


def field(value, limit, multiline=False, required=True):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError(f'Texto inválido ou acima de {limit} caracteres.')
    if any((ord(c)<32 and not (multiline and c in '\n\t')) or 127<=ord(c)<=159 for c in value):
        raise ValueError('Caracteres de controle não permitidos.')
    value = value.strip()
    if required and not value:
        raise ValueError('Preencha título e categoria.')
    return value


@dataclass(frozen=True)
class Idea:
    id: int
    title: str
    category: str
    body: str
    status: str


class IdeasStore:
    def __init__(self):
        self._items = {}
        self._next_id = 1

    def list(self):
        return tuple(self._items.values())

    def get(self, idea_id):
        return self._items[idea_id]

    @staticmethod
    def validated(idea_id, title, category, body, status):
        if status not in STATUSES:
            raise ValueError('Estado inválido.')
        return Idea(idea_id, field(title, 160), field(category, 60), field(body, 4000, True, False), status)

    def add(self, title, category, body='', status='Nova'):
        if len(self._items) >= MAX_IDEAS:
            raise ValueError('Limite de 200 ideias por sessão.')
        item = self.validated(self._next_id, title, category, body, status)
        self._items[item.id] = item
        self._next_id += 1
        return item

    def edit(self, idea_id, title, category, body, status):
        self.get(idea_id)
        item = self.validated(idea_id, title, category, body, status)
        self._items[idea_id] = item
        return item

    def delete(self, idea_id):
        del self._items[idea_id]

    def search(self, query='', status=None, category=None):
        words = normalize(field(query, 200, required=False)).split()
        if status is not None and status not in STATUSES:
            raise ValueError('Filtro de estado inválido.')
        if category is not None:
            category = normalize(field(category, 60))
        return tuple(item for item in self.list()
                     if (status is None or item.status == status)
                     and (category is None or normalize(item.category) == category)
                     and all(word in normalize(f'{item.title} {item.category} {item.body}') for word in words))

    def clear(self):
        self._items.clear()
