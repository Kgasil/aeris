# Aeris Accessibility — v0.9.0a4

Leitor local de textos inseridos voluntariamente, sem acesso a arquivos, outros aplicativos, captura de tela ou rede. Não pretende substituir tecnologias assistivas do sistema operacional.

## Uso

Ative Accessibility no catálogo. Digite ou cole texto fictício e pressione Preparar leitura (Ctrl+Enter). Ajuste a fonte de 12 a 30 pontos, a paleta Natural, Escuro ou Alto contraste (branco sobre preto, destaque amarelo), espaçamento e guia por linha. Alt+seta para cima/baixo move o guia entre linhas lógicas delimitadas por quebras de linha, não entre linhas visuais resultantes da quebra automática. A prévia é somente leitura. Tab e Shift+Tab percorrem controles nos campos de texto; Escape solicita fechamento. Restaurar padrões não apaga o conteúdo. Limpar e fechar com texto solicitam confirmação. A prévia permanece independente do tema geral do Hub.

## Limites e privacidade

A preparação valida até 20.000 caracteres e rejeita NUL, normalizando CRLF/CR para LF. Uma entrada inválida preserva a prévia anterior e informa isso. O limite é de processamento da prévia, não de inserção no editor. A entrada e prévia ficam apenas em memória, descartadas ao fechar, limpar a sessão ou desativar o módulo. Não há armazenamento protegido de texto nem apagamento seguro de memória. Ativação e favoritos são preferências não sensíveis, esquema 43. A colagem e seleção/cópia nativas do editor são ações explícitas do usuário; o sistema pode manter histórico de clipboard. Nenhuma leitura automática do clipboard ou serviço auxiliar foi acrescentado.

## Validação

Seis testes unitários específicos, incluindo migração do esquema 42, limites, normalização, guia e limpeza. Smoke gráfico com texto real, mudança de contraste, espaçamento, foco, proteção contra descarte e limpeza pela central de privacidade. Linux: 264 testes unitários aprovados (4 ignorados por depender de Windows), 42 scripts gráficos aprovados. Sem certificação WCAG, validação com leitores de tela, testes nativos Windows, leitura por voz, ampliação global ou persistência das opções de leitura. Esses recursos dependem de trabalho posterior e testes com usuários.
