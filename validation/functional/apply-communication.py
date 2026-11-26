"""Refine Communication UI against independently identified RC4 inputs."""
from pathlib import Path
import hashlib
import sys

def replace(s, old, new):
    if s.count(old)!=1: raise ValueError("Unexpected anchor: "+old[:100])
    return s.replace(old,new,1)

def apply(root):
    root=Path(root)/"aeris"
    hashes={
        "translate_ui.py":"49c42b37ef2edc1247afb7bc8b7c11e64bad64960374d6eea817b43f8a29cce5",
        "voice_ui.py":"cdcc1e584609c2a28d6b6b824d6b861eb269a07fdada47c3235c66558059d3ce",
        "text_ui.py":"c88e7ff4faeaba3a942ece1ade47c1412ce5c569473415964919b910fe47ba84",
        "email_ui.py":"8d5369722e5742a7ecf6eca42e5a696da9504fe539025016d8099979ef2b3985",
        "meeting_ui.py":"e1237ad4ee86c1f979deb8866acde251117c5ec69009b30ce8e8a2dd54650ffc",
    }
    files={}
    for name,expected in hashes.items():
        raw=(root/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected: raise ValueError("Unexpected RC4 source: "+name)
        files[name]=raw.decode("utf-8").replace("\r\n","\n")
    s=files["translate_ui.py"]
    s=replace(s,"self.job=0; self.output=''","self.job=0; self.output=''; self.snapshot=None; self.request=None; self.result_generation=0")
    s=replace(s,"        self.refresh_examples()\n    def refresh_examples","""        self.refresh_examples()
        for var in (self.source,self.target,self.mode): trace_window(self.window,var,self.invalidate)
        self.input.bind('<<Modified>>',self.modified); self.input.edit_modified(False)

    def context(self):
        return (self.input.get('1.0','end-1c'),self.source.get(),self.target.get(),self.mode.get())

    def modified(self,_=None):
        if self.input.edit_modified():
            self.input.edit_modified(False); self.invalidate()

    def invalidate(self,*_):
        self.cancel(); self.set_result(''); self.status.set('Entrada alterada. Traduza novamente.')

    def refresh_examples""")
    s=replace(s,"        self.output=text; self.result.configure","        self.result_generation+=1; self.snapshot=self.context() if text else None\n        self.output=text; self.result.configure")
    s=replace(s,"        self.cancel(); self.set_result('')\n        codes=", "        self.cancel(); self.set_result(''); self.input.edit_modified(False)\n        request=self.context(); generation=self.job\n        codes=")
    s=replace(s,"        try:\n            flags=subprocess.CREATE_NO_WINDOW", """        if not self.window.winfo_exists() or self.context()!=request or self.job!=generation: return
        self.request=request
        try:
            flags=subprocess.CREATE_NO_WINDOW""")
    s=replace(s,"            if res.get('ok') is True and isinstance(res.get('text'),str):", """            if self.request!=self.context():
                self.set_result(''); self.status.set('Entrada alterada. Traduza novamente.'); return
            if isinstance(res,dict) and res.get('ok') is True and isinstance(res.get('text'),str):""")
    s=replace(s,"        self.job+=1\n        if self.timer", "        self.job+=1; self.request=None\n        if self.timer")
    s=replace(s,"        if not self.output or not self.hub.permissions.allowed(COPY_TRANSLATION): return\n        if not messagebox", """        if not self.output or not self.hub.permissions.allowed(COPY_TRANSLATION): return
        if self.snapshot!=self.context(): self.invalidate(); return
        reviewed=self.output; generation=self.result_generation
        if not messagebox""")
    s=replace(s,"        if not self.hub.permissions.allowed(COPY_TRANSLATION): return\n        try: self.hub.root.clipboard_clear(); self.hub.root.clipboard_append(self.output)", """        if not self.window.winfo_exists() or not self.hub.permissions.allowed(COPY_TRANSLATION): return
        if self.result_generation!=generation or self.snapshot!=self.context() or self.output!=reviewed:
            self.invalidate(); return
        try: self.hub.root.clipboard_clear(); self.hub.root.clipboard_append(reviewed)""")
    files["translate_ui.py"]=s
    s=files["voice_ui.py"]
    s=replace(s,"        self.text=tk.Text(f,height=6,wrap='word'); self.text.pack(fill='both',expand=True,pady=6)", """        self.text=tk.Text(f,height=6,wrap='word',undo=True); self.text.pack(fill='both',expand=True,pady=6)
        self.count=tk.StringVar(self.window,'0 caracteres')
        ttk.Label(f,textvariable=self.count).pack(anchor='w')
        self.text.bind('<<Modified>>',self.update_count); self.text.edit_modified(False)""")
    s=replace(s,"    def permissions_changed(self):", """    def update_count(self,_=None):
        if self.text.edit_modified():
            self.text.edit_modified(False)
            self.count.set(f"{len(self.text.get('1.0','end-1c'))} caracteres")

    def permissions_changed(self):""")
    s=replace(s,"        except ValueError as e: self.status.set(str(e)); return","        except (ValueError,tk.TclError) as e: self.status.set(str(e)); return")
    s=replace(s,"        self.voices=data; self.choice.configure(values=('Voz padrão do Windows',*data)); self.voice.set('Voz padrão do Windows'); self.status.set(f'{len(data)} vozes instaladas encontradas.')", """        selected=self.voice.get()
        self.voices=data; self.choice.configure(values=('Voz padrão do Windows',*data))
        self.voice.set(selected if selected in data else 'Voz padrão do Windows')
        self.status.set(f'{len(data)} vozes instaladas encontradas.')""")
    s=replace(s,"    def clear(self): self.stop(); self.text.delete('1.0','end'); self.status.set('Texto removido da sessão.')", """    def clear(self):
        self.stop(); self.text.delete('1.0','end'); self.text.edit_reset(); self.text.edit_modified(False)
        self.count.set('0 caracteres'); self.status.set('Texto removido da sessão.')""")
    files["voice_ui.py"]=s
    s=files["text_ui.py"]
    s=replace(s,"self.output=None; self.pending=None;","self.output=None; self.result_context=None; self.result_generation=0; self.pending=None;")
    s=replace(s,"    def set_result(self,value):", """    def context(self):
        return (self.original(),self.operation.get(),self.language.get(),self.mode.get(),self.dictionary[self.language.get()])

    def set_result(self,value):
        self.result_generation+=1
        self.result_context=self.context() if value is not None else None""")
    s=replace(s,"        if self.output is None or not self.hub.permissions.allowed(COPY_TEXT): return\n        if not messagebox", """        if self.output is None or not self.hub.permissions.allowed(COPY_TEXT): return
        if self.result_context!=self.context() or (self.ai_preview and not self.hub.permissions.allowed(TEXT_AI)):
            self.invalidate(); return
        reviewed=self.output; generation=self.result_generation
        if not messagebox""")
    s=replace(s,"        if self.output is None or not self.hub.permissions.allowed(COPY_TEXT): return\n        try: self.hub.root.clipboard_clear(); self.hub.root.clipboard_append(self.output)", """        if not self.window.winfo_exists() or not self.hub.permissions.allowed(COPY_TEXT): return
        if self.result_generation!=generation or self.result_context!=self.context() or self.output!=reviewed or (self.ai_preview and not self.hub.permissions.allowed(TEXT_AI)):
            self.invalidate(); return
        try: self.hub.root.clipboard_clear(); self.hub.root.clipboard_append(reviewed)""")
    s=replace(s,"        if self.reviewed is None or self.original()!=self.reviewed[0]: self.invalidate(); return","        if self.reviewed is None or self.original()!=self.reviewed[0] or self.result_context!=self.context(): self.invalidate(); return")
    files["text_ui.py"]=s
    s=files["email_ui.py"]
    s=replace(s,"        ttk.Button(buttons,text='Limpar',command=self.clear).pack(side='left')","""        ttk.Button(buttons,text='Limpar',command=self.clear).pack(side='left')
        self.copy_full=ttk.Button(f,text='Copiar assunto e mensagem',command=lambda:self.copy('full'))
        self.copy_full.pack(fill='x',pady=(4,0))""")
    s=replace(s,"        self.copy_subject.configure(state=state); self.copy_body.configure(state=state)","        self.copy_subject.configure(state=state); self.copy_body.configure(state=state); self.copy_full.configure(state=state)")
    s=replace(s,"        if part not in ('subject','body') or self.draft is None or self.snapshot!=self.values() or not self.hub.permissions.allowed(COPY_EMAIL): return","""        if part not in ('subject','body','full') or self.draft is None or self.snapshot!=self.values() or not self.hub.permissions.allowed(COPY_EMAIL): return
        reviewed=self.draft; snapshot=self.snapshot
        payload=('Assunto: '+reviewed.subject+'\\n\\n'+reviewed.body) if part=='full' else getattr(reviewed,part)""")
    s=replace(s,"        if self.draft is None or self.snapshot!=self.values() or not self.hub.permissions.allowed(COPY_EMAIL): return\n        try: self.hub.root.clipboard_clear(); self.hub.root.clipboard_append(getattr(self.draft,part))","""        if not self.window.winfo_exists() or not self.hub.permissions.allowed(COPY_EMAIL): return
        if self.draft is not reviewed or self.snapshot!=snapshot or snapshot!=self.values():
            self.invalidate(); self.status.set('Rascunho alterado. Gere novamente.'); return
        try: self.hub.root.clipboard_clear(); self.hub.root.clipboard_append(payload)""")
    files["email_ui.py"]=s
    s=files["meeting_ui.py"]
    s=replace(s,"        ttk.Button(row,text='Pesquisar',command=self.render).pack(side='left'); ttk.Button(row,text='Abrir selecionada',command=self.load).pack(side='left')","""        ttk.Button(row,text='Pesquisar',command=self.render).pack(side='left'); ttk.Button(row,text='Limpar busca',command=self.clear_search).pack(side='left')
        ttk.Button(row,text='Abrir selecionada',command=self.load).pack(side='left')""")
    s=replace(s,"        item=self.store.get(self.selected_id) if self.selected_id is not None else None","        try: item=self.store.get(self.selected_id) if self.selected_id is not None else None\n        except KeyError: return True")
    s=replace(s,"    def render(self):\n        try: items=", """    def clear_search(self):
        self.query.set(''); self.render()

    def render(self):
        selected=self.tree.selection()
        try: items=""")
    s=replace(s,"        for m in items: self.tree.insert('','end',iid=str(m.id),values=(m.title,m.day or '—',f'{m.completed}/{len(m.actions)}'))","""        for m in items: self.tree.insert('','end',iid=str(m.id),values=(m.title,m.day or '—',f'{m.completed}/{len(m.actions)}'))
        if selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected[0]); self.tree.focus(selected[0]); self.tree.see(selected[0])""")
    s=replace(s,"        if ids and self.discard_ok(): self.set_editor(self.store.get(int(ids[0]))); self.status.set('Reunião aberta.')","""        if not ids: return
        try: item=self.store.get(int(ids[0]))
        except KeyError: self.render(); self.status.set('Reunião removida.'); return
        before=(self.selected_id,self.values(),self.action_fields(),self.editing_action)
        if not self.discard_ok() or not self.window.winfo_exists(): return
        try: same=self.store.get(item.id) is item
        except KeyError: same=False
        if not same or self.tree.selection()!=ids or before!=(self.selected_id,self.values(),self.action_fields(),self.editing_action):
            self.render(); self.status.set('Seleção alterada. Revise novamente.'); return
        self.set_editor(item); self.status.set('Reunião aberta.')""")
    s=replace(s,"        except ValueError as exc: self.status.set(str(exc)); return\n        self.set_editor(item); self.refresh()","        except (ValueError,KeyError) as exc: self.status.set(str(exc)); return\n        self.set_editor(item); self.refresh()")
    s=replace(s,"        if self.selected_id is not None and messagebox.askyesno('Excluir reunião?','Excluir reunião salva e rascunho?',parent=self.window):\n            self.store.delete(self.selected_id); self.set_editor(); self.refresh(); self.status.set('Reunião excluída.')","""        if self.selected_id is None: return
        try: item=self.store.get(self.selected_id)
        except KeyError: self.render(); self.status.set('Reunião removida.'); return
        before=(self.values(),self.action_fields(),self.editing_action)
        if not messagebox.askyesno('Excluir reunião?','Excluir reunião salva e rascunho?',parent=self.window): return
        if not self.window.winfo_exists(): return
        try: same=self.store.get(item.id) is item
        except KeyError: same=False
        if not same or self.selected_id!=item.id or before!=(self.values(),self.action_fields(),self.editing_action):
            self.render(); self.status.set('Reunião alterada. Revise novamente.'); return
        self.store.delete(item.id); self.set_editor(); self.refresh(); self.status.set('Reunião excluída.')""")
    s=replace(s,"        if i is not None and messagebox.askyesno('Excluir atividade?','Excluir atividade do rascunho?',parent=self.window): self.actions.pop(i); self.clear_action_fields(); self.render_actions(); self.close_preview()","""        if i is None: return
        reviewed=tuple(self.actions); selected_id=self.selected_id
        if not messagebox.askyesno('Excluir atividade?','Excluir atividade do rascunho?',parent=self.window): return
        if not self.window.winfo_exists(): return
        if self.selected_id!=selected_id or tuple(self.actions)!=reviewed or self.action_index()!=i or self.editing_action is not None or any(self.action_fields()):
            self.status.set('Atividade alterada. Revise novamente.'); return
        self.actions.pop(i); self.clear_action_fields(); self.render_actions(); self.close_preview()""")
    files["meeting_ui.py"]=s
    for name,code in files.items(): compile(code,name,"exec")
    for name,code in files.items(): (root/name).write_bytes(code.encode("utf-8"))
    print("Communication: five RC4 files verified and refined")

if __name__=="__main__": apply(sys.argv[1])
