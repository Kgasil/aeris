"""Manual reference editor, no URL opening, automatic retrieval or file reads."""
import tkinter as tk
from tkinter import ttk, messagebox
from aeris.research import KINDS, STATES

class ResearchWindow:
    def __init__(self, hub):
        self.hub, self.store=hub,hub.research_store
        self.selected_id=None
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris Research'); self.window.geometry('820x740'); self.window.minsize(650,650)
        self.window.protocol('WM_DELETE_WINDOW',self.close); self.window.bind('<Escape>',lambda _:self.close())
        f=ttk.Frame(self.window,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Aeris Research',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text='Referências informadas por você. Somente nesta sessão; sem consultar fontes.').pack(anchor='w')
        self.query=tk.StringVar(self.window); self.project_filter=tk.StringVar(self.window); self.filter=tk.StringVar(self.window,'Todos')
        bar=ttk.Frame(f); bar.pack(fill='x',pady=5)
        ttk.Label(bar,text='Busca').pack(side='left'); ttk.Entry(bar,textvariable=self.query,width=20).pack(side='left',fill='x',expand=True)
        ttk.Label(bar,text='Projeto exato').pack(side='left',padx=4); ttk.Entry(bar,textvariable=self.project_filter,width=16).pack(side='left')
        ttk.Combobox(bar,textvariable=self.filter,values=('Todos',)+STATES,state='readonly',width=14).pack(side='left',padx=4)
        ttk.Button(bar,text='Filtrar',command=self.render).pack(side='left')
        ttk.Button(bar,text='Limpar filtros',command=self.clear_filters).pack(side='left',padx=2)
        self.stats=tk.StringVar(self.window); ttk.Label(f,textvariable=self.stats).pack(anchor='w')
        area=ttk.Frame(f); area.pack(fill='both',expand=True)
        self.tree=ttk.Treeview(area,columns=('title','project','kind','state'),show='headings',selectmode='browse',height=5)
        for key,label,width in [('title','Título',260),('project','Projeto',160),('kind','Tipo',90),('state','Leitura',100)]:
            self.tree.heading(key,text=label); self.tree.column(key,width=width,stretch=key=='title')
        sb=ttk.Scrollbar(area,command=self.tree.yview); self.tree.configure(yscrollcommand=sb.set); self.tree.pack(side='left',fill='both',expand=True); sb.pack(side='right',fill='y')
        self.tree.bind('<Double-1>',lambda _:self.load_selected()); self.tree.bind('<Return>',lambda _:self.load_selected())
        ttk.Button(f,text='Abrir referência selecionada',command=self.load_selected).pack(anchor='w',pady=3)
        self.editor_label=tk.StringVar(self.window,'Nova referência'); ttk.Label(f,textvariable=self.editor_label,font=('Segoe UI',12,'bold')).pack(anchor='w')
        self.title=tk.StringVar(self.window); self.project=tk.StringVar(self.window,'Geral'); self.kind=tk.StringVar(self.window,KINDS[0]); self.authors=tk.StringVar(self.window); self.year=tk.StringVar(self.window); self.locator=tk.StringVar(self.window); self.state=tk.StringVar(self.window,STATES[0])
        for label,var,choices in [('Título',self.title,None),('Projeto',self.project,None),('Tipo',self.kind,KINDS),('Autoria',self.authors,None),('Ano',self.year,None),('URL / DOI / edição',self.locator,None),('Leitura',self.state,STATES)]:
            bar=ttk.Frame(f); bar.pack(fill='x',pady=1); ttk.Label(bar,text=label,width=19).pack(side='left')
            widget=ttk.Combobox(bar,textvariable=var,values=choices,state='readonly') if choices else ttk.Entry(bar,textvariable=var)
            widget.pack(side='left',fill='x',expand=True)
        ttk.Label(f,text='Anotações vinculadas à referência (até 4.000 caracteres)').pack(anchor='w')
        area=ttk.Frame(f); area.pack(fill='both',expand=True)
        self.notes=tk.Text(area,height=4,wrap='word'); sb=ttk.Scrollbar(area,command=self.notes.yview); self.notes.configure(yscrollcommand=sb.set); self.notes.pack(side='left',fill='both',expand=True); sb.pack(side='right',fill='y')
        actions=ttk.Frame(f); actions.pack(fill='x',pady=4)
        for label,cmd in [('Nova / limpar',self.new),('Salvar',self.save),('Excluir aberta',self.delete),('Prévia bibliográfica',self.preview)]:
            ttk.Button(actions,text=label,command=cmd).pack(side='left',fill='x',expand=True,padx=2)
        ttk.Button(f,text='Enviar referência ao Learn',command=self.send_reference).pack(anchor='w',pady=3)
        self.status=tk.StringVar(self.window); ttk.Label(f,textvariable=self.status,wraplength=600).pack(anchor='w')
        self.render()

    def values(self): return (self.title.get(),self.project.get(),self.kind.get(),self.authors.get(),self.year.get(),self.locator.get(),self.notes.get('1.0','end-1c'),self.state.get())
    def dirty(self):
        if self.selected_id is None: return self.values()!=('','Geral',KINDS[0],'','','','',STATES[0])
        try: r=self.store.get(self.selected_id)
        except KeyError: return True
        return self.values()!=(r.title,r.project,r.kind,r.authors,r.year,r.locator,r.notes,r.state)
    def discard_ok(self): return not self.dirty() or messagebox.askyesno('Descartar rascunho?','Alterações não salvas serão descartadas.',parent=self.window)
    def close(self):
        if self.discard_ok(): self.window.destroy()
    def set_editor(self,r=None):
        self.selected_id=r.id if r else None; self.editor_label.set('Editar referência' if r else 'Nova referência')
        for var,value in zip((self.title,self.project,self.kind,self.authors,self.year,self.locator,self.state), (r.title,r.project,r.kind,r.authors,r.year,r.locator,r.state) if r else ('','Geral',KINDS[0],'','','',STATES[0])): var.set(value)
        self.notes.delete('1.0','end')
        if r: self.notes.insert('1.0',r.notes)
    def new(self):
        if self.discard_ok(): self.set_editor(); self.status.set('Nova referência.')
    def load_selected(self):
        ids=self.tree.selection()
        if not ids: self.status.set('Selecione uma referência.'); return
        try: item=self.store.get(int(ids[0]))
        except KeyError: self.render(); self.status.set('Registro removido.'); return
        before=(self.selected_id,self.values())
        if not self.discard_ok() or not self.window.winfo_exists(): return
        try: same=self.store.get(item.id) is item
        except KeyError: same=False
        if not same or before!=(self.selected_id,self.values()) or self.tree.selection()!=ids:
            self.render(); self.status.set('Seleção alterada. Revise novamente.'); return
        self.set_editor(item); self.status.set('Referência aberta.')
    def clear_filters(self):
        self.query.set(''); self.project_filter.set(''); self.filter.set('Todos')
        self.render()

    def render(self):
        selected=self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        try: items=self.store.search(self.query.get(),self.project_filter.get(),None if self.filter.get()=='Todos' else self.filter.get())
        except ValueError as e: self.stats.set('Filtro inválido.'); self.status.set(str(e)); return
        for r in items: self.tree.insert('','end',iid=str(r.id),values=(r.title,r.project,r.kind,r.state))
        if selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected[0]); self.tree.focus(selected[0]); self.tree.see(selected[0])
        self.stats.set(f'{len(items)} exibidas / {len(self.store.list())} referências na sessão')
    def changed(self):
        self.render()
        if self.hub.alive(self.hub.privacy_window): self.hub.privacy_window.refresh()
    def save(self):
        try: r=self.store.add(*self.values()) if self.selected_id is None else self.store.edit(self.selected_id,*self.values())
        except (ValueError,KeyError) as e: self.status.set(str(e)); return
        self.set_editor(r); self.changed(); self.status.set('Referência salva somente na sessão.')
    def delete(self):
        if self.selected_id is None: self.status.set('Abra uma referência antes de excluir.'); return
        try: item=self.store.get(self.selected_id)
        except KeyError: self.render(); self.status.set('Registro removido.'); return
        draft=self.values()
        if not messagebox.askyesno('Excluir referência?','Excluir referência e anotações?',parent=self.window): return
        if not self.window.winfo_exists(): return
        try: same=self.store.get(item.id) is item
        except KeyError: same=False
        if not same or self.selected_id!=item.id or self.values()!=draft:
            self.render(); self.status.set('Registro alterado. Revise novamente.'); return
        self.store.delete(item.id); self.set_editor(); self.changed(); self.status.set('Referência excluída.')
    def preview(self):
        try: r=self.store.validated(0,*self.values())
        except ValueError as e: self.status.set(str(e)); return
        messagebox.showinfo('Prévia descritiva (não ABNT/APA)',r.bibliography(),parent=self.window)

    def send_reference(self):
        from aeris.study_integration_ui import send_reference
        try: changed=send_reference(self)
        except (ValueError,PermissionError,KeyError) as exc: self.status.set(str(exc)); return
        self.status.set("Tópico criado na sessão." if changed else "Operação cancelada.")
