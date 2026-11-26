# Aeris Polish — evidências

Branch desktop-experience; nenhum merge, lançamento ou atualização do instalador público.

## Mudanças

- Cores secundárias e de foco distintas para os dois temas.
- Navegação por teclado: Tab/Shift+Tab nos editores centrais, Ctrl+Enter para enviar, Ctrl+L para retornar à conversa quando o assistente estiver ocioso, Ctrl+F para catálogo e Ctrl+Shift+S para interromper atividade.
- Modo compacto abaixo de 930 px na janela principal: conversa ou painel de contexto, com retorno explícito; modo amplo mantém os dois painéis quando o contexto está aberto.
- Autoteste integrado inclui as duas disposições. Ainda não executado integralmente.

## Testes executados

Python 3.13.5, Tk 8.6, Linux com Xvfb.
Comando: xvfb-run -a python -m unittest discover -s tests -v
Escopo: cópias isoladas de aeris/theme.py, aeris/polish.py e tests/test_polish.py.
Resultado: 7 testes executados, 7 aprovados, 0 falhas, 0 erros, 0 ignorados. Cinco testes de cálculo/regras e dois de componentes Tk reais (consulta de estilos e troca de tema preservando texto).

Hashes Git conferidos com o repositório após os testes:
- aeris/theme.py: 3007cbe99dbdf5cee7b4f57bb80854eef99cff56
- aeris/polish.py: 57c241714509d29817def0c5d911f4cdc7f170aa
- tests/test_polish.py: 069ff38df7a38bf334deae75f2ecdf22b2bf2ca7

Contraste de texto secundário (ar/fundo de campo/painel):
- Claro: 5,85 / 6,45 / 5,32.
- Escuro: 9,05 / 10,09 / 6,90.
Todos os pares principais de texto testados atendem 4,5:1; foco testado atende 3:1. Isso não certifica acessibilidade integral, leitores de tela, DPI ou todas as janelas.

## Bloqueios

git ls-remote falhou por DNS: Could not resolve host: github.com. Regressão integral e autoteste da interface completa não foram executados aqui. Ainda são necessários testes reais de geometria, DPI, teclado, leitura de tela e dispositivos no Windows, além de revisão de dependências e pacote. Prévia conceitual não equivale a captura real.
