# Integration Engine I — v0.11.0a5

Dois fluxos locais para atividades pendentes de reuniões salvas. Nenhuma gravação de disco automática, rede, leitura de outros aplicativos ou alteração na reunião original.

## Uso
1. Ative Meeting e a ferramenta de destino no Hub. Abra ambas. Para Checklist, crie uma lista de destino previamente.
2. Conceda a permissão de sessão `Meeting → Integrações` em Permissions.
3. Salve a reunião e selecione uma atividade pendente na aba Plano de ação. Finalize rascunhos antes de transferir.
4. Clique em Enviar para Checklist ou Criar Reminder. Informe a lista existente (nome exato) ou horário local HH:MM para a data já cadastrada na atividade.
5. Confira a prévia e confirme. O registro será criado no destino na sessão e a interface aberta será atualizada. Para Reminder, o agendador é reativado.

Checklist recebe apenas título, prioridade Normal e estado pendente: não possui campos de responsável ou prazo. Reminder recebe título e horário absoluto, com alerta visual genérico enquanto o Aeris estiver aberto. O prazo precisa estar no futuro, dentro de sete dias; horários ambíguos ou inexistentes são rejeitados. Não há sincronização posterior ou vínculo persistente de origem. Duplicatas são bloqueadas por título (sem distinguir caixa) na lista de tarefas ou título e horário entre lembretes pendentes. O usuário pode modificar/excluir o registro no destino independentemente. Use Protected Storage manual para salvar os destinos.

## Segurança e testes
O executor aceita somente os dois destinos fixos, revalida permissão, identidade da reunião salva e do store de destino, estado da atividade, parâmetros, capacidade e horário após confirmação. Não interpreta texto de reunião como comando. A permissão é temporária. Não é uma barreira contra processos hostis no mesmo usuário do sistema.

Sete testes unitários e um script gráfico novo; testes com diálogos simulados e relógios controlados não substituem uso real no Windows. Testes nativos anteriores continuam pendentes. Próximas integrações: Learn/Research/Flashcards com revisão humana; não gerar respostas de cartões a partir de títulos sem conteúdo validado.
