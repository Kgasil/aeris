"""Explicit, session-only application permissions. Not an OS sandbox."""
SEARCH_CAPTURE = 'search.capture'
SEARCH_SNIPPETS = 'search.snippets'
COPY_SNIPPETS = 'snippets.clipboard.write'
READ_CLIPBOARD = 'clipboard.read'
WRITE_CLIPBOARD = 'clipboard.write'
OPEN_BOOKMARK = 'bookmarks.browser.open'
CREATE_BACKUP = 'backup.create'
RESTORE_BACKUP = 'backup.restore'
COPY_TRANSLATION = 'translate.clipboard.write'
PLAY_VOICE = 'voice.audio.play'
COPY_TEXT = 'text.clipboard.write'
TEXT_AI = 'text.ai.review'
COPY_EMAIL = 'email.clipboard.write'
PLAY_PRONOUNCE = 'pronounce.audio.play'
COPY_AUTOFILL = 'autofill.clipboard.write'
COPY_EXPAND = 'expand.clipboard.write'
BRIDGE_CAPTURE = 'bridge.capture.read'
BRIDGE_SNIPPETS = 'bridge.snippets.read'
BRIDGE_RUN = 'bridge.run'
BRIDGE_SAVE = 'bridge.capture.write'
BRIDGE_COPY = 'bridge.clipboard.write'
BRIDGE_GRANTS = (BRIDGE_CAPTURE, BRIDGE_SNIPPETS, BRIDGE_RUN, BRIDGE_SAVE, BRIDGE_COPY)
ROUTINE_RUN = 'routine.run'
ROUTINE_COPY = 'routine.clipboard.write'
ROUTINE_GRANTS = (ROUTINE_RUN, ROUTINE_COPY)
WORKSPACE_OPEN = 'workspace.browser.open'
METADATA_READ = 'metadata.file.read'
VERIFY_READ = 'verify.file.read'
DOCUMENTS_READ = 'documents.file.read'
DROP_ADD = 'drop.files.add'
DROP_COPY = 'drop.paths.copy'
ORGANIZER_SCAN = 'organizer.folder.scan'
COMPARE_READ = 'compare.files.read'
LENS_READ = 'lens.image.read'
DATA_READ = 'data.csv.read'
DASHBOARD_READ = 'dashboard.csv.read'
REPORT_READ = 'report.csv.read'
REPORT_COPY = 'report.clipboard.write'
COPILOT_RUN = 'copilot.run'
CONTEXT_PREVIEW = 'context.preview'
INTEGRATION_RUN = 'integration.run'
MEETING_COPY = 'meeting.clipboard.write'
STORAGE_SAVE = 'storage.save'
STORAGE_AUTO = 'storage.auto'
STORAGE_LOAD = 'storage.load'
STORAGE_DELETE = 'storage.delete'
COMPANION_CHAT = 'companion.chat'
COMPANION_MIC = 'companion.mic'
COMPANION_SPEAK = 'companion.speak'
COMPANION_SCREEN = 'companion.screen'
CAPABILITIES = {
    COMPANION_SCREEN: ('Assistente → Tela', 'Capturar uma imagem da tela principal após ação explícita; enviar a imagem revisada ao modelo local de visão somente mediante confirmação separada.'),
    INTEGRATION_RUN: ('Integrações entre ferramentas', 'Transferir registros salvos entre Meeting, Checklist, Reminder, Learn, Flashcards e Research após prévia e confirmação.'),
    COMPANION_CHAT: ('Companion → IA local', 'Enviar mensagens e histórico da conversa ou uma solicitação isolada de sugestão de comando ao servidor Ollama local.'),
    COMPANION_MIC: ('Companion → Microfone', 'Ditado explícito e temporário pelo Windows.'),
    COMPANION_SPEAK: ('Companion → Voz', 'Ler respostas com voz masculina local; leitura automática opcional na janela.'),
    STORAGE_AUTO: ('Storage → Automático', 'Autorizar salvamento periódico apenas nos módulos selecionados nesta sessão.'),
    STORAGE_SAVE: ('Storage → Salvar', 'Gravar cópia protegida dos registros confirmados.'),
    STORAGE_LOAD: ('Storage → Restaurar', 'Substituir os registros da sessão por uma cópia protegida.'),
    STORAGE_DELETE: ('Storage → Excluir', 'Excluir uma cópia protegida do disco após confirmação.'),
    MEETING_COPY: ('Meeting → Clipboard', 'Copiar ata salva após revisão e confirmação.'),
    CONTEXT_PREVIEW: ('Context → Prévia', 'Montar prévia local de registros selecionados individualmente.'),
    COPILOT_RUN: ('Copilot → Executar', 'Executar comandos locais permitidos após prévia e confirmação individual.'),
    REPORT_READ: ('Report → Ler CSV', 'Ler CSV selecionado e confirmado para gerar relatório local.'),
    REPORT_COPY: ('Report → Clipboard', 'Copiar relatório revisado mediante confirmação.'),
    DASHBOARD_READ: ('Dashboard → Ler CSV', 'Ler CSV selecionado e confirmado para agregações locais.'),
    DATA_READ: ('Data → Ler CSV', 'Analisar arquivo CSV local selecionado e confirmado.'),
    LENS_READ: ('Lens → Ler imagem', 'Reconhecer texto de imagem selecionada e confirmada com OCR local.'),
    COMPARE_READ: ('Compare → Ler arquivos', 'Extrair texto de dois arquivos selecionados e confirmados para comparação.'),
    DROP_ADD: ('Drop → Adicionar', 'Consultar nomes e tamanhos dos arquivos locais selecionados e confirmados.'),
    DROP_COPY: ('Drop → Clipboard', 'Copiar caminhos selecionados mediante confirmação; não copia o conteúdo.'),
    ORGANIZER_SCAN: ('Organizer → Listar pasta', 'Listar metadados de arquivos de uma pasta selecionada e confirmada.'),
    DOCUMENTS_READ: ('Documents → Ler arquivo', 'Extrair texto do arquivo selecionado e confirmado.'),
    METADATA_READ: ('Metadata → Ler arquivo', 'Inspecionar metadados do arquivo selecionado e confirmado.'),
    VERIFY_READ: ('Verify → Ler arquivo', 'Calcular hash do arquivo explicitamente selecionado e confirmado.'),
    WORKSPACE_OPEN: ('Workspace → Navegador', 'Abrir um link salvo por vez, mediante confirmação.'),
    ROUTINE_RUN: ('Routine → Executar', 'Executar sequências explícitas de fluxos Bridge.'),
    ROUTINE_COPY: ('Routine → Clipboard', 'Copiar prévia mediante confirmação.'),
    BRIDGE_CAPTURE: ('Bridge → Capture (ler)', 'Importar anotação explicitamente selecionada.'),
    BRIDGE_SNIPPETS: ('Bridge → Snippets (ler)', 'Importar snippet explicitamente selecionado.'),
    BRIDGE_RUN: ('Bridge → Executar', 'Executar fluxos locais com módulos ativos.'),
    BRIDGE_SAVE: ('Bridge → Capture (salvar)', 'Criar anotação após revisão e confirmação.'),
    BRIDGE_COPY: ('Bridge → Clipboard', 'Copiar resultado mediante confirmação.'),
    COPY_EXPAND: ('Expand → Clipboard', 'Copiar a prévia revisada mediante confirmação.'),
    COPY_AUTOFILL: ('Autofill → Clipboard', 'Copiar um campo revisado mediante confirmação.'),
    PLAY_PRONOUNCE: ('Pronounce → Áudio', 'Consultar vozes por idioma e reproduzir exercícios por ação explícita.'),
    COPY_EMAIL: ('Email → Clipboard', 'Copiar assunto ou mensagem mediante confirmação.'),
    TEXT_AI: ('Text → Revisão por IA local', 'Enviar apenas o texto do editor confirmado ao Ollama local, sem histórico ou arquivos.'),
    COPY_TEXT: ('Text → Clipboard', 'Copiar resultado mediante confirmação.'),
    PLAY_VOICE: ('Voice → Áudio', 'Consultar vozes locais e ler texto somente por ação explícita.'),
    COPY_TRANSLATION: ('Translate → Clipboard', 'Copiar tradução mediante confirmação.'),
    CREATE_BACKUP: ('Backup → Criar', 'Exportar arquivos protegidos e aparência local.'),
    RESTORE_BACKUP: ('Backup → Restaurar', 'Restaurar um item mediante confirmação explícita.'),
    OPEN_BOOKMARK: ('Bookmarks → Navegador', 'Abrir link salvo mediante confirmação explícita.'),
    READ_CLIPBOARD: ('Clipboard → Ler', 'Capturar texto atual apenas por ação explícita.'),
    WRITE_CLIPBOARD: ('Clipboard → Escrever', 'Copiar um item salvo, mediante confirmação.'),
    SEARCH_CAPTURE: ('Search → Capture', 'Pesquisar anotações salvas na sessão.'),
    SEARCH_SNIPPETS: ('Search → Snippets', 'Pesquisar textos reutilizáveis salvos na sessão.'),
    COPY_SNIPPETS: ('Snippets → Clipboard', 'Usar o botão de cópia do Aeris. Cada cópia ainda exige confirmação.'),
}

class Permissions:
    def __init__(self, on_change=None):
        self._grants = set()
        self._revision = 0
        self._on_change = on_change or (lambda: None)

    @property
    def revision(self):
        return self._revision

    def allowed(self, capability):
        return capability in CAPABILITIES and capability in self._grants

    def set(self, capability, granted):
        if capability not in CAPABILITIES or type(granted) is not bool:
            raise ValueError('Permissão inválida')
        if self.allowed(capability) == granted:
            return
        if granted:
            self._grants.add(capability)
        else:
            self._grants.discard(capability)
        self._revision += 1
        self._on_change()

    def revoke_all(self):
        # Even an empty revocation cancels outstanding confirmation dialogs.
        self._revision += 1
        if self._grants:
            self._grants.clear()
            self._on_change()

    def require(self, capability):
        if not self.allowed(capability):
            raise PermissionError('Permissão não concedida nesta sessão.')
