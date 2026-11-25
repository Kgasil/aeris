# Aeris Desktop — Naturalmente bom.

Pré-alpha 0.1.0a4 · by K&G Vision. Hub, Capture e Snippets em protótipo, 47 ferramentas planejadas.
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
Os testes da versão a1 foram executados em Linux. As versões a2 a a4 incluem testes adicionais ainda não executados; Windows, acessibilidade e desempenho requerem validação.

## Aprender fazendo

Leia main.py, aeris/registry.py e aeris/hub.py nessa ordem. Observe a separação entre catálogo declarativo, regras de filtro e eventos da interface. Experimente escrever um teste para dois termos de pesquisa.

Consulte ../docs/architecture.md para as decisões e os próximos passos.

## Aparência e acesso rápido (a3)

No Hub, abra Configurações para editar posição relativa ao Hub, tamanho inicial do painel,
opacidade (quando suportada), tamanho previsto do ícone e ativação do acesso rápido.
Salve ou restaure os padrões. A prévia não é um overlay do Windows.
O painel rápido abre pelo botão Acesso rápido e lista Capture e Snippets quando ativados.
Escape fecha o painel. A geometria é limitada à tela primária neste protótipo.
Preferências antigas (esquemas 1 e 2) são lidas pelo esquema 3 sem perder a ativação de Capture.
Ícone global, integração contextual, monitores múltiplos, favoritos, tema e detecção de tela cheia são pendentes.

## Snippets (a4)

Ative Snippets no catálogo e abra pelo Hub ou painel rápido. Cadastre título,
categoria e texto fictício; pesquise, edite, exclua e copie o texto salvo.
A cópia exige confirmação e substitui a área de transferência do sistema.
Não há leitura automática, monitoramento, colagem automática ou gravação dos textos.
O conteúdo se perde ao desativar ou encerrar; o clipboard ou seu histórico pode
reter cópias independentes. Não use senhas ou informações pessoais reais.
O esquema 3 guarda somente preferências e flags dos módulos fora do repositório.
