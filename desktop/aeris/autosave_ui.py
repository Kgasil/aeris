"""Explicit per-module session opt-in controls."""
import tkinter as tk
from tkinter import ttk, messagebox
from aeris.protected_storage import MODULES
from aeris.permissions import STORAGE_AUTO, STORAGE_SAVE

class AutoSavePanel:
    def __init__(self,parent,hub,refresh):
        self.parent=parent; self.hub=hub; self.refresh_parent=refresh
        self.module=tk.StringVar(parent,MODULES[0]); self.notice=tk.StringVar(parent,'')
        ttk.Label(parent,text='Salvamento automático opcional. Apenas nesta sessão, a cada 10 segundos, se os registros confirmados mudarem. Nenhum rascunho é copiado.',wraplength=490).pack(anchor='w',pady=5)
        select=ttk.Combobox(parent,values=MODULES,textvariable=self.module,state='readonly'); select.pack(fill='x')
        self.states=tk.StringVar(parent); ttk.Label(parent,textvariable=self.states,wraplength=490,justify='left').pack(anchor='w',pady=5)
        for text,fn in [('Ativar automático para selecionado',self.arm),('Desativar selecionado',self.stop),('Desativar todos',self.stop_all),('Salvar alterações agora (módulos ativos)',self.flush)]:
            ttk.Button(parent,text=text,command=fn).pack(fill='x',pady=2)
        ttk.Label(parent,text='Conceda Storage → Salvar e Storage → Automático em Permissões. Abra a ferramenta e crie registros fictícios. Se a cópia divergir, restaure ou salve manualmente antes de ativar. A versão anterior é preservada. Não há gravação final ao encerrar ou limpar sessão; salve antes de sair.',wraplength=490).pack(anchor='w',pady=5)
        ttk.Label(parent,textvariable=self.notice,wraplength=490).pack(anchor='w')
        self.refresh()

    def refresh(self):
        a=self.hub.autosave
        self.states.set('\n'.join(m+': '+(a.status.get(m,'Desativado.') if a else 'Desativado.') for m in MODULES))

    def arm(self):
        m=self.module.get()
        try:
            self.hub.permissions.require(STORAGE_AUTO); self.hub.permissions.require(STORAGE_SAVE)
            if not messagebox.askyesno('Salvamento automático',f'Autorizar cópias automáticas de {m} nesta sessão, incluindo substituição protegida de alterações confirmadas?',parent=self.parent): return
            if self.module.get()!=m: return
            self.hub.arm_autosave(m)
        except (OSError,ValueError,TypeError,KeyError,RuntimeError):
            self.notice.set('Não ativado. Confira permissões, DPAPI, registros e cópia existente.'); return
        self.notice.set('Autorização registrada nesta sessão.'); self.refresh_parent()
    def stop(self):
        self.hub.stop_autosave(self.module.get()); self.refresh_parent()
    def stop_all(self):
        self.hub.stop_autosave(); self.refresh_parent()
    def flush(self):
        if self.hub.autosave and self.hub.autosave.armed: self.hub.autosave_tick()
