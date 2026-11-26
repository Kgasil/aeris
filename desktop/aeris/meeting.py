"""Manual meeting minutes; no recording, calendar access or persistent storage."""
from dataclasses import dataclass
from datetime import date
import re
from aeris.ideas import field
from aeris.registry import normalize

MAX_MEETINGS = 50
MAX_ACTIONS = 50


def optional_date(value):
    value = field(value, 10, required=False)
    if value:
        try:
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value): raise ValueError
            date.fromisoformat(value)
        except ValueError: raise ValueError('Data inválida. Use AAAA-MM-DD.') from None
    return value


@dataclass(frozen=True)
class Action:
    title: str
    owner: str = ''
    due: str = ''
    done: bool = False

    def __post_init__(self):
        object.__setattr__(self,'title',field(self.title,200))
        object.__setattr__(self,'owner',field(self.owner,120,required=False))
        object.__setattr__(self,'due',optional_date(self.due))
        if type(self.done) is not bool: raise ValueError('Estado de atividade inválido.')


@dataclass(frozen=True)
class Meeting:
    id: int
    title: str
    day: str
    participants: str
    agenda: str
    notes: str
    actions: tuple[Action, ...]

    @property
    def completed(self): return sum(a.done for a in self.actions)


def validated(mid,title,day,participants,agenda,notes,actions):
    if not isinstance(actions,(tuple,list)) or len(actions)>MAX_ACTIONS or any(type(a) is not Action for a in actions):
        raise ValueError('Plano inválido ou acima de 50 atividades.')
    return Meeting(mid,field(title,160),optional_date(day),field(participants,2000,True,False),field(agenda,4000,True,False),field(notes,8000,True,False),tuple(actions))


class MeetingStore:
    def __init__(self): self._items={}; self._next=1
    def list(self): return tuple(self._items.values())
    def get(self,mid): return self._items[mid]
    def add(self,*values):
        if len(self._items)>=MAX_MEETINGS: raise ValueError('Limite de 50 reuniões por sessão.')
        item=validated(self._next,*values); self._items[item.id]=item; self._next+=1; return item
    def edit(self,mid,*values):
        self.get(mid); item=validated(mid,*values); self._items[mid]=item; return item
    def delete(self,mid): del self._items[mid]
    def clear(self): self._items.clear()
    def search(self,query=''):
        words=normalize(field(query,200,required=False)).split()
        return tuple(m for m in self.list() if all(w in normalize(' '.join((m.title,m.day,m.participants,m.agenda,m.notes,*(a.title+' '+a.owner for a in m.actions)))) for w in words))


def minutes(item):
    lines=['ATA DE REUNIÃO',item.title,'Data: '+(item.day or 'Não informada'),'','PARTICIPANTES',item.participants or 'Não informados','','PAUTA',item.agenda or 'Não informada','','ANOTAÇÕES E DECISÕES',item.notes or 'Não informadas','','PLANO DE AÇÃO',f'{item.completed}/{len(item.actions)} atividades concluídas']
    for a in item.actions:
        lines.append(f"[{'x' if a.done else ' '}] {a.title} | Responsável: {a.owner or 'Não definido'} | Prazo: {a.due or 'Não definido'}")
    return '\n'.join(lines)
