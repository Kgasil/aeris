"""Checked Intelligence refinement; no new capabilities or external endpoints."""
from pathlib import Path
import hashlib
import sys

def replace(s,old,new):
    if s.count(old)!=1: raise ValueError("Unexpected anchor: "+old[:100])
    return s.replace(old,new,1)

def apply(root):
    root=Path(root)/"aeris"
    hashes={
        "copilot_ui.py":"52274242779c72640d2020d38dc826600612a7d555a4ba77f4ed6662856da197",
        "companion_ui.py":"57e10293ff9ea1432a2708d365899843323aaebbee8cb935950df831d5eefd79",
        "context_ui.py":"de3f863fba8cf5fda30ba33c14cd18dc8d29211ad519ba16c7fa7733324099bc",
        "interview_ui.py":"767082d0705e71849d9abc6db3f45d3a07e448aae919c9b8da4b8130bfcc9d7e",
        "search_ui.py":"eb23ec3d511aed1b44fa5da0b207b53320d8209a9ae1b99bc2434e2e5ca8aea7",
        "debug_ui.py":"45b7f733433c768e73bc3f30fec0f38d0080cb0cac58fa4a0f62e2ab987b9f0c",
        "hub.py":"e0a7a2b5a79ab30cc3b6d9cacbf42ee4e22def22eab9a2e0aa7c685ac1bcc61f",
    }
    files={}
    for name,expected in hashes.items():
        raw=(root/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected: raise ValueError("Unexpected input: "+name)
        files[name]=raw.decode("utf-8").replace("\r\n","\n")
    s=files["copilot_ui.py"]
    s=replace(s,"        ttk.Entry(f,textvariable=self.command).pack(fill='x',pady=8)", """        self.entry=ttk.Entry(f,textvariable=self.command); self.entry.pack(fill='x',pady=8)
        self.count=tk.StringVar(w,'0 / 500 caracteres'); ttk.Label(f,textvariable=self.count).pack(anchor='w')
        self.entry.bind('<Return>',self.keyboard_prepare)
        self.entry.focus_set()""")
    s=replace(s,"    def invalidate(self,*_):\n        self.session.cancel()", """    def keyboard_prepare(self,_=None):
        self.prepare()
        return 'break'
    def invalidate(self,*_):
        self.session.cancel()
        if hasattr(self,'count'): self.count.set(f'{len(self.command.get())} / 500 caracteres')""")
    files["copilot_ui.py"]=s
    s=files["companion_ui.py"]
    s=replace(s,"        self.input=tk.Text(f,wrap='word',height=4); self.input.pack(fill='x',pady=5)", """        self.input=tk.Text(f,wrap='word',height=4); self.input.pack(fill='x',pady=5)
        self.count=tk.StringVar(w,'0 / 4000 caracteres')
        ttk.Label(f,textvariable=self.count).pack(anchor='w')
        self.input.bind('<<Modified>>',self.input_changed); self.input.edit_modified(False)
        self.input.bind('<Control-Return>',self.keyboard_send)""")
    s=replace(s,"    def model_changed(self,*_): self.clear()", """    def input_changed(self,_=None):
        if not self.input.edit_modified(): return
        self.input.edit_modified(False)
        text=self.input.get('1.0','end-1c')
        self.count.set(f'{len(text)} / 4000 caracteres')
        if self.candidate and self.candidate[0]!=text:
            self.discard_candidate(); self.refresh()
    def keyboard_send(self,_=None):
        self.send()
        return 'break'
    def model_changed(self,*_):
        # Changing model invalidates history and any pending operation, not the unsent draft.
        self.stop(); self.history.clear(); self.draw()
        self.status.set('Modelo alterado. Histórico limpo; texto não enviado preservado.')
        self.refresh()""")
    files["companion_ui.py"]=s
    s=files["context_ui.py"]
    s=replace(s,"        self.tree.bind('<Double-1>',lambda _:self.load_selected())", """        self.tree.bind('<Double-1>',self.open_row)
        self.tree.bind('<Return>',lambda _: (self.load_selected(),'break')[1])""")
    s=replace(s,"    def load_selected(self):\n        ids=self.tree.selection()\n        if ids and self.discard_ok(): self.set_editor(self.store.get(int(ids[0])))", """    def open_row(self,event):
        row=self.tree.identify_row(event.y)
        if row and self.tree.identify_region(event.x,event.y) in ('cell','tree'):
            self.tree.selection_set(row); self.load_selected()
        return 'break'
    def load_selected(self):
        ids=self.tree.selection()
        if not ids: return
        try: item=self.store.get(int(ids[0]))
        except KeyError: self.changed(); return
        draft=(self.selected_id,self.values())
        if not self.discard_ok() or not self.window.winfo_exists(): return
        try: same=self.store.get(item.id) is item
        except KeyError: same=False
        if not same or self.tree.selection()!=ids or draft!=(self.selected_id,self.values()):
            self.changed(); self.status.set('Registro alterado. Revise novamente.'); return
        self.set_editor(item)""")
    s=replace(s,"        self.tree.delete(*self.tree.get_children())\n        for item in self.store.list(): self.tree.insert('','end',iid=str(item.id),values=(item.title,item.category,'Sim' if self.store.selected(item.id) else 'Não'))", """        selected=self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for item in self.store.list(): self.tree.insert('','end',iid=str(item.id),values=(item.title,item.category,'Sim' if self.store.selected(item.id) else 'Não'))
        if selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected[0]); self.tree.focus(selected[0]); self.tree.see(selected[0])""")
    s=replace(s,"        if messagebox.askyesno('Excluir registro?', 'Excluir registro e rascunho?',parent=self.window):\n            self.store.delete(self.selected_id); self.set_editor(); self.changed(); self.status.set('Registro excluído.')", """        try: item=self.store.get(self.selected_id)
        except KeyError: self.changed(); return
        draft=self.values()
        if not messagebox.askyesno('Excluir registro?', 'Excluir registro e rascunho?',parent=self.window): return
        if not self.window.winfo_exists(): return
        try: same=self.store.get(item.id) is item
        except KeyError: same=False
        if not same or self.selected_id!=item.id or draft!=self.values():
            self.changed(); self.status.set('Registro alterado. Revise novamente.'); return
        self.store.delete(item.id); self.set_editor(); self.changed(); self.status.set('Registro excluído.')""")
    s=replace(s,"        item_id=int(ids[0]); include=not self.store.selected(item_id)\n        if include and not messagebox.askyesno('Incluir contexto?', 'Autorizar este registro salvo na prévia local?',parent=self.window): return\n        try: self.store.select(item_id,include)", """        item_id=int(ids[0]); include=not self.store.selected(item_id)
        try: item=self.store.get(item_id)
        except KeyError: self.changed(); return
        if include and not self.hub.permissions.allowed(CONTEXT_PREVIEW):
            self.status.set('Autorize a prévia primeiro.'); return
        if include and not messagebox.askyesno('Incluir contexto?', 'Autorizar este registro salvo na prévia local?',parent=self.window): return
        if not self.window.winfo_exists(): return
        try: same=self.store.get(item_id) is item
        except KeyError: same=False
        if not same or self.tree.selection()!=ids or self.store.selected(item_id)==include:
            self.changed(); self.status.set('Registro ou seleção alterados. Revise novamente.'); return
        try: self.store.select(item_id,include)""")
    files["context_ui.py"]=s
    s=files["interview_ui.py"]
    s=replace(s,"        self.next=ttk.Button(row,text='Próxima',command=lambda:self.move(1)); self.next.pack(side='left',padx=3)", """        self.next=ttk.Button(row,text='Próxima',command=lambda:self.move(1)); self.next.pack(side='left',padx=3)
        self.pending=ttk.Button(f,text='Próxima pergunta sem resposta nesta área',command=self.next_unanswered); self.pending.pack(anchor='w')""")
    # The row is packed before the new control; no data leaves the session.
    s=replace(s,"        if new not in AREAS or not self.discard_ok(): self.area.set(self.current_area); return\n        self.current_area=new; self.index=0; self.render()", """        if new not in AREAS or not self.navigation_ok():
            if self.window.winfo_exists(): self.area.set(self.current_area)
            return
        if self.area.get()!=new: self.area.set(self.current_area); return
        self.current_area=new; self.index=0; self.render()""")
    s=replace(s,"    def move(self,delta):\n        if 0<=self.index+delta<len(self.questions()) and self.discard_ok(): self.index+=delta; self.render()", """    def navigation_ok(self):
        before=(self.current().id,self.values(),self.store.get(self.current().id))
        if not self.discard_ok() or not self.window.winfo_exists(): return False
        if before!=(self.current().id,self.values(),self.store.get(self.current().id)):
            self.status.set('Resposta alterada. Confirme novamente.'); return False
        return True
    def move(self,delta):
        target=self.index+delta
        if 0<=target<len(self.questions()) and self.navigation_ok():
            self.index=target; self.render()
    def next_unanswered(self):
        qs=self.questions()
        indices=[(self.index+i)%len(qs) for i in range(1,len(qs)+1)]
        target=next((i for i in indices if self.store.get(qs[i].id) is None),None)
        if target is None: self.status.set('Todas as perguntas desta área têm resposta salva.'); return
        if target==self.index: self.status.set('Esta pergunta ainda não tem resposta salva.'); return
        if self.navigation_ok() and self.store.get(qs[target].id) is None:
            self.index=target; self.render()""")
    s=replace(s,"        if messagebox.askyesno('Limpar resposta?', 'Descartar resposta salva e rascunho desta pergunta?',parent=self.window):\n            self.store.delete(self.current().id); self.render(); self.refresh_privacy()", """        q=self.current().id; draft=self.values(); item=self.store.get(q)
        if not messagebox.askyesno('Limpar resposta?', 'Descartar resposta salva e rascunho desta pergunta?',parent=self.window): return
        if not self.window.winfo_exists(): return
        if self.current().id!=q or self.values()!=draft or self.store.get(q) is not item:
            self.status.set('Resposta alterada. Confirme novamente.'); return
        self.store.delete(q); self.render(); self.refresh_privacy()""")
    s=replace(s,"        if self.discard_ok(): self.window.destroy()","        if self.navigation_ok(): self.window.destroy()")
    files["interview_ui.py"]=s
    s=files["search_ui.py"]
    s=replace(s,"        self.entry.pack(fill='x', pady=6)", """        self.entry.pack(fill='x', pady=6)
        ttk.Button(frame,text='Limpar busca',command=self.clear_query).pack(anchor='w')
        self.entry.bind('<Return>',self.focus_results)""")
    s=replace(s,"    def on_focus(self, event):", """    def clear_query(self):
        self.query.set(''); self.entry.focus_set()
    def focus_results(self,_=None):
        if self.results:
            self.items.focus_set()
            if not self.items.curselection(): self.items.selection_set(0)
            self.preview()
        return 'break'
    def selected(self):
        selection=self.items.curselection()
        return self.results[selection[0]] if selection and selection[0]<len(self.results) else None
    def on_focus(self, event):""")
    s=replace(s,"        hub = self.hub\n        allowed = {'Ferramentas'}","        hub = self.hub\n        selected=self.selected() if hasattr(self,'results') else None\n        allowed = {'Ferramentas'}")
    s=replace(s,"        self.status.set(f'{len(self.results)} resultado(s)'", """        if selected in self.results:
            index=self.results.index(selected); self.items.selection_set(index); self.items.see(index)
        self.status.set(f'{len(self.results)} resultado(s)'""")
    s=replace(s,"        selection = self.items.curselection()\n        self.detail.configure", "        result=self.selected()\n        self.detail.configure")
    s=replace(s,"        if selection:\n            result = self.results[selection[0]]", "        if result is not None:")
    s=replace(s,"        self.button.configure(state='normal' if selection else 'disabled')","        self.button.configure(state='normal' if result is not None else 'disabled')")
    s=replace(s,"        selection = self.items.curselection()\n        if not selection:\n            return\n        result = self.results[selection[0]]\n        if self.hub.open_search_result(result):\n            self.window.destroy()", """        result=self.selected()
        if result is None: return 'break'
        self.refresh()
        if self.selected()!=result:
            self.status.set('Resultado alterado. Pesquise novamente.'); return 'break'
        if self.hub.open_search_result(result):
            if self.window.winfo_exists(): self.window.destroy()
        elif self.window.winfo_exists():
            self.refresh(); self.status.set('Resultado indisponível ou abertura cancelada.')
        return 'break'""")
    files["search_ui.py"]=s
    s=files["hub.py"]
    s=replace(s,"        self.open_tool(result.source); editor=getattr(self,key+'_window')\n        if editor.current!=item.id:\n            if not editor.allow_discard(): return False\n            editor.fill(item)", """        if (item.title,item.body,getattr(item,'category','Anotação'))!=(result.title,result.body,result.category): return False
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
            editor.fill(item)""")
    files["hub.py"]=s
    s=files["debug_ui.py"]
    s=replace(s,"        self.analysis=None; self.status=tk.StringVar(w)", "        self.analysis=None; self.snapshot=None; self.diagnostic_index=-1; self.status=tk.StringVar(w)")
    s=replace(s,"        ttk.Button(row,text='Ir ao primeiro diagnóstico',command=self.goto).pack(side='left',padx=5)", """        ttk.Button(row,text='Primeiro diagnóstico',command=self.goto).pack(side='left',padx=5)
        self.next_button=ttk.Button(row,text='Próximo',command=lambda:self.goto(True),state='disabled'); self.next_button.pack(side='left')""")
    s=replace(s,"        self.analysis=None; self.status.set(''); self.display('')","        self.analysis=None; self.snapshot=None; self.diagnostic_index=-1; self.next_button.configure(state='disabled'); self.status.set(''); self.display('')")
    s=replace(s,"        r=self.analysis\n        self.status.set", """        r=self.analysis
        self.snapshot=self.source.get('1.0','end-1c')
        self.next_button.configure(state='normal' if r.diagnostics else 'disabled')
        self.status.set""")
    s=replace(s,"    def goto(self):\n        if self.source.edit_modified(): self.changed(); return\n        if self.analysis and self.analysis.diagnostics:\n            d=self.analysis.diagnostics[0]; pos=f'{d.line}.{d.column-1}'; self.source.mark_set('insert',pos); self.source.see(pos); self.source.focus_set()", """    def goto(self,advance=False):
        if self.source.edit_modified() or self.snapshot!=self.source.get('1.0','end-1c'):
            self.source.edit_modified(False); self.invalidate(); return
        if self.analysis and self.analysis.diagnostics:
            ds=self.analysis.diagnostics
            self.diagnostic_index=(self.diagnostic_index+1)%len(ds) if advance else 0
            d=ds[self.diagnostic_index]; pos=f'{d.line}.{d.column-1}'
            self.source.mark_set('insert',pos); self.source.see(pos); self.source.focus_set()
            self.status.set(f'Diagnóstico {self.diagnostic_index+1}/{len(ds)} · Linha {d.line}, coluna {d.column}')""")
    s=replace(s,"        if self.dirty() and not messagebox.askyesno('Limpar código?', 'Descartar código e diagnóstico?',parent=self.window): return\n        self.source.delete('1.0','end'); self.source.edit_modified(False); self.invalidate()\n    def close(self):\n        if not self.dirty() or messagebox.askyesno('Fechar Debug?', 'Descartar código e diagnóstico?',parent=self.window): self.window.destroy()", """        if not self.discard_confirmed('Limpar código?'): return
        self.source.delete('1.0','end'); self.source.edit_modified(False); self.invalidate()
    def discard_confirmed(self,title):
        reviewed=self.source.get('1.0','end-1c')
        if reviewed and not messagebox.askyesno(title,'Descartar código e diagnóstico?',parent=self.window): return False
        if not self.window.winfo_exists(): return False
        if reviewed!=self.source.get('1.0','end-1c'):
            self.status.set('Código alterado. Confirme novamente.'); return False
        return True
    def close(self):
        if self.discard_confirmed('Fechar Debug?'): self.window.destroy()""")
    s=replace(s,"        if event.widget is self.window: self.analysis=None; self.status.set('')","        if event.widget is self.window: self.analysis=None; self.snapshot=None; self.status.set('')")
    files["debug_ui.py"]=s
    for name,code in files.items(): compile(code,name,"exec")
    for name,code in files.items(): (root/name).write_bytes(code.encode("utf-8"))
    print("Intelligence: six RC4 files and cumulative Hub verified and refined")

if __name__=="__main__": apply(sys.argv[1])
