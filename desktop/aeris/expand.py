"""Expansão explícita de abreviações; sem hooks globais, disco ou rede."""
import re
from dataclasses import dataclass

MAX_INPUT = 20000
MAX_OUTPUT = 100000
MAX_RULES = 100
MAX_REPLACEMENT = 2000
CODE = re.compile(r';[a-z][a-z0-9_-]{0,31}', re.ASCII)
TOKEN = re.compile(r'(?<![\w;@-]);[a-z][a-z0-9_-]{0,31}(?![\w-])')
DEFAULTS = ((';att', 'Atenciosamente,'), (';obg', 'Muito obrigado pela atenção!'), (';retorno', 'Fico à disposição e aguardo seu retorno.'))

@dataclass(frozen=True)
class Expansion:
    text: str
    count: int

class ExpandStore:
    def __init__(self):
        self._rules = dict(DEFAULTS)

    def list(self):
        return tuple(sorted(self._rules.items()))

    def save(self, code, text):
        if not isinstance(code,str) or not CODE.fullmatch(code):
            raise ValueError('Use ; seguido de 1–32 letras minúsculas ASCII, números, _ ou -, começando por letra.')
        if not isinstance(text,str) or not text.strip() or len(text)>MAX_REPLACEMENT:
            raise ValueError('Texto obrigatório, até 2.000 caracteres.')
        if code not in self._rules and len(self._rules)>=MAX_RULES:
            raise ValueError('Limite de 100 abreviações.')
        self._rules[code]=text

    def delete(self, code):
        del self._rules[code]

    def clear(self):
        self._rules.clear()

    def expand(self, text):
        if not isinstance(text,str) or len(text)>MAX_INPUT:
            raise ValueError('Entrada limitada a 20.000 caracteres.')
        parts=[]; size=0; count=0; end=0
        for match in TOKEN.finditer(text):
            replacement=self._rules.get(match.group())
            if replacement is None: continue
            prefix=text[end:match.start()]
            size+=len(prefix)+len(replacement)
            if size>MAX_OUTPUT: raise ValueError('Resultado excede 100.000 caracteres.')
            parts.extend((prefix,replacement)); end=match.end(); count+=1
        tail=text[end:]
        if size+len(tail)>MAX_OUTPUT: raise ValueError('Resultado excede 100.000 caracteres.')
        parts.append(tail)
        return Expansion(''.join(parts),count)
