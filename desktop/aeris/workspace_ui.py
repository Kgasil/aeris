"""Local preset editor and individually confirmed actions."""
import tkinter as tk
from tkinter import ttk, messagebox
from aeris.workspace import TOOLS
from aeris.permissions import WORKSPACE_OPEN

class WorkspaceWindow:
    def __init__(self, hub, store):
        self.hub, self.store = hub, store
        self.window = tk.Toplevel(hub.root)
        self.window.title('Aeris Workspace · Ambientes')
        self.window.geometry('590x630'); self.window.minsize(440,530)
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        self.window.bind('<Escape>', lambda _: self.close())
        f = ttk.Frame(self.window, padding=12); f.pack(fill='both', expand=True)
        ttk.Label(f, text='Workspace · organize seu ambiente', font=('Segoe UI',17)).pack(anchor='w')
        ttk.Label(f, text='Ambientes da sessão. Ativar apenas filtra o painel rápido; não abre nada automaticamente.', wraplength=430).pack(anchor='w')
        row=ttk.Frame(f); row.pack(fill='x',pady=4)
        self.saved=ttk.Combobox(row,state='readonly'); self.saved.pack(side='left',fill='x',expand=True)
        ttk.Button(row,text='Carregar',command=self.load).pack(side='left')
        ttk.Button(row,text='Excluir',command=self.delete).pack(side='left')
        self.name=tk.StringVar(self.window)
        ttk.Label(f,text='Nome do ambiente').pack(anchor='w'); ttk.Entry(f,textvariable=self.name).pack(fill='x')
        ttk.Label(f,text='Ferramentas desejadas (clique para marcar ou desmarcar)').pack(anchor='w',pady=(6,0))
        r=ttk.Frame(f); r.pack(fill='x'); scroll=ttk.Scrollbar(r); scroll.pack(side='right',fill='y')
        self.tools=tk.Listbox(r,selectmode='multiple',exportselection=False,height=6,yscrollcommand=scroll.set); self.tools.pack(fill='x',expand=True)
        scroll.configure(command=self.tools.yview)
        for n in TOOLS: self.tools.insert('end',n)
        ttk.Label(f,text='Links opcionais · um HTTP/HTTPS por linha, até oito. Use dados fictícios.').pack(anchor='w',pady=(6,0))
        self.links=tk.Text(f,height=4,wrap='none'); self.links.pack(fill='both',expand=True)
        r=ttk.Frame(f); r.pack(fill='x',pady=4)
        ttk.Button(r,text='Salvar ambiente',command=self.save).pack(side='left',padx=2)
        ttk.Button(r,text='Novo',command=self.new).pack(side='left',padx=2)
        ttk.Button(r,text='Ativar salvo',command=self.activate).pack(side='left',padx=2)
        ttk.Button(r,text='Sair do ambiente',command=self.deactivate).pack(side='left',padx=2)
        ttk.Label(f,text='Abrir individualmente a partir do ambiente salvo').pack(anchor='w')
        self.actions=ttk.Combobox(f,state='readonly'); self.actions.pack(fill='x')
        self.saved.bind('<<ComboboxSelected>>',lambda _:self.refresh_actions())
        self.actions.bind('<<ComboboxSelected>>',lambda _:self.permissions_changed())
        self.open_button=ttk.Button(f,text='Abrir seleção',command=self.open_selected); self.open_button.pack(fill='x',pady=3)
        ttk.Button(f,text='Permissões',command=hub.open_permissions).pack(fill='x')
        self.status=tk.StringVar(self.window); ttk.Label(f,textvariable=self.status,wraplength=420).pack(anchor='w',pady=3)
        self.refresh(); self.baseline=self.values()

    def values(self):
        return self.name.get(), tuple(TOOLS[i] for i in self.tools.curselection()), tuple(self.links.get('1.0','end-1c').splitlines())
    def dirty(self): return self.values()!=self.baseline
    def allow_discard(self): return not self.dirty() or messagebox.askyesno('Descartar?', 'Descartar alterações não salvas?',parent=self.window)
    def fill(self,item=None):
        self.name.set(item.name if item else ''); self.tools.selection_clear(0,'end'); self.links.delete('1.0','end')
        if item:
            for n in item.tools: self.tools.selection_set(TOOLS.index(n))
            self.links.insert('1.0','\n'.join(item.links))
        self.baseline=self.values()
    def refresh(self,name=''):
        self.saved.configure(values=tuple(x.name for x in self.store.list())); self.saved.set(name); self.refresh_actions()
    def refresh_actions(self):
        self.actions.set(''); self.action_items=[]
        if self.saved.get() in tuple(x.name for x in self.store.list()):
            item=self.store.get(self.saved.get())
            self.action_items=[('tool',n) for n in item.tools]+[('link',i) for i in range(len(item.links))]
            self.actions.configure(values=tuple(['Ferramenta: '+n for n in item.tools]+['Link: '+u for u in item.links]))
        else: self.actions.configure(values=())
        self.permissions_changed()
    def permissions_changed(self):
        i=self.actions.current(); allowed=False
        if 0<=i<len(self.action_items):
            kind,value=self.action_items[i]
            allowed=self.hub.enabled(value) if kind=='tool' else self.hub.permissions.allowed(WORKSPACE_OPEN)
        self.open_button.configure(state='normal' if allowed else 'disabled')
    def new(self):
        if self.allow_discard(): self.fill(); self.refresh()
    def save(self):
        name,tools,links=self.values(); name=name.strip()
        if any(x.name==name for x in self.store.list()) and not messagebox.askyesno('Atualizar?', 'Substituir ambiente salvo?',parent=self.window): return
        try: item=self.store.save(name,tools,tuple(x.strip() for x in links if x.strip()))
        except ValueError as exc: self.status.set(str(exc)); return
        self.fill(item); self.refresh(item.name); self.hub.workspace_changed(); self.status.set('Salvo somente nesta sessão.')
    def load(self):
        name=self.saved.get()
        if not name: return
        try: item=self.store.get(name)
        except KeyError: self.refresh(); self.status.set('Ambiente não encontrado.'); return
        if not self.allow_discard(): return
        if self.saved.get()!=name or not any(x is item for x in self.store.list()):
            self.status.set('Seleção alterada. Carregue novamente.'); return
        self.fill(item)
    def delete(self):
        name=self.saved.get()
        if not name: return
        try: item=self.store.get(name)
        except KeyError: self.refresh(); self.status.set('Ambiente não encontrado.'); return
        if messagebox.askyesno('Excluir?', 'Remover ambiente salvo?',parent=self.window):
            if self.saved.get()!=name or not any(x is item for x in self.store.list()):
                self.status.set('Seleção alterada. Revise novamente.'); return
            self.store.delete(name); self.refresh(); self.hub.workspace_changed(); self.status.set('Ambiente removido.')
    def activate(self):
        if not self.saved.get(): self.status.set('Selecione um ambiente salvo.'); return
        try: self.store.activate(self.saved.get())
        except KeyError: self.refresh(); self.status.set('Ambiente não encontrado.'); return
        self.hub.workspace_changed(); self.status.set('Ambiente ativo: '+self.store.active)
    def deactivate(self):
        self.store.activate(None); self.hub.workspace_changed(); self.status.set('Painel rápido normal restaurado.')
    def open_selected(self):
        i=self.actions.current()
        if not 0<=i<len(self.action_items) or not self.hub.enabled('Workspace'): return
        kind,value=self.action_items[i]; name=self.saved.get()
        if kind=='tool':
            if self.hub.enabled(value): self.hub.open_tool(value)
            else: self.status.set('Ative a ferramenta no Hub primeiro.')
            return
        try:
            self.hub.permissions.require(WORKSPACE_OPEN)
            url=self.store.get(name).links[value]
            if not messagebox.askyesno('Abrir endereço externo?',f'{url}\n\nO navegador poderá acessar a internet. O site não foi verificado. Continuar?',parent=self.window): return
            if not self.hub.alive(self) or not self.hub.enabled('Workspace') or self.saved.get()!=name or self.actions.current()!=i or self.store.get(name).links[value]!=url: return
            self.store.open_link(name,value,self.hub.permissions)
            self.status.set('Endereço encaminhado ao navegador.')
        except (ValueError, OSError, KeyError, IndexError) as exc: self.status.set('Não foi possível abrir o link: '+str(exc))
    def close(self):
        if self.allow_discard(): self.window.destroy()
