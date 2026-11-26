"""Learning plan editor; dialogs commit only after explicit user input."""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

class LearnWindow:
    def __init__(self,hub):
        self.hub=hub; self.store=hub.learn_store
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris Learn'); self.window.geometry('800x600'); self.window.minsize(640,460)
        self.window.bind('<Escape>',lambda _:self.window.destroy())
        f=ttk.Frame(self.window,padding=18); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Meu plano de estudos',font=('Segoe UI',21,'bold')).pack(anchor='w')
        ttk.Label(f,text='Crie uma trilha, organize tópicos e acompanhe seu progresso nesta sessão.').pack(anchor='w',pady=(0,8))
        ttk.Label(f,text='1. Escolha ou crie uma trilha',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(4,4))
        bar=ttk.Frame(f); bar.pack(fill='x')
        self.selector=ttk.Combobox(bar,state='readonly'); self.selector.pack(side='left',fill='x',expand=True)
        self.selector.bind('<<ComboboxSelected>>',lambda _:self.render())
        for label,cmd in [('Nova trilha',self.create),('Renomear',self.rename),('Excluir',self.delete_plan)]:
            ttk.Button(bar,text=label,command=cmd).pack(side='left',padx=2)
        ttk.Label(f,text='2. Acompanhe seu progresso',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(8,0))
        self.stats=tk.StringVar(self.window); ttk.Label(f,textvariable=self.stats).pack(anchor='w',pady=(10,0))
        self.progress=ttk.Progressbar(f,maximum=100); self.progress.pack(fill='x',pady=6)
        self.pending_only=tk.BooleanVar(self.window,False)
        ttk.Checkbutton(f,text='Somente tópicos pendentes',variable=self.pending_only,command=self.render).pack(anchor='w')
        area=ttk.Frame(f); area.pack(fill='both',expand=True)
        self.tree=ttk.Treeview(area,columns=('title','minutes','done'),show='headings',selectmode='browse')
        for c,label,w in [('title','Tópico',320),('minutes','Estimativa (min)',115),('done','Estado',100)]:
            self.tree.heading(c,text=label); self.tree.column(c,width=w,stretch=c=='title')
        scroll=ttk.Scrollbar(area,orient='vertical',command=self.tree.yview); self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side='left',fill='both',expand=True); scroll.pack(side='right',fill='y')
        actions=ttk.Frame(f); actions.pack(fill='x',pady=8)
        for label,cmd in [('Adicionar tópico',self.add),('Editar',self.edit),('Concluir / reabrir',self.toggle),('Subir',lambda:self.move(-1)),('Descer',lambda:self.move(1)),('Excluir tópico',self.delete_topic)]:
            ttk.Button(actions,text=label,command=cmd,style='Aeris.Primary.TButton' if label=='Adicionar tópico' else 'TButton').pack(side='left',fill='x',expand=True,padx=1)
        ttk.Button(f,text='Enviar para cartões de estudo',command=self.send_topic).pack(anchor='w',pady=3)
        self.status=tk.StringVar(self.window); ttk.Label(f,textvariable=self.status,wraplength=500).pack(anchor='w')
        self.plan_rows=()
        self.refresh()

    def plan_id(self):
        i=self.selector.current()
        if 0<=i<len(self.plan_rows):
            ident,title=self.plan_rows[i]
            try: plan=self.store.get(ident)
            except KeyError: plan=None
            if plan is not None and plan.title==title==self.selector.get(): return ident
        raise ValueError('Selecione ou crie uma trilha.')

    def selected(self):
        if not self.tree.selection(): raise ValueError('Selecione um tópico.')
        return int(self.tree.selection()[0])

    def refresh(self, plan_id=None):
        plans=self.store.list()
        if plan_id is None:
            try: plan_id=self.plan_id()
            except ValueError: pass
        self.plan_rows=tuple((p.id,p.title) for p in plans)
        self.selector.configure(values=[p.title for p in plans])
        if plans: self.selector.current(next((i for i,p in enumerate(plans) if p.id==plan_id),0))
        else: self.selector.set('')
        self.render()
        if self.hub.alive(self.hub.privacy_window): self.hub.privacy_window.refresh()

    def render(self,topic_id=None):
        selected=self.tree.selection()
        if topic_id is None and selected: topic_id=selected[0]
        self.tree.delete(*self.tree.get_children()); done=total=used=planned=0
        try: p=self.store.get(self.plan_id())
        except (ValueError,KeyError): p=None
        if p:
            done,total,used,planned=self.store.progress(p.id)
            for t in p.topics:
                if self.pending_only.get() and t.done: continue
                self.tree.insert('','end',iid=str(t.id),values=(t.title,t.minutes,'Concluído' if t.done else 'Pendente'))
        self.stats.set(f'{done}/{total} tópicos · {used}/{planned} min estimados concluídos')
        self.progress['value']=100*done/total if total else 0
        if topic_id is not None and self.tree.exists(str(topic_id)):
            self.tree.selection_set(str(topic_id)); self.tree.focus(str(topic_id)); self.tree.see(str(topic_id))

    def require_plan(self,p,topic_id=None):
        if not self.window.winfo_exists() or not self.hub.enabled('Learn'):
            raise ValueError('Trilha indisponível.')
        if self.plan_id()!=p.id or self.store.get(p.id) is not p or (topic_id is not None and self.selected()!=topic_id):
            raise ValueError('Trilha ou tópico alterado. Revise novamente.')

    def perform(self,fn):
        try: changed=fn()
        except (KeyError,ValueError,PermissionError,tk.TclError) as exc:
            if self.window.winfo_exists(): self.status.set(str(exc) if isinstance(exc,(ValueError,PermissionError)) else 'Registro não encontrado.')
            return
        if not self.window.winfo_exists(): return
        self.status.set('Nenhuma alteração.' if changed is False else 'Alteração realizada na sessão.')
        if self.hub.alive(self.hub.privacy_window): self.hub.privacy_window.refresh()

    def create(self):
        title=simpledialog.askstring('Nova trilha','Nome da trilha:',parent=self.window)
        if title is not None: self.perform(lambda:self.refresh(self.store.create(title).id))

    def rename(self):
        def action():
            p=self.store.get(self.plan_id()); title=simpledialog.askstring('Renomear','Nome da trilha:',initialvalue=p.title,parent=self.window)
            if title is None: return False
            self.require_plan(p); self.store.rename(p.id,title); self.refresh(p.id)
        self.perform(action)

    def delete_plan(self):
        def action():
            p=self.store.get(self.plan_id())
            if not messagebox.askyesno('Excluir trilha?','Descartar esta trilha e todos os tópicos?',parent=self.window): return False
            self.require_plan(p); self.store.delete_plan(p.id); self.refresh()
        self.perform(action)

    def topic_fields(self, title='',minutes=25):
        title=simpledialog.askstring('Tópico','Título:',initialvalue=title,parent=self.window)
        if title is None: return None
        mins=simpledialog.askinteger('Estimativa','Minutos planejados (não medidos):',initialvalue=minutes,minvalue=1,maxvalue=1440,parent=self.window)
        return None if mins is None else (title,mins)

    def add(self):
        def action():
            p=self.store.get(self.plan_id()); fields=self.topic_fields()
            if fields is None: return False
            self.require_plan(p); self.render(self.store.add(p.id,*fields).id)
        self.perform(action)

    def edit(self):
        def action():
            p=self.store.get(self.plan_id()); i=self.selected(); t=next((t for t in p.topics if t.id==i),None)
            if t is None: raise ValueError('Tópico não encontrado.')
            fields=self.topic_fields(t.title,t.minutes)
            if fields is None: return False
            self.require_plan(p,i); self.store.edit(p.id,i,*fields); self.render(i)
        self.perform(action)

    def toggle(self):
        def action():
            i=self.selected(); self.store.toggle(self.plan_id(),i); self.render(i)
        self.perform(action)

    def move(self,direction):
        def action():
            i=self.selected(); changed=self.store.move(self.plan_id(),i,direction); self.render(i); return changed
        self.perform(action)

    def delete_topic(self):
        def action():
            p=self.store.get(self.plan_id()); i=self.selected()
            if not messagebox.askyesno('Excluir tópico?','Descartar o tópico selecionado?',parent=self.window): return False
            self.require_plan(p,i); self.store.delete_topic(p.id,i); self.render()
        self.perform(action)

    def send_topic(self):
        from aeris.study_integration_ui import send_topic
        self.perform(lambda:send_topic(self))
