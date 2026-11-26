"""Desktop profile editor and explicit preview/copy. Browser filling is pending."""
import tkinter as tk
from tkinter import ttk,messagebox
from aeris.autofill import FIELDS
from aeris.permissions import COPY_AUTOFILL
from aeris.theme import apply_tree

class AutofillWindow:
    def __init__(self,hub,store):
        self.hub,self.store=hub,store
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris Autofill')
        self.window.geometry('570x690'); self.window.minsize(450,600)
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.window.bind('<Escape>',lambda _:self.close())
        self.window.bind('<Destroy>',lambda e:self.store.lock() if e.widget is self.window else None,add='+')
        self.frame=ttk.Frame(self.window,padding=12); self.frame.pack(fill='both',expand=True)
        self.current=None; self.visible=(); self.render_locked()
    def reset(self):
        for widget in self.frame.winfo_children(): widget.destroy()
        self.current=None; self.visible=()
    def render_locked(self):
        self.reset()
        ttk.Label(self.frame,text='Autofill · bloqueado',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(self.frame,text='Perfis protegidos pela conta Windows. Use exemplos fictícios. Não cadastre senhas, dados bancários ou documentos.',wraplength=380).pack(anchor='w',pady=8)
        ttk.Button(self.frame,text='Desbloquear',command=self.unlock).pack(fill='x')
    def unlock(self):
        try: self.store.unlock()
        except (OSError,ValueError,TypeError,KeyError):
            messagebox.showerror('Autofill','Não foi possível abrir os perfis. O arquivo existente foi preservado.',parent=self.window); return
        self.reset()
        ttk.Label(self.frame,text='Autofill · perfis locais',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(self.frame,text='Prévia e cópia manual. Preenchimento em sites ainda indisponível.',wraplength=400).pack(anchor='w')
        self.items=tk.Listbox(self.frame,height=4,exportselection=False); self.items.pack(fill='x',pady=5)
        self.items.bind('<<ListboxSelect>>',self.select)
        self.title=tk.StringVar(self.window); self.vars={k:tk.StringVar(self.window) for k in FIELDS}
        for label,var in [('Nome do perfil',self.title),*((FIELDS[k],v) for k,v in self.vars.items())]:
            row=ttk.Frame(self.frame); row.pack(fill='x',pady=2)
            ttk.Label(row,text=label,width=18).pack(side='left'); ttk.Entry(row,textvariable=var).pack(side='left',fill='x',expand=True)
        actions=ttk.Frame(self.frame); actions.pack(fill='x',pady=5)
        for label,cmd in [('Novo',self.new),('Salvar',self.save),('Excluir',self.delete),('Bloquear',self.lock)]:
            ttk.Button(actions,text=label,command=cmd).pack(side='left',padx=2)
        ttk.Label(self.frame,text='Escolha os campos para revisar').pack(anchor='w')
        self.requested={k:tk.BooleanVar(self.window,False) for k in FIELDS}
        row=ttk.Frame(self.frame); row.pack(fill='x')
        for i,(k,var) in enumerate(self.requested.items()):
            ttk.Checkbutton(row,text=FIELDS[k],variable=var,command=self.clear_preview).grid(row=i//2,column=i%2,sticky='w')
        ttk.Button(self.frame,text='Limpar seleção de campos',command=self.clear_fields).pack(fill='x')
        ttk.Button(self.frame,text='Revisar campos salvos',command=self.show_preview).pack(fill='x',pady=3)
        self.preview_items=tk.Listbox(self.frame,height=5,exportselection=False); self.preview_items.pack(fill='both',expand=True)
        self.preview_items.bind('<<ListboxSelect>>',lambda _:self.permissions_changed())
        self.copy_button=ttk.Button(self.frame,text='Copiar campo selecionado',command=self.copy); self.copy_button.pack(fill='x',pady=4)
        self.status=tk.StringVar(self.window); ttk.Label(self.frame,textvariable=self.status,wraplength=400).pack(anchor='w')
        self.preview_rows=()
        for v in (self.title,*self.vars.values()): v.trace_add('write',self.clear_preview)
        self.refresh(); self.permissions_changed(); apply_tree(self.window,self.hub.settings.appearance.theme)
    def clear_fields(self):
        for var in self.requested.values(): var.set(False)
        self.clear_preview()

    def values(self): return self.title.get(),{k:v.get() for k,v in self.vars.items() if v.get()}
    def dirty(self):
        if not self.store.unlocked: return False
        try: item=self.store.get(self.current) if self.current is not None else None
        except KeyError: return True
        return self.values()!=((item.title,item.fields) if item else ('',{}))
    def allow_discard(self): return not self.dirty() or messagebox.askyesno('Descartar?','Descartar alterações não salvas?',parent=self.window)
    def refresh(self):
        self.visible=self.store.list(); self.items.delete(0,'end')
        for i,item in enumerate(self.visible):
            self.items.insert('end',item.title)
            if item.id==self.current: self.items.selection_set(i)
    def fill(self,item=None):
        self.current=item.id if item else None; self.title.set(item.title if item else '')
        for k,v in self.vars.items(): v.set(item.fields.get(k,'') if item else '')
        self.clear_preview()
    def select(self,_=None):
        s=self.items.curselection()
        if s and self.visible[s[0]].id!=self.current:
            if self.allow_discard(): self.fill(self.visible[s[0]])
            else: self.refresh()
    def new(self):
        if self.allow_discard(): self.fill(); self.refresh()
    def save(self):
        try: item=self.store.save(*self.values(),item_id=self.current)
        except (OSError,ValueError,KeyError,TypeError): messagebox.showwarning('Autofill','Verifique os campos ou o acesso ao arquivo.',parent=self.window); return
        self.fill(item); self.refresh(); self.status.set('Perfil salvo no armazenamento protegido.')
    def delete(self):
        if self.current is None or not self.store.unlocked: return
        try: item=self.store.get(self.current)
        except KeyError: self.refresh(); return
        draft=self.values()
        if not messagebox.askyesno('Excluir?','Excluir o perfil salvo?',parent=self.window): return
        if not self.window.winfo_exists() or not self.store.unlocked: return
        try: same=self.store.get(item.id)==item
        except KeyError: same=False
        if not same or self.current!=item.id or self.values()!=draft:
            self.refresh(); self.clear_preview(); self.status.set('Perfil alterado. Revise novamente.'); return
        try: self.store.delete(item.id)
        except (OSError,ValueError,KeyError): messagebox.showerror('Autofill','Falha ao excluir.',parent=self.window); return
        self.fill(); self.refresh()
    def clear_preview(self,*_):
        self.preview_rows=(); self.preview_items.delete(0,'end'); self.permissions_changed()
    def show_preview(self):
        self.clear_preview()
        if self.current is None or self.dirty(): self.status.set('Salve o perfil antes de revisar.'); return
        self.preview_rows=self.store.preview(self.current,[k for k,v in self.requested.items() if v.get()])
        if not self.preview_rows:
            self.status.set('Selecione ao menos um campo preenchido.'); return
        for key,val in self.preview_rows: self.preview_items.insert('end',f'{FIELDS[key]}: {val}')
        self.status.set('Revise os valores. Selecione um campo para copiar manualmente.')
    def permissions_changed(self):
        if self.store.unlocked and hasattr(self,'copy_button'):
            allowed=bool(self.preview_items.curselection()) and self.hub.permissions.allowed(COPY_AUTOFILL)
            self.copy_button.configure(state='normal' if allowed else 'disabled')
    def copy(self):
        selection=self.preview_items.curselection()
        if not selection or self.current is None or self.dirty() or not self.hub.permissions.allowed(COPY_AUTOFILL): return
        if selection[0]>=len(self.preview_rows): return
        profile=self.store.get(self.current)
        reviewed=self.preview_rows
        fields=tuple(k for k,v in self.requested.items() if v.get())
        key,shown=reviewed[selection[0]]
        if key not in fields: self.clear_preview(); return
        if not messagebox.askyesno('Copiar campo?', 'O texto pode permanecer no histórico do Windows. Continuar?',parent=self.window): return
        if not self.window.winfo_exists() or not self.store.unlocked: return
        if self.current!=profile.id or self.preview_rows is not reviewed or self.preview_items.curselection()!=selection or tuple(k for k,v in self.requested.items() if v.get())!=fields or self.dirty():
            self.clear_preview(); self.status.set('Prévia alterada. Revise novamente.'); return
        try:
            if self.store.get(profile.id)!=profile: self.clear_preview(); return
            value=self.store.copy_value(profile.id,key)
            if value!=shown: return
            self.hub.root.clipboard_clear(); self.hub.root.clipboard_append(value)
        except (PermissionError,KeyError,ValueError,tk.TclError): self.status.set('Cópia não realizada.'); return
        self.status.set('Copiado. Cole manualmente no destino.')
    def force_lock(self):
        self.store.lock(); self.preview_rows=()
        if hasattr(self,'vars'):
            for v in (self.title,*self.vars.values()):
                # Drop traces before clearing; widgets will be destroyed below.
                for mode,cb in v.trace_info(): v.trace_remove(mode,cb)
                v.set('')
        self.render_locked(); apply_tree(self.window,self.hub.settings.appearance.theme)
    def lock(self):
        if self.allow_discard(): self.force_lock()
    def close(self):
        if self.allow_discard(): self.force_lock(); self.window.destroy()
