# Aeris Ideas — v0.7.0a4

## Objetivo
Registrar ideias voluntariamente, categorizá-las e acompanhar seu desenvolvimento, sem monitoramento, rede ou persistência de conteúdo. O módulo é opcional e inicialmente desativado.

## Uso
1. Ative Ideas no Hub. Abra pelo Hub ou painel rápido (Spotlight/Workspace quando configurados).
2. Digite título, categoria personalizada, descrição e estado; salve. Até 200 ideias por sessão, 160 caracteres no título, 60 na categoria, 4.000 na descrição. Título e categoria obrigatórios.
3. Pesquise palavras em título, categoria ou descrição (até 200 caracteres; todas as palavras devem corresponder, sem distinção de acentos e caixa). Filtre por estado: Nova, Em desenvolvimento, Concluída ou Arquivada.
4. Selecione e abra um registro para editar. Excluir pede confirmação. Nova/limpar, abrir outro registro e fechar pedem confirmação se houver alterações não salvas.
5. Fechar preserva registros salvos na memória. Desativar com conteúdo ou janela aberta pede confirmação. Limpeza da sessão e encerramento descartam os registros. Privacy contabiliza somente os itens salvos. Não há apagamento seguro de memória.

## Implementação
- `aeris/ideas.py`: dataclass imutável, IDs de sessão, validação, CRUD e pesquisa. Reutiliza normalização do catálogo. Edição valida antes de substituir o item.
- `aeris/ideas_ui.py`: editor Tk/ttk, filtros e proteção de rascunho; nenhum serviço residente.
- `aeris/settings.py`: esquema 33, migração dos esquemas 1–32; somente a preferência de ativação e favoritos persistem.
- `aeris/hub.py`, `privacy.py`: ciclo de vida e inventário de contagem.

## Limites
Sem persistência protegida, anexos, sincronização, busca global, integração com Checklist, Timeline ou Companion. O motor possui filtro de categoria, mas a UI usa pesquisa textual e filtro de estado. Arquivar é um estado, não uma operação de armazenamento. A futura interface de comandos por voz deve validar intenção, confirmar a operação e informar o resultado real; não implementada. Usar dados fictícios nesta pré-alpha.

## Validação
Linux: 203 testes unitários descobertos, 199 aprovados e quatro ignorados (Windows); 32 scripts gráficos executados com Xvfb, todos aprovados. Testes de criação, edição atômica, estados, pesquisa, limites e migração; teste gráfico de descarte, exclusão, desativação e limpeza. Confirmações simuladas nos testes. Sem validação nativa Windows, auditoria independente ou novas medições de desempenho.


**Atualização da consolidação (v0.11.0a2):** registros confirmados podem ser salvos/restaurados manualmente por Privacy → Cópias protegidas. Rascunhos e alterações não copiadas continuam temporários. Consulte `protected-storage.md` para permissões, prazos, limitações e validação.
