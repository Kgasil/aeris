"""User-initiated workflow preview. Imported data stays in this window only."""
import tkinter as tk
from aeris.window_lifecycle import trace_window
from tkinter import ttk, messagebox
from aeris.bridge import Bridge, ROUTES, SOURCE_GRANTS
from aeris.permissions import BRIDGE_RUN, BRIDGE_SAVE, BRIDGE_COPY
from aeris.translate import LANGUAGES

class BridgeWindow:
    def __init__(self, hub):
        self.hub=hub; self.engine=Bridge(hub); self.preview=None; self.preview_context=None; self.imported='Manual'; self.records=()
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris Bridge · Fluxos locais'); self.window.geometry('650x690'); self.window.minsize(510,620)
        self.window.protocol('WM_DELETE_WINDOW', self.close); self.window.bind('<Escape>',lambda _:self.close())
        f=ttk.Frame(self.window,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Bridge · conecte suas ferramentas',font=('Segoe UI',17)).pack(anchor='w')
        ttk.Label(f,text='Selecione fontes e execute conscientemente. Use dados fictícios.',wraplength=470).pack(anchor='w')
        self.source=tk.StringVar(self.window,'Manual'); self.route=tk.StringVar(self.window,next(iter(ROUTES)))
        r=ttk.Frame(f); r.pack(fill='x',pady=5)
        ttk.Combobox(r,textvariable=self.source,values=('Manual','Capture','Snippets'),state='readonly',width=13).pack(side='left')
        ttk.Button(r,text='Listar registros',command=self.list_records).pack(side='left',padx=4)
        ttk.Button(r,text='Importar seleção',command=self.import_record).pack(side='left')
        self.record=ttk.Combobox(f,state='readonly'); self.record.pack(fill='x')
        self.input=tk.Text(f,height=4,wrap='word'); self.input.pack(fill='both',expand=True,pady=5)
        self.input.bind('<<Modified>>',self.changed); self.input.edit_modified(False)
        ttk.Label(f,text='Fluxo').pack(anchor='w')
        ttk.Combobox(f,textvariable=self.route,values=tuple(ROUTES),state='readonly').pack(fill='x')
        r=ttk.Frame(f); r.pack(fill='x',pady=4)
        self.src=tk.StringVar(self.window,'pt'); self.dst=tk.StringVar(self.window,'en')
        ttk.Label(r,text='Idiomas (Translate → Email):').pack(side='left')
        for v in (self.src,self.dst): ttk.Combobox(r,textvariable=v,values=tuple(LANGUAGES),state='readonly',width=5).pack(side='left',padx=3)
        for v in (self.route,self.src,self.dst): trace_window(self.window, v, lambda *_:self.invalidate())
        trace_window(self.window, self.source, lambda *_:self.source_changed())
        self.run_button=ttk.Button(f,text='Executar e revisar',command=self.run); self.run_button.pack(fill='x')
        self.output=tk.Text(f,height=5,wrap='word',state='disabled'); self.output.pack(fill='both',expand=True,pady=5)
        self.title=tk.StringVar(self.window,'Resultado do Bridge')
        ttk.Entry(f,textvariable=self.title).pack(fill='x')
        r=ttk.Frame(f); r.pack(fill='x',pady=4)
        self.save_button=ttk.Button(r,text='Salvar no Capture',command=self.save); self.save_button.pack(side='left')
        self.copy_button=ttk.Button(r,text='Copiar prévia',command=self.copy); self.copy_button.pack(side='left',padx=4)
        ttk.Button(r,text='Permissões',command=hub.open_permissions).pack(side='right')
        self.status=tk.StringVar(self.window,'Nenhum fluxo executado.'); ttk.Label(f,textvariable=self.status,wraplength=480).pack(anchor='w')
        self.buttons()

    def buttons(self):
        p=self.hub.permissions
        self.run_button.configure(state='normal' if p.allowed(BRIDGE_RUN) else 'disabled')
        self.copy_button.configure(state='normal' if self.preview and p.allowed(BRIDGE_COPY) else 'disabled')
        self.save_button.configure(state='normal' if self.preview and self.preview.route=='Text → Capture' and p.allowed(BRIDGE_SAVE) else 'disabled')

    def invalidate(self):
        self.preview=None; self.preview_context=None; self.output.configure(state='normal'); self.output.delete('1.0','end'); self.output.configure(state='disabled'); self.buttons()

    def changed(self,_=None):
        if self.input.edit_modified(): self.input.edit_modified(False); self.invalidate()

    def clear_records(self):
        self.records=(); self.record.configure(values=()); self.record.set('')

    def source_changed(self):
        self.clear_records(); self.input.delete('1.0','end'); self.imported='Manual'; self.invalidate()

    def permissions_changed(self):
        self.clear_records()
        if self.imported in SOURCE_GRANTS and not self.hub.permissions.allowed(SOURCE_GRANTS[self.imported]):
            self.input.delete('1.0','end'); self.imported='Manual'
        self.invalidate(); self.status.set('Permissões alteradas; execute novamente.')

    def list_records(self):
        self.clear_records()
        try:
            self.records=self.engine.records(self.source.get())
            self.record.configure(values=tuple(f'{i.id} · {i.title}' for i in self.records))
            if self.records: self.record.current(0)
            self.status.set(f'{len(self.records)} registros disponíveis.')
        except (ValueError,PermissionError) as e: self.status.set(str(e))

    def import_record(self):
        idx=self.record.current()
        if idx<0 or idx>=len(self.records): return
        try:
            source=self.source.get(); records=self.engine.records(source); item=next((x for x in records if x.id==self.records[idx].id),None)
            if item is None: raise ValueError('Registro removido. Liste novamente.')
            if len(item.body)>20000: raise ValueError('Registro acima do limite do Bridge.')
            if not messagebox.askyesno('Importar texto?',f'Importar uma cópia do registro de {source}?',parent=self.window): return
            self.engine.require(SOURCE_GRANTS[source],source)
            self.input.delete('1.0','end'); self.input.insert('1.0',item.body); self.input.edit_modified(False); self.imported=source; self.invalidate()
        except (ValueError,PermissionError) as e: self.status.set(str(e))

    def current_context(self):
        return (self.route.get(), self.input.get('1.0','end-1c'), self.imported, self.src.get(), self.dst.get())

    def run(self):
        self.invalidate()
        try:
            self.preview_context=self.current_context(); self.preview=self.engine.run(*self.preview_context)
            self.output.configure(state='normal'); self.output.insert('1.0',self.render()); self.output.configure(state='disabled'); self.status.set('Revise o resultado antes de usar.'); self.buttons()
        except (ValueError,PermissionError) as e: self.status.set(str(e))

    def render(self): return (self.preview.subject+'\n\n' if self.preview.subject else '')+self.preview.text

    def require_preview(self,cap):
        if self.preview is None or self.preview_context != self.current_context():
            self.invalidate()
            raise ValueError('Entrada ou fluxo alterado. Execute novamente.')
        self.engine.require(BRIDGE_RUN,*ROUTES[self.preview.route]); self.engine.require(cap)
        if self.imported in SOURCE_GRANTS: self.engine.require(SOURCE_GRANTS[self.imported],self.imported)

    def save(self):
        try:
            self.require_preview(BRIDGE_SAVE)
            reviewed=self.preview; title=self.title.get()
            if not messagebox.askyesno('Salvar anotação?','Criar uma nova anotação da sessão no Capture?',parent=self.window): return
            self.require_preview(BRIDGE_SAVE)
            if self.preview is not reviewed or self.title.get()!=title: raise ValueError('Seleção alterada. Revise novamente.')
            self.engine.save_capture(reviewed,title); self.status.set('Anotação criada.'); self.invalidate()
        except (ValueError,PermissionError) as e: self.status.set(str(e))

    def copy(self):
        try:
            self.require_preview(BRIDGE_COPY)
            reviewed=self.preview
            if not messagebox.askyesno('Copiar?','Substituir o clipboard? O histórico do sistema pode reter o texto.',parent=self.window): return
            self.require_preview(BRIDGE_COPY)
            if self.preview is not reviewed: raise ValueError('Prévia alterada. Revise novamente.')
            self.hub.root.clipboard_clear(); self.hub.root.clipboard_append(self.render()); self.status.set('Copiado. Cole manualmente.')
        except (ValueError,PermissionError,tk.TclError) as e: self.status.set(str(e))

    def close(self):
        if self.input.get('1.0','end-1c').strip() and not messagebox.askyesno('Fechar Bridge?','Descartar texto e prévia?',parent=self.window): return
        self.window.destroy()
