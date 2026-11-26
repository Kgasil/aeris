"""Local model recommends a catalog entry; it cannot execute or access tools."""
from aeris.companion import chat, validate_message
from aeris.experience_help import HELP

TOOLS=(
    'Text','Email','Translate','Voice','Pronounce','Capture','Meeting',
    'Checklist','Reminder','Focus','Ideas','Data','Dashboard','Report',
    'Calculator','Convert','Decision','Documents','Organizer','Compare',
    'Lens','Learn','Research','Flashcards','Debug','Privacy','Link','Verify',
    'Snippets','Bookmarks','Accessibility','Interview',
)
SYSTEM=(
    'Classifique somente a solicitação atual. Retorne exatamente um identificador '
    'da lista abaixo, ou NONE se não houver uma ferramenta claramente adequada. '
    'Não execute ações, não invente recursos e não retorne argumentos ou explicações.\n'
    + '\n'.join(name+': '+HELP[name][0] for name in TOOLS)
)

def recommend_tool(model, request, *, chat_fn=chat):
    """No history, file content, screen, clipboard or tool execution."""
    text=validate_message(request)
    if len(text)>1000:
        raise ValueError('Descreva sua necessidade em até 1.000 caracteres.')
    result=chat_fn(model, (), text, system=SYSTEM)
    if result=='NONE':
        return None
    if result not in TOOLS:
        raise ValueError('Resposta fora do catálogo permitido.')
    return result
