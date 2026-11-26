"""Explicit user actions only; system clipboard history remains outside Aeris."""
import tkinter as tk
from aeris.window_lifecycle import trace_window
from tkinter import ttk, messagebox
from aeris.permissions import READ_CLIPBOARD, WRITE_CLIPBOARD

class ClipboardWindow:
    def __init__(self, hub, store):
        self.hub, self.store = hub, store
        self.window = tk.Toplevel(hub.root)
        self.window.title('Aeris Clipboard · sessão local')
        self.window.geometry('480x540'); self.window.minsize(380, 480)
        self.window.bind('<Escape>', lambda _: self.window.destroy())
        frame = ttk.Frame(self.window, padding=12); frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Clipboard', font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(frame, text='Somente captura manual de texto. Use dados fictícios; não capture senhas.', wraplength=350).pack(anchor='w', pady=(0,6))
        self.capture_button = ttk.Button(frame, text='Capturar texto atual', command=self.capture)
        self.capture_button.pack(fill='x')
        ttk.Button(frame, text='Permissões da sessão', command=hub.open_permissions).pack(fill='x', pady=(2,6))
        self.query = tk.StringVar(self.window)
        ttk.Label(frame, text='Pesquisar histórico local').pack(anchor='w')
        search=ttk.Entry(frame,textvariable=self.query); search.pack(fill='x')
        self.window.bind('<Control-f>',lambda _:search.focus_set())
        self.pinned_only=tk.BooleanVar(self.window,False)
        ttk.Checkbutton(frame,text='Somente fixados',variable=self.pinned_only,command=self.refresh).pack(anchor='w')
        listing = ttk.Frame(frame); listing.pack(fill='both', expand=True, pady=4)
        scroll = ttk.Scrollbar(listing); scroll.pack(side='right', fill='y')
        self.items = tk.Listbox(listing, height=5, exportselection=False, yscrollcommand=scroll.set)
        self.items.pack(fill='both', expand=True); scroll.configure(command=self.items.yview)
        self.items.bind('<<ListboxSelect>>', self.preview)
        self.detail = tk.Text(frame, height=4, wrap='word', state='disabled', exportselection=False)
        self.detail.pack(fill='x')
        self.actions = ttk.Frame(frame); self.actions.pack(fill='x', pady=4)
        self.copy_button = ttk.Button(self.actions, text='Copiar', command=self.copy); self.copy_button.pack(side='left', padx=2)
        self.pin_button = ttk.Button(self.actions, text='Fixar / soltar', command=self.pin); self.pin_button.pack(side='left', padx=2)
        ttk.Button(self.actions, text='Excluir', command=self.delete).pack(side='left', padx=2)
        ttk.Button(frame, text='Limpar histórico do Aeris', command=self.clear).pack(fill='x')
        self.status = tk.StringVar(self.window)
        ttk.Label(frame, textvariable=self.status, wraplength=350).pack(anchor='w', pady=4)
        trace_window(self.window, self.query, self.refresh)
        self.permissions_changed(); self.refresh()

    def permissions_changed(self):
        self.capture_button.configure(state='normal' if self.hub.permissions.allowed(READ_CLIPBOARD) else 'disabled')
        self.copy_button.configure(state='normal' if self.hub.permissions.allowed(WRITE_CLIPBOARD) else 'disabled')
        self.status.set('Leitura e escrita exigem permissões separadas. Histórico apenas nesta sessão.')

    def selected(self):
        selection = self.items.curselection()
        return self.visible[selection[0]] if selection and selection[0]<len(self.visible) else None

    def refresh(self, *_):
        selected=self.selected() if hasattr(self,'visible') else None
        self.visible=tuple(c for c in self.store.list(self.query.get()) if not self.pinned_only.get() or c.pinned)
        self.items.delete(0,'end')
        for c in self.visible:
            label = ' '.join(c.text.split())[:65]
            self.items.insert('end', ('[Fixado] ' if c.pinned else '') + label)
        if selected:
            for i,c in enumerate(self.visible):
                if c.id==selected.id: self.items.selection_set(i); self.items.see(i); break
        self.preview()

    def preview(self, _=None):
        item = self.selected()
        self.detail.configure(state='normal'); self.detail.delete('1.0','end')
        if item: self.detail.insert('1.0', item.text)
        self.detail.configure(state='disabled')

    def capture(self):
        if not self.hub.permissions.allowed(READ_CLIPBOARD): return
        if not messagebox.askyesno('Capturar texto?', 'O conteúdo de texto atual será lido e mantido na memória do Aeris. Não capture dados sensíveis.', parent=self.window): return
        try:
            self.store.capture(self.hub.root.clipboard_get)
        except (tk.TclError, ValueError, PermissionError) as exc:
            self.status.set(str(exc) if isinstance(exc, ValueError) else 'Texto indisponível ou acesso negado.'); return
        self.query.set(''); self.refresh(); self.status.set('Texto capturado. Até 50 itens; fixados não são removidos automaticamente.')

    def write(self, text):
        self.hub.root.clipboard_clear(); self.hub.root.clipboard_append(text)

    def copy(self):
        item = self.selected()
        if not item or not self.hub.permissions.allowed(WRITE_CLIPBOARD): return
        if not messagebox.askyesno('Copiar?', 'Substituir o clipboard atual? O Windows pode manter cópias no próprio histórico.', parent=self.window): return
        if not self.window.winfo_exists(): return
        if self.selected() is not item or not any(c is item for c in self.store.list()):
            self.refresh(); self.status.set('Seleção alterada. Revise novamente.'); return
        try: self.store.copy(item.id, self.write)
        except (tk.TclError, PermissionError, StopIteration): self.status.set('Não foi possível copiar.'); return
        self.status.set('Copiado. Cole manualmente no destino.')

    def pin(self):
        item = self.selected()
        if item: self.store.pin(item.id); self.refresh()

    def delete(self):
        item = self.selected()
        if item and messagebox.askyesno('Excluir?', 'Remover somente do histórico do Aeris?', parent=self.window):
            if not self.window.winfo_exists(): return
            if self.selected() is not item or not any(c is item for c in self.store.list()):
                self.refresh(); self.status.set('Seleção alterada. Revise novamente.'); return
            self.store.delete(item.id); self.refresh()

    def clear(self):
        reviewed=self.store.list()
        if messagebox.askyesno('Limpar?', 'Excluir todos os itens, inclusive fixados? O clipboard do Windows não será alterado.', parent=self.window):
            if not self.window.winfo_exists(): return
            if self.store.list()!=reviewed: self.refresh(); self.status.set('Histórico alterado. Confirme novamente.'); return
            self.store.clear(); self.query.set(''); self.refresh(); self.status.set('Histórico local limpo.')
