"""Checked Security refinements: no new permissions, external endpoints or file writes."""
from pathlib import Path
import hashlib
import sys

def replace(s,old,new):
    if s.count(old)!=1: raise ValueError("Unexpected anchor: "+old[:100])
    return s.replace(old,new,1)

def apply(root):
    root=Path(root)/"aeris"
    hashes={
        "privacy_ui.py":"5c3a47d983af3f841414735874165562c6553a60f4beeb77d24f4dcf4fb2a8d2",
        "link_ui.py":"0ee9da6e5fcc000f6447ecef8fc75c379b284cf5b23dddaac91102f46a03ae42",
        "link.py":"398c655e31522a24913502206ae18a05727c20ebccb5d8c633c2ae1176ea4f81",
        "verify_ui.py":"001e8d95443a3e6cecccbf9262672426f4e9f14157aa151e63dad3def1d06a43",
        "permissions_ui.py":"a199b10d278564f261a0b672584f64a365cae4dc8cf5b81c5335720c3979eea2",
        "permissions.py":"225e8e3ee057cfb02ffefd5daa38d0df94e5701a52d801fa84db1b23fc921fe5",
        "metadata_ui.py":"ec8c5ffd9d1dab1217f15263c33b6f63748338e5274cfde894f90a08fd64186d",
    }
    files={}
    for name,expected in hashes.items():
        raw=(root/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected: raise ValueError("Unexpected RC4 source: "+name)
        files[name]=raw.decode("utf-8").replace("\r\n","\n")
    s=files["permissions.py"]
    s=replace(s,"        self._grants = set()","        self._grants = set()\n        self._revision = 0")
    s=replace(s,"    def allowed(self, capability):","    @property\n    def revision(self):\n        return self._revision\n\n    def allowed(self, capability):")
    s=replace(s,"        self._on_change()\n\n    def revoke_all(self):\n        if self._grants:", """        self._revision += 1
        self._on_change()

    def revoke_all(self):
        # Even an empty revocation cancels outstanding confirmation dialogs.
        self._revision += 1
        if self._grants:""")
    files["permissions.py"]=s
    s=files["permissions_ui.py"]
    s=replace(s,"        self.buttons = {}","        self.buttons = {}\n        self.summary=tk.StringVar(self.window)\n        self.status=tk.StringVar(self.window)\n        ttk.Label(frame,textvariable=self.summary).pack(anchor='w')\n        ttk.Label(frame,textvariable=self.status,wraplength=640).pack(anchor='w')")
    s=replace(s,"        for key, button in self.buttons.items():","        self.summary.set(f'{sum(self.hub.permissions.allowed(k) for k in CAPABILITIES)}/{len(CAPABILITIES)} acessos autorizados nesta sessão')\n        for key, button in self.buttons.items():")
    s=replace(s,"        granted = not self.hub.permissions.allowed(key)\n        if granted and not messagebox.askyesno('Autorizar acesso?', CAPABILITIES[key][1]+'\\n\\nApenas nesta sessão.', parent=self.window):\n            return\n        self.hub.permissions.set(key, granted)", """        permissions=self.hub.permissions
        granted=not permissions.allowed(key)
        reviewed=permissions.revision
        if granted and not messagebox.askyesno('Autorizar acesso?', CAPABILITIES[key][1]+'\\n\\nApenas nesta sessão.', parent=self.window):
            return
        if not self.window.winfo_exists(): return
        if permissions is not self.hub.permissions or reviewed!=permissions.revision:
            self.status.set('Permissões alteradas. Confirme novamente.'); self.refresh(); return
        permissions.set(key,granted)
        self.status.set('Acesso autorizado nesta sessão.' if granted else 'Acesso revogado.')""")
    files["permissions_ui.py"]=s
    s=files["privacy_ui.py"]
    s=replace(s,"        self.grants=tk.Listbox(permissions,exportselection=False)", """        self.granted_only=tk.BooleanVar(self.window,False)
        ttk.Checkbutton(permissions,text='Somente acessos autorizados',variable=self.granted_only,command=self.refresh).pack(anchor='w')
        self.grants=tk.Listbox(permissions,exportselection=False)""")
    s=replace(s,"        for name,allowed in grants: self.grants.insert('end',('Autorizado: ' if allowed else 'Negado: ')+name)","        for name,allowed in grants:\n            if not self.granted_only.get() or allowed: self.grants.insert('end',('Autorizado: ' if allowed else 'Negado: ')+name)")
    s=replace(s,"        self.set_preview(result.text); self.mask_status.set(f'{sum(n for _,n in result.counts)} padrões mascarados. Revise: não é anonimização garantida.')", """        self.set_preview(result.text)
        counts='; '.join(f'{name}: {n}' for name,n in result.counts)
        self.mask_status.set(f'{sum(n for _,n in result.counts)} padrões mascarados. {counts}. Revise: não é anonimização garantida.')""")
    s=replace(s,"        self.hub.lock_protected(); self.refresh(); self.status.set('Cofres bloqueados.')","        if not self.window.winfo_exists(): return\n        self.hub.lock_protected(); self.refresh(); self.status.set('Cofres bloqueados.')")
    files["privacy_ui.py"]=s
    s=files["link.py"]
    s=replace(s,"    return Inspection(canonical, p.scheme, tuple(notes))", """    if p.fragment:
        notes.append('Fragmento presente: pode conter parâmetros ou dados sensíveis; não compartilhe sem revisar.')
    if re.search(r'%(?![0-9a-fA-F]{2})',p.path+'?'+p.query+'#'+p.fragment):
        notes.append('Sequência percentual incompleta ou inválida; interpretação pode variar.')
    return Inspection(canonical, p.scheme, tuple(notes))""")
    files["link.py"]=s
    s=files["link_ui.py"]
    s=replace(s,"            lines.append('Indicadores para revisar:'); lines.extend('• '+note for note in result.indicators)","            lines.append(f'Indicadores para revisar: {len(result.indicators)} (não é pontuação de risco)'); lines.extend('• '+note for note in result.indicators)")
    s=replace(s,"    def clear(self): self.url.set('')","    def clear(self): self.url.set(''); self.entry.focus_set()")
    files["link_ui.py"]=s
    for name,permission in (("verify_ui.py","VERIFY_READ"),("metadata_ui.py","METADATA_READ")):
        s=files[name]
        s=replace(s,"self.job=None; self.timer=None; self.path=None","self.job=None; self.timer=None; self.path=None; self.revision=0; self.request=None")
        extra=",self.algorithm.get(),self.expected.get()" if name=="verify_ui.py" else ""
        s=replace(s,"    def show(self,text):","    def context(self): return (self.revision,self.path"+extra+")\n    def show(self,text):")
        s=replace(s,"        value=filedialog.askopenfilename","        reviewed=self.context(); permission_revision=self.hub.permissions.revision\n        value=filedialog.askopenfilename")
        s=replace(s,f"        if value and self.hub.permissions.allowed({permission}):",f"        if value and self.window.winfo_exists() and self.job is None and reviewed==self.context() and permission_revision==self.hub.permissions.revision and self.hub.permissions.allowed({permission}):")
        s=replace(s,"            self.path=value;","            self.revision+=1; self.path=value;")
        s=replace(s,"        if not messagebox.askyesno('Ler arquivo?',","        reviewed=self.context(); permission_revision=self.hub.permissions.revision\n        if not messagebox.askyesno('Ler arquivo?',")
        s=replace(s,f"        if not self.window.winfo_exists() or not self.path or not self.hub.permissions.allowed({permission}): return",f"        if not self.window.winfo_exists() or self.job or reviewed!=self.context() or permission_revision!=self.hub.permissions.revision or not self.hub.permissions.allowed({permission}): return\n        self.request=reviewed")
        s=replace(s,"        self.job=None; self.controls()\n        if event.is_set() or not self.hub.permissions.allowed("+permission+"): return","        self.job=None; reviewed=self.request; self.request=None; self.controls()\n        if event.is_set() or reviewed!=self.context() or not self.hub.permissions.allowed("+permission+"): return")
        s=replace(s,"        self.cancel(); self.path=None;","        self.revision+=1; self.cancel(); self.path=None;")
        files[name]=s
    s=files["verify_ui.py"]
    s=replace(s,"        for var in (self.algorithm,self.expected): trace_window(self.window, var, lambda *_:self.show('Resultado pendente.'))","        for var in (self.algorithm,self.expected): trace_window(self.window,var,self.options_changed)")
    s=replace(s,"    def context(self):","    def options_changed(self,*_):\n        self.revision+=1; self.cancel(); self.progress['value']=0; self.show('Opções alteradas. Calcule novamente.')\n    def context(self):")
    files["verify_ui.py"]=s
    s=files["metadata_ui.py"]
    s=replace(s,"self.revision=0; self.request=None","self.revision=0; self.request=None; self.result=None; self.result_context=None")
    s=replace(s,"        frame=ttk.Frame(f); frame.pack(fill='both',expand=True,pady=5)", """        self.hide_values=tk.BooleanVar(self.window,False)
        ttk.Checkbutton(f,text='Ocultar valores na tela',variable=self.hide_values,command=self.render_result).pack(anchor='w')
        frame=ttk.Frame(f); frame.pack(fill='both',expand=True,pady=5)""")
    s=replace(s,"    def show(self,text):\n        self.report.configure","    def show(self,text,keep=False):\n        if not keep: self.result=None; self.result_context=None\n        self.report.configure")
    s=replace(s,"        lines=[f'Formato reconhecido: {result.format}', '', *[f'{k}: {v}' for k,v in result.fields], *result.notes, '', 'Inspeção parcial: ausência de campos não significa ausência de metadados. Arquivo original preservado.']\n        self.show('\\n'.join(lines))", """        self.result=result; self.result_context=reviewed; self.render_result()
    def render_result(self):
        result=self.result
        if result is None: return
        if self.result_context!=self.context() or not self.hub.permissions.allowed(METADATA_READ):
            self.show('Resultado descartado.'); return
        hidden=self.hide_values.get()
        # Field labels can themselves contain user-provided PNG text keys.
        fields=[f'Campo {i}: [oculto]' if hidden else f'{k}: {v}' for i,(k,v) in enumerate(result.fields,1)]
        lines=[f'Formato reconhecido: {result.format}', f'Campos exibidos: {len(fields)}', '',
               *fields, *result.notes, '', 'Inspeção parcial: ausência de campos não significa ausência de metadados. Arquivo original preservado.']
        if hidden: lines.append('Ocultação apenas visual; dados permanecem na memória até limpar. Não altera o arquivo.')
        self.show('\\n'.join(lines),keep=True)""")
    files["metadata_ui.py"]=s
    for name,code in files.items(): compile(code,name,"exec")
    for name,code in files.items(): (root/name).write_bytes(code.encode("utf-8"))
    print("Security: seven verified original RC4 files refined")

if __name__=="__main__": apply(sys.argv[1])
