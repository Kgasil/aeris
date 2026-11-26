"""Editor comum para Capture e Snippets, sem persistência de conteúdo."""
import tkinter as tk
from aeris.window_lifecycle import trace_window
from tkinter import ttk,messagebox

class Editor:
    def __init__(self,parent,store,snippets=False,permissions=None):
        self.parent,self.store,self.snippets=parent,store,snippets
        self.permissions=permissions
        self.name='Snippets' if snippets else 'Capture'
        self.current=None
        self.window=tk.Toplevel(parent)
        self.window.title(f'Aeris {self.name} · sessão local')
        self.window.geometry('650x550')
        self.window.minsize(460,470)
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.window.bind('<Escape>',lambda _:self.close())
        frame=ttk.Frame(self.window,padding=18); frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='Textos rápidos' if snippets else 'Minhas anotações',font=('Segoe UI',21,'bold')).pack(anchor='w')
        ttk.Label(frame,text='Organize suas ideias e textos nesta sessão. Use dados fictícios, sem informações sensíveis.',wraplength=410).pack(anchor='w')
        self.query=tk.StringVar(self.window)
        ttk.Label(frame,text='Encontrar um registro salvo',font=('Segoe UI',10,'bold')).pack(anchor='w',pady=(8,0))
        entry=ttk.Entry(frame,textvariable=self.query); entry.pack(fill='x')
        self.window.bind('<Control-f>',lambda _:entry.focus_set())
        row=ttk.Frame(frame); row.pack(fill='x',pady=5)
        scroll=ttk.Scrollbar(row); scroll.pack(side='right',fill='y')
        self.items=tk.Listbox(row,height=4,exportselection=False,yscrollcommand=scroll.set); self.items.pack(fill='x',expand=True)
        scroll.configure(command=self.items.yview)
        self.items.bind('<<ListboxSelect>>',self.select)
        self.title=tk.StringVar(self.window); self.category=tk.StringVar(self.window,'Geral')
        for label,var in [('Título',self.title)]+([('Categoria',self.category)] if snippets else []):
            ttk.Label(frame,text=label).pack(anchor='w'); ttk.Entry(frame,textvariable=var).pack(fill='x',pady=(0,4))
        ttk.Label(frame,text='Escreva ou edite o conteúdo',font=('Segoe UI',11,'bold')).pack(anchor='w')
        row=ttk.Frame(frame); row.pack(fill='both',expand=True)
        scroll=ttk.Scrollbar(row); scroll.pack(side='right',fill='y')
        self.body=tk.Text(row,height=5,wrap='word',undo=True,padx=12,pady=10,relief='flat',highlightthickness=1,yscrollcommand=scroll.set,exportselection=False); self.body.pack(fill='both',expand=True)
        scroll.configure(command=self.body.yview)
        buttons=ttk.Frame(frame); buttons.pack(fill='x',pady=6)
        for text,cmd in [('Novo',self.new),('Salvar',self.save),('Excluir',self.delete)]+([('Copiar salvo',self.copy)] if snippets else []):
            ttk.Button(buttons,text=text,command=cmd,style='Aeris.Primary.TButton' if text=='Salvar' else 'TButton').pack(side='left',padx=(0,4))
        self.window.bind('<Control-s>',self.keyboard_save)
        self.status=tk.StringVar(self.window,'Textos não são gravados em disco.')
        ttk.Label(frame,textvariable=self.status,wraplength=420).pack(anchor='w')
        trace_window(self.window, self.query, self.refresh); self.refresh()
    def keyboard_save(self,_=None):
        self.save()
        return 'break'

    def values(self):
        body=self.body.get('1.0','end-1c')
        return (self.title.get(),self.category.get(),body) if self.snippets else (self.title.get(),body)
    def dirty(self):
        if self.current is None: baseline=('', 'Geral','') if self.snippets else ('','')
        else:
            try: i=self.store.get(self.current)
            except KeyError: return True
            baseline=(i.title,i.category,i.body) if self.snippets else (i.title,i.body)
        return self.values()!=baseline
    def allow_discard(self):
        return not self.dirty() or messagebox.askyesno('Descartar edição?','Alterações não salvas serão descartadas.',parent=self.window)
    def refresh(self,*_):
        self.visible=self.store.list(self.query.get()); self.items.delete(0,'end')
        for n,i in enumerate(self.visible):
            self.items.insert('end',i.title+(f' · {i.category}' if self.snippets else ''))
            if i.id==self.current: self.items.selection_set(n)
    def fill(self,item=None):
        self.current=item.id if item else None
        self.title.set(item.title if item else '')
        self.category.set(getattr(item,'category','Geral'))
        self.body.delete('1.0','end')
        if item: self.body.insert('1.0',item.body)
        self.body.edit_reset()
    def select(self,_=None):
        selected=self.items.curselection()
        if selected:
            i=self.visible[selected[0]]
            if i.id!=self.current:
                before=(self.current,self.values())
                if not self.allow_discard(): self.refresh(); return
                if not self.window.winfo_exists(): return
                try: current_item=self.store.get(i.id)
                except KeyError: self.refresh(); self.status.set('Registro removido.'); return
                if current_item is not i or before!=(self.current,self.values()):
                    self.refresh(); self.status.set('Seleção alterada. Revise novamente.'); return
                self.fill(i)
    def new(self):
        if self.allow_discard(): self.fill(); self.refresh()
    def save(self):
        try: item=self.store.save(*self.values(),self.current)
        except (ValueError,KeyError) as exc: messagebox.showwarning(self.name,str(exc),parent=self.window); return
        self.fill(item); self.refresh(); self.status.set('Salvo na sessão.')
    def delete(self):
        if self.current is None: return
        try: item=self.store.get(self.current)
        except KeyError: self.refresh(); self.status.set('Registro removido.'); return
        draft=self.values()
        if not messagebox.askyesno('Excluir?','Remover o texto e as edições atuais? Cópias anteriores no clipboard podem permanecer.',parent=self.window): return
        if not self.window.winfo_exists(): return
        try: same=self.store.get(item.id) is item
        except KeyError: same=False
        if not same or self.current!=item.id or self.values()!=draft:
            self.refresh(); self.status.set('Seleção alterada. Revise novamente.'); return
        self.store.delete(item.id); self.fill(); self.refresh(); self.status.set('Texto removido.')
    def copy(self):
        if not self.snippets: return
        from aeris.permissions import COPY_SNIPPETS
        if self.permissions is None or not self.permissions.allowed(COPY_SNIPPETS):
            self.status.set("Autorize a cópia em Permissões no Hub."); return
        if self.current is None or self.dirty(): self.status.set('Selecione e salve o texto antes de copiar.'); return
        reviewed=self.store.get(self.current)
        if not messagebox.askyesno('Copiar texto?','Substitui o clipboard; o histórico do sistema pode reter a cópia. Continuar?',parent=self.window): return
        if not self.window.winfo_exists() or not self.permissions.allowed(COPY_SNIPPETS): return
        try: same=self.store.get(reviewed.id) is reviewed
        except KeyError: same=False
        if not same or self.current!=reviewed.id or self.dirty():
            self.refresh(); self.status.set('Texto alterado. Revise novamente.'); return
        try:
            self.parent.clipboard_clear(); self.parent.clipboard_append(reviewed.body)
        except tk.TclError: messagebox.showerror(self.name,'Não foi possível copiar.',parent=self.window); return
        self.status.set('Copiado. Cole manualmente no destino.')
    def close(self):
        if self.allow_discard(): self.window.destroy()
