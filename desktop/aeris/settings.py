"""Preferências locais não sensíveis, com migração dos esquemas 1 e 2."""
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import tempfile

CORNERS = ('Inferior direito', 'Inferior esquerdo', 'Superior direito', 'Superior esquerdo')
SIZES = {'Compacto': (280, 280), 'Normal': (320, 420), 'Grande': (420, 520)}

@dataclass(frozen=True)
class Appearance:
    corner: str = 'Inferior direito'
    icon_size: int = 36
    panel_size: str = 'Normal'
    opacity: int = 100
    quick_enabled: bool = True

    def __post_init__(self):
        if self.corner not in CORNERS or self.panel_size not in SIZES:
            raise ValueError('Posição ou tamanho desconhecido')
        if type(self.icon_size) is not int or not 24 <= self.icon_size <= 64:
            raise ValueError('Ícone fora do intervalo')
        if type(self.opacity) is not int or not 80 <= self.opacity <= 100:
            raise ValueError('Opacidade fora do intervalo')
        if type(self.quick_enabled) is not bool:
            raise ValueError('Modo inválido')

def default_path():
    return Path(os.environ.get('LOCALAPPDATA') or Path.home() / '.config') / 'Aeris' / 'settings.json'

class Settings:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else default_path()
        self.capture_enabled = False
        self.snippets_enabled = False
        self.appearance = Appearance()
        self.warning = ''
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or type(data.get('schema')) is not int or data['schema'] not in (1, 2, 3) or type(data.get('capture_enabled')) is not bool:
                raise ValueError('Formato desconhecido')
            appearance = Appearance(**data['appearance']) if data['schema'] >= 2 else Appearance()
            snippets = data['snippets_enabled'] if data['schema'] == 3 else False
            if type(snippets) is not bool:
                raise ValueError('Formato desconhecido')
            self.snippets_enabled = snippets
            self.capture_enabled = data['capture_enabled']
            self.appearance = appearance
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError, KeyError):
            self.warning = 'Preferências inválidas ou inacessíveis. Padrões restaurados; Capture e Snippets desativados.'

    def _save(self, capture_enabled, appearance, snippets_enabled):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.path.parent, delete=False) as file:
                tmp = Path(file.name)
                json.dump({'schema': 3, 'capture_enabled': capture_enabled,
                           'snippets_enabled': snippets_enabled,
                           'appearance': asdict(appearance)}, file, ensure_ascii=False)
            os.replace(tmp, self.path)
        finally:
            if tmp is not None:
                tmp.unlink(missing_ok=True)
        self.capture_enabled = capture_enabled
        self.snippets_enabled = snippets_enabled
        self.appearance = appearance
        self.warning = ''

    def set_capture(self, enabled):
        if type(enabled) is not bool:
            raise TypeError('Esperado booleano')
        self._save(enabled, self.appearance, self.snippets_enabled)

    def set_appearance(self, appearance):
        if not isinstance(appearance, Appearance):
            raise TypeError('Esperado Appearance')
        self._save(self.capture_enabled, appearance, self.snippets_enabled)

    def set_snippets(self, enabled):
        if type(enabled) is not bool:
            raise TypeError('Esperado booleano')
        self._save(self.capture_enabled, self.appearance, enabled)
