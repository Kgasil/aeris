"""Compare pasted text or explicitly selected local documents."""
import queue
import threading
import tkinter as tk
from aeris.window_lifecycle import trace_window
from tkinter import ttk, filedialog, messagebox
from aeris.permissions import COMPARE_READ
from aeris.compare import compare_texts, compare_files, Cancelled, MAX_CHARS

class CompareWindow:
    def __init__(self,hub):
        self.hub=hub; self.job=None; self.timer=None; self.paths=[None,None]; self.revision=0; self.request=None; self.comparison=None; self.comparison_context=None
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris Compare'); self.window.geometry('860x700'); self.window.minsize(560,550)
        self.window.protocol('WM_DELETE_WINDOW',self.close); self.window.bind('<Escape>',lambda _:self.close()); self.window.bind('<Destroy>',self.destroyed,add='+')
        f=ttk.Frame(self.window,padding=18); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Comparar textos e documentos',font=('Segoe UI',21,'bold')).pack(anchor='w')
        ttk.Label(f,text='Compare linhas de textos ou arquivos TXT, MD, CSV e DOCX (extração parcial).',wraplength=510).pack(anchor='w')
        ttk.Label(f,text='1. Escolha o tipo de comparação',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(6,0))
        self.mode=tk.StringVar(self.window,'Texto'); ttk.Combobox(f,textvariable=self.mode,values=('Texto','Arquivos'),state='readonly').pack(fill='x',pady=4); trace_window(self.window, self.mode, lambda *_:self.mode_changed())
        self.inputs=[]; self.labels=[]; self.buttons=[]
        pair=ttk.Frame(f);pair.pack(fill='both',expand=True)
        for i,name in enumerate(('Original','Revisado')):
            col=ttk.Frame(pair);col.pack(side='left',fill='both',expand=True,padx=3)
            ttk.Label(col,text=name,font=('Segoe UI',11,'bold')).pack(anchor='w')
            b=ttk.Button(col,text='Selecionar arquivo',command=lambda i=i:self.choose(i));b.pack(fill='x');self.buttons.append(b)
            label=tk.StringVar(self.window,'Nenhum arquivo');ttk.Label(col,textvariable=label,wraplength=240).pack(anchor='w');self.labels.append(label)
            t=tk.Text(col,height=6,width=25,wrap='word',undo=False,padx=10,pady=8,relief='flat',highlightthickness=1);t.pack(fill='both',expand=True);self.inputs.append(t)
            t.bind('<<Modified>>',self.edited);t.edit_modified(False)
        actions=ttk.Frame(f);actions.pack(fill='x',pady=4)
        self.run_button=ttk.Button(actions,text='2. Comparar',command=self.run,style='Aeris.Primary.TButton');self.run_button.pack(side='left',fill='x',expand=True)
        self.cancel_button=ttk.Button(actions,text='Cancelar',command=self.cancel);self.cancel_button.pack(side='left',fill='x',expand=True)
        ttk.Button(actions,text='Limpar',command=self.clear).pack(side='left',fill='x',expand=True)
        ttk.Label(f,text='3. Confira as diferenças',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(6,0))
        self.changes_only=tk.BooleanVar(self.window,False)
        ttk.Checkbutton(f,text='Mostrar apenas linhas alteradas',variable=self.changes_only,command=self.render_comparison).pack(anchor='w')
        self.status=tk.StringVar(self.window,'Pronto.');ttk.Label(f,textvariable=self.status,wraplength=520).pack(anchor='w')
        frame=ttk.Frame(f);frame.pack(fill='both',expand=True)
        self.report=tk.Text(frame,height=10,width=45,wrap='none',state='disabled',padx=10,pady=8,relief='flat',highlightthickness=1);self.report.pack(side='left',fill='both',expand=True)
        bar=ttk.Scrollbar(frame,command=self.report.yview);bar.pack(side='right',fill='y');self.report.configure(yscrollcommand=bar.set)
        xbar=ttk.Scrollbar(f,orient='horizontal',command=self.report.xview);xbar.pack(fill='x');self.report.configure(xscrollcommand=xbar.set)
        self.controls()
    def context(self):
        return (self.revision,self.mode.get(),tuple(self.paths) if self.mode.get()=='Arquivos' else tuple(t.get('1.0','end-1c') for t in self.inputs))
    def show(self,text,keep=False):
        if not keep: self.comparison=None; self.comparison_context=None
        self.report.configure(state='normal');self.report.delete('1.0','end');self.report.insert('1.0',text);self.report.configure(state='disabled')
    def controls(self):
        files=self.mode.get()=='Arquivos';allowed=self.hub.permissions.allowed(COMPARE_READ);busy=self.job is not None
        for b in self.buttons:b.configure(state='normal' if files and allowed and not busy else 'disabled')
        for t in self.inputs:t.configure(state='disabled' if files or busy else 'normal')
        self.run_button.configure(state='normal' if not busy and (not files or allowed and all(self.paths)) else 'disabled')
        self.cancel_button.configure(state='normal' if busy else 'disabled')
    def edited(self,event):
        if event.widget.edit_modified():
            event.widget.edit_modified(False);self.revision+=1;self.cancel();self.show('');self.status.set('Texto alterado; compare novamente.')
    def mode_changed(self):
        self.clear();self.controls()
    def permissions_changed(self):
        if self.mode.get()=='Arquivos' and not self.hub.permissions.allowed(COMPARE_READ):self.clear();self.status.set('Autorize Compare → Ler arquivos em Permissões.')
        self.controls()
    def choose(self,i):
        if self.job or self.mode.get()!='Arquivos' or not self.hub.permissions.allowed(COMPARE_READ):return
        reviewed=self.context()
        value=filedialog.askopenfilename(parent=self.window,filetypes=[('Formatos suportados','*.txt *.md *.csv *.docx')])
        if value and self.window.winfo_exists() and self.job is None and reviewed==self.context() and self.mode.get()=='Arquivos' and self.hub.permissions.allowed(COMPARE_READ):
            self.revision+=1;self.paths[i]=value;self.labels[i].set(value);self.show('');self.status.set('Compare novamente.');self.controls()
    def run(self):
        if self.job:return
        files=self.mode.get()=='Arquivos'
        if files:
            if not all(self.paths) or not self.hub.permissions.allowed(COMPARE_READ):return
            selected=tuple(self.paths); reviewed=self.context()
            if not messagebox.askyesno('Ler arquivos?', 'Comparar o texto extraído dos dois arquivos selecionados?',parent=self.window):return
            if not self.window.winfo_exists() or self.job or reviewed!=self.context() or self.mode.get()!='Arquivos' or tuple(self.paths)!=selected or not self.hub.permissions.allowed(COMPARE_READ):return
            args=selected
        else:
            if any((t.count('1.0','end-1c','chars') or (0,))[0]>MAX_CHARS for t in self.inputs):self.status.set('Limite de 100.000 caracteres por texto.');return
            args=tuple(t.get('1.0','end-1c') for t in self.inputs)
            for t in self.inputs:t.edit_modified(False)
        self.request=self.context()
        event=threading.Event();outcome=queue.Queue(1)
        def work():
            try:outcome.put((compare_files if files else compare_texts)(*args,cancelled=event.is_set))
            except Cancelled:outcome.put(None)
            except ValueError as exc:outcome.put(str(exc))
            except Exception:outcome.put('Não foi possível comparar os textos ou arquivos.')
        self.job=(event,outcome,files);self.show('');self.status.set('Comparando...');self.controls();threading.Thread(target=work,daemon=True).start();self.poll()
    def poll(self):
        self.timer=None
        if not self.job:return
        event,outcome,files=self.job
        try:result=outcome.get_nowait()
        except queue.Empty:self.timer=self.window.after(60,self.poll);return
        self.job=None;reviewed=self.request;self.request=None;self.controls()
        if reviewed!=self.context() or event.is_set() or files and not self.hub.permissions.allowed(COMPARE_READ):return
        if isinstance(result,str):self.status.set(result);return
        if result is None:self.status.set('Cancelado.');return
        self.status.set(f'Mantidas: {result.kept} | Removidas: {result.removed} | Adicionadas: {result.added}'+(' | Texto extraído, não bytes.' if files else ''))
        self.comparison=result; self.comparison_context=reviewed; self.render_comparison()
    def render_comparison(self):
        result=self.comparison
        if result is None: return
        if self.comparison_context!=self.context(): self.show(''); self.status.set('Entrada alterada; compare novamente.'); return
        if self.mode.get()=='Arquivos' and not self.hub.permissions.allowed(COMPARE_READ):
            self.show(''); return
        rows=[]
        for r in result.rows:
            if self.changes_only.get() and r.kind==' ': continue
            rows.append(f'{r.kind} {str(r.old or ""):>4} {str(r.new or ""):>4} | '+r.text.rstrip('\n')+('' if r.text.endswith('\n') else ' [sem quebra final]'))
        self.show('\n'.join(rows) if rows else 'Nenhuma linha alterada.',keep=True)
    def cancel(self):
        if self.job:self.job[0].set();self.status.set('Cancelamento solicitado; resultado descartado.');self.show('')
    def clear(self):
        self.revision+=1;self.cancel();self.paths=[None,None]
        for label in self.labels:label.set('Nenhum arquivo')
        for t in self.inputs:t.configure(state='normal');t.delete('1.0','end');t.edit_reset();t.edit_modified(False)
        self.show('');self.status.set('Sessão de comparação limpa.');self.controls()
    def destroyed(self,event):
        if event.widget is self.window:
            if self.job:self.job[0].set()
            if self.timer is not None:self.window.after_cancel(self.timer);self.timer=None
    def close(self):self.cancel();self.window.destroy()
