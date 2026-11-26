# Health — v0.5.0a5

Diagnóstico voluntário do próprio processo. Não enumera outros processos, não usa rede, não escreve relatórios automaticamente. Não precisa de nova permissão de acesso a dados: o clique explícito mede apenas o processo atual. O módulo vem desativado por padrão e o esquema 24 preserva as preferências existentes. Nenhuma coleta contínua. O callback único do Tk é cancelado ao limpar/fechar/desativar; os resultados permanecem na janela até nova medição ou limpeza. O fechamento da sessão também fecha a janela.

## Métricas

- CPU: diferença de `time.process_time()` dividida pelo intervalo de `time.monotonic()`, multiplicada por 100. 100% representa um núcleo lógico; pode superar 100%. Não é o mesmo percentual de CPU total do Gerenciador de Tarefas.
- Memória: working set atual no Windows via `GetProcessMemoryInfo` (ctypes); RSS aproximado via `/proc/self/statm` no Linux. Inclui páginas compartilhadas e não equivale a memória privada. Falha/ambiente incompatível é apresentado como indisponível, nunca zero inventado.
- Contagem de módulos opcionais ativos ao final, não de módulos residentes ou processos.

## Diagnóstico preliminar reproduzível

Na pasta desktop: `python -S -m tests.benchmark_health` (Windows: `py -3 -S -m tests.benchmark_health`). No Linux com Xvfb: `xvfb-run -a python -S -m tests.benchmark_health`. Preferências temporárias; três amostras de dois segundos com Hub padrão e três com Health aberto, sem atividade humana. Python -S evita inicialização automática de site e pacotes externos. `health-baseline-linux.json` contém o resultado real da execução Linux/Xvfb com Python 3.13.5. O teste gráfico padrão, com infraestrutura adicional e laço de atualização manual, observou ~112 MiB; essa condição não é comparável à execução limpa. Não é avaliação estatística nem certificação de desempenho. A meta de 30 MB da interface é apenas referência; 26,55 MiB equivale a aproximadamente 27,84 MB nesta amostra Linux. Não existe processo de núcleo separado mensurável nesta arquitetura; meta de 10 MB ainda não avaliada. Não mede filhos (Argos/PowerShell), atalhos, instalador, inicialização ou pressão de memória sob carga.

## Validação

143 unitários aprovados, 4 específicos Windows ignorados, 23 scripts gráficos aprovados. O teste Windows nativo do working set foi adicionado, mas não executado. Ainda falta validar Windows 10/11 x64, medir com e sem módulos, filhos, períodos longos e latência. Não publicar como versão pronta para produção.
