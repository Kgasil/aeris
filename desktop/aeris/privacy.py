"""Local inventory and conservative pattern masking, not data loss prevention."""
from dataclasses import dataclass
import re
import stat
from aeris.permissions import CAPABILITIES

FILES = ('settings.json', 'vault.bin', 'bookmarks.bin', 'autofill.bin', 'storage-checklist.bin', 'storage-ideas.bin', 'storage-learn.bin', 'storage-meeting.bin', 'storage-research.bin', 'storage-flashcards.bin', 'storage-reminder.bin')
FILES += tuple('storage-'+m+'.previous.bin' for m in ('checklist','ideas','learn','meeting','research','flashcards','reminder'))
STORES = ('capture', 'snippets', 'clipboard', 'expand', 'routine', 'workspace', 'drop', 'checklist', 'reminder', 'ideas', 'timeline', 'learn', 'research', 'flashcards', 'context', 'interview', 'meeting')
PATTERNS = {
    'E-mail': r'(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+',
    'CPF formatado': r'(?<!\d)\d{3}\.\d{3}\.\d{3}-\d{2}(?!\d)',
    'CNPJ formatado': r'(?<!\d)\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}(?!\d)',
    'Telefone BR formatado': r'(?<!\d)\(\d{2}\)[ \t]?\d{4,5}-\d{4}(?!\d)',
}
_COMBINED = re.compile('|'.join(f'(?P<p{i}>{pattern})' for i,pattern in enumerate(PATTERNS.values())))

@dataclass(frozen=True)
class MaskResult:
    text: str
    counts: tuple[tuple[str,int], ...]

def mask_text(text):
    if not isinstance(text,str) or len(text)>20000:
        raise ValueError('Texto inválido ou acima de 20.000 caracteres.')
    names=tuple(PATTERNS)
    counts=dict.fromkeys(names,0)
    def replace(match):
        name=names[int(match.lastgroup[1:])]
        counts[name]+=1
        return '['+name+' ocultado]'
    return MaskResult(_COMBINED.sub(replace,text),tuple(counts.items()))

def file_status(path):
    try: mode=path.lstat().st_mode
    except FileNotFoundError: return 'Não encontrado'
    except OSError: return 'Não foi possível verificar'
    return 'Presente (conteúdo não verificado)' if stat.S_ISREG(mode) else 'Tipo não regular (não inspecionado)'

def inventory(hub):
    """No file reads, no record contents returned; refresh only on request/events."""
    grants=tuple((label,hub.permissions.allowed(key)) for key,(label,_) in CAPABILITIES.items())
    files=tuple((name,file_status(hub.settings.path if name=='settings.json' else hub.settings.path.parent/name)) for name in FILES)
    stores=tuple((name,len(store.list()) if (store:=getattr(hub,name+'_store',None)) is not None else 0) for name in STORES)
    locks=[]
    for name,attr in [('Vault','vault'),('Bookmarks','store'),('Autofill','store')]:
        ui=getattr(hub,name.lower()+'_window',None)
        locks.append((name,'Desbloqueado' if hub.alive(ui) and getattr(ui,attr).unlocked else 'Fechado / bloqueado'))
    return grants,files,stores,tuple(locks)
