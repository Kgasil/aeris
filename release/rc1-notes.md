# Project Aeris — Discreto e Eficiente.

**Primeira prévia pública · 1.0.0rc1 · 25/11/2026 · K&G Vision**

O Aeris reúne 50 ferramentas em protótipo para produtividade, estudos, trabalho, automação e segurança. A edição é gratuita, sem conta obrigatória ou anúncios. IA local, OCR e voz dependem de recursos opcionais.

## O que está disponível
- Código-fonte correspondente à compilação experimental aprovada, com os ajustes de teste e empacotamento incorporados.
- [Aeris Web Lab](https://kgasil.github.io/aeris/demo.html): seis demonstrações no navegador.
- [Instalador e versão portátil experimentais — artefato de CI](https://github.com/Kgasil/aeris/actions/runs/45730507059/artifacts/15076935274): disponibilidade temporária até 3 de dezembro de 2026, pode exigir login. Não são assets desta release.

## Evidências
395 testes unitários aprovados e quatro ignorados no Windows Server 2022; compilação, autoteste empacotado, instalação, reinstalação da mesma versão, desinstalação e preservação de dados fictícios aprovados. [Execução](https://github.com/Kgasil/aeris/actions/runs/45730507059) · [Hashes dos binários experimentais](https://github.com/Kgasil/aeris/blob/main/downloads/windows-preview-evidence.json).

## Antes de usar
Pré-release experimental, sem assinatura digital e sem certificação de Windows 10/11. Use dados fictícios. Não desative as proteções do Windows. Para executar o código, instale Python 3.12 ou 3.13 com Tcl/Tk, extraia o ZIP e execute `py -3 main.py` na pasta desktop. Não há liberação binária definitiva neste lançamento: revisão das condições de redistribuição dos componentes nativos, testes Windows 10/11, atualização entre versões, IA/voz/OCR reais e desempenho permanecem pendentes. Gratuidade não implica concessão de uma licença de código aberto; a licença do projeto deve ser definida pelo titular.

**English:** First public source preview; 50 desktop prototypes, 395 passing Windows Server 2022 unit tests, four skips, successful experimental installer lifecycle tests with dummy data. Unsigned CI binaries are temporary test artifacts, not release assets. No stable Windows 10/11 release or redistribution clearance is claimed.

[Site oficial / Website](https://kgasil.github.io/aeris/) · [Estado da versão / Release status](https://kgasil.github.io/aeris/release-status.html)
