# Aeris Flashcards — v0.9.0a3

Módulo opcional, local, sem dependências externas. Baralhos são agrupamentos por nome. Até 500 cartões na sessão, nome do baralho até 100 caracteres, pergunta até 1.000, resposta até 4.000. Pesquisa normalizada e filtro exato por baralho. Seleção de próximo cartão disponível por prazo e ID. A resposta só é revelada na aba de revisão após ação explícita; a aba de edição permite consultar todos os conteúdos.

## Agendamento experimental

Cartão novo disponível imediatamente. Após avaliação voluntária: difícil = 10 minutos; médio = máximo entre 1 dia e 2 vezes o intervalo anterior; fácil = máximo entre 3 dias e 3 vezes o intervalo anterior. Teto de 365 dias. Não é algoritmo validado cientificamente nem implementação de SM-2/FSRS. Prazos em UTC, apresentados no horário local; mudanças no relógio podem afetar disponibilidade. Não há alertas ou polling; pressione Atualizar ou Revisar próximo disponível. Cartão não vencido não aceita nova avaliação. Editar pergunta ou resposta reinicia o progresso; alterar apenas baralho mantém prazo e contagem.

## Privacidade e limitações

A memória da sessão preserva cartões quando a janela fecha, mas não após encerrar o Aeris. Desativar ou limpar a sessão descarta cartões e revisões mediante confirmação. Não há sincronização, importação, exportação, geração por IA, microfone ou integração de voz nesta versão. O agendamento de vários dias só se torna plenamente útil com persistência protegida, ainda pendente. Sem monitoramento de estudos. Favoritos e ativação ficam nas preferências não sensíveis (esquema 42).

## Testes

`python -m unittest tests.test_flashcards` e `python -m tests.smoke_flashcards` dentro de desktop. Relógio injetado nos testes de prazos; Windows nativo ainda não validado.


**Atualização da consolidação (v0.11.0a2):** registros confirmados podem ser salvos/restaurados manualmente por Privacy → Cópias protegidas. Rascunhos e alterações não copiadas continuam temporários. Consulte `protected-storage.md` para permissões, prazos, limitações e validação.
