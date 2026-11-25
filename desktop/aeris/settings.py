"""Apenas preferências não sensíveis; nenhum conteúdo de anotações."""
import json
import os
from pathlib import Path
import tempfile

def default_path():
    return Path(os.environ.get('LOCALAPPDATA') or Path.home() / '.config') / 'Aeris' / 'settings.json'

class Settings:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else default_path()
        self.capture_enabled = False
        self.warning = ''
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or data.get('schema') != 1 or type(data.get('capture_enabled')) is not bool:
                raise ValueError('Formato desconhecido')
            self.capture_enabled = data['capture_enabled']
        except FileNotFoundError:
            pass
        except (OSError, ValueError):
            self.warning = 'Preferências não puderam ser lidas. Capture desativado por segurança.'

    def set_capture(self, enabled):
        if type(enabled) is not bool:
            raise TypeError('Esperado booleano')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.path.parent, delete=False) as file:
                tmp = Path(file.name)
                json.dump({'schema': 1, 'capture_enabled': enabled}, file)
            os.replace(tmp, self.path)
        finally:
            if tmp is not None:
                tmp.unlink(missing_ok=True)
        self.capture_enabled = enabled
        self.warning = ''
