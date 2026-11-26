# Validação local a8

Ambiente: Linux, Python 3.13.5, Tcl/Tk, Xvfb.

- `python -m unittest discover -v`: 28/28 aprovados.
- `xvfb-run -a python -m tests.smoke_integration`: aprovado.
- `xvfb-run -a python -m tests.smoke_spotlight_isolated`: aprovado.
- `xvfb-run -a python -m tests.smoke_refinement`: aprovado.

O teste gráfico adicional verifica tema claro/escuro, persistência das preferências, filtragem de favoritos, confirmação/cancelamento da limpeza, manutenção do clipboard e das flags de ativação, ausência dos textos fictícios no JSON de preferências e ocultação do ícone. Confirmações simuladas, dados fictícios. Os testes não demonstram segurança contra vazamento de memória, nem compatibilidade Windows ou desempenho.
