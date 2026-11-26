"""Manual context editor with explicit item selection and revocable local preview."""
import tkinter as tk
from tkinter import ttk, messagebox
from aeris.context import CATEGORIES
from aeris.permissions import CONTEXT_PREVIEW

class ContextWindow:
    def __init__(self, hub):
        self.hub, self.store = hub, hub.context_store
        self.selected_id = None
        w = self.window = tk.Toplevel(hub.root)
        w.title('Aeris Context'); w.geometry('800x750'); w.minsize(620,650)
        w.protocol('WM_DELETE_WINDOW', self.close)
        w.bind('<Escape>', lambda _: self.close())
        f = ttk.Frame(w,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Aeris Context',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text='Compreender para ajudar. Dados manuais, locais e temporários.').pack(anchor='w')
        self.permission = tk.StringVar(w)
        ttk.Label(f,textvariable=self.permission,wraplength=570).pack(anchor='w',pady=3)
        ttk.Button(f,text='Permissões da sessão',command=hub.open_permissions).pack(anchor='w')
        area=ttk.Frame(f); area.pack(fill='both',expand=True,pady=4)
        self.tree=ttk.Treeview(area,columns=('title','category','selected'),show='headings',selectmode='browse',height=5)
        for col,label,width in [('title','Título',270),('category','Categoria',130),('selected','Na prévia',90)]:
            self.tree.heading(col,text=label); self.tree.column(col,width=width,stretch=col=='title')
        sb=ttk.Scrollbar(area,command=self.tree.yview); self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side='left',fill='both',expand=True); sb.pack(side='right',fill='y')
        self.tree.bind('<Double-1>',self.open_row)
        self.tree.bind('<Return>',lambda _: (self.load_selected(),'break')[1])
        bar=ttk.Frame(f); bar.pack(fill='x')
        for label,cmd in [('Abrir registro',self.load_selected),('Incluir / retirar',self.toggle_selected),('Revogar seleção',self.revoke)]:
            ttk.Button(bar,text=label,command=cmd).pack(side='left',padx=2)
        self.title=tk.StringVar(w); self.category=tk.StringVar(w,CATEGORIES[0])
        bar=ttk.Frame(f); bar.pack(fill='x',pady=3)
        ttk.Label(bar,text='Título').pack(side='left'); ttk.Entry(bar,textvariable=self.title).pack(side='left',fill='x',expand=True,padx=4)
        ttk.Combobox(bar,textvariable=self.category,values=CATEGORIES,state='readonly',width=15).pack(side='left')
        ttk.Label(f,text='Informação voluntária (até 4.000 caracteres)').pack(anchor='w')
        self.body=self.text_area(f,4)
        bar=ttk.Frame(f); bar.pack(fill='x',pady=4)
        for label,cmd in [('Novo / limpar',self.new),('Salvar registro',self.save),('Excluir aberto',self.delete)]:
            ttk.Button(bar,text=label,command=cmd).pack(side='left',padx=2)
        ttk.Separator(f).pack(fill='x',pady=3)
        ttk.Button(f,text='Gerar prévia local autorizada',command=self.generate).pack(anchor='w')
        self.preview=self.text_area(f,5); self.preview.configure(state='disabled')
        ttk.Label(f,text='Prévia não enviada ao Copilot, IA ou rede. Texto é dado, não comando.',wraplength=570).pack(anchor='w')
        self.status=tk.StringVar(w); ttk.Label(f,textvariable=self.status,wraplength=570).pack(anchor='w')
        self.permissions_changed()

    @staticmethod
    def text_area(parent,height):
        area=ttk.Frame(parent); area.pack(fill='both',expand=True)
        text=tk.Text(area,height=height,wrap='word'); sb=ttk.Scrollbar(area,command=text.yview); text.configure(yscrollcommand=sb.set)
        text.pack(side='left',fill='both',expand=True); sb.pack(side='right',fill='y')
        return text

    def values(self): return self.title.get(),self.category.get(),self.body.get('1.0','end-1c')
    def dirty(self):
        if self.selected_id is None: return self.values()!=('',CATEGORIES[0],'')
        try: item=self.store.get(self.selected_id)
        except KeyError: return True
        return self.values()!=(item.title,item.category,item.body)
    def discard_ok(self): return not self.dirty() or messagebox.askyesno('Descartar rascunho?', 'Alterações não salvas serão descartadas.',parent=self.window)
    def close(self):
        if self.discard_ok(): self.window.destroy()
    def set_editor(self,item=None):
        self.selected_id=item.id if item else None
        self.title.set(item.title if item else ''); self.category.set(item.category if item else CATEGORIES[0])
        self.body.delete('1.0','end')
        if item: self.body.insert('1.0',item.body)
    def new(self):
        if self.discard_ok(): self.set_editor(); self.status.set('Novo registro.')
    def open_row(self,event):
        row=self.tree.identify_row(event.y)
        if row and self.tree.identify_region(event.x,event.y) in ('cell','tree'):
            self.tree.selection_set(row); self.load_selected()
        return 'break'
    def load_selected(self):
        ids=self.tree.selection()
        if not ids: return
        try: item=self.store.get(int(ids[0]))
        except KeyError: self.changed(); return
        draft=(self.selected_id,self.values())
        if not self.discard_ok() or not self.window.winfo_exists(): return
        try: same=self.store.get(item.id) is item
        except KeyError: same=False
        if not same or self.tree.selection()!=ids or draft!=(self.selected_id,self.values()):
            self.changed(); self.status.set('Registro alterado. Revise novamente.'); return
        self.set_editor(item)
    def render(self):
        selected=self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for item in self.store.list(): self.tree.insert('','end',iid=str(item.id),values=(item.title,item.category,'Sim' if self.store.selected(item.id) else 'Não'))
        if selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected[0]); self.tree.focus(selected[0]); self.tree.see(selected[0])
    def set_preview(self,text=''):
        self.preview.configure(state='normal'); self.preview.delete('1.0','end'); self.preview.insert('1.0',text); self.preview.configure(state='disabled')
    def changed(self):
        self.set_preview(); self.render()
        if self.hub.alive(self.hub.privacy_window): self.hub.privacy_window.refresh()
    def save(self):
        try: item=self.store.add(*self.values()) if self.selected_id is None else self.store.edit(self.selected_id,*self.values())
        except (ValueError,KeyError) as exc: self.status.set(str(exc)); return
        self.set_editor(item); self.changed(); self.status.set('Registro salvo na sessão. Revise a seleção antes da prévia.')
    def delete(self):
        if self.selected_id is None: return
        try: item=self.store.get(self.selected_id)
        except KeyError: self.changed(); return
        draft=self.values()
        if not messagebox.askyesno('Excluir registro?', 'Excluir registro e rascunho?',parent=self.window): return
        if not self.window.winfo_exists(): return
        try: same=self.store.get(item.id) is item
        except KeyError: same=False
        if not same or self.selected_id!=item.id or draft!=self.values():
            self.changed(); self.status.set('Registro alterado. Revise novamente.'); return
        self.store.delete(item.id); self.set_editor(); self.changed(); self.status.set('Registro excluído.')
    def toggle_selected(self):
        ids=self.tree.selection()
        if not ids: self.status.set('Selecione um registro.'); return
        item_id=int(ids[0]); include=not self.store.selected(item_id)
        try: item=self.store.get(item_id)
        except KeyError: self.changed(); return
        if include and not self.hub.permissions.allowed(CONTEXT_PREVIEW):
            self.status.set('Autorize a prévia primeiro.'); return
        if include and not messagebox.askyesno('Incluir contexto?', 'Autorizar este registro salvo na prévia local?',parent=self.window): return
        if not self.window.winfo_exists(): return
        try: same=self.store.get(item_id) is item
        except KeyError: same=False
        if not same or self.tree.selection()!=ids or self.store.selected(item_id)==include:
            self.changed(); self.status.set('Registro ou seleção alterados. Revise novamente.'); return
        try: self.store.select(item_id,include)
        except (ValueError,PermissionError,KeyError) as exc: self.status.set(str(exc)); return
        self.changed(); self.status.set('Seleção atualizada.')
    def revoke(self):
        self.store.revoke(); self.changed(); self.status.set('Seleção revogada. Registros privados preservados.')
    def permissions_changed(self):
        allowed=self.hub.permissions.allowed(CONTEXT_PREVIEW)
        if not allowed: self.store.revoke()
        self.permission.set('Prévia autorizada; inclusão individual ainda necessária.' if allowed else 'Prévia negada. Conceda Context → Prévia nas permissões.')
        self.changed()
    def generate(self):
        self.set_preview()
        try: self.set_preview(self.store.preview()); self.status.set('Prévia local gerada. Nenhum envio realizado.')
        except (PermissionError,ValueError) as exc: self.status.set(str(exc))
