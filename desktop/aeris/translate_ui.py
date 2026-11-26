"""Explicit, session-only translation; no automatic clipboard or screen access."""
import json
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from aeris.window_lifecycle import trace_window
from tkinter import ttk, messagebox
from aeris.translate import LANGUAGES, PHRASES, phrase_translate, validate
from pathlib import Path
from aeris.permissions import COPY_TRANSLATION
from aeris.distribution import translation_worker_available

class TranslateWindow:
    def __init__(self,hub):
        self.hub=hub; self.process=None; self.job=0; self.output=''; self.snapshot=None; self.request=None; self.result_generation=0
        self.results=queue.Queue(); self.timer=None
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris · Translate')
        self.window.geometry('560x540'); self.window.minsize(440,480)
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.window.bind('<Escape>',lambda _:self.close())
        self.window.bind('<Destroy>',self.destroyed,add='+')
        f=ttk.Frame(self.window,padding=16); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Traduzir texto',font=('Segoe UI',21,'bold')).pack(anchor='w')
        ttk.Label(f,text=('Guia de 12 frases por idioma; textos livres exigem modelos locais preparados.' if translation_worker_available() else 'Guia de 12 frases por idioma. Argos experimental disponível somente na execução por código-fonte.'),wraplength=400).pack(anchor='w')
        ttk.Label(f,text='1. Escolha o modo e os idiomas',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(8,0))
        self.mode=tk.StringVar(self.window,'Guia de frases')
        ttk.Combobox(f,textvariable=self.mode,values=('Guia de frases','Modelo local (experimental)') if translation_worker_available() else ('Guia de frases',),state='readonly').pack(fill='x',pady=4)
        row=ttk.Frame(f); row.pack(fill='x',pady=3)
        self.source=tk.StringVar(self.window,'Português'); self.target=tk.StringVar(self.window,'Inglês')
        ttk.Combobox(row,textvariable=self.source,values=tuple(LANGUAGES.values()),state='readonly',width=14).pack(side='left',fill='x',expand=True)
        ttk.Button(row,text='Inverter',command=self.swap).pack(side='left',padx=4)
        ttk.Combobox(row,textvariable=self.target,values=tuple(LANGUAGES.values()),state='readonly',width=14).pack(side='left',fill='x',expand=True)
        self.example=tk.StringVar(self.window,'Escolher frase do guia…')
        self.examples=ttk.Combobox(f,textvariable=self.example,state='readonly')
        self.examples.pack(fill='x',pady=2)
        self.examples.bind('<<ComboboxSelected>>',self.use_example)
        ttk.Label(f,text='2. Texto para traduzir',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(5,0))
        self.input=tk.Text(f,height=5,wrap='word',padx=10,pady=8,relief='flat',highlightthickness=1); self.input.pack(fill='both',expand=True,pady=4)
        btn=ttk.Frame(f); btn.pack(fill='x')
        self.go=ttk.Button(btn,text='Traduzir',style='Aeris.Primary.TButton',command=self.translate); self.go.pack(side='left')
        ttk.Button(btn,text='Limpar / cancelar',command=self.clear).pack(side='left',padx=4)
        ttk.Label(f,text='3. Tradução',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(6,0))
        self.result=tk.Text(f,height=5,wrap='word',state='disabled',padx=10,pady=8,relief='flat',highlightthickness=1); self.result.pack(fill='both',expand=True,pady=4)
        self.copy_button=ttk.Button(f,text='Copiar tradução',command=self.copy); self.copy_button.pack(fill='x')
        self.status=tk.StringVar(self.window,'Use dados fictícios. Nenhum histórico é salvo.')
        ttk.Label(f,textvariable=self.status,wraplength=400).pack(anchor='w',pady=4)
        self.permissions_changed()
        trace_window(self.window, self.source, self.refresh_examples)
        self.refresh_examples()
        for var in (self.source,self.target,self.mode): trace_window(self.window,var,self.invalidate)
        self.input.bind('<<Modified>>',self.modified); self.input.edit_modified(False)

    def context(self):
        return (self.input.get('1.0','end-1c'),self.source.get(),self.target.get(),self.mode.get())

    def modified(self,_=None):
        if self.input.edit_modified():
            self.input.edit_modified(False); self.invalidate()

    def invalidate(self,*_):
        self.cancel(); self.set_result(''); self.status.set('Entrada alterada. Traduza novamente.')

    def refresh_examples(self,*_):
        i=tuple(LANGUAGES.values()).index(self.source.get())
        self.examples.configure(values=tuple(row[i] for row in PHRASES))
        self.example.set('Escolher frase do guia…')
    def use_example(self,_=None):
        self.cancel(); self.set_result(''); self.input.delete('1.0','end'); self.input.insert('1.0',self.example.get())
    def set_result(self,text):
        self.result_generation+=1; self.snapshot=self.context() if text else None
        self.output=text; self.result.configure(state='normal'); self.result.delete('1.0','end'); self.result.insert('1.0',text); self.result.configure(state='disabled'); self.permissions_changed()
    def permissions_changed(self):
        self.copy_button.configure(state='normal' if self.output and self.hub.permissions.allowed(COPY_TRANSLATION) else 'disabled')
    def swap(self):
        a,b=self.source.get(),self.target.get(); self.source.set(b); self.target.set(a); self.cancel(); self.set_result('')
    def translate(self):
        self.cancel(); self.set_result(''); self.input.edit_modified(False)
        request=self.context(); generation=self.job
        codes={v:k for k,v in LANGUAGES.items()}; text=self.input.get('1.0','end-1c')
        a,b=codes[self.source.get()],codes[self.target.get()]
        try:
            validate(text,a,b)
            if self.mode.get()=='Guia de frases':
                self.set_result(phrase_translate(text,a,b)); self.status.set('Frase do guia local.'); return
        except ValueError as e: self.status.set(str(e)); return
        if not translation_worker_available():
            self.status.set('Argos experimental indisponível na edição empacotada.'); return
        if not messagebox.askyesno('Modelo experimental','Utilizar modelos locais previamente instalados? Nenhum download será iniciado pelo Aeris. Use somente texto fictício.',parent=self.window): return
        if not self.window.winfo_exists() or self.context()!=request or self.job!=generation: return
        self.request=request
        try:
            flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
            self.process=subprocess.Popen([sys.executable,'-m','aeris.translate_worker'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf-8',creationflags=flags,cwd=Path(__file__).resolve().parent.parent)
        except OSError: self.status.set('Não foi possível iniciar o motor local.'); return
        process=self.process; job=self.job; payload=json.dumps(dict(text=text,source=a,target=b))
        def work():
            try:
                out,_=process.communicate(payload,timeout=90)
                result=json.loads(out)
            except Exception:
                process.kill() if process.poll() is None else None
                process.communicate(); result={'ok':False}
            self.results.put((job,result))
        threading.Thread(target=work,daemon=True).start()
        self.go.configure(state='disabled'); self.status.set('Traduzindo localmente…'); self.timer=self.window.after(80,self.poll)
    def poll(self):
        self.timer=None
        while True:
            try: job,res=self.results.get_nowait()
            except queue.Empty: break
            if job!=self.job: continue
            self.process=None; self.go.configure(state='normal')
            if self.request!=self.context():
                self.set_result(''); self.status.set('Entrada alterada. Traduza novamente.'); return
            if isinstance(res,dict) and res.get('ok') is True and isinstance(res.get('text'),str): self.set_result(res['text']); self.status.set('Tradução automática: revise o resultado.')
            else: self.status.set('Motor ou recursos locais indisponíveis. Prepare o Argos fora do Aeris.')
            return
        if self.process is not None: self.timer=self.window.after(80,self.poll)
    def cancel(self):
        self.job+=1; self.request=None
        if self.timer is not None: self.window.after_cancel(self.timer); self.timer=None
        if self.process is not None:
            if self.process.poll() is None: self.process.kill()
            self.process=None
        self.go.configure(state='normal')
    def clear(self): self.cancel(); self.input.delete('1.0','end'); self.set_result(''); self.status.set('Sessão de tradução limpa.')
    def copy(self):
        if not self.output or not self.hub.permissions.allowed(COPY_TRANSLATION): return
        if self.snapshot!=self.context(): self.invalidate(); return
        reviewed=self.output; generation=self.result_generation
        if not messagebox.askyesno('Copiar tradução?','O texto substituirá o clipboard e poderá permanecer no histórico.',parent=self.window): return
        if not self.window.winfo_exists() or not self.hub.permissions.allowed(COPY_TRANSLATION): return
        if self.result_generation!=generation or self.snapshot!=self.context() or self.output!=reviewed:
            self.invalidate(); return
        try: self.hub.root.clipboard_clear(); self.hub.root.clipboard_append(reviewed)
        except tk.TclError: self.status.set('Falha ao copiar.'); return
        self.status.set('Copiado. Cole manualmente.')
    def close(self): self.cancel(); self.window.destroy()
    def destroyed(self,event):
        if event.widget is self.window and self.process is not None:
            if self.process.poll() is None: self.process.kill()
            self.process=None
