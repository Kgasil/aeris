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
| 01 | Auditoria de distribuição e inventário de dependências | Inventário dos componentes realmente empacotados, versões, termos, avisos e lacunas de redistribuição | Próxima |
| 02 | Instalador simplificado | Revisar Inno Setup, instalação por usuário, idioma, atalhos, abertura opcional, desinstalação e ausência de dependências manuais; preservar AppId e dados | Pendente |
| 03 | Build e CI de instalação | Validar novo workflow, gerar Setup.exe, hashes, logs e evidências; investigar falhas e testes ignorados | Pendente |
| 04 | Segurança e confiança da distribuição | Revisão dos binários, permissões, malware scan, hashes, decisão documentada sobre Authenticode e autorização de redistribuição; nenhuma alegação falsa de assinatura | Pendente |
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
