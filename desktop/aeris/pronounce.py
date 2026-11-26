"""Local pronunciation exercises using the shared speech engine."""
from aeris.voice import speech_payload

LANGUAGES = {'Português':'pt', 'English':'en', 'Español':'es'}
EXERCISES = {
    'pt': ('Bom dia!', 'Muito obrigado pela ajuda.', 'Gostaria de aprender algo novo.', 'Como posso ajudar?'),
    'en': ('Good morning!', 'Thank you for your help.', 'I would like to learn something new.', 'How can I help?'),
    'es': ('¡Buenos días!', 'Muchas gracias por tu ayuda.', 'Me gustaría aprender algo nuevo.', '¿Cómo puedo ayudar?'),
}

def practice_payload(text, language, voice, rate=-2, volume=80, repeat=2):
    if language not in EXERCISES: raise ValueError('Idioma inválido.')
    if not isinstance(text,str) or len(text)>500: raise ValueError('Limite de 500 caracteres por exercício.')
    if not isinstance(voice,str) or not voice.strip(): raise ValueError('Selecione uma voz instalada para o idioma.')
    if type(repeat) is not int or not 1<=repeat<=5: raise ValueError('Escolha de 1 a 5 repetições.')
    return dict(speech_payload(text,voice,rate,volume),language=language,repeat=repeat)
