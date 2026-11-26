"""Bounded voluntary flashcards; session-only, no network or background jobs."""
from dataclasses import dataclass, replace
from datetime import datetime, timezone, timedelta
from aeris.ideas import field
from aeris.registry import normalize

MAX_CARDS = 500
RATINGS = ('Difícil', 'Médio', 'Fácil')
DAY = 86400
MAX_INTERVAL = 365 * DAY

@dataclass(frozen=True)
class Flashcard:
    id: int
    deck: str
    question: str
    answer: str
    due: datetime
    interval: int = 0
    reviews: int = 0

class FlashcardsStore:
    def __init__(self, clock=None):
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._items = {}
        self._next_id = 1

    def now(self): return self._clock()
    def list(self): return tuple(self._items.values())
    def get(self, ident): return self._items[ident]
    def clear(self): self._items.clear()
    def delete(self, ident): del self._items[ident]

    @staticmethod
    def fields(deck, question, answer):
        return field(deck, 100), field(question, 1000, True), field(answer, 4000, True)

    def add(self, deck, question, answer):
        if len(self._items) >= MAX_CARDS: raise ValueError('Limite de 500 cartões por sessão.')
        deck, question, answer = self.fields(deck, question, answer)
        card = Flashcard(self._next_id, deck, question, answer, self.now())
        self._items[card.id] = card; self._next_id += 1
        return card

    def restore_card(self, deck, question, answer, due, interval, reviews):
        """Rebuild an explicitly loaded record without resetting its schedule."""
        if len(self._items) >= MAX_CARDS: raise ValueError('Limite de cartões.')
        deck, question, answer = self.fields(deck, question, answer)
        if type(due) is not str or len(due)>40: raise ValueError('Data de revisão inválida.')
        try:
            when = datetime.fromisoformat(due)
            if when.tzinfo is None or when.utcoffset()!=timedelta(0) or when.isoformat()!=due:
                raise ValueError('Data de revisão deve ser UTC canônica.')
        except (ValueError, OverflowError): raise ValueError('Data de revisão inválida.') from None
        if type(interval) is not int or type(reviews) is not int or not 0<=reviews<=10**9:
            raise ValueError('Histórico de revisão inválido.')
        if (reviews==0 and interval!=0) or (reviews>0 and not 600<=interval<=MAX_INTERVAL):
            raise ValueError('Intervalo de revisão inválido.')
        card=Flashcard(self._next_id, deck, question, answer, when, interval, reviews)
        self._items[card.id]=card; self._next_id+=1
        return card

    def edit(self, ident, deck, question, answer):
        old = self.get(ident)
        deck, question, answer = self.fields(deck, question, answer)
        if (question, answer) != (old.question, old.answer):
            card = Flashcard(ident, deck, question, answer, self.now())
        else: card = replace(old, deck=deck)
        self._items[ident] = card
        return card

    def search(self, query='', deck='', due_only=False):
        words = normalize(field(query, 200, required=False)).split()
        deck = normalize(field(deck, 100, required=False))
        now = self.now()
        return tuple(sorted((c for c in self.list() if (not deck or normalize(c.deck)==deck)
                      and (not due_only or c.due <= now)
                      and all(w in normalize(' '.join((c.deck,c.question,c.answer))) for w in words)),
                      key=lambda c:(c.due,c.id)))

    def review(self, ident, rating):
        if rating not in RATINGS: raise ValueError('Dificuldade inválida.')
        card = self.get(ident); now = self.now()
        if card.due > now: raise ValueError('Este cartão ainda não está disponível para revisão.')
        if rating == 'Difícil': interval = 600
        elif rating == 'Médio': interval = max(DAY, card.interval * 2)
        else: interval = max(3 * DAY, card.interval * 3)
        interval = min(MAX_INTERVAL, interval)
        updated = replace(card, due=now+timedelta(seconds=interval), interval=interval, reviews=card.reviews+1)
        self._items[ident] = updated
        return updated
