"""Conversation-first desktop workspace. Reuses existing session stores and capabilities."""
import base64
from datetime import date
import json
import queue
import subprocess
import tkinter as tk
from tkinter import ttk,messagebox
from aeris.hub import Hub, COLORS
from aeris.experience_help import HELP
from aeris.intelligence import recommend_tool
from aeris.voice_session import VoiceSession, MAX_TURNS
from aeris.vision_session import VisionSession, INTERVAL_MS, MAX_SECONDS, MAX_FRAMES
from aeris.companion_ui import CompanionWindow
from aeris.companion import chat,validate_message,speech_process,MAX_HISTORY
from aeris.copilot import CopilotSession,parse_command
from aeris.permissions import (COMPANION_CHAT,COMPANION_MIC,COMPANION_SPEAK,COPILOT_RUN,
                              COMPANION_SCREEN)
from aeris.screen_context import capture_process,read_capture,describe_screen,installed_models
from aeris.local_worker import worker_for
from aeris.safe_input import strict_json
from aeris.window_lifecycle import trace_window

NAMES=dict(zip(
('Hub','Spotlight','Health','Backup','Bridge','Focus','Workspace','Checklist','Reminder','Routine','Vault','Capture','Timeline','Ideas','Bookmarks','Autofill','Clipboard','Snippets','Expand','Convert','Translate','Voice','Text','Email','Meeting','Learn','Research','Flashcards','Pronounce','Accessibility','Copilot','Context','Interview','Search','Debug','Data','Dashboard','Report','Calculator','Decision','Documents','Organizer','Drop','Compare','Lens','Privacy','Link','Verify','Permissions','Metadata'),
('Início','Atalho flutuante','Estado do aplicativo','Cópias de segurança','Fluxos de trabalho','Concentração','Espaço de trabalho','Lista de tarefas','Lembretes','Rotinas','Cofre','Anotações','Linha do tempo','Ideias','Favoritos','Preenchimento de formulários','Área de transferência','Textos rápidos','Expandir texto','Conversor','Tradução','Leitura em voz alta','Revisão de texto','E-mail','Reuniões','Plano de estudos','Pesquisa','Cartões de estudo','Pronúncia','Leitura acessível','Assistente','Contexto','Treino de entrevista','Busca','Revisão de código','Análise de dados','Indicadores','Relatórios','Calculadora','Decisões','Documentos','Organização de arquivos','Seleção de arquivos','Comparação','Leitura de imagem','Privacidade','Análise de links','Integridade de arquivos','Permissões','Metadados')))
CATEGORIES=dict(zip(('Core','Productivity','Memory','Quick Actions','Communication','Learning','Intelligence','Business','Files','Security'),
('Essenciais','Produtividade','Memória','Ações rápidas','Comunicação','Aprendizado','Inteligência','Negócios','Arquivos','Segurança')))

GOALS={
    'Escrever e comunicar': ["Text","Email","Translate","Voice","Pronounce","Snippets","Expand","Accessibility"],
    'Organizar meu trabalho': ["Capture","Meeting","Checklist","Reminder","Focus","Ideas","Timeline","Workspace","Bookmarks"],
    'Analisar informações': ["Data","Dashboard","Report","Calculator","Convert","Decision","Debug"],
    'Estudar e aprender': ["Learn","Research","Flashcards","Interview"],
    'Trabalhar com arquivos': ["Documents","Organizer","Drop","Compare","Lens","Metadata"],
    'Proteger informações': ["Privacy","Permissions","Vault","Backup","Link","Verify"],
    'Automatizar e configurar': ["Hub","Spotlight","Health","Bridge","Routine","Autofill","Clipboard","Copilot","Context","Search"],
}


# Explicit task phrases only; no inference, execution, or data transfer.
TASK_HINTS=(
    ('Email',('escrever email','escrever e-mail','responder email','responder e-mail','rascunho de email','rascunho de e-mail')),
    ('Text',('corrigir texto','revisar texto','corrigir um texto','revisar um texto','corrigir ortografia')),
    ('Translate',('traduzir','traduza','traducao')),
    ('Meeting',('resumir reuniao','transcrever reuniao','ata de reuniao','acompanhar reuniao')),
    ('Capture',('fazer anotacoes','salvar anotacao','anotar uma ideia')),
    ('Checklist',('lista de tarefas','organizar tarefas','criar checklist')),
    ('Reminder',('criar lembrete','me lembre','lembre-me')),
    ('Data',('analisar csv','analisar planilha csv','qualidade dos dados','dados duplicados')),
    ('Dashboard',('criar indicadores','criar dashboard','agrupar dados')),
    ('Report',('relatorio de csv','relatorio dos dados')),
    ('Documents',('ler documento','extrair texto de documento')),
    ('Compare',('comparar arquivos','comparar textos')),
    ('Lens',('extrair texto de imagem','ler texto de imagem')),
    ('Learn',('plano de estudos','organizar estudos')),
    ('Flashcards',('criar flashcards','cartoes de estudo')),
    ('Privacy',('mascarar dados','ocultar dados pessoais')),
)
def task_hint(text):
    import re
    from aeris.registry import normalize
    if not isinstance(text,str) or len(text)>4000:
        return None
    words=' '.join(re.findall(r'\w+',normalize(text)))
    matches=[name for name,phrases in TASK_HINTS
             if any(' '+' '.join(re.findall(r'\w+',normalize(p)))+' ' in ' '+words+' ' for p in phrases)]
    return matches[0] if len(matches)==1 else None


