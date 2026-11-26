"""Local, restricted Portuguese command router. No AI, shell, audio or network."""
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
import unicodedata
from time import time
from aeris.checklist import clean
from aeris.ideas import field
from aeris.permissions import COPILOT_RUN
from aeris.reminder import MAX_MINUTES

EXAMPLES = (
    'Lembre-me de revisar o relatório em 30 minutos',
    'Marque uma reunião amanhã às 14:00',
    'Adicione estudar Python à lista Estudos',
    'Inicie uma concentração de 25 minutos',
    'Anote minha ideia de automatizar relatórios',
    'Aeris, me lembre de revisar o relatório em 30 minutos',
    'Aeris, marque uma reunião amanhã às 14h',
    'Aeris, comece uma concentração de 25 minutos',
)

@dataclass(frozen=True)
class Proposal:
    tool: str
    args: tuple
    preview: str


def parse_command(text, now=None):
    if not isinstance(text,str) or len(text)>500 or any(unicodedata.category(c).startswith('C') for c in text):
        raise ValueError('Comando inválido (até 500 caracteres, sem controles).')
    text=text.strip().rstrip('.').strip()
    text=re.sub(r'^aeris,?\s+', '', text, count=1, flags=re.I)
    now=time() if now is None else now
    match=re.fullmatch(r'(?:lembre-me de|me lembre de|crie um lembrete para) (.+) em ([0-9]{1,5}) minutos?',text,re.I)
    if match:
        title=clean(match[1],200); minutes=int(match[2])
        if not 1<=minutes<=MAX_MINUTES: raise ValueError('Lembrete: de 1 a 10080 minutos.')
        due=now+minutes*60
        return reminder_proposal(title,due)
    match=re.fullmatch(r'marque (.+) (hoje|amanhã|amanha) (?:às|as) ([0-9]{1,2})(?::([0-9]{2})|h(?:([0-9]{2}))?)',text,re.I)
    if match:
        title=clean(match[1],200); day=datetime.fromtimestamp(now).date()+timedelta(days=match[2].casefold()!='hoje')
        try: local=datetime(day.year,day.month,day.day,int(match[3]),int(match[4] or match[5] or 0))
        except ValueError: raise ValueError('Horário inválido. Use HH:MM.') from None
        stamps={local.replace(fold=f).timestamp() for f in (0,1)}
        if len(stamps)!=1 or datetime.fromtimestamp(next(iter(stamps)))!=local:
            raise ValueError('Horário local inexistente ou ambíguo.')
        due=stamps.pop()
        if not now<due<=now+MAX_MINUTES*60: raise ValueError('O horário precisa estar no futuro.')
        return reminder_proposal(title,due)
    match=re.fullmatch(r'adicione (.+) (?:à|a) lista (.+)',text,re.I)
    if match:
        title=clean(match[1],200); name=clean(match[2],80)
        return Proposal('Checklist',(name,title),f'Criar tarefa: {title}\nLista existente: {name}\nPrioridade: Normal')
    match=re.fullmatch(r'(?:inicie|comece) (?:uma? )?(concentração|concentracao|intervalo) de ([0-9]{1,3}) minutos?',text,re.I)
    if match:
        mode='Intervalo' if match[1].casefold()=='intervalo' else 'Concentração'; minutes=int(match[2])
        if not 1<=minutes<=120: raise ValueError('Focus: de 1 a 120 minutos.')
        return Proposal('Focus',(mode,minutes),f'Iniciar {mode.lower()} de {minutes} minutos. Abrirá o Focus, sem substituir sessão ativa ou pausada.')
    match=re.fullmatch(r'anote (?:minha )?ideia de (.+)',text,re.I)
    if match:
        title=field(match[1],160)
        return Proposal('Ideas',(title,),f'Registrar ideia: {title}\nCategoria: Geral\nEstado: Nova')
    raise ValueError('Comando não reconhecido. Use um dos modelos disponíveis; nenhuma ação realizada.')


def reminder_proposal(title,due):
    return Proposal('Reminder',(title,due),f'Criar lembrete: {title}\nHorário local: {datetime.fromtimestamp(due):%d/%m/%Y %H:%M:%S}\nAlerta visual genérico: sim')


class CopilotSession:
    """Single-use proposal; editing, cancellation or revocation invalidates it."""
    def __init__(self, hub):
        self.hub=hub; self.pending=None

    def cancel(self): self.pending=None

    def prepare(self,text):
        self.cancel()
        self.hub.permissions.require(COPILOT_RUN)
        if not self.hub.enabled('Copilot'): raise ValueError('Copilot desativado.')
        proposal=parse_command(text)
        self.check_target(proposal)
        self.pending=proposal
        return proposal

    def check_target(self,p):
        h=self.hub
        if not h.enabled(p.tool): raise ValueError(f'Ative {p.tool} no catálogo antes de continuar.')
        if p.tool=='Checklist' and (h.checklist_store is None or p.args[0] not in h.checklist_store.names()):
            raise ValueError('Crie a lista indicada no Checklist antes de continuar (nome exato).')
        if p.tool=='Focus' and h.focus_timer and h.focus_timer.state in ('running','paused'):
            raise ValueError('Há uma sessão Focus ativa ou pausada. Não será substituída.')

    def confirm(self):
        p=self.pending; self.cancel()
        if p is None: raise ValueError('Prepare uma nova prévia antes de confirmar.')
        h=self.hub
        h.permissions.require(COPILOT_RUN)
        if not h.enabled('Copilot'): raise ValueError('Copilot desativado.')
        self.check_target(p)
        # Explicit dispatch only. No generic method lookup or arbitrary execution.
        if p.tool=='Reminder':
            from aeris.reminder import ReminderStore
            store=h.reminder_store if h.reminder_store is not None else ReminderStore()
            store.add_at(*p.args,alert=True); h.reminder_store=store
            h.schedule_reminders()
            if h.alive(h.reminder_window): h.reminder_window.render()
        elif p.tool=='Checklist':
            h.checklist_store.add(*p.args)
            if h.alive(h.checklist_window): h.checklist_window.render()
        elif p.tool=='Ideas':
            from aeris.ideas import IdeasStore
            store=h.ideas_store if h.ideas_store is not None else IdeasStore()
            store.add(p.args[0],'Geral'); h.ideas_store=store
            if h.alive(h.ideas_window): h.ideas_window.render()
        elif p.tool=='Focus':
            h.open_tool('Focus'); ui=h.focus_window
            ui.mode.set(p.args[0]); ui.minutes.set(str(p.args[1])); ui.start()
            if h.focus_timer.state!='running': raise ValueError('Não foi possível iniciar Focus.')
        else: raise ValueError('Operação não autorizada.')
        if h.alive(h.privacy_window): h.privacy_window.refresh()
        return f'Operação concluída em {p.tool}. Dados temporários nesta sessão.'
