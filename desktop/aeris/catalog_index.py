"""Immutable search index for the public tool catalog; never cache user queries."""
from aeris.registry import normalize


class CatalogIndex:
    def __init__(self, modules, names, categories, help_text, goals):
        self.rows=tuple((m,normalize(' '.join((m.name,names.get(m.name,m.name),m.description,m.category,categories.get(m.category,m.category),*help_text.get(m.name,('','')))))) for m in modules)
        self.goals={name:frozenset(items) for name,items in goals.items()}

    def search(self, query='', category='Todas', goal='Todas'):
        words=normalize(query).split()
        allowed=None if goal=='Todas' else self.goals.get(goal,frozenset())
        return tuple(m for m,description in self.rows
                     if (allowed is None or m.name in allowed)
                     and (category=='Todas' or m.category==category)
                     and all(word in description for word in words))
