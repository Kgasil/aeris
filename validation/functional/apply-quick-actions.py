"""Checked Quick Actions refinement, cumulative after the Memory editor overlay."""
from pathlib import Path
import hashlib
import sys

def replace(s,old,new):
    if s.count(old)!=1: raise ValueError("Unexpected anchor: "+old[:100])
    return s.replace(old,new,1)

def apply(root):
    root=Path(root)/"aeris"
    hashes={
        "autofill_ui.py":"e2bf3bfc7e3e7aefb89deb602266093d35335b2d9d49a95ba0dfe53923c93ffc",
        "clipboard_ui.py":"9a3a8328a470e345ecbe42456531fcb8d2e6493277c8a431a5b402b8367d8f0a",
        "editor.py":"c586176f792c0b23cc12bf6d3e4cb43aedde761d0f40b047e791e799a1f9612e",
        "expand_ui.py":"3c65b36d7b1a3ced1a9ca75dfe7f20db71701169e19dfd531691c6fb2bb5003a",
        "convert_ui.py":"8c02801105e64270d1f58da762b623776f3719a51e04c8383d5e7c379be76511",
    }
    files={}
    for name,expected in hashes.items():
        raw=(root/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected: raise ValueError("Unexpected input source: "+name)
        files[name]=raw.decode("utf-8").replace("\r\n","\n")
    s=files["autofill_ui.py"]
    s=replace(s,"        self.requested={k:tk.BooleanVar(self.window,True) for k in FIELDS}","        self.requested={k:tk.BooleanVar(self.window,False) for k in FIELDS}")
    s=replace(s,"        ttk.Button(self.frame,text='Revisar campos salvos'", """        ttk.Button(self.frame,text='Limpar seleção de campos',command=self.clear_fields).pack(fill='x')
        ttk.Button(self.frame,text='Revisar campos salvos'""")
    s=replace(s,"    def values(self):","""    def clear_fields(self):
        for var in self.requested.values(): var.set(False)
        self.clear_preview()

    def values(self):""")
    s=replace(s,"        item=self.store.get(self.current) if self.current is not None else None","        try: item=self.store.get(self.current) if self.current is not None else None\n        except KeyError: return True")
    s=replace(s,"        if self.current is None or not messagebox.askyesno('Excluir?','Excluir o perfil salvo?',parent=self.window): return\n        try: self.store.delete(self.current)", """        if self.current is None or not self.store.unlocked: return
        try: item=self.store.get(self.current)
        except KeyError: self.refresh(); return
        draft=self.values()
        if not messagebox.askyesno('Excluir?','Excluir o perfil salvo?',parent=self.window): return
        if not self.window.winfo_exists() or not self.store.unlocked: return
        try: same=self.store.get(item.id)==item
        except KeyError: same=False
        if not same or self.current!=item.id or self.values()!=draft:
            self.refresh(); self.clear_preview(); self.status.set('Perfil alterado. Revise novamente.'); return
        try: self.store.delete(item.id)""")
    s=replace(s,"        for key,val in self.preview_rows: self.preview_items.insert('end',f'{FIELDS[key]}: {val}')","""        if not self.preview_rows:
            self.status.set('Selecione ao menos um campo preenchido.'); return
        for key,val in self.preview_rows: self.preview_items.insert('end',f'{FIELDS[key]}: {val}')""")
    s=replace(s,"        key,shown=self.preview_rows[selection[0]]","""        if selection[0]>=len(self.preview_rows): return
        profile=self.store.get(self.current)
        reviewed=self.preview_rows
        fields=tuple(k for k,v in self.requested.items() if v.get())
        key,shown=reviewed[selection[0]]
        if key not in fields: self.clear_preview(); return""")
    s=replace(s,"        if not self.store.unlocked or self.current is None or self.dirty(): return\n        try:\n            value=self.store.copy_value(self.current,key)", """        if not self.window.winfo_exists() or not self.store.unlocked: return
        if self.current!=profile.id or self.preview_rows is not reviewed or self.preview_items.curselection()!=selection or tuple(k for k,v in self.requested.items() if v.get())!=fields or self.dirty():
            self.clear_preview(); self.status.set('Prévia alterada. Revise novamente.'); return
        try:
            if self.store.get(profile.id)!=profile: self.clear_preview(); return
            value=self.store.copy_value(profile.id,key)""")
    files["autofill_ui.py"]=s
    s=files["clipboard_ui.py"]
    s=replace(s,"        ttk.Entry(frame, textvariable=self.query).pack(fill='x')","""        search=ttk.Entry(frame,textvariable=self.query); search.pack(fill='x')
        self.window.bind('<Control-f>',lambda _:search.focus_set())
        self.pinned_only=tk.BooleanVar(self.window,False)
        ttk.Checkbutton(frame,text='Somente fixados',variable=self.pinned_only,command=self.refresh).pack(anchor='w')""")
    s=replace(s,"        self.visible = self.store.list(self.query.get())","""        selected=self.selected() if hasattr(self,'visible') else None
        self.visible=tuple(c for c in self.store.list(self.query.get()) if not self.pinned_only.get() or c.pinned)""")
    s=replace(s,"        self.preview()\n\n    def preview","""        if selected:
            for i,c in enumerate(self.visible):
                if c.id==selected.id: self.items.selection_set(i); self.items.see(i); break
        self.preview()

    def preview""")
    s=replace(s,"        return self.visible[selection[0]] if selection else None","        return self.visible[selection[0]] if selection and selection[0]<len(self.visible) else None")
    s=replace(s,"        try: self.store.copy(item.id, self.write)\n        except (tk.TclError, PermissionError):","""        if not self.window.winfo_exists(): return
        if self.selected() is not item or not any(c is item for c in self.store.list()):
            self.refresh(); self.status.set('Seleção alterada. Revise novamente.'); return
        try: self.store.copy(item.id, self.write)
        except (tk.TclError, PermissionError, StopIteration):""")
    s=replace(s,"        if item and messagebox.askyesno('Excluir?', 'Remover somente do histórico do Aeris?', parent=self.window):\n            self.store.delete(item.id); self.refresh()","""        if item and messagebox.askyesno('Excluir?', 'Remover somente do histórico do Aeris?', parent=self.window):
            if not self.window.winfo_exists(): return
            if self.selected() is not item or not any(c is item for c in self.store.list()):
                self.refresh(); self.status.set('Seleção alterada. Revise novamente.'); return
            self.store.delete(item.id); self.refresh()""")
    s=replace(s,"        if messagebox.askyesno('Limpar?',","        reviewed=self.store.list()\n        if messagebox.askyesno('Limpar?',")
    s=replace(s,"            self.store.clear(); self.query.set(''); self.refresh();","""            if not self.window.winfo_exists(): return
            if self.store.list()!=reviewed: self.refresh(); self.status.set('Histórico alterado. Confirme novamente.'); return
            self.store.clear(); self.query.set(''); self.refresh();""")
    files["clipboard_ui.py"]=s
    s=files["editor.py"]
    s=replace(s,"        if not messagebox.askyesno('Copiar texto?',","        reviewed=self.store.get(self.current)\n        if not messagebox.askyesno('Copiar texto?',")
    s=replace(s,"        if not self.permissions.allowed(COPY_SNIPPETS): return\n        try:\n            self.parent.clipboard_clear(); self.parent.clipboard_append(self.store.get(self.current).body)", """        if not self.window.winfo_exists() or not self.permissions.allowed(COPY_SNIPPETS): return
        try: same=self.store.get(reviewed.id) is reviewed
        except KeyError: same=False
        if not same or self.current!=reviewed.id or self.dirty():
            self.refresh(); self.status.set('Texto alterado. Revise novamente.'); return
        try:
            self.parent.clipboard_clear(); self.parent.clipboard_append(reviewed.body)""")
    files["editor.py"]=s
    s=files["expand_ui.py"]
    s=replace(s,"        self.set_result(None); self.source=None;","        self.set_result(None); self.source=None; self.reviewed_rules=None;")
    s=replace(s,"        self.source=self.original(); self.set_result(result);","        self.source=self.original(); self.reviewed_rules=self.store.list(); self.set_result(result);")
    s=replace(s,"    def copy(self):\n        if self.output is None or self.original()!=self.source or not self.hub.permissions.allowed(COPY_EXPAND): return","""    def copy(self):
        if self.output is None or self.original()!=self.source or self.store.list()!=self.reviewed_rules or not self.hub.permissions.allowed(COPY_EXPAND): return
        reviewed=self.output""")
    s=replace(s,"        if self.output is None or self.original()!=self.source or not self.hub.permissions.allowed(COPY_EXPAND): return","""        if not self.window.winfo_exists() or not self.hub.permissions.allowed(COPY_EXPAND): return
        if self.output is not reviewed or self.original()!=self.source or self.store.list()!=self.reviewed_rules:
            self.invalidate(); self.status.set('Prévia ou regras alteradas. Expanda novamente.'); return""")
    s=replace(s,"        if selected and messagebox.askyesno('Excluir regra?','Remover esta abreviação da sessão?',parent=self.window):\n            self.store.delete(self.rows[selected[0]][0]); self.refresh(); self.invalidate()","""        if not selected: return
        code,value=self.rows[selected[0]]
        if messagebox.askyesno('Excluir regra?','Remover esta abreviação da sessão?',parent=self.window):
            if not self.window.winfo_exists(): return
            if self.items.curselection()!=selected or dict(self.store.list()).get(code)!=value:
                self.refresh(); self.invalidate(); self.status.set('Regra alterada. Revise novamente.'); return
            self.store.delete(code); self.refresh(); self.invalidate()""")
    files["expand_ui.py"]=s
    s=files["convert_ui.py"]
    s=replace(s,"        ttk.Button(buttons,text='Limpar',command=self.clear).pack(side='left',fill='x',expand=True)","""        ttk.Button(buttons,text='Limpar',command=self.clear).pack(side='left',fill='x',expand=True)
        self.reverse_button=ttk.Button(f,text='Usar resultado na conversão inversa',command=self.reverse_result)
        self.reverse_button.pack(fill='x',pady=(0,4))""")
    s=replace(s,"        for v in (self.amount,self.source,self.target):","        for v in (self.amount,self.source,self.target,self.category):")
    s=replace(s,"    def invalidate(self,*_):self.result.set('');self.status.set('')","""    def invalidate(self,*_):
        self.last_result=None; self.result.set(''); self.status.set('')
        self.reverse_button.configure(state='disabled')

    def reverse_result(self):
        if self.last_result is None: return
        value=format(self.last_result.value,'f')
        if len(value)>64:
            self.status.set('Resultado excede o limite de entrada para inverter.'); return
        a,b=self.source.get(),self.target.get()
        self.source.set(b); self.target.set(a); self.amount.set(value)
        self.run()""")
    s=replace(s,"        self.result.set(format_value(r.value)+' '+r.unit);self.status.set(r.explanation)","""        self.last_result=r
        self.result.set(format_value(r.value)+' '+r.unit);self.status.set(r.explanation)
        self.reverse_button.configure(state='normal')""")
    files["convert_ui.py"]=s
    for name,code in files.items(): compile(code,name,"exec")
    for name,code in files.items(): (root/name).write_bytes(code.encode("utf-8"))
    # Autofill intentionally requires explicit field selection now; adapt only the
    # existing smoke setup, preserving its copy and permission assertions.
    smoke=root.parent/"tests"/"smoke_autofill.py"
    raw=smoke.read_bytes()
    if hashlib.sha256(raw).hexdigest()!="22a1b1436515b08d7ddcfae05ba86b9dc596eae5811afe2237249880c424c3a7":
        raise ValueError("Unexpected Autofill smoke")
    code=replace(raw.decode("utf-8").replace("\r\n","\n"),"ui.save(); ui.show_preview()","ui.save(); ui.requested['name'].set(True); ui.show_preview()")
    compile(code,"smoke_autofill.py","exec")
    smoke.write_bytes(code.encode("utf-8"))
    print("Quick Actions: four RC4 files and cumulative Memory editor refined")

if __name__=="__main__": apply(sys.argv[1])
