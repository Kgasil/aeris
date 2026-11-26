"""Bounded line comparison; not a byte-level or semantic comparison."""
from dataclasses import dataclass
from difflib import SequenceMatcher
from aeris.documents import extract_file, Cancelled

MAX_CHARS = 100_000
MAX_LINES = 2_000

@dataclass(frozen=True)
class Change:
    kind: str
    old: int | None
    new: int | None
    text: str

@dataclass(frozen=True)
class Comparison:
    rows: tuple[Change, ...]
    kept: int
    removed: int
    added: int


def _lines(text):
    if not isinstance(text, str) or len(text)>MAX_CHARS:
        raise ValueError('Cada texto deve ter até 100.000 caracteres.')
    text=text.replace('\r\n','\n').replace('\r','\n')
    # Split only LF, preserving the final newline distinction.
    lines=text.split('\n')
    if lines[-1]=='': lines.pop()
    result=[line+'\n' if i<len(lines)-1 or text.endswith('\n') else line for i,line in enumerate(lines)]
    if len(result)>MAX_LINES: raise ValueError('Cada texto deve ter até 2.000 linhas.')
    return result


def compare_texts(original, revised, *, cancelled=lambda:False):
    def check():
        if cancelled(): raise Cancelled()
    check(); a,b=_lines(original),_lines(revised); check()
    matcher=SequenceMatcher(None,a,b,autojunk=False)
    rows=[]; kept=removed=added=0
    for tag,i,j,k,l in matcher.get_opcodes():
        check()
        if tag=='equal':
            kept+=j-i
            rows.extend(Change(' ',x+1,y+1,a[x]) for x,y in zip(range(i,j),range(k,l)))
        else:
            removed+=j-i; added+=l-k
            rows.extend(Change('-',x+1,None,a[x]) for x in range(i,j))
            rows.extend(Change('+',None,y+1,b[y]) for y in range(k,l))
    check(); return Comparison(tuple(rows),kept,removed,added)


def compare_files(original, revised, *, cancelled=lambda:False):
    a=extract_file(original,cancelled=cancelled)
    b=extract_file(revised,cancelled=cancelled)
    if a.truncated or b.truncated: raise ValueError('Texto extraído truncado; comparação incompleta recusada.')
    return compare_texts(a.text,b.text,cancelled=cancelled)
