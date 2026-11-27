"""Interface gráfica do Hub. Nenhum serviço residente ou acesso à rede."""
import tkinter as tk
from tkinter import ttk, messagebox
from aeris import __version__
from aeris.settings import Settings
from aeris.permissions import Permissions, SEARCH_CAPTURE, SEARCH_SNIPPETS, COPY_SNIPPETS, READ_CLIPBOARD, WRITE_CLIPBOARD, OPEN_BOOKMARK, CREATE_BACKUP, RESTORE_BACKUP, COPY_TRANSLATION, PLAY_VOICE, COPY_TEXT, TEXT_AI, COPY_EMAIL, PLAY_PRONOUNCE, COPY_AUTOFILL, COPY_EXPAND, BRIDGE_GRANTS, ROUTINE_GRANTS, WORKSPACE_OPEN, VERIFY_READ, METADATA_READ, DOCUMENTS_READ, ORGANIZER_SCAN, DROP_ADD, DROP_COPY, COMPARE_READ, LENS_READ, DATA_READ, DASHBOARD_READ, REPORT_READ, REPORT_COPY, COPILOT_RUN, CONTEXT_PREVIEW, MEETING_COPY
from aeris.theme import configure, apply_tree, WIND_CURVES
from aeris.scroll_area import scroll_area
from aeris.window_lifecycle import track_window
from aeris.registry import load_catalog, filter_catalog, Module

COLORS = {'air': '#F6FAF7', 'soft': '#DCEFE3', 'natural': '#8FC7A3',
          'forest': '#508D70', 'deep': '#285640', 'muted': '#CFDFD5'}

