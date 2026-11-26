"""Local templates; no translation, delivery, accounts or generated facts."""
from dataclasses import dataclass

LANGUAGES = ('Português', 'English', 'Español')
TONES = ('Formal', 'Direto')
PURPOSES = ('Solicitação', 'Acompanhamento', 'Agradecimento', 'Atualização')
# Per-language opening sentences and suggested subjects. User supplies factual details.
TEMPLATES = {
    'Português': (
        ('Solicitação', 'Gostaria de solicitar sua atenção ao seguinte assunto.', 'Segue minha solicitação.'),
        ('Acompanhamento', 'Gostaria de acompanhar o andamento do assunto abaixo.', 'Retomo o assunto abaixo.'),
        ('Agradecimento', 'Gostaria de expressar meu agradecimento.', 'Muito obrigado pela atenção.'),
        ('Atualização', 'Compartilho a seguinte atualização para sua ciência.', 'Segue uma atualização.'),
    ),
    'English': (
        ('Request', 'I would like to bring the following request to your attention.', 'Here is my request.'),
        ('Follow-up', 'I would like to follow up on the matter below.', 'I am following up on the matter below.'),
        ('Thank you', 'I would like to express my appreciation.', 'Thank you for your time.'),
        ('Update', 'I would like to share the following update.', 'Here is an update.'),
    ),
    'Español': (
        ('Solicitud', 'Me gustaría presentar la siguiente solicitud.', 'Comparto mi solicitud.'),
        ('Seguimiento', 'Me gustaría dar seguimiento al asunto indicado a continuación.', 'Retomo el asunto indicado a continuación.'),
        ('Agradecimiento', 'Me gustaría expresar mi agradecimiento.', 'Muchas gracias por su atención.'),
        ('Actualización', 'Me gustaría compartir la siguiente actualización.', 'Comparto una actualización.'),
    ),
}
GREETINGS = {
    'Português': ('Olá', 'Olá', 'Atenciosamente,', 'Obrigado,'),
    'English': ('Dear', 'Hello', 'Kind regards,', 'Best,'),
    'Español': ('Estimado/a', 'Hola', 'Atentamente,', 'Saludos,'),
}
GENERIC = {'Português': ('Prezados,', 'Olá,'), 'English': ('Hello,', 'Hello,'), 'Español': ('Estimados/as:', 'Hola,')}

@dataclass(frozen=True)
class Draft:
    subject: str
    body: str


def field(value, maximum, single_line=False):
    if not isinstance(value, str) or len(value) > maximum or '\0' in value:
        raise ValueError(f'Campo inválido ou acima de {maximum} caracteres.')
    if single_line and any(c in value for c in '\r\n\u0085\u2028\u2029'):
        raise ValueError('Nome e assunto devem ter apenas uma linha.')
    return value.strip()


def compose(language, tone, purpose, recipient, subject, details, signature):
    if language not in LANGUAGES or tone not in TONES or purpose not in PURPOSES:
        raise ValueError('Selecione idioma, formalidade e finalidade válidos.')
    recipient = field(recipient, 120, True)
    subject = field(subject, 200, True)
    details = field(details, 8000)
    signature = field(signature, 1000)
    if not details:
        raise ValueError('Informe os detalhes da mensagem no idioma desejado.')
    index = TONES.index(tone)
    default_subject, *intro = TEMPLATES[language][PURPOSES.index(purpose)]
    greetings = GREETINGS[language]
    greeting = (f'{greetings[index]} {recipient}' + (':' if language == 'Español' else ',')) if recipient else GENERIC[language][index]
    closing = greetings[index+2]
    body = '\n\n'.join((greeting, intro[index], details, closing + ('\n'+signature if signature else '')))
    return Draft(subject or default_subject, body)
