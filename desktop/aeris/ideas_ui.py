"""Manual idea editor, with no integrations outside its own session store."""
import tkinter as tk
from tkinter import ttk, messagebox
from aeris.ideas import STATUSES


class IdeasWindow:
    def __init__(self, hub):
        self.hub, self.store = hub, hub.ideas_store
        self.selected_id = None
        self.window = tk.Toplevel(hub.root)
        self.window.title('Aeris Ideas'); self.window.geometry('740x620'); self.window.minsize(580,560)
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        self.window.bind('<Escape>', lambda _: self.close())
        f=ttk.Frame(self.window,padding=14); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Aeris Ideas',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text='Grandes coisas começam com pequenas ideias. Apenas nesta sessão.').pack(anchor='w',pady=(0,8))
        filters=ttk.Frame(f); filters.pack(fill='x')
        self.query=tk.StringVar(self.window); self.filter=tk.StringVar(self.window,'Todos')
        ttk.Label(filters,text='Pesquisar').pack(side='left')
        q=ttk.Entry(filters,textvariable=self.query); q.pack(side='left',fill='x',expand=True,padx=4); q.bind('<Return>',lambda _: self.render())
        ttk.Combobox(filters,textvariable=self.filter,values=('Todos',)+STATUSES,state='readonly',width=20).pack(side='left')
        ttk.Button(filters,text='Filtrar',command=self.render).pack(side='left',padx=4)
        ttk.Button(filters,text='Limpar',command=self.clear_filters).pack(side='left')
        self.stats=tk.StringVar(self.window); ttk.Label(f,textvariable=self.stats).pack(anchor='w',pady=4)
        area=ttk.Frame(f); area.pack(fill='both',expand=True)
        self.tree=ttk.Treeview(area,columns=('title','category','status'),show='headings',selectmode='browse',height=6)
        for col,label,width in [('title','Título',260),('category','Categoria',125),('status','Estado',140)]:
            self.tree.heading(col,text=label); self.tree.column(col,width=width,stretch=col=='title')
        sb=ttk.Scrollbar(area,orient='vertical',command=self.tree.yview); self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side='left',fill='both',expand=True); sb.pack(side='right',fill='y')
        self.tree.bind('<Double-1>',lambda _: self.load_selected())
        self.tree.bind('<Return>',lambda _: self.load_selected())
        ttk.Button(f,text='Abrir ideia selecionada',command=self.load_selected).pack(anchor='w',pady=3)
        self.title=tk.StringVar(self.window); self.category=tk.StringVar(self.window,'Geral'); self.state=tk.StringVar(self.window,'Nova')
        self.editor_label=tk.StringVar(self.window,'Nova ideia'); ttk.Label(f,textvariable=self.editor_label,font=('Segoe UI',12,'bold')).pack(anchor='w')
        for label,var in [('Título',self.title),('Categoria',self.category)]:
            bar=ttk.Frame(f); bar.pack(fill='x',pady=2); ttk.Label(bar,text=label,width=12).pack(side='left'); ttk.Entry(bar,textvariable=var).pack(side='left',fill='x',expand=True)
        bar=ttk.Frame(f); bar.pack(fill='x'); ttk.Label(bar,text='Estado',width=12).pack(side='left'); ttk.Combobox(bar,textvariable=self.state,values=STATUSES,state='readonly').pack(side='left',fill='x',expand=True)
        ttk.Label(f,text='Descrição (até 4.000 caracteres)').pack(anchor='w',pady=(4,0))
        body_area=ttk.Frame(f); body_area.pack(fill='both',expand=True)
        self.body=tk.Text(body_area,height=5,wrap='word'); sb=ttk.Scrollbar(body_area,command=self.body.yview); self.body.configure(yscrollcommand=sb.set); self.body.pack(side='left',fill='both',expand=True); sb.pack(side='right',fill='y')
        actions=ttk.Frame(f); actions.pack(fill='x',pady=5)
        for label,cmd in [('Nova / limpar',self.new),('Salvar ideia',self.save),('Excluir ideia aberta',self.delete)]:
            ttk.Button(actions,text=label,command=cmd).pack(side='left',fill='x',expand=True,padx=2)
        self.status=tk.StringVar(self.window); ttk.Label(f,textvariable=self.status,wraplength=520).pack(anchor='w')
        self.render()

    def values(self):
        return self.title.get(),self.category.get(),self.body.get('1.0','end-1c'),self.state.get()

    def dirty(self):
        if self.selected_id is None: return self.values()!=('','Geral','','Nova')
        try: item=self.store.get(self.selected_id)
        except KeyError: return True
        return self.values()!=(item.title,item.category,item.body,item.status)

    def discard_ok(self):
        return not self.dirty() or messagebox.askyesno('Descartar rascunho?', 'Alterações não salvas serão descartadas.',parent=self.window)

    def close(self):
        if self.discard_ok(): self.window.destroy()

    def set_editor(self,item=None):
        self.selected_id=item.id if item else None
        self.editor_label.set('Editar ideia' if item else 'Nova ideia')
        self.title.set(item.title if item else ''); self.category.set(item.category if item else 'Geral'); self.state.set(item.status if item else 'Nova')
        self.body.delete('1.0','end')
        if item: self.body.insert('1.0',item.body)

    def new(self):
        if self.discard_ok(): self.set_editor(); self.status.set('Nova ideia.')

    def load_selected(self):
        ids=self.tree.selection()
        if not ids: self.status.set('Selecione uma ideia.'); return
        try: item=self.store.get(int(ids[0]))
        except KeyError: self.render(); self.status.set('Registro removido.'); return
        before=(self.selected_id,self.values())
        if not self.discard_ok(): return
        if not self.window.winfo_exists(): return
        try: same=self.store.get(item.id) is item
        except KeyError: same=False
        if not same or before!=(self.selected_id,self.values()) or self.tree.selection()!=ids:
            self.render(); self.status.set('Seleção alterada. Revise novamente.'); return
        self.set_editor(item); self.status.set('Aberto para edição.')

    def clear_filters(self):
        self.query.set(''); self.filter.set('Todos')
        self.render()

    def render(self):
        selected=self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        try: items=self.store.search(self.query.get(), None if self.filter.get()=='Todos' else self.filter.get())
        except ValueError as e: self.stats.set('Filtro inválido.'); self.status.set(str(e)); return
        for item in items: self.tree.insert('','end',iid=str(item.id),values=(item.title,item.category,item.status))
        if selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected[0]); self.tree.focus(selected[0]); self.tree.see(selected[0])
        self.stats.set(f'{len(items)} exibidas / {len(self.store.list())} ideias na sessão')

    def changed(self):
        self.render()
        if self.hub.alive(self.hub.privacy_window): self.hub.privacy_window.refresh()

    def save(self):
        try: item=self.store.add(*self.values()) if self.selected_id is None else self.store.edit(self.selected_id,*self.values())
        except (ValueError,KeyError) as e: self.status.set(str(e)); return
        self.set_editor(item); self.changed(); self.status.set('Ideia salva somente na sessão.')

    def delete(self):
        if self.selected_id is None: self.status.set('Abra uma ideia antes de excluir.'); return
        try: item=self.store.get(self.selected_id)
        except KeyError: self.render(); self.status.set('Registro removido.'); return
        draft=self.values()
        if not messagebox.askyesno('Excluir?', 'Excluir o registro aberto e seu rascunho?',parent=self.window): return
        if not self.window.winfo_exists(): return
        try: same=self.store.get(item.id) is item
        except KeyError: same=False
        if not same or self.selected_id!=item.id or self.values()!=draft:
            self.render(); self.status.set('Seleção alterada. Revise novamente.'); return
        self.store.delete(item.id); self.set_editor(); self.changed(); self.status.set('Registro excluído.')
