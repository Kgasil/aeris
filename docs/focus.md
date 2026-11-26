# Aeris Focus — v0.7.0a1

## Comportamento
- Concentração (25 min) e Intervalo (5 min), duração personalizável de 1 a 120 minutos.
- Estados: pronto, em andamento, pausado e concluído. Iniciar a partir de concluído cria uma nova sessão. Reiniciar descarta a sessão incompleta e mantém contadores concluídos.
- `time.monotonic()` fornece o prazo de referência. A interface atualiza a cada 250 ms enquanto a sessão está ativa; atraso de interface não é contado como número de ticks. A conclusão é registrada uma única vez quando observada.
- Não troca automaticamente de modalidade nem inicia a próxima sessão.
- O sinal sonoro opcional é `Tk.bell()`, desativado por padrão a cada abertura. Não é uma notificação nativa do Windows e pode ser inaudível dependendo das configurações do sistema.
- Fechar a janela cancela o callback e pausa (ou registra conclusão se o prazo já tiver vencido). Reabrir permite retomar manualmente. Minimizar mantém a contagem enquanto o processo estiver em execução.
- Desativar módulo, limpar sessão ou encerrar descarta temporizador e contadores. Não há histórico em disco; somente o estado de ativação e favoritos usa as preferências já existentes.

## Privacidade e limites
Não lê teclado, aplicativos, janelas, microfone, clipboard, arquivos de usuário ou atividade de navegação. Não há permissões de dados novas. O checkbox do sinal sonoro é um consentimento local da interface, não uma autorização do sistema. Não mede produtividade real. O relógio monotônico não é um relógio de parede; o comportamento em suspensão depende da plataforma. O inventário de privacidade não exibe os contadores de Focus. Nenhum serviço residente, agendamento externo ou sincronização.

## Verificação
`cd desktop` e `python -m unittest discover -q` (185 casos: 181 aprovados e quatro ignorados por exigir Windows). `xvfb-run -a python -m tests.smoke_focus` em Linux. Todos os 29 smoke tests gráficos passaram. O relógio foi injetado nos testes para verificar conclusão, pausa, retomada e limpeza sem aguardar minutos; o sinal sonoro foi simulado. A precisão de longo prazo, comportamento em suspensão, som real e Windows 10/11 continuam pendentes, assim como medições de desempenho nesta versão.
