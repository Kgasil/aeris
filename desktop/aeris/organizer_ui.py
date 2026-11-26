"""Explicit, cancellable folder inventory with no write operations."""
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from aeris.permissions import ORGANIZER_SCAN
from aeris.organizer import scan_folder, Cancelled, safe_name

class OrganizerWindow:
    def __init__(self,hub):
        self.hub=hub; self.job=None; self.timer=None; self.path=None; self.revision=0; self.request=None; self.inventory=None
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris Organizer'); self.window.geometry('680x520'); self.window.minsize(510,460)
        self.window.protocol('WM_DELETE_WINDOW',self.close); self.window.bind('<Escape>',lambda _:self.close())
        self.window.bind('<Destroy>',self.destroyed,add='+')
        f=ttk.Frame(self.window,padding=14); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Aeris Organizer',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text='Classificação por extensão e tamanho. Somente uma pasta, sem mover arquivos. Use exemplos fictícios.',wraplength=460).pack(anchor='w',pady=5)
        self.choose_button=ttk.Button(f,text='Selecionar pasta local',command=self.choose); self.choose_button.pack(fill='x')
        self.filename=tk.StringVar(self.window,'Nenhuma pasta selecionada'); ttk.Label(f,textvariable=self.filename,wraplength=460).pack(anchor='w',pady=4)
        self.run_button=ttk.Button(f,text='Analisar pasta',command=self.run); self.run_button.pack(fill='x',pady=6)
        self.cancel_button=ttk.Button(f,text='Cancelar',command=self.cancel); self.cancel_button.pack(fill='x',pady=4)
        order=ttk.Frame(f); order.pack(fill='x')
        ttk.Label(order,text='Ordenar:').pack(side='left')
        self.order=tk.StringVar(self.window,'Categoria')
        box=ttk.Combobox(order,textvariable=self.order,values=('Categoria','Maior tamanho','Nome'),state='readonly')
        box.pack(side='left',fill='x',expand=True,padx=4)
        box.bind('<<ComboboxSelected>>',lambda _:self.render_inventory())
        frame=ttk.Frame(f); frame.pack(fill='both',expand=True,pady=5)
        self.report=tk.Text(frame,height=10,wrap='word',state='disabled'); self.report.pack(side='left',fill='both',expand=True)
        bar=ttk.Scrollbar(frame,command=self.report.yview); bar.pack(side='right',fill='y'); self.report.configure(yscrollcommand=bar.set)
        ttk.Button(f,text='Limpar resultado',command=self.clear).pack(fill='x')
        self.permissions_changed()
    def context(self): return (self.revision,self.path)
    def show(self,text,keep=False):
        if not keep: self.inventory=None
        self.report.configure(state='normal'); self.report.delete('1.0','end'); self.report.insert('1.0',text); self.report.configure(state='disabled')
    def controls(self):
        allowed=self.hub.permissions.allowed(ORGANIZER_SCAN); busy=self.job is not None
        self.choose_button.configure(state='normal' if allowed and not busy else 'disabled')
        self.run_button.configure(state='normal' if allowed and not busy and self.path else 'disabled')
        self.cancel_button.configure(state='normal' if busy else 'disabled')
    def permissions_changed(self):
        if not self.hub.permissions.allowed(ORGANIZER_SCAN): self.clear(); self.show('Autorize Organizer → Listar pasta em Permissões.')
        self.controls()
    def choose(self):
        if self.job or not self.hub.permissions.allowed(ORGANIZER_SCAN): return
        reviewed=self.context()
        value=filedialog.askdirectory(parent=self.window,title='Selecione pasta fictícia',mustexist=True)
        if value and self.window.winfo_exists() and self.job is None and reviewed==self.context() and self.hub.permissions.allowed(ORGANIZER_SCAN):
            self.revision+=1; self.path=value; self.filename.set(safe_name(value)); self.show('Resultado pendente.'); self.controls()
    def run(self):
        if self.job or not self.path or not self.hub.permissions.allowed(ORGANIZER_SCAN): return
        reviewed=self.context()
        if not messagebox.askyesno('Listar pasta?', 'Listar nomes e tamanhos dos arquivos desta pasta? A prévia pode revelar dados pessoais.',parent=self.window): return
        if not self.window.winfo_exists() or self.job or reviewed!=self.context() or not self.hub.permissions.allowed(ORGANIZER_SCAN): return
        self.request=reviewed
        event=threading.Event(); outcome=queue.Queue(1); path=self.path
        def work():
            try: outcome.put(scan_folder(path,cancelled=event.is_set))
            except Cancelled: outcome.put(None)
            except ValueError as exc: outcome.put(str(exc))
            except Exception: outcome.put('Não foi possível listar a pasta.')
        self.job=(event,outcome); self.controls(); self.show('Analisando pasta...')
        threading.Thread(target=work,daemon=True).start(); self.poll()
    def poll(self):
        self.timer=None
        if self.job is None: return
        event,outcome=self.job
        try: result=outcome.get_nowait()
        except queue.Empty: self.timer=self.window.after(60,self.poll); return
        self.job=None; reviewed=self.request; self.request=None; self.controls()
        if event.is_set() or reviewed!=self.context() or not self.hub.permissions.allowed(ORGANIZER_SCAN): return
        if isinstance(result,str): self.show(result); return
        if result is None: self.show('Cancelado.'); return
        self.inventory=result; self.render_inventory()
    def render_inventory(self):
        result=self.inventory
        if result is None or not self.hub.permissions.allowed(ORGANIZER_SCAN): return
        files=result.files
        if self.order.get()=='Maior tamanho': files=sorted(files,key=lambda x:(-x.size,x.name.casefold(),x.name))
        elif self.order.get()=='Nome': files=sorted(files,key=lambda x:(x.name.casefold(),x.name))
        lines=[f'Arquivos listados: {len(files)} | Entradas ignoradas: {result.skipped}',
               f'Tamanho total listado: {sum(x.size for x in files):,} bytes | Ordem: {self.order.get()}',
               'Sugestão por categoria (não cria pastas nem move arquivos).']
        if result.truncated: lines.append('Resultado parcial: limite de 2.000 entradas atingido.')
        lines.extend(f'{label}: {count} arquivos | {size:,} bytes' for label,count,size in result.totals)
        lines.append('\nCategoria | Tamanho em bytes | Nome')
        lines.extend(f'{item.category} | {item.size:,} | {item.name}' for item in files)
        self.show('\n'.join(lines),keep=True)
    def cancel(self):
        if self.job: self.job[0].set(); self.show('Cancelamento solicitado; resultado descartado.')
    def clear(self):
        self.revision+=1; self.cancel(); self.path=None; self.filename.set('Nenhuma pasta selecionada'); self.show('Resultado descartado.'); self.controls()
    def destroyed(self,event):
        if event.widget is self.window:
            if self.job: self.job[0].set()
            if self.timer is not None: self.window.after_cancel(self.timer); self.timer=None
    def close(self):
        self.cancel(); self.window.destroy()
