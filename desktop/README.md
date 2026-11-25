# Aeris Desktop — Naturalmente bom.

Pré-alpha 0.1.0a1 · by K&G Vision. Hub parcial, 49 ferramentas planejadas.
Não é uma versão de distribuição.

## Windows

Instale Python 3.12 ou 3.13 com Tcl/Tk. No PowerShell, dentro de desktop:

    py -3 --version
    py -3 -m tkinter
    py -3 main.py

Feche a janela de verificação do Tkinter antes de iniciar o Hub.
Sem dependências externas do Python.

## Testes

    py -3 -m unittest discover -v
    py -3 -m tests.smoke_gui

O filtro interno do catálogo não é Aeris Search. Não há instalação ou ativação de módulos, serviços residentes, rede, captura automática ou persistência de dados pessoais.
Os testes do protótipo foram executados em Linux com display virtual; Windows, acessibilidade e desempenho ainda requerem validação.

## Aprender fazendo

Leia main.py, aeris/registry.py e aeris/hub.py nessa ordem. Observe a separação entre catálogo declarativo, regras de filtro e eventos da interface. Experimente escrever um teste para dois termos de pesquisa.

Consulte ../docs/architecture.md para as decisões e os próximos passos.
