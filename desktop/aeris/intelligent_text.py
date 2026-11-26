"""Small conservative, offline correction rules. Suggestions are not a grammar model."""
from dataclasses import dataclass
import re
from aeris.text import validate

LANGUAGES = ('Português (BR)', 'English', 'Español')
# Only unambiguous/common misspellings in ordinary prose; context is not understood.
WORDS = {
    LANGUAGES[0]: {'voce':'você','voces':'vocês','nao':'não','tambem':'também',
        'informacao':'informação','informacoes':'informações','reuniao':'reunião',
        'concerteza':'com certeza','derrepente':'de repente','excessão':'exceção',
        'previlégio':'privilégio','nescessário':'necessário','seje':'seja','esteje':'esteja',
        'portugês':'português','obrigatorio':'obrigatório','ola':'olá', 'adiministrar':'administrar','beneficiente':'beneficente','paralização':'paralisação','impecilho':'empecilho','reinvindicar':'reivindicar','indentidade':'identidade','progeto':'projeto','pesquiza':'pesquisa'},
    LANGUAGES[1]: {'teh':'the','recieve':'receive','recieved':'received','seperate':'separate',
        'definately':'definitely','adress':'address','occured':'occurred','wich':'which',
        'enviroment':'environment','goverment':'government','becuase':'because','accomodate':'accommodate','tommorow':'tomorrow','sucessful':'successful','begining':'beginning','neccessary':'necessary','existance':'existence','recomendation':'recommendation','untill':'until'},
    LANGUAGES[2]: {'tambien':'también','informacion':'información','reunion':'reunión',
        'comunicacion':'comunicación','organizacion':'organización','nesesario':'necesario',
        'desarollo':'desarrollo','exepción':'excepción','aser':'hacer','nececario':'necesario','desición':'decisión','exelente':'excelente','conosimiento':'conocimiento','investigacion':'investigación','educacion':'educación','tambiem':'también','proyeto':'proyecto'},
}
# Grammar suggestions only: never automatically apply contextual changes.
PHRASES = {LANGUAGES[0]: {'a gente fomos':'a gente foi','a gente estamos':'a gente está'},
           LANGUAGES[1]: {'he have':'he has','she have':'she has'},
           LANGUAGES[2]: {'yo tiene':'yo tengo','nosotros tiene':'nosotros tenemos'}}
# Skip common identifiers, URLs, email addresses, file paths and inline/fenced code.
PROTECTED = re.compile(r'```[\s\S]*?(?:```|\Z)|`[^`\n]*(?:`|\n|\Z)|(?:https?://|www\.)\S+|\b[^\s<>@]+@[^\s<>@]+|(?:[A-Za-z]:[\\/]|(?<!\w)/)\S+|\b\w+(?:[._/\\-]\w+)+\b', re.I)

@dataclass(frozen=True)
class Edit:
    start: int
    end: int
    before: str
    after: str
    kind: str

@dataclass(frozen=True)
class Review:
    text: str
    edits: tuple[Edit, ...]


def _case(before, after):
    if before.isupper(): return after.upper()
    if before.islower(): return after
    if before[0].isupper() and before[1:].islower(): return after[0].upper()+after[1:]
    return before  # mixed-case identifiers


def dictionary_words(raw):
    """Validate a bounded, session-only list of exact case-insensitive words."""
    if not isinstance(raw,str) or len(raw)>5000: raise ValueError('Dicionário inválido.')
    terms=[w.strip() for w in raw.split(',') if w.strip()]
    if len(terms)>100 or any(len(w)>50 or not w.isalpha() for w in terms):
        raise ValueError('Use até 100 palavras de até 50 letras, separadas por vírgula.')
    return frozenset(w.casefold() for w in terms)


def review(text, language, *, automatic=False, ignored=frozenset()):
    validate(text)
    if language not in WORDS: raise ValueError('Idioma não suportado.')
    rules = {k:(v,'Ortografia') for k,v in WORDS[language].items()}
    if not automatic: rules.update({k:(v,'Gramática (sugestão)') for k,v in PHRASES[language].items()})
    pattern = re.compile(r'(?<![\w])(?:'+'|'.join(re.escape(k) for k in sorted(rules,key=len,reverse=True))+r')(?![\w])',re.I)
    protected = iter(PROTECTED.finditer(text)); block = next(protected,None)
    edits=[]; pieces=[]; pos=0
    for match in pattern.finditer(text):
        start,end=match.span()
        while block is not None and block.end()<=start: block=next(protected,None)
        if block is not None and block.start()<end: continue
        if automatic and end==len(text): continue  # don't replace an unfinished final word
        before=match.group()
        if any(w.casefold() in ignored for w in before.split()): continue
        rule=rules.get(before.lower())
        if rule is None: continue
        after,kind=rule; after=_case(before,after)
        if before==after: continue
        edits.append(Edit(start,end,before,after,kind)); pieces.extend((text[pos:start],after)); pos=end
    pieces.append(text[pos:]); result=''.join(pieces); validate(result)
    return Review(result,tuple(edits))


def cursor_after(offset, edits):
    shift=0
    for e in edits:
        if offset<e.start: break
        if offset<e.end: return e.start+shift+min(offset-e.start,len(e.after))
        shift+=len(e.after)-(e.end-e.start)
    return offset+shift
