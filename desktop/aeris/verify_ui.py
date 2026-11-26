"""File hashing in a cancellable worker; Tk operations stay on the main thread."""
import queue
import threading
import tkinter as tk
from aeris.window_lifecycle import trace_window
from tkinter import ttk, filedialog, messagebox
from aeris.permissions import VERIFY_READ
from aeris.verify import ALGORITHMS, Cancelled, expected_hash, hash_file

class VerifyWindow:
    def __init__(self,hub):
        self.hub=hub; self.job=None; self.timer=None; self.path=None; self.revision=0; self.request=None
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris Verify'); self.window.geometry('680x520'); self.window.minsize(510,460)
        self.window.protocol('WM_DELETE_WINDOW',self.close); self.window.bind('<Escape>',lambda _:self.close())
        self.window.bind('<Destroy>',self.destroyed,add='+')
        f=ttk.Frame(self.window,padding=18); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Verificar integridade de arquivo',font=('Segoe UI',21,'bold')).pack(anchor='w')
        ttk.Label(f,text='Calcule e compare hashes. Uma correspondência não garante que o arquivo seja seguro ou autêntico.',wraplength=470).pack(anchor='w',pady=5)
        ttk.Label(f,text='1. Selecione o arquivo',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(6,4))
        source=ttk.Frame(f); source.pack(fill='x')
        self.choose_button=ttk.Button(source,text='Selecionar arquivo local',command=self.choose); self.choose_button.pack(side='left',fill='x',expand=True)
        ttk.Button(source,text='Permissões',command=hub.open_permissions).pack(side='right',padx=(6,0))
        self.filename=tk.StringVar(self.window,'Nenhum arquivo selecionado'); ttk.Label(f,textvariable=self.filename,wraplength=460).pack(anchor='w',pady=4)
        ttk.Label(f,text='2. Escolha o algoritmo de verificação',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(6,0))
        self.algorithm=tk.StringVar(self.window,'SHA-256'); self.combo=ttk.Combobox(f,textvariable=self.algorithm,values=tuple(ALGORITHMS),state='readonly'); self.combo.pack(fill='x')
        ttk.Label(f,text='Hash esperado (opcional, de uma fonte confiável)').pack(anchor='w',pady=(6,0))
        self.expected=tk.StringVar(self.window); self.entry=ttk.Entry(f,textvariable=self.expected); self.entry.pack(fill='x')
        self.run_button=ttk.Button(f,text='Calcular / comparar',command=self.run,style='Aeris.Primary.TButton'); self.run_button.pack(fill='x',pady=6)
        self.progress=ttk.Progressbar(f,maximum=100); self.progress.pack(fill='x')
        self.cancel_button=ttk.Button(f,text='Cancelar',command=self.cancel); self.cancel_button.pack(fill='x',pady=4)
        ttk.Label(f,text='3. Resultado da verificação',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(6,0))
        self.report=tk.Text(f,height=6,wrap='word',state='disabled',padx=12,pady=10,relief='flat',highlightthickness=1); self.report.pack(fill='both',expand=True,pady=5)
        ttk.Button(f,text='Limpar sessão da ferramenta',command=self.clear).pack(fill='x')
        for var in (self.algorithm,self.expected): trace_window(self.window,var,self.options_changed)
        self.permissions_changed()
    def options_changed(self,*_):
        self.revision+=1; self.cancel(); self.progress['value']=0; self.show('Opções alteradas. Calcule novamente.')
    def context(self): return (self.revision,self.path,self.algorithm.get(),self.expected.get())
    def show(self,text):
        self.report.configure(state='normal'); self.report.delete('1.0','end'); self.report.insert('1.0',text); self.report.configure(state='disabled')
    def controls(self):
        allowed=self.hub.permissions.allowed(VERIFY_READ); busy=self.job is not None
        self.choose_button.configure(state='normal' if allowed and not busy else 'disabled')
        self.run_button.configure(state='normal' if allowed and not busy and self.path else 'disabled')
        self.cancel_button.configure(state='normal' if busy else 'disabled')
        self.combo.configure(state='disabled' if busy else 'readonly'); self.entry.configure(state='disabled' if busy else 'normal')
    def permissions_changed(self):
        if not self.hub.permissions.allowed(VERIFY_READ):
            self.clear(); self.show('Autorize Verify → Ler arquivo em Permissões.')
        self.controls()
    def choose(self):
        if self.job or not self.hub.permissions.allowed(VERIFY_READ): return
        reviewed=self.context(); permission_revision=self.hub.permissions.revision
        value=filedialog.askopenfilename(parent=self.window,title='Selecione um arquivo local fictício')
        if value and self.window.winfo_exists() and self.job is None and reviewed==self.context() and permission_revision==self.hub.permissions.revision and self.hub.permissions.allowed(VERIFY_READ):
            self.revision+=1; self.path=value; self.filename.set(value); self.show('Resultado pendente.'); self.progress['value']=0; self.controls()
    def run(self):
        if self.job or not self.path or not self.hub.permissions.allowed(VERIFY_READ): return
        try: expected=expected_hash(self.algorithm.get(),self.expected.get())
        except ValueError as exc: self.show(str(exc)); return
        reviewed=self.context(); permission_revision=self.hub.permissions.revision
        if not messagebox.askyesno('Ler arquivo?', 'Ler o arquivo selecionado para calcular o hash, sem modificar seu conteúdo?',parent=self.window): return
        if not self.window.winfo_exists() or self.job or reviewed!=self.context() or permission_revision!=self.hub.permissions.revision or not self.hub.permissions.allowed(VERIFY_READ): return
        self.request=reviewed
        event=threading.Event(); outcome=queue.Queue(1); progress=[(0,0)]
        path=self.path; algorithm=self.algorithm.get()
        def work():
            try: outcome.put(hash_file(path,algorithm,expected,cancelled=event.is_set,progress=lambda a,b:progress.__setitem__(0,(a,b))))
            except Cancelled: outcome.put(None)
            except ValueError as exc: outcome.put(str(exc))
            except Exception: outcome.put('Não foi possível ler o arquivo.')
        self.job=(event,outcome,progress); self.controls(); self.show('Calculando...')
        threading.Thread(target=work,daemon=True).start(); self.poll()
    def poll(self):
        self.timer=None
        if self.job is None: return
        event,outcome,progress=self.job
        done,total=progress[0]
        if not event.is_set(): self.progress['value']=100*done/total if total else 0
        try: result=outcome.get_nowait()
        except queue.Empty: self.timer=self.window.after(60,self.poll); return
        self.job=None; reviewed=self.request; self.request=None; self.controls()
        if event.is_set() or reviewed!=self.context() or not self.hub.permissions.allowed(VERIFY_READ): return
        if isinstance(result,str): self.show(result); return
        if result is None: self.show('Cancelado.'); return
        self.progress['value']=100
        comparison='Hash calculado; nenhum esperado informado.' if result.matches is None else ('Hashes correspondentes.' if result.matches else 'Hashes diferentes.')
        self.show(f'{result.algorithm} · {result.size} bytes\n{result.digest}\n\n{comparison}\nNão comprova autenticidade nem ausência de malware.')
    def cancel(self):
        if self.job: self.job[0].set(); self.show('Cancelamento solicitado; resultado descartado.'); self.progress['value']=0
    def clear(self):
        self.revision+=1; self.cancel(); self.path=None; self.filename.set('Nenhum arquivo selecionado'); self.expected.set(''); self.progress['value']=0; self.show('Resultado descartado.'); self.controls()
    def destroyed(self,event):
        if event.widget is self.window:
            if self.job: self.job[0].set()
            if self.timer is not None: self.window.after_cancel(self.timer); self.timer=None
    def close(self):
        self.cancel(); self.window.destroy()
