# Etapa 11 — Desempenho e acessibilidade
Escopo: testes em Windows Server 2022 descartável; RC2 portátil exato e benchmarks separados do código-fonte histórico, não certificação do Windows cliente.

## Metas provisórias definidas antes da execução
- Três inicializações de processo do RC2: janela principal visível/respondendo em até 10 s; não equivalem a boot frio do sistema.
- Cinco amostras de memória em repouso por execução: working set de até 200 MiB; CPU média de até 5% de um núcleo; encerramento normal em até 5 s.
- Benchmarks Health e Eco: seis amostras de 2 s cada, CPU de até 5% de um núcleo, RSS até 200 MiB.
- Ciclo de vida: cinco ciclos com 12 ferramentas e Companion, 65 janelas no total, zero objetos ou referências de janelas fechadas retidos, crescimento RSS de até 64 MiB. Esses limites são metas de CI conservadoras, não garantias para todos os computadores.
- Acessibilidade: seis testes unitários e smoke real do leitor (alto contraste interno, tamanho, guia, navegação e limpeza de sessão). Não equivale a conformidade WCAG ou acessibilidade geral.

O workflow baixa o RC2 exato do artefato 15132831716, verifica digest externo, ZIP interno e 91 hashes; extrai em diretório novo, mede somente o processo filho do teste, usa LOCALAPPDATA isolado, não instala ou publica nada. Não relançar em máquina de produção sem revisão do artefato. Benchmark de fonte usa implementação histórica verificada, não é o mesmo binário. Falhas não são mascaradas.

## Validação manual cliente pendente
Em Windows 10/11 limpos, conta comum, após revisão de segurança, registrar hardware e build, repetir inicialização fria após reinicialização, uso de CPU/RAM, abertura de módulos e resposta durante trabalho, encerramento; testar teclado real, ordem Tab/Shift+Tab, foco visível, ausência de armadilhas, Enter/Escape, Narrator, alto contraste do SO, escala 100/150/200%, leitura de mensagens, zoom, redimensionamento e acessibilidade de controles nas principais ferramentas. Registrar defeitos por tela e resultado PASS/FAIL/NOT_TESTED. Não declarar compatibilidade universal, nem substituir os testes de cliente por CI.

Resultados ainda pendentes. Não há autorização de publicação.