class Hub:
    def __init__(self, root: tk.Tk, settings=None):
        self.root = root
        self.modules = load_catalog()
        self.settings = settings if settings is not None else Settings()
        self.capture_store = self.snippets_store = None
        self.capture_window = self.snippets_window = self.search_window = None
        self.quick_panel = self.appearance_window = self.spotlight = None
        self.spotlight_hidden = False
        self.permissions_window = self.privacy_window = None
        self.vault_window = self.bookmarks_window = self.backup_window = None
        self.clipboard_window = self.clipboard_store = None
        self.translate_window = self.voice_window = self.text_window = self.email_window = self.pronounce_window = None
        self.autofill_window = None
        self.expand_window = self.expand_store = None
        self.bridge_window = None
        self.routine_window = self.routine_store = None
        self.workspace_window = self.workspace_store = None
        self.link_window = self.verify_window = self.metadata_window = self.health_window = self.documents_window = self.organizer_window = None
        self.drop_window = self.drop_store = self.compare_window = self.lens_window = None
        self.focus_window = self.focus_timer = None
        self.ideas_window = self.ideas_store = None
        self.timeline_window = self.timeline_store = None
        self.learn_window = self.learn_store = None
        self.research_window = self.research_store = None
        self.flashcards_window = self.flashcards_store = None
        self.accessibility_window = self.decision_window = self.copilot_window = None
        self.context_window = self.context_store = None
        self.interview_window = self.interview_store = None
        self.debug_window = None
        self.meeting_window = self.meeting_store = None
        self.data_window = self.dashboard_window = self.report_window = self.calculator_window = self.convert_window = None
        self.checklist_window = self.checklist_store = None
        self.reminder_window = self.reminder_store = self.reminder_alert = self.reminder_job = None
        self.autosave = self.autosave_job = None
        self.permissions = Permissions(self.permissions_changed)
        self.visible: tuple[Module, ...] = ()
        self.query = tk.StringVar(root)
        self.category = tk.StringVar(root, 'Todas')
        root.title(f'Project Aeris | {__version__}')
        root.geometry('1040x650')
        root.minsize(750, 500)
        root.configure(bg=COLORS['air'])
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('Aeris.TCombobox', padding=5)
        self.build()
        self.query.trace_add('write', self.refresh)
        self.category.trace_add('write', self.refresh)
        self.refresh()
        self.apply_appearance()
        root.protocol('WM_DELETE_WINDOW', self.close)
        if self.settings.warning:
            root.after_idle(lambda: messagebox.showwarning('Aeris', self.settings.warning, parent=root))
        root.bind('<Control-f>', lambda _: self.search.focus_set())

    def label(self, parent, text='', size=11, bg='air', fg='deep', **kwargs):
        return tk.Label(parent, text=text, font=('Segoe UI', size), bg=COLORS[bg],
                        fg=COLORS[fg], anchor='w', **kwargs)

    def build(self):
        side = tk.Frame(self.root, bg=COLORS['soft'], width=200)
        side.pack(side='left', fill='y')
        side.pack_propagate(False)
        logo = tk.Canvas(side, width=64, height=60, bg=COLORS['soft'], highlightthickness=0)
        logo._aeris_logo = True
        logo.pack(anchor='w', padx=20, pady=(12, 0))
        # Curvas aproximadas do símbolo oficial, desenhadas nativamente.
        for points in WIND_CURVES:
            logo.create_line(*points, smooth=True, width=3, fill=COLORS['forest'], capstyle=tk.ROUND)
        self.label(side, 'aeris.', 30, 'soft').pack(anchor='w', padx=20)
        self.label(side, 'Eficiência e Simplicidade.', 10, 'soft').pack(anchor='w', padx=20)
        self.label(side, 'by K&G Vision', 9, 'soft').pack(anchor='w', padx=20, pady=(2,6))
        self.label(side, '  Hub / Catálogo', 13, 'muted', pady=10).pack(fill='x', padx=12)
        self.label(side, 'FERRAMENTAS', 9, 'soft').pack(anchor='w', padx=20, pady=(5,3))
        self.tool_buttons = {}
        tool_frame=scroll_area(side)
        for col in range(2): tool_frame.columnconfigure(col,weight=1,uniform='tool')
        for i,name in enumerate(('Capture', 'Snippets', 'Search', 'Vault', 'Clipboard', 'Bookmarks', 'Backup', 'Translate', 'Voice', 'Text', 'Email', 'Pronounce', 'Autofill', 'Expand', 'Bridge', 'Routine', 'Workspace', 'Link', 'Verify', 'Metadata', 'Health', 'Documents', 'Organizer', 'Drop', 'Compare', 'Lens', 'Focus', 'Checklist', 'Reminder', 'Ideas', 'Timeline', 'Data', 'Dashboard', 'Report', 'Calculator', 'Convert', 'Learn', 'Research', 'Flashcards', 'Accessibility', 'Decision', 'Copilot', 'Context', 'Interview', 'Debug', 'Meeting')):
            b = ttk.Button(tool_frame, text=name, command=lambda n=name: self.open_tool(n))
            b.grid(row=i//2,column=i%2,sticky='ew',padx=1,pady=1)
            self.tool_buttons[name] = b
        self.spotlight_button = ttk.Button(side, command=self.toggle_spotlight_visibility)
        self.spotlight_button.pack(fill='x', padx=15, pady=1)
        self.quick_button = ttk.Button(side, text='Acesso rápido', command=self.toggle_quick_panel)
        self.quick_button.pack(fill='x', padx=15, pady=(5,3))
        ttk.Button(side, text='Configurações', command=self.open_appearance).pack(fill='x', padx=15, pady=1)
        ttk.Button(side, text='Privacidade', command=self.open_privacy).pack(fill='x', padx=15, pady=1)
        ttk.Button(side, text='Permissões', command=self.open_permissions).pack(fill='x', padx=15, pady=1)
        self.label(side, f'Prévia {__version__}', 9, 'soft').pack(side='bottom', anchor='w', padx=20, pady=8)
        tool_frame.master.master.pack_forget()
        tool_frame.master.master.pack(fill='both', expand=True, padx=4, before=self.spotlight_button)
        body = tk.Frame(self.root, bg=COLORS['air'])
        body.pack(fill='both', expand=True, padx=24, pady=22)
        self.label(body, 'Seu espaço, mais leve.', 25).pack(fill='x')
        self.label(body, 'Explore o catálogo de ferramentas do Aeris.', 11).pack(fill='x', pady=(3,16))
        filters = tk.Frame(body, bg=COLORS['air']); filters.pack(fill='x')
        self.search = tk.Entry(filters, textvariable=self.query, font=('Segoe UI', 12), relief='flat',
                               bg='white', fg=COLORS['deep'], highlightthickness=1, highlightbackground=COLORS['muted'])
        self.search.pack(side='left', fill='x', expand=True, ipady=7)
        ttk.Button(filters, text='Limpar', command=self.clear_filters).pack(side='right', padx=(8,0))
        self.search.bind('<Escape>', lambda _: self.clear_filters())
        self.search.bind('<Return>', self.focus_results)
        categories = ['Todas', *dict.fromkeys(m.category for m in self.modules)]
        ttk.Combobox(filters, textvariable=self.category, values=categories, state='readonly',
                     width=18, style='Aeris.TCombobox').pack(side='left', padx=(10,0))
        self.label(body, 'Filtrar por nome, descrição ou categoria · Ctrl+F', 9).pack(fill='x', pady=(4,12))
        self.count = self.label(body, '', 10); self.count.pack(fill='x', pady=(0,5))
        content = tk.Frame(body, bg=COLORS['air']); content.pack(fill='both', expand=True)
        list_frame = tk.Frame(content, bg=COLORS['air']); list_frame.pack(side='left', fill='both', expand=True)
        scroll = ttk.Scrollbar(list_frame); scroll.pack(side='right', fill='y')
        self.listbox = tk.Listbox(list_frame, font=('Segoe UI', 11), relief='flat', borderwidth=0,
                                  bg='white', fg=COLORS['deep'], selectbackground=COLORS['soft'],
                                  selectforeground=COLORS['deep'], activestyle='none', exportselection=False,
                                  yscrollcommand=scroll.set, width=27, highlightthickness=1,
                                  highlightbackground=COLORS['muted'])
        self.listbox.pack(fill='both', expand=True)
        scroll.configure(command=self.listbox.yview)
        self.listbox.bind('<<ListboxSelect>>', self.show_selected)
        self.listbox.bind('<Return>', self.open_selected)
        self.listbox.bind('<Double-Button-1>', self.open_selected)
        detail = tk.Frame(content, bg=COLORS['soft'], width=265)
        detail.pack(side='right', fill='y', padx=(12,0)); detail.pack_propagate(False)
        self.detail_name = self.label(detail, '', 19, 'soft', wraplength=230, justify='left')
        self.detail_name.pack(fill='x', padx=15, pady=(20,5))
        self.detail_status = self.label(detail, '', 10, 'soft', wraplength=230, justify='left')
        self.detail_status.pack(fill='x', padx=15, pady=(0,16))
        self.detail_desc = self.label(detail, '', 11, 'soft', wraplength=230, justify='left')
        self.detail_desc.pack(fill='x', padx=15)
        self.toggle = ttk.Button(detail)
        self.launch = ttk.Button(detail)
        self.label(body, 'Local por padrão · Sem conta ou coleta. Links abrem no navegador sob autorização.', 9).pack(fill='x', pady=(12,0))

    def clear_filters(self):
        self.query.set('')
        self.category.set('Todas')
        self.search.focus_set()
        return 'break'

    def focus_results(self, _=None):
        if self.visible:
            self.listbox.focus_set()
        return 'break'

    def open_selected(self, _=None):
        selection = self.listbox.curselection()
        if selection:
            self.show_selected()
            if self.launch.winfo_manager():
                self.launch.invoke()
        return 'break'

    def refresh(self, *_):
        selection = self.listbox.curselection()
        selected = self.visible[selection[0]].name if selection and selection[0] < len(self.visible) else None
        self.visible = filter_catalog(self.modules, self.query.get(), self.category.get())
        self.listbox.delete(0, tk.END)
        for module in self.visible:
            self.listbox.insert(tk.END, f'  {module.name}  ·  {module.category}')
        self.count.configure(text=f'{len(self.visible)} de {len(self.modules)} ferramentas no catálogo')
        if self.visible:
            index = next((i for i, module in enumerate(self.visible) if module.name == selected), 0)
            self.listbox.selection_set(index)
            self.listbox.activate(index)
            self.listbox.see(index)
        self.show_selected()

    def enabled(self,name):
        return getattr(self.settings,name.lower()+'_enabled',False)

    def active_tools(self):
        return [(n,lambda n=n:self.open_tool(n)) for n in ('Capture','Snippets','Search','Vault','Clipboard','Bookmarks','Backup','Translate','Voice','Text','Email','Pronounce','Autofill','Expand','Bridge','Routine','Workspace','Link','Verify','Metadata','Health','Documents','Organizer','Drop','Compare','Lens','Focus','Checklist','Reminder','Ideas','Timeline','Data','Dashboard','Report','Calculator','Convert','Learn','Research','Flashcards','Accessibility','Decision','Copilot','Context','Interview','Debug','Meeting') if self.enabled(n)]

    def quick_tools(self):
        prefs = self.settings.appearance
        tools = self.active_tools()
        favorites = prefs.favorites
        if self.enabled('Workspace') and self.workspace_store is not None and self.workspace_store.active is not None:
            return self.workspace_store.filter_tools(tools)
        if prefs.favorites_only:
            tools = [pair for pair in tools if pair[0] in favorites]
        return sorted(tools, key=lambda pair: pair[0] not in favorites)

    def workspace_changed(self):
        self.close_window('quick_panel')
        if self.spotlight: self.spotlight.dismiss()
        if self.alive(self.workspace_window): self.workspace_window.permissions_changed()

    def arm_autosave(self,module):
        from aeris.permissions import STORAGE_AUTO, STORAGE_SAVE
        from aeris.autosave import AutoSave
        from aeris.protected_storage import ProtectedStorage
        if self.autosave is None:
            self.autosave=AutoSave(ProtectedStorage(self.settings.path.parent),
                lambda: self.permissions.allowed(STORAGE_AUTO) and self.permissions.allowed(STORAGE_SAVE),
                lambda m: getattr(self,m.lower()+'_store') if self.enabled(m) else None)
        self.autosave.arm(module)
        self.schedule_autosave()

    def schedule_autosave(self):
        if self.autosave is not None and self.autosave.armed and self.autosave_job is None:
            self.autosave_job=self.root.after(10000,self.autosave_tick)

    def stop_autosave(self,module=None):
        if self.autosave is not None:
            if module is None: self.autosave.stop_all()
            else: self.autosave.stop(module)
        if self.autosave_job is not None and not (self.autosave and self.autosave.armed):
            self.root.after_cancel(self.autosave_job); self.autosave_job=None

    def autosave_tick(self):
        if self.autosave_job is not None:
            self.root.after_cancel(self.autosave_job)
        self.autosave_job=None
        failed=self.autosave.tick()
        self.schedule_autosave()
        if self.alive(self.privacy_window): self.privacy_window.refresh()
        if failed: messagebox.showwarning('Aeris Storage','Salvamento automático pausado: '+', '.join(failed)+'. Verifique as cópias em Privacidade.',parent=self.root)

    def permissions_changed(self):
        if self.autosave is not None and not self.autosave.allowed(): self.stop_autosave()
        if self.alive(self.meeting_window): self.meeting_window.permissions_changed()
        if self.context_store is not None and not self.permissions.allowed(CONTEXT_PREVIEW): self.context_store.revoke()
        if self.alive(self.context_window): self.context_window.permissions_changed()
        if self.alive(self.copilot_window): self.copilot_window.permissions_changed()
        if self.alive(self.report_window): self.report_window.permissions_changed()
        if self.alive(self.dashboard_window): self.dashboard_window.permissions_changed()
        if self.alive(self.data_window): self.data_window.permissions_changed()
        if self.drop_store is not None and not self.permissions.allowed(DROP_ADD): self.drop_store.clear()
        if self.alive(self.lens_window): self.lens_window.permissions_changed()
        if self.alive(self.compare_window): self.compare_window.permissions_changed()
        if self.alive(self.drop_window): self.drop_window.permissions_changed()
        if self.alive(self.permissions_window): self.permissions_window.refresh()
        if self.alive(self.privacy_window): self.privacy_window.refresh()
        self.invalidate_search()
        if self.alive(self.clipboard_window): self.clipboard_window.permissions_changed()
        if self.alive(self.bookmarks_window): self.bookmarks_window.permissions_changed()
        if self.alive(self.backup_window): self.backup_window.permissions_changed()
        if self.alive(self.translate_window): self.translate_window.permissions_changed()
        if self.alive(self.voice_window): self.voice_window.permissions_changed()
        if self.alive(self.text_window): self.text_window.permissions_changed()
        if self.alive(self.email_window): self.email_window.permissions_changed()
        if self.alive(self.pronounce_window): self.pronounce_window.permissions_changed()
        if self.alive(self.autofill_window): self.autofill_window.permissions_changed()

        if self.alive(self.expand_window): self.expand_window.permissions_changed()
        if self.alive(self.bridge_window): self.bridge_window.permissions_changed()
        if self.alive(self.routine_window): self.routine_window.permissions_changed()
        if self.alive(self.workspace_window): self.workspace_window.permissions_changed()

        if self.alive(self.verify_window): self.verify_window.permissions_changed()
        if self.alive(self.metadata_window): self.metadata_window.permissions_changed()
        if self.alive(self.documents_window): self.documents_window.permissions_changed()
        if self.alive(self.organizer_window): self.organizer_window.permissions_changed()

    def open_permissions(self):
        if self.alive(self.permissions_window): self.permissions_window.window.lift(); return
        from aeris.permissions_ui import PermissionsWindow
        self.permissions_window = PermissionsWindow(self)
        track_window(self,'permissions_window')
        apply_tree(self.permissions_window.window, self.settings.appearance.theme)

    def open_privacy(self):
        from aeris.privacy_ui import PrivacyWindow
        if self.alive(getattr(self, 'privacy_window', None)):
            self.privacy_window.refresh(); self.privacy_window.window.lift(); return
        self.privacy_window = PrivacyWindow(self)
        track_window(self,'privacy_window')
        apply_tree(self.privacy_window.window, self.settings.appearance.theme)

    def lock_protected(self):
        for w in (self.vault_window,self.bookmarks_window,self.autofill_window):
            if self.alive(w): w.force_lock()

    def clear_session(self):
        if not messagebox.askyesno('Limpar sessão?', 'Descartar dados temporários, conversas, capturas, transcrições, rascunhos e sessões de concentração, revogar acessos e bloquear cofres? Cópias protegidas em disco e clipboard do Windows serão preservados.', parent=self.root):
            return False
        self.stop_autosave()
        if self.alive(self.translate_window): self.translate_window.close(); self.translate_window=None
        if self.alive(self.voice_window): self.voice_window.close(); self.voice_window=None
        if self.alive(self.pronounce_window): self.pronounce_window.close(); self.pronounce_window=None
        self.close_window('text_window'); self.close_window('email_window'); self.close_window('expand_window'); self.close_window('bridge_window'); self.close_window('routine_window')
        if self.routine_store is not None: self.routine_store.clear(); self.routine_store=None
        self.close_window('workspace_window'); self.close_window('link_window'); self.close_window('verify_window'); self.close_window('metadata_window'); self.close_window('health_window'); self.close_window('documents_window'); self.close_window('organizer_window'); self.close_window('drop_window'); self.close_window('compare_window'); self.close_window('lens_window'); self.close_window('data_window'); self.close_window('dashboard_window'); self.close_window('report_window'); self.close_window('calculator_window'); self.close_window('convert_window'); self.close_window('accessibility_window'); self.close_window('decision_window'); self.close_window('copilot_window'); self.close_window('debug_window')
        self.close_window('focus_window'); self.focus_timer=None
        self.reset_reminders()
        self.reset_context()
        self.reset_interview()
        self.reset_meeting()
        self.reset_ideas()
        self.reset_timeline()
        self.reset_learn()
        self.reset_research()
        self.reset_flashcards()
        self.close_window('checklist_window')
        if self.checklist_store is not None: self.checklist_store.clear(); self.checklist_store=None
        if self.drop_store is not None: self.drop_store.clear(); self.drop_store=None
        if self.workspace_store is not None: self.workspace_store.clear(); self.workspace_store=None
        if self.expand_store is not None: self.expand_store.clear(); self.expand_store=None
        for attr in ('search_window','capture_window','snippets_window','clipboard_window'):
            self.close_window(attr)
        for attr in ('capture_store','snippets_store','clipboard_store'):
            store = getattr(self,attr)
            if store is not None: store.clear()
            setattr(self,attr,None)
        self.lock_protected()
        self.close_window('backup_window')
        self.query.set('')
        if self.alive(self.privacy_window): self.privacy_window.reset_mask()
        self.permissions.revoke_all()
        if self.alive(self.privacy_window): self.privacy_window.refresh()
        self.close_window('quick_panel')
        if self.spotlight: self.spotlight.dismiss()
        return True

    @staticmethod
    def alive(obj):
        return obj is not None and bool(obj.window.winfo_exists())

    def show_selected(self, _=None):
        self.toggle.pack_forget(); self.launch.pack_forget()
        for name,button in self.tool_buttons.items():
            button.configure(state='normal' if self.enabled(name) else 'disabled')
        selection=self.listbox.curselection()
        if not selection:
            self.detail_name.configure(text='Nenhum resultado'); self.detail_status.configure(text='')
            self.detail_desc.configure(text='Tente outro termo ou categoria.'); return
        module=self.visible[selection[0]]; name=module.name
        self.detail_name.configure(text=name)
        self.detail_status.configure(text=f'{module.category} · '+('Protótipo disponível' if module.status=='prototype' else 'Planejado · não implementado'))
        self.detail_desc.configure(text=module.description)
        if name in self.tool_buttons:
            enabled=self.enabled(name)
            self.detail_status.configure(text=f'{module.category} · Protótipo '+('ativado' if enabled else 'desativado'))
            self.toggle.configure(text='Desativar' if enabled else 'Ativar',command=lambda:self.toggle_tool(name)); self.toggle.pack(fill='x',padx=15,pady=(18,4))
            if enabled:
                self.launch.configure(text='Abrir '+name,command=lambda:self.open_tool(name)); self.launch.pack(fill='x',padx=15,pady=4)
        elif name=='Privacy':
            self.launch.configure(text='Abrir Privacy',command=self.open_privacy); self.launch.pack(fill='x',padx=15,pady=4)
        elif name=='Permissions':
            self.launch.configure(text='Gerenciar permissões',command=self.open_permissions); self.launch.pack(fill='x',padx=15,pady=4)
        elif name=='Spotlight':
            self.detail_status.configure(text='Core · Protótipo '+('ativado' if self.settings.appearance.floating_enabled else 'desativado'))
            self.toggle.configure(text='Configurar',command=self.open_appearance); self.toggle.pack(fill='x',padx=15,pady=(18,4))
            if self.settings.appearance.floating_enabled:
                self.launch.configure(text='Mostrar / ocultar ícone',command=self.toggle_spotlight_visibility); self.launch.pack(fill='x',padx=15,pady=4)

    def close_window(self,attr):
        obj=getattr(self,attr)
        if self.alive(obj): obj.window.destroy()
        setattr(self,attr,None)

    def reset_learn(self):
        self.close_window('learn_window')
        if self.learn_store is not None: self.learn_store.clear(); self.learn_store=None

    def reset_research(self):
        self.close_window('research_window')
        if self.research_store is not None: self.research_store.clear(); self.research_store=None

    def reset_flashcards(self):
        self.close_window('flashcards_window')
        if self.flashcards_store is not None: self.flashcards_store.clear(); self.flashcards_store=None

    def reset_timeline(self):
        self.close_window('timeline_window')
        if self.timeline_store is not None: self.timeline_store.clear(); self.timeline_store=None

    def reset_meeting(self):
        self.close_window('meeting_window')
        if self.meeting_store is not None: self.meeting_store.clear(); self.meeting_store=None

    def reset_interview(self):
        self.close_window('interview_window')
        if self.interview_store is not None: self.interview_store.clear(); self.interview_store=None

    def reset_context(self):
        self.close_window('context_window')
        if self.context_store is not None: self.context_store.clear(); self.context_store=None

    def reset_ideas(self):
        self.close_window('ideas_window')
        if self.ideas_store is not None: self.ideas_store.clear(); self.ideas_store=None

    def cancel_reminder_job(self):
        if self.reminder_job is not None:
            self.root.after_cancel(self.reminder_job)
            self.reminder_job = None

    def reset_reminders(self):
        self.cancel_reminder_job()
        self.close_window('reminder_window'); self.close_window('reminder_alert')
        if self.reminder_store is not None: self.reminder_store.clear(); self.reminder_store=None

    def schedule_reminders(self):
        self.cancel_reminder_job()
        if self.reminder_store is None or not self.enabled('Reminder'): return
        delay=self.reminder_store.next_delay_ms()
        if delay is not None: self.reminder_job=self.root.after(delay,self.poll_reminders)

    def poll_reminders(self):
        self.cancel_reminder_job()
        if self.reminder_store is None or not self.enabled('Reminder'): return
        due=self.reminder_store.collect_due()
        if due and self.alive(self.reminder_window): self.reminder_window.render()
        count=sum(r.alert for r in due)
        if count:
            from aeris.reminder_ui import ReminderAlert
            if self.alive(self.reminder_alert): self.reminder_alert.update_count(count)
            else:
                self.reminder_alert=ReminderAlert(self,count)
                track_window(self,'reminder_alert')
                apply_tree(self.reminder_alert.window,self.settings.appearance.theme)
        self.schedule_reminders()

    def toggle_tool(self,name):
        was_enabled=self.enabled(name)
        self._toggle_tool(name)
        if was_enabled and not self.enabled(name): self.stop_autosave(name)
        if self.enabled(name) != was_enabled:
            self.workspace_changed()
            if self.alive(self.copilot_window): self.copilot_window.invalidate()
        if was_enabled and not self.enabled(name) and name in ('Bridge','Capture','Snippets','Expand','Text','Translate','Email'):
            self.close_window('bridge_window')
            for capability in BRIDGE_GRANTS: self.permissions.set(capability,False)
        if was_enabled and not self.enabled(name) and name in ('Routine','Bridge','Expand','Text','Translate','Email','Capture'):
            self.close_window('routine_window')
            for capability in ROUTINE_GRANTS: self.permissions.set(capability,False)

    def _toggle_tool(self,name):
        if name not in self.tool_buttons: return
        enabled=not self.enabled(name)
        if name=='Flashcards':
            if not enabled and (bool(self.flashcards_store and self.flashcards_store.list()) or self.alive(self.flashcards_window)) and not messagebox.askyesno('Desativar Flashcards?', 'Descartar cartões e rascunhos da sessão?', parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled: self.reset_flashcards()
            if self.alive(self.privacy_window): self.privacy_window.refresh()
            self.show_selected(); return
        if name=='Research':
            if not enabled and (bool(self.research_store and self.research_store.list()) or self.alive(self.research_window)) and not messagebox.askyesno('Desativar Research?', 'Descartar referências e rascunhos da sessão?', parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled: self.reset_research()
            if self.alive(self.privacy_window): self.privacy_window.refresh()
            self.show_selected(); return
        if name=='Learn':
            if not enabled and (bool(self.learn_store and self.learn_store.list()) or self.alive(self.learn_window)) and not messagebox.askyesno('Desativar Learn?', 'Descartar trilhas de estudo e tópicos da sessão?', parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled: self.reset_learn()
            if self.alive(self.privacy_window): self.privacy_window.refresh()
            self.show_selected(); return
        if name=='Timeline':
            if not enabled and (bool(self.timeline_store and self.timeline_store.list()) or self.alive(self.timeline_window)) and not messagebox.askyesno('Desativar Timeline?', 'Descartar registros da linha do tempo e rascunhos da sessão?', parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled: self.reset_timeline()
            if self.alive(self.privacy_window): self.privacy_window.refresh()
            self.show_selected(); return
        if name=='Ideas':
            if not enabled and (bool(self.ideas_store and self.ideas_store.list()) or self.alive(self.ideas_window)) and not messagebox.askyesno('Desativar Ideas?', 'Descartar ideias e rascunhos da sessão?', parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled: self.reset_ideas()
            if self.alive(self.privacy_window): self.privacy_window.refresh()
            self.show_selected(); return
        if name=='Reminder':
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled: self.reset_reminders()
            if self.alive(self.privacy_window): self.privacy_window.refresh()
            self.show_selected(); return
        if name=='Checklist':
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.close_window('checklist_window')
                if self.checklist_store is not None: self.checklist_store.clear(); self.checklist_store=None
            if self.alive(self.privacy_window): self.privacy_window.refresh()
            self.show_selected(); return
        if name=='Focus':
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.close_window('focus_window'); self.focus_timer=None
            self.show_selected(); return
        if name=='Lens':
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.close_window('lens_window'); self.permissions.set(LENS_READ,False)
            self.show_selected(); return
        if name=='Compare':
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.close_window('compare_window'); self.permissions.set(COMPARE_READ,False)
            self.show_selected(); return
        if name=='Drop':
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.close_window('drop_window')
                if self.drop_store is not None: self.drop_store.clear(); self.drop_store=None
                self.permissions.set(DROP_ADD,False); self.permissions.set(DROP_COPY,False)
            self.show_selected(); return
        if name=='Debug':
            if not enabled and self.alive(self.debug_window) and self.debug_window.dirty() and not messagebox.askyesno('Desativar Debug?', 'Descartar código e diagnóstico?',parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled: self.close_window('debug_window')
            self.show_selected(); return
        if name=='Meeting':
            if not enabled and (bool(self.meeting_store and self.meeting_store.list()) or (self.alive(self.meeting_window) and self.meeting_window.dirty())) and not messagebox.askyesno('Desativar Meeting?', 'Descartar reuniões e rascunhos?',parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled: self.reset_meeting(); self.permissions.set(MEETING_COPY,False)
            if self.alive(self.privacy_window): self.privacy_window.refresh()
            self.show_selected(); return
        if name=='Interview':
            if not enabled and (bool(self.interview_store and self.interview_store.list()) or (self.alive(self.interview_window) and self.interview_window.dirty())) and not messagebox.askyesno('Desativar Interview?', 'Descartar respostas e rascunhos?',parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled: self.reset_interview()
            if self.alive(self.privacy_window): self.privacy_window.refresh()
            self.show_selected(); return
        if name=='Context':
            if not enabled and (bool(self.context_store and self.context_store.list()) or self.alive(self.context_window)) and not messagebox.askyesno('Desativar Context?', 'Descartar registros e rascunhos?',parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.reset_context(); self.permissions.set(CONTEXT_PREVIEW,False)
            if self.alive(self.privacy_window): self.privacy_window.refresh()
            self.show_selected(); return
        if name=='Copilot':
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.close_window('copilot_window'); self.permissions.set(COPILOT_RUN,False)
                from aeris.permissions import COMPANION_CHAT, COMPANION_MIC, COMPANION_SPEAK
                for cap in (COMPANION_CHAT, COMPANION_MIC, COMPANION_SPEAK): self.permissions.set(cap,False)
            self.show_selected(); return
        if name=='Decision':
            if not enabled and self.alive(self.decision_window) and self.decision_window.dirty() and not messagebox.askyesno('Desativar Decision?', 'Descartar matriz da sessão?', parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled: self.close_window('decision_window')
            self.show_selected(); return
        if name=='Accessibility':
            if not enabled and self.alive(self.accessibility_window) and self.accessibility_window.dirty() and not messagebox.askyesno('Desativar Accessibility?', 'Descartar texto da sessão?', parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled: self.close_window('accessibility_window')
            self.show_selected(); return
        if name=='Convert':
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled: self.close_window('convert_window')
            self.show_selected(); return
        if name=='Calculator':
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled: self.close_window('calculator_window')
            self.show_selected(); return
        if name=='Report':
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.close_window('report_window'); self.permissions.set(REPORT_READ,False); self.permissions.set(REPORT_COPY,False)
            self.show_selected(); return
        if name=='Dashboard':
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.close_window('dashboard_window'); self.permissions.set(DASHBOARD_READ,False)
            self.show_selected(); return
        if name=='Data':
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.close_window('data_window'); self.permissions.set(DATA_READ,False)
            self.show_selected(); return
        if name=='Organizer':
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.close_window('organizer_window'); self.permissions.set(ORGANIZER_SCAN,False)
            self.show_selected(); return
        if name=='Documents':
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.close_window('documents_window'); self.permissions.set(DOCUMENTS_READ,False)
            self.show_selected(); return
        if name=='Health':
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled: self.close_window('health_window')
            self.show_selected(); return
        if name=='Metadata':
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.close_window('metadata_window'); self.permissions.set(METADATA_READ,False)
            self.show_selected(); return
        if name=='Verify':
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.close_window('verify_window'); self.permissions.set(VERIFY_READ,False)
            self.show_selected(); return
        if name=='Link':
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled: self.close_window('link_window')
            self.show_selected(); return
        if name=='Workspace':
            if not enabled and not messagebox.askyesno('Desativar Workspace?', 'Descartar ambientes e links da sessão?',parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.close_window('workspace_window')
                if self.workspace_store is not None: self.workspace_store.clear(); self.workspace_store=None
                self.permissions.set(WORKSPACE_OPEN,False)
            self.workspace_changed(); self.show_selected(); return
        if name=='Routine':
            if not enabled and not messagebox.askyesno('Desativar Routine?', 'Descartar rotinas e textos da sessão?',parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.close_window('routine_window')
                if self.routine_store is not None: self.routine_store.clear(); self.routine_store=None
            self.close_window('quick_panel')
            if self.spotlight: self.spotlight.dismiss()
            self.show_selected(); return
        if name=='Bridge':
            if not enabled and not messagebox.askyesno('Desativar Bridge?', 'Descartar texto e prévia?',parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled: self.close_window('bridge_window')
            self.close_window('quick_panel')
            if self.spotlight: self.spotlight.dismiss()
            self.show_selected(); return
        if name=='Expand':
            if not enabled and not messagebox.askyesno('Desativar Expand?', 'Descartar regras e textos da sessão?',parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.close_window('expand_window')
                if self.expand_store is not None: self.expand_store.clear(); self.expand_store=None
                self.permissions.set(COPY_EXPAND,False)
            self.close_window('quick_panel')
            if self.spotlight: self.spotlight.dismiss()
            self.show_selected(); return
        if name=='Autofill':
            if not enabled and not messagebox.askyesno('Desativar Autofill?', 'Bloquear perfis e descartar rascunhos? Perfis salvos serão preservados.',parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.permissions.set(COPY_AUTOFILL,False)
                if self.alive(self.autofill_window): self.autofill_window.force_lock(); self.close_window('autofill_window')
            self.close_window('quick_panel')
            if self.spotlight: self.spotlight.dismiss()
            self.show_selected(); return
        if name=='Email':
            if not enabled and not messagebox.askyesno('Desativar Email?', 'Descartar rascunho da sessão?',parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.close_window('email_window'); self.permissions.set(COPY_EMAIL,False)
            self.close_window('quick_panel')
            if self.spotlight: self.spotlight.dismiss()
            self.show_selected(); return
        if name=='Text':
            if not enabled and not messagebox.askyesno('Desativar Text?', 'Descartar textos da sessão?',parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.close_window('text_window'); self.permissions.set(COPY_TEXT,False); self.permissions.set(TEXT_AI,False)
            self.close_window('quick_panel')
            if self.spotlight: self.spotlight.dismiss()
            self.show_selected(); return
        if name=='Pronounce':
            if not enabled and not messagebox.askyesno('Desativar Pronounce?', 'Parar exercício e descartar texto?',parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                if self.alive(self.pronounce_window): self.pronounce_window.close(); self.pronounce_window=None
                self.permissions.set(PLAY_PRONOUNCE,False)
            self.close_window('quick_panel')
            if self.spotlight: self.spotlight.dismiss()
            self.show_selected(); return
        if name=='Voice':
            if not enabled and not messagebox.askyesno('Desativar Voice?', 'Parar a leitura e descartar o texto?',parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                if self.alive(self.voice_window): self.voice_window.close(); self.voice_window=None
                self.permissions.set(PLAY_VOICE,False)
            self.close_window('quick_panel')
            if self.spotlight: self.spotlight.dismiss()
            self.show_selected(); return
        if name=='Translate':
            if not enabled and not messagebox.askyesno('Desativar Translate?', 'Descartar os textos da tradução?',parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                if self.alive(self.translate_window): self.translate_window.close(); self.translate_window=None
                self.permissions.set(COPY_TRANSLATION,False)
            self.close_window('quick_panel')
            if self.spotlight: self.spotlight.dismiss()
            self.show_selected(); return
        if name=='Backup':
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.permissions.set(CREATE_BACKUP,False); self.permissions.set(RESTORE_BACKUP,False)
                self.close_window('backup_window')
            self.close_window('quick_panel')
            if self.spotlight: self.spotlight.dismiss()
            self.show_selected(); return
        if name=='Bookmarks':
            if not enabled and not messagebox.askyesno('Desativar Bookmarks?', 'Bloquear links e descartar rascunhos? Registros salvos serão preservados.', parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled:
                self.permissions.set(OPEN_BOOKMARK,False)
                if self.alive(self.bookmarks_window): self.bookmarks_window.force_lock(); self.close_window('bookmarks_window')
            self.close_window('quick_panel')
            if self.spotlight: self.spotlight.dismiss()
            self.show_selected(); return
        if name=='Vault':
            if not enabled and not messagebox.askyesno('Desativar Vault?', 'Bloquear o cofre e descartar rascunhos? Registros salvos serão preservados.', parent=self.root): return
            try: self.settings.set_module(name,enabled)
            except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
            if not enabled and self.alive(self.vault_window): self.vault_window.force_lock(); self.close_window('vault_window')
            self.close_window('quick_panel')
            if self.spotlight: self.spotlight.dismiss()
            self.show_selected(); return
        if not enabled and name!='Search' and not messagebox.askyesno('Desativar '+name+'?','Textos e edições da sessão serão descartados. Cópias anteriores no clipboard podem permanecer.',parent=self.root): return
        try: self.settings.set_module(name,enabled)
        except OSError: messagebox.showerror('Aeris','Não foi possível salvar preferência.',parent=self.root); return
        # Close search before clearing data to remove results and previews.
        self.close_window('search_window'); self.close_window('quick_panel')
        if self.spotlight: self.spotlight.dismiss()
        if not enabled:
            for capability in {'Capture': (SEARCH_CAPTURE,), 'Snippets': (SEARCH_SNIPPETS, COPY_SNIPPETS), 'Search': (SEARCH_CAPTURE, SEARCH_SNIPPETS), 'Clipboard': (READ_CLIPBOARD, WRITE_CLIPBOARD)}[name]:
                self.permissions.set(capability, False)
        if not enabled and name!='Search':
            key=name.lower(); self.close_window(key+'_window')
            store=getattr(self,key+'_store')
            if store: store.clear()
            setattr(self,key+'_store',None)
        self.show_selected()

    def open_tool(self,name):
        if name not in self.tool_buttons or not self.enabled(name): return
        attr=name.lower()+'_window'
        if self.alive(getattr(self,attr)):
            self._open_tool(name); return
        self._open_tool(name)
        if self.alive(getattr(self,attr)): track_window(self,attr)

    def _open_tool(self,name):
        if name not in self.tool_buttons or not self.enabled(name): return
        attr=name.lower()+'_window'; obj=getattr(self,attr)
        if self.alive(obj): obj.window.lift(); obj.window.focus_set(); return
        if name=='Debug':
            from aeris.debug_ui import DebugWindow
            self.debug_window=DebugWindow(self)
            apply_tree(self.debug_window.window,self.settings.appearance.theme); return
        if name=='Meeting':
            from aeris.meeting import MeetingStore
            from aeris.meeting_ui import MeetingWindow
            if self.meeting_store is None: self.meeting_store=MeetingStore()
            self.meeting_window=MeetingWindow(self)
            apply_tree(self.meeting_window.window,self.settings.appearance.theme); return
        if name=='Interview':
            from aeris.interview import InterviewStore
            from aeris.interview_ui import InterviewWindow
            if self.interview_store is None: self.interview_store=InterviewStore()
            self.interview_window=InterviewWindow(self)
            apply_tree(self.interview_window.window,self.settings.appearance.theme); return
        if name=='Context':
            from aeris.context import ContextStore
            from aeris.context_ui import ContextWindow
            if self.context_store is None: self.context_store=ContextStore(self.permissions)
            self.context_window=ContextWindow(self)
            apply_tree(self.context_window.window,self.settings.appearance.theme); return
        if name=='Copilot':
            from aeris.copilot_ui import CopilotWindow
            self.copilot_window=CopilotWindow(self)
            apply_tree(self.copilot_window.window,self.settings.appearance.theme); return
        if name=='Decision':
            from aeris.decision_ui import DecisionWindow
            self.decision_window=DecisionWindow(self)
            apply_tree(self.decision_window.window,self.settings.appearance.theme); return
        if name=='Accessibility':
            from aeris.accessibility_ui import AccessibilityWindow
            self.accessibility_window=AccessibilityWindow(self)
            apply_tree(self.accessibility_window.window,self.settings.appearance.theme); return
        if name=='Flashcards':
            from aeris.flashcards import FlashcardsStore
            from aeris.flashcards_ui import FlashcardsWindow
            if self.flashcards_store is None: self.flashcards_store=FlashcardsStore()
            self.flashcards_window=FlashcardsWindow(self)
            apply_tree(self.flashcards_window.window,self.settings.appearance.theme); return
        if name=='Research':
            from aeris.research import ResearchStore
            from aeris.research_ui import ResearchWindow
            if self.research_store is None: self.research_store=ResearchStore()
            self.research_window=ResearchWindow(self)
            apply_tree(self.research_window.window,self.settings.appearance.theme); return
        if name=='Learn':
            from aeris.learn import LearnStore
            from aeris.learn_ui import LearnWindow
            if self.learn_store is None: self.learn_store=LearnStore()
            self.learn_window=LearnWindow(self)
            apply_tree(self.learn_window.window,self.settings.appearance.theme); return
        if name=='Timeline':
            from aeris.timeline import TimelineStore
            from aeris.timeline_ui import TimelineWindow
            if self.timeline_store is None: self.timeline_store=TimelineStore()
            self.timeline_window=TimelineWindow(self)
            apply_tree(self.timeline_window.window,self.settings.appearance.theme); return
        if name=='Ideas':
            from aeris.ideas import IdeasStore
            from aeris.ideas_ui import IdeasWindow
            if self.ideas_store is None: self.ideas_store=IdeasStore()
            self.ideas_window=IdeasWindow(self)
            apply_tree(self.ideas_window.window,self.settings.appearance.theme); return
        if name=='Reminder':
            from aeris.reminder import ReminderStore
            from aeris.reminder_ui import ReminderWindow
            if self.reminder_store is None: self.reminder_store=ReminderStore()
            self.reminder_window=ReminderWindow(self)
            apply_tree(self.reminder_window.window,self.settings.appearance.theme); self.poll_reminders(); return
        if name=='Checklist':
            from aeris.checklist import ChecklistStore
            from aeris.checklist_ui import ChecklistWindow
            if self.checklist_store is None: self.checklist_store=ChecklistStore()
            self.checklist_window=ChecklistWindow(self)
            apply_tree(self.checklist_window.window,self.settings.appearance.theme); return
        if name=='Focus':
            from aeris.focus import FocusTimer
            from aeris.focus_ui import FocusWindow
            if self.focus_timer is None: self.focus_timer=FocusTimer()
            self.focus_window=FocusWindow(self)
            apply_tree(self.focus_window.window,self.settings.appearance.theme); return
        if name=='Lens':
            from aeris.lens_ui import LensWindow
            self.lens_window=LensWindow(self)
            apply_tree(self.lens_window.window,self.settings.appearance.theme); return
        if name=='Compare':
            from aeris.compare_ui import CompareWindow
            self.compare_window=CompareWindow(self)
            apply_tree(self.compare_window.window,self.settings.appearance.theme); return
        if name=='Drop':
            from aeris.drop import DropStore
            from aeris.drop_ui import DropWindow
            if self.drop_store is None: self.drop_store=DropStore()
            self.drop_window=DropWindow(self)
            apply_tree(self.drop_window.window,self.settings.appearance.theme); return
        if name=='Convert':
            from aeris.convert_ui import ConvertWindow
            self.convert_window=ConvertWindow(self)
            apply_tree(self.convert_window.window,self.settings.appearance.theme); return
        if name=='Calculator':
            from aeris.calculator_ui import CalculatorWindow
            self.calculator_window=CalculatorWindow(self)
            apply_tree(self.calculator_window.window,self.settings.appearance.theme); return
        if name=='Report':
            from aeris.report_ui import ReportWindow
            self.report_window=ReportWindow(self)
            apply_tree(self.report_window.window,self.settings.appearance.theme); return
        if name=='Dashboard':
            from aeris.dashboard_ui import DashboardWindow
            self.dashboard_window=DashboardWindow(self)
            apply_tree(self.dashboard_window.window,self.settings.appearance.theme); return
        if name=='Data':
            from aeris.data_ui import DataWindow
            self.data_window=DataWindow(self)
            apply_tree(self.data_window.window,self.settings.appearance.theme); return
        if name=='Organizer':
            from aeris.organizer_ui import OrganizerWindow
            self.organizer_window=OrganizerWindow(self)
            apply_tree(self.organizer_window.window,self.settings.appearance.theme); return
        if name=='Documents':
            from aeris.documents_ui import DocumentsWindow
            self.documents_window=DocumentsWindow(self)
            apply_tree(self.documents_window.window,self.settings.appearance.theme); return
        if name=='Health':
            from aeris.health_ui import HealthWindow
            self.health_window=HealthWindow(self)
            apply_tree(self.health_window.window,self.settings.appearance.theme); return
        if name=='Metadata':
            from aeris.metadata_ui import MetadataWindow
            self.metadata_window=MetadataWindow(self)
            apply_tree(self.metadata_window.window,self.settings.appearance.theme); return
        if name=='Verify':
            from aeris.verify_ui import VerifyWindow
            self.verify_window=VerifyWindow(self)
            apply_tree(self.verify_window.window,self.settings.appearance.theme); return
        if name=='Link':
            from aeris.link_ui import LinkWindow
            self.link_window=LinkWindow(self)
            apply_tree(self.link_window.window,self.settings.appearance.theme); return
        if name=='Workspace':
            from aeris.workspace import WorkspaceStore
            from aeris.workspace_ui import WorkspaceWindow
            if self.workspace_store is None: self.workspace_store=WorkspaceStore()
            self.workspace_window=WorkspaceWindow(self,self.workspace_store)
            apply_tree(self.workspace_window.window,self.settings.appearance.theme); return
        if name=='Routine':
            from aeris.routine import RoutineStore
            from aeris.routine_ui import RoutineWindow
            if self.routine_store is None: self.routine_store=RoutineStore()
            self.routine_window=RoutineWindow(self,self.routine_store)
            apply_tree(self.routine_window.window,self.settings.appearance.theme); return
        if name=='Bridge':
            from aeris.bridge_ui import BridgeWindow
            self.bridge_window=BridgeWindow(self)
            apply_tree(self.bridge_window.window,self.settings.appearance.theme); return
        if name=='Expand':
            from aeris.expand import ExpandStore
            from aeris.expand_ui import ExpandWindow
            if self.expand_store is None: self.expand_store=ExpandStore()
            self.expand_window=ExpandWindow(self,self.expand_store)
            apply_tree(self.expand_window.window,self.settings.appearance.theme); return
        if name=='Autofill':
            from aeris.autofill import ProfileStore
            from aeris.autofill_ui import AutofillWindow
            try: store=ProfileStore(self.settings.path.parent/'autofill.bin',self.permissions)
            except OSError: messagebox.showinfo('Autofill','Perfis protegidos disponíveis somente no Windows.',parent=self.root); return
            self.autofill_window=AutofillWindow(self,store)
            apply_tree(self.autofill_window.window,self.settings.appearance.theme); return
        if name=='Email':
            from aeris.email_ui import EmailWindow
            self.email_window=EmailWindow(self)
            apply_tree(self.email_window.window,self.settings.appearance.theme); return
        if name=='Text':
            from aeris.text_ui import TextWindow
            self.text_window=TextWindow(self)
            apply_tree(self.text_window.window,self.settings.appearance.theme); return
        if name=='Pronounce':
            from aeris.pronounce_ui import PronounceWindow
            self.pronounce_window=PronounceWindow(self)
            apply_tree(self.pronounce_window.window,self.settings.appearance.theme); return
        if name=='Voice':
            from aeris.voice_ui import VoiceWindow
            self.voice_window=VoiceWindow(self)
            apply_tree(self.voice_window.window,self.settings.appearance.theme); return
        if name=='Translate':
            from aeris.translate_ui import TranslateWindow
            self.translate_window=TranslateWindow(self)
            apply_tree(self.translate_window.window,self.settings.appearance.theme); return
        if name=='Backup':
            from aeris.backup_ui import BackupWindow
            self.backup_window=BackupWindow(self)
            apply_tree(self.backup_window.window,self.settings.appearance.theme); return
        if name=='Vault':
            from aeris.vault import Vault
            from aeris.vault_ui import VaultWindow
            try: vault=Vault(self.settings.path.parent/'vault.bin')
            except OSError: messagebox.showinfo('Vault','O cofre criptografado está disponível somente no Windows.',parent=self.root); return
            self.vault_window=VaultWindow(self,vault)
            apply_tree(self.vault_window.window,self.settings.appearance.theme); return
        if name=='Bookmarks':
            from aeris.bookmarks import BookmarkStore
            from aeris.bookmarks_ui import BookmarksWindow
            try: store=BookmarkStore(self.settings.path.parent/'bookmarks.bin', self.permissions)
            except OSError: messagebox.showinfo('Bookmarks','Links protegidos disponíveis somente no Windows.',parent=self.root); return
            self.bookmarks_window=BookmarksWindow(self,store)
            apply_tree(self.bookmarks_window.window,self.settings.appearance.theme); return
        if name=='Clipboard':
            from aeris.clipboard import ClipboardStore
            from aeris.clipboard_ui import ClipboardWindow
            if self.clipboard_store is None: self.clipboard_store=ClipboardStore(self.permissions)
            self.clipboard_window=ClipboardWindow(self,self.clipboard_store)
            apply_tree(self.clipboard_window.window,self.settings.appearance.theme); return
        if name=='Search':
            from aeris.search_ui import SearchWindow
            self.search_window=SearchWindow(self); apply_tree(self.search_window.window, self.settings.appearance.theme); return
        if name=='Capture':
            from aeris.capture import CaptureStore,CaptureWindow
            if self.capture_store is None: self.capture_store=CaptureStore(self.invalidate_search)
            self.capture_window=CaptureWindow(self.root,self.capture_store)
        else:
            from aeris.snippets import SnippetStore
            from aeris.snippets_ui import SnippetsWindow
            if self.snippets_store is None: self.snippets_store=SnippetStore(self.invalidate_search)
            self.snippets_window=SnippetsWindow(self.root,self.snippets_store,self.permissions)
        apply_tree(getattr(self,attr).window, self.settings.appearance.theme)

    def open_capture(self): self.open_tool('Capture')
    def open_snippets(self): self.open_tool('Snippets')
    def open_search(self): self.open_tool('Search')
    def invalidate_search(self):
        if self.alive(self.search_window): self.search_window.refresh()

    def open_search_result(self,result):
        if not self.enabled('Search'): return False
        if result.source=='Ferramentas':
            self.category.set('Todas'); self.query.set(result.title)
            for idx,m in enumerate(self.visible):
                if m.id==result.id:
                    self.listbox.selection_clear(0,'end'); self.listbox.selection_set(idx); self.listbox.see(idx); self.show_selected(); self.root.deiconify(); self.root.lift(); return True
            return False
        if result.source not in ('Capture','Snippets') or not self.enabled(result.source): return False
        if not self.permissions.allowed({'Capture':SEARCH_CAPTURE,'Snippets':SEARCH_SNIPPETS}[result.source]): return False
        key=result.source.lower(); store=getattr(self,key+'_store')
        if store is None: return False
        try: item=store.get(result.id)
        except KeyError: return False
        if (item.title,item.body,getattr(item,'category','Anotação'))!=(result.title,result.body,result.category): return False
        self.open_tool(result.source); editor=getattr(self,key+'_window')
        if not self.alive(editor): return False
        if editor.current!=item.id:
            before=(editor.current,editor.values())
            if not editor.allow_discard(): return False
            if not self.enabled('Search') or not self.enabled(result.source) or not self.alive(editor): return False
            if not self.permissions.allowed({'Capture':SEARCH_CAPTURE,'Snippets':SEARCH_SNIPPETS}[result.source]): return False
            if getattr(self,key+'_store') is not store or getattr(self,key+'_window') is not editor: return False
            try: same=store.get(result.id) is item
            except KeyError: same=False
            if not same or before!=(editor.current,editor.values()): return False
            editor.fill(item)
        editor.query.set(''); editor.refresh(); editor.window.lift(); return True

    def toggle_quick_panel(self):
        if not self.settings.appearance.quick_enabled: return
        if self.alive(self.quick_panel): self.close_window('quick_panel'); return
        from aeris.quick_panel import QuickPanel
        self.quick_panel=QuickPanel(self)
        track_window(self,'quick_panel')
        apply_tree(self.quick_panel.window, self.settings.appearance.theme)

    def open_appearance(self):
        if self.alive(self.appearance_window): self.appearance_window.window.lift(); return
        from aeris.appearance_ui import AppearanceWindow
        self.appearance_window=AppearanceWindow(self)
        track_window(self,'appearance_window')
        apply_tree(self.appearance_window.window, self.settings.appearance.theme)

    def apply_appearance(self):
        self.close_window('quick_panel'); self.close_window('search_window')
        self.quick_button.configure(state='normal' if self.settings.appearance.quick_enabled else 'disabled')
        configure(self.root, self.settings.appearance.theme)
        apply_tree(self.root, self.settings.appearance.theme)
        self.refresh_spotlight(); self.show_selected()

    def refresh_spotlight(self):
        if self.spotlight: self.spotlight.destroy(); self.spotlight=None
        if self.settings.appearance.floating_enabled and not self.spotlight_hidden:
            from aeris.spotlight import Spotlight
            self.spotlight=Spotlight(self)
        self.spotlight_button.configure(text='Ocultar Spotlight' if self.spotlight else 'Mostrar Spotlight')

    def hide_spotlight(self):
        self.spotlight_hidden=True; self.refresh_spotlight()

    def toggle_spotlight_visibility(self):
        if not self.settings.appearance.floating_enabled: self.open_appearance(); return
        self.spotlight_hidden=self.spotlight is not None; self.refresh_spotlight()

    def close(self):
        has_content=any(s and s.list() for s in (self.capture_store,self.snippets_store,self.clipboard_store,self.expand_store,self.drop_store)) or self.alive(self.expand_window) or self.alive(self.bridge_window) or self.alive(self.routine_window) or bool(self.routine_store and self.routine_store.list()) or bool(self.workspace_store and self.workspace_store.list()) or self.alive(self.workspace_window)
        has_content=has_content or bool(self.research_store and self.research_store.list()) or (self.alive(self.research_window) and self.research_window.dirty())
        has_content=has_content or bool(self.flashcards_store and self.flashcards_store.list()) or (self.alive(self.flashcards_window) and self.flashcards_window.dirty())
        has_content=has_content or bool(self.learn_store and self.learn_store.list())
        has_content=has_content or bool(self.timeline_store and self.timeline_store.list()) or (self.alive(self.timeline_window) and self.timeline_window.dirty())
        has_content=has_content or bool(self.meeting_store and self.meeting_store.list()) or (self.alive(self.meeting_window) and self.meeting_window.dirty())
        has_content=has_content or bool(self.interview_store and self.interview_store.list()) or (self.alive(self.interview_window) and self.interview_window.dirty())
        has_content=has_content or bool(self.context_store and self.context_store.list()) or (self.alive(self.context_window) and self.context_window.dirty())
        has_content=has_content or bool(self.ideas_store and self.ideas_store.list()) or (self.alive(self.ideas_window) and self.ideas_window.dirty())
        has_content=has_content or bool(self.reminder_store and self.reminder_store.list())
        has_content=has_content or bool(self.checklist_store and self.checklist_store.names())
        has_content=has_content or bool(self.focus_timer and (self.focus_timer.state in ('running','paused') or any(self.focus_timer.completed.values())))
        has_draft=any(self.alive(w) and w.dirty() for w in (self.capture_window,self.snippets_window,self.text_window,self.email_window,self.accessibility_window,self.decision_window,self.copilot_window,self.debug_window))
        has_appearance=self.alive(self.appearance_window) and self.appearance_window.values()!=self.settings.appearance
        if (has_content or has_draft or has_appearance or (self.alive(self.vault_window) and self.vault_window.dirty()) or (self.alive(self.bookmarks_window) and self.bookmarks_window.dirty()) or (self.alive(self.autofill_window) and self.autofill_window.dirty())) and not messagebox.askyesno('Encerrar Aeris?','Textos e alterações da sessão serão descartados. Cópias protegidas já gravadas e clipboard podem permanecer.',parent=self.root): return
        self.stop_autosave()
        if self.alive(self.vault_window): self.vault_window.force_lock()
        if self.alive(self.bookmarks_window): self.bookmarks_window.force_lock()
        if self.alive(self.autofill_window): self.autofill_window.force_lock()
        if self.alive(self.translate_window): self.translate_window.close()
        if self.alive(self.voice_window): self.voice_window.close()
        if self.alive(self.pronounce_window): self.pronounce_window.close()
        self.reset_reminders()
        self.reset_context()
        self.reset_interview()
        self.reset_meeting()
        self.reset_ideas()
        self.reset_timeline()
        self.reset_learn()
        self.reset_research()
        self.reset_flashcards()
        self.root.destroy()

def main():
    root=tk.Tk(); Hub(root); root.mainloop()
