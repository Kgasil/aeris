"""Refine five Learning modules on the verified RC4 source, preserving storage and limits."""
from pathlib import Path
import hashlib
import sys

def replace(s,old,new):
    if s.count(old)!=1: raise ValueError("Unexpected anchor: "+old[:100])
    return s.replace(old,new,1)

def apply(root):
    root=Path(root)/"aeris"
    hashes={
        "learn_ui.py":"b502055fc82373a7b1302d6ce88d743128f02497d0c8eb69f736f19c2e3a32fc",
        "research_ui.py":"f1a53d8eb5d27955d1ee651c16d280879e2f85e6e8ac52fdb485ce6323128ab4",
        "flashcards_ui.py":"01bdf4ca972829385a45cba35f7b999e7c2ebb776f74f6fe698facbfe7a4dfae",
        "pronounce_ui.py":"9cc0949cffd03da56a6ad15659e3fb58daba253bb834679604757508ef190ced",
        "accessibility_ui.py":"1333b4f927d467bc6f791ca7220b029c086dd2f83862d4617cbbe77ebd94a198",
    }
    files={}
    for name,expected in hashes.items():
        raw=(root/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected: raise ValueError("Unexpected RC4 source: "+name)
        files[name]=raw.decode("utf-8").replace("\r\n","\n")
    s=files["learn_ui.py"]
    s=replace(s,"        self.progress=ttk.Progressbar(f,maximum=100); self.progress.pack(fill='x',pady=6)", """        self.progress=ttk.Progressbar(f,maximum=100); self.progress.pack(fill='x',pady=6)
        self.pending_only=tk.BooleanVar(self.window,False)
        ttk.Checkbutton(f,text='Somente tópicos pendentes',variable=self.pending_only,command=self.render).pack(anchor='w')""")
    s=replace(s,"        i=self.selector.current(); plans=self.store.list()\n        if not 0<=i<len(plans): raise ValueError('Selecione ou crie uma trilha.')\n        return plans[i].id", """        i=self.selector.current()
        if 0<=i<len(self.plan_rows):
            ident,title=self.plan_rows[i]
            try: plan=self.store.get(ident)
            except KeyError: plan=None
            if plan is not None and plan.title==title==self.selector.get(): return ident
        raise ValueError('Selecione ou crie uma trilha.')""")
    s=replace(s,"        self.refresh()\n\n    def plan_id", "        self.plan_rows=()\n        self.refresh()\n\n    def plan_id")
    s=replace(s,"        self.selector.configure(values=[p.title for p in plans])","        self.plan_rows=tuple((p.id,p.title) for p in plans)\n        self.selector.configure(values=[p.title for p in plans])")
    s=replace(s,"self.window.geometry('720x500'); self.window.minsize(570,420)","self.window.geometry('760x540'); self.window.minsize(640,460)")
    s=replace(s,"        self.tree.delete(*self.tree.get_children()); done=total=used=planned=0", """        selected=self.tree.selection()
        if topic_id is None and selected: topic_id=selected[0]
        self.tree.delete(*self.tree.get_children()); done=total=used=planned=0""")
    s=replace(s,"            for t in p.topics: self.tree.insert('','end',iid=str(t.id),values=(t.title,t.minutes,'Concluído' if t.done else 'Pendente'))", """            for t in p.topics:
                if self.pending_only.get() and t.done: continue
                self.tree.insert('','end',iid=str(t.id),values=(t.title,t.minutes,'Concluído' if t.done else 'Pendente'))""")
    s=replace(s,"        if topic_id is not None and self.tree.exists(str(topic_id)): self.tree.selection_set(str(topic_id))", """        if topic_id is not None and self.tree.exists(str(topic_id)):
            self.tree.selection_set(str(topic_id)); self.tree.focus(str(topic_id)); self.tree.see(str(topic_id))

    def require_plan(self,p,topic_id=None):
        if not self.window.winfo_exists() or not self.hub.enabled('Learn'):
            raise ValueError('Trilha indisponível.')
        if self.plan_id()!=p.id or self.store.get(p.id) is not p or (topic_id is not None and self.selected()!=topic_id):
            raise ValueError('Trilha ou tópico alterado. Revise novamente.')""")
    s=replace(s,"            self.store.rename(p.id,title); self.refresh(p.id)", "            self.require_plan(p); self.store.rename(p.id,title); self.refresh(p.id)")
    s=replace(s,"            p=self.plan_id()\n            if not messagebox.askyesno('Excluir trilha?'","            p=self.store.get(self.plan_id())\n            if not messagebox.askyesno('Excluir trilha?'")
    s=replace(s,"            self.store.delete_plan(p); self.refresh()", "            self.require_plan(p); self.store.delete_plan(p.id); self.refresh()")
    s=replace(s,"            p=self.plan_id(); fields=self.topic_fields()\n            if fields is None: return False\n            self.render(self.store.add(p,*fields).id)", """            p=self.store.get(self.plan_id()); fields=self.topic_fields()
            if fields is None: return False
            self.require_plan(p); self.render(self.store.add(p.id,*fields).id)""")
    s=replace(s,"            p=self.plan_id(); i=self.selected(); t=next((t for t in self.store.get(p).topics if t.id==i),None)", "            p=self.store.get(self.plan_id()); i=self.selected(); t=next((t for t in p.topics if t.id==i),None)")
    s=replace(s,"            self.store.edit(p,i,*fields); self.render(i)", "            self.require_plan(p,i); self.store.edit(p.id,i,*fields); self.render(i)")
    s=replace(s,"            p=self.plan_id(); i=self.selected()\n            if not messagebox.askyesno('Excluir tópico?'","            p=self.store.get(self.plan_id()); i=self.selected()\n            if not messagebox.askyesno('Excluir tópico?'")
    s=replace(s,"            self.store.delete_topic(p,i); self.render()", "            self.require_plan(p,i); self.store.delete_topic(p.id,i); self.render()")
    # A modal dialog can destroy the window via a global session clear.
    s=replace(s,"        except (KeyError,ValueError,PermissionError) as exc: self.status.set(str(exc) if isinstance(exc,(ValueError,PermissionError)) else 'Registro não encontrado.'); return", """        except (KeyError,ValueError,PermissionError,tk.TclError) as exc:
            if self.window.winfo_exists(): self.status.set(str(exc) if isinstance(exc,(ValueError,PermissionError)) else 'Registro não encontrado.')
            return
        if not self.window.winfo_exists(): return""")
    files["learn_ui.py"]=s
    for name,kind,filter_line in (
        ("research_ui.py","referência","        self.query.set(''); self.project_filter.set(''); self.filter.set('Todos')"),
        ("flashcards_ui.py","cartão","        self.query.set(''); self.deck_filter.set(''); self.due_only.set(False)"),
    ):
        s=files[name]
        label="Filtrar" if kind=="referência" else "Atualizar"
        s=replace(s,f"        ttk.Button(bar,text='{label}',command=self.render).pack(side='left')",f"""        ttk.Button(bar,text='{label}',command=self.render).pack(side='left')
        ttk.Button(bar,text='Limpar filtros',command=self.clear_filters).pack(side='left',padx=2)""")
        s=replace(s,"    def render(self):\n        self.tree.delete(*self.tree.get_children())","    def clear_filters(self):\n"+filter_line+"\n        self.render()\n\n    def render(self):\n        selected=self.tree.selection()\n        self.tree.delete(*self.tree.get_children())")
        marker="        self.stats.set(f'{len(items)} exibidas" if kind=="referência" else "        self.stats.set(f'{len(items)} exibidos"
        s=replace(s,marker,"        if selected and self.tree.exists(selected[0]):\n            self.tree.selection_set(selected[0]); self.tree.focus(selected[0]); self.tree.see(selected[0])\n"+marker)
        old="        if self.discard_ok(): self.set_editor(self.store.get(int(ids[0]))); self.status.set('Referência aberta.')" if kind=="referência" else "        if self.discard_ok(): self.set_editor(self.store.get(int(ids[0]))); self.tabs.select(self.edit_tab)"
        end="self.status.set('Referência aberta.')" if kind=="referência" else "self.tabs.select(self.edit_tab)"
        s=replace(s,old,"""        try: item=self.store.get(int(ids[0]))
        except KeyError: self.render(); self.status.set('Registro removido.'); return
        before=(self.selected_id,self.values())
        if not self.discard_ok() or not self.window.winfo_exists(): return
        try: same=self.store.get(item.id) is item
        except KeyError: same=False
        if not same or before!=(self.selected_id,self.values()) or self.tree.selection()!=ids:
            self.render(); self.status.set('Seleção alterada. Revise novamente.'); return
        self.set_editor(item); """+end)
        confirm="        if not messagebox.askyesno('Excluir referência?','Excluir referência e anotações?',parent=self.window): return" if kind=="referência" else "        if not messagebox.askyesno('Excluir cartão?','Excluir cartão e seu progresso?',parent=self.window): return"
        s=replace(s,confirm,"""        try: item=self.store.get(self.selected_id)
        except KeyError: self.render(); self.status.set('Registro removido.'); return
        draft=self.values()
"""+confirm+"""
        if not self.window.winfo_exists(): return
        try: same=self.store.get(item.id) is item
        except KeyError: same=False
        if not same or self.selected_id!=item.id or self.values()!=draft:
            self.render(); self.status.set('Registro alterado. Revise novamente.'); return""")
        s=replace(s,"        self.store.delete(self.selected_id); self.set_editor(); self.changed();","        self.store.delete(item.id); self.set_editor(); self.changed();")
        files[name]=s
    s=files["flashcards_ui.py"]
    s=replace(s,"        self.revealed = False","        self.revealed = False; self.reviewed_card=None")
    s=replace(s,"        self.review_id=None; self.revealed=False; self.show_review('');","        self.review_id=None; self.revealed=False; self.reviewed_card=None; self.show_review('');")
    s=replace(s,"        c=items[0]; self.review_id=c.id; self.show_review(c.question);","        c=items[0]; self.review_id=c.id; self.reviewed_card=c; self.show_review(c.question);")
    s=replace(s,"    def reveal(self):\n        if self.review_id is None: return\n        c=self.store.get(self.review_id);", """    def current_review(self):
        if self.review_id is None: return None
        try: c=self.store.get(self.review_id)
        except KeyError: c=None
        if c is None or c is not self.reviewed_card or c.due>self.store.now():
            self.clear_review(); self.status.set('Cartão alterado ou indisponível. Inicie nova revisão.'); return None
        return c

    def reveal(self):
        c=self.current_review()
        if c is None: return
       """)
    s=replace(s,"        if self.review_id is None or not self.revealed: return\n        try: c=self.store.review(self.review_id,rating)", """        if not self.revealed: return
        reviewed=self.current_review()
        if reviewed is None: return
        try: c=self.store.review(reviewed.id,rating)""")
    files["flashcards_ui.py"]=s
    s=files["pronounce_ui.py"]
    s=replace(s,"from aeris.pronounce import LANGUAGES, EXERCISES, practice_payload","from aeris.pronounce import LANGUAGES, EXERCISES, practice_payload\nfrom aeris.window_lifecycle import trace_window")
    s=replace(s,"        lang.bind('<<ComboboxSelected>>',self.language_changed)\n","")
    s=replace(s,"        self.play_button.configure(text='Ouvir exercício')\n        self.permissions_changed()", """        self.play_button.configure(text='Ouvir exercício')
        trace_window(self.window,self.language,self.language_changed)
        self.permissions_changed()""")
    s=replace(s,"    def language_changed(self,event=None):","    def language_changed(self,*_):")
    s=replace(s,"        self.voices=data; self.choice.configure(values=data); self.voice.set(data[0] if data else 'Nenhuma voz compatível')", """        selected=self.voice.get()
        self.voices=data; self.choice.configure(values=data)
        self.voice.set(selected if selected in data else data[0] if data else 'Nenhuma voz compatível')""")
    files["pronounce_ui.py"]=s
    s=files["accessibility_ui.py"]
    s=replace(s,"        self.position=tk.StringVar(w); ttk.Label(nav,textvariable=self.position).pack(side='left',padx=4)", """        self.first=ttk.Button(nav,text='Primeira',command=lambda:self.jump(False)); self.first.pack(side='left',padx=2)
        self.last=ttk.Button(nav,text='Última',command=lambda:self.jump(True)); self.last.pack(side='left',padx=2)
        self.position=tk.StringVar(w); ttk.Label(nav,textvariable=self.position).pack(side='left',padx=4)""")
    s=replace(s,"        opt=ReadingOptions(self.size.get(),self.palette.get(),self.spacious.get(),self.guide.get()); bg,fg,mark,markfg=PALETTES[opt.palette]", """        try: opt=ReadingOptions(self.size.get(),self.palette.get(),self.spacious.get(),self.guide.get())
        except (ValueError,tk.TclError) as exc: self.status.set(str(exc)); return
        bg,fg,mark,markfg=PALETTES[opt.palette]""")
    s=replace(s,"        self.prev.configure(state='normal' if enabled and n>1 else 'disabled'); self.next.configure(state='normal' if enabled and n<self.reader.lines else 'disabled')", """        self.prev.configure(state='normal' if enabled and n>1 else 'disabled'); self.next.configure(state='normal' if enabled and n<self.reader.lines else 'disabled')
        self.first.configure(state='normal' if enabled and n>1 else 'disabled')
        self.last.configure(state='normal' if enabled and n<self.reader.lines else 'disabled')
    def jump(self,last):
        if self.guide.get() and self.reader.lines:
            self.reader.line=self.reader.lines if last else 1; self.refresh_guide()
        return 'break'""")
    s=replace(s,"    def confirm_clear(self):\n        if not self.dirty() or messagebox.askyesno('Limpar leitura?', 'Descartar texto e prévia?',parent=self.window): self.clear()\n    def close(self):\n        if not self.dirty() or messagebox.askyesno('Fechar leitura?', 'Descartar texto e prévia?',parent=self.window): self.window.destroy()", """    def snapshot(self): return (self.source.get('1.0','end-1c'),self.reader.text)
    def discard_confirmed(self,title):
        reviewed=self.snapshot()
        if self.dirty() and not messagebox.askyesno(title,'Descartar texto e prévia?',parent=self.window): return False
        if not self.window.winfo_exists(): return False
        if reviewed!=self.snapshot():
            self.status.set('Texto alterado. Confirme novamente.'); return False
        return True
    def confirm_clear(self):
        if self.discard_confirmed('Limpar leitura?'): self.clear()
    def close(self):
        if self.discard_confirmed('Fechar leitura?'): self.window.destroy()""")
    files["accessibility_ui.py"]=s
    for name,code in files.items(): compile(code,name,"exec")
    for name,code in files.items(): (root/name).write_bytes(code.encode("utf-8"))
    print("Learning: five RC4 files verified and refined")

if __name__=="__main__": apply(sys.argv[1])
