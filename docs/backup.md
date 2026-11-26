# Aeris Backup — pré-alpha

Escopo Windows: DPAPI por usuário, backup manual, dados fictícios. Exporta aparência e blobs Vault/Bookmarks existentes, não descriptografa para gravar. A aparência não é secreta. Limite 90 MiB, campos fixos, integridade SHA-256 não autenticada. Importar apenas arquivos confiáveis. Restaurar um item exige autorização de sessão e confirmação na UI. As travas de arquivo existentes impedem substituir cofres abertos. O arquivo anterior é preservado em `.recovery-*.bin`; recuperação desses blobs é manual e deve ser validada antes de substituir dados. Não há recuperação de senha/conta, portabilidade entre PCs, histórico de sessão, permissões persistidas, agendamento ou nuvem. Cópias devem ser gerenciadas pelo usuário.

Testes Linux usam simulador não criptográfico apenas nos testes. Testes nativos de DPAPI e do Backup exigem Windows.
