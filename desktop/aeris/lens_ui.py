"""Explicit, cancellable OCR preview."""
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from aeris.permissions import LENS_READ
from aeris.lens import recognize, Cancelled, LANGUAGES
from aeris.window_lifecycle import trace_window

class LensWindow:
    def __init__(self,hub):
        self.hub=hub; self.job=None; self.timer=None; self.path=None; self.revision=0; self.request=None
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris Lens'); self.window.geometry('680x520'); self.window.minsize(510,460)
        self.window.protocol('WM_DELETE_WINDOW',self.close); self.window.bind('<Escape>',lambda _:self.close())
        self.window.bind('<Destroy>',self.destroyed,add='+')
        f=ttk.Frame(self.window,padding=14); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Aeris Lens',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text='OCR local opcional Tesseract. PNG/JPEG até 8 MiB e 12 megapixels. Use imagens fictícias.',wraplength=460).pack(anchor='w',pady=5)
        self.choose_button=ttk.Button(f,text='Selecionar arquivo local',command=self.choose); self.choose_button.pack(fill='x')
        self.filename=tk.StringVar(self.window,'Nenhum arquivo selecionado'); ttk.Label(f,textvariable=self.filename,wraplength=460).pack(anchor='w',pady=4)
        self.language=tk.StringVar(self.window,'Português'); self.lang_box=ttk.Combobox(f,textvariable=self.language,values=tuple(LANGUAGES),state='readonly'); self.lang_box.pack(fill='x',pady=4)

        self.run_button=ttk.Button(f,text='Reconhecer texto',command=self.run); self.run_button.pack(fill='x',pady=6)
        self.cancel_button=ttk.Button(f,text='Cancelar',command=self.cancel); self.cancel_button.pack(fill='x',pady=4)
        frame=ttk.Frame(f); frame.pack(fill='both',expand=True,pady=5)
        self.report=tk.Text(frame,height=10,wrap='word',state='disabled'); self.report.pack(side='left',fill='both',expand=True)
        bar=ttk.Scrollbar(frame,command=self.report.yview); bar.pack(side='right',fill='y'); self.report.configure(yscrollcommand=bar.set)
        ttk.Button(f,text='Limpar resultado',command=self.clear).pack(fill='x')
        self.permissions_changed()
        trace_window(self.window,self.language,self.language_changed)
    def language_changed(self,*_):
        self.revision+=1; self.cancel(); self.show('Idioma alterado; execute novamente.')
    def context(self): return (self.revision,self.path,self.language.get())
    def show(self,text):
        self.report.configure(state='normal'); self.report.delete('1.0','end'); self.report.insert('1.0',text); self.report.configure(state='disabled')
    def controls(self):
        allowed=self.hub.permissions.allowed(LENS_READ); busy=self.job is not None
        self.choose_button.configure(state='normal' if allowed and not busy else 'disabled')
        self.run_button.configure(state='normal' if allowed and not busy and self.path else 'disabled')
        self.cancel_button.configure(state='normal' if busy else 'disabled')
        self.lang_box.configure(state='disabled' if busy else 'readonly')
    def permissions_changed(self):
        if not self.hub.permissions.allowed(LENS_READ): self.clear(); self.show('Autorize Lens → Ler imagem em Permissões.')
        self.controls()
    def choose(self):
        if self.job or not self.hub.permissions.allowed(LENS_READ): return
        reviewed=self.context()
        value=filedialog.askopenfilename(parent=self.window,title='Selecione arquivo fictício',filetypes=[('Imagens PNG/JPEG','*.png *.jpg *.jpeg')])
        if value and self.window.winfo_exists() and self.job is None and reviewed==self.context() and self.hub.permissions.allowed(LENS_READ):
            self.revision+=1; self.path=value; self.filename.set(value); self.show('Resultado pendente.'); self.controls()
    def run(self):
        if self.job or not self.path or not self.hub.permissions.allowed(LENS_READ): return
        selected=(self.path,self.language.get()); reviewed=self.context()
        if not messagebox.askyesno('Ler arquivo?', 'Reconhecer texto da imagem selecionada com Tesseract local? A prévia pode revelar dados pessoais.',parent=self.window): return
        if not self.window.winfo_exists() or self.job or reviewed!=self.context() or not self.hub.permissions.allowed(LENS_READ): return
        self.request=reviewed
        event=threading.Event(); outcome=queue.Queue(1); path,language=selected
        def work():
            try: outcome.put(recognize(path,language,cancelled=event.is_set))
            except Cancelled: outcome.put(None)
            except ValueError as exc: outcome.put(str(exc))
            except Exception: outcome.put('Não foi possível ler o arquivo.')
        self.job=(event,outcome); self.controls(); self.show('Reconhecendo texto...')
        threading.Thread(target=work,daemon=False).start(); self.poll()
    def poll(self):
        self.timer=None
        if self.job is None: return
        event,outcome=self.job
        try: result=outcome.get_nowait()
        except queue.Empty: self.timer=self.window.after(60,self.poll); return
        self.job=None; reviewed=self.request; self.request=None; self.controls()
        if event.is_set() or reviewed!=self.context() or not self.hub.permissions.allowed(LENS_READ): return
        if isinstance(result,str): self.show(result); return
        if result is None: self.show('Cancelado.'); return
        heading=f'Idioma: {self.language.get()} | Formato: {result.format} | {result.width} × {result.height} | Palavras na prévia: {len(result.text.split())}\n'
        if result.truncated: heading+='Prévia limitada a 100.000 caracteres.\n'
        self.show(heading+'OCR pode conter erros. Imagem original preservada.\n\n'+(result.text or 'Nenhum texto reconhecido.'))
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
