# Aeris Privacy — v0.5.0a1

## Escopo
Central de segurança sempre acessível (sem flag adicional). Reutiliza Permissions, estado de cofres e limpeza de sessão do Hub. Não é sandbox do sistema operacional, DLP, antivírus ou auditoria independente.

## Inventário
- Somente presença/tipo dos arquivos conhecidos settings.json, vault.bin, bookmarks.bin, autofill.bin, sem abrir conteúdo. Arquivo presente não prova integridade ou criptografia válida.
- Contagem dos stores temporários Capture, Snippets, Clipboard, Expand, Routine e Workspace; não inclui todos os rascunhos abertos.
- Estado das permissões de sessão e dos cofres Vault, Bookmarks e Autofill. Atualização manual e quando permissões mudam. Sem coleta contínua.
- Não enumera backups externos, cópias de recuperação, cache de modelos ou arquivos desconhecidos.

## Ações
Revogar permissões não apaga dados já copiados. Bloqueio de cofres pede confirmação e descarta rascunhos não salvos. Limpeza da sessão revoga permissões, interrompe ferramentas de voz/tradução abertas, fecha ferramentas temporárias, limpa consulta do Hub e prévias de Privacy, preservando dados protegidos e clipboard do sistema. Não garante remoção de resíduos em RAM, swap, históricos ou cópias externas. Ocultar Spotlight é ação independente.

## Mascaramento
Operação manual com prévia; entrada limitada a 20.000 caracteres. Padrões aproximados para e-mail, CPF e CNPJ numéricos pontuados e telefone brasileiro com DDD entre parênteses e hífen. Substituição por marcador de categoria; sem validação de identidade ou dígitos verificadores. Pode haver falsos positivos e negativos, incluindo formatos não reconhecidos, nomes, endereços, segredos e identificadores. Não é anonimização garantida. Texto original e prévia permanecem em memória até descarte. Seleção/cópia normal do sistema pode deixar resíduos no clipboard. Nenhum monitoramento de digitação externa.

## Validação
117 testes unitários executáveis, 19 smoke tests gráficos em Linux/Xvfb; 3 testes específicos Windows ignorados. Testes usam dados fictícios e simuladores quando necessário. Compatibilidade Windows real, desempenho e auditoria externa pendentes. Esquema de preferências permanece 20: Privacy não precisa ser ativado. Não usar dados reais nesta pré-alpha.
