# GRAAL Security & Trust 1.1 — Etapa 05 / Aeris Extension
Data: 2026-11-26. Escopo: os dois ZIPs originais 1.0.0. Sem alteração de código de runtime, interface, permissões ou distribuição.
## Evidências dos originais
Snapshot 35fa603bf110f2d23d98012b06547d33c9c7a2de, backup-graal-security-trust-1.1-2026-11-26.
| Pacote | Bytes | Git blob | SHA-256 publicado |
|---|---:|---|---|
| install | 31883 | e49d7a8990b8ad17386f1d0afcd2e2427b49778c | e77e6e8596c14e54f22303e7a5d368356c19eaa79df8c8597752790755d9a0d9 |
| completa | 53997 | ce14fbf5351d32ed191fa4177849897527ccbc5b | d0f064c1b73c46465171cc1fb208b530ed66573e054c2ca211b216547bbb3c00 |
Main e backup: blobs idênticos. Inspeção dos bytes obtidos do GitHub: 15 e 23 entradas, respectivamente; descompressão, CRC-32, cabeçalhos e estrutura aprovados; 15/15 arquivos de runtime idênticos entre ambos. Não há executáveis nativos. SHA-256 publicado será recalculado na nova CI. ZIP completo é a fonte de referência; não há árvore de runtime avulsa na raiz.
## Revisão dos sete módulos JS e recursos
- app.js: 16 ferramentas; manipulação de DOM por textContent/value; captura de seleção, consulta de aba e preenchimento após ação explícita; sem monitoramento em segundo plano. Cópia explícita. Operações de sessão sincronizadas com locks e evento de limpeza.
- automation.js: expansão local e Autofill com campo único vazio, HTTPS, prévia e confirmação, prazo, revalidação do documento/campo e bloqueio heurístico de campos sensíveis. A página pode observar valores inseridos; usar dados fictícios.
- context.js: análise local de leitura e referências, remove credenciais por rejeição, query e fragmentos; caminho opcional pode conter informação privada.
- core.js e intelligent-text.js: cálculos, conversões, análise local de URL (não visita o endereço), frases e revisão textual determinística. Validação de tamanho, prévia e desfazer; sem execução dinâmica do texto.
- session.js: normalização e limites para registros temporários, reset e Focus. chrome.storage.session não é armazenamento criptografado; limpar sessão não apaga clipboard, página ou servidor.
- connect.js: único endpoint programado http://127.0.0.1:11434/api/chat, POST após consentimento e concessão opcional do navegador. Sem cookies, redirecionamentos, histórico automático ou ferramentas; limite de 4.000 caracteres, 256 KiB de resposta, timeout de 45 s e cancelamento. Resposta de modelo tratada como texto. Modelo/servidor local pode reter ou encaminhar dados; negar nomes com cloud não garante execução exclusivamente local do servidor. Cancelamento do cliente não garante interrupção do processamento no servidor. Revogar host permission separadamente.
- HTML, CSS e SVG locais, sem recursos de rede externos observados; quatro ícones PNG. Manifest V3 com activeTab, scripting e storage; host opcional http://127.0.0.1/* (permissão de host não limita porta, mas CSP e código limitam conexão programada à porta 11434). Sem host permanente, background, content_scripts, native messaging ou externally_connectable. CSP restritiva.
- package.json sem dependências npm declaradas; módulos locais e APIs do navegador. Ollama/modelo instalado separadamente não faz parte do pacote e não foi auditado. pack.py usa allowlist explícita; não foi executado para preservar os originais.
## Testes e limites
Nova CI somente para verificação dos ZIPs e testes Node existentes (50 casos esperados) em checkout temporário, sem instalar dependências npm, sem recompilar ou publicar o produto. Testes de navegador incluídos no ZIP exigem ambiente específico; não executados nesta fase, inclusive porque os scripts existentes usam opções de sandbox de Chromium que não serão reproduzidas aqui. Não há teste real Ollama, instalação Chrome/Edge/Opera, revisão completa da cadeia CI, assinatura digital ou nova análise Defender. Auditoria estática não equivale a aprovação de segurança. Nenhum custo contratado.

## Registro de execução
[CI 45878981054](https://github.com/Kgasil/aeris/actions/runs/45878981054), commit `6290ca6aef5af2129829bf1047f5a429e29b931a`: disparada, ainda na fila na última consulta. Nenhum novo resultado Node ou SHA-256 da CI confirmado. A comparação main/backup mostrou exclusivamente os três arquivos novos de validação/documentação. O resultado histórico de 50/50 em release/extension-1.0.0-notes.md não substitui esta execução.

## Confirmação CI na etapa 06
A [execução 45878981054](https://github.com/Kgasil/aeris/actions/runs/45878981054) concluiu com sucesso: recálculo SHA-256 e verificação dos dois ZIPs, sintaxe dos módulos e suíte Node original aprovados. Runner Linux; não é scan Defender, teste Ollama real ou instalação nativa.
