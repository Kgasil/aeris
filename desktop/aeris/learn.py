"""Manual learning plans, bounded and session-scoped. No I/O."""
from dataclasses import dataclass, replace
from aeris.ideas import field
from aeris.registry import normalize

MAX_PLANS = 20
MAX_TOPICS = 100

@dataclass(frozen=True)
class Topic:
    id: int
    title: str
    minutes: int
    done: bool = False

@dataclass(frozen=True)
class Plan:
    id: int
    title: str
    topics: tuple[Topic, ...] = ()

class LearnStore:
    def __init__(self):
        self._plans = {}
        self._next = 1

    def list(self):
        return tuple(self._plans.values())

    def get(self, plan_id):
        return self._plans[plan_id]

    def _title(self, title, exclude=None):
        title = field(title, 100)
        if any(normalize(p.title)==normalize(title) and p.id!=exclude for p in self.list()):
            raise ValueError('Já existe uma trilha com esse nome.')
        return title

    def create(self, title):
        if len(self._plans)>=MAX_PLANS: raise ValueError('Limite de 20 trilhas.')
        p=Plan(self._next,self._title(title)); self._plans[p.id]=p; self._next+=1
        return p

    def rename(self, plan_id, title):
        p=self.get(plan_id)
        self._plans[plan_id]=replace(p,title=self._title(title,plan_id))

    def delete_plan(self, plan_id):
        del self._plans[plan_id]

    @staticmethod
    def _fields(title, minutes):
        if type(minutes) is not int or not 1<=minutes<=1440: raise ValueError('Estimativa entre 1 e 1440 minutos.')
        return field(title,200), minutes

    def add(self, plan_id, title, minutes):
        p=self.get(plan_id)
        if len(p.topics)>=MAX_TOPICS: raise ValueError('Limite de 100 tópicos por trilha.')
        t=Topic(self._next,*self._fields(title,minutes)); self._next+=1
        self._plans[plan_id]=replace(p,topics=p.topics+(t,))
        return t

    def _locate(self, plan_id, topic_id):
        p=self.get(plan_id)
        for i,t in enumerate(p.topics):
            if t.id==topic_id: return p,i,t
        raise KeyError(topic_id)

    def _update(self, p, i, t):
        self._plans[p.id]=replace(p,topics=p.topics[:i]+(t,)+p.topics[i+1:])

    def edit(self, plan_id, topic_id, title, minutes):
        p,i,t=self._locate(plan_id,topic_id); title,minutes=self._fields(title,minutes)
        self._update(p,i,replace(t,title=title,minutes=minutes))

    def toggle(self, plan_id, topic_id):
        p,i,t=self._locate(plan_id,topic_id); self._update(p,i,replace(t,done=not t.done))

    def move(self, plan_id, topic_id, direction):
        if type(direction) is not int or direction not in (-1,1): raise ValueError('Direção inválida.')
        p,i,t=self._locate(plan_id,topic_id); j=i+direction
        if not 0<=j<len(p.topics): return False
        topics=list(p.topics); topics[i],topics[j]=topics[j],topics[i]
        self._plans[p.id]=replace(p,topics=tuple(topics)); return True

    def delete_topic(self, plan_id, topic_id):
        p,i,_=self._locate(plan_id,topic_id)
        self._plans[p.id]=replace(p,topics=p.topics[:i]+p.topics[i+1:])

    def progress(self, plan_id):
        ts=self.get(plan_id).topics
        return sum(t.done for t in ts),len(ts),sum(t.minutes for t in ts if t.done),sum(t.minutes for t in ts)

    def clear(self):
        self._plans.clear()
