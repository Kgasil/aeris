"""Manual selection and authorized copying of path references."""
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from aeris.drop import inspect_paths, Cancelled
from aeris.organizer import safe_name
from aeris.permissions import DROP_ADD, DROP_COPY

class DropWindow:
    def __init__(self,hub):
        self.hub=hub; self.store=hub.drop_store; self.job=None; self.timer=None; self.items=(); self.revision=0
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris Drop'); self.window.geometry('700x520'); self.window.minsize(500,400)
        self.window.protocol('WM_DELETE_WINDOW',self.close); self.window.bind('<Escape>',lambda _:self.close())
        self.window.bind('<Destroy>',self.destroyed,add='+')
        f=ttk.Frame(self.window,padding=14); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Aeris Drop',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text='Prateleira de referências temporárias. Tamanhos são da seleção, não atualizados automaticamente. Use arquivos fictícios.',wraplength=460).pack(anchor='w',pady=5)
        self.add_button=ttk.Button(f,text='Adicionar arquivos locais…',command=self.choose); self.add_button.pack(fill='x')
        self.cancel_button=ttk.Button(f,text='Cancelar adição',command=self.cancel); self.cancel_button.pack(fill='x',pady=4)
        frame=ttk.Frame(f); frame.pack(fill='both',expand=True,pady=5)
        self.listbox=tk.Listbox(frame,selectmode='extended',exportselection=False); self.listbox.pack(side='left',fill='both',expand=True)
        bar=ttk.Scrollbar(frame,command=self.listbox.yview); bar.pack(side='right',fill='y'); self.listbox.configure(yscrollcommand=bar.set)
        self.listbox.bind('<<ListboxSelect>>',lambda _:self.controls())
        selection=ttk.Frame(f); selection.pack(fill='x')
        ttk.Button(selection,text='Selecionar todas',command=self.select_all).pack(side='left')
        ttk.Button(selection,text='Limpar seleção',command=self.unselect_all).pack(side='left',padx=4)
        self.summary=tk.StringVar(self.window); ttk.Label(f,textvariable=self.summary).pack(anchor='w')
        self.status=tk.StringVar(self.window); ttk.Label(f,textvariable=self.status,wraplength=460).pack(anchor='w',pady=5)
        self.remove_button=ttk.Button(f,text='Remover referências selecionadas',command=self.remove); self.remove_button.pack(fill='x')
        self.copy_button=ttk.Button(f,text='Copiar caminhos selecionados',command=self.copy); self.copy_button.pack(fill='x',pady=4)
        ttk.Button(f,text='Limpar prateleira',command=self.clear).pack(fill='x')
        self.permissions_changed()
    def selected(self): return tuple(self.items[i].path for i in self.listbox.curselection() if i<len(self.items))
    def select_all(self):
        self.listbox.selection_set(0,'end'); self.controls()
    def unselect_all(self):
        self.listbox.selection_clear(0,'end'); self.controls()
    def refresh(self):
        reviewed=set(self.selected())
        self.items=self.store.list(); self.listbox.delete(0,'end')
        for item in self.items: self.listbox.insert('end',f'{safe_name(Path(item.path).name)} | {item.size:,} bytes | {safe_name(item.path)}')
        for i,item in enumerate(self.items):
            if item.path in reviewed: self.listbox.selection_set(i)
        self.controls()
        if self.hub.alive(self.hub.privacy_window): self.hub.privacy_window.refresh()
    def controls(self):
        allowed=self.hub.permissions.allowed(DROP_ADD); busy=self.job is not None; selected=bool(self.selected())
        paths=set(self.selected())
        self.summary.set(f'{len(self.items)}/100 referências | {len(paths)} selecionadas | {sum(i.size for i in self.items if i.path in paths):,} bytes selecionados (estimativa da adição)')
        self.add_button.configure(state='normal' if allowed and not busy else 'disabled')
        self.cancel_button.configure(state='normal' if busy else 'disabled')
        self.remove_button.configure(state='normal' if selected else 'disabled')
        self.copy_button.configure(state='normal' if selected and allowed and self.hub.permissions.allowed(DROP_COPY) else 'disabled')
    def permissions_changed(self):
        if not self.hub.permissions.allowed(DROP_ADD):
            self.revision+=1; self.cancel(); self.store.clear(); self.status.set('Autorize Drop → Adicionar em Permissões.')
        self.refresh()
    def choose(self):
        if self.job or not self.hub.permissions.allowed(DROP_ADD): return
        reviewed=self.revision
        paths=filedialog.askopenfilenames(parent=self.window,title='Selecione arquivos fictícios')
        if not paths or len(paths)>100:
            if paths: self.status.set('Selecione até 100 arquivos.')
            return
        if not self.window.winfo_exists() or self.job or reviewed!=self.revision or not self.hub.permissions.allowed(DROP_ADD): return
        if not messagebox.askyesno('Adicionar referências?',f'Consultar nomes e tamanhos de {len(paths)} arquivos? Nenhum conteúdo será lido.',parent=self.window): return
        if not self.window.winfo_exists() or self.job or reviewed!=self.revision or not self.hub.permissions.allowed(DROP_ADD): return
        event=threading.Event(); outcome=queue.Queue(1)
        def work():
            try: outcome.put(inspect_paths(paths,cancelled=event.is_set))
            except Cancelled: outcome.put(None)
            except ValueError as exc: outcome.put(str(exc))
            except Exception: outcome.put('Não foi possível consultar os arquivos selecionados.')
        self.job=(event,outcome); self.status.set('Consultando referências…'); self.controls()
        threading.Thread(target=work,daemon=True).start(); self.poll()
    def poll(self):
        self.timer=None
        if self.job is None: return
        event,outcome=self.job
        try: result=outcome.get_nowait()
        except queue.Empty: self.timer=self.window.after(60,self.poll); return
        self.job=None; self.controls()
        if event.is_set() or not self.hub.permissions.allowed(DROP_ADD): return
        if isinstance(result,str): self.status.set(result); return
        if result is None: self.status.set('Cancelado.'); return
        try: self.store.add(result)
        except ValueError as exc: self.status.set(str(exc)); return
        self.revision+=1; self.status.set('Referências adicionadas. Arquivos originais preservados.'); self.refresh()
    def cancel(self):
        if self.job: self.job[0].set(); self.status.set('Cancelamento solicitado; resultado descartado.')
    def remove(self): self.revision+=1; self.store.remove(self.selected()); self.refresh()
    def clear(self): self.revision+=1; self.cancel(); self.store.clear(); self.refresh(); self.status.set('Prateleira limpa. Nenhum arquivo excluído.')
    def copy(self):
        paths=self.selected(); reviewed=self.revision; records=self.store.list()
        if not paths or not all(self.hub.permissions.allowed(k) for k in (DROP_ADD,DROP_COPY)): return
        if not messagebox.askyesno('Copiar caminhos?', 'Copiar caminhos selecionados como texto? Podem revelar dados pessoais e permanecer no histórico do clipboard.',parent=self.window): return
        if not self.window.winfo_exists() or reviewed!=self.revision or records!=self.store.list() or paths!=self.selected() or not all(self.hub.permissions.allowed(k) for k in (DROP_ADD,DROP_COPY)): return
        try: self.hub.root.clipboard_clear(); self.hub.root.clipboard_append('\n'.join(paths))
        except tk.TclError: self.status.set('Não foi possível copiar.'); return
        self.status.set('Caminhos copiados como texto, não arquivos.')
    def destroyed(self,event):
        if event.widget is self.window:
            if self.job: self.job[0].set()
            if self.timer is not None: self.window.after_cancel(self.timer); self.timer=None
    def close(self): self.cancel(); self.window.destroy()
