"""Permission management with visible session scope and immediate revocation."""
import tkinter as tk
from tkinter import ttk, messagebox
from aeris.scroll_area import scroll_area
from aeris.permissions import CAPABILITIES

class PermissionsWindow:
    def __init__(self, hub):
        self.hub = hub
        self.window = tk.Toplevel(hub.root)
        self.window.title('Aeris Permissions')
        self.window.geometry('760x570')
        self.window.minsize(700, 540)
        self.window.bind('<Escape>', lambda _: self.window.destroy())
        frame = ttk.Frame(self.window, padding=16)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Permissões', font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(frame, text='Negadas por padrão. Autorizações valem até o encerramento da sessão.', wraplength=380).pack(anchor='w', pady=8)
        self.buttons = {}
        self.summary=tk.StringVar(self.window)
        self.status=tk.StringVar(self.window)
        ttk.Label(frame,textvariable=self.summary).pack(anchor='w')
        ttk.Label(frame,textvariable=self.status,wraplength=640).pack(anchor='w')
        cards=scroll_area(frame)
        for col in range(2): cards.columnconfigure(col,weight=1,uniform='permissions')
        for i,(key, (label, desc)) in enumerate(CAPABILITIES.items()):
            row = ttk.Frame(cards,padding=6); row.grid(row=i//2,column=i%2,sticky='nsew',pady=4,padx=4)
            ttk.Label(row, text=label).pack(anchor='w')
            ttk.Label(row, text=desc, wraplength=290).pack(anchor='w')
            button = ttk.Button(row, command=lambda k=key: self.toggle(k))
            button.pack(anchor='w', pady=3); self.buttons[key] = button
        ttk.Button(frame, text='Revogar todas', command=self.hub.permissions.revoke_all).pack(fill='x', pady=6)
        self.refresh()

    def refresh(self):
        self.summary.set(f'{sum(self.hub.permissions.allowed(k) for k in CAPABILITIES)}/{len(CAPABILITIES)} acessos autorizados nesta sessão')
        for key, button in self.buttons.items():
            button.configure(text='Revogar acesso' if self.hub.permissions.allowed(key) else 'Autorizar nesta sessão')

    def toggle(self, key):
        permissions=self.hub.permissions
        granted=not permissions.allowed(key)
        reviewed=permissions.revision
        if granted and not messagebox.askyesno('Autorizar acesso?', CAPABILITIES[key][1]+'\n\nApenas nesta sessão.', parent=self.window):
            return
        if not self.window.winfo_exists(): return
        if permissions is not self.hub.permissions or reviewed!=permissions.revision:
            self.status.set('Permissões alteradas. Confirme novamente.'); self.refresh(); return
        permissions.set(key,granted)
        self.status.set('Acesso autorizado nesta sessão.' if granted else 'Acesso revogado.')
