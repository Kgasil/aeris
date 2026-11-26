"""Checked Files refinements, retaining read-only originals and bounded readers."""
from pathlib import Path
import hashlib
import sys

def replace(s,old,new):
    if s.count(old)!=1: raise ValueError("Unexpected anchor: "+old[:100])
    return s.replace(old,new,1)

def apply(root):
    root=Path(root)/"aeris"
    hashes={
        "documents_ui.py":"6d821b08114f2fde9e114bb3a8b458d5753b0f11785cedf854152e677ea9e3ce",
        "organizer_ui.py":"3bb9c203e8335d80cd3583915487891cfc4f85779f39704af5843379f27fec0b",
        "drop_ui.py":"73b751ade9f1793ef08d358f886c495bde7ebc36d1e004ac7396bc19ee456df9",
        "compare_ui.py":"946deb5218318f8011491f63794508ca1f157721d14b1340445e4f68db3353e0",
        "lens_ui.py":"138ce83175fcd8c451a17d00a565b0d0deff2777fd238034f7f824486641a57a",
    }
    files={}
    for name,expected in hashes.items():
        raw=(root/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected: raise ValueError("Unexpected RC4 source: "+name)
        files[name]=raw.decode("utf-8").replace("\r\n","\n")
    # Bind selection dialogs and worker results to the exact reviewed UI state.
    # Core file readers retain their own existing local path and during-read checks.
    for name,permission in (("documents_ui.py","DOCUMENTS_READ"),("organizer_ui.py","ORGANIZER_SCAN"),("lens_ui.py","LENS_READ")):
        s=files[name]
        s=replace(s,"self.job=None; self.timer=None; self.path=None","self.job=None; self.timer=None; self.path=None; self.revision=0; self.request=None")
        extra=",self.language.get()" if name=="lens_ui.py" else ""
        s=replace(s,"    def show(self,text):","    def context(self): return (self.revision,self.path"+extra+")\n    def show(self,text):")
        marker="        value=filedialog."
        s=replace(s,marker,"        reviewed=self.context()\n"+marker)
        old=f"        if value and self.hub.permissions.allowed({permission}):" if name!="lens_ui.py" else f"        if value and self.window.winfo_exists() and self.hub.permissions.allowed({permission}):"
        s=replace(s,old,f"        if value and self.window.winfo_exists() and self.job is None and reviewed==self.context() and self.hub.permissions.allowed({permission}):")
        s=replace(s,"            self.path=value;", "            self.revision+=1; self.path=value;")
        if name=="lens_ui.py":
            s=replace(s,"        selected=(self.path,self.language.get())","        selected=(self.path,self.language.get()); reviewed=self.context()")
            s=replace(s,"        if not self.window.winfo_exists() or selected!=(self.path,self.language.get()) or not self.hub.permissions.allowed(LENS_READ): return", "        if not self.window.winfo_exists() or self.job or reviewed!=self.context() or not self.hub.permissions.allowed(LENS_READ): return\n        self.request=reviewed")
        else:
            s=replace(s,"        if not messagebox.askyesno(","        reviewed=self.context()\n        if not messagebox.askyesno(")
            s=replace(s,f"        if not self.window.winfo_exists() or not self.path or not self.hub.permissions.allowed({permission}): return",f"        if not self.window.winfo_exists() or self.job or reviewed!=self.context() or not self.hub.permissions.allowed({permission}): return\n        self.request=reviewed")
        s=replace(s,"        self.job=None; self.controls()\n        if event.is_set() or not self.hub.permissions.allowed("+permission+"): return","        self.job=None; reviewed=self.request; self.request=None; self.controls()\n        if event.is_set() or reviewed!=self.context() or not self.hub.permissions.allowed("+permission+"): return")
        s=replace(s,"        self.cancel(); self.path=None;", "        self.revision+=1; self.cancel(); self.path=None;")
        files[name]=s
    s=files["documents_ui.py"]
    s=replace(s,"        frame=ttk.Frame(f); frame.pack(fill='both',expand=True,pady=5)", """        find=ttk.Frame(f); find.pack(fill='x')
        self.query=tk.StringVar(self.window)
        entry=ttk.Entry(find,textvariable=self.query); entry.pack(side='left',fill='x',expand=True)
        ttk.Button(find,text='Localizar próxima',command=self.find_next).pack(side='left',padx=3)
        self.find_status=tk.StringVar(self.window)
        ttk.Label(f,textvariable=self.find_status).pack(anchor='w')
        entry.bind('<Return>',lambda _:self.find_next())
        self.window.bind('<Control-f>',lambda _:entry.focus_set())
        self.match_end='1.0'; self.last_query=''
        frame=ttk.Frame(f); frame.pack(fill='both',expand=True,pady=5)""")
    s=replace(s,"    def show(self,text):\n        self.report.configure", """    def find_next(self):
        query=self.query.get()
        self.report.tag_remove('found','1.0','end')
        if not self.hub.permissions.allowed(DOCUMENTS_READ) or not query or len(query)>500:
            self.find_status.set('Informe até 500 caracteres para localizar.'); return 'break'
        start=self.match_end if query==self.last_query else '1.0'
        count=tk.IntVar(self.window)
        pos=self.report.search(query,start,stopindex='end',nocase=True,regexp=False,count=count)
        if not pos and start!='1.0':
            pos=self.report.search(query,'1.0',stopindex='end',nocase=True,regexp=False,count=count)
        self.last_query=query
        if not pos or count.get()<=0:
            self.find_status.set('Nenhuma ocorrência.'); self.match_end='1.0'; return 'break'
        self.match_end=self.report.index(f'{pos}+{count.get()}c')
        self.report.tag_add('found',pos,self.match_end); self.report.tag_configure('found',background='#F5DC80',foreground='#202020')
        self.report.see(pos); self.find_status.set(f'Ocorrência na linha {pos.split(".")[0]}.')
        return 'break'
    def show(self,text):
        self.match_end='1.0'; self.last_query=''; self.find_status.set('')
        self.report.configure""")
    s=replace(s,"        self.revision+=1; self.cancel(); self.path=None;","        self.query.set(''); self.revision+=1; self.cancel(); self.path=None;")
    files["documents_ui.py"]=s
    s=files["organizer_ui.py"]
    s=replace(s,"self.revision=0; self.request=None","self.revision=0; self.request=None; self.inventory=None")
    s=replace(s,"        frame=ttk.Frame(f); frame.pack(fill='both',expand=True,pady=5)", """        order=ttk.Frame(f); order.pack(fill='x')
        ttk.Label(order,text='Ordenar:').pack(side='left')
        self.order=tk.StringVar(self.window,'Categoria')
        box=ttk.Combobox(order,textvariable=self.order,values=('Categoria','Maior tamanho','Nome'),state='readonly')
        box.pack(side='left',fill='x',expand=True,padx=4)
        box.bind('<<ComboboxSelected>>',lambda _:self.render_inventory())
        frame=ttk.Frame(f); frame.pack(fill='both',expand=True,pady=5)""")
    s=replace(s,"    def show(self,text):\n        self.report.configure", """    def show(self,text,keep=False):
        if not keep: self.inventory=None
        self.report.configure""")
    s=replace(s,"        lines=[f'Arquivos listados: {len(result.files)} | Entradas ignoradas: {result.skipped}', 'Sugestão por categoria (não cria pastas nem move arquivos).']", """        self.inventory=result; self.render_inventory()
    def render_inventory(self):
        result=self.inventory
        if result is None or not self.hub.permissions.allowed(ORGANIZER_SCAN): return
        files=result.files
        if self.order.get()=='Maior tamanho': files=sorted(files,key=lambda x:(-x.size,x.name.casefold(),x.name))
        elif self.order.get()=='Nome': files=sorted(files,key=lambda x:(x.name.casefold(),x.name))
        lines=[f'Arquivos listados: {len(files)} | Entradas ignoradas: {result.skipped}',
               f'Tamanho total listado: {sum(x.size for x in files):,} bytes | Ordem: {self.order.get()}',
               'Sugestão por categoria (não cria pastas nem move arquivos).']""")
    s=replace(s,"for item in result.files)\n        self.show('\\n'.join(lines))","for item in files)\n        self.show('\\n'.join(lines),keep=True)")
    files["organizer_ui.py"]=s
    s=files["drop_ui.py"]
    s=replace(s,"self.timer=None; self.items=()","self.timer=None; self.items=(); self.revision=0")
    s=replace(s,"        self.summary=tk.StringVar(self.window);", """        selection=ttk.Frame(f); selection.pack(fill='x')
        ttk.Button(selection,text='Selecionar todas',command=self.select_all).pack(side='left')
        ttk.Button(selection,text='Limpar seleção',command=self.unselect_all).pack(side='left',padx=4)
        self.summary=tk.StringVar(self.window);""")
    s=replace(s,"    def refresh(self):\n        self.items=self.store.list();", """    def select_all(self):
        self.listbox.selection_set(0,'end'); self.controls()
    def unselect_all(self):
        self.listbox.selection_clear(0,'end'); self.controls()
    def refresh(self):
        reviewed=set(self.selected())
        self.items=self.store.list();""")
    s=replace(s,"        self.summary.set(f'{len(self.items)}/100 referências | {sum(i.size for i in self.items):,} bytes (na seleção)')", """        for i,item in enumerate(self.items):
            if item.path in reviewed: self.listbox.selection_set(i)
""".rstrip())
    s=replace(s,"        self.add_button.configure(state=", """        paths=set(self.selected())
        self.summary.set(f'{len(self.items)}/100 referências | {len(paths)} selecionadas | {sum(i.size for i in self.items if i.path in paths):,} bytes selecionados (estimativa da adição)')
        self.add_button.configure(state=""")
    s=replace(s,"            self.cancel(); self.store.clear(); self.status.set","            self.revision+=1; self.cancel(); self.store.clear(); self.status.set")
    s=replace(s,"        paths=filedialog.askopenfilenames", "        reviewed=self.revision\n        paths=filedialog.askopenfilenames")
    s=replace(s,"        if not self.window.winfo_exists() or not self.hub.permissions.allowed(DROP_ADD): return","        if not self.window.winfo_exists() or self.job or reviewed!=self.revision or not self.hub.permissions.allowed(DROP_ADD): return")
    s=replace(s,"        if not self.window.winfo_exists() or self.job or not self.hub.permissions.allowed(DROP_ADD): return","        if not self.window.winfo_exists() or self.job or reviewed!=self.revision or not self.hub.permissions.allowed(DROP_ADD): return")
    s=replace(s,"        self.status.set('Referências adicionadas.","        self.revision+=1; self.status.set('Referências adicionadas.")
    s=replace(s,"    def remove(self): self.store.remove(self.selected()); self.refresh()","    def remove(self): self.revision+=1; self.store.remove(self.selected()); self.refresh()")
    s=replace(s,"    def clear(self): self.cancel(); self.store.clear();","    def clear(self): self.revision+=1; self.cancel(); self.store.clear();")
    s=replace(s,"        paths=self.selected()\n        if not paths","        paths=self.selected(); reviewed=self.revision; records=self.store.list()\n        if not paths")
    s=replace(s,"if not self.window.winfo_exists() or paths!=self.selected() or not all", "if not self.window.winfo_exists() or reviewed!=self.revision or records!=self.store.list() or paths!=self.selected() or not all")
    files["drop_ui.py"]=s
    s=files["compare_ui.py"]
    s=replace(s,"self.paths=[None,None]\n        self.window", "self.paths=[None,None]; self.revision=0; self.request=None; self.comparison=None\n        self.window")
    s=replace(s,"        self.status=tk.StringVar(self.window,'Pronto.');", """        self.changes_only=tk.BooleanVar(self.window,False)
        ttk.Checkbutton(f,text='Mostrar apenas linhas alteradas',variable=self.changes_only,command=self.render_comparison).pack(anchor='w')
        self.status=tk.StringVar(self.window,'Pronto.');""")
    s=replace(s,"    def show(self,text):\n        self.report.configure","""    def context(self):
        return (self.revision,self.mode.get(),tuple(self.paths) if self.mode.get()=='Arquivos' else tuple(t.get('1.0','end-1c') for t in self.inputs))
    def show(self,text,keep=False):
        if not keep: self.comparison=None
        self.report.configure""")
    s=replace(s,"            event.widget.edit_modified(False);self.cancel();", "            event.widget.edit_modified(False);self.revision+=1;self.cancel();")
    s=replace(s,"        value=filedialog.askopenfilename","        reviewed=self.context()\n        value=filedialog.askopenfilename")
    s=replace(s,"        if value and self.window.winfo_exists() and self.mode.get()=='Arquivos'", "        if value and self.window.winfo_exists() and self.job is None and reviewed==self.context() and self.mode.get()=='Arquivos'")
    s=replace(s,"            self.paths[i]=value;", "            self.revision+=1;self.paths[i]=value;")
    s=replace(s,"            selected=tuple(self.paths)", "            selected=tuple(self.paths); reviewed=self.context()")
    s=replace(s,"if not self.window.winfo_exists() or self.mode.get()!='Arquivos' or tuple(self.paths)!=selected", "if not self.window.winfo_exists() or self.job or reviewed!=self.context() or self.mode.get()!='Arquivos' or tuple(self.paths)!=selected")
    s=replace(s,"        event=threading.Event();outcome=queue.Queue(1)", "        self.request=self.context()\n        event=threading.Event();outcome=queue.Queue(1)")
    s=replace(s,"        self.job=None;self.controls()\n        if event.is_set()", "        self.job=None;reviewed=self.request;self.request=None;self.controls()\n        if reviewed!=self.context() or event.is_set()")
    s=replace(s,"        rows=[]\n        for r in result.rows:", """        self.comparison=result; self.render_comparison()
    def render_comparison(self):
        result=self.comparison
        if result is None: return
        if self.mode.get()=='Arquivos' and not self.hub.permissions.allowed(COMPARE_READ):
            self.show(''); return
        rows=[]
        for r in result.rows:
            if self.changes_only.get() and r.kind=='=': continue""")
    s=replace(s,"        self.show('\\n'.join(rows))","        self.show('\\n'.join(rows) if rows else 'Nenhuma linha alterada.',keep=True)")
    s=replace(s,"        self.cancel();self.paths=[None,None]", "        self.revision+=1;self.cancel();self.paths=[None,None]")
    files["compare_ui.py"]=s
    s=files["lens_ui.py"]
    s=replace(s,"from aeris.lens import recognize, Cancelled, LANGUAGES","from aeris.lens import recognize, Cancelled, LANGUAGES\nfrom aeris.window_lifecycle import trace_window")
    s=replace(s,"        self.lang_box.bind('<<ComboboxSelected>>',lambda _:self.show('Idioma alterado; execute novamente.'))","")
    s=replace(s,"        self.permissions_changed()\n    def context", """        self.permissions_changed()
        trace_window(self.window,self.language,self.language_changed)
    def language_changed(self,*_):
        self.revision+=1; self.cancel(); self.show('Idioma alterado; execute novamente.')
    def context""")
    s=replace(s,"        heading=f'Formato: {result.format} |", "        heading=f'Idioma: {self.language.get()} | Formato: {result.format} |")
    files["lens_ui.py"]=s
    for name,code in files.items(): compile(code,name,"exec")
    for name,code in files.items(): (root/name).write_bytes(code.encode("utf-8"))
    print("Files: five verified original RC4 files refined")

if __name__=="__main__": apply(sys.argv[1])
