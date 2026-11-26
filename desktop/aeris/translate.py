"""Small exact phrasebook; optional free-text engine runs in a separate process."""
import unicodedata

LANGUAGES = {'pt':'Português', 'en':'Inglês', 'es':'Espanhol'}
PHRASES = (
    ('Olá!', 'Hello!', '¡Hola!'),
    ('Bom dia!', 'Good morning!', '¡Buenos días!'),
    ('Boa tarde!', 'Good afternoon!', '¡Buenas tardes!'),
    ('Boa noite!', 'Good night!', '¡Buenas noches!'),
    ('Por favor.', 'Please.', 'Por favor.'),
    ('Muito obrigado.', 'Thank you very much.', 'Muchas gracias.'),
    ('Como posso ajudar?', 'How can I help?', '¿Cómo puedo ayudar?'),
    ('Fico à disposição.', 'I am available to help.', 'Quedo a disposición.'),
    ('Até logo!', 'See you later!', '¡Hasta luego!'),
    ('Preciso de ajuda.', 'I need help.', 'Necesito ayuda.'),
    ('Onde fica a estação?', 'Where is the station?', '¿Dónde está la estación?'),
    ('Qual é o preço?', 'What is the price?', '¿Cuál es el precio?'),
)
MAX_TEXT=4000

def validate(text, source, target):
    if source not in LANGUAGES or target not in LANGUAGES or source==target:
        raise ValueError('Selecione idiomas diferentes.')
    if not isinstance(text,str) or not text.strip() or len(text)>MAX_TEXT:
        raise ValueError('Digite entre 1 e 4.000 caracteres.')

def key(text):
    return ' '.join(unicodedata.normalize('NFC',text).casefold().strip().strip('!¡?¿.').split())

def phrase_translate(text, source, target):
    validate(text,source,target)
    codes=tuple(LANGUAGES); a,b=codes.index(source),codes.index(target)
    for row in PHRASES:
        if key(row[a])==key(text): return row[b]
    raise ValueError('Frase não encontrada no guia. Use um modelo opcional preparado para textos livres.')
