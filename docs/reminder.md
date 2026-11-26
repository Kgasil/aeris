# Aeris Reminder — v0.7.0a3

Ative o módulo no catálogo, abra pelo Hub/Spotlight/Workspace, informe descrição (até 200 caracteres), prazo relativo de 1 a 10.080 minutos (sete dias) e, opcionalmente, marque o alerta visual genérico. Adicione, reprograme um lembrete pendente, cancele ou exclua. Até 100 registros em memória. A lista mostra vencimento local e estados pendente, vencido e cancelado. Não há agenda externa, recorrência, datas absolutas, áudio, persistência ou notificações nativas do Windows.

ReminderStore utiliza tempo de parede para vencimentos e transições únicas. Hub mantém no máximo um callback Tk, com reavaliação a cada 30 segundos no máximo enquanto houver lembretes pendentes; não há callback se não houver pendências. Fechar a janela mantém o agendamento durante a execução do Aeris. O alerta visual genérico não mostra títulos; pode agregar múltiplos vencimentos e ser dispensado. Desativar, limpar sessão ou encerrar cancela o callback e descarta os registros. Privacy contabiliza registros sem expor o texto. Mudanças no relógio, suspensão e bloqueio do computador podem atrasar ou antecipar o alerta; não usar para compromissos críticos. Sem serviço residente adicional ou rede.

Validação: 193 testes unitários executáveis em Linux, 4 ignorados por exigirem Windows; 31 smoke tests gráficos aprovados em Linux/Xvfb, em lotes. Relógio controlado nos testes de vencimento. Windows nativo, suspensão e precisão de longo prazo pendentes.

Próxima ferramenta: Ideas. A integração futura de comandos por voz está especificada em `ai-companion-concept.md`.


**Atualização da consolidação (v0.11.0a2):** registros confirmados podem ser salvos/restaurados manualmente por Privacy → Cópias protegidas. Rascunhos e alterações não copiadas continuam temporários. Consulte `protected-storage.md` para permissões, prazos, limitações e validação.
