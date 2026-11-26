# Aeris Timeline — v0.7.0a5

Histórico voluntário e local, sem coleta de eventos de outros módulos ou aplicações.

## Implementação

- `aeris/timeline.py`: registros imutáveis em memória, até 300, título 160 caracteres, categoria 60, descrição opcional 2.000; validação de caracteres de controle reutilizada de Ideas; IDs monotônicos por store.
- Data/hora civil local, formato estrito `AAAA-MM-DD HH:MM`, sem offset, conversão de fuso ou validação de horários ambíguos de verão. Pode ser fornecida pelo usuário, inclusive futura; não é prova de execução da atividade. Ordenação decrescente por data e hora, com desempate por ID.
- Pesquisa textual insensível a acentos e caixa; categoria exata normalizada; intervalo inclusivo de datas, limites opcionais e validação de ordem.
- `timeline_ui.py`: editor com confirmação de exclusão e proteção de rascunhos, tabela e filtros; botão Agora preenche horário local, mas não salva.
- `hub.py`, `settings.py`, `catalog.json`, `privacy.py`: habilitação opcional, favoritos, Workspace, Spotlight, inventário e descarte na limpeza. Migração de preferências 1–33 para esquema 34 na próxima gravação. Somente preferências não sensíveis persistem.

## Verificação

205 testes unitários aprovados, quatro ignorados por exigir Windows, e 33 scripts gráficos aprovados com Xvfb no Linux. Seis novos testes unitários e um gráfico. Nenhum teste nativo Windows novo executado.

## Limites

Fechar a janela preserva registros durante a sessão, mas não rascunhos descartados. Desativar ou encerrar exige confirmação quando há conteúdo; limpar sessão solicita confirmação global. Não é apagamento seguro de memória. Não há rastreamento de atividades, gravação de tela, coleta de digitação, rede, exportação, agendamento, sincronização ou persistência. Não há importação automática de Focus, Checklist, Reminder ou Ideas nem execução de comandos de voz. Tais integrações deverão ser explicitamente autorizadas, limitadas e revisáveis. Datas e textos são declarados pelo usuário, não auditados. O protótipo deve usar dados fictícios até validação nativa e revisão independente.
