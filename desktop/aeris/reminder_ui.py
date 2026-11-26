"""Reminder editor and nonmodal generic local notification."""
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from math import ceil

STATES = {'pending':'Pendente','due':'Vencido','cancelled':'Cancelado'}

class ReminderWindow:
    def __init__(self, hub):
        self.hub = hub; self.store = hub.reminder_store
        self.window = tk.Toplevel(hub.root)
        self.window.title('Aeris Reminder'); self.window.geometry('760x540'); self.window.minsize(600,420)
        self.window.bind('<Escape>', lambda _: self.window.destroy())
        f = ttk.Frame(self.window,padding=18); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Meus lembretes',font=('Segoe UI',21,'bold')).pack(anchor='w')
        ttk.Label(f,text='Receba lembretes enquanto o Aeris estiver aberto. Os registros são temporários.').pack(anchor='w',pady=(0,8))
        ttk.Label(f,text='Lembretes da sessão',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(4,5))
        area=ttk.Frame(f); area.pack(fill='both',expand=True)
        self.tree=ttk.Treeview(area,columns=('title','due','state','alert'),show='headings',selectmode='browse')
        for col,label,width in [('title','Lembrete',240),('due','Vencimento local',155),('state','Estado',90),('alert','Alerta',65)]:
            self.tree.heading(col,text=label); self.tree.column(col,width=width,stretch=col=='title')
        scroll=ttk.Scrollbar(area,orient='vertical',command=self.tree.yview); self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side='left',fill='both',expand=True); scroll.pack(side='right',fill='y')
        self.tree.bind('<<TreeviewSelect>>',self.select)
        self.title=tk.StringVar(self.window); self.minutes=tk.StringVar(self.window,'25'); self.alert=tk.BooleanVar(self.window,False)
        ttk.Label(f,text='O que você quer lembrar? (até 200 caracteres)',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(6,0))
        ttk.Entry(f,textvariable=self.title).pack(fill='x')
        opts=ttk.Frame(f); opts.pack(fill='x',pady=5)
        ttk.Label(opts,text='Daqui a (minutos):').pack(side='left')
        ttk.Entry(opts,textvariable=self.minutes,width=8).pack(side='left',padx=5)
        ttk.Checkbutton(opts,text='Exibir alerta visual sem o conteúdo',variable=self.alert).pack(side='left')
        actions=ttk.Frame(f); actions.pack(fill='x')
        for label,cmd in [('Criar lembrete',self.add),('Reprogramar selecionado',self.edit),('Cancelar',self.cancel),('Excluir',self.delete)]:
            ttk.Button(actions,text=label,command=cmd,style='Aeris.Primary.TButton' if label=='Criar lembrete' else 'TButton').pack(side='left',fill='x',expand=True,padx=2)
        self.status=tk.StringVar(self.window)
        ttk.Label(f,textvariable=self.status,wraplength=560).pack(anchor='w',pady=5)
        self.render()

    def render(self):
        selected=self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for r in self.store.list():
            self.tree.insert('','end',iid=str(r.id),values=(r.title,datetime.fromtimestamp(r.due).strftime('%d/%m/%Y %H:%M:%S'),STATES[r.state],'Sim' if r.alert else 'Não'))
        if selected and self.tree.exists(selected[0]): self.tree.selection_set(selected[0])

    def selected(self):
        ids=self.tree.selection()
        if not ids: raise ValueError('Selecione um lembrete.')
        return int(ids[0])

    def select(self,_=None):
        if not self.tree.selection(): return
        for r in self.store.list():
            if r.id==self.selected():
                self.title.set(r.title); self.minutes.set(str(max(1,ceil((r.due-self.store.clock())/60)))); self.alert.set(r.alert); break

    def values(self):
        try: minutes=int(self.minutes.get())
        except ValueError: raise ValueError('Informe minutos inteiros.') from None
        return self.title.get(),minutes,self.alert.get()

    def perform(self, fn):
        try: fn()
        except (ValueError,KeyError) as e:
            self.status.set(str(e) if isinstance(e,ValueError) else 'Seleção não encontrada.'); return
        self.status.set('Alteração realizada na sessão.')
        self.render(); self.hub.schedule_reminders()
        if self.hub.alive(self.hub.privacy_window): self.hub.privacy_window.refresh()

    def add(self): self.perform(lambda:self.store.add(*self.values()))
    def edit(self): self.perform(lambda:self.store.edit(self.selected(),*self.values()))
    def cancel(self): self.perform(lambda:self.store.cancel(self.selected()))
    def delete(self): self.perform(lambda:self.store.delete(self.selected()))

class ReminderAlert:
    def __init__(self, hub, count):
        self.hub=hub; self.count=count
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris Reminder'); self.window.resizable(False,False)
        f=ttk.Frame(self.window,padding=18); f.pack(fill='both',expand=True)
        self.message=tk.StringVar(self.window); ttk.Label(f,textvariable=self.message).pack(pady=(0,10))
        self.update_count(0)
        ttk.Button(f,text='Ver lembretes',command=self.open).pack(fill='x')
        ttk.Button(f,text='Dispensar',command=self.window.destroy).pack(fill='x',pady=(5,0))
        self.window.bind('<Escape>',lambda _:self.window.destroy())

    def update_count(self,count):
        self.count+=count; self.message.set(f'{self.count} lembrete(s) chegaram ao vencimento.')

    def open(self):
        self.window.destroy(); self.hub.open_tool('Reminder')
