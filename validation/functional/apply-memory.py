"""Refine Memory UI on verified RC4 files; preserve schemas, storage and permissions."""
from pathlib import Path
import hashlib
import sys

def replace(s, old, new):
    if s.count(old) != 1:
        raise ValueError("Unexpected anchor: " + old[:100])
    return s.replace(old,new,1)

def apply(root):
    root=Path(root)/"aeris"
    hashes={
        "vault_ui.py":"143f5671eb6081e9bb3ce57a7e94434bdb311d35e1b35a8951596d703fc2c297",
        "editor.py":"6a04d9d49055e217b0dd31d6a0b21c123119c21166b1a1543ad5fa6f9e42c473",
        "timeline_ui.py":"cf00b5b6319e2dd06117ce6413ed5a4460caa3d26ddf4d6e625d4116350d1121",
        "ideas_ui.py":"4da882b406cabbec9114c4c6aecb57dd6ff4c940ee142f2a2b8e8c90c769d283",
        "bookmarks_ui.py":"ff6833a87ff1decf0f400850ba1834edacaab52b820f99d548009ea9e5cc5390",
    }
    files={}
    for name,expected in hashes.items():
        raw=(root/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected: raise ValueError("Unexpected RC4 file: "+name)
        files[name]=raw.decode("utf-8").replace("\r\n","\n")
    s=files["vault_ui.py"]
    s=replace(s,"        self.listbox.bind('<<ListboxSelect>>',self.select)", """        self.listbox.bind('<<ListboxSelect>>',self.select)
        self.count=tk.StringVar(self.window)
        ttk.Label(self.frame,textvariable=self.count).pack(anchor='w')""")
    s=replace(s,"        self.refresh()\n        from aeris.theme", """        self.window.bind('<Control-s>',self.keyboard_save)
        self.refresh()
        from aeris.theme""")
    s=replace(s,"    def values(self):", """    def keyboard_save(self,_=None):
        if self.vault.unlocked: self.save()
        return 'break'

    def values(self):""")
    s=replace(s,"        self.items=self.vault.list(); self.listbox.delete(0,'end')","        self.items=self.vault.list(); self.count.set(f'{len(self.items)} de 100 registros'); self.listbox.delete(0,'end')")
    s=replace(s,"            if item.id!=self.current and self.allow_discard(): self.fill(item)\n            else: self.refresh()", """            if item.id==self.current: return
            before=(self.current,self.values())
            if not self.allow_discard(): self.refresh(); return
            if not self.vault.unlocked or not self.window.winfo_exists(): return
            if before!=(self.current,self.values()) or not any(x is item for x in self.vault.list()):
                self.refresh(); return
            self.fill(item)""")
    s=replace(s,"        if self.current is None or not messagebox.askyesno('Excluir registro?', 'Excluir este registro do cofre? Não é apagamento seguro.',parent=self.window): return\n        try: self.vault.delete(self.current)", """        if not self.vault.unlocked or self.current is None: return
        item=next((x for x in self.vault.list() if x.id==self.current),None)
        if item is None: self.refresh(); return
        draft=self.values()
        if not messagebox.askyesno('Excluir registro?', 'Excluir este registro do cofre? Não é apagamento seguro.',parent=self.window): return
        if not self.vault.unlocked or not self.window.winfo_exists(): return
        if self.current!=item.id or self.values()!=draft or not any(x is item for x in self.vault.list()):
            self.refresh(); return
        try: self.vault.delete(item.id)""")
    s=replace(s,"        self.vault.lock()\n        if hasattr(self,'title'):","        self.window.unbind('<Control-s>')\n        self.vault.lock()\n        if hasattr(self,'count'): self.count.set('')\n        if hasattr(self,'title'):")
    files["vault_ui.py"]=s
    s=files["editor.py"]
    s=replace(s,"        self.status=tk.StringVar(self.window,'Textos não são gravados em disco.')","        self.window.bind('<Control-s>',self.keyboard_save)\n        self.status=tk.StringVar(self.window,'Textos não são gravados em disco.')")
    s=replace(s,"    def values(self):","""    def keyboard_save(self,_=None):
        self.save()
        return 'break'

    def values(self):""")
    s=replace(s,"            i=self.store.get(self.current); baseline=(i.title,i.category,i.body) if self.snippets else (i.title,i.body)","""            try: i=self.store.get(self.current)
            except KeyError: return True
            baseline=(i.title,i.category,i.body) if self.snippets else (i.title,i.body)""")
    s=replace(s,"                if self.allow_discard(): self.fill(i)\n                else: self.refresh()","""                before=(self.current,self.values())
                if not self.allow_discard(): self.refresh(); return
                if not self.window.winfo_exists(): return
                try: current_item=self.store.get(i.id)
                except KeyError: self.refresh(); self.status.set('Registro removido.'); return
                if current_item is not i or before!=(self.current,self.values()):
                    self.refresh(); self.status.set('Seleção alterada. Revise novamente.'); return
                self.fill(i)""")
    s=replace(s,"        except ValueError as exc: messagebox.showwarning(self.name,str(exc),parent=self.window); return","        except (ValueError,KeyError) as exc: messagebox.showwarning(self.name,str(exc),parent=self.window); return")
    s=replace(s,"        if self.current is not None and messagebox.askyesno('Excluir?','Remover o texto e as edições atuais? Cópias anteriores no clipboard podem permanecer.',parent=self.window):\n            self.store.delete(self.current); self.fill(); self.refresh()","""        if self.current is None: return
        try: item=self.store.get(self.current)
        except KeyError: self.refresh(); self.status.set('Registro removido.'); return
        draft=self.values()
        if not messagebox.askyesno('Excluir?','Remover o texto e as edições atuais? Cópias anteriores no clipboard podem permanecer.',parent=self.window): return
        if not self.window.winfo_exists(): return
        try: same=self.store.get(item.id) is item
        except KeyError: same=False
        if not same or self.current!=item.id or self.values()!=draft:
            self.refresh(); self.status.set('Seleção alterada. Revise novamente.'); return
        self.store.delete(item.id); self.fill(); self.refresh(); self.status.set('Texto removido.')""")
    files["editor.py"]=s
    for name,kind in (("timeline_ui.py","registro"),("ideas_ui.py","ideia")):
        s=files[name]
        if kind=="registro":
            s=replace(s,"        ttk.Button(f,text='Filtrar',command=self.render).pack(anchor='w')","""        filters=ttk.Frame(f); filters.pack(fill='x')
        ttk.Button(filters,text='Filtrar',command=self.render).pack(side='left')
        ttk.Button(filters,text='Limpar filtros',command=self.clear_filters).pack(side='left',padx=4)""")
            reset="        for var in (self.query,self.category_filter,self.day_from,self.day_to): var.set('')"
        else:
            s=replace(s,"        ttk.Button(filters,text='Filtrar',command=self.render).pack(side='left',padx=4)","""        ttk.Button(filters,text='Filtrar',command=self.render).pack(side='left',padx=4)
        ttk.Button(filters,text='Limpar',command=self.clear_filters).pack(side='left')""")
            reset="        self.query.set(''); self.filter.set('Todos')"
        s=replace(s,"    def render(self):\n        self.tree.delete(*self.tree.get_children())","    def clear_filters(self):\n"+reset+"\n        self.render()\n\n    def render(self):\n        selected=self.tree.selection()\n        self.tree.delete(*self.tree.get_children())")
        marker="        self.stats.set(f'{len(items)} exibidos" if kind=="registro" else "        self.stats.set(f'{len(items)} exibidas"
        s=replace(s,marker,"        if selected and self.tree.exists(selected[0]):\n            self.tree.selection_set(selected[0]); self.tree.focus(selected[0]); self.tree.see(selected[0])\n"+marker)
        original="        if self.discard_ok(): self.set_editor(self.store.get(int(ids[0]))); self.status.set('Registro aberto para edição.')" if kind=="registro" else "        if self.discard_ok(): self.set_editor(self.store.get(int(ids[0]))); self.status.set('Ideia aberta para edição.')"
        s=replace(s,original,"""        try: item=self.store.get(int(ids[0]))
        except KeyError: self.render(); self.status.set('Registro removido.'); return
        before=(self.selected_id,self.values())
        if not self.discard_ok(): return
        if not self.window.winfo_exists(): return
        try: same=self.store.get(item.id) is item
        except KeyError: same=False
        if not same or before!=(self.selected_id,self.values()) or self.tree.selection()!=ids:
            self.render(); self.status.set('Seleção alterada. Revise novamente.'); return
        self.set_editor(item); self.status.set('Aberto para edição.')""")
        old="        if not messagebox.askyesno('Excluir registro?', 'Excluir o registro aberto e seu rascunho?',parent=self.window): return\n        self.store.delete(self.selected_id); self.set_editor(); self.changed(); self.status.set('Registro excluído.')" if kind=="registro" else "        if not messagebox.askyesno('Excluir ideia?', 'Excluir a ideia aberta e seu rascunho?',parent=self.window): return\n        self.store.delete(self.selected_id); self.set_editor(); self.changed(); self.status.set('Ideia excluída.')"
        s=replace(s,old,"""        try: item=self.store.get(self.selected_id)
        except KeyError: self.render(); self.status.set('Registro removido.'); return
        draft=self.values()
        if not messagebox.askyesno('Excluir?', 'Excluir o registro aberto e seu rascunho?',parent=self.window): return
        if not self.window.winfo_exists(): return
        try: same=self.store.get(item.id) is item
        except KeyError: same=False
        if not same or self.selected_id!=item.id or self.values()!=draft:
            self.render(); self.status.set('Seleção alterada. Revise novamente.'); return
        self.store.delete(item.id); self.set_editor(); self.changed(); self.status.set('Registro excluído.')""")
        files[name]=s
    s=files["bookmarks_ui.py"]
    s=replace(s,"        item=self.store.get(self.current); return self.values()!=(item.title,item.category,item.url)","        try: item=self.store.get(self.current)\n        except KeyError: return True\n        return self.values()!=(item.title,item.category,item.url)")
    s=replace(s,"        if self.current is None or not messagebox.askyesno('Excluir?','Excluir link salvo?',parent=self.window): return\n        try: self.store.delete(self.current)","""        if self.current is None or not self.store.unlocked: return
        try: item=self.store.get(self.current)
        except KeyError: self.refresh(); return
        draft=self.values()
        if not messagebox.askyesno('Excluir?','Excluir link salvo?',parent=self.window): return
        if not self.window.winfo_exists() or not self.store.unlocked: return
        try: same=self.store.get(item.id)==item
        except KeyError: same=False
        if not same or self.current!=item.id or self.values()!=draft:
            self.refresh(); self.status.set('Seleção alterada. Revise novamente.'); return
        try: self.store.delete(item.id)""")
    s=replace(s,"        try: self.store.open(item.id)","""        if not self.window.winfo_exists() or not self.store.unlocked or not self.hub.permissions.allowed(OPEN_BOOKMARK): return
        try: same=self.store.get(item.id)==item
        except KeyError: same=False
        if not same or self.current!=item.id or self.dirty():
            self.refresh(); self.status.set('Endereço alterado. Revise novamente.'); return
        try: self.store.open(item.id)""")
    files["bookmarks_ui.py"]=s
    for name,code in files.items(): compile(code,name,"exec")
    for name,code in files.items(): (root/name).write_bytes(code.encode("utf-8"))
    print("Memory: five original RC4 files verified and refined")

if __name__=="__main__": apply(sys.argv[1])
