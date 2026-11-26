# Security & Quality I — v0.12.0a1

## Escopo
Revisão focal de entradas nas fronteiras de confiança, não auditoria independente nem certificação. Mantém os 50 módulos e os formatos de dados existentes.

| Achado | Mitigação |
|---|---|
| JSON com chaves duplicadas, NaN, Infinity, números que transbordam para infinito | Parser compartilhado, rejeição explícita |
| JSON muito aninhado ou UTF-8 inválido | Limite de bytes, tratamento de RecursionError, validação de profundidade máxima 32 após parsing |
| Preferências com leitura ilimitada | Limite de 64 KiB; estado seguro com aviso quando inválidas |
| Esquema de Vault aceitava booleano como inteiro | Campos exatos e tipo inteiro estrito |
| Leitura de arquivo especial ou link final | lstat, arquivo regular, flags de abertura quando disponíveis, fstat e comparação de metadados após leitura |
| Backup com Base64 acima do limite por item | Checagem antes da decodificação, hash e limites existentes mantidos |
| Respostas ambíguas do endpoint Ollama local | Parser compartilhado; conexão fechada mesmo em falha |

## Verificação
`python -m unittest discover -q`: 376 executados, 371 aprovados, 5 ignorados por Windows. Nove novos testes, incluindo FIFO POSIX, links simbólicos, limites, números não finitos, JSON ambíguo e preservação de arquivo inválido. 58 scripts gráficos em Linux/Xvfb, todos com saída 0. Backend criptográfico e respostas de IA simulados. Nenhum teste nativo Windows executado.

## Limites e próximos passos
As verificações de caminho e metadados reduzem riscos de leitura de arquivos especiais e mudanças concorrentes, mas não constituem sandbox e não eliminam todas as corridas, caminhos intermediários no POSIX ou ataques de processos com a mesma identidade. O parser carrega JSON dentro do limite antes de validar profundidade; o limite máximo global do backup continua 170 MiB. Não garante segurança de arquivos ou modelos externos. DPAPI, voz e compatibilidade nativa precisam de validação real. Revisão de permissões, encerramento de workers, escrita em arquivos e falhas concorrentes na próxima entrega. O instalador ainda não foi construído.

## Security & Quality II — v0.12.0a2

- Uma trava por Hub serializa solicitações do Companion (chat, sugestão, voz e ditado) e a revisão contextual do Text. A trava é liberada no retorno do worker, inclusive após falha. Fechar janela, limpar sessão ou revogar autorização não libera prematuramente a trava. Resultados são enviados à fila da janela original após liberar a trava, sem acesso ao Tk pelo worker. Não inicia captura se a trava estiver ocupada. Se a thread falhar ao iniciar, a operação não fica marcada como ocupada e o conteúdo original permanece; processo de voz já iniciado é encerrado quando possível.
- JSON interno da revisão e saída de ditado usam parser estrito com limite de 32 KiB, rejeitando duplicatas e entradas inválidas.
- Encerramento do Hub inclui rascunhos do Text e conteúdo ou operação ativa do Companion na confirmação de descarte.
- Testes: 380 unitários executados (375 aprovados, 5 ignorados por Windows), 59 scripts gráficos aprovados em Linux/Xvfb. Quatro novos testes unitários e um novo cenário gráfico com worker bloqueado, janela reaberta, falha de inicialização e confirmação de encerramento.

Limitações: o bloqueio é por instância do Hub e não limita outros processos, o servidor Ollama ou os módulos Voice/Translate independentes. Descartar resultado não cancela necessariamente a inferência HTTP já enviada. O timeout HTTP é de socket, não um prazo absoluto de parede; a operação permanece bloqueada até retornar. Voz e criptografia nativas continuam sem validação real; não é auditoria completa nem garantia contra processos locais maliciosos. Instalador e verificação de distribuição permanecem pendentes.
