"""Explicit text command preview and confirmation."""
import tkinter as tk
from tkinter import ttk
from aeris.copilot import CopilotSession, EXAMPLES
from aeris.permissions import COPILOT_RUN
from aeris.window_lifecycle import track_window

class CopilotWindow:
    def __init__(self,hub):
        self.hub=hub; self.session=CopilotSession(hub); self.companion=None
        self.window=tk.Toplevel(hub.root); w=self.window
        w.title('Aeris Copilot'); w.geometry('660x540'); w.minsize(520,450)
        f=ttk.Frame(w,padding=14); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Aeris Copilot',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text='Comandos textuais locais por regras. Conversa por IA opcional em janela separada. Nenhuma ação sem confirmação.',wraplength=490).pack(anchor='w')
        ttk.Label(f,text='Modelos de comandos:').pack(anchor='w',pady=(10,0))
        self.example=tk.StringVar(w,EXAMPLES[0]); box=ttk.Combobox(f,textvariable=self.example,values=EXAMPLES,state='readonly'); box.pack(fill='x')
        ttk.Button(f,text='Usar modelo',command=lambda:self.command.set(self.example.get())).pack(anchor='w')
        self.command=tk.StringVar(w); self.trace=self.command.trace_add('write',self.invalidate)
        self.entry=ttk.Entry(f,textvariable=self.command); self.entry.pack(fill='x',pady=8)
        self.count=tk.StringVar(w,'0 / 500 caracteres'); ttk.Label(f,textvariable=self.count).pack(anchor='w')
        self.entry.bind('<Return>',self.keyboard_prepare)
        self.entry.focus_set()
        self.permission=tk.StringVar(w); ttk.Label(f,textvariable=self.permission,wraplength=490).pack(anchor='w')
        ttk.Button(f,text='Permissões',command=hub.open_permissions).pack(anchor='w')
        ttk.Button(f,text='Preparar prévia',command=self.prepare).pack(anchor='w',pady=5)
        self.preview=tk.StringVar(w); ttk.Label(f,textvariable=self.preview,wraplength=490,justify='left').pack(fill='x',pady=10)
        actions=ttk.Frame(f); actions.pack(fill='x')
        self.confirm_button=ttk.Button(actions,text='Confirmar operação',command=self.confirm,state='disabled'); self.confirm_button.pack(side='left')
        ttk.Button(actions,text='Cancelar prévia',command=self.invalidate).pack(side='left',padx=5)
        ttk.Button(f,text='Abrir AI Companion (integrado)',command=self.open_companion).pack(anchor='w',pady=5)
        self.status=tk.StringVar(w); ttk.Label(f,textvariable=self.status,wraplength=490).pack(anchor='w',pady=8)
        w.bind('<Escape>',lambda _:w.destroy()); w.bind('<Destroy>',self.destroyed,add='+')
        self.permissions_changed()
    def open_companion(self):
        if self.hub.alive(self.companion): self.companion.window.lift(); return
        from aeris.companion_ui import CompanionWindow
        from aeris.theme import apply_tree
        self.companion=CompanionWindow(self); track_window(self,'companion'); apply_tree(self.companion.window,self.hub.settings.appearance.theme)
    def keyboard_prepare(self,_=None):
        self.prepare()
        return 'break'
    def invalidate(self,*_):
        self.session.cancel()
        if hasattr(self,'count'): self.count.set(f'{len(self.command.get())} / 500 caracteres')
        if hasattr(self,'preview'):
            self.preview.set(''); self.confirm_button.configure(state='disabled'); self.status.set('')
    def permissions_changed(self):
        self.invalidate()
        if self.hub.alive(self.companion): self.companion.permissions_changed()
        self.permission.set('Permissão de sessão concedida.' if self.hub.permissions.allowed(COPILOT_RUN) else 'Conceda Copilot → Executar nas permissões da sessão.')
    def prepare(self):
        self.invalidate()
        try: p=self.session.prepare(self.command.get())
        except (ValueError,PermissionError) as exc: self.status.set(str(exc)); return
        self.preview.set(p.preview); self.confirm_button.configure(state='normal')
    def confirm(self):
        try: result=self.session.confirm()
        except (ValueError,PermissionError,KeyError) as exc: result=str(exc)
        self.invalidate(); self.status.set(result)
    def dirty(self): return bool(self.command.get() or self.session.pending or (self.hub.alive(self.companion) and self.companion.dirty()))
    def destroyed(self,event):
        if event.widget is self.window:
            self.session.cancel(); self.command.trace_remove('write',self.trace); self.command.set(''); self.preview.set(''); self.status.set('')
