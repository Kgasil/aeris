"""Conversation-first desktop workspace. Reuses existing session stores and capabilities."""
import base64
from datetime import date
from dataclasses import replace
from time import monotonic
import json
import queue
import subprocess
import threading
import tkinter as tk
from tkinter import ttk,messagebox,filedialog
from aeris.hub import Hub, COLORS
from aeris.experience_help import HELP
from aeris.intelligence import recommend_tool
from aeris.voice_session import VoiceSession, MAX_TURNS
from aeris.vision_session import VisionSession, INTERVAL_MS, MAX_SECONDS, MAX_FRAMES
from aeris.visual_question import VisualQuestion
from aeris.ready import inspect_environment, model_selection, check_model, test_model_response, TEST_PROMPT
from aeris.ai_setup import ManagedRuntime, load_choice, reset_endpoint
from aeris.catalog_index import CatalogIndex
from aeris.polish import compact_workspace
from aeris.theme import wind_mark, polish_tool_window
from aeris.settings import FAVORITES
from aeris.consent_ui import ask_permission, ask_confirmation
from aeris.voice_feedback import feedback_process, listen_with_feedback, ERRORS
from aeris.meeting_audio import available as loopback_available, model_path, start_loopback, read_loopback, BLOCK_SECONDS
from aeris.meeting_intelligence import prepare_minutes
from aeris.companion_ui import CompanionWindow
from aeris.companion import chat,validate_message,speech_process,MAX_HISTORY,SYSTEM
from aeris.copilot import CopilotSession,parse_command
from aeris.permissions import (COMPANION_CHAT,COMPANION_MIC,COMPANION_SPEAK,COPILOT_RUN,
                              COMPANION_SCREEN, MEETING_LOOPBACK)
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
        self.ai_runtime=ManagedRuntime(hub.settings.path); self.setup_cancel=None; self.setup_progress=queue.Queue(); self.test_started=None; self.progress_running=False
        self.chat_allowed=False; self.kind=None; self.candidate=None
        self.stream_pending=None; self.stream_cancel=None; self.stream_chunks=queue.Queue(); self.stream_partial=''; self.stream_started=None; self.stream_first=None
        self.voice=VoiceSession(); self.voice_timer=None
        self.voice_events=queue.Queue(); self.voice_capture_job=None; self.voice_capture_state='preparing'; self.voice_level=0; self.voice_partial=''; self.voice_cancel=None
        self.vision=VisionSession(); self.vision_timer=None; self.vision_expiry=None; self.vision_badge=None
        self.vision_phase='idle'; self.vision_pending=None; self.vision_answer=''; self.vision_message=''; self.screen_stamp=None
        self.session=CopilotSession(hub); self.action_input=None; self.screen=None; self.photo=None
        self.capture_timer=None; self.screen_question=None; self.visual_invalid=False; self.meeting_active=False
        self.meeting_timer=None; self.meeting_generation=0; self.meeting_chunks=[]
        self.meeting_source='mic'; self.meeting_model=None; self.meeting_badge=None; self.meeting_review=None
        self.meeting_phase='idle'; self.meeting_silences=0
        self.window=w=ttk.Frame(parent,padding=(24,16)); w.bind('<Destroy>',self.destroyed,add='+')
        top=ttk.Frame(w); top.pack(fill='x',pady=(0,8))
        ttk.Label(top,text='Assistente',style='Experience.Title.TLabel').pack(side='left')
        ttk.Button(top,text='Nova conversa',command=self.reset_chat).pack(side='right')
        ttk.Button(top,text='Alternar tema',command=self.hub.toggle_theme).pack(side='right',padx=(0,8))
        ai_header=ttk.Frame(w,padding=(10,6),style='Experience.Card.TFrame'); ai_header.pack(fill='x',pady=(0,6))
        self.ai_state=tk.StringVar(w,'IA local · escolha um modelo')
        ttk.Label(ai_header,textvariable=self.ai_state,style='Experience.Model.TLabel',wraplength=330).pack(side='left',fill='x',expand=True)
        self.ai_toggle=ttk.Button(ai_header,text='Configurar IA',command=self.toggle_ai_settings,style='Experience.Quiet.TButton')
        self.ai_toggle.pack(side='right')
        self.ai_settings=ttk.Frame(w,padding=12,style='Experience.Card.TFrame')
        setup=self.ai_settings
        ttk.Label(setup,text='Configure seu assistente',style='Experience.Card.TLabel',font=('Segoe UI',13,'bold')).pack(anchor='w')
        ttk.Label(setup,text='Escolha um modelo Ollama local. Conversas ficam no computador; downloads exigem sua autorização.',wraplength=580,style='Experience.Card.TLabel').pack(anchor='w',pady=(4,6))
        modelrow=ttk.Frame(setup,style='Experience.Card.TFrame'); modelrow.pack(fill='x')
        self.ai_header=ai_header
        self.mode_status=tk.StringVar(w,'Pronto · microfone e tela desligados')
        modes=ttk.Frame(w,padding=(10,2)); modes.pack(fill='x',pady=(0,8))
        ttk.Label(modes,textvariable=self.mode_status,style='Experience.Muted.TLabel',wraplength=380).pack(side='left',fill='x',expand=True)
        self.global_stop=ttk.Button(modes,text='Parar atividade',command=self.stop,style='Experience.Stop.TButton'); self.global_stop.pack(side='right')
        self.activity_progress=ttk.Progressbar(w,mode='indeterminate',style='Experience.Horizontal.TProgressbar')
        self.ai_open=False
        ttk.Label(modelrow,text='Modelo local').pack(side='left')
        self.model=tk.StringVar(w,'')
        self.model_entry=ttk.Combobox(modelrow,textvariable=self.model,width=19); self.model_entry.pack(side='left',padx=6)
        self.detect_button=ttk.Button(modelrow,text='Detectar modelos',command=self.detect_models); self.detect_button.pack(side='left')
        self.test_ai_button=ttk.Button(modelrow,text='Testar IA',command=self.test_ai); self.test_ai_button.pack(side='left',padx=4)
        self.ready_state=tk.StringVar(w,'Nenhum diagnóstico executado.')
        ttk.Label(setup,textvariable=self.ready_state,wraplength=580,style='Experience.Card.TLabel').pack(anchor='w',pady=(6,0))
        ttk.Label(setup,text='Durante a preparação, funções de IA ficam pausadas; ferramentas independentes continuam disponíveis.',wraplength=580,style='Experience.Card.TLabel').pack(anchor='w',pady=(4,0))
        info=inspect_environment()
        voice='Windows detectado; voz e tela ainda não testadas.' if info.windows else 'Voz e tela nativas exigem Windows.'
        audio=('Áudio interno: dependências encontradas; modelo e dispositivo ainda não testados.' if info.loopback_candidate else 'Áudio interno: opcional, exige execução por código-fonte no Windows e dependências próprias.')
        ttk.Label(setup,text=voice+' '+audio,wraplength=580,style='Experience.Card.TLabel').pack(anchor='w',pady=4)
        self.setup_button=ttk.Button(setup,text='Preparar IA automaticamente',command=self.configure_ai,style='Experience.Primary.TButton'); self.setup_button.pack(anchor='w')
        self.setup_bar=ttk.Progressbar(setup,mode='indeterminate',style='Experience.Horizontal.TProgressbar'); self.setup_phase=tk.StringVar(w,''); self.setup_detail=ttk.Label(setup,textvariable=self.setup_phase,wraplength=580,style='Experience.Card.TLabel')
        self.setup_result=''
        trace_window(w,self.model,self.model_changed)
        self.panes=panes=ttk.Frame(w); panes.pack(fill='both',expand=True)
        panes.columnconfigure(0,weight=3); panes.columnconfigure(1,weight=0); panes.rowconfigure(0,weight=1)
        left=ttk.Frame(panes,padding=(0,0,8,0)); right=ttk.Frame(panes,padding=(8,0,0,0)); left.grid(row=0,column=0,sticky='nsew'); right.grid(row=0,column=1,sticky='nsew'); self.context_panel=right; self.chat_panel=left; right.grid_remove(); self.context_open=False; self.compact=False
        self.composer=ttk.Frame(left,padding=(12,8),style='Experience.Card.TFrame'); self.composer.pack(side='bottom',fill='x',pady=(8,0))
        chathead=ttk.Frame(left); chathead.pack(fill='x',pady=(0,6))
        ttk.Label(chathead,text='CONVERSA PRIVADA',style='Experience.Section.TLabel').pack(side='left')
        self.context_toggle=ttk.Button(chathead,text='Mostrar contexto',command=self.toggle_context,style='Experience.Quiet.TButton')
        self.context_toggle.pack(side='right')
        chatbox=self.chatbox=ttk.Frame(left); chatbox.pack(fill='both',expand=True)
        self.welcome=ttk.Frame(chatbox,padding=8,height=96); self.welcome.pack_propagate(False)
        # Reserve shortcuts before the flexible hero, so compact windows cannot crop a card.
        quick=ttk.Frame(self.welcome); quick.pack(side='bottom',fill='x',pady=(2,0))
        self.quick_actions={}
        for index,(label,detail,view) in enumerate((('Tela','Analisar captura','screen'),('Anotações','Organizar ideias','notes'),('Reuniões','Transcrever e revisar','meeting'))):
            button=ttk.Button(quick,text=label+'\n'+detail,command=lambda v=view:self.hub.navigate(v),style='Experience.Launch.TButton')
            button.grid(row=0,column=index,sticky='nsew',padx=3); self.quick_actions[view]=button
            quick.columnconfigure(index,weight=1,uniform='launch')
        center=ttk.Frame(self.welcome); center.pack(fill='both',expand=True)
        hero=ttk.Frame(center); hero.place(relx=.5,rely=.5,anchor='center')
        self.welcome_mark=wind_mark(hero,hub.settings.appearance.theme,size=36,surface='air'); self.welcome_mark.pack(pady=(0,2))
        self.hero_title=ttk.Label(hero,text='Como posso ajudar?',style='Experience.Hero.TLabel',anchor='center'); self.hero_title.pack(fill='x')
        self.hero_subtitle=ttk.Label(hero,text='Trabalhe com a IA local, do seu jeito.',style='Experience.Muted.TLabel',wraplength=320,justify='center',anchor='center'); self.hero_subtitle.pack(fill='x',pady=(2,0))
        center.bind('<Configure>',self.resize_hero,add='+')
        self.transcript=tk.Text(chatbox,wrap='word',height=5,state='disabled',font=('Segoe UI',11),padx=16,pady=14,relief='flat',highlightthickness=1)
        self.transcript.pack(side='left',fill='both',expand=True)
        self.chat_scroll=ttk.Scrollbar(chatbox,command=self.transcript.yview); self.chat_scroll.pack(side='right',fill='y'); self.transcript.configure(yscrollcommand=self.chat_scroll.set)
        self.hint_panel=ttk.Frame(self.composer,padding=8,style='Experience.Card.TFrame')
        self.hint_text=tk.StringVar(w,'')
        ttk.Label(self.hint_panel,textvariable=self.hint_text,wraplength=330,justify='left',style='Experience.Card.TLabel').pack(fill='x')
        self.hint_button=ttk.Button(self.hint_panel,text='Conhecer ferramenta',command=self.open_hint)
        self.hint_button.pack(anchor='w',pady=(4,0))
        self.hint_name=None; self.ai_hint=None
        self.input=tk.Text(self.composer,wrap='word',height=2,font=('Segoe UI',11),padx=10,pady=8,relief='flat',highlightthickness=1); self.input.pack(fill='x',pady=(0,4))
        self.count=tk.StringVar(w,'0 / 4000 caracteres'); editor_hint=ttk.Frame(self.composer,style='Experience.Card.TFrame'); editor_hint.pack(fill='x')
        ttk.Label(editor_hint,text='Ctrl+Enter para enviar',style='Experience.ComposerMuted.TLabel').pack(side='left')
        ttk.Label(editor_hint,textvariable=self.count,style='Experience.ComposerMuted.TLabel').pack(side='right')
        self.input.bind('<<Modified>>',self.input_changed); self.input.edit_modified(False)
        self.input.bind('<Control-Return>',self.keyboard_send)
        self.visual_notice=ttk.Frame(self.composer,padding=6,style='Experience.Card.TFrame')
        self.visual_notice_text=tk.StringVar(w,'')
        ttk.Label(self.visual_notice,textvariable=self.visual_notice_text,wraplength=330,style='Experience.Card.TLabel').pack(fill='x')
        ttk.Button(self.visual_notice,text='Usar texto sem imagem',command=self.release_question).pack(anchor='w',pady=(4,0))
        row=ttk.Frame(self.composer,style='Experience.Card.TFrame'); row.pack(fill='x',pady=(6,0))
        self.send_button=ttk.Button(row,text='Enviar',style='Experience.Primary.TButton',command=self.send); self.send_button.pack(side='right')
        self.mic_button=ttk.Button(row,text='Ditar',command=self.listen); self.mic_button.pack(side='left')
        self.voice_button=ttk.Button(row,text='Conversar por voz',command=self.toggle_voice); self.voice_button.pack(side='left',padx=4)
        self.stop_button=ttk.Button(row,text='Parar',command=self.stop); self.stop_button.pack_forget()
        self.advanced_toggle=ttk.Button(row,text='Mais opções',command=self.toggle_advanced); self.advanced_toggle.pack(side='right',padx=4)
        self.voice_indicator=tk.StringVar(w,'Voz desligada')
        self.voice_strip=ttk.Frame(left,padding=(12,8),style='Experience.Card.TFrame')
        voice_head=ttk.Frame(self.voice_strip,style='Experience.Card.TFrame'); voice_head.pack(fill='x')
        self.voice_panel=ttk.Label(voice_head,textvariable=self.voice_indicator,style='Experience.Model.TLabel'); self.voice_panel.pack(side='left',fill='x',expand=True)
        self.voice_stop=ttk.Button(voice_head,text='Interromper',command=self.stop,style='Experience.Stop.TButton'); self.voice_stop.pack(side='right')
        self.voice_meter=ttk.Progressbar(self.voice_strip,mode='determinate',maximum=100,style='Experience.Horizontal.TProgressbar')
        self.voice_live=tk.StringVar(w,''); self.voice_live_label=ttk.Label(self.voice_strip,textvariable=self.voice_live,wraplength=460,style='Experience.ComposerMuted.TLabel')
        self.advanced_open=False
        self.advanced=ttk.Frame(self.composer,padding=(8,4),style='Experience.Card.TFrame')
        extra=ttk.Frame(self.advanced,style='Experience.Card.TFrame'); extra.pack(fill='x')
        self.speak_button=ttk.Button(extra,text='Ouvir resposta',command=self.speak); self.speak_button.pack(side='left')
        self.route_button=ttk.Button(extra,text='Encontrar ferramenta',command=self.route_tool); self.route_button.pack(side='left',padx=4)
        self.auto_speak=tk.BooleanVar(w,False)
        self.auto_button=ttk.Checkbutton(self.advanced,text='Ler respostas automaticamente',variable=self.auto_speak); self.auto_button.pack(anchor='w')
        row=ttk.Frame(self.advanced); row.pack(fill='x')
        self.prepare_button=ttk.Button(row,text='Preparar ação',command=self.prepare_action); self.prepare_button.pack(side='left')
        self.suggest_button=ttk.Button(row,text='Preparar ação com IA',command=self.suggest); self.suggest_button.pack(side='left',padx=4)
        self.proposal_panel=ttk.Frame(self.composer,padding=5,style='Experience.Card.TFrame')
        self.candidate_label=tk.StringVar(w,''); ttk.Label(self.proposal_panel,textvariable=self.candidate_label,wraplength=310,justify='left',style='Experience.Card.TLabel').pack(anchor='w')
        self.preview=tk.StringVar(w,''); ttk.Label(self.proposal_panel,textvariable=self.preview,wraplength=310,justify='left',style='Experience.Card.TLabel').pack(anchor='w')
        row=ttk.Frame(self.proposal_panel,style='Experience.Card.TFrame'); row.pack(fill='x')
        self.accept_button=ttk.Button(row,text='Usar sugestão',command=self.accept_candidate); self.accept_button.pack(side='left')
        self.confirm_button=ttk.Button(row,text='Confirmar ação',command=self.confirm_action,style='Experience.Primary.TButton'); self.confirm_button.pack(side='left',padx=4)
        contexthead=ttk.Frame(right); contexthead.pack(fill='x',pady=(0,8))
        ttk.Label(contexthead,text='CONTEXTO DE TRABALHO',style='Experience.Section.TLabel').pack(side='left')
        self.context_back=ttk.Button(contexthead,text='Voltar à conversa',command=lambda:self.hub.navigate('chat'))
        tabs=self.context_tabs=ttk.Notebook(right); tabs.pack(fill='both',expand=True)
        tabs.bind('<<NotebookTabChanged>>',self.context_changed,add='+')
        tabs.enable_traversal()
        screen=ttk.Frame(tabs,padding=9); tabs.add(screen,text='Tela')
        ttk.Label(screen,text='Acompanhe a tela principal',style='Experience.Subtitle.TLabel',wraplength=320).pack(anchor='w')
        ttk.Label(screen,text='Capture a tela ou acompanhe por até 5 minutos. Só a última imagem fica na memória; revise antes de enviar à IA.',wraplength=460,justify='left').pack(anchor='w',pady=5)
        # Reserve the action area before allocating space to the image preview.
        controls=ttk.Frame(screen); controls.pack(side='bottom',fill='x')
        controls.columnconfigure(0,weight=1); controls.columnconfigure(1,weight=1)
        self.vision_state=tk.StringVar(w,'Acompanhamento desligado')
        ttk.Label(controls,textvariable=self.vision_state,style='Experience.Section.TLabel',wraplength=320).grid(row=0,column=0,columnspan=2,sticky='w',pady=(0,4))
        self.monitor_button=ttk.Button(controls,text='Acompanhar tela',command=self.toggle_vision,style='Experience.Primary.TButton'); self.monitor_button.grid(row=1,column=0,sticky='ew',padx=(0,3),pady=3)
        self.capture_button=ttk.Button(controls,text='Capturar tela',command=self.capture); self.capture_button.grid(row=1,column=1,sticky='ew',padx=(3,0),pady=3)
        self.visual_mic=ttk.Button(controls,text='Perguntar por voz',command=self.ask_screen_voice); self.visual_mic.grid(row=2,column=0,sticky='ew',padx=(0,3),pady=3)
        self.analyze_button=ttk.Button(controls,text='Analisar captura com IA',command=self.analyze); self.analyze_button.grid(row=2,column=1,sticky='ew',padx=(3,0),pady=3)
        self.discard_button=ttk.Button(controls,text='Descartar captura',command=self.discard_screen); self.discard_button.grid(row=3,column=0,columnspan=2,sticky='ew',pady=3)
        self.visual_status=tk.StringVar(w,'')
        ttk.Label(controls,textvariable=self.visual_status,wraplength=320,style='Experience.Muted.TLabel').grid(row=4,column=0,columnspan=2,sticky='w')
        self.image_label=ttk.Label(screen,text='Nenhuma captura',anchor='center',style='Experience.Card.TLabel'); self.image_label.pack(fill='both',expand=True,pady=5)
        notes=ttk.Frame(tabs,padding=9); tabs.add(notes,text='Anotações')
        ttk.Label(notes,text='Bloco de trabalho',style='Experience.Subtitle.TLabel').pack(anchor='w')
        ttk.Label(notes,text='Escreva ou copie uma resposta para revisar. Salve em Anotações somente quando quiser.',wraplength=320).pack(anchor='w',pady=5)
        self.note=tk.Text(notes,wrap='word',height=7,relief='flat',highlightthickness=1,padx=8,pady=5); self.note.pack(fill='both',expand=True)
        ttk.Button(notes,text='Adicionar última resposta',command=self.append_answer).pack(fill='x',pady=(8,3))
        ttk.Button(notes,text='Salvar anotação na sessão',command=self.save_note).pack(fill='x')
        meetings=ttk.Frame(tabs,padding=8); tabs.add(meetings,text='Reunião')
        self.meeting_steps=ttk.Frame(meetings); self.meeting_steps.pack(fill='x',pady=(0,4))
        self.meeting_step_labels=[]
        for index,title in enumerate(('1  Preparar','2  Transcrever','3  Revisar')):
            step=ttk.Label(self.meeting_steps,text=title,style='Experience.Step.TLabel',anchor='center'); step.grid(row=0,column=index,sticky='ew',padx=2); self.meeting_steps.columnconfigure(index,weight=1); self.meeting_step_labels.append(step)
        self.meeting_status=tk.StringVar(w,'1 · Preparar áudio')
        self.meeting_status_label=ttk.Label(meetings,textvariable=self.meeting_status,style='Experience.Section.TLabel',wraplength=310); self.meeting_status_label.pack(anchor='w')
        self.meeting_detail=tk.StringVar(w,'Avise os participantes antes de iniciar.')
        self.meeting_detail_label=ttk.Label(meetings,textvariable=self.meeting_detail,style='Experience.Muted.TLabel',wraplength=310,justify='left'); self.meeting_detail_label.pack(anchor='w',pady=(1,3))
        self.meeting_meter=ttk.Progressbar(meetings,maximum=100,mode='determinate',style='Experience.Horizontal.TProgressbar')
        self.meeting_controls=ttk.Frame(meetings); self.meeting_controls.pack(fill='x',pady=3)
        self.meeting_start=ttk.Button(self.meeting_controls,text='Iniciar microfone',command=self.start_meeting,style='Experience.Primary.TButton')
        self.meeting_loopback=ttk.Button(self.meeting_controls,text='Áudio interno',command=self.start_internal_meeting)
        self.meeting_stop=ttk.Button(self.meeting_controls,text='Parar transcrição',command=self.stop_meeting,style='Experience.Stop.TButton')
        self.meeting_actions=ttk.Frame(meetings); self.meeting_actions.pack(side='bottom',fill='x',pady=(4,0))
        self.minutes_button=ttk.Button(self.meeting_actions,text='Revisar ata com IA',command=self.meeting_summary,style='Experience.Primary.TButton')
        self.meeting_save=ttk.Button(self.meeting_actions,text='Salvar texto na sessão',command=self.save_meeting)
        self.meeting_wide=None; self.layout_meeting_controls(False)
        meetings.bind('<Configure>',self.resize_meeting,add='+')
        self.meeting_editors=ttk.Notebook(meetings); self.meeting_editors.pack(fill='both',expand=True,pady=4); self.meeting_editors.enable_traversal()
        transcript_tab=ttk.Frame(self.meeting_editors,padding=3); self.meeting_editors.add(transcript_tab,text='Transcrição')
        notes_tab=ttk.Frame(self.meeting_editors,padding=3); self.meeting_editors.add(notes_tab,text='Minhas notas')
        self.meeting_text=tk.Text(transcript_tab,wrap='word',height=3,relief='flat',highlightthickness=1,padx=8,pady=5)
        self.meeting_notes=tk.Text(notes_tab,wrap='word',height=3,relief='flat',highlightthickness=1,padx=8,pady=5)
        for editor,tab in ((self.meeting_text,transcript_tab),(self.meeting_notes,notes_tab)):
            scroll=ttk.Scrollbar(tab,orient='vertical',command=editor.yview); scroll.pack(side='right',fill='y')
            editor.configure(yscrollcommand=scroll.set); editor.pack(side='left',fill='both',expand=True)
        for editor in (self.input,self.transcript,self.note,self.meeting_text,self.meeting_notes):
            editor.bind('<Tab>',lambda e:self.traverse_editor(e.widget,1))
            editor.bind('<Shift-Tab>',lambda e:self.traverse_editor(e.widget,-1))
            editor.bind('<ISO_Left_Tab>',lambda e:self.traverse_editor(e.widget,-1))
        self.status=tk.StringVar(w,'Pronto. Microfone e tela desligados.')
        ttk.Label(w,textvariable=self.status,style='Experience.Muted.TLabel',wraplength=800).pack(side='bottom',fill='x',pady=(6,0),before=self.panes)
        self.draw(); self.permissions_changed()
    def toggle_ai_settings(self):
        self.ai_open=not self.ai_open
        if self.ai_open:
            self.ai_settings.pack(fill='x',pady=(0,8),before=self.panes)
        else:
            self.ai_settings.pack_forget()
        self.ai_toggle.configure(text='Fechar configuração' if self.ai_open else 'Configurar IA')
    def traverse_editor(self,widget,direction):
        target=widget.tk_focusNext() if direction==1 else widget.tk_focusPrev()
        if target is not None: target.focus_set()
        return 'break'
    def resize_meeting(self,event):
        if event.width<=1: return
        width=max(180,event.width-20)
        self.meeting_status_label.configure(wraplength=width)
        self.meeting_detail_label.configure(wraplength=width)
        self.layout_meeting_controls(width>=480)
    def layout_meeting_controls(self,wide):
        if wide==self.meeting_wide: return
        self.meeting_wide=wide
        for frame,controls in ((self.meeting_controls,(self.meeting_start,self.meeting_loopback,self.meeting_stop)),(self.meeting_actions,(self.minutes_button,self.meeting_save))):
            for column in range(3): frame.columnconfigure(column,weight=0)
            columns=len(controls) if wide else (2 if frame is self.meeting_controls else 1)
            for column in range(columns): frame.columnconfigure(column,weight=1)
            for index,control in enumerate(controls):
                span=2 if not wide and frame is self.meeting_controls and index==2 else 1
                control.grid(row=index//columns,column=index%columns,columnspan=span,sticky='ew',padx=2,pady=2)
    def resize_hero(self,event):
        # On short layouts, prioritize actions and message editor, not decoration.
        compact=event.height<110 or event.width<340
        if compact:
            self.welcome_mark.pack_forget(); self.hero_subtitle.pack_forget()
        else:
            if not self.welcome_mark.winfo_manager(): self.welcome_mark.pack(before=self.hero_title,pady=(0,2))
            if not self.hero_subtitle.winfo_manager(): self.hero_subtitle.pack(fill='x',pady=(2,0))
    def resize_workspace(self,width):
        compact=compact_workspace(width)
        if compact!=self.compact:
            self.compact=compact
            self.layout_context()
    def layout_context(self):
        compact_context=self.compact and self.context_open
        self.panes.columnconfigure(0,weight=0 if compact_context else 3)
        self.panes.columnconfigure(1,weight=3 if compact_context else 2 if self.context_open else 0)
        if compact_context:
            self.chat_panel.grid_remove()
            self.context_back.pack(side='right')
        else:
            self.chat_panel.grid()
            self.context_back.pack_forget()
        if self.context_open: self.context_panel.grid()
        else: self.context_panel.grid_remove()
        self.context_toggle.configure(text='Ocultar contexto' if self.context_open else 'Mostrar contexto')
    def set_context(self,visible):
        if not visible and self.vision.active: self.stop_vision()
        self.context_open=bool(visible)
        self.layout_context()
        if not visible and not self.voice.active: self.input.focus_set()
    def toggle_context(self):
        self.set_context(not self.context_open)
    def authorize(self,cap,label):
        permissions=self.hub.permissions
        if permissions.allowed(cap): return True
        revision=permissions.revision
        if not ask_permission(self.hub.root,self.hub.settings.appearance.theme,cap,label): return False
        if self.closed or permissions is not self.hub.permissions or revision!=permissions.revision: return False
        permissions.set(cap,True); return True
    def ensure_tool(self,name):
        if not self.hub.enabled(name): self.hub.toggle_tool(name)
        return self.hub.enabled(name)
    def model_changed(self,*args):
        self.ready_state.set('Modelo alterado. Clique Testar IA para verificar a resposta.')
        self.detach_question()
        self.close_meeting_review()
        self.session.cancel(); self.action_input=None; self.preview.set(''); self.ai_hint=None; self.update_hint(); super().model_changed(*args)
        self.ai_state.set('IA local · '+self.model.get().strip()[:48] if self.model.get().strip() else 'IA local · escolha um modelo')
    def detect_models(self):
        if not self.idle(): return
        if not self.authorize(COMPANION_CHAT,'Consultar os nomes dos modelos instalados no Ollama local? Nenhuma mensagem ou arquivo será enviado.'): return
        if not self.idle(): return
        if self.start(COMPANION_CHAT,installed_models,kind='models'):
            self.ready_state.set('Consultando Ollama local…'); self.status.set('Consultando modelos instalados…')
    def test_ai(self):
        if not self.idle(): return
        model=self.model.get().strip()
        if not model:
            self.ready_state.set('Escolha um modelo instalado primeiro.'); return
        if not self.authorize(COMPANION_CHAT,'Enviar uma saudação fictícia ao Ollama local para testar a resposta? Nenhuma mensagem pessoal, imagem ou arquivo será enviado.'): return
        if not self.idle() or model!=self.model.get().strip(): return
        if self.start(COMPANION_CHAT,lambda:(model,test_model_response(model,chat_fn=chat)),kind='ready_test'):
            self.test_started=monotonic()
            self.ready_state.set('Teste de texto · mensagem: '+TEST_PROMPT+' Aguardando resposta do modelo local.'); self.status.set('Teste de inferência em andamento. A primeira resposta pode demorar enquanto o modelo é carregado.')
    def configure_ai(self):
        if not self.idle(): return
        if not self.ai_open: self.toggle_ai_settings()
        if not inspect_environment().windows:
            messagebox.showinfo('Configuração da IA','A preparação automática exige Windows. Você pode selecionar modelos do Ollama local já instalado.',parent=self.hub.root); return
        from aeris.setup_dialog import choose_setup
        revision=self.hub.permissions.revision
        model=choose_setup(self.hub.root,self.hub.settings.appearance.theme)
        if model is None or self.closed or not self.idle() or revision!=self.hub.permissions.revision: return
        if not self.authorize(COMPANION_CHAT,'Autorizar o teste de texto fictício no modelo local?'): return
        self.begin_ai_setup(model,download=True)
    def restore_ai(self):
        model=load_choice(self.ai_runtime.choice)
        if model and self.idle():
            self.begin_ai_setup(model,download=False)
    def begin_ai_setup(self,model,*,download):
        if not self.idle(): return
        cancel=threading.Event(); self.setup_progress=queue.Queue(); progress=self.setup_progress; runtime=self.ai_runtime
        self.setup_result=''
        job=self.job+1; results=self.results
        def work():
            try: return (job,True,runtime.prepare(model,cancel,progress.put,download=download))
            except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as exc:
                return (job,False,str(exc)[:300])
            except Exception:
                return (job,False,'Configuração não concluída. Confira o Ollama e tente novamente.')
        if not worker_for(self.hub).start(work,results.put):
            self.ready_state.set('Outra operação local ainda está em andamento.'); return
        self.setup_cancel=cancel; self.busy=True; self.cap=COMPANION_CHAT
        self.kind='ai_setup' if download else 'ai_restore'; self.job=job
        self.ready_state.set('Preparando IA local…'); self.status.set('Preparando IA local…')
        if not self.ai_open and download: self.toggle_ai_settings()
        self.setup_phase.set('Verificando requisitos…'); self.setup_detail.pack(fill='x',pady=(6,2)); self.setup_bar.pack(fill='x',pady=(0,4)); self.setup_bar.configure(mode='indeterminate'); self.setup_bar.start(14)
        self.refresh(); self.schedule_poll()
    def idle(self):
        return not (self.closed or self.busy or self.voice.active or self.vision.active or self.meeting_active or self.capture_timer is not None)
    def send(self):
        if not self.idle(): return
        if self.visual_invalid:
            self.status.set('A captura mudou. Escolha Usar texto sem imagem ou limpe o rascunho.'); return
        if self.screen_question is not None:
            if self.screen_question.matches(self.screen,self.model.get().strip()): self.analyze(); return
            self.detach_question(); self.status.set('Captura ou modelo alterado. Revise o rascunho antes de enviar.'); return
        # Recognized local commands use the same reviewed action path, without a model.
        try: parse_command(self.input.get('1.0','end-1c'))
        except ValueError: pass
        else: self.prepare_action(); return
        if not self.model.get().strip():
            if not self.ai_open: self.toggle_ai_settings()
            self.configure_ai(); return
        if self.ensure_tool('Copilot') and self.authorize(COMPANION_CHAT,'Enviar a mensagem e o histórico ao Ollama local? Nenhum outro arquivo será enviado.'):
            self.send_stream()
    def send_stream(self):
        from aeris import companion_ui
        try:
            text=validate_message(self.input.get('1.0','end-1c')); model=self.model.get().strip(); history=tuple(self.history)
            self.discard_candidate()
            cancel=threading.Event(); chunks=queue.Queue()
            def run(): return companion_ui.chat(model,history,text,on_chunk=chunks.put,cancel=cancel)
            if not self.start(COMPANION_CHAT,run,kind='stream_chat'): return
        except (ValueError,PermissionError) as exc: self.status.set(str(exc)); return
        self.stream_pending=text; self.stream_cancel=cancel; self.stream_chunks=chunks; self.stream_partial=''
        self.stream_started=monotonic(); self.stream_first=None
        self.input.delete('1.0','end'); self.draw()
        self.status.set('Carregando modelo ou aguardando a primeira resposta…')

    def restore_stream_draft(self):
        if self.stream_pending and not self.input.get('1.0','end-1c').strip():
            self.input.insert('1.0',self.stream_pending)

    def poll_stream(self):
        self.timer=None
        if self.closed: return
        allowed=self.hub.permissions.allowed(COMPANION_CHAT)
        changed=False
        try:
            while True:
                piece=self.stream_chunks.get_nowait()
                if allowed and self.stream_pending is not None:
                    self.stream_partial+=piece; changed=True
                    if self.stream_first is None: self.stream_first=monotonic()
        except queue.Empty: pass
        if changed:
            self.draw(); self.status.set('Gerando resposta…')
        try: job,ok,result=self.results.get_nowait()
        except queue.Empty:
            self.schedule_poll(); return
        valid=job==self.job and allowed and self.stream_pending is not None
        self.busy=False; self.process=None
        auto=False
        if valid and ok:
            self.history.extend((('user',self.stream_pending),('assistant',result))); self.history=self.history[-MAX_HISTORY:]
            elapsed=monotonic()-self.stream_started
            first=f' · primeiro texto em {self.stream_first-self.stream_started:.1f}s' if self.stream_first is not None else ''
            self.status.set(f'Resposta concluída em {elapsed:.1f}s'+first+'. A IA pode errar.')
            auto=self.auto_speak.get() and self.hub.permissions.allowed(COMPANION_SPEAK)
        elif valid:
            self.restore_stream_draft()
            self.status.set('Resposta não concluída. Confira Ollama, modelo e recursos; o rascunho foi preservado se o editor estava vazio.')
        self.stream_pending=None; self.stream_cancel=None; self.stream_partial=''; self.draw(); self.refresh()
        if auto: self.speech('speak')

    def toggle_voice(self):
        if self.voice.active:
            self.stop_voice(); return
        if not self.idle(): return
        if self.input.get('1.0','end-1c').strip():
            self.status.set('Envie ou limpe o rascunho antes de iniciar a conversa por voz.'); return
        model=self.model.get().strip()
        if not model:
            if not self.ai_open: self.toggle_ai_settings()
            self.configure_ai(); return
        revision=self.hub.permissions.revision
        if not ask_confirmation(self.hub.root,self.hub.settings.appearance.theme,'Conversar por voz?',f'O microfone será reativado após cada resposta, por até {MAX_TURNS} turnos. A fala reconhecida será enviada ao modelo Ollama local com o histórico da conversa. O Aeris não grava áudio em arquivo. Clique Parar voz a qualquer momento.'): return
        if self.closed or revision!=self.hub.permissions.revision or model!=self.model.get().strip(): return
        for cap,label in ((COMPANION_MIC,'Autorizar ditado pelo microfone?'),(COMPANION_CHAT,'Autorizar envio de texto e histórico ao modelo local?'),(COMPANION_SPEAK,'Autorizar reprodução de respostas por voz?')):
            if not self.authorize(cap,label): return
        if not self.idle() or model!=self.model.get().strip() or self.input.get('1.0','end-1c').strip(): return
        if not self.ensure_tool('Copilot') or not self.voice_allowed(): return
        self.session.cancel(); self.action_input=None; self.preview.set(''); self.discard_candidate()
        self.voice.begin(model); self.voice_next()
    def voice_allowed(self):
        return all(self.hub.permissions.allowed(cap) for cap in (COMPANION_MIC,COMPANION_CHAT,COMPANION_SPEAK))
    def stop_voice(self,message='Conversa por voz encerrada.'):
        if self.voice_cancel is not None: self.voice_cancel.set(); self.voice_cancel=None
        self.clear_voice_feedback()
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
        if phase=='listen':
            self.start_voice_capture('voice_listen'); return
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
        self.status.set('Reproduzindo resposta · microfone desligado.')
    def clear_voice_feedback(self):
        self.voice_capture_job=None; self.voice_capture_state='preparing'; self.voice_level=0; self.voice_partial=''
        self.voice_live.set(''); self.voice_meter.configure(value=0)
        self.voice_meter.pack_forget(); self.voice_live_label.pack_forget()

    def start_voice_capture(self,kind):
        if self.busy or not self.hub.permissions.allowed(COMPANION_MIC): return
        self.clear_voice_feedback()
        self.voice_events=events=queue.Queue()
        try:
            if worker_for(self.hub).busy: raise OSError('Outra operação local ativa.')
            p=feedback_process(); self.process=p
            if not self.start(COMPANION_MIC,lambda:listen_with_feedback(p,events.put),kind=kind):
                p.kill(); p.wait(timeout=3); p.stdout.close(); self.process=None
                raise OSError('Não foi possível iniciar a escuta.')
        except (OSError,PermissionError,subprocess.SubprocessError):
            if self.voice.active: self.stop_voice('Não foi possível iniciar a voz. Confira o microfone e o Windows.')
            else: self.status.set('Microfone indisponível. Confira o Windows.')
            return
        self.voice_capture_job=self.job
        self.voice_meter.pack(fill='x',pady=(3,0)); self.voice_live_label.pack(anchor='w',fill='x')
        self.status.set('Preparando microfone… aguarde a confirmação da captura.'); self.refresh()

    def drain_voice_feedback(self):
        if self.voice_capture_job!=self.job or not self.hub.permissions.allowed(COMPANION_MIC): return
        changed=False
        try:
            while True:
                kind,value=self.voice_events.get_nowait()
                if kind=='level':
                    self.voice_level=value
                    if self.voice_capture_state=='preparing': self.voice_capture_state='Silence'
                elif kind=='state': self.voice_capture_state=value
                elif kind=='partial': self.voice_partial=value
                changed=True
        except queue.Empty: pass
        if changed:
            self.voice_meter.configure(value=self.voice_level if self.voice_capture_state in ('Speech','Silence') else 0)
            self.voice_live.set(('Reconhecendo: '+self.voice_partial) if self.voice_partial else 'Nível de entrada do microfone (0–100)')
            self.refresh()

    def voice_result(self,kind,ok,result):
        if not self.voice.active: return
        if not ok or not self.voice_allowed() or self.voice.model!=self.model.get().strip():
            self.stop_voice('Conversa por voz interrompida: silêncio, erro ou permissão revogada.'); return
        phase=kind.removeprefix('voice_')
        if phase!=self.voice.phase:
            self.stop_voice(); return
        if phase=='listen':
            if not isinstance(result,tuple) or result[0]!='ok':
                self.stop_voice(ERRORS.get(result[1] if isinstance(result,tuple) else 'recognition',ERRORS['recognition'])); return
            result=result[1]
            # A spoken local action is a draft, never an automatic execution.
            try: parse_command(result)
            except ValueError: pass
            else:
                self.stop_voice('Pedido de ação reconhecido. Revise o texto e envie para preparar a confirmação.')
                self.input.insert('1.0',result); return
            self.voice.advance(phase)
            model=self.voice.model; history=tuple(self.history)
            self.voice_cancel=cancel=threading.Event()
            if not self.start(COMPANION_CHAT,lambda:(result,chat(model,history,result,system=SYSTEM+' Para voz, responda de forma breve, natural e sem listas longas.',on_chunk=lambda _:None,cancel=cancel)),kind='voice_chat'):
                self.stop_voice('Não foi possível consultar a IA.'); return
            self.voice_live.set('Você disse: '+result); self.voice_live_label.pack(anchor='w',fill='x')
            self.status.set('Consultando IA local · microfone desligado.')
        elif phase=='chat':
            self.voice_cancel=None
            text,response=result
            self.history.extend((('user',text),('assistant',response))); self.history=self.history[-MAX_HISTORY:]; self.draw()
            self.voice.advance(phase)
            self.voice_timer=self.window.after(250,self.voice_next)
        else:
            if self.voice.advance(phase) is None:
                self.stop_voice('Limite da sessão de voz atingido. Inicie outra se quiser continuar.'); return
            self.voice_timer=self.window.after(450,self.voice_next)
    def listen(self):
        if not self.idle(): return
        if self.ensure_tool('Copilot') and self.authorize(COMPANION_MIC,'Usar o microfone padrão para um ditado curto? Nenhuma gravação é salva pelo Aeris.'):
            if self.input.get('1.0','end-1c').strip(): self.status.set('Envie ou limpe o rascunho antes de ditar.'); return
            self.start_voice_capture('voice_dictation')
    def speak(self):
        if not self.idle(): return
        if self.history and self.authorize(COMPANION_SPEAK,'Ler a última resposta com a voz local do Windows?'):
            self.speech('speak')
    def toggle_advanced(self):
        self.advanced_open=not self.advanced_open
        if self.advanced_open: self.advanced.pack(fill='x',pady=3,before=self.input)
        else: self.advanced.pack_forget()
        self.advanced_toggle.configure(text='Menos opções' if self.advanced_open else 'Mais opções')
    def refresh(self):
        if self.closed: return
        if self.candidate or self.session.pending:
            if not self.proposal_panel.winfo_manager(): self.proposal_panel.pack(fill='x',pady=4,before=self.input)
        else: self.proposal_panel.pack_forget()
        free=self.idle()
        linked=self.screen_question is not None or self.visual_invalid
        if linked:
            self.visual_notice_text.set('Captura não disponível. Confirme se deseja usar apenas o texto.' if self.visual_invalid else 'Pergunta vinculada à captura. Revise antes de enviar.')
            if not self.visual_notice.winfo_manager(): self.visual_notice.pack(fill='x',pady=4,before=self.input)
        else: self.visual_notice.pack_forget()
        if self.voice_capture_job==self.job and self.busy:
            mode={'preparing':'Microfone · preparando','Silence':'Microfone ativo · aguardando fala','Speech':'Microfone ativo · reconhecendo fala','Stopped':'Microfone desligado · finalizando'}.get(self.voice_capture_state,'Microfone · preparando')
        elif self.voice.active:
            mode={'listen':'Voz · preparando escuta','chat':'Voz · pensando','speak':'Voz · respondendo'}[self.voice.phase]
        elif self.vision.active: mode='Tela · acompanhamento autorizado'
        elif self.meeting_active: mode='Reunião · '+('áudio interno' if self.meeting_source=='internal' else 'microfone')
        elif self.busy and self.kind=='visual_question': mode='Voz + tela · ditando pergunta'
        elif self.busy and self.kind=='vision': mode='Tela · analisando captura'
        elif self.busy and self.kind in ('ai_setup','ai_restore'): mode='IA local · preparação em andamento; funções dependentes pausadas'
        elif self.busy and self.kind=='ready_test': mode='IA local · teste de resposta em andamento'
        elif self.busy and self.cap==COMPANION_CHAT: mode='IA local · processando; aguarde ou interrompa'
        elif self.busy or self.capture_timer is not None: mode='Operação local em andamento'
        else: mode='Pronto · microfone e tela desligados'
        self.mode_status.set(mode)
        if self.busy and not self.progress_running:
            self.activity_progress.pack(fill='x',pady=(0,8),before=self.panes)
            self.activity_progress.start(14); self.progress_running=True
        elif not self.busy and self.progress_running:
            self.activity_progress.stop(); self.activity_progress.pack_forget(); self.progress_running=False
        self.global_stop.configure(state='disabled' if free else 'normal')
        self.model_entry.configure(state='normal' if free else 'disabled')
        self.test_ai_button.configure(state='normal' if free else 'disabled')
        self.setup_button.configure(state='normal' if free else 'disabled')
        self.monitor_button.configure(text='Parar acompanhamento' if self.vision.active else 'Acompanhar tela',state='normal' if free or self.vision.active else 'disabled')
        self.vision_state.set(f'TELA ATIVA · {self.vision.frames}/{MAX_FRAMES} capturas' if self.vision.active else 'Acompanhamento desligado')
        self.voice_button.configure(text='Parar voz' if self.voice.active else 'Conversar por voz',state='normal' if free or self.voice.active else 'disabled')
        voice_engaged=self.voice.active or self.voice_capture_job==self.job and self.busy
        self.voice_indicator.set(mode if voice_engaged else 'Voz desligada')
        if voice_engaged and not self.voice_strip.winfo_manager(): self.voice_strip.pack(fill='x',pady=(3,0),before=self.chatbox)
        elif not voice_engaged: self.voice_strip.pack_forget()
        self.input.configure(state='disabled' if self.voice.active else 'normal')
        for button in (self.send_button,self.mic_button,self.prepare_button,self.suggest_button,self.capture_button,self.meeting_start,self.detect_button):
            button.configure(state='normal' if free else 'disabled')
        for button in (self.hint_button,self.route_button,self.prepare_button,self.suggest_button):
            button.configure(state='normal' if free and not linked else 'disabled')
        self.speak_button.configure(state='normal' if free and self.history else 'disabled')
        self.stop_button.configure(state='normal' if not free else 'disabled')
        self.meeting_stop.configure(state='normal' if self.meeting_active else 'disabled')
        self.meeting_loopback.configure(state='normal' if free and loopback_available() else 'disabled')
        self.minutes_button.configure(state='normal' if free else 'disabled')
        self.meeting_save.configure(state='normal' if free else 'disabled')
        self.refresh_meeting_status()
        self.analyze_button.configure(state='normal' if (free or (self.vision.active and not self.busy and self.vision_phase in ('idle','answer'))) and self.screen and not self.visual_invalid else 'disabled')
        self.visual_mic.configure(state='normal' if (free or (self.vision.active and not self.busy and self.vision_phase in ('idle','answer'))) and self.screen else 'disabled')
        self.accept_button.configure(state='normal' if free and self.candidate and self.hub.permissions.allowed(COPILOT_RUN) and self.hub.permissions.allowed(COMPANION_CHAT) else 'disabled')
        self.confirm_button.configure(state='normal' if free and self.session.pending else 'disabled')
        self.auto_button.configure(state='normal' if self.hub.permissions.allowed(COMPANION_SPEAK) else 'disabled')
        if not self.hub.permissions.allowed(COMPANION_SPEAK): self.auto_speak.set(False)
        self.refresh_vision_panel()
    def draw(self):
        self.transcript.configure(state='normal'); self.transcript.delete('1.0','end')
        self.transcript.tag_configure('person',font=('Segoe UI',11,'bold'),spacing1=16,spacing3=5)
        self.transcript.tag_configure('message',spacing3=14,lmargin1=8,lmargin2=8,rmargin=12)
        if not self.history and self.stream_pending is None:
            self.transcript.insert('end','Olá! Como posso ajudar hoje?\n','person')
            self.transcript.insert('end','Escreva o que precisa fazer. Posso ajudar a encontrar uma ferramenta, conversar sobre um assunto ou preparar uma ação. Você decide o que compartilhar.','message')
        for role,value in self.history:
            self.transcript.insert('end',('Você' if role=='user' else 'Aeris')+'\n','person')
            self.transcript.insert('end',value+'\n','message')
        if self.stream_pending is not None:
            self.transcript.insert('end','Você\n','person'); self.transcript.insert('end',self.stream_pending+'\n','message')
            self.transcript.insert('end','Aeris\n','person'); self.transcript.insert('end',self.stream_partial or 'Preparando resposta…','message')
        self.transcript.configure(state='disabled'); self.transcript.see('end')
        if self.history or self.stream_pending is not None:
            self.welcome.pack_forget()
            if not self.transcript.winfo_manager():
                self.chat_scroll.pack(side='right',fill='y'); self.transcript.pack(side='left',fill='both',expand=True)
        else:
            self.transcript.pack_forget(); self.chat_scroll.pack_forget()
            if not self.welcome.winfo_manager(): self.welcome.pack(fill='both',expand=True)
    def clear_workspace(self):
        self.stop()
        self.discard_screen()
        self.session.cancel(); self.action_input=None; self.preview.set('')
        self.clear()
        self.note.delete('1.0','end')
        self.meeting_text.configure(state='normal'); self.meeting_text.delete('1.0','end'); self.meeting_notes.delete('1.0','end')
        self.meeting_phase='idle'; self.meeting_chunks.clear(); self.close_meeting_review()
        self.auto_speak.set(False)
        self.ai_hint=None; self.update_hint()
        self.status.set('Sessão limpa. Resultados pendentes descartados; registros protegidos preservados.')
        self.refresh()
    def reset_chat(self):
        if self.dirty() and not messagebox.askyesno('Nova conversa?','Limpar conversa e rascunho? As anotações e a reunião permanecem.',parent=self.hub.root): return
        self.session.cancel(); self.action_input=None; self.preview.set(''); self.clear()
    def input_changed(self,event=None):
        if self.closed or not self.input.edit_modified(): return
        self.session.cancel(); self.action_input=None; self.preview.set('')
        if not self.input.get('1.0','end-1c').strip(): self.detach_question(completed=True)
        super().input_changed(event); self.update_hint(); self.refresh()
    def update_hint(self):
        draft=self.input.get('1.0','end-1c')
        if self.screen_question is not None or self.visual_invalid:
            self.ai_hint=None; self.hint_name=None; self.hint_panel.pack_forget(); return
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
        if not self.idle() or self.screen_question is not None or self.visual_invalid: return
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
        if not self.hint_name or not self.idle():
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
        if self.vision.active and ((self.vision_phase in ('listen','review','analysis') and not self.hub.permissions.allowed(COMPANION_MIC)) or (self.vision_phase in ('analysis','answer','speak') and not self.hub.permissions.allowed(COMPANION_CHAT)) or (self.vision_phase=='speak' and not self.hub.permissions.allowed(COMPANION_SPEAK))):
            self.stop_vision('Tela e voz encerradas: permissão revogada.')
        if not self.hub.permissions.allowed(COMPANION_CHAT):
            self.ai_hint=None; self.update_hint()
            if self.busy and self.kind=='vision': super().stop()
        if not self.hub.permissions.allowed(COMPANION_MIC):
            self.detach_question()
            if self.busy and self.kind=='visual_question': super().stop()
        if not self.hub.permissions.allowed(COMPANION_SCREEN): self.discard_screen()
        if self.meeting_active and not self.hub.permissions.allowed(self.meeting_cap()): self.stop_meeting()
        if not self.hub.permissions.allowed(COMPANION_CHAT): self.close_meeting_review()
        super().permissions_changed()
    def suggest(self):
        if not self.idle() or self.screen_question is not None or self.visual_invalid: return
        if not self.model.get().strip():
            if not self.ai_open: self.toggle_ai_settings()
            self.configure_ai(); return
        if self.ensure_tool('Copilot') and self.authorize(COMPANION_CHAT,'Enviar apenas seu pedido ao modelo local?') and self.authorize(COPILOT_RUN,'Permitir preparar ações locais para sua confirmação?'):
            super().suggest()
    def accept_candidate(self):
        if not self.idle() or self.screen_question is not None or self.visual_invalid: return
        super().accept_candidate()
        if self.input.get('1.0','end-1c'): self.status.set('Revise o pedido e clique Preparar ação. Nada foi executado.')
    def prepare_action(self):
        if not self.idle() or self.screen_question is not None or self.visual_invalid: return
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
        if not self.idle() or self.screen_question is not None or self.visual_invalid: return
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
        if not ask_confirmation(self.hub.root,self.hub.settings.appearance.theme,'Acompanhar tela principal?', 'O Aeris fará capturas periódicas da tela principal a cada 15 segundos, por até 5 minutos ou 20 imagens. Apenas a última captura fica na memória. Nenhuma imagem será enviada automaticamente à IA. O painel flutuante permite atualizar a captura, ditar uma pergunta, revisar a imagem e enviar explicitamente ao modelo local. A captura pausa durante a pergunta e análise. O painel pode aparecer na captura. Evite abrir dados sensíveis.'): return
        if self.closed or revision!=self.hub.permissions.revision: return
        if not self.authorize(COMPANION_SCREEN,'Autorizar captura de tela nesta sessão?'): return
        if self.closed or self.busy or self.voice.active or self.meeting_active or self.capture_timer is not None or self.vision.active or not self.hub.permissions.allowed(COMPANION_SCREEN): return
        self.discard_screen()
        badge=tk.Toplevel(self.hub.root); self.vision_badge=badge
        badge.title('Aeris · Tela'); badge.attributes('-topmost',True); badge.resizable(False,False)
        badge.protocol('WM_DELETE_WINDOW',self.stop_vision)
        badge.bind('<Unmap>',lambda e:self.stop_vision() if e.widget is badge and not self.closed and self.vision_badge is badge and self.vision.active else None,add='+')
        panel=ttk.Frame(badge,padding=10); panel.pack(fill='both',expand=True)
        head=ttk.Frame(panel); head.pack(fill='x')
        wind_mark(head,self.hub.settings.appearance.theme,size=36,surface='air').pack(side='left',padx=(0,8))
        ttk.Label(head,text='Aeris · Tela e voz',style='Experience.Section.TLabel').pack(side='left')
        self.vision_panel_state=tk.StringVar(badge,'Preparando captura…')
        ttk.Label(panel,textvariable=self.vision_panel_state,wraplength=310,style='Experience.Section.TLabel').pack(anchor='w',pady=(4,0))
        self.vision_panel_age=tk.StringVar(badge,'Nenhuma captura')
        ttk.Label(panel,textvariable=self.vision_panel_age,wraplength=310,style='Experience.Muted.TLabel').pack(anchor='w')
        self.vision_panel_image=ttk.Label(panel,text='Nenhuma captura',style='Experience.Card.TLabel',anchor='center'); self.vision_panel_image.pack(fill='x',pady=5)
        self.vision_panel_meter=ttk.Progressbar(panel,maximum=100,mode='determinate',style='Experience.Horizontal.TProgressbar')
        self.vision_panel_text=tk.Text(panel,width=36,height=4,wrap='word',state='disabled',padx=6,pady=5); self.vision_panel_text.pack(fill='x',pady=4)
        controls=ttk.Frame(panel); controls.pack(fill='x')
        self.vision_ask_button=ttk.Button(controls,text='Falar sobre a tela',command=self.panel_ask,style='Aeris.Primary.TButton')
        self.vision_ask_button.grid(row=0,column=0,columnspan=2,sticky='ew',pady=2)
        self.vision_update_button=ttk.Button(controls,text='Atualizar captura',command=self.panel_update); self.vision_update_button.grid(row=1,column=0,sticky='ew',padx=(0,2),pady=2)
        self.vision_send_button=ttk.Button(controls,text='Enviar imagem + pergunta',command=self.panel_send); self.vision_send_button.grid(row=1,column=1,sticky='ew',pady=2)
        self.vision_cancel_button=ttk.Button(controls,text='Descartar pergunta',command=self.panel_cancel); self.vision_cancel_button.grid(row=2,column=0,sticky='ew',padx=(0,2),pady=2)
        self.vision_read_button=ttk.Button(controls,text='Ouvir resposta',command=self.panel_read); self.vision_read_button.grid(row=2,column=1,sticky='ew',pady=2)
        controls.columnconfigure(0,weight=1); controls.columnconfigure(1,weight=1)
        ttk.Label(panel,text='Ctrl+Espaço com este painel em foco. Capturas pontuais, não vídeo ao vivo.',wraplength=310,style='Experience.Muted.TLabel').pack(anchor='w',pady=4)
        ttk.Button(panel,text='Encerrar tela e voz',command=self.stop_vision,style='Aeris.Stop.TButton').pack(fill='x',pady=(5,0))
        badge.bind('<Control-space>',lambda _:self.panel_ask() or 'break')
        self.vision_phase='idle'; self.vision_pending=None; self.vision_answer=''; self.vision_message=''
        self.hub.apply_appearance()
        badge.update_idletasks()
        badge.geometry(f'+{max(0,badge.winfo_screenwidth()-badge.winfo_reqwidth()-30)}+32')
        self.vision.begin()
        self.vision_expiry=self.window.after(MAX_SECONDS*1000,self.vision_expired)
        self.vision_timer=self.window.after(150,self.vision_next); self.refresh()
    def panel_visible(self):
        return (not self.closed and self.vision.allowed() and self.vision_badge is not None
                and self.vision_badge.winfo_viewable() and self.hub.permissions.allowed(COMPANION_SCREEN))

    def panel_text(self,text):
        widget=self.vision_panel_text
        widget.configure(state='normal'); widget.delete('1.0','end'); widget.insert('1.0',text); widget.configure(state='disabled')

    def refresh_vision_panel(self):
        if self.vision_badge is None or not self.vision_badge.winfo_exists(): return
        phase=self.vision_phase
        listening=phase=='listen' and self.voice_capture_job==self.job and self.busy
        if phase=='listen':
            state={'preparing':'Preparando microfone…','Silence':'Ouvindo · aguardando fala','Speech':'Ouvindo · reconhecendo fala','Stopped':'Microfone desligado · finalizando'}.get(self.voice_capture_state,'Preparando microfone…')
        else:
            state={'idle':'Tela · capturas periódicas','review':'Captura congelada · revise a pergunta','analysis':'IA analisando · microfone desligado','answer':'Resposta disponível · microfone desligado','speak':'Reproduzindo · microfone desligado'}.get(phase,'Tela')
        if self.busy and self.kind=='monitor_screen': state='Atualizando captura local…'
        self.vision_panel_state.set(state)
        age=max(0,int(monotonic()-self.screen_stamp)) if self.screen_stamp is not None else None
        self.vision_panel_age.set(('Captura de '+str(age)+' s atrás · ' if age is not None else 'Sem captura · ')+f'{self.vision.frames}/{MAX_FRAMES}')
        self.vision_panel_image.configure(image=self.photo or '',text='' if self.photo else 'Nenhuma captura')
        if listening:
            if not self.vision_panel_meter.winfo_manager(): self.vision_panel_meter.pack(fill='x',before=self.vision_panel_text)
            self.vision_panel_meter.configure(value=self.voice_level if self.voice_capture_state in ('Speech','Silence') else 0)
            self.panel_text(self.voice_partial or 'Fale quando o microfone estiver ativo.')
        else:
            self.vision_panel_meter.pack_forget()
            self.panel_text(self.vision_message or 'Atualize a captura e fale sobre o que está vendo.')
        available=self.vision.allowed() and not self.busy and self.hub.permissions.allowed(COMPANION_SCREEN)
        self.vision_ask_button.configure(state='normal' if available and phase in ('idle','answer') and self.screen else 'disabled')
        self.vision_update_button.configure(state='normal' if available and phase in ('idle','answer') else 'disabled')
        self.vision_send_button.configure(state='normal' if available and phase=='review' and self.vision_pending else 'disabled')
        self.vision_cancel_button.configure(state='normal' if available and phase=='review' else 'disabled')
        self.vision_read_button.configure(state='normal' if available and phase=='answer' and self.vision_answer else 'disabled')

    def panel_update(self):
        if not self.panel_visible() or self.busy or self.vision_phase not in ('idle','answer'): return
        if self.vision_timer is not None: self.window.after_cancel(self.vision_timer); self.vision_timer=None
        self.vision_next()

    def panel_ask(self):
        if not self.panel_visible() or self.busy or self.vision_phase not in ('idle','answer') or not self.screen: return
        model=self.model.get().strip(); raw=self.screen
        if not model:
            self.vision_message='Escolha um modelo de visão na configuração da IA antes de iniciar.'; self.refresh(); return
        if not self.authorize(COMPANION_MIC,'Ditar uma pergunta sobre a captura exibida no painel? A captura será congelada; nenhuma imagem será enviada nesta etapa.'): return
        if not self.panel_visible() or self.busy or self.screen is not raw or model!=self.model.get().strip() or not self.hub.permissions.allowed(COMPANION_MIC): return
        self.vision_pending=VisualQuestion(raw,model); self.vision_phase='listen'; self.vision_message=''; self.vision_answer=''
        self.start_voice_capture('panel_listen')
        if not self.busy:
            self.vision_pending=None; self.vision_phase='idle'; self.vision_message='Microfone indisponível. Confira os recursos de fala pt-BR.'; self.refresh()

    def panel_cancel(self):
        if not self.panel_visible() or self.busy or self.vision_phase!='review': return
        self.vision_pending=None; self.vision_phase='idle'; self.vision_message='Pergunta descartada. Nenhuma imagem enviada.'; self.refresh()

    def panel_send(self):
        pending=self.vision_pending
        if not self.panel_visible() or self.busy or self.vision_phase!='review' or pending is None: return
        question=self.vision_message
        if not self.authorize(COMPANION_CHAT,'Enviar somente a imagem e a pergunta revisadas neste painel ao modelo de visão local?'): return
        if (not self.panel_visible() or self.busy or self.vision_phase!='review' or self.vision_pending is not pending
                or self.vision_message!=question or not pending.matches(self.screen,self.model.get().strip())
                or not self.hub.permissions.allowed(COMPANION_CHAT) or not self.hub.permissions.allowed(COMPANION_MIC)): return
        self.vision_phase='analysis'
        if self.start(COMPANION_SCREEN,lambda:(question,describe_screen(pending.model,question,pending.image)),kind='panel_analysis'):
            self.vision_message='Analisando a imagem revisada…'
        else: self.vision_phase='review'
        self.refresh()

    def panel_read(self):
        answer=self.vision_answer
        if not self.panel_visible() or self.busy or self.vision_phase!='answer' or not answer: return
        if not self.authorize(COMPANION_SPEAK,'Reproduzir a resposta desta captura usando a voz local do Windows?'): return
        if not self.panel_visible() or self.busy or self.vision_phase!='answer' or self.vision_answer!=answer or not self.hub.permissions.allowed(COMPANION_SPEAK): return
        try:
            if worker_for(self.hub).busy: raise OSError('Outra operação local ativa.')
            p=speech_process(); self.process=p
            def run():
                try:
                    p.communicate(json.dumps({'action':'speak','text':answer},ensure_ascii=True),timeout=90)
                    if p.returncode: raise OSError('Voz indisponível.')
                except subprocess.TimeoutExpired:
                    p.kill(); p.communicate(); raise
            self.vision_phase='speak'
            if not self.start(COMPANION_SPEAK,run,kind='panel_speak'):
                p.kill(); p.communicate(timeout=2); self.process=None; raise OSError('Não foi possível reproduzir.')
        except (OSError,PermissionError,subprocess.SubprocessError):
            self.vision_phase='answer'; self.vision_message='Voz indisponível. Resposta: '+answer
        self.refresh()

    def panel_result(self,kind,valid,ok,result):
        if not self.panel_visible(): return
        if not valid: return
        if kind=='panel_listen':
            pending=self.vision_pending
            if ok and isinstance(result,tuple) and result[0]=='ok' and pending and pending.matches(self.screen,self.model.get().strip()) and self.hub.permissions.allowed(COMPANION_MIC):
                self.vision_message=validate_message(result[1]); self.vision_phase='review'
            else:
                self.vision_pending=None; self.vision_phase='idle'
                self.vision_message=ERRORS.get(result[1] if ok and isinstance(result,tuple) else 'recognition',ERRORS['recognition'])
        elif kind=='panel_analysis':
            self.vision_pending=None; self.vision_phase='answer'
            if ok and self.hub.permissions.allowed(COMPANION_CHAT):
                question,answer=result; self.vision_answer=answer; self.vision_message=answer
                self.history.extend((('user',('[Captura pontual] '+question)[:4000]),('assistant',answer))); self.history=self.history[-MAX_HISTORY:]; self.draw()
            else:
                self.vision_answer=''; self.vision_message='Análise indisponível. Confira se o modelo aceita imagens e tente novamente.'
        elif kind=='panel_speak':
            self.vision_phase='answer'
            self.vision_message=self.vision_answer if ok else 'Voz indisponível. Resposta: '+self.vision_answer

    def vision_expired(self):
        if self.vision_expiry is not None:
            self.window.after_cancel(self.vision_expiry); self.vision_expiry=None
        self.stop_vision('Limite de acompanhamento atingido. Última captura disponível para revisão.')
    def stop_vision(self,message='Acompanhamento encerrado. Última captura disponível para revisão.'):
        self.vision.stop()
        self.vision_pending=None; self.vision_phase='idle'; self.vision_answer=''; self.vision_message=''
        if self.busy and self.kind=='panel_listen': self.clear_voice_feedback()
        for attr in ('vision_timer','vision_expiry'):
            timer=getattr(self,attr)
            if timer is not None:
                self.window.after_cancel(timer); setattr(self,attr,None)
        if self.vision_badge is not None:
            badge=self.vision_badge; self.vision_badge=None
            if badge.winfo_exists(): badge.destroy()
        if self.busy and self.kind in ('monitor_screen','panel_listen','panel_analysis','panel_speak'): super().stop()
        self.status.set(message); self.refresh()
    def vision_next(self):
        self.vision_timer=None
        if not self.vision.active: return
        if not self.vision.allowed() or not self.hub.permissions.allowed(COMPANION_SCREEN) or self.closed:
            self.stop_vision(); return
        if self.vision_badge is None or not self.vision_badge.winfo_viewable():
            self.stop_vision('Acompanhamento encerrado: indicador não visível.'); return
        if self.busy or self.vision_phase not in ('idle','answer') or worker_for(self.hub).busy:
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
        self.detach_question()
        image=tk.PhotoImage(data=base64.b64encode(result).decode('ascii'))
        factor=max(1,(image.width()+229)//230,(image.height()+259)//260)
        self.photo=image.subsample(factor,factor); self.screen=result; self.screen_stamp=monotonic()
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
        self.detach_question()
        if self.vision.active: self.stop_vision()
        self.screen=None; self.photo=None; self.screen_stamp=None
        if hasattr(self,'image_label'): self.image_label.configure(image='',text='Nenhuma captura')
        if self.capture_timer is not None:
            self.hub.root.after_cancel(self.capture_timer); self.capture_timer=None; self.hub.root.deiconify()
        if self.busy and self.kind in ('screen','vision','visual_question'): super().stop()
        self.refresh()
    def detach_question(self,*,completed=False):
        if self.screen_question is not None and not completed: self.visual_invalid=True
        self.screen_question=None
        if completed: self.visual_invalid=False
        if hasattr(self,'visual_status'): self.visual_status.set('')
    def release_question(self):
        if not self.idle(): return
        self.detach_question(completed=True)
        self.status.set('Rascunho desvinculado. Nenhum texto ou imagem foi enviado.')
        self.update_hint(); self.refresh()
    def ask_screen_voice(self):
        if self.vision.active: return self.panel_ask()
        if self.closed or self.busy or self.voice.active or self.meeting_active or self.capture_timer is not None or not self.screen: return
        if not self.hub.permissions.allowed(COMPANION_SCREEN): return
        if self.input.get('1.0','end-1c').strip():
            self.status.set('Envie ou limpe o rascunho antes de ditar uma pergunta.'); return
        model=self.model.get().strip()
        if not model:
            if not self.ai_open: self.toggle_ai_settings()
            self.configure_ai(); return
        raw=self.screen
        if not self.authorize(COMPANION_MIC,'Usar o microfone para ditar uma pergunta sobre a captura revisada? Nenhuma imagem será enviada neste passo.'): return
        if not self.idle() or self.screen is not raw or model!=self.model.get().strip() or self.input.get('1.0','end-1c').strip() or not self.hub.permissions.allowed(COMPANION_SCREEN) or not self.hub.permissions.allowed(COMPANION_MIC): return
        self.detach_question(completed=True)
        pending=VisualQuestion(raw,model)
        try:
            if worker_for(self.hub).busy: raise OSError('Outra operação local ativa.')
            p=speech_process(); self.process=p
            def work():
                try:
                    out,_=p.communicate(json.dumps({'action':'listen','text':''}),timeout=18)
                    if p.returncode: raise OSError('Sem transcrição.')
                    return pending,validate_message(strict_json(out,32768))
                except subprocess.TimeoutExpired:
                    p.kill(); p.communicate(); raise
            if not self.start(COMPANION_MIC,work,kind='visual_question'):
                p.kill()
                try: p.communicate(timeout=2)
                except (OSError,subprocess.TimeoutExpired): pass
                self.process=None; raise OSError('Não foi possível iniciar a voz.')
        except (OSError,PermissionError):
            self.status.set('Ditado indisponível. Confira o microfone e o reconhecedor pt-BR.'); self.refresh(); return
        self.status.set('MICROFONE ATIVO · dite sua pergunta sobre a captura.')
    def analyze(self):
        if self.closed or self.busy or self.meeting_active or self.voice.active or self.capture_timer is not None or not self.screen or not self.hub.permissions.allowed(COMPANION_SCREEN): return
        if self.visual_invalid or (self.screen_question is not None and not self.screen_question.matches(self.screen,self.model.get().strip())):
            self.detach_question(); self.status.set('Captura ou modelo alterado. Revise o rascunho.'); self.refresh(); return
        if self.vision.active:
            if self.vision_phase not in ('idle','answer'): return
            self.stop_vision('Acompanhamento encerrado para análise manual da captura.')
        if not self.model.get().strip():
            if not self.ai_open: self.toggle_ai_settings()
            self.configure_ai(); return
        if not self.authorize(COMPANION_CHAT,'Permitir comunicação com o modelo local?'): return
        raw=self.screen; model=self.model.get().strip(); question=self.input.get('1.0','end-1c').strip() or 'Explique o que aparece nesta imagem e como posso continuar.'
        try: validate_message(question)
        except ValueError as e: self.status.set(str(e)); return
        revision=self.hub.permissions.revision
        if not ask_confirmation(self.hub.root,self.hub.settings.appearance.theme,'Enviar captura?', 'Enviar apenas esta imagem revisada e a pergunta ao modelo de visão local? Não inclui histórico ou outros arquivos.'): return
        if self.screen is not raw or revision!=self.hub.permissions.revision or model!=self.model.get().strip() or question!=(self.input.get('1.0','end-1c').strip() or 'Explique o que aparece nesta imagem e como posso continuar.') or not self.hub.permissions.allowed(COMPANION_CHAT): return
        if not self.idle() or not self.hub.permissions.allowed(COMPANION_SCREEN): return
        if self.start(COMPANION_SCREEN,lambda:(question,describe_screen(model,question,raw)),kind='vision'):
            self.detach_question(completed=True); self.input.delete('1.0','end')
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
    def meeting_cap(self):
        return MEETING_LOOPBACK if self.meeting_source=='internal' else COMPANION_MIC
    def start_internal_meeting(self):
        if self.busy or self.meeting_active or self.voice.active or self.vision.active: return
        if not loopback_available():
            messagebox.showinfo('Áudio interno experimental','Disponível na execução por código-fonte no Windows, com soundcard, numpy e faster-whisper instalados. Escolha uma pasta de modelo Whisper convertido previamente instalada. Nenhum download é iniciado pelo Aeris.',parent=self.hub.root); return
        folder=filedialog.askdirectory(parent=self.hub.root,title='Modelo Whisper local')
        if not folder: return
        try: model=model_path(folder)
        except (OSError,ValueError) as exc: self.status.set(str(exc)); return
        self.start_meeting('internal',model)
    def start_meeting(self,source='mic',model=None):
        if self.closed or self.busy or self.meeting_active or self.voice.active or self.vision.active or self.capture_timer is not None: return
        self.close_meeting_review()
        revision=self.hub.permissions.revision
        description=('A saída padrão do Windows inclui TODOS os sons reproduzidos, não apenas a chamada. O áudio é capturado em blocos de 30 segundos, com pausas durante a transcrição local. Até 20 blocos; sem gravação em arquivo.' if source=='internal' else 'Microfone padrão em blocos de ditado, até 20 blocos; sem gravação em arquivo.')
        if not ask_confirmation(self.hub.root,self.hub.settings.appearance.theme,'Transcrição de reunião','Todos os participantes foram avisados e concordam com a transcrição? '+description+' Você pode interromper a qualquer momento.'): return
        if self.closed or self.hub.permissions.revision!=revision: return
        cap=MEETING_LOOPBACK if source=='internal' else COMPANION_MIC
        if not self.authorize(cap,'Autorizar a fonte de áudio selecionada nesta sessão?'): return
        if self.closed or self.busy or self.meeting_active or self.voice.active or self.vision.active or self.capture_timer is not None or not self.hub.permissions.allowed(cap): return
        self.meeting_source=source; self.meeting_model=model
        self.meeting_active=True; self.meeting_generation+=1; self.meeting_chunks=[]; self.meeting_silences=0; self.meeting_phase='preparing'
        badge=tk.Toplevel(self.hub.root); self.meeting_badge=badge
        badge.title('Aeris · Reunião'); badge.attributes('-topmost',True); badge.resizable(False,False)
        badge.protocol('WM_DELETE_WINDOW',self.stop_meeting)
        panel=ttk.Frame(badge,padding=10); panel.pack(fill='both',expand=True)
        head=ttk.Frame(panel); head.pack(fill='x')
        wind_mark(head,self.hub.settings.appearance.theme,size=36,surface='air').pack(side='left',padx=(0,8))
        ttk.Label(head,text='Aeris · Reunião',style='Experience.Section.TLabel').pack(side='left')
        ttk.Label(panel,textvariable=self.meeting_status,style='Experience.Section.TLabel',wraplength=280).pack(anchor='w',pady=4)
        ttk.Label(panel,textvariable=self.meeting_detail,style='Experience.Muted.TLabel',wraplength=280).pack(anchor='w')
        self.meeting_badge_meter=ttk.Progressbar(panel,maximum=100,mode='determinate',style='Experience.Horizontal.TProgressbar')
        if source=='mic': self.meeting_badge_meter.pack(fill='x',pady=3)
        ttk.Button(panel,text='Parar transcrição',command=self.stop_meeting,style='Aeris.Stop.TButton').pack(fill='x',pady=(5,0))
        from aeris.theme import apply_tree
        apply_tree(badge,self.hub.settings.appearance.theme)
        badge.update_idletasks(); badge.geometry(f'+{max(0,badge.winfo_screenwidth()-badge.winfo_reqwidth()-30)}+32')
        badge.bind('<Unmap>',lambda e:self.stop_meeting() if e.widget is badge and not self.closed and self.meeting_badge is badge and self.meeting_active else None,add='+')
        self.meeting_text.configure(state='disabled'); self.meeting_timer=self.window.after(150,self.meeting_next); self.refresh()
    def meeting_next(self):
        self.meeting_timer=None
        if not self.meeting_active or not self.hub.permissions.allowed(self.meeting_cap()) or len(self.meeting_chunks)>=20 or self.meeting_badge is None or not self.meeting_badge.winfo_viewable(): self.stop_meeting(); return
        if self.meeting_source=='internal':
            self.meeting_phase='internal'
            try:
                if worker_for(self.hub).busy: raise OSError()
                p=start_loopback(self.meeting_model); self.process=p
                if not self.start(MEETING_LOOPBACK,lambda:read_loopback(p),kind='meeting'):
                    p.kill(); self.process=None; raise OSError()
            except (OSError,ValueError,PermissionError): self.stop_meeting(); self.status.set('Áudio interno indisponível. Confira dependências, saída padrão e modelo local.'); return
            self.status.set('REUNIÃO ATIVA · áudio interno · captura e transcrição em blocos.'); return
        self.meeting_phase='preparing'
        self.start_voice_capture('meeting_mic')
        if not self.busy:
            self.stop_meeting('Microfone indisponível. Confira o reconhecedor pt-BR e tente novamente.')

    def refresh_meeting_status(self):
        stage=1 if self.meeting_active else 2 if self.meeting_phase=='review' or (self.busy and self.kind=='minutes') else 0
        for index,label in enumerate(self.meeting_step_labels):
            label.configure(style='Experience.CurrentStep.TLabel' if index==stage else 'Experience.Step.TLabel')
        if self.meeting_active:
            if self.meeting_source=='mic':
                state=self.voice_capture_state if self.busy and self.kind=='meeting_mic' and self.voice_capture_job==self.job else 'preparing'
                label={'preparing':'Preparando microfone','Silence':'Microfone ativo · aguardando fala','Speech':'Microfone ativo · reconhecendo','Stopped':'Finalizando trecho'}.get(state,'Preparando microfone')
                level=self.voice_level if state in ('Silence','Speech') else 0
                if not self.meeting_meter.winfo_manager(): self.meeting_meter.pack(fill='x',before=self.meeting_controls,pady=2)
                self.meeting_meter.configure(value=level)
                if self.meeting_badge is not None and self.meeting_badge.winfo_exists(): self.meeting_badge_meter.configure(value=level)
                detail=(self.voice_partial[:180] if self.voice_partial else 'Ditado em blocos · pausas entre trechos.')
            else:
                label='Áudio interno · preparando/capturando/transcrevendo' if self.busy else 'Preparando próximo bloco'
                detail='Todos os sons da saída padrão · sem nível de entrada disponível.'
                self.meeting_meter.pack_forget()
            self.meeting_status.set('2 · '+label)
            self.meeting_detail.set(f'{len(self.meeting_chunks)}/20 blocos concluídos · '+detail)
        else:
            self.meeting_meter.pack_forget()
            if self.meeting_phase=='review':
                self.meeting_status.set('3 · Revisar e salvar')
                self.meeting_detail.set('Confira transcrição e notas. A ata gerada por IA é um rascunho.')
            elif self.busy and self.kind=='minutes':
                self.meeting_status.set('3 · Preparando rascunho da ata')
                self.meeting_detail.set('Nenhuma tarefa ou ata será salva automaticamente.')
            else:
                self.meeting_status.set('1 · Preparar áudio')
                self.meeting_detail.set('Avise os participantes. Sem identificação de interlocutores. '+('Áudio interno experimental: Whisper local.' if loopback_available() else 'Áudio interno indisponível.'))

    def meeting_content(self):
        transcript=self.meeting_text.get('1.0','end-1c')
        notes=self.meeting_notes.get('1.0','end-1c').strip()
        return transcript+('\n\nNotas manuais:\n'+notes if notes else '')

    def stop_meeting(self,message='Captura de áudio encerrada. Revise a transcrição antes de salvar.'):
        self.meeting_active=False; self.meeting_generation+=1; self.meeting_model=None; self.meeting_phase='review'
        if self.busy and self.kind=='meeting_mic': self.clear_voice_feedback()
        if self.meeting_badge is not None:
            badge=self.meeting_badge; self.meeting_badge=None
            if badge.winfo_exists(): badge.destroy()
        if self.meeting_timer is not None: self.window.after_cancel(self.meeting_timer); self.meeting_timer=None
        if self.busy and self.kind in ('meeting','meeting_mic'): super().stop()
        self.meeting_text.configure(state='normal'); self.status.set(message); self.refresh()
    def close_meeting_review(self):
        if self.meeting_review is not None:
            window=self.meeting_review; self.meeting_review=None
            if window.winfo_exists(): window.destroy()
    def meeting_summary(self):
        if self.meeting_active or self.busy or self.voice.active or self.vision.active: return
        source=self.meeting_content()
        text=source.strip()
        if len(text)>4000 and self.meeting_text.tag_ranges('sel'):
            text=self.meeting_text.get('sel.first','sel.last').strip()
            self.status.set('Somente o trecho selecionado será enviado; notas manuais não incluídas.')
        if not text or len(text)>4000:
            self.status.set('Selecione um trecho de até 4.000 caracteres para gerar a ata.'); return
        model=self.model.get().strip()
        if not model:
            if not self.ai_open: self.toggle_ai_settings()
            self.configure_ai(); return
        scope='Somente o trecho selecionado da transcrição, sem notas manuais.' if text!=source.strip() else 'Transcrição e notas manuais, quando presentes.'
        if not self.authorize(COMPANION_CHAT,'Gerar uma ata com o modelo local? '+scope+' Não inclui histórico.'): return
        revision=self.hub.permissions.revision
        if not ask_confirmation(self.hub.root,self.hub.settings.appearance.theme,'Gerar ata?', scope+' Enviar ao modelo local '+str(len(text))+' caracteres? A ata poderá conter erros e será revisada antes de salvar.'): return
        if self.closed or self.busy or revision!=self.hub.permissions.revision or source!=self.meeting_content() or model!=self.model.get().strip(): return
        self.close_meeting_review()
        if self.start(COMPANION_CHAT,lambda:(source,model,prepare_minutes(model,text)),kind='minutes'):
            self.status.set('Preparando ata e sugestões de tarefas. Nada foi salvo.')
    def review_minutes(self,source,draft):
        self.close_meeting_review()
        window=tk.Toplevel(self.hub.root); self.meeting_review=window
        window.title('Aeris · Revisar ata'); window.geometry('680x640'); window.minsize(480,520)
        window.protocol('WM_DELETE_WINDOW',self.close_meeting_review)
        panel=ttk.Frame(window,padding=16); panel.pack(fill='both',expand=True)
        head=ttk.Frame(panel); head.pack(fill='x')
        wind_mark(head,self.hub.settings.appearance.theme,size=40,surface='air').pack(side='left',padx=(0,8))
        ttk.Label(head,text='Revisar ata e tarefas',style='Experience.Subtitle.TLabel').pack(side='left')
        ttk.Label(panel,text='Rascunho da IA · confira os fatos e remova sugestões incorretas. Nenhuma tarefa será transferida automaticamente.',wraplength=440).pack(anchor='w')
        title=tk.StringVar(window,'Ata revisada'); participants=tk.StringVar(window,'')
        ttk.Label(panel,text='Título da reunião').pack(anchor='w',pady=(5,0)); ttk.Entry(panel,textvariable=title).pack(fill='x')
        ttk.Label(panel,text='Participantes (opcional, informe manualmente)').pack(anchor='w',pady=(5,0)); ttk.Entry(panel,textvariable=participants).pack(fill='x')
        ttk.Label(panel,text='Resumo e decisões').pack(anchor='w',pady=(8,0))
        notes=tk.Text(panel,wrap='word',height=8); notes.pack(fill='both',expand=True); notes.insert('1.0',draft.notes)
        ttk.Label(panel,text='Tarefas sugeridas (uma por linha)').pack(anchor='w',pady=(8,0))
        actions=tk.Text(panel,wrap='word',height=5); actions.pack(fill='both',expand=True); actions.insert('1.0','\n'.join(a.title for a in draft.actions))
        def save():
            if self.meeting_review is not window or self.meeting_active or source!=self.meeting_content() or not self.hub.permissions.allowed(COMPANION_CHAT):
                self.close_meeting_review(); self.status.set('Ata expirada. Gere novamente.'); return
            from aeris.meeting import MeetingStore,Action
            try:
                tasks=tuple(Action(v.strip()) for v in actions.get('1.0','end-1c').splitlines() if v.strip())
                body=notes.get('1.0','end-1c').strip()
                if not body: raise ValueError('Informe o resumo revisado.')
                if not self.ensure_tool('Meeting'): return
                if self.meeting_review is not window or source!=self.meeting_content() or not self.hub.permissions.allowed(COMPANION_CHAT): return
                if self.hub.meeting_store is None: self.hub.meeting_store=MeetingStore()
                self.hub.meeting_store.add(title.get(),date.today().isoformat(),participants.get(),'',body,tasks)
            except ValueError as exc: messagebox.showwarning('Revisar ata',str(exc),parent=window); return
            if self.hub.alive(self.hub.meeting_window): self.hub.meeting_window.render()
            self.close_meeting_review(); self.status.set('Ata e sugestões revisadas salvas em Reuniões. Transfira tarefas individualmente.')
        ttk.Button(panel,text='Salvar ata revisada',command=save,style='Experience.Primary.TButton').pack(fill='x',pady=(8,3))
        ttk.Button(panel,text='Descartar',command=self.close_meeting_review).pack(fill='x')
        from aeris.theme import apply_tree
        apply_tree(window,self.hub.settings.appearance.theme)
    def save_meeting(self):
        if self.meeting_active: return
        text=self.meeting_content().strip()
        if not text: return
        if not messagebox.askyesno('Salvar ata?', 'Salvar a transcrição revisada e notas manuais como anotação de reunião nesta sessão?',parent=self.hub.root): return
        if text!=self.meeting_content().strip() or not self.ensure_tool('Meeting'): return
        from aeris.meeting import MeetingStore
        if self.hub.meeting_store is None: self.hub.meeting_store=MeetingStore()
        try: self.hub.meeting_store.add('Reunião transcrita',date.today().isoformat(),'','',text,())
        except ValueError as e: self.status.set(str(e)); return
        if self.hub.alive(self.hub.meeting_window): self.hub.meeting_window.render()
        self.status.set('Ata salva na sessão. Revise participantes e decisões em Reuniões.')
    def stop(self):
        self.clear_voice_feedback()
        if self.stream_cancel is not None:
            self.stream_cancel.set()
            if self.hub.permissions.allowed(COMPANION_CHAT): self.restore_stream_draft()
            self.stream_pending=None; self.stream_partial=''; self.draw()
        if self.setup_cancel is not None: self.setup_cancel.set()
        self.detach_question()
        if self.vision.active: self.stop_vision()
        if self.voice.active: self.stop_voice()
        if self.meeting_active: self.stop_meeting()
        if self.capture_timer is not None: self.discard_screen()
        super().stop()
        if self.hub.root.state()=='withdrawn': self.hub.root.deiconify()
    def poll(self):
        if self.kind=='stream_chat': return self.poll_stream()
        if self.kind in ('ai_setup','ai_restore'):
            self.timer=None
            if self.closed: return
            try:
                while True:
                    stage,msg,completed,total=self.setup_progress.get_nowait()
                    self.setup_phase.set(msg); self.status.set(msg)
                    if stage=='test' and msg.startswith('Resposta em '): self.setup_result=msg
                    if total is not None:
                        self.setup_bar.stop(); self.setup_bar.configure(mode='determinate',maximum=total,value=completed)
                        self.setup_phase.set(f'{msg} · {completed/1048576:.1f}/{total/1048576:.1f} MiB · {completed/total:.0%} desta camada')
                    elif str(self.setup_bar.cget('mode'))!='indeterminate':
                        self.setup_bar.configure(mode='indeterminate',maximum=100,value=0); self.setup_bar.start(14)
            except queue.Empty: pass
            try: job,ok,result=self.results.get_nowait()
            except queue.Empty: self.schedule_poll(); return
            self.busy=False; self.process=None; self.setup_cancel=None
            self.setup_bar.stop(); self.setup_bar.pack_forget(); self.setup_detail.pack_forget()
            if job==self.job and ok:
                self.model_entry.configure(values=(result,)); self.model.set(result)
                self.ready_state.set(('IA local pronta. '+self.setup_result+' · Visão e voz exigem teste separado.') if self.kind=='ai_setup' else 'Servidor e modelo restaurados. Execute Testar IA para verificar a inferência.')
                self.status.set('IA local pronta para conversar.')
            elif job==self.job:
                self.ready_state.set(str(result)); self.status.set('Configuração não concluída.');
            else: self.ready_state.set('Configuração cancelada.')
            self.refresh(); return
        if self.kind in ('voice_listen','voice_dictation','panel_listen','meeting_mic'): self.drain_voice_feedback()
        if self.kind not in ('screen','vision','meeting','models','route','voice_listen','voice_dictation','voice_chat','voice_speak','monitor_screen','minutes','visual_question','ready_test','panel_listen','panel_analysis','panel_speak','meeting_mic'): return super().poll()
        self.timer=None
        if self.closed: return
        try: job,ok,result=self.results.get_nowait()
        except queue.Empty: self.schedule_poll(); return
        self.busy=False; self.process=None
        kind=self.kind
        if kind=='screen': self.hub.root.deiconify()
        valid=job==self.job and self.hub.permissions.allowed(self.cap)
        if kind in ('voice_listen','voice_dictation','panel_listen','meeting_mic'): self.clear_voice_feedback()
        if kind in ('panel_listen','panel_analysis','panel_speak'):
            self.panel_result(kind,valid,ok,result)
        elif kind=='voice_dictation':
            if valid and ok and isinstance(result,tuple) and result[0]=='ok':
                if not self.input.get('1.0','end-1c').strip(): self.input.insert('1.0',result[1]); self.status.set('Ditado concluído. Revise o texto antes de enviar.')
                else: self.status.set('Ditado descartado para preservar o rascunho.')
            elif valid: self.status.set(ERRORS.get(result[1] if ok and isinstance(result,tuple) else 'recognition',ERRORS['recognition']))
        elif kind in ('voice_listen','voice_chat','voice_speak'):
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
        elif kind=='ready_test':
            elapsed=f' ({monotonic()-self.test_started:.1f} s)' if self.test_started is not None else ''
            self.test_started=None
            if valid and ok and result[0]==self.model.get().strip() and result[1]:
                self.ready_state.set('Teste de texto aprovado'+elapsed+'. Resposta: '+str(result[1])[:240]+' · Visão e voz exigem teste separado.')
                self.status.set('O modelo respondeu à saudação fictícia'+elapsed+'.')
            else:
                self.ready_state.set('Teste não concluído'+elapsed+'. Confira modelo, Ollama, autorização e recursos do computador.')
        elif kind=='models':
            if valid and ok and result:
                self.model_entry.configure(values=result)
                chosen=model_selection(self.model.get(),result)
                if chosen!=self.model.get(): self.model.set(chosen)
                self.ready_state.set(f'{len(result)} modelo(s) local(is) encontrado(s). Selecione e teste a IA.')
                self.status.set('Modelos locais encontrados.')
            elif valid and ok:
                self.model_entry.configure(values=()); self.ready_state.set('Ollama respondeu, mas não há modelo local elegível. Instale um modelo manualmente.')
            else:
                self.ready_state.set('Consulta não concluída. Verifique se o Ollama está aberto e autorizado.')
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
        elif valid and kind=='visual_question':
            if ok:
                pending,text=result
                try:
                    draft=pending.draft(text,self.screen,self.model.get().strip(),mic_allowed=self.hub.permissions.allowed(COMPANION_MIC),screen_allowed=self.hub.permissions.allowed(COMPANION_SCREEN),empty_editor=not self.input.get('1.0','end-1c').strip())
                except ValueError as exc: self.status.set(str(exc))
                else:
                    self.screen_question=pending; self.visual_invalid=False; self.input.insert('1.0',draft)
                    if self.compact: self.hub.navigate('chat')
                    self.visual_status.set('Pergunta vinculada à captura. Revise e envie.')
                    self.status.set('Revise a pergunta transcrita e clique Enviar ou Analisar captura com IA.')
            else: self.status.set('Não foi possível reconhecer a pergunta por voz.')
        elif valid and kind=='vision':
            if ok and self.hub.permissions.allowed(COMPANION_CHAT):
                question,response=result; self.history.extend((('user',('[Captura pontual] '+question)[:4000]),('assistant',response))); self.history=self.history[-MAX_HISTORY:]; self.draw(); self.status.set('Análise concluída. A IA pode errar.')
                if self.auto_speak.get() and self.hub.permissions.allowed(COMPANION_SPEAK): self.speech('speak')
            else: self.status.set('Modelo de visão indisponível ou permissão revogada.')
        elif valid and kind=='minutes':
            if ok:
                source,model,draft=result
                if source==self.meeting_content() and model==self.model.get().strip(): self.review_minutes(source,draft)
                else: self.status.set('Transcrição ou modelo alterado; ata descartada.')
            else: self.status.set('Não foi possível gerar uma ata válida. Tente novamente ou revise manualmente.')
        elif valid and kind in ('meeting','meeting_mic') and self.meeting_active:
            if kind=='meeting_mic':
                if ok and isinstance(result,tuple) and result[0]=='ok': result=result[1]; self.meeting_silences=0
                elif ok and isinstance(result,tuple) and result[1]=='silence' and self.meeting_silences<2:
                    self.meeting_silences+=1; self.meeting_chunks.append('')
                    if len(self.meeting_chunks)<20: self.meeting_timer=self.window.after(350,self.meeting_next)
                    else: self.stop_meeting()
                    self.refresh(); return
                else:
                    self.stop_meeting(ERRORS.get(result[1] if ok and isinstance(result,tuple) else 'recognition',ERRORS['recognition'])); return
            if ok:
                current=self.meeting_text.get('1.0','end-1c')
                if result.strip() and len(current)+len(result)+(1 if current else 0)>8000: self.stop_meeting(); self.status.set('Limite de transcrição atingido; revise e salve.'); self.refresh(); return
                if result.strip():
                    self.meeting_text.configure(state='normal'); self.meeting_text.insert('end',('\n' if current else '')+result); self.meeting_text.configure(state='disabled'); self.meeting_text.see('end')
                self.meeting_chunks.append(result)
                if len(self.meeting_chunks)<20: self.meeting_timer=self.window.after(350,self.meeting_next)
                else: self.stop_meeting()
            else: self.stop_meeting(); self.status.set('Transcrição pausada: silêncio ou recurso indisponível. Revise e reinicie se necessário.')
        self.refresh()
    def dirty(self):
        return super().dirty() or self.voice.active or self.vision.active or bool(self.screen or self.note.get('1.0','end-1c') or self.meeting_content() or self.meeting_active)
    def destroyed(self,event):
        if event.widget is self.window:
            self.closed=True; self.meeting_active=False
            if self.voice_cancel is not None: self.voice_cancel.set()
            if self.stream_cancel is not None: self.stream_cancel.set()
            self.stream_pending=None; self.stream_partial=''
            if self.progress_running:
                try: self.activity_progress.stop()
                except tk.TclError: pass
                self.progress_running=False
            if self.setup_cancel is not None: self.setup_cancel.set()
            try: self.setup_bar.stop()
            except tk.TclError: pass
            self.ai_runtime.close(); reset_endpoint()
            self.voice.stop(); self.vision.stop()
            # Tk may already be destroying siblings from a snapshot of root.children.
            # Defer cleanup when only the workspace is being destroyed.
            for attr in ('meeting_badge','vision_badge'):
                badge=getattr(self,attr); setattr(self,attr,None)
                if badge is not None:
                    try: self.hub.root.after_idle(lambda w=badge: w.destroy() if w.winfo_exists() else None)
                    except tk.TclError: pass
            for timer in (self.meeting_timer,self.capture_timer,self.voice_timer,self.vision_timer,self.vision_expiry):
                if timer is not None:
                    try: self.hub.root.after_cancel(timer)
                    except tk.TclError: pass
            self.screen=None; self.photo=None; self.screen_question=None; self.meeting_chunks.clear(); self.meeting_active=False
        super().destroyed(event)

class ExperienceHub(Hub):
    def __init__(self,root,settings=None):
        super().__init__(root,settings)
        root.bind('<Control-f>',self.focus_catalog)
        root.bind('<Control-l>',self.focus_conversation)
        root.bind('<Control-Shift-S>',self.stop_activity)
        root.bind('<Configure>',self.workspace_configure,add='+')
        self.conversation.resize_workspace(root.winfo_width() if root.winfo_width()>1 else root.winfo_reqwidth())
    def workspace_configure(self,event):
        if event.widget is self.root and not self.conversation.closed:
            self.conversation.resize_workspace(event.width)
    def focus_catalog(self,_=None):
        self.navigate('catalog'); self.search.focus_set()
        return 'break'
    def focus_conversation(self,_=None):
        if self.conversation.idle():
            self.navigate('chat'); self.conversation.set_context(False); self.conversation.input.focus_set()
        return 'break'
    def stop_activity(self,_=None):
        if not self.conversation.idle(): self.conversation.stop()
        return 'break'
    def build(self):
        super().build()
        self.legacy_side,self.catalog=self.root.winfo_children()[:2]
        self.legacy_side.pack_forget(); self.catalog.pack_forget()
        self.legacy_catalog=self.catalog; self.build_catalog()
        sw=self.root.winfo_screenwidth(); sh=self.root.winfo_screenheight()
        width=min(1240,max(760,sw-44)); height=min(780,max(540,sh-100))
        self.root.geometry(f'{width}x{height}+16+12'); self.root.minsize(min(870,width),min(570,height))
        side=self.sidebar=ttk.Frame(self.root,padding=16,width=216,style='Experience.Side.TFrame'); side.pack(side='left',fill='y'); side.pack_propagate(False)
        self.sidebar_compact=False
        brand=ttk.Frame(side,style='Experience.Side.TFrame'); brand.pack(fill='x',pady=(0,4))
        self.sidebar_mark=wind_mark(brand,self.settings.appearance.theme,size=40,surface='sidebar',ink='sidebar_muted'); self.sidebar_mark.pack(side='left')
        ttk.Label(brand,text='aeris.',style='Experience.CompactBrand.TLabel').pack(side='left',padx=(5,0))
        self.sidebar_slogan=ttk.Label(side,text='Eficiência e Simplicidade.',style='Experience.Side.TLabel',wraplength=165); self.sidebar_slogan.pack(anchor='w',pady=(0,8))
        self.sidebar_toggle=ttk.Button(side,text='Recolher menu',command=self.toggle_sidebar,style='Experience.Nav.TButton'); self.sidebar_toggle.pack(fill='x',pady=(0,10))
        ttk.Label(side,text='ESPAÇO DE TRABALHO',style='Experience.SideSection.TLabel').pack(anchor='w',pady=(0,8))
        self.nav_buttons={}
        for label,command in [('Conversar',lambda:self.navigate('chat')),('Tela',lambda:self.navigate('screen')),('Anotações',lambda:self.navigate('notes')),('Reuniões',lambda:self.navigate('meeting')),('Tarefas',lambda:self.open_friendly('Checklist')),('Ferramentas',lambda:self.navigate('catalog'))]:
            button=ttk.Button(side,text=label,command=command,style='Experience.Nav.TButton'); button.pack(fill='x',pady=2); self.nav_buttons[label]=button
        ttk.Separator(side).pack(fill='x',pady=10)
        ttk.Label(side,text='PREFERÊNCIAS',style='Experience.SideSection.TLabel').pack(anchor='w',pady=(0,8))
        ttk.Button(side,text='Configurações',command=self.open_appearance,style='Experience.Nav.TButton').pack(fill='x',pady=3)
        ttk.Button(side,text='Privacidade',command=self.open_privacy,style='Experience.Nav.TButton').pack(fill='x',pady=3)
        ttk.Button(side,text='Permissões',command=self.open_permissions,style='Experience.Nav.TButton').pack(fill='x',pady=3)
        self.sidebar_footer=ttk.Label(side,text='K&G Vision\nVersão em desenvolvimento',style='Experience.Side.TLabel',wraplength=150); self.sidebar_footer.pack(side='bottom',anchor='w')
        self.conversation=Conversation(self,self.root)
        self.navigate('chat')
    def toggle_theme(self):
        # Respect any unsaved appearance preferences instead of overwriting them.
        if self.alive(self.appearance_window):
            self.appearance_window.window.lift(); return
        current=self.settings.appearance
        target='Claro' if current.theme=='Escuro' else 'Escuro'
        try: self.settings.set_appearance(replace(current,theme=target))
        except (OSError,ValueError):
            messagebox.showerror('Aeris','Não foi possível salvar o tema.',parent=self.root); return
        self.apply_appearance()
    def toggle_sidebar(self):
        self.sidebar_compact=not self.sidebar_compact
        self.sidebar.configure(width=154 if self.sidebar_compact else 216,padding=8 if self.sidebar_compact else 16)
        self.sidebar_slogan.configure(wraplength=130 if self.sidebar_compact else 165)
        self.sidebar_footer.configure(wraplength=130 if self.sidebar_compact else 150)
        self.sidebar_toggle.configure(text='Expandir menu' if self.sidebar_compact else 'Recolher menu')
    def build_catalog(self):
        self.catalog_index=CatalogIndex(self.modules,NAMES,CATEGORIES,HELP,GOALS)
        self.recent_tools=[]
        self.catalog=ttk.Frame(self.root,padding=18)
        f=self.catalog
        ttk.Label(f,text='Biblioteca de ferramentas',style='Experience.Title.TLabel').pack(anchor='w')
        ttk.Label(f,text='50 ferramentas locais, organizadas por objetivo. Escolha uma para conhecer ou abrir.',style='Experience.Muted.TLabel').pack(anchor='w',pady=(2,12))
        ttk.Label(f,text='Buscar por nome, tarefa ou exemplo',style='Experience.Muted.TLabel').pack(anchor='w')
        filters=ttk.Frame(f); filters.pack(fill='x',pady=(0,8))
        self.search=ttk.Entry(filters,textvariable=self.query); self.search.pack(side='left',fill='x',expand=True,ipady=5)
        self.search.bind('<Return>',self.focus_results); self.search.bind('<Escape>',lambda _:self.clear_filters())
        ttk.Button(filters,text='Limpar filtros',command=self.clear_filters).pack(side='right',padx=(5,0))
        scopes=ttk.Frame(f); scopes.pack(fill='x',pady=(0,8))
        self.catalog_scope=tk.StringVar(self.root,'Todas')
        for label in ('Todas','Favoritas','Recentes'):
            ttk.Radiobutton(scopes,text=label,value=label,variable=self.catalog_scope,command=self.refresh,style='Experience.Goal.TRadiobutton').pack(side='left',padx=(0,8))
        self.goal=tk.StringVar(self.root,'Todas')
        choices=self.catalog_choices=ttk.Frame(f); choices.pack(fill='x',pady=(0,8))
        self.goal_label=ttk.Label(choices,text='Objetivo')
        self.goalbox=ttk.Combobox(choices,textvariable=self.goal,values=('Todas',*GOALS),state='readonly',width=18)
        self.goalbox.bind('<<ComboboxSelected>>',lambda _:self.refresh())
        self.category_label=ttk.Label(choices,text='Categoria')
        self.category_display=tk.StringVar(self.root,'Todas')
        self.category_box=ttk.Combobox(choices,textvariable=self.category_display,values=('Todas',*CATEGORIES.values()),state='readonly',width=13)
        self.category_box.bind('<<ComboboxSelected>>',self.choose_category)
        self.catalog_filters_compact=None
        self.layout_catalog_filters(True)
        choices.bind('<Configure>',self.resize_catalog_filters,add='+')
        self.count=ttk.Label(f,text='',style='Experience.Muted.TLabel'); self.count.pack(anchor='w',pady=(0,6))
        body=ttk.Frame(f); body.pack(fill='both',expand=True); body.columnconfigure(0,weight=2); body.columnconfigure(1,weight=3); body.rowconfigure(0,weight=1)
        left=ttk.Frame(body); left.grid(row=0,column=0,sticky='nsew',padx=(0,10))
        self.listbox=tk.Listbox(left,font=('Segoe UI',11),relief='flat',highlightthickness=1,exportselection=False,activestyle='none',width=24)
        ttk.Label(left,text='RESULTADOS',style='Experience.Section.TLabel').grid(row=0,column=0,sticky='w',pady=(0,6))
        left.columnconfigure(0,weight=1); left.rowconfigure(1,weight=1)
        self.listbox.grid(row=1,column=0,sticky='nsew')
        sb=ttk.Scrollbar(left,command=self.listbox.yview); sb.grid(row=1,column=1,sticky='ns')
        horizontal=ttk.Scrollbar(left,orient='horizontal',command=self.listbox.xview); horizontal.grid(row=2,column=0,sticky='ew')
        self.listbox.configure(yscrollcommand=sb.set,xscrollcommand=horizontal.set)
        self.listbox.bind('<<ListboxSelect>>',self.show_selected); self.listbox.bind('<Return>',self.open_selected); self.listbox.bind('<Double-1>',self.open_selected)
        self.listbox.bind('<Escape>',self.focus_catalog_search)
        detail_host=ttk.Frame(body,style='Experience.Card.TFrame'); detail_host.grid(row=0,column=1,sticky='nsew')
        self.detail_canvas=tk.Canvas(detail_host,highlightthickness=1,takefocus=True,width=180,height=120)
        self.detail_canvas._aeris_scroll=True
        detail_scroll=ttk.Scrollbar(detail_host,orient='vertical',command=self.detail_canvas.yview)
        detail_scroll.pack(side='right',fill='y'); self.detail_canvas.pack(side='left',fill='both',expand=True)
        self.detail_canvas.configure(yscrollcommand=detail_scroll.set)
        detail=ttk.Frame(self.detail_canvas,padding=14,style='Experience.Card.TFrame')
        self.detail_canvas_item=self.detail_canvas.create_window(0,0,anchor='nw',window=detail)
        self.detail_canvas.bind('<Configure>',lambda e:self.detail_canvas.itemconfigure(self.detail_canvas_item,width=e.width))
        for key,amount,unit in (('<Up>',-1,'units'),('<Down>',1,'units'),('<Prior>',-1,'pages'),('<Next>',1,'pages')):
            self.detail_canvas.bind(key,lambda e,a=amount,u=unit:self.scroll_catalog_detail(a,u))
        self.detail_name=ttk.Label(detail,text='',style='Experience.Detail.TLabel',wraplength=250,justify='left'); self.detail_name.pack(anchor='w',fill='x')
        self.detail_status=ttk.Label(detail,text='',style='Experience.Model.TLabel',wraplength=215); self.detail_status.pack(anchor='w',pady=(4,12),fill='x')
        self.detail_desc=ttk.Label(detail,text='',style='Experience.Card.TLabel',wraplength=215,justify='left'); self.detail_desc.pack(anchor='w',fill='x')
        self.example=ttk.Label(detail,text='',style='Experience.ComposerMuted.TLabel',wraplength=215,justify='left'); self.example.pack(anchor='w',pady=(12,6),fill='x')
        self.toggle=ttk.Button(detail,text='Ativar')
        self.launch=ttk.Button(detail,text='Abrir',style='Experience.Primary.TButton')
        self.favorite_button=ttk.Button(detail,text='Adicionar aos favoritos')
        self.catalog_hint=ttk.Label(detail,text='',style='Experience.Card.TLabel',wraplength=215); self.catalog_hint.pack(anchor='w',side='bottom',pady=(6,0),fill='x')
        detail.bind('<Configure>',self.resize_catalog_detail,add='+')
        detail.bind('<Configure>',lambda e:self.detail_canvas.configure(scrollregion=self.detail_canvas.bbox('all')),add='+')
        for control in (self.toggle,self.launch,self.favorite_button):
            control.bind('<FocusIn>',self.reveal_catalog_control,add='+')
        for control in (self.detail_canvas,detail,self.detail_name,self.detail_status,self.detail_desc,self.example,self.catalog_hint,self.toggle,self.launch,self.favorite_button):
            control.bind('<MouseWheel>',self.catalog_detail_wheel,add='+')
            control.bind('<Button-4>',lambda e:self.scroll_catalog_detail(-1,'units'),add='+')
            control.bind('<Button-5>',lambda e:self.scroll_catalog_detail(1,'units'),add='+')
    def scroll_catalog_detail(self,amount,unit):
        self.detail_canvas.yview_scroll(amount,unit)
        return 'break'
    def catalog_detail_wheel(self,event):
        if event.delta: return self.scroll_catalog_detail(-1 if event.delta>0 else 1,'units')
    def reveal_catalog_control(self,event):
        canvas=self.detail_canvas
        bounds=canvas.bbox('all')
        if not bounds: return
        height=bounds[3]-bounds[1]
        visible=canvas.winfo_height()
        if height<=visible or visible<=1: return
        top=canvas.canvasy(0)
        y=event.widget.winfo_y()
        bottom=y+event.widget.winfo_height()
        if y<top: canvas.yview_moveto(max(0,y/height))
        elif bottom>top+visible: canvas.yview_moveto(max(0,(bottom-visible)/height))
    def resize_catalog_filters(self,event):
        if event.width>1: self.layout_catalog_filters(event.width<540)
    def layout_catalog_filters(self,compact):
        if compact==self.catalog_filters_compact: return
        self.catalog_filters_compact=compact
        for column in range(4): self.catalog_choices.columnconfigure(column,weight=0)
        self.catalog_choices.columnconfigure(1,weight=1)
        self.goal_label.grid(row=0,column=0,sticky='w',padx=(0,6),pady=2)
        self.goalbox.grid(row=0,column=1,sticky='ew',pady=2)
        if compact:
            self.category_label.grid(row=1,column=0,sticky='w',padx=(0,6),pady=2)
            self.category_box.grid(row=1,column=1,sticky='ew',pady=2)
        else:
            self.catalog_choices.columnconfigure(3,weight=1)
            self.category_label.grid(row=0,column=2,sticky='w',padx=(12,6),pady=2)
            self.category_box.grid(row=0,column=3,sticky='ew',pady=2)
    def resize_catalog_detail(self,event):
        # Use the actual card width; preserve the initial wrapping while unmapped.
        if event.width <= 1: return
        width=max(120,min(420,event.width-28))
        for label in (self.detail_name,self.detail_status,self.detail_desc,self.example,self.catalog_hint):
            if int(label.cget('wraplength')) != width:
                label.configure(wraplength=width)
    def focus_catalog_search(self,_=None):
        self.search.focus_set()
        return 'break'
    def clear_filters(self):
        if hasattr(self,'goal'): self.goal.set('Todas')
        if hasattr(self,'catalog_scope'): self.catalog_scope.set('Todas')
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
            elif view=='chat': self.conversation.set_context(False)
        self.view=view
        active={'catalog':'Ferramentas','screen':'Tela','notes':'Anotações','meeting':'Reuniões'}.get(view,'Conversar')
        for label,button in self.nav_buttons.items(): button.configure(style='Experience.Active.TButton' if label==active else 'Experience.Nav.TButton')
    def open_search_result(self,result):
        if result.source=='Ferramentas': self.goal.set('Todas'); self.catalog_scope.set('Todas')
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
            window.title('Aeris · '+NAMES.get(name,name))
            polish_tool_window(window)
        if name in self.recent_tools: self.recent_tools.remove(name)
        self.recent_tools.insert(0,name); del self.recent_tools[12:]
        if self.catalog_scope.get()=='Recentes': self.refresh()
    def open_friendly(self,name):
        if not self.enabled(name): self.toggle_tool(name)
        if self.enabled(name): self.open_tool(name)
    def refresh(self,*_):
        old=self.listbox.curselection()
        selected=self.visible[old[0]].name if old and old[0]<len(self.visible) else None
        self.listbox.delete(0,'end')
        self.category_display.set(CATEGORIES.get(self.category.get(),'Todas'))
        rows=self.catalog_index.search(self.query.get(),self.category.get(),self.goal.get())
        favorites=self.settings.appearance.favorites; scope=self.catalog_scope.get()
        if scope=='Favoritas': rows=tuple(m for m in rows if m.name in favorites)
        elif scope=='Recentes':
            by_name={m.name:m for m in rows}; rows=tuple(by_name[n] for n in self.recent_tools if n in by_name)
        self.visible=rows
        for m in self.visible: self.listbox.insert('end',('★  ' if m.name in favorites else '    ')+NAMES.get(m.name,m.name)+'  ·  '+CATEGORIES.get(m.category,m.category))
        self.count.configure(text=f'{len(self.visible)} de {len(self.modules)} itens · '+scope)
        if self.visible:
            index=next((i for i,m in enumerate(self.visible) if m.name==selected),0)
            self.listbox.selection_set(index); self.listbox.activate(index); self.listbox.see(index)
        self.show_selected()
    def show_selected(self,*_):
        super().show_selected(*_)
        self.example.configure(text=''); self.favorite_button.pack_forget(); self.catalog_hint.configure(text='')
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
                self.detail_status.configure(text=CATEGORIES.get(m.category,m.category)+' · '+('Ativada' if self.enabled(m.name) else 'Ative ao abrir'))
                self.toggle.configure(style='Aeris.Stop.TButton')
            elif m.name=='Hub':
                self.detail_status.configure(text='Espaço de trabalho')
                self.launch.configure(text='Voltar à conversa',command=lambda:self.navigate('chat')); self.launch.pack(fill='x',pady=8)
            elif m.name=='Privacy': self.launch.configure(text='Abrir privacidade')
            elif m.name=='Spotlight': self.toggle.configure(style='TButton')
            if m.name in FAVORITES:
                self.favorite_button.configure(text='Remover dos favoritos' if m.name in self.settings.appearance.favorites else 'Adicionar aos favoritos',command=lambda n=m.name:self.toggle_favorite(n)); self.favorite_button.pack(fill='x',pady=4)
            self.catalog_hint.configure(text='Abrir não autoriza acessos sensíveis. Revise as permissões quando solicitadas.' if m.name in self.tool_buttons else '')
        elif self.catalog_scope.get()=='Favoritas': self.detail_desc.configure(text='Adicione uma ferramenta aos favoritos na aba Todas.')
        elif self.catalog_scope.get()=='Recentes': self.detail_desc.configure(text='As ferramentas abertas nesta sessão aparecem aqui.')
    def toggle_favorite(self,name):
        if name not in FAVORITES: return
        prefs=self.settings.appearance
        values=tuple(n for n in prefs.favorites if n!=name) if name in prefs.favorites else (*prefs.favorites,name)
        try: self.settings.set_appearance(replace(prefs,favorites=values))
        except OSError:
            self.catalog_hint.configure(text='Não foi possível salvar a preferência.'); return
        self.workspace_changed(); self.refresh()
    def open_privacy(self):
        super().open_privacy()
        if self.alive(self.privacy_window): polish_tool_window(self.privacy_window.window)
    def open_permissions(self):
        super().open_permissions()
        if self.alive(self.permissions_window): polish_tool_window(self.permissions_window.window)
    def permissions_changed(self):
        super().permissions_changed()
        if hasattr(self,'conversation'): self.conversation.permissions_changed()
    def clear_session(self):
        if not super().clear_session(): return False
        self.conversation.clear_workspace()
        self.recent_tools.clear(); self.refresh()
        return True
    def close(self):
        if self.conversation.dirty() and not messagebox.askyesno('Encerrar Aeris?', 'A conversa, captura, transcrição e rascunhos desta sessão serão descartados. Encerrar?',parent=self.root): return
        self.conversation.stop()
        super().close()

def main(configure=False):
    root=tk.Tk(); hub=ExperienceHub(root)
    root.after(500,hub.conversation.configure_ai if configure else hub.conversation.restore_ai)
    root.mainloop()
