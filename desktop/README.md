# Aeris Desktop — Naturalmente bom.

Pré-alpha 0.1.0a2 · by K&G Vision. Hub e Capture em protótipo, 48 ferramentas planejadas.
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

O filtro interno do catálogo não é Aeris Search. Selecione Capture no catálogo, ative-o e abra a ferramenta. Crie, edite e exclua notas fictícias. As notas ficam apenas em memória e desaparecem ao encerrar ou desativar o módulo. A preferência de ativação (booleano) fica em %LOCALAPPDATA%/Aeris/settings.json no Windows. Não há instalação de módulos, serviços residentes, rede, captura automática ou persistência de dados pessoais.
Os testes da versão a1 foram executados em Linux. A versão a2 inclui testes adicionais ainda não executados; Windows, acessibilidade e desempenho requerem validação.

## Aprender fazendo

Leia main.py, aeris/registry.py e aeris/hub.py nessa ordem. Observe a separação entre catálogo declarativo, regras de filtro e eventos da interface. Experimente escrever um teste para dois termos de pesquisa.

Consulte ../docs/architecture.md para as decisões e os próximos passos.
