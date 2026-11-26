"""Explicit, single-record integrations. No network or automatic persistence."""
from dataclasses import dataclass
from datetime import datetime
import re
from aeris.permissions import INTEGRATION_RUN
from aeris.checklist import clean, MAX_TASKS
from aeris.reminder import MAX_REMINDERS, MAX_MINUTES

@dataclass(frozen=True)
class Transfer:
    source: object
    meeting: object
    index: int
    target: str
    destination: object
    args: tuple
    preview: str


def prepare(hub, meeting, index, target, value):
    hub.permissions.require(INTEGRATION_RUN)
    if target not in ('Checklist','Reminder') or not hub.enabled('Meeting') or not hub.enabled(target):
        raise ValueError('Origem ou destino desativado.')
    source=hub.meeting_store
    if source is None or not any(m is meeting for m in source.list()):
        raise ValueError('A reunião salva mudou ou não existe mais.')
    if type(index) is not int or not 0<=index<len(meeting.actions):
        raise ValueError('Selecione uma atividade salva.')
    action=meeting.actions[index]
    if action.done: raise ValueError('Selecione uma atividade pendente.')
    title=clean(action.title,200)
    dest=getattr(hub,target.lower()+'_store')
    if dest is None: raise ValueError('Abra a ferramenta de destino primeiro.')
    if target=='Checklist':
        name=clean(value,80)
        if name not in dest.names(): raise ValueError('Selecione uma lista existente.')
        tasks=dest.tasks(name)
        if len(tasks)>=MAX_TASKS: raise ValueError('Lista cheia.')
        if any(t.title.casefold()==title.casefold() for t in tasks): raise ValueError('Já existe tarefa com esse título na lista.')
        args=(name,title)
        preview=f'Criar tarefa: {title}\nLista: {name}\nPrioridade: Normal\nResponsável e prazo não serão transferidos.'
    else:
        if not action.due or not isinstance(value,str) or not re.fullmatch(r'[0-9]{2}:[0-9]{2}',value):
            raise ValueError('A atividade precisa de data e horário HH:MM.')
        try:
            local=datetime.fromisoformat(action.due+'T'+value)
            stamps={local.replace(fold=f).timestamp() for f in (0,1)}
            if len(stamps)!=1 or datetime.fromtimestamp(next(iter(stamps)))!=local: raise ValueError
            due=stamps.pop()
        except (ValueError,OverflowError,OSError): raise ValueError('Horário local inválido ou ambíguo.') from None
        now=dest.clock()
        if not now<due<=now+MAX_MINUTES*60: raise ValueError('Prazo deve estar no futuro, em até sete dias.')
        items=dest.list()
        if len(items)>=MAX_REMINDERS: raise ValueError('Limite de lembretes.')
        if any(r.title.casefold()==title.casefold() and r.due==due and r.state=='pending' for r in items): raise ValueError('Já existe lembrete pendente com esse título e horário.')
        args=(title,due,True)
        preview=f'Criar lembrete: {title}\nHorário local: {local:%d/%m/%Y %H:%M}\nAlerta visual genérico enquanto Aeris estiver aberto.'
    return Transfer(source,meeting,index,target,dest,args,preview)


def execute(hub, proposal, value):
    """Called only after explicit UI confirmation; revalidate live source and target."""
    fresh=prepare(hub,proposal.meeting,proposal.index,proposal.target,value)
    if fresh!=proposal or fresh.source is not proposal.source or fresh.destination is not proposal.destination:
        raise ValueError('Origem ou destino mudou. Prepare novamente.')
    if proposal.target=='Checklist': return fresh.destination.add(*fresh.args)
    return fresh.destination.add_at(*fresh.args)

@dataclass(frozen=True)
class StudyTransfer:
    source: object
    record: object
    topic: object
    destination: object
    target_plan: object
    route: str
    args: tuple
    preview: str


def prepare_study(hub, route, record, value, topic=None):
    """Only saved, current records; user supplies answer or study estimate."""
    from aeris.flashcards import FlashcardsStore, MAX_CARDS
    from aeris.learn import LearnStore, MAX_TOPICS
    from aeris.registry import normalize
    hub.permissions.require(INTEGRATION_RUN)
    if route not in ('Learn-Flashcards','Research-Learn'):
        raise ValueError('Integração inválida.')
    src,target=route.split('-')
    if not hub.enabled(src) or not hub.enabled(target): raise ValueError('Origem ou destino desativado.')
    source=getattr(hub,src.lower()+'_store'); dest=getattr(hub,target.lower()+'_store')
    if source is None or not any(r is record for r in source.list()): raise ValueError('Registro de origem alterado ou excluído.')
    if dest is None: raise ValueError('Abra a ferramenta de destino primeiro.')
    plan=None
    if route=='Learn-Flashcards':
        if not any(t is topic for t in record.topics): raise ValueError('Selecione um tópico salvo.')
        args=FlashcardsStore.fields(record.title,topic.title,value)
        if len(dest.list())>=MAX_CARDS: raise ValueError('Limite de cartões.')
        if any(normalize(c.deck)==normalize(args[0]) and normalize(c.question)==normalize(args[1]) for c in dest.list()): raise ValueError('Já existe um cartão com essa pergunta no baralho.')
        preview=f'Baralho: {args[0]}\nPergunta: {args[1]}\nResposta informada por você: {args[2]}'
    else:
        if not isinstance(value,tuple) or len(value)!=2 or type(value[0]) is not int: raise ValueError('Selecione uma trilha e informe minutos.')
        try: plan=dest.get(value[0])
        except KeyError: raise ValueError('Trilha não encontrada.') from None
        title,minutes=LearnStore._fields(record.title,value[1])
        if len(plan.topics)>=MAX_TOPICS: raise ValueError('Trilha cheia.')
        if any(normalize(t.title)==normalize(title) for t in plan.topics): raise ValueError('Já existe tópico com esse título.')
        args=(plan.id,title,minutes)
        preview=f'Trilha: {plan.title}\nTópico: {title}\nEstimativa: {minutes} min\nSomente o título será transferido, não anotações ou URL.'
    return StudyTransfer(source,record,topic,dest,plan,route,args,preview)


def execute_study(hub, proposal, value):
    fresh=prepare_study(hub,proposal.route,proposal.record,value,proposal.topic)
    if fresh!=proposal or fresh.source is not proposal.source or fresh.destination is not proposal.destination or fresh.target_plan is not proposal.target_plan:
        raise ValueError('Origem ou destino mudou. Prepare novamente.')
    return fresh.destination.add(*fresh.args)
