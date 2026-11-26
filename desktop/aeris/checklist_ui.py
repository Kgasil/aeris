"""Checklist UI; user-entered tasks only, session scoped."""
import tkinter as tk
from tkinter import ttk, messagebox
from aeris.checklist import PRIORITIES


class ChecklistWindow:
    def __init__(self, hub):
        self.hub = hub
        self.store = hub.checklist_store
        self.window = tk.Toplevel(hub.root)
        self.window.title('Aeris Checklist'); self.window.geometry('680x530'); self.window.minsize(560, 490)
        self.window.bind('<Escape>', lambda _: self.window.destroy())
        f = ttk.Frame(self.window, padding=14); f.pack(fill='both', expand=True)
        ttk.Label(f, text='Aeris Checklist', font=('Segoe UI', 18)).pack(anchor='w')
        ttk.Label(f, text='Pequenos passos. Grandes resultados. Listas temporárias da sessão.').pack(anchor='w', pady=(0,8))
        bar=ttk.Frame(f); bar.pack(fill='x')
        self.current=tk.StringVar(self.window)
        self.selector=ttk.Combobox(bar, textvariable=self.current, state='readonly', width=20); self.selector.pack(side='left', fill='x', expand=True)
        self.selector.bind('<<ComboboxSelected>>', lambda _: self.switch())
        self.list_name=tk.StringVar(self.window)
        ttk.Entry(bar, textvariable=self.list_name, width=19).pack(side='left', padx=4)
        ttk.Button(bar,text='Criar',command=self.create).pack(side='left')
        ttk.Button(bar,text='Renomear',command=self.rename).pack(side='left', padx=2)
        ttk.Button(bar,text='Excluir lista',command=self.delete_list).pack(side='left')
        self.stats=tk.StringVar(self.window)
        ttk.Label(f,textvariable=self.stats).pack(anchor='w',pady=(8,0))
        self.progress=ttk.Progressbar(f,maximum=100); self.progress.pack(fill='x',pady=4)
        filters=ttk.Frame(f); filters.pack(fill='x')
        self.filter=tk.StringVar(self.window,'Todas')
        filter_box=ttk.Combobox(filters,textvariable=self.filter,values=('Todas','Pendentes','Concluídas'),state='readonly',width=15); filter_box.pack(side='left')
        self.priority_filter=tk.StringVar(self.window,'Todas')
        priority_box=ttk.Combobox(filters,textvariable=self.priority_filter,values=('Todas',)+PRIORITIES,state='readonly',width=12); priority_box.pack(side='left',padx=4)
        priority_box.bind('<<ComboboxSelected>>',lambda _: self.render())
        filter_box.bind('<<ComboboxSelected>>',lambda _: self.render())
        area=ttk.Frame(f); area.pack(fill='both',expand=True,pady=5)
        self.tree=ttk.Treeview(area,columns=('title','priority','done'),show='headings',selectmode='browse',height=7)
        for col,label,width in [('title','Tarefa',300),('priority','Prioridade',90),('done','Estado',100)]:
            self.tree.heading(col,text=label); self.tree.column(col,width=width,stretch=col=='title')
        scrollbar=ttk.Scrollbar(area,orient='vertical',command=self.tree.yview); self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left',fill='both',expand=True); scrollbar.pack(side='right',fill='y')
        self.tree.bind('<<TreeviewSelect>>',self.select_task)
        self.tree.bind('<Double-1>',self.toggle_row)
        self.tree.bind('<Return>',lambda _: (self.toggle(),'break')[1])
        entry=ttk.Frame(f); entry.pack(fill='x')
        self.title=tk.StringVar(self.window); self.priority=tk.StringVar(self.window,'Normal')
        ttk.Entry(entry,textvariable=self.title).pack(side='left',fill='x',expand=True)
        ttk.Combobox(entry,textvariable=self.priority,values=PRIORITIES,state='readonly',width=10).pack(side='left',padx=4)
        ttk.Button(entry,text='Adicionar',command=self.add).pack(side='left')
        actions=ttk.Frame(f); actions.pack(fill='x',pady=5)
        for label,cmd in [('Editar selecionada',self.edit),('Alternar conclusão',self.toggle),('Excluir tarefa',self.delete_task)]:
            ttk.Button(actions,text=label,command=cmd).pack(side='left',fill='x',expand=True,padx=2)
        self.status=tk.StringVar(self.window)
        ttk.Label(f,textvariable=self.status,wraplength=510).pack(anchor='w')
        self.refresh_lists()

    def changed(self):
        self.render()
        if self.hub.alive(self.hub.privacy_window): self.hub.privacy_window.refresh()

    def refresh_lists(self, name=None):
        names=self.store.names(); self.selector.configure(values=names)
        self.current.set(name if name in names else self.current.get() if self.current.get() in names else names[0] if names else '')
        self.switch()

    def switch(self):
        self.list_name.set(self.current.get()); self.title.set(''); self.priority.set('Normal'); self.render()

    def toggle_row(self,event):
        row=self.tree.identify_row(event.y)
        if row and self.tree.identify_region(event.x,event.y) in ('cell','tree'):
            self.tree.selection_set(row); self.toggle()
        return 'break'

    def render(self):
        selected=self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        name=self.current.get()
        done,total=self.store.progress(name) if name in self.store.names() else (0,0)
        self.stats.set(f'{done} de {total} concluídas')
        self.progress['value']=100*done/total if total else 0
        if name not in self.store.names(): return
        for task in self.store.tasks(name):
            if self.filter.get()=='Pendentes' and task.done or self.filter.get()=='Concluídas' and not task.done: continue
            if self.priority_filter.get()!='Todas' and task.priority!=self.priority_filter.get(): continue
            self.tree.insert('', 'end', iid=str(task.id), values=(task.title,task.priority,'Concluída' if task.done else 'Pendente'))
        if selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected[0]); self.tree.focus(selected[0]); self.tree.see(selected[0])

    def selected(self):
        ids=self.tree.selection()
        if not ids: raise ValueError('Selecione uma tarefa.')
        return int(ids[0])

    def select_task(self, _=None):
        if not self.tree.selection(): return
        for task in self.store.tasks(self.current.get()):
            if task.id==self.selected(): self.title.set(task.title); self.priority.set(task.priority); break

    def perform(self, fn):
        try: fn()
        except (ValueError,KeyError) as e: self.status.set(str(e) if isinstance(e,ValueError) else 'Selecione ou crie uma lista.'); return False
        self.status.set('Alteração realizada na sessão.'); self.changed(); return True

    def create(self):
        self.perform(lambda: self.refresh_lists(self.store.create(self.list_name.get())))

    def rename(self):
        self.perform(lambda: self.refresh_lists(self.store.rename(self.current.get(),self.list_name.get())))

    def delete_list(self):
        if self.current.get() in self.store.names() and messagebox.askyesno('Excluir lista?', 'Descartar esta lista e suas tarefas?', parent=self.window):
            def action(): self.store.delete_list(self.current.get()); self.refresh_lists()
            self.perform(action)

    def add(self):
        if self.perform(lambda: self.store.add(self.current.get(),self.title.get(),self.priority.get())): self.title.set('')

    def edit(self):
        self.perform(lambda: self.store.edit(self.current.get(),self.selected(),self.title.get(),self.priority.get()))

    def toggle(self):
        self.perform(lambda: self.store.toggle(self.current.get(),self.selected()))

    def delete_task(self):
        if self.perform(lambda: self.store.delete(self.current.get(),self.selected())): self.title.set('')
