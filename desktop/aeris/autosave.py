"""Opt-in session autosave; no timer while disarmed, no plaintext persistence."""
import hashlib
import json
from aeris.protected_storage import MODULES, snapshot, rebuild


def digest(records):
    return hashlib.sha256(json.dumps(records,ensure_ascii=False,sort_keys=True,allow_nan=False).encode('utf-8')).digest()


class AutoSave:
    def __init__(self, storage, allowed, get_store):
        self.storage=storage; self.allowed=allowed; self.get_store=get_store
        self.armed={}; self.status={}

    def arm(self, module):
        if module not in MODULES or not self.allowed(): raise PermissionError('Autorização necessária.')
        store=self.get_store(module)
        if store is None: raise ValueError('Ative e abra a ferramenta.')
        records=snapshot(module,store); rebuild(module,records)
        if not records: raise ValueError('Sessão vazia.')
        token, saved=self.storage.baseline(module)
        if saved is not None and digest(saved)!=digest(records):
            raise ValueError('Restaure ou salve manualmente a cópia antes de ativar.')
        self.armed[module]=(store,token,digest(records) if token is not None else None)
        self.status[module]='Ativo nesta sessão.'

    def stop(self,module,reason='Desativado.'):
        self.armed.pop(module,None); self.status[module]=reason

    def stop_all(self):
        for module in tuple(self.armed): self.stop(module)

    def tick(self):
        failed=[]
        for module,(original,token,last) in tuple(self.armed.items()):
            try:
                store=self.get_store(module)
                if not self.allowed() or store is not original:
                    self.stop(module); continue
                records=snapshot(module,store)
                if not records:
                    self.stop(module,'Pausado: sessão vazia; cópia preservada.'); failed.append(module); continue
                current=digest(records)
                if current==last: continue
                token=self.storage.save_if_current(module,store,token)
                self.armed[module]=(store,token,current)
                self.status[module]='Alterações confirmadas salvas.'
            except (OSError,ValueError,TypeError,KeyError,RecursionError,RuntimeError):
                self.stop(module,'Pausado: conflito ou falha; verifique a cópia manualmente.'); failed.append(module)
        return failed
