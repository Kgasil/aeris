"""Always-accessible privacy center; no monitoring or telemetry."""
import tkinter as tk
from tkinter import ttk, messagebox
from aeris.privacy import inventory, mask_text
from aeris.theme import apply_tree

class PrivacyWindow:
    def __init__(self, hub):
        self.hub=hub
        self.window=tk.Toplevel(hub.root)
        self.window.title('Aeris Privacy')
        self.window.geometry('720x600'); self.window.minsize(560,460)
        self.window.bind('<Escape>',lambda _:self.window.destroy())
        frame=ttk.Frame(self.window,padding=14); frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='Aeris Privacy',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(frame,text='Controle local. Não é uma auditoria do sistema nem apagamento seguro.',wraplength=520).pack(anchor='w',pady=4)
        tabs=ttk.Notebook(frame); tabs.pack(fill='both',expand=True,pady=6)
        overview=ttk.Frame(tabs,padding=8); tabs.add(overview,text='Inventário')
        self.report=tk.Text(overview,wrap='word',height=12,state='disabled')
        bar=ttk.Scrollbar(overview,command=self.report.yview); self.report.configure(yscrollcommand=bar.set)
        bar.pack(side='right',fill='y'); self.report.pack(fill='both',expand=True)
        permissions=ttk.Frame(tabs,padding=8); tabs.add(permissions,text='Permissões')
        self.granted_only=tk.BooleanVar(self.window,False)
        ttk.Checkbutton(permissions,text='Somente acessos autorizados',variable=self.granted_only,command=self.refresh).pack(anchor='w')
        self.grants=tk.Listbox(permissions,exportselection=False)
        bar=ttk.Scrollbar(permissions,command=self.grants.yview); self.grants.configure(yscrollcommand=bar.set)
        bar.pack(side='right',fill='y'); self.grants.pack(fill='both',expand=True)
        masking=ttk.Frame(tabs,padding=8); tabs.add(masking,text='Mascarar texto')
        ttk.Label(masking,text='Prévia local: e-mail, CPF, CNPJ e telefone brasileiro formatados. Não detecta todos os dados sensíveis; revise o resultado.',wraplength=480).pack(anchor='w')
        self.original=tk.Text(masking,height=4,wrap='word'); self.original.pack(fill='both',expand=True,pady=4)
        self.original.bind('<<Modified>>',self.invalidate)
        ttk.Button(masking,text='Gerar prévia mascarada',command=self.mask).pack(fill='x')
        self.preview=tk.Text(masking,height=4,wrap='word',state='disabled'); self.preview.pack(fill='both',expand=True,pady=4)
        self.mask_status=tk.StringVar(self.window,'Nenhum texto processado.')
        ttk.Label(masking,textvariable=self.mask_status,wraplength=480).pack(anchor='w')
        ttk.Button(masking,text='Limpar texto e prévia',command=self.reset_mask).pack(fill='x')
        from aeris.storage_ui import StoragePanel
        storage=ttk.Frame(tabs,padding=8); tabs.add(storage,text='Cópias protegidas')
        self.storage_panel=StoragePanel(storage,hub,self.refresh)
        from aeris.autosave_ui import AutoSavePanel
        auto=ttk.Frame(tabs,padding=8); tabs.add(auto,text="Automático")
        self.auto_panel=AutoSavePanel(auto,hub,self.refresh)
        actions=ttk.Frame(frame); actions.pack(fill='x')
        for i,(label,cmd) in enumerate([('Atualizar inventário',self.refresh),('Gerenciar permissões',hub.open_permissions),('Revogar todas',self.revoke),('Bloquear cofres',self.lock),('Limpar sessão',self.clear),('Ocultar Spotlight',self.hide)]):
            ttk.Button(actions,text=label,command=cmd).grid(row=i//2,column=i%2,sticky='ew',padx=2,pady=2)
        actions.columnconfigure(0,weight=1); actions.columnconfigure(1,weight=1)
        self.status=tk.StringVar(self.window,''); ttk.Label(frame,textvariable=self.status,wraplength=520).pack(anchor='w')
        self.refresh()
    def refresh(self):
        self.storage_panel.refresh()
        self.auto_panel.refresh()
        grants,files,stores,locks=inventory(self.hub)
        lines=[f'Permissões autorizadas: {sum(v for _,v in grants)}/{len(grants)}','\nArquivos locais conhecidos (somente presença):']
        lines.extend(f'  {name}: {state}' for name,state in files)
        lines.append('\nItens em memória (não inclui rascunhos abertos):')
        lines.extend(f'  {name.capitalize()}: {count}' for name,count in stores)
        lines.append('\nCofres:'); lines.extend(f'  {name}: {state}' for name,state in locks)
        lines.append('\nInventário parcial. Backups externos, cópias de recuperação, cache de modelos, memória residual e clipboard do Windows não são examinados.')
        self.report.configure(state='normal'); self.report.delete('1.0','end'); self.report.insert('1.0','\n'.join(lines)); self.report.configure(state='disabled')
        self.grants.delete(0,'end')
        for name,allowed in grants:
            if not self.granted_only.get() or allowed: self.grants.insert('end',('Autorizado: ' if allowed else 'Negado: ')+name)
    def revoke(self):
        self.hub.permissions.revoke_all(); self.refresh(); self.status.set('Permissões revogadas. Dados já copiados não são apagados.')
    def lock(self):
        if not messagebox.askyesno('Bloquear cofres?', 'Descartar rascunhos não salvos de Vault, Bookmarks e Autofill? Registros salvos serão preservados.',parent=self.window): return
        if not self.window.winfo_exists(): return
        self.hub.lock_protected(); self.refresh(); self.status.set('Cofres bloqueados.')
    def clear(self):
        if self.hub.clear_session(): self.status.set('Sessão limpa. Clipboard e registros protegidos preservados.')
    def hide(self):
        self.hub.hide_spotlight(); self.status.set('Spotlight oculto nesta sessão.')
    def set_preview(self,text):
        self.preview.configure(state='normal'); self.preview.delete('1.0','end'); self.preview.insert('1.0',text); self.preview.configure(state='disabled')
    def invalidate(self,_=None):
        if self.original.edit_modified():
            self.original.edit_modified(False); self.set_preview(''); self.mask_status.set('Texto alterado. Gere uma nova prévia.')
    def mask(self):
        self.original.edit_modified(False)
        try: result=mask_text(self.original.get('1.0','end-1c'))
        except ValueError: self.set_preview(''); self.mask_status.set('Limite de 20.000 caracteres.'); return
        self.set_preview(result.text)
        counts='; '.join(f'{name}: {n}' for name,n in result.counts)
        self.mask_status.set(f'{sum(n for _,n in result.counts)} padrões mascarados. {counts}. Revise: não é anonimização garantida.')
    def reset_mask(self):
        self.original.delete('1.0','end'); self.original.edit_modified(False); self.set_preview(''); self.mask_status.set('Nenhum texto processado.')
