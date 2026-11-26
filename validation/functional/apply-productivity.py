"""Checked cumulative refinement of the original RC4 Productivity files."""
import hashlib
from pathlib import Path
import sys

def replace(s, old, new):
    if s.count(old) != 1:
        raise ValueError("Unexpected anchor: " + old[:100])
    return s.replace(old,new,1)

def apply(root):
    root=Path(root)/"aeris"
    hashes={
        "focus_ui.py":"b2f5c65052b1c89f69ec363e4bc6da5ab413511a7b3782b6f6249122bf2a3801",
        "workspace_ui.py":"b61fc3de25d6e0d378bbfbfe0ca58b1bdaeb495552fdea50a654e8fb1bf8edef",
        "checklist_ui.py":"6dbf7157c95978c078c11103e88e581b95a25bc042bbab2700e809c6d00275f6",
        "reminder.py":"ee1d79b7d5300fdd8e4902541768f21bd8d989ca0ea0fbfb9160ba46932667be",
        "routine_ui.py":"83cde2147e44ee4b73cd156c88e35a88fb285bd0a172ff72bd3433685120e4f8",
    }
    files={}
    for name,expected in hashes.items():
        raw=(root/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected:
            raise ValueError("Unexpected RC4 source: "+name)
        files[name]=raw.decode("utf-8").replace("\r\n","\n")
    s=files["focus_ui.py"]
    s=replace(s,"        self.duration_box.pack(side='right')", """        self.duration_box.pack(side='right')
        presets=ttk.Frame(f); presets.pack(fill='x')
        self.preset_buttons=[]
        for label, mode, minutes in [('25 min', MODES[0],25),('50 min', MODES[0],50),('5 min pausa', MODES[1],5)]:
            button=ttk.Button(presets,text=label,command=lambda m=mode,n=minutes:self.preset(m,n))
            button.pack(side='left',fill='x',expand=True,padx=2)
            self.preset_buttons.append(button)""")
    s=replace(s,"self.window.geometry('460x430'); self.window.minsize(370,400)","self.window.geometry('460x490'); self.window.minsize(370,460)")
    s=replace(s,"    def mode_changed(self, _=None):","""    def preset(self, mode, minutes):
        if self.model.state not in ('ready','finished'):
            return
        self.model.configure(mode,minutes)
        self.mode.set(mode); self.minutes.set(str(minutes)); self.render()

    def mode_changed(self, _=None):""")
    s=replace(s,"        self.duration_box.configure(state='normal' if editable else 'disabled')","""        self.duration_box.configure(state='normal' if editable else 'disabled')
        for button in self.preset_buttons:
            button.configure(state='normal' if editable else 'disabled')""")
    files["focus_ui.py"]=s
    s=files["workspace_ui.py"]
    s=replace(s,"        if self.saved.get():\n            item=self.store.get(self.saved.get())","        if self.saved.get() in tuple(x.name for x in self.store.list()):\n            item=self.store.get(self.saved.get())")
    s=replace(s,"        if self.saved.get() and self.allow_discard(): self.fill(self.store.get(self.saved.get()))","""        name=self.saved.get()
        if not name: return
        try: item=self.store.get(name)
        except KeyError: self.refresh(); self.status.set('Ambiente não encontrado.'); return
        if not self.allow_discard(): return
        if self.saved.get()!=name or not any(x is item for x in self.store.list()):
            self.status.set('Seleção alterada. Carregue novamente.'); return
        self.fill(item)""")
    s=replace(s,"        if name and messagebox.askyesno('Excluir?', 'Remover ambiente salvo?',parent=self.window):\n            self.store.delete(name);", """        if not name: return
        try: item=self.store.get(name)
        except KeyError: self.refresh(); self.status.set('Ambiente não encontrado.'); return
        if messagebox.askyesno('Excluir?', 'Remover ambiente salvo?',parent=self.window):
            if self.saved.get()!=name or not any(x is item for x in self.store.list()):
                self.status.set('Seleção alterada. Revise novamente.'); return
            self.store.delete(name);""")
    s=replace(s,"        self.store.activate(self.saved.get()); self.hub.workspace_changed(); self.status.set('Ambiente ativo: '+self.store.active)","""        try: self.store.activate(self.saved.get())
        except KeyError: self.refresh(); self.status.set('Ambiente não encontrado.'); return
        self.hub.workspace_changed(); self.status.set('Ambiente ativo: '+self.store.active)""")
    files["workspace_ui.py"]=s
    s=files["checklist_ui.py"]
    s=replace(s,"        self.filter=tk.StringVar(self.window,'Todas')\n        filter_box=ttk.Combobox(f,textvariable=self.filter,values=('Todas','Pendentes','Concluídas'),state='readonly'); filter_box.pack(anchor='w')","""        filters=ttk.Frame(f); filters.pack(fill='x')
        self.filter=tk.StringVar(self.window,'Todas')
        filter_box=ttk.Combobox(filters,textvariable=self.filter,values=('Todas','Pendentes','Concluídas'),state='readonly',width=15); filter_box.pack(side='left')
        self.priority_filter=tk.StringVar(self.window,'Todas')
        priority_box=ttk.Combobox(filters,textvariable=self.priority_filter,values=('Todas',)+PRIORITIES,state='readonly',width=12); priority_box.pack(side='left',padx=4)
        priority_box.bind('<<ComboboxSelected>>',lambda _: self.render())""")
    s=replace(s,"        self.tree.bind('<Double-1>',lambda _: self.toggle())","""        self.tree.bind('<Double-1>',self.toggle_row)
        self.tree.bind('<Return>',lambda _: (self.toggle(),'break')[1])""")
    s=replace(s,"    def render(self):\n        self.tree.delete(*self.tree.get_children())","""    def toggle_row(self,event):
        row=self.tree.identify_row(event.y)
        if row and self.tree.identify_region(event.x,event.y) in ('cell','tree'):
            self.tree.selection_set(row); self.toggle()
        return 'break'

    def render(self):
        selected=self.tree.selection()
        self.tree.delete(*self.tree.get_children())""")
    s=replace(s,"            self.tree.insert('', 'end', iid=str(task.id), values=(task.title,task.priority,'Concluída' if task.done else 'Pendente'))","""            if self.priority_filter.get()!='Todas' and task.priority!=self.priority_filter.get(): continue
            self.tree.insert('', 'end', iid=str(task.id), values=(task.title,task.priority,'Concluída' if task.done else 'Pendente'))
        if selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected[0]); self.tree.focus(selected[0]); self.tree.see(selected[0])""")
    files["checklist_ui.py"]=s
    s=files["reminder.py"]
    s=replace(s,"        if r.state != 'pending': raise ValueError('Somente lembretes pendentes podem ser editados.')","        if r.state != 'pending' or r.due <= self.clock(): raise ValueError('Somente lembretes ainda não vencidos podem ser editados.')")
    s=replace(s,"        if r.state != 'pending': raise ValueError('Lembrete não está pendente.')","        if r.state != 'pending' or r.due <= self.clock(): raise ValueError('Lembrete não está pendente ou já venceu.')")
    files["reminder.py"]=s
    s=files["routine_ui.py"]
    s=replace(s,"        self.executed = None\n        self.steps", "        self.executed = None\n        self.preview_context = None\n        self.steps")
    s=replace(s,"        self.preview = self.executed = None\n", "        self.preview = self.executed = self.preview_context = None\n")
    s=replace(s,"    def run(self):\n", """    def context(self):
        return (self.name.get(),tuple(self.steps),self.input.get('1.0','end-1c'),self.src.get(),self.dst.get())

    def require_review(self):
        if self.preview is None or self.preview_context!=self.context():
            self.invalidate()
            raise ValueError('Entrada ou sequência alterada. Execute novamente.')
        self.engine.require(self.executed); self.hub.permissions.require(ROUTINE_COPY)

    def run(self):
""")
    s=replace(s,"            self.executed=item; self.preview=previews[-1]","            self.executed=item; self.preview=previews[-1]; self.preview_context=self.context()")
    s=replace(s,"            if self.preview is None: raise ValueError('Execute novamente.')\n            self.engine.require(self.executed); self.hub.permissions.require(ROUTINE_COPY)\n            if not messagebox.askyesno", """            self.require_review()
            reviewed=self.preview
            if not messagebox.askyesno""")
    s=replace(s,"            if self.preview is None: raise ValueError('Execute novamente.')\n            self.engine.require(self.executed); self.hub.permissions.require(ROUTINE_COPY)\n            self.hub.root.clipboard_clear()", """            self.require_review()
            if self.preview is not reviewed: raise ValueError('Prévia alterada. Execute novamente.')
            self.hub.root.clipboard_clear()""")
    files["routine_ui.py"]=s
    for name,code in files.items(): compile(code,name,"exec")
    for name,code in files.items(): (root/name).write_bytes(code.encode("utf-8"))
    print("Productivity: five RC4 files verified and refined")

if __name__=="__main__": apply(sys.argv[1])
