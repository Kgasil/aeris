"""Explicit local workflows. No background jobs or arbitrary code execution."""
from dataclasses import dataclass
from aeris.permissions import BRIDGE_CAPTURE, BRIDGE_SNIPPETS, BRIDGE_RUN, BRIDGE_SAVE, BRIDGE_COPY

ROUTES = {
    'Expand → Text': ('Expand', 'Text'),
    'Translate → Email': ('Translate', 'Email'),
    'Text → Capture': ('Text', 'Capture'),
}
SOURCE_GRANTS = {'Capture': BRIDGE_CAPTURE, 'Snippets': BRIDGE_SNIPPETS}

@dataclass(frozen=True)
class Preview:
    route: str
    text: str
    subject: str = ''

class Bridge:
    def __init__(self, hub):
        self.hub = hub

    def require(self, capability, *modules):
        if not self.hub.enabled('Bridge') or not all(self.hub.enabled(n) for n in modules):
            raise PermissionError('Ative Bridge e os módulos envolvidos no Hub.')
        self.hub.permissions.require(capability)

    def records(self, source):
        if source not in SOURCE_GRANTS: raise ValueError('Fonte não suportada.')
        self.require(SOURCE_GRANTS[source], source)
        store = getattr(self.hub, source.lower()+'_store')
        return store.list() if store is not None else ()

    def run(self, route, text, source='Manual', source_language='pt', target_language='en'):
        if route not in ROUTES: raise ValueError('Fluxo não suportado.')
        self.require(BRIDGE_RUN, *ROUTES[route])
        if source != 'Manual':
            if source not in SOURCE_GRANTS: raise ValueError('Fonte não suportada.')
            self.require(SOURCE_GRANTS[source], source)
        if not isinstance(text,str) or not text.strip() or len(text)>20000 or '\0' in text:
            raise ValueError('Informe texto fictício de 1 a 20.000 caracteres.')
        if route == 'Expand → Text':
            from aeris.expand import ExpandStore
            from aeris.text import transform
            if self.hub.expand_store is None: self.hub.expand_store = ExpandStore()
            expanded = self.hub.expand_store.expand(text).text
            return Preview(route, transform(expanded, 'Remover espaços excedentes'))
        if route == 'Translate → Email':
            from aeris.translate import phrase_translate
            from aeris.email_draft import compose
            translated = phrase_translate(text, source_language, target_language)
            language = {'pt':'Português', 'en':'English', 'es':'Español'}[target_language]
            draft = compose(language, 'Formal', 'Atualização', '', '', translated, '')
            return Preview(route, draft.body, draft.subject)
        from aeris.text import transform
        return Preview(route, transform(text, 'Remover espaços excedentes'))

    def save_capture(self, preview, title):
        if preview.route != 'Text → Capture': raise ValueError('Fluxo não permite salvar anotação.')
        self.require(BRIDGE_RUN, 'Text', 'Capture')
        self.require(BRIDGE_SAVE, 'Capture')
        from aeris.content import CaptureStore
        if self.hub.capture_store is None:
            self.hub.capture_store = CaptureStore(self.hub.invalidate_search)
        item = self.hub.capture_store.save(title, preview.text)
        if self.hub.alive(self.hub.capture_window): self.hub.capture_window.refresh()
        return item
