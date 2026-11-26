"""Session-only research records; source metadata is supplied by the user."""
from dataclasses import dataclass
from aeris.ideas import field
from aeris.registry import normalize

KINDS = ('Artigo', 'Livro', 'Site', 'Relatório', 'Outro')
STATES = ('A consultar', 'Em leitura', 'Consultada')
MAX_REFERENCES = 300

@dataclass(frozen=True)
class Reference:
    id: int
    title: str
    project: str
    kind: str
    authors: str
    year: str
    locator: str
    notes: str
    state: str

    def bibliography(self):
        # Descriptive only, never infer missing metadata or claim a citation standard.
        parts = [self.authors or '[Autoria não informada]', self.title,
                 self.year or '[Ano não informado]', self.kind]
        if self.locator: parts.append(self.locator)
        return ' | '.join(parts)

class ResearchStore:
    def __init__(self):
        self._items = {}
        self._next_id = 1

    def list(self): return tuple(self._items.values())
    def get(self, ident): return self._items[ident]

    @staticmethod
    def validated(ident, title, project, kind, authors='', year='', locator='', notes='', state='A consultar'):
        if kind not in KINDS or state not in STATES: raise ValueError('Tipo ou estado inválido.')
        year = field(year, 4, required=False)
        if year and (not year.isascii() or not year.isdecimal() or len(year)!=4 or int(year)==0):
            raise ValueError('Informe um ano de quatro dígitos ou deixe vazio.')
        return Reference(ident, field(title, 200), field(project, 100), kind,
                         field(authors, 300, required=False), year,
                         field(locator, 500, required=False), field(notes, 4000, True, False), state)

    def add(self, *args, **kwargs):
        if len(self._items)>=MAX_REFERENCES: raise ValueError('Limite de 300 referências por sessão.')
        item=self.validated(self._next_id,*args,**kwargs)
        self._items[item.id]=item; self._next_id+=1
        return item

    def edit(self, ident, *args, **kwargs):
        self.get(ident)
        item=self.validated(ident,*args,**kwargs); self._items[ident]=item
        return item

    def delete(self, ident): del self._items[ident]
    def clear(self): self._items.clear()

    def search(self, query='', project='', state=None):
        words=normalize(field(query,200,required=False)).split()
        project=normalize(field(project,100,required=False))
        if state is not None and state not in STATES: raise ValueError('Estado inválido.')
        return tuple(r for r in self.list() if (not project or normalize(r.project)==project)
                     and (state is None or r.state==state)
                     and all(w in normalize(' '.join((r.title,r.project,r.kind,r.authors,r.year,r.locator,r.notes))) for w in words))
