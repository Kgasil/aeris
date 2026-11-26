# Eco Engine I — v0.11.0a7

## Alteração

A janela Companion consultava a fila de resultados a cada 100 ms, inclusive em repouso. Agora a consulta é agendada somente enquanto existe uma operação pendente; o callback é removido quando a janela é destruída. Uma operação cancelada pode permanecer ocupada até o worker terminar, mas seu resultado é descartado. Não há mudança no comportamento das permissões nem no protocolo Ollama. Não há modelo carregado automaticamente.

## Reprodução

Em Linux com Tk/Xvfb, a partir de desktop: `xvfb-run -a python -m tests.benchmark_eco`. Em Windows: `py -3 -m tests.benchmark_eco` (ainda não executado). O benchmark usa pasta temporária, não usa registros reais, microfone, rede ou inferência. Para comparar com a a6, copie apenas o script benchmark_eco.py para a pasta tests daquela versão e execute nas mesmas condições.

## Resultados preliminares

Python 3.13.5, Linux/Xvfb, processos separados, três janelas de aproximadamente 2 segundos por condição. Dados brutos: `eco-before-linux.json` e `eco-after-linux.json`. CPU média de um núcleo com Hub + Copilot + Companion ociosos: 0,347% → 0,017%; callbacks: 20 → 0 por amostra. RSS permanece aproximadamente 110 MiB nesse ambiente Python, e a pequena diferença entre processos não demonstra economia de memória atribuível à mudança. Não houve medição de inferência, bateria, atalhos globais ou instalador. Os resultados não são garantia de desempenho Windows; as metas originais permanecem experimentais.

## Validação e pendências

344 testes unitários aprovados (5 ignorados por Windows), 54 smoke scripts gráficos aprovados. Novo smoke_eco verifica repouso sem callback, operação pendente, revogação, descarte de resposta atrasada e destruição da janela. Próximo: medir carregamento de módulos e memória em execução limpa, investigar oportunidades de carregamento tardio e validar recursos no Windows.
