"""Bounded, local reading preferences and logical-line guide."""
from dataclasses import dataclass

MAX_TEXT = 20_000
PALETTES = {
    'Natural': ('#FFFFFF', '#285640', '#DCEFE3', '#285640'),
    'Escuro': ('#17221C', '#E3F3E9', '#365843', '#FFFFFF'),
    'Alto contraste': ('#000000', '#FFFFFF', '#FFFF00', '#000000'),
}

@dataclass(frozen=True)
class ReadingOptions:
    size: int = 16
    palette: str = 'Natural'
    spacious: bool = False
    guide: bool = False

    def __post_init__(self):
        if type(self.size) is not int or not 12 <= self.size <= 30:
            raise ValueError('Tamanho deve estar entre 12 e 30 pontos.')
        if self.palette not in PALETTES or type(self.spacious) is not bool or type(self.guide) is not bool:
            raise ValueError('Preferência de leitura inválida.')

class Reader:
    def __init__(self): self.clear()
    def clear(self): self.text = ''; self.line = 1
    @property
    def lines(self): return self.text.count('\n') + 1 if self.text else 0
    def load(self, text):
        if not isinstance(text, str) or len(text)>MAX_TEXT or '\x00' in text:
            raise ValueError('Texto inválido ou acima de 20.000 caracteres.')
        self.text = text.replace('\r\n','\n').replace('\r','\n'); self.line = 1
    def move(self, delta):
        if type(delta) is not int or delta not in (-1,1): raise ValueError('Direção inválida.')
        self.line = max(1,min(self.lines,self.line+delta)); return self.line
