# Aeris Documents — v0.6.0a1

Primeiro protótipo de File Intelligence. Módulo opcional, desativado por padrão, integrado a Hub, favoritos, Workspace e Spotlight. A permissão Documents → Ler arquivo é negada por padrão e vale somente na sessão. A escolha do arquivo e a confirmação precedem cada extração. Revogação, cancelamento, desativação e limpeza de sessão descartam a prévia; o cancelamento é cooperativo e não interrompe imediatamente leitura ou parse em andamento. Não há indexação de diretórios, acesso a serviços externos nem histórico permanente.

## Escopo

- TXT/MD/CSV: texto bruto, UTF-8 (com ou sem BOM) ou UTF-16 com BOM, até 1 MiB. Markdown não é renderizado e CSV não é interpretado como planilha.
- DOCX: pacote ZIP até 8 MiB, até 2.048 entradas (verificação após abrir o índice ZIP), XML principal até 1 MiB; somente compressão stored/deflate; sem extração para disco. Leitura parcial de parágrafos e texto do corpo, incluindo parágrafos de tabelas. Sem formatação, cabeçalhos, rodapés, notas, objetos, imagens, macros ou garantia de ordem visual/fidelidade. Não é validador de conformidade OOXML; pode incluir conteúdo oculto e revisões, não usar como sanitizador. Não resolve relações externas. XML com DTD/entidades explícitas recusado.
- Prévia limitada a 100 mil caracteres, contagens somente sobre a prévia, quebras de linha normalizadas e certos controles invisíveis substituídos por caractere de reposição. Nenhum botão de exportação/cópia; seleção manual de texto não é controlada pelo sistema de permissões.
- Arquivos regulares; usa a verificação de caminho do Verify (Windows: recusa UNC, unidades não fixas e reparse points conhecidos); checa identidade/tamanho/tempos antes e depois da leitura, sem garantir detecção de toda alteração ou corrida de sistema de arquivos. Não é sandbox, antivírus ou apagamento seguro.

## Validação

Linux: 150 testes unitários aprovados, 4 ignorados por exigirem Windows, 24 smoke tests gráficos aprovados em Xvfb. Os sete novos testes cobrem formatos, preservação de bytes, codificação, limites, controle invisível, XML inválido/DTD, cancelamento e migração 24→25. Smoke confirma ativação, permissão, prévia real de TXT, revogação, desativação e limpeza. Arquivos sintéticos; sem teste nativo Windows ou benchmark sob carga. Nenhuma nova dependência Python externa obrigatória.

## Próximos passos

PDF e OCR opcionais, mais formatos, testes com documentos variados, revisão de segurança e integração explícita com Text/Privacy, sem envio externo automático.
