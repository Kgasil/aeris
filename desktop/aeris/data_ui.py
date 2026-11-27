"""Explicit, cancellable CSV profiling with no write operations."""
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from aeris.permissions import DATA_READ
from aeris.data import profile_file, Cancelled
from aeris.organizer import safe_name
from aeris.window_lifecycle import trace_window
from pathlib import Path

class DataWindow:
    permission=DATA_READ
    title="Aeris Data"
    display_title='Analisar dados'
    description="Encontre valores ausentes, duplicatas e estatísticas de um CSV local com cabeçalho. Use dados fictícios."
    def parse(self,path,delimiter,decimal,cancelled):
        return profile_file(path,delimiter,decimal,cancelled=cancelled)
    def __init__(self,hub):
        self.hub=hub; self.job=None; self.timer=None; self.path=None; self.revision=0; self.request=None
        self.window=tk.Toplevel(hub.root); self.window.title(self.display_title); self.window.geometry('740x600'); self.window.minsize(510,460)
        self.window.protocol('WM_DELETE_WINDOW',self.close); self.window.bind('<Escape>',lambda _:self.close())
        self.window.bind('<Destroy>',self.destroyed,add='+')
        f=ttk.Frame(self.window,padding=18); f.pack(fill='both',expand=True)
        ttk.Label(f,text=self.display_title,font=('Segoe UI',21,'bold')).pack(anchor='w')
        ttk.Label(f,text=self.description,wraplength=460,style='Aeris.Muted.TLabel').pack(anchor='w',pady=5)
        ttk.Label(f,text='1. Escolha o arquivo CSV',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(6,4))
        source=ttk.Frame(f); source.pack(fill='x')
        self.choose_button=ttk.Button(source,text='Selecionar arquivo',command=self.choose); self.choose_button.pack(side='left',fill='x',expand=True)
        ttk.Button(source,text='Permissões',command=hub.open_permissions).pack(side='right',padx=(6,0))
        self.filename=tk.StringVar(self.window,'Nenhum CSV selecionado'); ttk.Label(f,textvariable=self.filename,wraplength=460).pack(anchor='w',pady=4)
        ttk.Label(f,text='2. Confira o formato do arquivo',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(6,0))
        opts=ttk.Frame(f); opts.pack(fill='x',pady=4)
        self.delimiter=tk.StringVar(self.window,','); self.decimal=tk.StringVar(self.window,'.')
        ttk.Label(opts,text='Separador de campos').pack(side='left')
        self.delim_box=ttk.Combobox(opts,textvariable=self.delimiter,values=(',', ';', 'TAB'),state='readonly',width=5); self.delim_box.pack(side='left',padx=6)
        ttk.Label(opts,text='Decimal').pack(side='left')
        self.dec_box=ttk.Combobox(opts,textvariable=self.decimal,values=('.', ','),state='readonly',width=5); self.dec_box.pack(side='left',padx=6)

        actions=ttk.Frame(f); actions.pack(fill='x',pady=6)
        self.run_button=ttk.Button(actions,text='Analisar CSV',command=self.run,style='Aeris.Primary.TButton'); self.run_button.pack(side='left',fill='x',expand=True)
        self.cancel_button=ttk.Button(actions,text='Cancelar',command=self.cancel,style='Aeris.Stop.TButton'); self.cancel_button.pack(side='right',padx=(6,0))
        ttk.Label(f,text='3. Resultados da análise',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(8,0))
        frame=ttk.Frame(f); frame.pack(fill='both',expand=True,pady=5)
        self.report=tk.Text(frame,height=10,wrap='word',state='disabled',padx=12,pady=10,relief='flat',highlightthickness=1); self.report.pack(side='left',fill='both',expand=True)
        bar=ttk.Scrollbar(frame,command=self.report.yview); bar.pack(side='right',fill='y'); self.report.configure(yscrollcommand=bar.set)
        ttk.Button(f,text='Limpar resultado',command=self.clear).pack(fill='x')
        self.permissions_changed()
        for var in (self.delimiter,self.decimal): trace_window(self.window,var,self.options_changed)
    def context(self):
        return (self.revision,self.path,self.delimiter.get(),self.decimal.get())
    def options_changed(self,*_):
        self.revision+=1; self.cancel(); self.show('Separadores alterados. Analise novamente.')
    def show(self,text):
        self.report.configure(state='normal'); self.report.delete('1.0','end'); self.report.insert('1.0',text); self.report.configure(state='disabled')
    def controls(self):
        allowed=self.hub.permissions.allowed(self.permission); busy=self.job is not None
        self.choose_button.configure(state='normal' if allowed and not busy else 'disabled')
        self.run_button.configure(state='normal' if allowed and not busy and self.path else 'disabled')
        self.cancel_button.configure(state='normal' if busy else 'disabled')
        for widget in (self.delim_box,self.dec_box): widget.configure(state='readonly' if allowed and not busy else 'disabled')
    def permissions_changed(self):
        if not self.hub.permissions.allowed(self.permission): self.clear(); self.show(f'Autorize {self.title} → Ler CSV em Permissões.')
        self.controls()
    def choose(self):
        if self.job or not self.hub.permissions.allowed(self.permission): return
        reviewed=self.context()
        value=filedialog.askopenfilename(parent=self.window,title='Selecione CSV fictício',filetypes=[('CSV','*.csv')])
        if value and self.window.winfo_exists() and self.hub.permissions.allowed(self.permission) and self.job is None and reviewed==self.context():
            self.revision+=1; self.path=value; self.filename.set(safe_name(Path(value).name)); self.show('Resultado pendente.'); self.controls()
    def run(self):
        if self.job or not self.path or not self.hub.permissions.allowed(self.permission): return
        reviewed=self.context()
        if not messagebox.askyesno('Analisar CSV?', 'Ler o CSV selecionado para calcular estatísticas? O relatório pode revelar dados pessoais.',parent=self.window): return
        if not self.window.winfo_exists() or not self.path or self.job or not self.hub.permissions.allowed(self.permission): return
        if reviewed!=self.context(): self.show('Seleção alterada. Confirme novamente.'); return
        self.request=reviewed
        event=threading.Event(); outcome=queue.Queue(1); path=self.path; delimiter="\t" if self.delimiter.get()=="TAB" else self.delimiter.get(); decimal=self.decimal.get()
        def work():
            try: outcome.put(self.parse(path,delimiter,decimal,event.is_set))
            except Cancelled: outcome.put(None)
            except ValueError as exc: outcome.put(str(exc))
            except Exception: outcome.put('Não foi possível analisar o CSV.')
        self.job=(event,outcome); self.controls(); self.show('Analisando CSV...')
        threading.Thread(target=work,daemon=True).start(); self.poll()
    def poll(self):
        self.timer=None
        if self.job is None: return
        event,outcome=self.job
        try: result=outcome.get_nowait()
        except queue.Empty: self.timer=self.window.after(60,self.poll); return
        self.job=None; reviewed=self.request; self.request=None; self.controls()
        if event.is_set() or reviewed!=self.context() or not self.hub.permissions.allowed(self.permission): return
        if isinstance(result,str): self.show(result); return
        if result is None: self.show('Cancelado.'); return
        self.render_result(result)
    def render_result(self,result):
        lines=[f'Registros: {result.rows} | Colunas: {len(result.columns)}',f'Valores ausentes: {result.missing} | Duplicatas exatas adicionais: {result.duplicates}', 'Inferência numérica simples; confira identificadores e separadores.']
        cells=result.rows*len(result.columns)
        missing=f'{100*result.missing/cells:.2f}%' if cells else '—'
        duplicates=f'{100*result.duplicates/result.rows:.2f}%' if result.rows else '—'
        lines.append(f'Células ausentes: {missing} | Duplicatas adicionais por registro: {duplicates}')
        for col in result.columns:
            lines.append(f'\n{safe_name(col.name)} | {col.kind} | Ausentes: {col.missing} | Distintos: {col.distinct}')
            if col.mean is not None: lines.append(f' Mín: {col.minimum} | Máx: {col.maximum} | Média: {col.mean:.10g}')
        self.show('\n'.join(lines))
        self.report.configure(state='normal')
        self.report.tag_configure('summary',font=('Segoe UI',11,'bold'),spacing3=5)
        self.report.tag_add('summary','1.0','3.0')
        self.report.configure(state='disabled')
    def cancel(self):
        if self.job: self.job[0].set(); self.show('Cancelamento solicitado; resultado descartado.')
    def clear(self):
        self.revision+=1; self.cancel(); self.path=None; self.filename.set('Nenhum CSV selecionado'); self.show('Resultado descartado.'); self.controls()
    def destroyed(self,event):
        if event.widget is self.window:
            if self.job: self.job[0].set()
            if self.timer is not None: self.window.after_cancel(self.timer); self.timer=None
    def close(self):
        self.cancel(); self.window.destroy()
