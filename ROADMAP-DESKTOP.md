# Project Aeris Desktop — Roadmap até 1.0.0

**Eficiência e Simplicidade. · K&G Vision · GRAAL**
Atualizado: 26/11/2026. Escopo: Desktop Windows x64. Extension 1.0.0 permanece independente.

Objetivo: oferecer um Setup.exe autossuficiente, gratuito, com instalação simples (baixar, abrir e confirmar), sem Python, terminal ou extração manual para o usuário final. Não instalar silenciosamente a partir do navegador, nem contornar avisos de segurança.

## Base concluída (evidência histórica)

- [x] 50 protótipos desktop consolidados no candidato 1.0.0rc1.
- [x] 395 testes nativos aprovados e quatro ignorados em Windows Server 2022.
- [x] Build x64, autoteste empacotado, instalação, reinstalação da mesma versão, desinstalação e preservação de dados fictícios testados em CI.
- [x] Website, README e fluxo opt-in de publicação de prévia preparados; nova execução do fluxo ainda não validada.
- [Evidence](downloads/windows-preview-evidence.json) · [Detailed checklist](validation/desktop-release-checklist.md)

## Sequência de execução

| Etapa | Entrega | Critério de conclusão | Status |
| --- | --- | --- | --- |
| 01 | Auditoria de distribuição e inventário de dependências | Inventário dos componentes realmente empacotados, versões, termos, avisos e lacunas de redistribuição | Em andamento — inventário verificado; direitos e avisos pendentes |
| 02 | Instalador simplificado | Revisar Inno Setup, instalação por usuário, idioma, atalhos, abertura opcional, desinstalação e ausência de dependências manuais; preservar AppId e dados | Concluída — CI aprovada; experiência interativa Windows 10/11 na etapa 06 |
| 03 | Build e CI de instalação | Validar novo workflow, gerar Setup.exe, hashes, logs e evidências; investigar falhas e testes ignorados | Concluída — 395 testes passaram; instalador e hashes verificados |
| 04 | Segurança e confiança da distribuição | Revisão dos binários, permissões, malware scan, hashes, decisão documentada sobre Authenticode e autorização de redistribuição; nenhuma alegação falsa de assinatura | Em andamento — Python 3.14.10/OpenSSL 3.5.9 confirmados no build; regressão corrigida, revalidação pendente |
| 05 | Prévia permanente | Publicar prerelease experimental versionada somente após aprovação da redistribuição e confiança; testar download direto e fallback do site | Pendente |
| 06 | Windows 10 e 11 | Executar checklist de instalação e primeiro uso em VMs limpas x64 com conta comum, sem Python; guardar evidências separadas | Pendente |
| 07 | Atualização e recuperação | Testar instalação de versões genuinamente distintas, preservação dos dados, falhas, rollback documentado e desinstalação | Pendente |
| 08 | Segurança nativa | Validar DPAPI, mutex, permissões e tratamento de dados sintéticos; corrigir defeitos e reexecutar testes | Pendente |
| 09 | IA local e integrações | Testar Ollama opcional, resposta real, indisponibilidade, timeout e configurações de privacidade; não empacotar modelos sem revisão | Pendente |
| 10 | Áudio e OCR | Validar dependências reais, autorização explícita, dados sintéticos, erros e comportamento offline | Pendente |
| 11 | Desempenho e acessibilidade | Definir metas antes dos testes; medir inicialização, CPU/RAM e responsividade; teclado, Narrator, escala e alto contraste | Pendente |
| 12 | Revisão integrada e candidato final | Regressão das 50 ferramentas, testes nativos e UI, revisão de licenças e evidências, correção de bloqueadores; candidato versionado | Pendente |
| 13 | Lançamento Desktop 1.0.0 | Publicar Setup.exe estável, hashes e notas somente após aprovação dos gates; atualizar site, README e página de status; conferir links e versão | Pendente |
| 14 | Integração GRAAL e pós-lançamento | Atualizar sites/READMEs do ecossistema, conferir links, identidade, versão, instruções e canal de reporte de bugs | Pendente |

## Regras de continuidade

- Ao receber “próximo”, trabalhar na primeira etapa aberta que tenha pré-requisitos satisfeitos; registrar alterações, commits, testes e limitações nesta página. Uma etapa pode exigir várias interações.
- Não marcar testes não executados como aprovados. Usar os estados Pendente, Em andamento, Bloqueada, Concluída; registrar o motivo quando bloqueada.
- Se uma tarefa depender de VM Windows, teste físico, confirmação de direitos ou assinatura que não estejam acessíveis, registrar o bloqueio e avançar nas tarefas independentes, sem publicar indevidamente.
- Preservar o histórico, o pacote de código-fonte original e a identidade visual. Manter 1.0.0rc1 experimental até o gate final. Não modificar a distribuição Extension 1.0.0 sem necessidade.
- Publicar somente com evidência verificável; não substituir assets publicados sem versionamento.

## Registro de andamento

- 26/11/2026 — Roadmap criado; etapa 01 é a próxima. Nenhum teste novo executado nesta atualização.

- 26/11/2026 — Etapa 01: [auditoria de distribuição](validation/desktop-distribution-audit.md) (8185ffd) e [verificador de manifesto](validation/audit-desktop-bundle.py) (71adb95) registrados. Artefato histórico baixado; três hashes e 1.002 arquivos conferidos. Inventário identifica 68 binários e seis arquivos de avisos/licenças. Revisão de direitos, versões incorporadas e avisos permanece em aberto; não publicar. Próxima tarefa independente: etapa 02, sem liberar distribuição.

