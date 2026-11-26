"""Editor de abreviações e prévia. Nenhuma leitura da digitação externa."""
import tkinter as tk
from tkinter import ttk,messagebox
from aeris.permissions import COPY_EXPAND

class ExpandWindow:
    def __init__(self,hub,store):
        self.hub,self.store=hub,store
        self.output=None
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris Expand · sessão local')
        self.window.geometry('700x620'); self.window.minsize(520,500)
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.window.bind('<Escape>',lambda _:self.close())
        f=ttk.Frame(self.window,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Expand · abreviações',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text='Regras em memória. Use ;att, ;obg ou crie suas próprias abreviações. Apenas textos fictícios.',wraplength=470).pack(anchor='w')
        rules=ttk.Frame(f); rules.pack(fill='x',pady=5)
        self.items=tk.Listbox(rules,height=4,exportselection=False); self.items.pack(side='left',fill='both',expand=True)
        scroll=ttk.Scrollbar(rules,command=self.items.yview); scroll.pack(side='left',fill='y'); self.items.configure(yscrollcommand=scroll.set)
        buttons=ttk.Frame(rules); buttons.pack(side='left',padx=5)
        ttk.Button(buttons,text='Editar selecionada',command=self.edit).pack(fill='x')
        ttk.Button(buttons,text='Excluir selecionada',command=self.delete).pack(fill='x')
        self.code=tk.StringVar(self.window); ttk.Label(f,text='Abreviação (ex.: ;att)').pack(anchor='w'); ttk.Entry(f,textvariable=self.code).pack(fill='x')
        ttk.Label(f,text='Texto completo').pack(anchor='w'); self.replacement=tk.Text(f,height=2,wrap='word'); self.replacement.pack(fill='x')
        ttk.Button(f,text='Salvar ou atualizar regra',command=self.save).pack(anchor='w',pady=4)
        ttk.Label(f,text='Texto original (digite aqui)').pack(anchor='w'); self.input=tk.Text(f,height=4,wrap='word',undo=True); self.input.pack(fill='both',expand=True)
        self.input.bind('<<Modified>>',self.modified); self.input.edit_modified(False)
        ttk.Button(f,text='Expandir e revisar',command=self.apply).pack(fill='x',pady=4)
        ttk.Label(f,text='Prévia (original preservado)').pack(anchor='w'); self.result=tk.Text(f,height=4,wrap='word',state='disabled'); self.result.pack(fill='both',expand=True)
        row=ttk.Frame(f); row.pack(fill='x',pady=4)
        self.copy_button=ttk.Button(row,text='Copiar resultado',command=self.copy); self.copy_button.pack(side='left',fill='x',expand=True)
        ttk.Button(row,text='Limpar textos',command=self.clear_text).pack(side='left',padx=4)
        self.status=tk.StringVar(self.window,'Nenhum monitoramento de digitação externa.'); ttk.Label(f,textvariable=self.status,wraplength=470).pack(anchor='w')
        self.refresh(); self.invalidate()
    def refresh(self):
        self.rows=self.store.list(); self.items.delete(0,'end')
        for code,text in self.rows: self.items.insert('end',f'{code} · {text[:50].replace(chr(10)," ")}')
    def edit(self):
        selected=self.items.curselection()
        if selected:
            if (self.code.get() or self.replacement.get('1.0','end-1c')) and not messagebox.askyesno('Trocar edição?','Substituir os campos de edição atuais?',parent=self.window): return
            code,text=self.rows[selected[0]]; self.code.set(code); self.replacement.delete('1.0','end'); self.replacement.insert('1.0',text)
    def save(self):
        code,text=self.code.get(),self.replacement.get('1.0','end-1c')
        if code in dict(self.store.list()) and not messagebox.askyesno('Atualizar regra?','Substituir a expansão existente?',parent=self.window): return
        try: self.store.save(code,text)
        except ValueError as exc: self.status.set(str(exc)); return
        self.code.set(''); self.replacement.delete('1.0','end'); self.refresh(); self.invalidate(); self.status.set('Regra salva apenas nesta sessão.')
    def delete(self):
        selected=self.items.curselection()
        if not selected: return
        code,value=self.rows[selected[0]]
        if messagebox.askyesno('Excluir regra?','Remover esta abreviação da sessão?',parent=self.window):
            if not self.window.winfo_exists(): return
            if self.items.curselection()!=selected or dict(self.store.list()).get(code)!=value:
                self.refresh(); self.invalidate(); self.status.set('Regra alterada. Revise novamente.'); return
            self.store.delete(code); self.refresh(); self.invalidate()
    def original(self): return self.input.get('1.0','end-1c')
    def modified(self,_=None):
        if self.input.edit_modified(): self.input.edit_modified(False); self.invalidate()
    def set_result(self,value):
        self.output=value; self.result.configure(state='normal'); self.result.delete('1.0','end'); self.result.insert('1.0',value.text if value else ''); self.result.configure(state='disabled'); self.permissions_changed()
    def invalidate(self):
        self.set_result(None); self.source=None; self.reviewed_rules=None; self.status.set('Expanda e revise o texto antes de copiar.')
    def apply(self):
        try: result=self.store.expand(self.original())
        except ValueError as exc: self.invalidate(); self.status.set(str(exc)); return
        self.source=self.original(); self.reviewed_rules=self.store.list(); self.set_result(result); self.status.set(f'{result.count} ocorrência(s) expandida(s). Revise antes de copiar.')
    def permissions_changed(self):
        self.copy_button.configure(state='normal' if self.output is not None and self.hub.permissions.allowed(COPY_EXPAND) else 'disabled')
    def copy(self):
        if self.output is None or self.original()!=self.source or self.store.list()!=self.reviewed_rules or not self.hub.permissions.allowed(COPY_EXPAND): return
        reviewed=self.output
        if not messagebox.askyesno('Copiar resultado?','O clipboard será substituído e o histórico do sistema pode reter o texto.',parent=self.window): return
        if not self.window.winfo_exists() or not self.hub.permissions.allowed(COPY_EXPAND): return
        if self.output is not reviewed or self.original()!=self.source or self.store.list()!=self.reviewed_rules:
            self.invalidate(); self.status.set('Prévia ou regras alteradas. Expanda novamente.'); return
        try: self.hub.root.clipboard_clear(); self.hub.root.clipboard_append(self.output.text)
        except tk.TclError: self.status.set('Não foi possível copiar.'); return
        self.status.set('Copiado. Cole manualmente no destino.')
    def clear_text(self):
        self.input.delete('1.0','end'); self.input.edit_reset(); self.code.set(''); self.replacement.delete('1.0','end'); self.invalidate()
    def close(self):
        if (self.original() or self.code.get() or self.replacement.get('1.0','end-1c')) and not messagebox.askyesno('Fechar Expand?','Descartar textos e edição atual? Regras salvas ficam nesta sessão.',parent=self.window): return
        self.window.destroy()
