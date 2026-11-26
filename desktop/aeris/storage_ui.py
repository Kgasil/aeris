"""Manual snapshot controls embedded in Privacy. No automatic file reads/writes."""
import tkinter as tk
from tkinter import ttk, messagebox
from aeris.permissions import STORAGE_SAVE, STORAGE_LOAD, STORAGE_DELETE
from aeris.protected_storage import MODULES, ProtectedStorage
from aeris.privacy import file_status

class StoragePanel:
    def __init__(self, parent, hub, refresh):
        self.hub=hub; self.parent=parent; self.refresh_parent=refresh
        self.module=tk.StringVar(parent, MODULES[0]); self.status=tk.StringVar(parent, '')
        ttk.Label(parent,text='Cópias locais protegidas (Windows DPAPI). Somente registros já confirmados nas ferramentas, não rascunhos. A gravação automática opcional fica na aba Automático.',wraplength=500).pack(anchor='w',pady=6)
        selector=ttk.Combobox(parent,textvariable=self.module,values=MODULES,state='readonly'); selector.pack(fill='x',pady=4)
        selector.bind('<<ComboboxSelected>>',lambda _:self.refresh())
        self.info=tk.StringVar(parent); ttk.Label(parent,textvariable=self.info,wraplength=500).pack(anchor='w',pady=4)
        self.keep_previous=tk.BooleanVar(parent,False)
        ttk.Checkbutton(parent,text='Preservar uma versão anterior ao salvar',variable=self.keep_previous).pack(anchor='w')
        buttons=ttk.Frame(parent); buttons.pack(fill='x',pady=3); buttons.columnconfigure(0,weight=1); buttons.columnconfigure(1,weight=1)
        for i,(label,action) in enumerate( [('Salvar cópia protegida',self.save),('Restaurar cópia na sessão',self.load),('Excluir cópia do disco',self.delete),('Recuperar versão anterior na sessão',self.load_previous),('Excluir versão anterior',self.delete_previous)]):
            ttk.Button(buttons,text=label,command=action).grid(row=i//2,column=i%2,sticky='ew',padx=2,pady=3)
        ttk.Label(parent,text='Feche a janela da ferramenta antes de restaurar. Restaurar substitui os registros em memória. Lembretes vencidos são marcados como vencidos sem repetir alertas. Limpar sessão preserva as cópias gravadas. Não use dados reais nesta pré-alpha.',wraplength=500).pack(anchor='w',pady=6)
        ttk.Label(parent,textvariable=self.status,wraplength=500).pack(anchor='w',pady=4)
        self.refresh()

    def refresh(self):
        m=self.module.get(); path=self.hub.settings.path.parent/('storage-'+m.lower()+'.bin')
        self.info.set('Cópia no disco: '+file_status(path)+' | Anterior: '+file_status(path.with_suffix('.previous.bin')))

    def storage(self): return ProtectedStorage(self.hub.settings.path.parent)

    def perform(self, capability, prompt, action):
        try:
            self.hub.permissions.require(capability)
            m=self.module.get()
            if m not in MODULES: raise ValueError('Módulo inválido.')
            if not messagebox.askyesno('Armazenamento protegido',prompt,parent=self.parent): return
            self.hub.permissions.require(capability)
            if self.module.get()!=m: return
            self.hub.stop_autosave(m)
            action(m)
        except (OSError, ValueError, TypeError, KeyError, RecursionError, RuntimeError):
            self.status.set('Operação não concluída. Verifique permissões, Windows DPAPI, estado da ferramenta e integridade da cópia.'); return
        self.status.set('Operação concluída.'); self.refresh_parent()

    def save(self):
        def action(m):
            store=getattr(self.hub,m.lower()+'_store')
            if not self.hub.enabled(m) or store is None: raise ValueError('Abra a ferramenta primeiro.')
            self.storage().save(m,store,overwrite=True,keep_previous=self.keep_previous.get())
        self.perform(STORAGE_SAVE,'Salvar os registros atuais e substituir a cópia anterior, se existir? Rascunhos não entram na cópia.',action)

    def load(self): self.restore(False)

    def load_previous(self): self.restore(True)

    def restore(self,previous):
        def action(m):
            attr=m.lower()
            if not self.hub.enabled(m) or self.hub.alive(getattr(self.hub,attr+'_window')): raise ValueError('Ative a ferramenta e feche sua janela.')
            if self.hub.alive(self.hub.copilot_window): raise ValueError('Feche também o Copilot.')
            restored=self.storage().load_previous(m) if previous else self.storage().load(m)
            setattr(self.hub,attr+'_store',restored)
            if m=='Reminder':
                self.hub.close_window('reminder_alert')
                self.hub.schedule_reminders()
        self.perform(STORAGE_LOAD,('Recuperar a versão anterior' if previous else 'Restaurar a cópia atual')+' e substituir os registros em memória? Feche a ferramenta e o Copilot primeiro.',action)

    def delete(self):
        self.perform(STORAGE_DELETE,'Excluir a cópia atual do disco? A versão anterior, se houver, permanece até exclusão separada. Não é apagamento seguro.',lambda m:self.storage().delete(m))

    def delete_previous(self):
        self.perform(STORAGE_DELETE,'Excluir a versão anterior protegida? A cópia atual permanece. Não é apagamento seguro.',lambda m:self.storage().delete_previous(m))
