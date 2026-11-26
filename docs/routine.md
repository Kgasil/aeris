# Aeris Routine — v0.4.0a4

## Escopo

Editor de sequências locais de um a cinco fluxos existentes do Bridge, com entrada manual e prévia final. Até 30 rotinas em memória. Nome de até 80 caracteres. Adicionar, remover, reordenar, atualizar, carregar e excluir sequências. As rotinas guardam apenas nomes e etapas; textos de entrada e resultados não são armazenados nas definições.

## Regras

- Expand → Text pode ser utilizado antes de outras etapas; Translate → Email e Text → Capture somente no final.
- Translate usa o guia local de frases, não Argos. Text → Capture é apenas prévia; não escreve no Capture.
- A execução exige Routine e Bridge ativos, todos os módulos envolvidos ativos e autorização Routine.run e Bridge.run por sessão.
- Cópia exige Routine.clipboard.write, verificação das permissões de execução e confirmação explícita. O clipboard do Windows pode manter cópias independentes.
- Alterar entrada, sequência, idioma ou permissões invalida a prévia. Desativar um participante fecha a janela e revoga autorizações de Routine. As definições permanecem até desativar Routine, limpar a sessão ou encerrar. Não há apagamento seguro de RAM.
- Sem agendamentos, shell, envio de e-mail, execução global, integração externa ou persistência de rotinas. Não é uma sandbox.

## Validação

Python 3.13.5, Linux/Xvfb: 107 testes unitários aprovados, três ignorados por exigir Windows e 17 testes gráficos aprovados. O teste gráfico novo verifica permissões, edição, resultado, clipboard, revogação, invalidação e limpeza. O primeiro comando de regressão gráfica usou separadores de caminho incorretos para `python -m`; corrigido e toda a suíte gráfica foi executada com sucesso. Windows 10/11, DPI e desempenho não validados. Testar somente com dados fictícios.
