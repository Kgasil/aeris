"""Textos reutilizáveis, inseridos voluntariamente e mantidos apenas em memória."""
from dataclasses import dataclass
from aeris.registry import normalize

@dataclass(frozen=True)
class Snippet:
    id: int
    title: str
    category: str
    body: str

class SnippetStore:
    def __init__(self):
        self._items = {}
        self._next = 1

    def list(self, query='', category=None):
        terms = normalize(query).split()
        return tuple(item for item in self._items.values()
                     if (category is None or item.category == category)
                     and all(word in normalize(f'{item.title} {item.category} {item.body}')
                             for word in terms))

    def get(self, snippet_id):
        return self._items[snippet_id]

    def save(self, title, category, body, snippet_id=None):
        title, category = title.strip(), category.strip()
        if not title or not category or not body.strip():
            raise ValueError('Preencha título, categoria e texto.')
        if len(title) > 120 or len(category) > 60 or len(body) > 20000:
            raise ValueError('Limites: título 120, categoria 60 e texto 20.000 caracteres.')
        if snippet_id is None:
            if len(self._items) >= 100:
                raise ValueError('Limite de 100 snippets por sessão.')
            snippet_id = self._next
            self._next += 1
        elif snippet_id not in self._items:
            raise KeyError(snippet_id)
        item = Snippet(snippet_id, title, category, body)
        self._items[snippet_id] = item
        return item

    def delete(self, snippet_id):
        del self._items[snippet_id]

    def clear(self):
        self._items.clear()
