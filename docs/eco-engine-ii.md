# Eco Engine II — v0.11.0a8

## Alterações

O Hub já utilizava importações tardias e stores inicializados quando necessários. Preservamos essa arquitetura e corrigimos retenção de objetos de janelas encerradas. `aeris/window_lifecycle.py` associa a instância ao evento Destroy, libera apenas a referência correspondente e não interfere nos stores ou em futuras instâncias. A central acompanha as 46 ferramentas opcionais, os painéis de Privacy, Permissions, Appearance, Quick Panel e Reminder Alert, além do Companion no Copilot. Spotlight conserva o ciclo anterior.

Callbacks Tcl de variáveis estáticas foram removidos no fechamento nas interfaces Editor (Capture/Snippets), Appearance, Bookmarks, Bridge, Clipboard, Companion, Compare, Convert, Email, Link, Routine, Search, Text, Translate e Verify. Calculator e Decision removem traces antes de substituir campos dinâmicos e ao fechar. Os demais callbacks e tarefas mantêm seu ciclo de vida próprio. Não se usa `gc.collect()` em produção, nem se força descarregamento de módulos Python, reinicialização de stores ou limpeza periódica da memória.

## Testes e benchmark

Linux/Xvfb, Python 3.13.5, três processos independentes por versão. A partir de desktop, `xvfb-run -a python -m tests.benchmark_lifecycle`. Para comparação, copie o script para a versão a7 ou execute o script com PYTHONPATH apontando para o desktop daquela versão. Cinco ciclos de 12 ferramentas e o Companion, total de 65 janelas por processo. Nenhum dado pessoal, inferência, rede ou microfone. Após fechar as janelas, chamar GC apenas no benchmark e medir referências fracas e RSS. Arquivos brutos `lifecycle-before-linux.json` e `lifecycle-after-linux.json`.

| Indicador | a7 | a8 |
| --- | ---: | ---: |
| Objetos retidos após GC (cada execução) | 61/65 | 0/65 |
| Referências a janelas fechadas no Hub (cada execução) | 12 | 0 |
| RSS após ciclos (média) | 111,39 MiB | 111,28 MiB |

Não há redução demonstrável de RSS; desalocação de objetos não significa retorno de páginas ao SO. Bibliotecas e alocadores permanecem em memória. O benchmark não representa carga com dados grandes, uso de IA, memória privada Windows ou consumo de energia. A coleta de objetos não é apagamento seguro. O benchmark e o smoke cobrem amostra de interfaces, não todas as combinações. Metas originais de memória e instalador continuam pendentes.

344 testes unitários aprovados, cinco ignorados por exigir Windows. 55 scripts gráficos aprovados, incluindo novo smoke de ciclo de vida, preservação de registro de Capture, reabertura, remoção de traces estáticos e dinâmicos. Não há validação nativa Windows, auditoria independente ou pacote instalável.
