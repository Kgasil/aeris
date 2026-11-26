# Aeris Interview — v0.10.0a3

Treinamento individual offline, não assistência durante entrevistas ou avaliações reais. Não utiliza IA, microfone, câmera, tela, clipboard, rede ou fontes externas.

## Uso
1. Ative Interview no Hub e abra a ferramenta.
2. Escolha uma das quatro áreas: Comportamental, Dados e BI, Engenharia ou Software. Cada área contém três perguntas fixas.
3. Escreva sua resposta (até 4.000 caracteres). A orientação de estudo é opcional e pode ser revelada manualmente.
4. Marque os quatro critérios de autoavaliação conforme sua própria revisão. Salve a resposta para registrar o progresso. A contagem de critérios não é uma nota objetiva nem previsão de aprovação.
5. Navegue entre perguntas, altere respostas ou limpe uma resposta com confirmação. Trocar pergunta/área ou fechar com rascunho exige confirmação.

## Dados e limites
Uma resposta por pergunta (máximo 12), substituída ao salvar novamente. Respostas e autoavaliações em memória durante a sessão, inclusive ao fechar a janela. Desativação, limpeza da sessão e encerramento descartam os registros; o inventário Privacy conta apenas respostas salvas. Não há garantia de apagamento seguro da memória. Somente a preferência de ativação e favoritos é persistida. Banco de perguntas e orientações são fixos e não cobrem todas as profissões. Não há análise semântica, avaliação automática, importação, exportação ou voz. Futuro AI Companion poderá simular entrevistas apenas em treinamento autorizado.

## Validação
Linux: `python -m unittest discover -q` (294 executados, 290 aprovados e 4 ignorados por Windows); 46 scripts gráficos aprovados via Xvfb, incluindo `tests.smoke_interview`. Testes nativos Windows e auditoria independente pendentes.
