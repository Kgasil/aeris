"""Explicit, cancellable document text preview with no write operations."""
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from aeris.permissions import DOCUMENTS_READ
from aeris.documents import extract_file, Cancelled

class DocumentsWindow:
    def __init__(self,hub):
        self.hub=hub; self.job=None; self.timer=None; self.path=None; self.revision=0; self.request=None
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris Documents'); self.window.geometry('680x520'); self.window.minsize(510,460)
        self.window.protocol('WM_DELETE_WINDOW',self.close); self.window.bind('<Escape>',lambda _:self.close())
        self.window.bind('<Destroy>',self.destroyed,add='+')
        f=ttk.Frame(self.window,padding=14); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Aeris Documents',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text='Prévia local de TXT, MD, CSV (até 1 MiB) e DOCX (até 8 MiB). Use arquivos fictícios.',wraplength=460).pack(anchor='w',pady=5)
        self.choose_button=ttk.Button(f,text='Selecionar arquivo local',command=self.choose); self.choose_button.pack(fill='x')
        self.filename=tk.StringVar(self.window,'Nenhum arquivo selecionado'); ttk.Label(f,textvariable=self.filename,wraplength=460).pack(anchor='w',pady=4)
        self.run_button=ttk.Button(f,text='Extrair texto',command=self.run); self.run_button.pack(fill='x',pady=6)
        self.cancel_button=ttk.Button(f,text='Cancelar',command=self.cancel); self.cancel_button.pack(fill='x',pady=4)
        find=ttk.Frame(f); find.pack(fill='x')
        self.query=tk.StringVar(self.window)
        entry=ttk.Entry(find,textvariable=self.query); entry.pack(side='left',fill='x',expand=True)
        ttk.Button(find,text='Localizar próxima',command=self.find_next).pack(side='left',padx=3)
        self.find_status=tk.StringVar(self.window)
        ttk.Label(f,textvariable=self.find_status).pack(anchor='w')
        entry.bind('<Return>',lambda _:self.find_next())
        self.window.bind('<Control-f>',lambda _:entry.focus_set())
        self.match_end='1.0'; self.last_query=''
        frame=ttk.Frame(f); frame.pack(fill='both',expand=True,pady=5)
        self.report=tk.Text(frame,height=10,wrap='word',state='disabled'); self.report.pack(side='left',fill='both',expand=True)
        bar=ttk.Scrollbar(frame,command=self.report.yview); bar.pack(side='right',fill='y'); self.report.configure(yscrollcommand=bar.set)
        ttk.Button(f,text='Limpar resultado',command=self.clear).pack(fill='x')
        self.permissions_changed()
    def context(self): return (self.revision,self.path)
    def find_next(self):
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
        self.report.configure(state='normal'); self.report.delete('1.0','end'); self.report.insert('1.0',text); self.report.configure(state='disabled')
    def controls(self):
        allowed=self.hub.permissions.allowed(DOCUMENTS_READ); busy=self.job is not None
        self.choose_button.configure(state='normal' if allowed and not busy else 'disabled')
        self.run_button.configure(state='normal' if allowed and not busy and self.path else 'disabled')
        self.cancel_button.configure(state='normal' if busy else 'disabled')
    def permissions_changed(self):
        if not self.hub.permissions.allowed(DOCUMENTS_READ): self.clear(); self.show('Autorize Documents → Ler arquivo em Permissões.')
        self.controls()
    def choose(self):
        if self.job or not self.hub.permissions.allowed(DOCUMENTS_READ): return
        reviewed=self.context()
        value=filedialog.askopenfilename(parent=self.window,title='Selecione arquivo fictício',filetypes=[('Formatos suportados','*.txt *.md *.csv *.docx'),('Todos','*')])
        if value and self.window.winfo_exists() and self.job is None and reviewed==self.context() and self.hub.permissions.allowed(DOCUMENTS_READ):
            self.revision+=1; self.path=value; self.filename.set(value); self.show('Resultado pendente.'); self.controls()
    def run(self):
        if self.job or not self.path or not self.hub.permissions.allowed(DOCUMENTS_READ): return
        reviewed=self.context()
        if not messagebox.askyesno('Ler arquivo?', 'Extrair texto do arquivo selecionado? A prévia pode revelar dados pessoais.',parent=self.window): return
        if not self.window.winfo_exists() or self.job or reviewed!=self.context() or not self.hub.permissions.allowed(DOCUMENTS_READ): return
        self.request=reviewed
        event=threading.Event(); outcome=queue.Queue(1); path=self.path
        def work():
            try: outcome.put(extract_file(path,cancelled=event.is_set))
            except Cancelled: outcome.put(None)
            except ValueError as exc: outcome.put(str(exc))
            except Exception: outcome.put('Não foi possível ler o arquivo.')
        self.job=(event,outcome); self.controls(); self.show('Extraindo texto...')
        threading.Thread(target=work,daemon=True).start(); self.poll()
    def poll(self):
        self.timer=None
        if self.job is None: return
        event,outcome=self.job
        try: result=outcome.get_nowait()
        except queue.Empty: self.timer=self.window.after(60,self.poll); return
        self.job=None; reviewed=self.request; self.request=None; self.controls()
        if event.is_set() or reviewed!=self.context() or not self.hub.permissions.allowed(DOCUMENTS_READ): return
        if isinstance(result,str): self.show(result); return
        if result is None: self.show('Cancelado.'); return
        heading=f'Formato: {result.format} | Palavras na prévia: {result.words} | Linhas: {result.lines}\n'
        if result.truncated: heading+='Prévia limitada a 100.000 caracteres.\n'
        self.show(heading+'Extração parcial, sem formatação. Arquivo original preservado.\n\n'+result.text)
    def cancel(self):
        if self.job: self.job[0].set(); self.show('Cancelamento solicitado; resultado descartado.')
    def clear(self):
        self.query.set(''); self.revision+=1; self.cancel(); self.path=None; self.filename.set('Nenhum arquivo selecionado'); self.show('Resultado descartado.'); self.controls()
    def destroyed(self,event):
        if event.widget is self.window:
            if self.job: self.job[0].set()
            if self.timer is not None: self.window.after_cancel(self.timer); self.timer=None
    def close(self):
        self.cancel(); self.window.destroy()
