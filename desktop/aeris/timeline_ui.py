"""Timeline editor. Every record is explicitly entered and saved by the user."""
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox


class TimelineWindow:
    def __init__(self, hub):
        self.hub, self.store = hub, hub.timeline_store
        self.selected_id = None
        self.window = tk.Toplevel(hub.root)
        self.window.title('Aeris Timeline'); self.window.geometry('800x640'); self.window.minsize(630,570)
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.window.bind('<Escape>',lambda _: self.close())
        f=ttk.Frame(self.window,padding=14); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Aeris Timeline',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text='Cada pequeno avanço importa. Registros manuais, somente nesta sessão.').pack(anchor='w')
        self.query=tk.StringVar(self.window); self.category_filter=tk.StringVar(self.window)
        self.day_from=tk.StringVar(self.window); self.day_to=tk.StringVar(self.window)
        for fields in ((('Pesquisar',self.query),('Categoria',self.category_filter)),(('De (AAAA-MM-DD)',self.day_from),('Até (AAAA-MM-DD)',self.day_to))):
            bar=ttk.Frame(f); bar.pack(fill='x',pady=3)
            for label,var in fields:
                ttk.Label(bar,text=label).pack(side='left',padx=(0,3)); entry=ttk.Entry(bar,textvariable=var,width=15); entry.pack(side='left',fill='x',expand=True,padx=(0,6)); entry.bind('<Return>',lambda _: self.render())
        filters=ttk.Frame(f); filters.pack(fill='x')
        ttk.Button(filters,text='Filtrar',command=self.render).pack(side='left')
        ttk.Button(filters,text='Limpar filtros',command=self.clear_filters).pack(side='left',padx=4)
        self.stats=tk.StringVar(self.window); ttk.Label(f,textvariable=self.stats).pack(anchor='w',pady=3)
        area=ttk.Frame(f); area.pack(fill='both',expand=True)
        self.tree=ttk.Treeview(area,columns=('when','title','category'),show='headings',selectmode='browse',height=6)
        for col,label,width in [('when','Data e hora local',150),('title','Atividade',260),('category','Categoria',125)]:
            self.tree.heading(col,text=label); self.tree.column(col,width=width,stretch=col=='title')
        sb=ttk.Scrollbar(area,orient='vertical',command=self.tree.yview); self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side='left',fill='both',expand=True); sb.pack(side='right',fill='y')
        self.tree.bind('<Double-1>',lambda _: self.load_selected()); self.tree.bind('<Return>',lambda _: self.load_selected())
        ttk.Button(f,text='Abrir registro selecionado',command=self.load_selected).pack(anchor='w',pady=3)
        self.editor_label=tk.StringVar(self.window); ttk.Label(f,textvariable=self.editor_label,font=('Segoe UI',12,'bold')).pack(anchor='w')
        self.when=tk.StringVar(self.window); self.title=tk.StringVar(self.window); self.category=tk.StringVar(self.window)
        for label,var in [('Data/hora local',self.when),('Atividade',self.title),('Categoria',self.category)]:
            bar=ttk.Frame(f); bar.pack(fill='x',pady=2); ttk.Label(bar,text=label,width=17).pack(side='left'); ttk.Entry(bar,textvariable=var).pack(side='left',fill='x',expand=True)
            if var is self.when: ttk.Button(bar,text='Agora',command=lambda:self.when.set(datetime.now().isoformat(sep=' ',timespec='minutes'))).pack(side='left',padx=3)
        ttk.Label(f,text='Descrição opcional (até 2.000 caracteres)').pack(anchor='w',pady=(4,0))
        body_area=ttk.Frame(f); body_area.pack(fill='both',expand=True)
        self.body=tk.Text(body_area,height=4,wrap='word'); sb=ttk.Scrollbar(body_area,command=self.body.yview); self.body.configure(yscrollcommand=sb.set); self.body.pack(side='left',fill='both',expand=True); sb.pack(side='right',fill='y')
        actions=ttk.Frame(f); actions.pack(fill='x',pady=5)
        for label,cmd in [('Novo / limpar',self.new),('Salvar registro',self.save),('Excluir registro aberto',self.delete)]:
            ttk.Button(actions,text=label,command=cmd).pack(side='left',fill='x',expand=True,padx=2)
        self.status=tk.StringVar(self.window); ttk.Label(f,textvariable=self.status,wraplength=580).pack(anchor='w')
        self.set_editor(); self.render()

    def values(self):
        return self.when.get(),self.title.get(),self.category.get(),self.body.get('1.0','end-1c')

    def dirty(self):
        return self.values()!=self.baseline

    def discard_ok(self):
        return not self.dirty() or messagebox.askyesno('Descartar rascunho?', 'Alterações não salvas serão descartadas.',parent=self.window)

    def close(self):
        if self.discard_ok(): self.window.destroy()

    def set_editor(self,item=None):
        self.selected_id=item.id if item else None
        self.editor_label.set('Editar registro' if item else 'Novo registro — AAAA-MM-DD HH:MM')
        self.when.set((item.when if item else datetime.now()).isoformat(sep=' ',timespec='minutes'))
        self.title.set(item.title if item else ''); self.category.set(item.category if item else 'Geral')
        self.body.delete('1.0','end')
        if item: self.body.insert('1.0',item.body)
        self.baseline=self.values()

    def new(self):
        if self.discard_ok(): self.set_editor(); self.status.set('Novo registro.')

    def load_selected(self):
        ids=self.tree.selection()
        if not ids: self.status.set('Selecione um registro.'); return
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
        for var in (self.query,self.category_filter,self.day_from,self.day_to): var.set('')
        self.render()

    def render(self):
        selected=self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        try: items=self.store.search(self.query.get(),self.category_filter.get(),self.day_from.get(),self.day_to.get())
        except ValueError as e: self.stats.set('Filtro inválido.'); self.status.set(str(e)); return
        for item in items: self.tree.insert('','end',iid=str(item.id),values=(item.when.isoformat(sep=' ',timespec='minutes'),item.title,item.category))
        if selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected[0]); self.tree.focus(selected[0]); self.tree.see(selected[0])
        self.stats.set(f'{len(items)} exibidos / {len(self.store.list())} registros na sessão')
        self.status.set('')

    def changed(self):
        self.render()
        if self.hub.alive(self.hub.privacy_window): self.hub.privacy_window.refresh()

    def save(self):
        try: item=self.store.add(*self.values()) if self.selected_id is None else self.store.edit(self.selected_id,*self.values())
        except (ValueError,KeyError) as e: self.status.set(str(e)); return
        self.set_editor(item); self.changed(); self.status.set('Registro salvo somente na sessão.')

    def delete(self):
        if self.selected_id is None: self.status.set('Abra um registro antes de excluir.'); return
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
