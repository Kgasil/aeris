"""Explicit, cancellable metadata inspection with no write operations."""
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from aeris.permissions import METADATA_READ
from aeris.metadata import inspect_file, Cancelled

class MetadataWindow:
    def __init__(self,hub):
        self.hub=hub; self.job=None; self.timer=None; self.path=None; self.revision=0; self.request=None; self.result=None; self.result_context=None
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris Metadata'); self.window.geometry('680x520'); self.window.minsize(510,460)
        self.window.protocol('WM_DELETE_WINDOW',self.close); self.window.bind('<Escape>',lambda _:self.close())
        self.window.bind('<Destroy>',self.destroyed,add='+')
        f=ttk.Frame(self.window,padding=14); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Aeris Metadata',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text='Inspecione propriedades selecionadas de PNG, JPEG e Office (até 32 MiB). O relatório pode conter dados pessoais.',wraplength=460).pack(anchor='w',pady=5)
        self.choose_button=ttk.Button(f,text='Selecionar arquivo local',command=self.choose); self.choose_button.pack(fill='x')
        self.filename=tk.StringVar(self.window,'Nenhum arquivo selecionado'); ttk.Label(f,textvariable=self.filename,wraplength=460).pack(anchor='w',pady=4)
        self.run_button=ttk.Button(f,text='Inspecionar metadados',command=self.run); self.run_button.pack(fill='x',pady=6)
        self.cancel_button=ttk.Button(f,text='Cancelar',command=self.cancel); self.cancel_button.pack(fill='x',pady=4)
        self.hide_values=tk.BooleanVar(self.window,False)
        ttk.Checkbutton(f,text='Ocultar valores na tela',variable=self.hide_values,command=self.render_result).pack(anchor='w')
        frame=ttk.Frame(f); frame.pack(fill='both',expand=True,pady=5)
        self.report=tk.Text(frame,height=10,wrap='word',state='disabled'); self.report.pack(side='left',fill='both',expand=True)
        bar=ttk.Scrollbar(frame,command=self.report.yview); bar.pack(side='right',fill='y'); self.report.configure(yscrollcommand=bar.set)
        ttk.Button(f,text='Limpar resultado',command=self.clear).pack(fill='x')
        self.permissions_changed()
    def context(self): return (self.revision,self.path)
    def show(self,text,keep=False):
        if not keep: self.result=None; self.result_context=None
        self.report.configure(state='normal'); self.report.delete('1.0','end'); self.report.insert('1.0',text); self.report.configure(state='disabled')
    def controls(self):
        allowed=self.hub.permissions.allowed(METADATA_READ); busy=self.job is not None
        self.choose_button.configure(state='normal' if allowed and not busy else 'disabled')
        self.run_button.configure(state='normal' if allowed and not busy and self.path else 'disabled')
        self.cancel_button.configure(state='normal' if busy else 'disabled')
    def permissions_changed(self):
        if not self.hub.permissions.allowed(METADATA_READ): self.clear(); self.show('Autorize Metadata → Ler arquivo em Permissões.')
        self.controls()
    def choose(self):
        if self.job or not self.hub.permissions.allowed(METADATA_READ): return
        reviewed=self.context(); permission_revision=self.hub.permissions.revision
        value=filedialog.askopenfilename(parent=self.window,title='Selecione arquivo fictício',filetypes=[('Formatos suportados','*.png *.jpg *.jpeg *.docx *.xlsx *.pptx'),('Todos','*')])
        if value and self.window.winfo_exists() and self.job is None and reviewed==self.context() and permission_revision==self.hub.permissions.revision and self.hub.permissions.allowed(METADATA_READ):
            self.revision+=1; self.path=value; self.filename.set(value); self.show('Resultado pendente.'); self.controls()
    def run(self):
        if self.job or not self.path or not self.hub.permissions.allowed(METADATA_READ): return
        reviewed=self.context(); permission_revision=self.hub.permissions.revision
        if not messagebox.askyesno('Ler arquivo?', 'Inspecionar propriedades do arquivo selecionado? O relatório pode revelar dados pessoais.',parent=self.window): return
        if not self.window.winfo_exists() or self.job or reviewed!=self.context() or permission_revision!=self.hub.permissions.revision or not self.hub.permissions.allowed(METADATA_READ): return
        self.request=reviewed
        event=threading.Event(); outcome=queue.Queue(1); path=self.path
        def work():
            try: outcome.put(inspect_file(path,cancelled=event.is_set))
            except Cancelled: outcome.put(None)
            except ValueError as exc: outcome.put(str(exc))
            except Exception: outcome.put('Não foi possível inspecionar o arquivo.')
        self.job=(event,outcome); self.controls(); self.show('Inspecionando...')
        threading.Thread(target=work,daemon=True).start(); self.poll()
    def poll(self):
        self.timer=None
        if self.job is None: return
        event,outcome=self.job
        try: result=outcome.get_nowait()
        except queue.Empty: self.timer=self.window.after(60,self.poll); return
        self.job=None; reviewed=self.request; self.request=None; self.controls()
        if event.is_set() or reviewed!=self.context() or not self.hub.permissions.allowed(METADATA_READ): return
        if isinstance(result,str): self.show(result); return
        if result is None: self.show('Cancelado.'); return
        self.result=result; self.result_context=reviewed; self.render_result()
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
        self.show('\n'.join(lines),keep=True)
    def cancel(self):
        if self.job: self.job[0].set(); self.show('Cancelamento solicitado; resultado descartado.')
    def clear(self):
        self.revision+=1; self.cancel(); self.path=None; self.filename.set('Nenhum arquivo selecionado'); self.show('Resultado descartado.'); self.controls()
    def destroyed(self,event):
        if event.widget is self.window:
            if self.job: self.job[0].set()
            if self.timer is not None: self.window.after_cancel(self.timer); self.timer=None
    def close(self):
        self.cancel(); self.window.destroy()
