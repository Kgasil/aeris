# Aeris Checklist — v0.7.0a2

## Escopo
Listas de tarefas locais, voluntárias e temporárias. Até 20 listas por sessão; cada uma aceita 100 tarefas. Nomes de listas têm até 80 caracteres; títulos de tarefas até 200. Prioridades Baixa, Normal e Alta. O identificador interno é único na sessão; títulos iguais são permitidos. Renomear preserva tarefas, editar preserva o estado de conclusão. A barra de progresso considera todas as tarefas da lista, mesmo com filtros.

## Operação
Ativar no Hub. Criar uma lista pelo campo de nome e botão Criar; selecionar pelo menu. Adicionar tarefas com título e prioridade; selecionar uma linha para editar, alternar conclusão ou excluir. Excluir lista exige confirmação. Fechar a janela descarta campos de edição não aplicados, mas mantém listas e tarefas.

## Privacidade e arquitetura
`aeris/checklist.py`: modelo imutável Task e ChecklistStore limitado em memória. `aeris/checklist_ui.py`: janela Tk, sem thread ou temporizador. `settings.py`: esquema 31, módulo desativado por padrão. Integração com Hub, Spotlight, favoritos, Workspace e inventário Privacy (contagem de tarefas). Nenhuma leitura de outros aplicativos, nenhuma rede, nenhum arquivo com tarefas. Desativação, limpeza de sessão e encerramento descartam listas; isso não é apagamento seguro de memória. Não use dados pessoais reais na pré-alpha.

## Limites
Sem armazenamento permanente, alertas, datas de vencimento, recorrência, reordenação, ordenação por prioridade ou integração funcional com Focus. Sem garantia de desempenho ou compatibilidade nativa Windows até validação no alvo.

## Validação
Linux: 191 testes unitários descobertos, 187 aprovados e 4 ignorados por exigirem Windows; 30 testes gráficos aprovados via Xvfb. Novos testes cobrem listas independentes, edição, exclusão, renomeação, validação, limites, migração, filtros e descarte da sessão.


**Atualização da consolidação (v0.11.0a2):** registros confirmados podem ser salvos/restaurados manualmente por Privacy → Cópias protegidas. Rascunhos e alterações não copiadas continuam temporários. Consulte `protected-storage.md` para permissões, prazos, limitações e validação.