- 26/11/2026 — Etapa 02: [receita Inno Setup simplificada](validation/installer/Aeris.iss) (d82dfd7), [workflow de CI](.github/workflows/aeris-windows-installer-preview.yml) (a495791) e [documentação](validation/installer/README.md) (599e737). Receita original inspecionada dentro do ZIP Fix 1; AppId, mutex, diretório, privilégios e aviso de prévia preservados. Seleção automática de idioma quando reconhecido, página de atalhos como confirmação de instalação, atalho desktop opcional selecionado por padrão, abertura voluntária desmarcada por padrão, sem abertura silenciosa. Verificações de atalhos e limpeza adicionadas à CI; compilação e execução gráfica não confirmadas nesta etapa. Próxima: etapa 03. Gate de licenças permanece aberto; nenhum binário novo publicado.

- 26/11/2026 — Etapa 03: identificada duplicação de YAML na edição anterior, com três execuções falhas antes da compilação (45844371158, 45844401154, 45844426759). Workflow reconstruído sobre a revisão anterior, mantendo verificações de atalhos, instalação/reinstalação/desinstalação, preservação de dados e ausência de abertura silenciosa; adicionados inventário do ZIP e diagnóstico de falhas. Commit e2c0e5d. [Nova execução Windows](https://github.com/Kgasil/aeris/actions/runs/45844664047) observada em fila; nenhum novo binário ou teste nativo confirmado ainda. Próxima ação: conferir resultados da execução, corrigir falhas se houver, baixar e verificar os artefatos. Publicação permanece condicionada às etapas 01 e 04.

- 26/11/2026 — Etapa 03 (continuação): [execução 45844664047](https://github.com/Kgasil/aeris/actions/runs/45844664047) confirmou os invariantes da receita, 399 testes executados (395 passaram, quatro ignorados) e build PyInstaller. Inno Setup 6.7.1 falhou na linha 65 do bloco Pascal [Code] com `'BEGIN' expected` (comentário iniciado por ponto e vírgula). Corrigida a sintaxe do comentário, sem mudar a lógica de instalação (commit 3bab9b7). [Nova execução 45844861678](https://github.com/Kgasil/aeris/actions/runs/45844861678) iniciou em fila. Instalação, atalhos, desinstalação, inventário e novos hashes ainda aguardam confirmação nesta revisão. Nenhum binário novo publicado; etapa 04 permanece condicionada às evidências.

- 26/11/2026 — Etapas 02 e 03: [CI 45844861678](https://github.com/Kgasil/aeris/actions/runs/45844861678) aprovada; 395 testes passaram, quatro ignorados. Instalador, atalhos, reinstalação, desinstalação e preservação de dados validados em Server 2022. [Evidências e hashes](downloads/windows-simplified-preview-evidence.json) conferidos após download (1.002 arquivos). Etapa 04 iniciada: comparação de inventário, modo por usuário, ausência de assinatura e lacunas de confiança documentadas. Workflow de build separado da publicação (62199c2) para impedir aprovação de bytes diferentes dos revisados. Malware scan, direitos e decisão de assinatura pendentes. Próxima: fechar etapas 01/04 e preparar publicação vinculada ao artefato aprovado, sem liberar antecipadamente.

- 26/11/2026 — Etapa 04 (continuação): [revisão de confiança e licenciamento](validation/desktop-trust-review.md) (e83d42f). Confirmados fim de suporte público de OpenSSL 3.0, correções posteriores ao Python 3.12.10 e versões corretivas do Inno Setup. [CI experimental Python 3.14.10](https://github.com/Kgasil/aeris/actions/runs/45845715571) (26ed9ac), isolada do build histórico e sem publicação, preparada para regressão e inventário de proveniência. Status inicial em fila. Próximo: revisar resultado e corrigir migração, conferir versão real do OpenSSL, licenças, DLLs, atualizar compilador com origem verificada, scan e decisão de assinatura. Nenhum lançamento autorizado; etapas 01/04 permanecem abertas.

- 26/11/2026 — Etapa 04: [primeira CI 3.14](https://github.com/Kgasil/aeris/actions/runs/45845715571) confirmou Python 3.14.10 e OpenSSL 3.5.9 no ambiente de build. 394 testes passaram, quatro ignorados e um falhou em validação de datas Timeline. Correção explícita dos limites de hora/minuto, sem remover testes; novos casos positivos de fronteira em CI (34ead92). [Nova execução](https://github.com/Kgasil/aeris/actions/runs/45845977466) iniciada; não houve novo instalador aprovado nesta interação. [Relatório de confiança](validation/desktop-trust-review.md) atualizado (d82965d). Próximo: confirmar suíte completa, inspecionar pacote e inventário, completar licenças e scan; publicação permanece bloqueada.

- 26/11/2026 — Etapa 04: regressão Timeline aprovada na CI 45845977466. Preparados [script de coleta de evidências Defender](validation/installer/scan-candidate.ps1) (50035cc) e [procedimento de análise](validation/installer/SCAN.md) (375f76d) com hashes vinculados ao artefato, proteção ativa, definições recentes, logs e detecções; sem execução do aplicativo, alterações do antivírus ou aprovação automática. O procedimento não foi executado em Windows. Status observado da CI: in_progress; conclusão pendente. Não publicar antes das verificações de pacote, licenças, scan e confiança.
