"""Preferências não sensíveis; leitura dos esquemas 1 a 49 e gravação em esquema 49."""
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import tempfile
from aeris.safe_input import bounded_read, strict_json

MAX_SETTINGS = 64 * 1024

CORNERS = ('Inferior direito', 'Inferior esquerdo', 'Superior direito', 'Superior esquerdo')
SIZES = {'Compacto': (280, 280), 'Normal': (320, 420), 'Grande': (420, 520)}
FAVORITES = ('Capture', 'Snippets', 'Search', 'Vault', 'Clipboard', 'Bookmarks', 'Backup', 'Translate', 'Voice', 'Text', 'Email', 'Pronounce', 'Autofill', 'Expand', 'Bridge', 'Routine', 'Workspace', 'Link', 'Verify', 'Metadata', 'Health', 'Documents', 'Organizer', 'Drop', 'Compare', 'Lens', 'Focus', 'Checklist', 'Reminder', 'Ideas', 'Timeline', 'Data', 'Dashboard', 'Report', 'Calculator', 'Convert', 'Learn', 'Research', 'Flashcards', 'Accessibility', 'Decision', 'Copilot', 'Context', 'Interview', 'Debug', 'Meeting')
THEMES = ('Claro', 'Escuro')
FLAGS = ('capture_enabled', 'snippets_enabled', 'search_enabled', 'vault_enabled', 'clipboard_enabled', 'bookmarks_enabled', 'backup_enabled', 'translate_enabled', 'voice_enabled', 'text_enabled', 'email_enabled', 'pronounce_enabled', 'autofill_enabled', 'expand_enabled', 'bridge_enabled', 'routine_enabled', 'workspace_enabled', 'link_enabled', 'verify_enabled', 'metadata_enabled', 'health_enabled', 'documents_enabled', 'organizer_enabled', 'drop_enabled', 'compare_enabled', 'lens_enabled', 'focus_enabled', 'checklist_enabled', 'reminder_enabled', 'ideas_enabled', 'timeline_enabled', 'data_enabled', 'dashboard_enabled', 'report_enabled', 'calculator_enabled', 'convert_enabled', 'learn_enabled', 'research_enabled', 'flashcards_enabled', 'accessibility_enabled', 'decision_enabled', 'copilot_enabled', 'context_enabled', 'interview_enabled', 'debug_enabled', 'meeting_enabled')

@dataclass(frozen=True)
class Appearance:
    corner: str = 'Inferior direito'
    icon_size: int = 36
    panel_size: str = 'Normal'
    opacity: int = 100
    quick_enabled: bool = True
    floating_enabled: bool = False
    floating_topmost: bool = False
    theme: str = 'Claro'
    favorites: tuple[str, ...] = ()
    favorites_only: bool = False

    def __post_init__(self):
        if self.theme not in THEMES:
            raise ValueError('Tema inválido')
        if not isinstance(self.favorites, (tuple, list)) or any(type(n) is not str or n not in FAVORITES for n in self.favorites) or len(set(self.favorites)) != len(self.favorites):
            raise ValueError('Favoritos inválidos')
        object.__setattr__(self, 'favorites', tuple(self.favorites))
        if self.corner not in CORNERS or self.panel_size not in SIZES:
            raise ValueError('Posição ou tamanho desconhecido')
        for value, lo, hi in [(self.icon_size,24,64),(self.opacity,80,100)]:
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError('Aparência fora do intervalo')
        if any(type(v) is not bool for v in (self.quick_enabled,self.floating_enabled,self.floating_topmost,self.favorites_only)):
            raise ValueError('Modo inválido')

def default_path():
    return Path(os.environ.get('LOCALAPPDATA') or Path.home()/'.config')/'Aeris'/'settings.json'

class Settings:
    def __init__(self,path=None):
        self.path = Path(path) if path is not None else default_path()
        self.appearance = Appearance()
        self.warning = ''
        for flag in FLAGS: setattr(self,flag,False)
        try:
            data = strict_json(bounded_read(self.path, MAX_SETTINGS), MAX_SETTINGS)
            schema = data['schema']
            if type(schema) is not int or schema not in (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49): raise ValueError('Esquema inválido')
            flags = {k: data[k] if schema >= required else False for k,required in zip(FLAGS,(1,3,4,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49))}
            if any(type(v) is not bool for v in flags.values()): raise ValueError('Flag inválida')
            appearance = Appearance(**data['appearance']) if schema >= 2 else Appearance()
            for k,v in flags.items(): setattr(self,k,v)
            self.appearance = appearance
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError, KeyError):
            self.warning = 'Preferências inválidas ou inacessíveis. Módulos opcionais desativados.'

    def _save(self, **changes):
        data = {k:getattr(self,k) for k in FLAGS}
        data['appearance'] = self.appearance
        data.update(changes)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        tmp = None
        try:
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=self.path.parent,delete=False) as f:
                tmp = Path(f.name)
                json.dump({'schema':49, **data, 'appearance':asdict(data['appearance'])},f,ensure_ascii=False)
            os.replace(tmp,self.path)
        finally:
            if tmp is not None: tmp.unlink(missing_ok=True)
        for k,v in data.items(): setattr(self,k,v)
        self.warning = ''

    def set_module(self,name,enabled):
        flag = name.lower()+'_enabled'
        if flag not in FLAGS: raise ValueError('Módulo desconhecido')
        if type(enabled) is not bool: raise TypeError('Esperado booleano')
        self._save(**{flag:enabled})

    def set_capture(self,enabled): self.set_module('Capture',enabled)
    def set_snippets(self,enabled): self.set_module('Snippets',enabled)
    def set_search(self,enabled): self.set_module('Search',enabled)
    def set_appearance(self,appearance):
        if not isinstance(appearance,Appearance): raise TypeError('Esperado Appearance')
        self._save(appearance=appearance)
