"""Desbloqueio explícito, editor isolado e bloqueio ao fechar."""
import tkinter as tk
from tkinter import ttk, messagebox

class VaultWindow:
    def __init__(self, hub, vault):
        self.hub, self.vault = hub, vault
        self.current=None; self.items=()
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris Vault · cofre local')
        self.window.geometry('560x540'); self.window.minsize(420,450)
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.window.bind('<Escape>',lambda _:self.close())
        self.window.bind('<Destroy>', self.destroyed, add='+')
        self.frame=ttk.Frame(self.window,padding=14); self.frame.pack(fill='both',expand=True)
        self.render_locked()

    def destroyed(self,event):
        if event.widget is self.window: self.vault.lock()

    def reset_frame(self):
        for child in self.frame.winfo_children(): child.destroy()
        self.current=None; self.items=()

    def render_locked(self):
        self.reset_frame()
        ttk.Label(self.frame,text='Vault · bloqueado',font=('Segoe UI',18)).pack(anchor='w',pady=8)
        ttk.Label(self.frame,text='Proteção DPAPI vinculada à conta Windows atual. Não é uma senha mestra. Use apenas dados fictícios nesta pré-alpha.',wraplength=365).pack(anchor='w',pady=8)
        ttk.Button(self.frame,text='Desbloquear nesta sessão',command=self.unlock).pack(fill='x',pady=8)
        ttk.Button(self.frame,text='Fechar',command=self.close).pack(fill='x')

    def unlock(self):
        try: self.vault.unlock()
        except (OSError,ValueError,TypeError,KeyError):
            messagebox.showerror('Vault','Não foi possível abrir o cofre. O arquivo existente não foi substituído. Verifique a conta Windows e se outra instância está aberta.',parent=self.window); return
        self.reset_frame()
        ttk.Label(self.frame,text='Vault · aberto',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(self.frame,text='Salve explicitamente. Não use senhas, dados bancários ou dados reais nesta versão.',wraplength=365).pack(anchor='w',pady=4)
        self.listbox=tk.Listbox(self.frame,height=5,exportselection=False); self.listbox.pack(fill='x')
        self.listbox.bind('<<ListboxSelect>>',self.select)
        self.count=tk.StringVar(self.window)
        ttk.Label(self.frame,textvariable=self.count).pack(anchor='w')
        self.title=tk.StringVar(self.window); ttk.Label(self.frame,text='Título').pack(anchor='w')
        ttk.Entry(self.frame,textvariable=self.title).pack(fill='x')
        ttk.Label(self.frame,text='Conteúdo').pack(anchor='w')
        self.body=tk.Text(self.frame,height=6,wrap='word',undo=False); self.body.pack(fill='both',expand=True)
        actions=ttk.Frame(self.frame); actions.pack(fill='x',pady=5)
        for label,cmd in [('Novo',self.new),('Salvar',self.save),('Excluir',self.delete),('Bloquear',self.lock)]:
            ttk.Button(actions,text=label,command=cmd).pack(side='left',padx=2)
        self.window.bind('<Control-s>',self.keyboard_save)
        self.refresh()
        from aeris.theme import apply_tree
        apply_tree(self.window,self.hub.settings.appearance.theme)

    def keyboard_save(self,_=None):
        if self.vault.unlocked: self.save()
        return 'break'

    def values(self): return self.title.get(),self.body.get('1.0','end-1c')
    def dirty(self):
        if not self.vault.unlocked: return False
        saved=next(((e.title,e.body) for e in self.items if e.id==self.current),('',''))
        return self.values()!=saved
    def allow_discard(self):
        return not self.dirty() or messagebox.askyesno('Descartar?', 'Descartar alterações não salvas?',parent=self.window)
    def fill(self,item=None):
        self.current=item.id if item else None; self.title.set(item.title if item else '')
        self.body.delete('1.0','end')
        if item: self.body.insert('1.0',item.body)
    def refresh(self):
        self.items=self.vault.list(); self.count.set(f'{len(self.items)} de 100 registros'); self.listbox.delete(0,'end')
        for i,item in enumerate(self.items):
            self.listbox.insert('end',item.title)
            if item.id==self.current: self.listbox.selection_set(i)
    def select(self,_=None):
        selection=self.listbox.curselection()
        if selection:
            item=self.items[selection[0]]
            if item.id==self.current: return
            before=(self.current,self.values())
            if not self.allow_discard(): self.refresh(); return
            if not self.vault.unlocked or not self.window.winfo_exists(): return
            if before!=(self.current,self.values()) or not any(x is item for x in self.vault.list()):
                self.refresh(); return
            self.fill(item)
    def new(self):
        if self.allow_discard(): self.fill(); self.refresh()
    def save(self):
        try: item=self.vault.save(*self.values(),entry_id=self.current)
        except (OSError,ValueError,KeyError):
            messagebox.showerror('Vault','Não foi possível salvar. Confira os campos, limites e acesso ao disco.',parent=self.window); return
        self.fill(item); self.refresh()
    def delete(self):
        if not self.vault.unlocked or self.current is None: return
        item=next((x for x in self.vault.list() if x.id==self.current),None)
        if item is None: self.refresh(); return
        draft=self.values()
        if not messagebox.askyesno('Excluir registro?', 'Excluir este registro do cofre? Não é apagamento seguro.',parent=self.window): return
        if not self.vault.unlocked or not self.window.winfo_exists(): return
        if self.current!=item.id or self.values()!=draft or not any(x is item for x in self.vault.list()):
            self.refresh(); return
        try: self.vault.delete(item.id)
        except (OSError,ValueError,KeyError):
            messagebox.showerror('Vault','Não foi possível excluir.',parent=self.window); return
        self.fill(); self.refresh()
    def lock(self):
        if not self.allow_discard(): return
        self.force_lock()
    def force_lock(self):
        self.window.unbind('<Control-s>')
        self.vault.lock()
        if hasattr(self,'count'): self.count.set('')
        if hasattr(self,'title'): self.title.set('')
        self.render_locked()
    def close(self):
        if self.allow_discard(): self.force_lock(); self.window.destroy()
