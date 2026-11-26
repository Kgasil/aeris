# Final Validation II — Aeris 1.1.0rc1

## CI

Consulta inicial: os runs 45881480028 e 45881480228 estavam enfileirados; não havia nova falha concluída após a correção do Dashboard. A última falha disponível continua sendo a do run 45876938170, 504 testes, 499 aprovados, 1 falha, 4 ignorados (commit histórico). Não extrapolar esse resultado para o candidato atual. O commit 6b2252774d1b0d63482daf5d2516fb7fc6d9d6c5 adiciona o job candidate-build; runs 45881672318 e 45881672237 estavam enfileirados na consulta seguinte. Nenhum resultado de build concluído. 

## Compilação candidata

O job depende da aprovação da matriz de regressão Windows/Linux. Executa em Windows x64 com Python 3.14.10 e utiliza distribution/build.ps1. Se ISCC estiver presente, o script exige assinatura válida e licença antes de compilar; se ausente, tenta apenas o portátil e identifica a modalidade. Não instala Inno Setup automaticamente. Registra commit, modalidade, logs, hashes SHA-256, inventário, dependências e dados de build. Somente evidências são enviadas como artefato temporário da CI, não EXE ou ZIP. Não há etapa de publicação ou alteração do release-gate. Nenhum novo binário foi produzido ou verificado neste turno.

## Execução local

Linux, Python 3.13.5, Xvfb. Reuni cópias locais da lógica de voz (5), visão (4), vínculo visual (5), prontidão (7), catálogo (3), papéis de tema (3), polish (7), gate (3), cabeçalho PE (4) e Dashboard (4). Executei `xvfb-run -a python -m unittest discover -s tests -q`. Resultado: 45/45, 0 falhas, 0 erros, 0 ignorados (0,152 s na segunda execução). Dados fictícios; testes de componentes Tk com display virtual. 20 dos 22 arquivos de código/testes/registro utilizados correspondem aos blobs do repositório na árvore do commit 6b225277: exceto o recorte de release_check.py contendo pe_installer e o teste local test_dashboard_draw.py, que usa um recorte do método draw. Logo, 37 casos testam módulos/registro exatos do repositório e 8 testam recortes. Não equivale à regressão integral. A função pending_checks, com o registro real e versão 1.1.0rc1, retornou todos os nove critérios pendentes.

## Bloqueios e decisão

git ls-remote falha por DNS. Ambiente local Linux, sem PowerShell/Windows. Build do instalador, testes reais dos dispositivos, VMs limpas, assinatura, licenças e análise antimalware permanecem pendentes. Não modificar ou publicar a versão pública. O resultado de CI deve ser conferido no SHA correspondente, sem usar testes de commits antigos como aprovação do candidato. Aguardar o resultado da CI antes de novas alterações desnecessárias que cancelem os runs.
