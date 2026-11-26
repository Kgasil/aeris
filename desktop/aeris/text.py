"""Deterministic local transformations. No network, grammar model or persistence."""
import re
from dataclasses import dataclass

LIMIT = 20000
OPERATIONS = ('Maiúsculas', 'Minúsculas', 'Remover espaços excedentes',
              'Remover linhas vazias', 'Remover linhas duplicadas', 'Padronizar quebras de linha')

@dataclass(frozen=True)
class Stats:
    characters: int
    words: int
    lines: int

def validate(text):
    if not isinstance(text, str) or len(text)>LIMIT or '\0' in text:
        raise ValueError('Use texto de até 20.000 caracteres, sem caracteres NUL.')

def stats(text):
    validate(text)
    return Stats(len(text), len(text.split()), len(text.splitlines()) if text else 0)

def transform(text, operation):
    validate(text)
    if operation not in OPERATIONS: raise ValueError('Operação desconhecida.')
    if operation == 'Maiúsculas': result = text.upper()
    elif operation == 'Minúsculas': result = text.lower()
    elif operation == 'Padronizar quebras de linha': result = text.replace('\r\n','\n').replace('\r','\n')
    else:
        lines = text.replace('\r\n','\n').replace('\r','\n').split('\n')
        if operation == 'Remover espaços excedentes':
            result = '\n'.join(re.sub(r'[ \t]+', ' ', line).strip(' \t') for line in lines)
        elif operation == 'Remover linhas vazias': result = '\n'.join(line for line in lines if line.strip())
        else: result = '\n'.join(dict.fromkeys(lines))
    validate(result)
    return result