class Conversation(CompanionWindow):
    """Reuse the bounded local worker, chat, speech, history and permission lifecycle."""
    def __init__(self,hub,parent):
        self.hub=hub; self.history=[]; self.results=queue.Queue(); self.job=0
        self.busy=False; self.process=None; self.timer=None; self.closed=False
        self.chat_allowed=False; self.kind=None; self.candidate=None
        self.voice=VoiceSession(); self.voice_timer=None
        self.vision=VisionSession(); self.vision_timer=None; self.vision_expiry=None; self.vision_badge=None
        self.session=CopilotSession(hub); self.action_input=None; self.screen=None; self.photo=None
        self.capture_timer=None; self.screen_question=None; self.meeting_active=False
        self.meeting_timer=None; self.meeting_generation=0; self.meeting_chunks=[]
        self.window=w=ttk.Frame(parent,padding=(18,12)); w.bind('<Destroy>',self.destroyed,add='+')
        top=ttk.Frame(w); top.pack(fill='x')
        ttk.Label(top,text='Olá. Como posso ajudar?',style='Experience.Title.TLabel').pack(side='left')
        ttk.Button(top,text='Nova conversa',command=self.reset_chat).pack(side='right')
        ttk.Label(w,text='Seu espaço de trabalho com IA local.',style='Experience.Muted.TLabel').pack(anchor='w',pady=(2,8))
        ai_header=ttk.Frame(w); ai_header.pack(fill='x',pady=(0,8))
        self.ai_state=tk.StringVar(w,'IA local · escolha um modelo')
        ttk.Label(ai_header,textvariable=self.ai_state,style='Experience.Muted.TLabel').pack(side='left')
        self.ai_toggle=ttk.Button(ai_header,text='Configurar IA',command=self.toggle_ai_settings)
        self.ai_toggle.pack(side='right')
        self.ai_settings= modelrow=ttk.Frame(w)
        self.ai_header=ai_header
        self.ai_open=False
        ttk.Label(modelrow,text='Modelo local').pack(side='left')
        self.model=tk.StringVar(w,'')
        self.model_entry=ttk.Combobox(modelrow,textvariable=self.model,width=19); self.model_entry.pack(side='left',padx=6)
        self.detect_button=ttk.Button(modelrow,text='Detectar modelos',command=self.detect_models); self.detect_button.pack(side='left')
        ttk.Button(modelrow,text='Ajuda',command=self.configure_ai).pack(side='left',padx=4)
        trace_window(w,self.model,self.model_changed)
        self.panes=panes=ttk.Frame(w); panes.pack(fill='both',expand=True)
        panes.columnconfigure(0,weight=3); panes.columnconfigure(1,weight=0); panes.rowconfigure(0,weight=1)
        left=ttk.Frame(panes,padding=(0,0,8,0)); right=ttk.Frame(panes,padding=(8,0,0,0)); left.grid(row=0,column=0,sticky='nsew'); right.grid(row=0,column=1,sticky='nsew'); self.context_panel=right; right.grid_remove(); self.context_open=False
        chathead=ttk.Frame(left); chathead.pack(fill='x',pady=(0,8))
        ttk.Label(chathead,text='CONVERSA',style='Experience.Section.TLabel').pack(side='left')
        self.context_toggle=ttk.Button(chathead,text='Mostrar contexto',command=self.toggle_context)
        self.context_toggle.pack(side='right')
        chatbox=ttk.Frame(left); chatbox.pack(fill='both',expand=True)
        self.transcript=tk.Text(chatbox,wrap='word',height=5,state='disabled',font=('Segoe UI',11),padx=16,pady=14,relief='flat',highlightthickness=1)
        self.transcript.pack(side='left',fill='both',expand=True)
        sb=ttk.Scrollbar(chatbox,command=self.transcript.yview); sb.pack(side='right',fill='y'); self.transcript.configure(yscrollcommand=sb.set)
        self.hint_panel=ttk.Frame(left,padding=8,style='Experience.Card.TFrame')
        self.hint_text=tk.StringVar(w,'')
        ttk.Label(self.hint_panel,textvariable=self.hint_text,wraplength=330,justify='left',style='Experience.Card.TLabel').pack(fill='x')
        self.hint_button=ttk.Button(self.hint_panel,text='Conhecer ferramenta',command=self.open_hint)
        self.hint_button.pack(anchor='w',pady=(4,0))
        self.hint_name=None; self.ai_hint=None
        self.input=tk.Text(left,wrap='word',height=3,font=('Segoe UI',11),padx=12,pady=8,relief='flat',highlightthickness=1); self.input.pack(fill='x',pady=(12,3))
        self.count=tk.StringVar(w,'0 / 4000 caracteres'); ttk.Label(left,textvariable=self.count,style='Experience.Muted.TLabel').pack(anchor='e')
        self.input.bind('<<Modified>>',self.input_changed); self.input.edit_modified(False)
        self.input.bind('<Control-Return>',self.keyboard_send)
        row=ttk.Frame(left); row.pack(fill='x',pady=6)
        self.send_button=ttk.Button(row,text='Enviar',style='Experience.Primary.TButton',command=self.send); self.send_button.pack(side='right')
        self.mic_button=ttk.Button(row,text='Ditar',command=self.listen); self.mic_button.pack(side='left')
        self.voice_button=ttk.Button(row,text='Conversar por voz',command=self.toggle_voice,style='Experience.Primary.TButton'); self.voice_button.pack(side='left',padx=4)
        self.stop_button=ttk.Button(row,text='Parar',command=self.stop); self.stop_button.pack(side='left',padx=4)
        row=ttk.Frame(left); row.pack(fill='x')
        self.speak_button=ttk.Button(row,text='Ouvir resposta',command=self.speak); self.speak_button.pack(side='left')
        self.voice_indicator=tk.StringVar(w,'Voz desligada')
        self.voice_panel=ttk.Label(left,textvariable=self.voice_indicator,style='Experience.Section.TLabel'); self.voice_panel.pack(anchor='w',pady=(3,0))
        self.advanced_open=False
        self.route_button=ttk.Button(row,text='Encontrar ferramenta',command=self.route_tool); self.route_button.pack(side='left',padx=4)
        self.advanced_toggle=ttk.Button(row,text='Mais opções',command=self.toggle_advanced); self.advanced_toggle.pack(side='right')
        self.advanced=ttk.Frame(left)
        self.auto_speak=tk.BooleanVar(w,False)
        self.auto_button=ttk.Checkbutton(self.advanced,text='Ler respostas automaticamente',variable=self.auto_speak); self.auto_button.pack(anchor='w')
        row=ttk.Frame(self.advanced); row.pack(fill='x')
        self.prepare_button=ttk.Button(row,text='Preparar ação',command=self.prepare_action); self.prepare_button.pack(side='left')
        self.suggest_button=ttk.Button(row,text='Preparar ação com IA',command=self.suggest); self.suggest_button.pack(side='left',padx=4)
        self.proposal_panel=ttk.Frame(left,padding=5,style='Experience.Card.TFrame')
        self.candidate_label=tk.StringVar(w,''); ttk.Label(self.proposal_panel,textvariable=self.candidate_label,wraplength=310,justify='left',style='Experience.Card.TLabel').pack(anchor='w')
        self.preview=tk.StringVar(w,''); ttk.Label(self.proposal_panel,textvariable=self.preview,wraplength=310,justify='left',style='Experience.Card.TLabel').pack(anchor='w')
        row=ttk.Frame(self.proposal_panel,style='Experience.Card.TFrame'); row.pack(fill='x')
        self.accept_button=ttk.Button(row,text='Usar sugestão',command=self.accept_candidate); self.accept_button.pack(side='left')
        self.confirm_button=ttk.Button(row,text='Confirmar ação',command=self.confirm_action,style='Experience.Primary.TButton'); self.confirm_button.pack(side='left',padx=4)
        ttk.Label(right,text='CONTEXTO DE TRABALHO',style='Experience.Section.TLabel').pack(anchor='w',pady=(0,8))
        tabs=self.context_tabs=ttk.Notebook(right); tabs.pack(fill='both',expand=True)
        tabs.bind('<<NotebookTabChanged>>',self.context_changed,add='+')
        screen=ttk.Frame(tabs,padding=9); tabs.add(screen,text='Tela')
        ttk.Label(screen,text='Acompanhe a tela principal',style='Experience.Subtitle.TLabel',wraplength=242).pack(anchor='w')
        ttk.Label(screen,text='Capture uma imagem ou acompanhe a tela por até 5 minutos. Somente a última imagem fica na memória. Revise antes de enviar à IA.',wraplength=242,justify='left').pack(anchor='w',pady=5)
        self.image_label=ttk.Label(screen,text='Nenhuma captura',anchor='center',style='Experience.Card.TLabel'); self.image_label.pack(fill='both',expand=True,pady=5)
        self.vision_state=tk.StringVar(w,'Acompanhamento desligado')
        ttk.Label(screen,textvariable=self.vision_state,style='Experience.Section.TLabel',wraplength=242).pack(anchor='w',pady=4)
        self.monitor_button=ttk.Button(screen,text='Acompanhar tela',command=self.toggle_vision,style='Experience.Primary.TButton'); self.monitor_button.pack(fill='x',pady=3)
        self.capture_button=ttk.Button(screen,text='Capturar tela',command=self.capture); self.capture_button.pack(fill='x',pady=3)
        self.analyze_button=ttk.Button(screen,text='Analisar captura com IA',command=self.analyze); self.analyze_button.pack(fill='x',pady=3)
        ttk.Button(screen,text='Descartar captura',command=self.discard_screen).pack(fill='x',pady=3)
        notes=ttk.Frame(tabs,padding=9); tabs.add(notes,text='Anotações')
        ttk.Label(notes,text='Bloco de trabalho',style='Experience.Subtitle.TLabel').pack(anchor='w')
        ttk.Label(notes,text='Escreva ou copie uma resposta para revisar. Salve em Anotações somente quando quiser.',wraplength=242).pack(anchor='w',pady=5)
        self.note=tk.Text(notes,wrap='word',height=7,relief='flat',highlightthickness=1,padx=8,pady=5); self.note.pack(fill='both',expand=True)
        ttk.Button(notes,text='Adicionar última resposta',command=self.append_answer).pack(fill='x',pady=(8,3))
        ttk.Button(notes,text='Salvar anotação na sessão',command=self.save_note).pack(fill='x')
        meetings=ttk.Frame(tabs,padding=9); tabs.add(meetings,text='Reunião')
        ttk.Label(meetings,text='Acompanhar reunião',style='Experience.Subtitle.TLabel').pack(anchor='w')
        ttk.Label(meetings,text='Microfone padrão do Windows, em blocos de ditado pt-BR. Não captura o áudio interno da chamada nem identifica participantes. Avise todos antes de iniciar.',wraplength=242,justify='left').pack(anchor='w',pady=5)
        self.meeting_text=tk.Text(meetings,wrap='word',height=6,relief='flat',highlightthickness=1,padx=8,pady=5); self.meeting_text.pack(fill='both',expand=True)
        self.meeting_start=ttk.Button(meetings,text='Iniciar transcrição pelo microfone',command=self.start_meeting); self.meeting_start.pack(fill='x',pady=(8,3))
        self.meeting_stop=ttk.Button(meetings,text='Parar transcrição',command=self.stop_meeting); self.meeting_stop.pack(fill='x',pady=3)
        ttk.Button(meetings,text='Preparar resumo na conversa',command=self.meeting_summary).pack(fill='x',pady=3)
        ttk.Button(meetings,text='Salvar ata na sessão',command=self.save_meeting).pack(fill='x',pady=3)
        self.status=tk.StringVar(w,'Pronto. Microfone e tela desligados.')
        ttk.Label(w,textvariable=self.status,style='Experience.Muted.TLabel',wraplength=800).pack(fill='x',pady=(12,0))
        self.draw(); self.permissions_changed()
    def toggle_ai_settings(self):
        self.ai_open=not self.ai_open
        if self.ai_open:
            self.ai_settings.pack(fill='x',pady=(0,8),before=self.panes)
        else:
            self.ai_settings.pack_forget()
        self.ai_toggle.configure(text='Fechar configuração' if self.ai_open else 'Configurar IA')
    def set_context(self,visible):
        if not visible and self.vision.active: self.stop_vision()
        self.context_open=bool(visible)
        self.panes.columnconfigure(1,weight=2 if visible else 0)
        if visible:
            self.context_panel.grid()
        else:
            self.context_panel.grid_remove()
        self.context_toggle.configure(text='Ocultar contexto' if visible else 'Mostrar contexto')
    def toggle_context(self):
        self.set_context(not self.context_open)
    def authorize(self,cap,label):
        permissions=self.hub.permissions
        if permissions.allowed(cap): return True
        revision=permissions.revision
        if not messagebox.askyesno('Autorizar nesta sessão?',label,parent=self.hub.root): return False
        if self.closed or revision!=permissions.revision: return False
        permissions.set(cap,True); return True
    def ensure_tool(self,name):
        if not self.hub.enabled(name): self.hub.toggle_tool(name)
        return self.hub.enabled(name)
    def model_changed(self,*args):
        self.session.cancel(); self.action_input=None; self.preview.set(''); self.ai_hint=None; self.update_hint(); super().model_changed(*args)
        self.ai_state.set('IA local · '+self.model.get().strip()[:48] if self.model.get().strip() else 'IA local · escolha um modelo')
    def detect_models(self):
        if self.busy or self.meeting_active: return
        if not self.authorize(COMPANION_CHAT,'Consultar os nomes dos modelos instalados no Ollama local? Nenhuma mensagem ou arquivo será enviado.'): return
        if self.start(COMPANION_CHAT,installed_models,kind='models'): self.status.set('Consultando modelos instalados…')
    def configure_ai(self):
        messagebox.showinfo('IA local','Instale o Ollama e um modelo local, com OLLAMA_NO_CLOUD=1. Em seguida clique Detectar modelos ou digite o nome exato. Para imagens, use um modelo compatível com visão. Aeris não instala modelos nem envia dados para uma API de nuvem.',parent=self.hub.root)
    def send(self):
        if self.meeting_active or self.busy or self.voice.active or self.vision.active: return
        # Recognized local commands use the same reviewed action path, without a model.
        try: parse_command(self.input.get('1.0','end-1c'))
        except ValueError: pass
        else: self.prepare_action(); return
        if not self.model.get().strip():
            if not self.ai_open: self.toggle_ai_settings()
            self.configure_ai(); return
        if self.ensure_tool('Copilot') and self.authorize(COMPANION_CHAT,'Enviar a mensagem e o histórico ao Ollama local? Nenhum outro arquivo será enviado.'):
            super().send()
    def toggle_voice(self):
        if self.voice.active:
            self.stop_voice(); return
        if self.closed or self.busy or self.meeting_active or self.capture_timer is not None: return
        if self.input.get('1.0','end-1c').strip():
            self.status.set('Envie ou limpe o rascunho antes de iniciar a conversa por voz.'); return
        model=self.model.get().strip()
        if not model:
            if not self.ai_open: self.toggle_ai_settings()
            self.configure_ai(); return
        revision=self.hub.permissions.revision
        if not messagebox.askyesno('Conversar por voz?',f'O microfone será reativado após cada resposta, por até {MAX_TURNS} turnos. A fala reconhecida será enviada ao modelo Ollama local com o histórico da conversa. O Aeris não grava áudio em arquivo. Clique Parar voz a qualquer momento.',parent=self.hub.root): return
        if self.closed or revision!=self.hub.permissions.revision or model!=self.model.get().strip(): return
        for cap,label in ((COMPANION_MIC,'Autorizar ditado pelo microfone?'),(COMPANION_CHAT,'Autorizar envio de texto e histórico ao modelo local?'),(COMPANION_SPEAK,'Autorizar reprodução de respostas por voz?')):
            if not self.authorize(cap,label): return
        if self.closed or self.busy or self.meeting_active or self.capture_timer is not None or self.voice.active or model!=self.model.get().strip() or self.input.get('1.0','end-1c').strip(): return
        if not self.ensure_tool('Copilot') or not self.voice_allowed(): return
        self.session.cancel(); self.action_input=None; self.preview.set(''); self.discard_candidate()
        self.voice.begin(model); self.voice_next()
    def voice_allowed(self):
        return all(self.hub.permissions.allowed(cap) for cap in (COMPANION_MIC,COMPANION_CHAT,COMPANION_SPEAK))
    def stop_voice(self,message='Conversa por voz encerrada.'):
        self.voice.stop()
        if self.voice_timer is not None:
            self.window.after_cancel(self.voice_timer); self.voice_timer=None
        if self.busy and self.kind in ('voice_listen','voice_chat','voice_speak'):
            super().stop()
        self.status.set(message); self.refresh()
    def voice_next(self):
        self.voice_timer=None
        if not self.voice.active: return
        if self.closed or not self.voice_allowed() or self.model.get().strip()!=self.voice.model or self.meeting_active or self.busy:
            self.stop_voice(); return
        phase=self.voice.phase
        if phase not in ('listen','speak'):
            self.stop_voice('Conversa por voz interrompida.'); return
        try:
            if worker_for(self.hub).busy: raise OSError('Outra operação local ativa.')
            p=speech_process(); self.process=p
            value=self.history[-1][1] if phase=='speak' and self.history else ''
            def work():
                try:
                    out,_=p.communicate(json.dumps({'action':phase,'text':value},ensure_ascii=True),timeout=18 if phase=='listen' else 90)
                    if p.returncode: raise OSError('Voz indisponível.')
                    return validate_message(strict_json(out,32768)) if phase=='listen' else None
                except subprocess.TimeoutExpired:
                    p.kill(); p.communicate(); raise
            if not self.start(COMPANION_MIC if phase=='listen' else COMPANION_SPEAK,work,kind='voice_'+phase):
                p.kill()
                try: p.communicate(timeout=2)
                except (OSError,subprocess.TimeoutExpired): pass
                self.process=None; raise OSError('Não foi possível iniciar a voz.')
        except (OSError,PermissionError):
            self.stop_voice('Voz indisponível. Confira o microfone e os recursos de voz pt-BR do Windows.'); return
        self.status.set('MICROFONE ATIVO · fale agora.' if phase=='listen' else 'Reproduzindo resposta · microfone desligado.')
    def voice_result(self,kind,ok,result):
        if not self.voice.active: return
        if not ok or not self.voice_allowed() or self.voice.model!=self.model.get().strip():
            self.stop_voice('Conversa por voz interrompida: silêncio, erro ou permissão revogada.'); return
        phase=kind.removeprefix('voice_')
        if phase!=self.voice.phase:
            self.stop_voice(); return
        if phase=='listen':
            # A spoken local action is a draft, never an automatic execution.
            try: parse_command(result)
            except ValueError: pass
            else:
                self.stop_voice('Pedido de ação reconhecido. Revise o texto e envie para preparar a confirmação.')
                self.input.insert('1.0',result); return
            self.voice.advance(phase)
            model=self.voice.model; history=tuple(self.history)
            if not self.start(COMPANION_CHAT,lambda:(result,chat(model,history,result)),kind='voice_chat'):
                self.stop_voice('Não foi possível consultar a IA.'); return
            self.status.set('Consultando IA local · microfone desligado.')
        elif phase=='chat':
            text,response=result
            self.history.extend((('user',text),('assistant',response))); self.history=self.history[-MAX_HISTORY:]; self.draw()
            self.voice.advance(phase)
            self.voice_timer=self.window.after(250,self.voice_next)
        else:
            if self.voice.advance(phase) is None:
                self.stop_voice('Limite da sessão de voz atingido. Inicie outra se quiser continuar.'); return
            self.voice_timer=self.window.after(450,self.voice_next)
    def listen(self):
        if self.ensure_tool('Copilot') and self.authorize(COMPANION_MIC,'Usar o microfone padrão para um ditado curto? Nenhuma gravação é salva pelo Aeris.'):
            self.speech('listen')
    def speak(self):
        if self.history and self.authorize(COMPANION_SPEAK,'Ler a última resposta com a voz local do Windows?'):
            self.speech('speak')
    def toggle_advanced(self):
        self.advanced_open=not self.advanced_open
        if self.advanced_open: self.advanced.pack(fill='x',pady=3,before=self.proposal_panel) if self.proposal_panel.winfo_manager() else self.advanced.pack(fill='x',pady=3)
        else: self.advanced.pack_forget()
        self.advanced_toggle.configure(text='Menos opções' if self.advanced_open else 'Mais opções')
    def refresh(self):
        if self.candidate or self.session.pending:
            if not self.proposal_panel.winfo_manager(): self.proposal_panel.pack(fill='x',pady=4)
        else: self.proposal_panel.pack_forget()
        free=not self.busy and not self.meeting_active and self.capture_timer is None and not self.voice.active and not self.vision.active
        self.monitor_button.configure(text='Parar acompanhamento' if self.vision.active else 'Acompanhar tela',state='normal' if free or self.vision.active else 'disabled')
        self.vision_state.set(f'TELA ATIVA · {self.vision.frames}/{MAX_FRAMES} capturas' if self.vision.active else 'Acompanhamento desligado')
        self.voice_button.configure(text='Parar voz' if self.voice.active else 'Conversar por voz',state='normal' if free or self.voice.active else 'disabled')
        self.voice_indicator.set({'listen':'VOZ · Ouvindo','chat':'VOZ · Pensando (microfone desligado)','speak':'VOZ · Respondendo (microfone desligado)'}.get(self.voice.phase,'Voz desligada'))
        self.input.configure(state='disabled' if self.voice.active else 'normal')
        for button in (self.send_button,self.mic_button,self.prepare_button,self.suggest_button,self.capture_button,self.meeting_start,self.detect_button):
            button.configure(state='normal' if free else 'disabled')
        self.hint_button.configure(state='normal' if free else 'disabled')
        self.route_button.configure(state='normal' if free else 'disabled')
        self.speak_button.configure(state='normal' if free and self.history else 'disabled')
        self.stop_button.configure(state='normal' if not free else 'disabled')
        self.meeting_stop.configure(state='normal' if self.meeting_active else 'disabled')
        self.analyze_button.configure(state='normal' if (free or (self.vision.active and not self.busy)) and self.screen else 'disabled')
        self.accept_button.configure(state='normal' if free and self.candidate and self.hub.permissions.allowed(COPILOT_RUN) and self.hub.permissions.allowed(COMPANION_CHAT) else 'disabled')
        self.confirm_button.configure(state='normal' if free and self.session.pending else 'disabled')
        self.auto_button.configure(state='normal' if self.hub.permissions.allowed(COMPANION_SPEAK) else 'disabled')
        if not self.hub.permissions.allowed(COMPANION_SPEAK): self.auto_speak.set(False)
    def draw(self):
        self.transcript.configure(state='normal'); self.transcript.delete('1.0','end')
        self.transcript.tag_configure('person',font=('Segoe UI',10,'bold'),spacing1=12,spacing3=4)
        self.transcript.tag_configure('message',spacing3=10)
        if not self.history:
            self.transcript.insert('end','Olá! Como posso ajudar hoje?\n','person')
            self.transcript.insert('end','Escreva o que precisa fazer. Posso ajudar a encontrar uma ferramenta, conversar sobre um assunto ou preparar uma ação. Você decide o que compartilhar.','message')
        for role,value in self.history:
            self.transcript.insert('end',('Você' if role=='user' else 'Aeris')+'\n','person')
            self.transcript.insert('end',value+'\n','message')
        self.transcript.configure(state='disabled'); self.transcript.see('end')
    def clear_workspace(self):
        self.stop()
        self.discard_screen()
        self.session.cancel(); self.action_input=None; self.preview.set('')
        self.clear()
        self.note.delete('1.0','end')
        self.meeting_text.configure(state='normal'); self.meeting_text.delete('1.0','end')
        self.meeting_chunks.clear()
        self.auto_speak.set(False)
        self.ai_hint=None; self.update_hint()
        self.status.set('Sessão limpa. Resultados pendentes descartados; registros protegidos preservados.')
        self.refresh()
    def reset_chat(self):
        if self.dirty() and not messagebox.askyesno('Nova conversa?','Limpar conversa e rascunho? As anotações e a reunião permanecem.',parent=self.hub.root): return
        self.session.cancel(); self.action_input=None; self.preview.set(''); self.clear()
    def input_changed(self,event=None):
        if self.input.edit_modified():
            self.session.cancel(); self.action_input=None; self.preview.set('')
        super().input_changed(event); self.update_hint(); self.refresh()
    def update_hint(self):
        draft=self.input.get('1.0','end-1c')
        if self.ai_hint and self.ai_hint[0]!=draft: self.ai_hint=None
        self.hint_name=self.ai_hint[1] if self.ai_hint else task_hint(draft)
        if self.hint_name:
            name=self.hint_name
            self.hint_text.set(('Sugestão da IA local: ' if self.ai_hint else 'Sugestão de ferramenta: ')+NAMES[name]+'\n'+HELP[name][0])
            if not self.hint_panel.winfo_manager():
                self.hint_panel.pack(fill='x',pady=(5,0),before=self.input)
        else:
            self.hint_panel.pack_forget()
    def route_tool(self):
        if self.busy or self.meeting_active or self.capture_timer is not None: return
        original=self.input.get('1.0','end-1c')
        try:
            text=validate_message(original)
            if len(text)>1000: raise ValueError('Descreva sua necessidade em até 1.000 caracteres.')
        except ValueError as exc: self.status.set(str(exc)); return
        if task_hint(original):
            self.update_hint(); self.status.set('Confira a sugestão local. Nenhuma ferramenta foi aberta.'); return
        if not self.model.get().strip():
            if not self.ai_open: self.toggle_ai_settings()
            self.configure_ai(); return
        model=self.model.get().strip()
        if not self.authorize(COMPANION_CHAT,'Enviar somente este pedido ao modelo local para recomendar uma ferramenta? Não inclui histórico, tela ou arquivos.'): return
        if original!=self.input.get('1.0','end-1c') or model!=self.model.get().strip(): return
        self.ai_hint=None; self.update_hint()
        if self.start(COMPANION_CHAT,lambda:(original,model,recommend_tool(model,text)),kind='route'):
            self.status.set('Procurando uma ferramenta adequada. Nenhuma ação será executada.')
    def open_hint(self):
        if not self.hint_name or self.busy or self.meeting_active:
            return
        name=self.hint_name
        if name in ('Meeting','Capture'):
            self.hub.navigate('meeting' if name=='Meeting' else 'notes')
            return
        self.hub.navigate('catalog')
        self.hub.goal.set('Todas')
        self.hub.category.set('Todas')
        self.hub.query.set(NAMES[name])
        self.hub.refresh()
        for i,module in enumerate(self.hub.visible):
            if module.name==name:
                self.hub.listbox.selection_clear(0,'end')
                self.hub.listbox.selection_set(i)
                self.hub.listbox.see(i)
                self.hub.show_selected()
                break
    def permissions_changed(self):
        self.session.cancel(); self.action_input=None; self.preview.set('')
        if self.voice.active and not self.voice_allowed(): self.stop_voice('Conversa por voz encerrada: permissão revogada.')
        if not self.hub.permissions.allowed(COMPANION_CHAT):
            self.ai_hint=None; self.update_hint()
        if not self.hub.permissions.allowed(COMPANION_SCREEN): self.discard_screen()
        if self.meeting_active and not self.hub.permissions.allowed(COMPANION_MIC): self.stop_meeting()
        super().permissions_changed()
    def suggest(self):
        if not self.model.get().strip():
            if not self.ai_open: self.toggle_ai_settings()
            self.configure_ai(); return
        if self.ensure_tool('Copilot') and self.authorize(COMPANION_CHAT,'Enviar apenas seu pedido ao modelo local?') and self.authorize(COPILOT_RUN,'Permitir preparar ações locais para sua confirmação?'):
            super().suggest()
    def accept_candidate(self):
        super().accept_candidate()
        if self.input.get('1.0','end-1c'): self.status.set('Revise o pedido e clique Preparar ação. Nada foi executado.')
    def prepare_action(self):
        if self.busy or self.meeting_active: return
        self.session.cancel(); self.preview.set('')
        text=self.input.get('1.0','end-1c')
        try: proposal=parse_command(text)
        except ValueError as e: self.status.set(str(e)); self.refresh(); return
        if not self.ensure_tool('Copilot') or not self.authorize(COPILOT_RUN,'Preparar ações locais? Cada execução ainda exige confirmação.'): return
        if text!=self.input.get('1.0','end-1c'): return
        if not self.ensure_tool(proposal.tool): return
        try: p=self.session.prepare(text)
        except (ValueError,PermissionError) as e: self.status.set(str(e)); return
        self.action_input=text; self.preview.set(p.preview); self.status.set('Revise a ação abaixo e confirme somente se estiver correta.'); self.refresh()
    def confirm_action(self):
        if self.busy or self.meeting_active: return
        if self.action_input!=self.input.get('1.0','end-1c'):
            self.session.cancel(); self.action_input=None; self.preview.set(''); self.status.set('Pedido alterado. Prepare novamente.'); self.refresh(); return
        self.action_input=None
        try: result=self.session.confirm()
        except (ValueError,PermissionError,KeyError) as e: result=str(e)
        self.preview.set(''); self.status.set(result); self.refresh()
    def context_changed(self,_=None):
        if self.vision.active and self.context_tabs.index('current')!=0: self.stop_vision()
    def toggle_vision(self):
        if self.vision.active:
            self.stop_vision(); return
        if self.closed or self.busy or self.voice.active or self.meeting_active or self.capture_timer is not None: return
        revision=self.hub.permissions.revision
        if not messagebox.askyesno('Acompanhar tela principal?', 'O Aeris fará capturas periódicas da tela principal a cada 15 segundos, por até 5 minutos ou 20 imagens. Apenas a última captura fica na memória. Nenhuma imagem será enviada automaticamente à IA. Um aviso flutuante permite parar, inclusive enquanto você trabalha em outros aplicativos. Evite abrir dados sensíveis.',parent=self.hub.root): return
        if self.closed or revision!=self.hub.permissions.revision: return
        if not self.authorize(COMPANION_SCREEN,'Autorizar captura de tela nesta sessão?'): return
        if self.closed or self.busy or self.voice.active or self.meeting_active or self.capture_timer is not None or self.vision.active or not self.hub.permissions.allowed(COMPANION_SCREEN): return
        self.discard_screen()
        badge=tk.Toplevel(self.hub.root); self.vision_badge=badge
        badge.title('Aeris · Tela'); badge.attributes('-topmost',True); badge.resizable(False,False)
        badge.protocol('WM_DELETE_WINDOW',self.stop_vision)
        panel=ttk.Frame(badge,padding=10); panel.pack(fill='both',expand=True)
        ttk.Label(panel,text='AERIS VISION · Captura autorizada',font=('Segoe UI',10,'bold')).pack(anchor='w')
        ttk.Button(panel,text='Parar acompanhamento',command=self.stop_vision).pack(fill='x',pady=(5,0))
        badge.update_idletasks()
        badge.geometry(f'+{max(0,badge.winfo_screenwidth()-badge.winfo_reqwidth()-30)}+32')
        self.vision.begin()
        self.vision_expiry=self.window.after(MAX_SECONDS*1000,self.vision_expired)
        self.vision_next()
    def vision_expired(self):
        if self.vision_expiry is not None:
            self.window.after_cancel(self.vision_expiry); self.vision_expiry=None
        self.stop_vision('Limite de acompanhamento atingido. Última captura disponível para revisão.')
    def stop_vision(self,message='Acompanhamento encerrado. Última captura disponível para revisão.'):
        self.vision.stop()
        for attr in ('vision_timer','vision_expiry'):
            timer=getattr(self,attr)
            if timer is not None:
                self.window.after_cancel(timer); setattr(self,attr,None)
        if self.vision_badge is not None:
            badge=self.vision_badge; self.vision_badge=None
            if badge.winfo_exists(): badge.destroy()
        if self.busy and self.kind=='monitor_screen': super().stop()
        self.status.set(message); self.refresh()
    def vision_next(self):
        self.vision_timer=None
        if not self.vision.active: return
        if not self.vision.allowed() or not self.hub.permissions.allowed(COMPANION_SCREEN) or self.closed:
            self.stop_vision(); return
        if self.vision_badge is None or not self.vision_badge.winfo_viewable():
            self.stop_vision('Acompanhamento encerrado: indicador não visível.'); return
        if self.busy or worker_for(self.hub).busy:
            self.vision_timer=self.window.after(1000,self.vision_next); return
        try:
            p=capture_process(); self.process=p
            if not self.start(COMPANION_SCREEN,lambda:read_capture(p),kind='monitor_screen'):
                p.kill()
                try: p.communicate(timeout=2)
                except (OSError,subprocess.TimeoutExpired): pass
                self.process=None; self.stop_vision('Não foi possível iniciar a captura.'); return
        except (OSError,PermissionError):
            self.stop_vision('Captura periódica indisponível.'); return
        self.status.set('TELA ATIVA · atualizando captura local.')
    def show_capture(self,result):
        image=tk.PhotoImage(data=base64.b64encode(result).decode('ascii'))
        factor=max(1,(image.width()+229)//230,(image.height()+259)//260)
        self.photo=image.subsample(factor,factor); self.screen=result
        self.image_label.configure(image=self.photo,text='')
    def capture(self):
        if self.busy or self.meeting_active or self.voice.active or self.vision.active or self.capture_timer is not None: return
        if not self.authorize(COMPANION_SCREEN,'Capturar uma imagem da tela principal? A imagem fica na memória até você descartar ou fechar. Ela não será enviada automaticamente.'): return
        self.discard_screen(); self.hub.root.withdraw()
        self.status.set('Capturando uma imagem da tela principal…')
        self.capture_timer=self.hub.root.after(350,self.capture_now); self.refresh()
    def capture_now(self):
        self.capture_timer=None
        if not self.hub.permissions.allowed(COMPANION_SCREEN): self.hub.root.deiconify(); self.refresh(); return
        try:
            if worker_for(self.hub).busy: raise OSError('Outra operação local ativa.')
            p=capture_process(); self.process=p
            if not self.start(COMPANION_SCREEN,lambda:read_capture(p),kind='screen'): p.kill(); self.process=None; self.hub.root.deiconify()
        except (OSError,PermissionError): self.hub.root.deiconify(); self.status.set('Captura indisponível.'); self.refresh()
    def discard_screen(self):
        if self.vision.active: self.stop_vision()
        self.screen=None; self.photo=None
        if hasattr(self,'image_label'): self.image_label.configure(image='',text='Nenhuma captura')
        if self.capture_timer is not None:
            self.hub.root.after_cancel(self.capture_timer); self.capture_timer=None; self.hub.root.deiconify()
        if self.busy and self.kind in ('screen','vision'): super().stop()
        self.refresh()
    def analyze(self):
        if self.busy or self.meeting_active or self.voice.active or not self.screen: return
        if self.vision.active: self.stop_vision('Acompanhamento pausado para revisar a captura.')
        if not self.model.get().strip():
            if not self.ai_open: self.toggle_ai_settings()
            self.configure_ai(); return
        if not self.authorize(COMPANION_CHAT,'Permitir comunicação com o modelo local?'): return
        raw=self.screen; model=self.model.get().strip(); question=self.input.get('1.0','end-1c').strip() or 'Explique o que aparece nesta imagem e como posso continuar.'
        try: validate_message(question)
        except ValueError as e: self.status.set(str(e)); return
        revision=self.hub.permissions.revision
        if not messagebox.askyesno('Enviar captura?', 'Enviar apenas esta imagem revisada e a pergunta ao modelo de visão local? Não inclui histórico ou outros arquivos.',parent=self.hub.root): return
        if self.screen is not raw or revision!=self.hub.permissions.revision or model!=self.model.get().strip() or question!=(self.input.get('1.0','end-1c').strip() or 'Explique o que aparece nesta imagem e como posso continuar.') or not self.hub.permissions.allowed(COMPANION_CHAT): return
        if self.start(COMPANION_SCREEN,lambda:(question,describe_screen(model,question,raw)),kind='vision'):
            self.status.set('Analisando uma captura, não a tela ao vivo…')
    def append_answer(self):
        if self.history and self.history[-1][0]=='assistant': self.note.insert('end',('\n\n' if self.note.get('1.0','end-1c') else '')+self.history[-1][1])
    def save_note(self):
        text=self.note.get('1.0','end-1c').strip()
        if not text: return
        if not messagebox.askyesno('Salvar anotação?', 'Criar uma anotação temporária com o texto revisado?',parent=self.hub.root): return
        if text!=self.note.get('1.0','end-1c').strip() or not self.ensure_tool('Capture'): return
        from aeris.content import CaptureStore
        if self.hub.capture_store is None: self.hub.capture_store=CaptureStore(self.hub.invalidate_search)
        try: self.hub.capture_store.save('Anotação de trabalho',text,None)
        except ValueError as e: self.status.set(str(e)); return
        if self.hub.alive(self.hub.capture_window): self.hub.capture_window.refresh()
        self.status.set('Anotação salva nesta sessão. O bloco continua disponível para edição.')
    def start_meeting(self):
        if self.busy or self.meeting_active: return
        revision=self.hub.permissions.revision
        if not messagebox.askyesno('Transcrição de reunião','Todos os participantes foram avisados e concordam com a transcrição? O microfone permanecerá ativo em blocos até Parar, fechar, revogar ou atingir o limite de 20 blocos. Nenhum áudio é gravado em arquivo pelo Aeris.',parent=self.hub.root): return
        if self.closed or self.hub.permissions.revision!=revision: return
        if not self.authorize(COMPANION_MIC,'Autorizar o microfone nesta sessão?'): return
        if self.busy or self.meeting_active: return
        self.meeting_active=True; self.meeting_generation+=1; self.meeting_chunks=[]
        self.meeting_text.configure(state='disabled'); self.meeting_next(); self.refresh()
    def meeting_next(self):
        self.meeting_timer=None
        if not self.meeting_active or not self.hub.permissions.allowed(COMPANION_MIC) or len(self.meeting_chunks)>=20: self.stop_meeting(); return
        try:
            if worker_for(self.hub).busy: raise OSError()
            p=speech_process(); self.process=p
            def listen():
                try:
                    out,_=p.communicate(json.dumps({'action':'listen','text':''}),timeout=18)
                    if p.returncode: raise OSError('Sem transcrição.')
                    return validate_message(strict_json(out,32768))
                except subprocess.TimeoutExpired: p.kill(); p.communicate(); raise
            if not self.start(COMPANION_MIC,listen,kind='meeting'): p.kill(); self.process=None; raise OSError()
        except (OSError,PermissionError): self.stop_meeting(); self.status.set('Microfone ou reconhecedor pt-BR indisponível.'); return
        self.status.set('MICROFONE ATIVO · reunião · pressione Parar para encerrar.')
    def stop_meeting(self):
        self.meeting_active=False; self.meeting_generation+=1
        if self.meeting_timer is not None: self.window.after_cancel(self.meeting_timer); self.meeting_timer=None
        if self.busy and self.kind=='meeting': super().stop()
        self.meeting_text.configure(state='normal'); self.status.set('Microfone desligado. Revise a transcrição antes de salvar.'); self.refresh()
    def meeting_summary(self):
        if self.meeting_active or self.busy: return
        text=self.meeting_text.get('1.0','end-1c').strip()
        prompt='Resuma a transcrição abaixo, separando decisões, dúvidas e ações. Não invente participantes, prazos ou responsáveis.\n\n'+text
        if not text or len(prompt)>4000:
            if self.meeting_text.tag_ranges('sel'):
                text=self.meeting_text.get('sel.first','sel.last').strip()
                prompt='Resuma o trecho abaixo, separando decisões, dúvidas e ações. Não invente participantes, prazos ou responsáveis.\n\n'+text
            if not text or len(prompt)>4000:
                self.status.set('Selecione um trecho de até 3.800 caracteres para resumir.'); return
        if self.input.get('1.0','end-1c').strip(): self.status.set('Envie ou limpe o rascunho da conversa primeiro.'); return
        self.input.insert('1.0',prompt); self.status.set('Resumo preparado no editor. Revise e clique Enviar.')
    def save_meeting(self):
        if self.meeting_active: return
        text=self.meeting_text.get('1.0','end-1c').strip()
        if not text: return
        if not messagebox.askyesno('Salvar ata?', 'Salvar a transcrição revisada como anotação de reunião nesta sessão?',parent=self.hub.root): return
        if text!=self.meeting_text.get('1.0','end-1c').strip() or not self.ensure_tool('Meeting'): return
        from aeris.meeting import MeetingStore
        if self.hub.meeting_store is None: self.hub.meeting_store=MeetingStore()
        try: self.hub.meeting_store.add('Reunião transcrita',date.today().isoformat(),'','',text,())
        except ValueError as e: self.status.set(str(e)); return
        if self.hub.alive(self.hub.meeting_window): self.hub.meeting_window.render()
        self.status.set('Ata salva na sessão. Revise participantes e decisões em Reuniões.')
    def stop(self):
        if self.vision.active: self.stop_vision()
        if self.voice.active: self.stop_voice()
        if self.meeting_active: self.stop_meeting()
        if self.capture_timer is not None: self.discard_screen()
        super().stop()
        if self.hub.root.state()=='withdrawn': self.hub.root.deiconify()
    def poll(self):
        if self.kind not in ('screen','vision','meeting','models','route','voice_listen','voice_chat','voice_speak','monitor_screen'): return super().poll()
        self.timer=None
        if self.closed: return
        try: job,ok,result=self.results.get_nowait()
        except queue.Empty: self.schedule_poll(); return
        self.busy=False; self.process=None
        kind=self.kind
        if kind=='screen': self.hub.root.deiconify()
        valid=job==self.job and self.hub.permissions.allowed(self.cap)
        if kind in ('voice_listen','voice_chat','voice_speak'):
            if valid: self.voice_result(kind,ok,result)
            elif self.voice.active: self.stop_voice()
        elif valid and kind=='route':
            if ok:
                original,model,name=result
                if original==self.input.get('1.0','end-1c') and model==self.model.get().strip():
                    self.ai_hint=(original,name) if name else None
                    self.update_hint()
                    self.status.set('Confira a ferramenta sugerida.' if name else 'Nenhuma ferramenta adequada encontrada. Você pode conversar normalmente.')
                else: self.status.set('Pedido ou modelo alterado. Sugestão descartada.')
            else: self.status.set('Não foi possível obter uma sugestão válida do modelo local.')
        elif valid and kind=='models':
            if ok and result:
                self.model_entry.configure(values=result)
                if len(result)==1 and not self.model.get().strip(): self.model.set(result[0])
                self.status.set('Modelos locais encontrados. Escolha um modelo para conversar.')
            else: self.status.set('Nenhum modelo local encontrado. Abra Ajuda para configurar o Ollama.')
        elif kind=='monitor_screen':
            if valid and self.vision.allowed():
                try:
                    if not ok: raise ValueError('Falha na captura.')
                    self.show_capture(result); self.vision.record()
                except (tk.TclError,ValueError): self.stop_vision('Não foi possível atualizar a captura.')
                else:
                    if self.vision.allowed():
                        self.vision_timer=self.window.after(INTERVAL_MS,self.vision_next)
                        self.status.set('TELA ATIVA · última captura pronta; nenhuma imagem enviada.')
                    else: self.vision_expired()
            elif self.vision.active: self.stop_vision()
        elif valid and kind=='screen':
            if ok:
                try:
                    self.show_capture(result)
                    self.status.set('Captura pronta. Revise antes de enviar.')
                except (tk.TclError,ValueError): self.status.set('Não foi possível mostrar a captura.')
            else: self.status.set('Captura indisponível.')
        elif valid and kind=='vision':
            if ok and self.hub.permissions.allowed(COMPANION_CHAT):
                question,response=result; self.history.extend((('user',('[Captura pontual] '+question)[:4000]),('assistant',response))); self.history=self.history[-MAX_HISTORY:]; self.draw(); self.status.set('Análise concluída. A IA pode errar.')
            else: self.status.set('Modelo de visão indisponível ou permissão revogada.')
        elif valid and kind=='meeting' and self.meeting_active:
            if ok:
                current=self.meeting_text.get('1.0','end-1c')
                if len(current)+len(result)+1>8000: self.stop_meeting(); self.status.set('Limite de transcrição atingido; revise e salve.'); self.refresh(); return
                self.meeting_text.configure(state='normal'); self.meeting_text.insert('end',('\n' if current else '')+result); self.meeting_text.configure(state='disabled'); self.meeting_text.see('end')
                self.meeting_chunks.append(result)
                if len(self.meeting_chunks)<20: self.meeting_timer=self.window.after(350,self.meeting_next)
                else: self.stop_meeting()
            else: self.stop_meeting(); self.status.set('Transcrição pausada: silêncio ou recurso indisponível. Revise e reinicie se necessário.')
        self.refresh()
    def dirty(self):
        return super().dirty() or bool(self.screen or self.note.get('1.0','end-1c') or self.meeting_text.get('1.0','end-1c') or self.meeting_active)
    def destroyed(self,event):
        if event.widget is self.window:
            self.voice.stop(); self.vision.stop()
            if self.vision_badge is not None:
                try: self.vision_badge.destroy()
                except tk.TclError: pass
                self.vision_badge=None
            for timer in (self.meeting_timer,self.capture_timer,self.voice_timer,self.vision_timer,self.vision_expiry):
                if timer is not None:
                    try: self.hub.root.after_cancel(timer)
                    except tk.TclError: pass
            self.screen=None; self.photo=None; self.meeting_chunks.clear(); self.meeting_active=False
        super().destroyed(event)

class ExperienceHub(Hub):
    def __init__(self,root,settings=None):
        super().__init__(root,settings)
        root.bind('<Control-f>',lambda _:self.navigate('catalog'))
    def build(self):
        super().build()
        self.legacy_side,self.catalog=self.root.winfo_children()[:2]
        self.legacy_side.pack_forget(); self.catalog.pack_forget()
        self.legacy_catalog=self.catalog; self.build_catalog()
        sw=self.root.winfo_screenwidth(); sh=self.root.winfo_screenheight()
        width=min(1240,max(760,sw-44)); height=min(780,max(540,sh-100))
        self.root.geometry(f'{width}x{height}+16+12'); self.root.minsize(min(870,width),min(570,height))
        side=ttk.Frame(self.root,padding=14,width=184,style='Experience.Side.TFrame'); side.pack(side='left',fill='y'); side.pack_propagate(False)
        ttk.Label(side,text='aeris.',style='Experience.Brand.TLabel').pack(anchor='w')
        ttk.Label(side,text='Eficiência e\nSimplicidade.',style='Experience.Side.TLabel').pack(anchor='w',pady=(0,22))
        self.nav_buttons={}
        for label,command in [('Conversar',lambda:self.navigate('chat')),('Tela',lambda:self.navigate('screen')),('Anotações',lambda:self.navigate('notes')),('Reuniões',lambda:self.navigate('meeting')),('Tarefas',lambda:self.open_friendly('Checklist')),('Ferramentas',lambda:self.navigate('catalog'))]:
            button=ttk.Button(side,text=label,command=command,style='Experience.Nav.TButton'); button.pack(fill='x',pady=2); self.nav_buttons[label]=button
        ttk.Separator(side).pack(fill='x',pady=18)
        ttk.Button(side,text='Configurações',command=self.open_appearance,style='Experience.Nav.TButton').pack(fill='x',pady=3)
        ttk.Button(side,text='Privacidade',command=self.open_privacy,style='Experience.Nav.TButton').pack(fill='x',pady=3)
        ttk.Button(side,text='Permissões',command=self.open_permissions,style='Experience.Nav.TButton').pack(fill='x',pady=3)
        ttk.Label(side,text='K&G Vision\nVersão em desenvolvimento',style='Experience.Side.TLabel',wraplength=150).pack(side='bottom',anchor='w')
        self.conversation=Conversation(self,self.root)
        self.navigate('chat')
    def build_catalog(self):
        self.catalog=ttk.Frame(self.root,padding=18)
        f=self.catalog
        ttk.Label(f,text='O que você deseja fazer?',style='Experience.Title.TLabel').pack(anchor='w')
        ttk.Label(f,text='Escolha um objetivo ou pesquise pelo que precisa fazer.',style='Experience.Muted.TLabel').pack(anchor='w',pady=(2,12))
        self.goal=tk.StringVar(self.root,'Todas')
        goals=ttk.Frame(f); goals.pack(fill='x',pady=(0,12))
        for i,name in enumerate(('Todas',*GOALS)):
            goals.columnconfigure(i%2,weight=1,uniform='goal')
            ttk.Radiobutton(goals,text=name,value=name,variable=self.goal,command=self.refresh,style='Experience.Goal.TRadiobutton').grid(row=i//2,column=i%2,sticky='ew',padx=3,pady=2)
        ttk.Label(f,text='Buscar por nome, tarefa ou exemplo',style='Experience.Muted.TLabel').pack(anchor='w')
        filters=ttk.Frame(f); filters.pack(fill='x',pady=(0,8))
        self.search=ttk.Entry(filters,textvariable=self.query); self.search.pack(side='left',fill='x',expand=True,ipady=5)
        self.search.bind('<Return>',self.focus_results); self.search.bind('<Escape>',lambda _:self.clear_filters())
        ttk.Button(filters,text='Limpar',command=self.clear_filters).pack(side='right',padx=(5,0))
        self.category_display=tk.StringVar(self.root,'Todas')
        self.category_box=ttk.Combobox(filters,textvariable=self.category_display,values=('Todas',*CATEGORIES.values()),state='readonly',width=15)
        self.category_box.bind('<<ComboboxSelected>>',self.choose_category)
        self.count=ttk.Label(f,text='',style='Experience.Muted.TLabel'); self.count.pack(anchor='w',pady=(0,6))
        body=ttk.Frame(f); body.pack(fill='both',expand=True); body.columnconfigure(0,weight=3); body.columnconfigure(1,weight=2); body.rowconfigure(0,weight=1)
        left=ttk.Frame(body); left.grid(row=0,column=0,sticky='nsew',padx=(0,10))
        self.listbox=tk.Listbox(left,font=('Segoe UI',11),relief='flat',highlightthickness=1,exportselection=False,activestyle='none',width=24)
        self.listbox.pack(side='left',fill='both',expand=True)
        sb=ttk.Scrollbar(left,command=self.listbox.yview); sb.pack(side='right',fill='y'); self.listbox.configure(yscrollcommand=sb.set)
        self.listbox.bind('<<ListboxSelect>>',self.show_selected); self.listbox.bind('<Return>',self.open_selected); self.listbox.bind('<Double-1>',self.open_selected)
        detail=ttk.Frame(body,padding=14,style='Experience.Card.TFrame'); detail.grid(row=0,column=1,sticky='nsew')
        self.detail_name=ttk.Label(detail,text='',style='Experience.Detail.TLabel',wraplength=250,justify='left'); self.detail_name.pack(anchor='w',fill='x')
        self.detail_status=ttk.Label(detail,text='',style='Experience.Card.TLabel',wraplength=215); self.detail_status.pack(anchor='w',pady=(4,12),fill='x')
        self.detail_desc=ttk.Label(detail,text='',style='Experience.Card.TLabel',wraplength=215,justify='left'); self.detail_desc.pack(anchor='w',fill='x')
        self.example=ttk.Label(detail,text='',style='Experience.Card.TLabel',wraplength=215,justify='left'); self.example.pack(anchor='w',pady=(12,6),fill='x')
        self.toggle=ttk.Button(detail,text='Ativar')
        self.launch=ttk.Button(detail,text='Abrir',style='Experience.Primary.TButton')
    def clear_filters(self):
        if hasattr(self,'goal'): self.goal.set('Todas')
        return super().clear_filters()
    def choose_category(self,_=None):
        selected=self.category_display.get()
        self.category.set(next((key for key,value in CATEGORIES.items() if value==selected),'Todas'))
    def navigate(self,view):
        if view!='chat' and self.conversation.voice.active: self.conversation.stop_voice()
        if view!='screen' and self.conversation.vision.active: self.conversation.stop_vision()
        self.catalog.pack_forget(); self.conversation.window.pack_forget()
        if view=='catalog': self.catalog.pack(fill='both',expand=True); self.search.focus_set()
        else:
            self.conversation.window.pack(fill='both',expand=True)
            if view in ('screen','notes','meeting'):
                self.conversation.set_context(True)
                self.conversation.context_tabs.select(('screen','notes','meeting').index(view))
        self.view=view
        active={'catalog':'Ferramentas','screen':'Tela','notes':'Anotações','meeting':'Reuniões'}.get(view,'Conversar')
        for label,button in self.nav_buttons.items(): button.configure(style='Experience.Active.TButton' if label==active else 'Experience.Nav.TButton')
    def open_search_result(self,result):
        found=super().open_search_result(result)
        if found and result.source=='Ferramentas': self.navigate('catalog')
        return found
    def open_tool(self,name):
        super().open_tool(name)
        if name not in self.tool_buttons or not self.enabled(name):
            return
        instance=getattr(self,name.lower()+'_window',None)
        if not self.alive(instance):
            return
        window=instance.window
        if isinstance(window,tk.Toplevel):
            window.title('Aeris | '+NAMES.get(name,name))
    def open_friendly(self,name):
        if not self.enabled(name): self.toggle_tool(name)
        if self.enabled(name): self.open_tool(name)
    def refresh(self,*_):
        old=self.listbox.curselection()
        selected=self.visible[old[0]].name if old and old[0]<len(self.visible) else None
        self.listbox.delete(0,'end')
        from aeris.registry import normalize
        self.category_display.set(CATEGORIES.get(self.category.get(),'Todas'))
        query=normalize(self.query.get()).split()
        goal=self.goal.get() if hasattr(self,'goal') else 'Todas'
        self.visible=tuple(m for m in self.modules if (goal=='Todas' or m.name in GOALS.get(goal,())) and (self.category.get()=='Todas' or m.category==self.category.get()) and all(q in normalize(' '.join((m.name,NAMES.get(m.name,m.name),m.description,m.category,CATEGORIES.get(m.category,m.category),*HELP.get(m.name,('',''))))) for q in query))
        for m in self.visible: self.listbox.insert('end',f'  {NAMES.get(m.name,m.name)}')
        self.count.configure(text=f'{len(self.visible)} ferramentas encontradas')
        if self.visible:
            index=next((i for i,m in enumerate(self.visible) if m.name==selected),0)
            self.listbox.selection_set(index); self.listbox.activate(index); self.listbox.see(index)
        self.show_selected()
    def show_selected(self,*_):
        super().show_selected(*_)
        self.example.configure(text='')
        sel=self.listbox.curselection()
        if sel and sel[0]<len(self.visible):
            m=self.visible[sel[0]]; self.detail_name.configure(text=NAMES.get(m.name,m.name))
            description,example=HELP.get(m.name,(m.description,'')); self.detail_desc.configure(text=description); self.example.configure(text='COMO USAR\n'+example)
            if m.name in self.tool_buttons:
                self.toggle.pack_forget()
                self.launch.configure(text='Abrir ferramenta',command=lambda name=m.name:self.open_friendly(name))
                self.launch.pack(fill='x',pady=(14,4))
                if self.enabled(m.name):
                    self.toggle.configure(text='Desativar ferramenta',command=lambda name=m.name:self.toggle_tool(name))
                    self.toggle.pack(fill='x',pady=4)
                self.detail_status.configure(text='Disponível nesta sessão' if self.enabled(m.name) else 'Pronta para ativar ao abrir')
    def apply_appearance(self):
        super().apply_appearance()
        from aeris.theme import PALETTES
        p=PALETTES[self.settings.appearance.theme]; style=ttk.Style(self.root)
        style.configure('Experience.Goal.TRadiobutton',padding=(8,5),font=('Segoe UI',10))
        style.configure('Experience.Title.TLabel',font=('Segoe UI',21,'bold'))
        style.configure('TNotebook.Tab',padding=(12,8),font=('Segoe UI',10))
        style.configure('Experience.Brand.TLabel',font=('Segoe UI',30,'bold'),background='#193D30',foreground='#FFFFFF')
        style.configure('Experience.Side.TFrame',background='#193D30')
        style.configure('Experience.Side.TLabel',background='#193D30',foreground='#D9E7DF',font=('Segoe UI',10))
        style.configure('Experience.Card.TFrame',background=p['field'])
        style.configure('Experience.Card.TLabel',background=p['field'],foreground=p['deep'])
        style.configure('Experience.Detail.TLabel',background=p['field'],foreground=p['deep'],font=('Segoe UI',17,'bold'))
        style.configure('Experience.Section.TLabel',font=('Segoe UI',10,'bold'),foreground=p['forest'])
        style.configure('Experience.Subtitle.TLabel',font=('Segoe UI',13,'bold'))
        style.configure('Experience.Muted.TLabel',font=('Segoe UI',10),foreground=p['deep'])
        style.configure('Experience.Nav.TButton',padding=(12,8),anchor='w',background='#193D30',foreground='#FFFFFF',borderwidth=0,relief='flat')
        style.map('Experience.Nav.TButton',background=[('active','#37614E'),('!disabled','#193D30')],foreground=[('!disabled','#FFFFFF')])
        style.configure('Experience.Active.TButton',padding=(12,8),anchor='w',background='#DCEFE3',foreground='#193D30',borderwidth=0,relief='flat')
        style.map('Experience.Active.TButton',background=[('active','#C9E6D4'),('!disabled','#DCEFE3')],foreground=[('!disabled','#193D30')])
        style.configure('Experience.Primary.TButton',padding=(16,8),background='#285640',foreground='#FFFFFF')
        style.map('Experience.Primary.TButton',background=[('active','#397557'),('disabled',p['soft'])],foreground=[('disabled',p['deep']),('!disabled','#FFFFFF')])
    def permissions_changed(self):
        super().permissions_changed()
        if hasattr(self,'conversation'): self.conversation.permissions_changed()
    def clear_session(self):
        if not super().clear_session(): return False
        self.conversation.clear_workspace()
        return True
    def close(self):
        if self.conversation.dirty() and not messagebox.askyesno('Encerrar Aeris?', 'A conversa, captura, transcrição e rascunhos desta sessão serão descartados. Encerrar?',parent=self.root): return
        self.conversation.stop()
        super().close()

def main():
    root=tk.Tk(); ExperienceHub(root); root.mainloop()
