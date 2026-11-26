"""Pesquisa local de catálogo e conteúdo explicitamente autorizado."""
from dataclasses import dataclass
from aeris.registry import normalize

SOURCES = ('Ferramentas', 'Capture', 'Snippets')

@dataclass(frozen=True)
class Result:
    source: str
    id: int
    title: str
    category: str
    body: str


def search(query, sources, modules=(), notes=(), snippets=()):
    terms = normalize(query).split()
    if not terms:
        return ()
    candidates = []
    if 'Ferramentas' in sources:
        candidates.extend(Result('Ferramentas', m.id, m.name, m.category, m.description) for m in modules)
    if 'Capture' in sources:
        candidates.extend(Result('Capture', n.id, n.title, 'Anotação', n.body) for n in notes)
    if 'Snippets' in sources:
        candidates.extend(Result('Snippets', s.id, s.title, s.category, s.body) for s in snippets)
    matches = []
    for item in candidates:
        title = normalize(item.title)
        metadata = normalize(f'{item.title} {item.category} {item.source}')
        full = f'{metadata} {normalize(item.body)}'
        if all(term in full for term in terms):
            rank = (sum(term in title for term in terms), sum(term in metadata for term in terms))
            matches.append((rank, item))
    matches.sort(key=lambda pair: (-pair[0][0], -pair[0][1], normalize(pair[1].title), pair[1].source, pair[1].id))
    return tuple(item for _, item in matches)
