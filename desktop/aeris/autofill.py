"""Protected allowlisted profiles; no browser, keyboard or network access."""
from dataclasses import dataclass
import json
from aeris.safe_input import strict_json
from aeris.vault import Vault
from aeris.permissions import COPY_AUTOFILL

FIELDS = {'name':'Nome completo', 'email':'E-mail', 'tel':'Telefone', 'organization':'Empresa', 'organization-title':'Cargo'}

@dataclass(frozen=True)
class Profile:
    id: int
    title: str
    fields: dict

def validate(title, fields):
    if type(title) is not str or not 1<=len(title.strip())<=120:
        raise ValueError('Nome do perfil obrigatório (até 120 caracteres).')
    if type(fields) is not dict or not fields or not set(fields)<=set(FIELDS):
        raise ValueError('Somente campos de perfil permitidos.')
    clean={}
    for key,value in fields.items():
        if type(value) is not str or len(value)>250 or any(ord(c)<32 or ord(c)==127 for c in value):
            raise ValueError('Campo inválido (até 250 caracteres, uma linha).')
        if value.strip(): clean[key]=value.strip()
    if not clean: raise ValueError('Preencha ao menos um campo.')
    return title.strip(),clean

def preview(fields, requested):
    """Exact allowlist intersection; never infer passwords or other sensitive fields."""
    if not isinstance(requested,(list,tuple)): raise ValueError('Seleção inválida.')
    return tuple((key,fields[key]) for key in FIELDS if key in requested and key in fields)

class ProfileStore:
    def __init__(self,path,permissions,backend=None):
        self.vault=Vault(path,backend); self.permissions=permissions
    @property
    def unlocked(self): return self.vault.unlocked
    def lock(self): self.vault.lock()
    def unlock(self):
        self.vault.unlock()
        try: self.list()
        except Exception: self.lock(); raise
    def list(self):
        result=[]
        for item in self.vault.list():
            title,fields=validate(item.title,strict_json(item.body, 80000))
            result.append(Profile(item.id,title,fields))
        return tuple(result)
    def get(self,item_id):
        for item in self.list():
            if item.id==item_id: return item
        raise KeyError(item_id)
    def save(self,title,fields,item_id=None):
        title,fields=validate(title,fields)
        item=self.vault.save(title,json.dumps(fields,ensure_ascii=False),item_id)
        return Profile(item.id,title,fields)
    def delete(self,item_id): self.vault.delete(item_id)
    def preview(self,item_id,requested): return preview(self.get(item_id).fields,requested)
    def copy_value(self,item_id,key):
        self.permissions.require(COPY_AUTOFILL)
        if key not in FIELDS: raise ValueError('Campo não permitido.')
        return self.get(item_id).fields[key]
