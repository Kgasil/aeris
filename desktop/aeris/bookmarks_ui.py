"""Bookmark manager. Links remain locked until explicitly opened locally."""
import tkinter as tk
from aeris.window_lifecycle import trace_window
from tkinter import ttk,messagebox
from aeris.permissions import OPEN_BOOKMARK
from aeris.theme import apply_tree

class BookmarksWindow:
    def __init__(self,hub,store):
        self.hub,self.store=hub,store
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris Bookmarks')
        self.window.geometry('560x570'); self.window.minsize(430,490)
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.window.bind('<Escape>',lambda _:self.close())
        self.window.bind('<Destroy>',lambda e: self.store.lock() if e.widget is self.window else None,add='+')
        self.frame=ttk.Frame(self.window,padding=14); self.frame.pack(fill='both',expand=True)
        self.current=None; self.visible=(); self.render_locked()

    def reset(self):
        for w in self.frame.winfo_children(): w.destroy()
        self.current=None; self.visible=()

    def render_locked(self):
        self.reset()
        ttk.Label(self.frame,text='Bookmarks · bloqueado',font=('Segoe UI',18)).pack(anchor='w',pady=6)
        ttk.Label(self.frame,text='Links protegidos pela conta Windows (DPAPI). Use somente exemplos nesta pré-alpha.',wraplength=360).pack(anchor='w',pady=6)
        ttk.Button(self.frame,text='Desbloquear',command=self.unlock).pack(fill='x',pady=6)
        ttk.Button(self.frame,text='Fechar',command=self.close).pack(fill='x')

    def unlock(self):
        try: self.store.unlock()
        except (OSError,ValueError,TypeError,KeyError):
            messagebox.showerror('Bookmarks','Não foi possível abrir os registros. O arquivo existente foi preservado.',parent=self.window); return
        self.reset()
        ttk.Label(self.frame,text='Bookmarks',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(self.frame,text='Links locais; nenhum site é consultado pelo Aeris.',wraplength=370).pack(anchor='w',pady=4)
        self.query=tk.StringVar(self.window)
        ttk.Label(self.frame,text='Pesquisar título, categoria ou endereço').pack(anchor='w')
        ttk.Entry(self.frame,textvariable=self.query).pack(fill='x')
        listing=ttk.Frame(self.frame); listing.pack(fill='both',expand=True,pady=5)
        scroll=ttk.Scrollbar(listing); scroll.pack(side='right',fill='y')
        self.items=tk.Listbox(listing,height=5,exportselection=False,yscrollcommand=scroll.set); self.items.pack(fill='both',expand=True); scroll.configure(command=self.items.yview)
        self.items.bind('<<ListboxSelect>>',self.select)
        self.title=tk.StringVar(self.window); self.category=tk.StringVar(self.window,'Geral'); self.url=tk.StringVar(self.window)
        for label,var in [('Título',self.title),('Categoria',self.category),('Endereço HTTP/HTTPS',self.url)]:
            ttk.Label(self.frame,text=label).pack(anchor='w'); ttk.Entry(self.frame,textvariable=var).pack(fill='x',pady=(0,4))
        actions=ttk.Frame(self.frame); actions.pack(fill='x',pady=5)
        for label,cmd in [('Novo',self.new),('Salvar',self.save),('Excluir',self.delete),('Bloquear',self.lock)]:
            ttk.Button(actions,text=label,command=cmd).pack(side='left',padx=2)
        self.open_button=ttk.Button(self.frame,text='Abrir link salvo no navegador',command=self.open_selected); self.open_button.pack(fill='x',pady=3)
        self.status=tk.StringVar(self.window); ttk.Label(self.frame,textvariable=self.status,wraplength=370).pack(anchor='w')
        trace_window(self.window, self.query, self.refresh); self.refresh(); self.permissions_changed(); apply_tree(self.window,self.hub.settings.appearance.theme)

    def values(self): return self.title.get(),self.category.get(),self.url.get()
    def dirty(self):
        if not self.store.unlocked: return False
        if self.current is None: return self.values()!=('','Geral','')
        try: item=self.store.get(self.current)
        except KeyError: return True
        return self.values()!=(item.title,item.category,item.url)
    def allow_discard(self): return not self.dirty() or messagebox.askyesno('Descartar?','Descartar alterações não salvas?',parent=self.window)
    def fill(self,item=None):
        self.current=item.id if item else None
        self.title.set(item.title if item else ''); self.category.set(item.category if item else 'Geral'); self.url.set(item.url if item else '')
        self.permissions_changed()
    def refresh(self,*_):
        if not self.store.unlocked: return
        self.visible=self.store.list(self.query.get()); self.items.delete(0,'end')
        for i,item in enumerate(self.visible):
            self.items.insert('end',f'{item.title} · {item.category}')
            if item.id==self.current: self.items.selection_set(i)
    def select(self,_=None):
        s=self.items.curselection()
        if s and self.visible[s[0]].id!=self.current:
            if self.allow_discard(): self.fill(self.visible[s[0]])
            else: self.refresh()
    def new(self):
        if self.allow_discard(): self.fill(); self.refresh()
    def save(self):
        try: item=self.store.save(*self.values(),item_id=self.current)
        except (ValueError,OSError,KeyError,TypeError):
            messagebox.showwarning('Bookmarks','Verifique título, categoria, URL válida, duplicatas e acesso ao arquivo. Nenhuma alteração foi confirmada.',parent=self.window); return
        self.fill(item); self.refresh(); self.status.set('Registro salvo localmente.')
    def delete(self):
        if self.current is None or not self.store.unlocked: return
        try: item=self.store.get(self.current)
        except KeyError: self.refresh(); return
        draft=self.values()
        if not messagebox.askyesno('Excluir?','Excluir link salvo?',parent=self.window): return
        if not self.window.winfo_exists() or not self.store.unlocked: return
        try: same=self.store.get(item.id)==item
        except KeyError: same=False
        if not same or self.current!=item.id or self.values()!=draft:
            self.refresh(); self.status.set('Seleção alterada. Revise novamente.'); return
        try: self.store.delete(item.id)
        except (OSError,ValueError,KeyError): messagebox.showerror('Bookmarks','Não foi possível excluir.',parent=self.window); return
        self.fill(); self.refresh(); self.status.set('Registro removido.')
    def permissions_changed(self):
        if self.store.unlocked and hasattr(self,'open_button'):
            allowed=self.hub.permissions.allowed(OPEN_BOOKMARK)
            self.open_button.configure(state='normal' if allowed and self.current is not None else 'disabled')
            self.status.set('Abertura autorizada nesta sessão.' if allowed else 'Autorize Bookmarks → Navegador em Permissões para abrir links.')
    def open_selected(self):
        if self.current is None or not self.hub.permissions.allowed(OPEN_BOOKMARK): return
        if self.dirty(): self.status.set('Salve as alterações antes de abrir.'); return
        item=self.store.get(self.current)
        if not messagebox.askyesno('Abrir endereço externo?',f'{item.url}\n\nO navegador poderá acessar a internet. O Aeris não verificou a segurança deste site. Continuar?',parent=self.window): return
        if not self.window.winfo_exists() or not self.store.unlocked or not self.hub.permissions.allowed(OPEN_BOOKMARK): return
        try: same=self.store.get(item.id)==item
        except KeyError: same=False
        if not same or self.current!=item.id or self.dirty():
            self.refresh(); self.status.set('Endereço alterado. Revise novamente.'); return
        try: self.store.open(item.id)
        except (OSError,ValueError,KeyError): messagebox.showerror('Bookmarks','Não foi possível abrir o navegador.',parent=self.window); return
        self.status.set('Endereço encaminhado ao navegador.')
    def lock(self):
        if self.allow_discard(): self.force_lock()
    def force_lock(self):
        if self.store.unlocked:
            for var in (self.title,self.category,self.url,self.query,self.status): var.set('')
        self.store.lock(); self.render_locked()
    def close(self):
        if self.allow_discard(): self.force_lock(); self.window.destroy()
