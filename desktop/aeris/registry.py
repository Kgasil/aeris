"""Catálogo declarativo; não carrega nem executa ferramentas planejadas."""
from dataclasses import dataclass
from pathlib import Path
import json
import unicodedata

@dataclass(frozen=True)
class Module:
    id: int
    name: str
    category: str
    description: str
    status: str


def normalize(value: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', value.casefold())
                   if not unicodedata.combining(c))


def load_catalog() -> tuple[Module, ...]:
    path = Path(__file__).with_name('catalog.json')
    return tuple(Module(**item) for item in json.loads(path.read_text(encoding='utf-8')))


def filter_catalog(modules: tuple[Module, ...], query: str = '', category: str = 'Todas') -> tuple[Module, ...]:
    words = normalize(query).split()
    return tuple(m for m in modules
                 if (category == 'Todas' or m.category == category)
                 and all(word in normalize(f'{m.name} {m.category} {m.description}') for word in words))
