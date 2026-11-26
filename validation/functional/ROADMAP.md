# Aeris — revisão funcional completa (orçamento zero)

Base imutável: RC4 integrado, run 45853309017, artefato 15134209156, SHA-256 fonte f52c8f065cb02b7052daffe79d57b58346528fd164688a847cc0aa8a57379efe. As melhorias são overlays versionados, verificando hashes de entrada, sem substituir o candidato histórico ou distribuir um novo instalador antes da revisão. O artefato expira em 26/12/2026; preservar o histórico e garantir fonte verificável para continuidade. Sem contratação de serviços, certificados ou lojas.

## Plano por categoria

| Fase | Ferramentas | Estado |
| --- | --- | --- |
| 01 Core | Hub, Spotlight, Health, Backup, Bridge | Alterações implementadas, CI iniciada |
| 02 Productivity | Focus, Workspace, Checklist, Reminder, Routine | Pendente |
| 03 Memory | Vault, Capture, Timeline, Ideas, Bookmarks | Pendente |
| 04 Quick Actions | Autofill, Clipboard, Snippets, Expand, Convert | Pendente |
| 05 Communication | Translate, Voice, Text, Email, Meeting | Pendente |
| 06 Learning | Learn, Research, Flashcards, Pronounce, Accessibility | Pendente |
| 07 Intelligence | Copilot, Context, Interview, Search, Debug | Pendente |
| 08 Business | Data, Dashboard, Report, Calculator, Decision | Pendente |
| 09 Files | Documents, Organizer, Drop, Compare, Lens | Pendente |
| 10 Security | Privacy, Link, Verify, Permissions, Metadata | Pendente |
| 11 Integração | Fluxos entre ferramentas, build experimental versionado, documentação e regressão final | Pendente |

Cada fase: revisar implementação real e limitações, adicionar melhorias úteis sem ampliar permissões, preservar dados, criar regressões e testar interface real quando disponível. A revisão não significa que todos os casos de uso foram testados. Não aumentar a versão pública nem declarar estabilidade sem direitos, scan e validação aplicável. Integrações gratuitas e opcionais; não introduzir APIs pagas.

## Fase 01 — Core (26/11/2026)

[Overlay](apply-core.py) (74ee294): seis arquivos do RC4 verificados byte a byte. Hub: corrigir subtítulo, preservar seleção após filtragem, limpar filtros, navegação Enter e duplo clique sem ativar módulos automaticamente. Spotlight: foco de teclado, menu Shift+F10, Escape retorna foco ao ícone. Health: finalizar medição cancelada/desativada sem manter botão bloqueado. Backup: vincular restauração ao SHA-256 de todo o arquivo inspecionado e confirmar a seleção após diálogo; não alterar formato nem DPAPI. Bridge: conferir contexto de entrada e identidade da prévia no momento de confirmar cópia/salvamento, inclusive alterações ocorridas antes do processamento do evento Tk. [Seis testes](test_core_refinement.py) (a9c3407). [Workflow](../../.github/workflows/aeris-functional-core.yml) (ba62003) baixa RC4 exato, aplica mudanças, roda seis novos testes, regressão completa e cinco smokes existentes. Resultado ainda não confirmado. Nenhum instalador novo publicado. Testes de foco real com Narrator e Windows cliente continuam pendentes; hash de backup não equivale a autenticação de autoria.

Próxima ação: conferir CI 01, corrigir falhas reais, registrar evidências e avançar para Productivity. Manter o código cumulativo em overlays verificáveis; antes da etapa 11, consolidar fonte e revalidar o pacote final.
