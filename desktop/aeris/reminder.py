"""Session-only reminders. No external scheduler or disk writes."""
from dataclasses import dataclass, replace
from time import time
from math import isfinite, ceil
from aeris.checklist import clean

MAX_REMINDERS = 100
MAX_MINUTES = 7 * 24 * 60

@dataclass(frozen=True)
class Reminder:
    id: int
    title: str
    due: float
    alert: bool
    state: str = 'pending'

class ReminderStore:
    def __init__(self, clock=time):
        self.clock = clock
        self._items = {}
        self._next_id = 1

    def list(self):
        return tuple(sorted(self._items.values(), key=lambda r: (r.due, r.id)))

    def _validate(self, title, minutes, alert):
        title = clean(title, 200)
        if type(minutes) is not int or not 1 <= minutes <= MAX_MINUTES:
            raise ValueError('Duração de 1 a 10080 minutos.')
        if type(alert) is not bool: raise ValueError('Alerta inválido.')
        due = self.clock() + minutes * 60
        if not isfinite(due): raise ValueError('Relógio indisponível.')
        return title, due

    def add(self, title, minutes, alert=False):
        title, due = self._validate(title, minutes, alert)
        return self.add_at(title, due, alert)

    def add_at(self, title, due, alert=False):
        title=clean(title,200)
        now=self.clock()
        if type(alert) is not bool or type(due) not in (float,int) or not isfinite(due) or not now < due <= now+MAX_MINUTES*60:
            raise ValueError('Horário vencido ou fora do intervalo de sete dias.')
        if len(self._items) >= MAX_REMINDERS: raise ValueError('Limite de 100 lembretes.')
        r = Reminder(self._next_id, title, due, alert)
        self._items[r.id] = r; self._next_id += 1
        return r

    def restore_record(self, title, due, alert, state):
        """Preserve absolute deadlines; overdue pending records do not replay alerts."""
        title=clean(title,200)
        if (type(due) not in (float,int) or not 0<=due<=253402300799 or not isfinite(due)
                or type(alert) is not bool or state not in ('pending','due','cancelled')):
            raise ValueError('Registro de lembrete inválido.')
        if len(self._items)>=MAX_REMINDERS: raise ValueError('Limite de lembretes.')
        if state=='pending' and due<=self.clock(): state='due'
        r=Reminder(self._next_id,title,due,alert,state)
        self._items[r.id]=r; self._next_id+=1
        return r

    def edit(self, item_id, title, minutes, alert=False):
        title, due = self._validate(title, minutes, alert)
        r = self._items[item_id]
        if r.state != 'pending' or r.due <= self.clock(): raise ValueError('Somente lembretes ainda não vencidos podem ser editados.')
        self._items[item_id] = replace(r, title=title, due=due, alert=alert)
        return self._items[item_id]

    def cancel(self, item_id):
        r = self._items[item_id]
        if r.state != 'pending' or r.due <= self.clock(): raise ValueError('Lembrete não está pendente ou já venceu.')
        self._items[item_id] = replace(r, state='cancelled')

    def delete(self, item_id):
        del self._items[item_id]

    def collect_due(self):
        now = self.clock()
        due = tuple(r for r in self.list() if r.state == 'pending' and r.due <= now)
        for r in due: self._items[r.id] = replace(r, state='due')
        return tuple(self._items[r.id] for r in due)

    def next_delay_ms(self):
        dates = [r.due for r in self._items.values() if r.state == 'pending']
        if not dates: return None
        # Recheck wall clock at most every 30s while reminders exist.
        return max(1, min(30000, ceil((min(dates) - self.clock()) * 1000)))

    def clear(self):
        self._items.clear()
