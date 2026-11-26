"""Explicitly entered local activity records; no observers or event collection."""
from dataclasses import dataclass
from datetime import date, datetime
from aeris.ideas import field
from aeris.registry import normalize
import re

MAX_EVENTS = 300


def parse_day(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
        raise ValueError('Use a data AAAA-MM-DD.')
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError('Data inválida.') from exc


def parse_when(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2} (?:[01][0-9]|2[0-3]):[0-5][0-9]', value):
        raise ValueError('Use AAAA-MM-DD HH:MM (hora local).')
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError('Data ou horário inválido.') from exc


@dataclass(frozen=True)
class Event:
    id: int
    when: datetime
    title: str
    category: str
    body: str


class TimelineStore:
    def __init__(self):
        self._items = {}
        self._next_id = 1

    def list(self):
        return tuple(sorted(self._items.values(), key=lambda item: (item.when, item.id), reverse=True))

    def get(self, event_id):
        return self._items[event_id]

    @staticmethod
    def validated(event_id, when, title, category, body):
        return Event(event_id, parse_when(when), field(title, 160), field(category, 60), field(body, 2000, True, False))

    def add(self, when, title, category, body=''):
        if len(self._items) >= MAX_EVENTS:
            raise ValueError('Limite de 300 registros por sessão.')
        item = self.validated(self._next_id, when, title, category, body)
        self._items[item.id] = item
        self._next_id += 1
        return item

    def edit(self, event_id, when, title, category, body):
        self.get(event_id)
        item = self.validated(event_id, when, title, category, body)
        self._items[event_id] = item
        return item

    def delete(self, event_id):
        del self._items[event_id]

    def search(self, query='', category='', day_from='', day_to=''):
        words = normalize(field(query, 200, required=False)).split()
        cat = normalize(field(category, 60, required=False))
        start = parse_day(day_from) if day_from else None
        end = parse_day(day_to) if day_to else None
        if start and end and start > end:
            raise ValueError('Data inicial deve preceder a final.')
        return tuple(item for item in self.list()
                     if (not cat or normalize(item.category) == cat)
                     and (not start or item.when.date() >= start)
                     and (not end or item.when.date() <= end)
                     and all(word in normalize(f'{item.title} {item.category} {item.body}') for word in words))

    def clear(self):
        self._items.clear()
