"""Explicit local export and one-item restore; no automated scheduling."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from aeris.backup import BackupService
from aeris.permissions import CREATE_BACKUP, RESTORE_BACKUP

class BackupWindow:
    def __init__(self, hub):
        self.hub = hub
        self.service = BackupService(hub.settings, hub.permissions)
        self.window = tk.Toplevel(hub.root); self.window.title('Aeris Backup')
        self.window.geometry('550x420'); self.window.minsize(460,390)
        self.window.bind('<Escape>', lambda _: self.window.destroy())
        frame=ttk.Frame(self.window,padding=16); frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='Backup e restauração',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(frame,text='Cópias locais do Vault, Bookmarks, sete módulos de Storage e aparência. Bloqueie os cofres antes. Dados DPAPI dependem da conta Windows original.',wraplength=400).pack(anchor='w',pady=8)
        self.create_button=ttk.Button(frame,text='Criar nova cópia',command=self.create); self.create_button.pack(fill='x',pady=4)
        self.inspect_button=ttk.Button(frame,text='Selecionar e verificar backup',command=self.inspect); self.inspect_button.pack(fill='x',pady=4)
        self.choice=tk.StringVar(self.window); self.items=ttk.Combobox(frame,textvariable=self.choice,state='readonly'); self.items.pack(fill='x',pady=4)
        self.restore_button=ttk.Button(frame,text='Restaurar item selecionado',command=self.restore); self.restore_button.pack(fill='x',pady=4)
        ttk.Button(frame,text='Gerenciar permissões',command=hub.open_permissions).pack(fill='x',pady=4)
        self.status=tk.StringVar(self.window,'Nenhum arquivo selecionado.')
        ttk.Label(frame,textvariable=self.status,wraplength=400).pack(anchor='w',pady=8)
        self.path=None; self.digest=None; self.permissions_changed()
    def permissions_changed(self):
        p=self.hub.permissions
        self.create_button.configure(state='normal' if p.allowed(CREATE_BACKUP) else 'disabled')
        allowed=p.allowed(RESTORE_BACKUP)
        self.inspect_button.configure(state='normal' if allowed else 'disabled')
        if not allowed:
            self.path=None; self.digest=None; self.choice.set(''); self.items.configure(values=()); self.status.set('Restauração não autorizada.')
        self.restore_button.configure(state='normal' if allowed and self.path else 'disabled')
    def blocked(self):
        return any(self.hub.alive(w) and w.dirty() for w in (self.hub.vault_window,self.hub.bookmarks_window))
    def create(self):
        if not self.hub.permissions.allowed(CREATE_BACKUP): return
        path=filedialog.asksaveasfilename(parent=self.window,defaultextension='.aerisbackup',filetypes=[('Aeris Backup','*.aerisbackup')])
        if not path: return
        if not messagebox.askyesno('Criar backup?', 'Exportar cópias atuais de Vault, Bookmarks, Checklist, Ideas, Learn, Meeting, Research, Flashcards, Reminder e aparência para o arquivo escolhido? Não será sobrescrito arquivo existente.',parent=self.window): return
        try: names=self.service.create(path); self.status.set('Criado: '+', '.join(names))
        except (OSError,ValueError,TypeError,KeyError) as e: messagebox.showerror('Backup','Falha ao criar. Bloqueie os cofres e escolha um arquivo novo. '+type(e).__name__,parent=self.window)
    def inspect(self):
        if not self.hub.permissions.allowed(RESTORE_BACKUP): return
        path=filedialog.askopenfilename(parent=self.window,filetypes=[('Aeris Backup','*.aerisbackup')])
        if not path: return
        self.path=None; self.digest=None; self.choice.set(''); self.items.configure(values=()); self.permissions_changed()
        try:
            names,self.digest=self.service.inspect_with_digest(path); self.path=path; self.items.configure(values=names); self.choice.set(names[0]); self.status.set('SHA-256 conferido. DPAPI será verificada na restauração.')
        except (OSError,ValueError,TypeError,KeyError) as e: messagebox.showerror('Backup','Arquivo inválido ou inacessível. '+type(e).__name__,parent=self.window)
        self.permissions_changed()
    def restore(self):
        if not self.path or not self.digest or not self.hub.permissions.allowed(RESTORE_BACKUP): return
        path,digest,name=self.path,self.digest,self.choice.get()
        if not messagebox.askyesno('Restaurar '+name+'?', 'Substituir somente este item? Arquivos protegidos anteriores serão preservados em cópia de recuperação local (Storage: substitui a versão anterior). Para Storage, restaure depois na sessão pelo Privacy. Aparência anterior será substituída.',parent=self.window): return
        if (path,digest,name)!=(self.path,self.digest,self.choice.get()):
            self.status.set('Seleção alterada. Inspecione novamente.'); return
        if self.blocked():
            messagebox.showwarning('Backup','Salve ou descarte rascunhos e bloqueie os cofres antes.',parent=self.window); return
        if name=='Aparência' and self.hub.alive(self.hub.appearance_window):
            messagebox.showwarning('Backup','Feche a janela de configurações antes.',parent=self.window); return
        try:
            recovery=self.service.restore(path,name,expected_digest=digest)
            if name=='Aparência': self.hub.apply_appearance()
            self.status.set('Restaurado: '+name+ (' · recuperação: '+recovery.name if recovery else ''))
        except (OSError,ValueError,TypeError,KeyError) as e: messagebox.showerror('Backup','Restauração bloqueada. Confira a conta Windows, o arquivo e os cofres bloqueados. '+type(e).__name__,parent=self.window)
