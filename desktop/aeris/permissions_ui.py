"""Permission management with visible session scope and immediate revocation."""
import tkinter as tk
from tkinter import ttk
from aeris.consent_ui import ask_permission
from aeris.scroll_area import scroll_area
from aeris.permissions import CAPABILITIES
from aeris.registry import normalize

class PermissionsWindow:
    def __init__(self, hub):
        self.hub = hub
        self.window = tk.Toplevel(hub.root)
        self.window.title('Aeris · Permissões')
        self.window.geometry('760x570')
        self.window.minsize(700, 540)
        self.window.bind('<Escape>', lambda _: self.window.destroy())
        frame = ttk.Frame(self.window, padding=16)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Controle de acessos', font=('Segoe UI',21,'bold')).pack(anchor='w')
        ttk.Label(frame, text='Você escolhe o que o Aeris pode acessar. Permissões internas, negadas por padrão e válidas somente nesta sessão.', wraplength=650).pack(anchor='w', pady=8)
        self.buttons = {}
        self.rows = {}
        self.states = {}
        self.state_labels = {}
        self.summary=tk.StringVar(self.window)
        self.status=tk.StringVar(self.window)
        summary_card=ttk.Frame(frame,padding=12,style='Experience.Card.TFrame'); summary_card.pack(fill='x',pady=(0,6))
        ttk.Label(summary_card,text='ACESSOS NESTA SESSÃO',style='Experience.Card.TLabel').pack(anchor='w')
        ttk.Label(summary_card,textvariable=self.summary,style='Experience.Detail.TLabel').pack(anchor='w')
        ttk.Label(summary_card,text='Autorização não significa que o dispositivo está ativo.',style='Experience.Card.TLabel',wraplength=610).pack(anchor='w')
        filters=ttk.Frame(frame); filters.pack(fill='x',pady=(6,4))
        self.query=tk.StringVar(self.window)
        ttk.Label(filters,text='Buscar acesso').pack(side='left',padx=(0,6))
        entry=ttk.Entry(filters,textvariable=self.query); entry.pack(side='left',fill='x',expand=True)
        entry.bind('<KeyRelease>',lambda _:self.refresh())
        self.granted_only=tk.BooleanVar(self.window,False)
        ttk.Checkbutton(filters,text='Somente autorizados',variable=self.granted_only,command=self.refresh).pack(side='left',padx=6)
        ttk.Button(filters,text='Limpar',command=self.clear_filters).pack(side='right')
        ttk.Label(frame,textvariable=self.status,wraplength=640).pack(anchor='w')
        cards=scroll_area(frame)
        for col in range(2): cards.columnconfigure(col,weight=1,uniform='permissions')
        for i,(key, (label, desc)) in enumerate(CAPABILITIES.items()):
            row = ttk.Labelframe(cards,padding=8,text=label); self.rows[key]=row; row.grid(row=i//2,column=i%2,sticky='nsew',pady=4,padx=4)
            state=tk.StringVar(self.window); self.states[key]=state
            indicator=ttk.Label(row,textvariable=state,style='Aeris.Info.TLabel'); indicator.pack(anchor='w'); self.state_labels[key]=indicator
            ttk.Label(row, text=desc, wraplength=290).pack(anchor='w')
            button = ttk.Button(row, command=lambda k=key: self.toggle(k))
            button.pack(anchor='w', pady=3); self.buttons[key] = button
        ttk.Button(frame,text='Revogar todos os acessos',command=self.hub.permissions.revoke_all,style='Aeris.Stop.TButton').pack(fill='x',pady=6)
        self.refresh()

    def clear_filters(self):
        self.query.set(''); self.granted_only.set(False); self.refresh()

    def refresh(self):
        self.summary.set(f'{sum(self.hub.permissions.allowed(k) for k in CAPABILITIES)}/{len(CAPABILITIES)} acessos autorizados nesta sessão')
        words=normalize(self.query.get()).split()
        index=0
        for key, button in self.buttons.items():
            allowed=self.hub.permissions.allowed(key)
            self.states[key].set('Autorizado nesta sessão' if allowed else 'Acesso negado')
            self.state_labels[key].configure(style='Aeris.Success.TLabel' if allowed else 'Experience.Muted.TLabel')
            button.configure(text='Revogar acesso' if allowed else 'Autorizar nesta sessão',style='Aeris.Stop.TButton' if allowed else 'TButton')
            label,desc=CAPABILITIES[key]
            if (not self.granted_only.get() or allowed) and all(word in normalize(label+' '+desc) for word in words):
                self.rows[key].grid(row=index//2,column=index%2,sticky='nsew',pady=4,padx=4); index+=1
            else:
                self.rows[key].grid_remove()

    def toggle(self, key):
        permissions=self.hub.permissions
        granted=not permissions.allowed(key)
        reviewed=permissions.revision
        if granted and not ask_permission(self.window,self.hub.settings.appearance.theme,key):
            return
        if not self.window.winfo_exists(): return
        if permissions is not self.hub.permissions or reviewed!=permissions.revision:
            self.status.set('Permissões alteradas. Confirme novamente.'); self.refresh(); return
        permissions.set(key,granted)
        self.status.set('Acesso autorizado nesta sessão.' if granted else 'Acesso revogado.')
