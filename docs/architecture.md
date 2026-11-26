# Foundation — consolidação a7

- Base local reconstruída a partir do protótipo a1, do catálogo, das interfaces e decisões documentadas da a4 e dos módulos locais a5/a6. Não foi possível clonar a branch develop pelo ambiente local. Não é um checkout byte a byte da a4; funcionalidades anteriores foram reimplementadas em estruturas compartilhadas. A branch develop existente não foi alterada.
- `registry.py` + `catalog.json`: catálogo declarativo de 50 ferramentas, somente cinco com status de protótipo.
- `hub.py`: coordena ativação, carregamento sob demanda, ciclo de vida e navegação. Não executa módulos planejados.
- `content.py` + `editor.py`: armazenamento volátil e editor compartilhados para Capture e Snippets. Limites de quantidade e tamanho; não há persistência de texto. `capture.py`, `snippets.py`, `snippets_ui.py` preservam interfaces dos módulos.
- `search.py` + `search_ui.py`: motor a5 reutilizado; fontes escolhidas explicitamente, consulta sem histórico ou indexação permanente, atualização por evento em alteração de conteúdo. Desativar módulo fecha pesquisa para evitar resultados obsoletos.
- `spotlight.py`: implementação a6 reutilizada; ícone opt-in, posicionamento no monitor primário, painel adjacente, sem monitoramento global de cliques. Sobreposição opcional e ocultação manual; não detecta jogos.
- `settings.py` + `appearance_ui.py`: preferências validadas e substituição atômica do arquivo JSON; leitura de esquemas anteriores. Configurações de canto, ícone 24–64 px, três tamanhos de painel e opacidade 80–100% (quando suportada), prévia e restauração. `quick_panel.py`: painel relativo ao Hub.
- Apenas um processo Python/Tkinter; módulos de conteúdo criados sob demanda. O ícone ainda depende do processo do Hub; não é serviço residente independente. Ao abrir ferramenta pelo Spotlight, restaura o Hub.

## Atualização a8 — refinamento

- `theme.py`: paletas claro/escuro, estilos ttk compartilhados e recoloração de widgets Tk; elementos nativos do sistema podem divergir. Não há tema automático.
- Esquema 6 mantém compatibilidade de leitura com 1–5. Validação de tema e favoritos; preferências salvas atomicamente. Favoritos são restritos aos módulos Capture/Snippets/Search; filtragem não concede permissão ou ativa ferramentas. Painéis compartilham `Hub.quick_tools()`.
- `privacy_ui.py`: transparência sobre sessão, ocultação manual e limpeza confirmada de textos e rascunhos. Fecha pesquisa/editores antes de liberar dados e mantém as preferências de ativação. Clipboard intocado. Não confundir remoção lógica com apagamento seguro de RAM/swap. Módulo Permissions ainda não implementado.
- Spotlight abre ferramentas sem restauração explícita do Hub. O comportamento de foco, minimização, DPI, monitores e fullscreen precisa ser validado em Windows.
- Sem alteração do catálogo de 50 ferramentas, cinco em protótipo. Nenhuma publicação GitHub.

## Próxima etapa

Validação Foundation e preparação do instalador Windows: testar escalas de exibição, teclado, foco, clique esquerdo/direito, área útil, telas pequenas, tema e legibilidade. Medir CPU e RAM ociosas com e sem Spotlight, latência de abertura, tamanho do pacote e tráfego de rede. Revisar comportamento de encerramento e retenção. Não afirmar cumprimento de metas sem medição. Definir proteção, retenção e exclusão antes de persistir conteúdo real, na fase Personal Memory.

## Personal Memory — v0.2.0a1

Permissions é um serviço interno central e uma interface administrativa. As três autorizações de sessão são negadas por padrão e verificadas nos fluxos de Search e na ação explícita de cópia de Snippets. A interface administrativa permanece acessível mesmo sem módulos opcionais. Não é sandbox de sistema. Veja permissions.md. Próximo módulo: Vault; sem armazenamento de dados pessoais reais até definição e validação da proteção. Windows 10/11 x64 continua plataforma-alvo, com validação nativa pendente.

## Personal Memory — v0.2.0a2

- Vault: módulo opt-in, editor próprio, persistência DPAPI Windows no escopo de usuário, sem fallback de criptografia.
- Esquema 7 inclui flag Vault e favorito; mantém leitura dos anteriores.
- O Search não recebe dados do Vault. Limpar sessão/fechar/desativar bloqueia o cofre e preserva registros gravados.
- Validação do fluxo com simulador em Linux; DPAPI e lock nativos precisam de testes Windows. Veja vault.md.

## Personal Memory — v0.2.0a3

- Clipboard opt-in: histórico manual e volátil, sem polling, acesso à rede ou persistência de conteúdo.
- Limites: 50 registros, 20.000 caracteres por texto; deduplicação exata e descarte do item não fixado mais antigo.
- Leitura e escrita do clipboard com permissões separadas, negadas por padrão, verificadas antes de cada ação e confirmação na interface.
- Revogar não apaga registros já capturados; limpar sessão/desativar apaga histórico e revoga acessos, preservando clipboard do sistema.
- Esquema 8, migração de 1–7. Hub, favoritos, Spotlight e temas integrados. Search não indexa Clipboard.
- Próximo: Bookmarks. Testes Windows e auditoria de segurança pendentes.

## Personal Memory — v0.2.0a4

- Bookmarks é opcional, com modelo independente e persistência protegida reutilizando o serviço Vault em arquivo separado `bookmarks.bin`. DPAPI real só em Windows; sem fallback de texto claro.
- Cadastro, edição, exclusão e pesquisa local por título, categoria e endereço; limite de 100 registros, URL até 4096 caracteres. Rejeita duplicatas exatas, credenciais e protocolos fora de HTTP/HTTPS. Validação sintática não é análise de risco.
- Autorização de sessão `bookmarks.browser.open` e confirmação explícita antes de encaminhar via `os.startfile` ao navegador padrão; nenhum acesso HTTP pelo Aeris.
- Limpeza de sessão bloqueia o armazenamento e revoga permissões; não apaga os registros persistidos. Esquema 9 migra preferências de 1–8.
- Ajuste de layout em duas colunas no Hub e painéis com mais de três ferramentas; configuração de favoritos e permissões também reorganizadas.
- Verificação: 50 unitários aprovados, 1 ignorado (DPAPI nativo), 7 testes gráficos aprovados em Linux/Xvfb; navegador e criptografia simulados. Próximo: Backup e restauração protegidos, seguidos de consolidação Personal Memory.

## Personal Memory — v0.2.0a5

Backup opt-in, com permissões de exportar/restaurar independentes. Formato JSON limitado (90 MiB), lista fechada de itens, Base64 de blobs DPAPI existentes e aparência, SHA-256 de cada item. Não extrai caminhos fornecidos pelo arquivo. Aquisição da mesma trava do Vault/Bookmarks antes de ler ou substituir dados protegidos. Restauração por item, verificação DPAPI e estrutura, recuperação do arquivo anterior e substituição atômica. Preferências schema 10; leitura de schemas anteriores. Não há assinatura do arquivo nem backup portátil, restauração de permissões ou dados de sessão. Teste nativo e política de retenção das cópias de recuperação pendentes.

## Communication — v0.3.0a1

Translate opt-in: guia de frases embutido e adaptador experimental Argos em subprocesso iniciado sob demanda. Sem persistência ou indexação. Autorização de sessão para cópia. Esquema 11 migra flags anteriores. Backup também aparece nos painéis ativos (corrigida omissão anterior). Sem download automático e sem fallback remoto. Testes de rede/recursos reais e Windows pendentes.

## Communication — v0.3.0a2

Voice opt-in, com síntese de texto em fala pelo Windows PowerShell 5.1/System.Speech sob demanda. Código PowerShell fixo, JSON ASCII em stdin, sem shell ou texto interpolado; somente Speak de texto simples, não SSML. Permissão de sessão para consultar vozes e reproduzir; revogação e fechamento cancelam subprocesso. Sem microfone, rede explícita, persistência ou indexação. Esquema 12 lê anteriores. Backend simulado em Linux; validação de áudio real e de vozes instaladas no Windows pendente.

## Text (0.3.0a3)

Operações determinísticas, prévia independente, permissão de cópia, sem dependências adicionais. Próximo: Email. Proposta futura separada: docs/ai-companion-concept.md.

## Communication — v0.3.0a4

Email opt-in. Composição determinística de 24 combinações de modelos locais (3 idiomas × 2 tons × 4 finalidades), detalhes fornecidos pelo usuário, prévia invalidada por edição, permissão separada de cópia e confirmação. Não acessa contas, rede ou aplicativos de e-mail. Sem armazenamento dos rascunhos. Esquema 14 preserva preferências anteriores.

## Communication — v0.3.0a5

Pronounce reutiliza VoiceWindow, o subprocesso de síntese e a serialização de dados via stdin; permissão independente e limitada à sessão. O script fixo de PowerShell filtra vozes por Culture.TwoLetterISOLanguageName e confirma a cultura na reprodução; 1–5 repetições com pausa de 700 ms. Sem fallback de idioma, microfone ou avaliação. A mudança de idioma cancela a operação e invalida a lista de vozes; texto permanece para revisão. Esquema 15 migra 1–14. Rolagem das listas de ferramentas e permissões. 15 protótipos; 35 planejados; nenhuma versão pública.

## Smart Automation — v0.4.0a1

- Autofill: módulo opt-in, perfis estruturados protegidos pelo backend de Vault em arquivo separado; prévia seletiva e cópia manual com permissão. Sem automação externa até implantação e avaliação da extensão contextual. Backup de perfis pendente.
- Configurações esquema 16, favoritos e central de permissões atualizados; limpeza de sessão bloqueia os perfis. Catálogo: 16 protótipos e 34 planejados.
- Correção ortográfica e gramatical automática adicionada aos requisitos do Text (ver text.md). Ainda não implementada.
- 90 testes unitários e 14 gráficos aprovados em Linux, 3 testes nativos Windows ignorados. Sem publicação GitHub.

## Smart Automation — Expand (a2)

Motor determinístico em memória separado da interface; integração pelo Hub e quick_tools, permissão de cópia independente. Esquema 17. Não há integração externa nem expansão durante digitação em terceiros. Próximo: Bridge.

## Bridge — 0.4.0a3

- Integração por fluxos fixos reutilizando Expand, Text, Translate básico e Email; criação de notas no Capture somente após revisão. Capture e Snippets podem fornecer entradas mediante permissões distintas.
- Motor e UI separados. Sem execução de código arbitrário, agendamento, rede ou serviços residentes. Permissões em memória, rechecadas antes das ações.
- Desativar módulo envolvido fecha Bridge e revoga seus acessos. Preferências migradas para esquema 18.
- 101 testes unitários aprovados, 3 específicos Windows ignorados, 16 testes gráficos aprovados em Linux. Validação nativa pendente.

## 0.4.0a4 — Routine

Sequências limitadas de fluxos Bridge, entrada manual, prévia final, 30 rotinas voláteis. Permissões Routine.run e Routine.clipboard.write independentes, além de Bridge.run e módulos ativos. Sem agendamento, execução arbitrária ou efeitos de escrita automáticos. Esquema 19. Validação Linux: 107 unitários e 17 gráficos aprovados, três testes Windows ignorados. Próximo: Workspace.

## 0.4.0a5 — Workspace

Presets voláteis de ferramentas ativas e links explícitos. Filtro temporário compartilhado por Spotlight e painel rápido, sem alteração de preferências, ativação automática ou abertura em lote. Permissão independente workspace.browser.open e confirmação por link. Reutiliza validação HTTP/HTTPS do Bookmarks e abertura Windows. Esquema 20. Validação Linux: 112 unitários e 18 gráficos aprovados; três testes Windows ignorados. Próxima fase: Digital Security.


## Verify — v0.5.0a3

Hash local em blocos de 1 MiB com thread sob demanda, autorização explícita, confirmação e cancelamento cooperativo. SHA-256/SHA-512 e comparação opcional; sem autenticação de origem, antivírus ou persistência. Consulte verify.md para os limites e validação.

## Metadata — v0.5.0a4

Leitor local opcional de metadados PNG/JPEG/OOXML, com permissão independente, limites de entrada e de relatório e thread transitória. Reutiliza validação de caminhos e verificação de alterações de Verify; usa somente biblioteca padrão. Nenhuma modificação, extração de pacote, envio ou histórico. Análise parcial, sem sandbox do SO. Veja `metadata.md`.

## Health — v0.5.0a5

Medição sob demanda do processo atual com CPU por intervalo monotônico e working set/RSS atual. Um callback único de dois segundos, sem polling residente, sem persistência e sem novas dependências. Esquema 24. Baseline Linux preliminar em `health-baseline-linux.json`; limites em `health.md`. Não mede processos filhos nem núcleo separado. 25 ferramentas em protótipo, cinco fases iniciais; próxima fase File Intelligence. Validação Windows e auditoria ainda pendentes.

## Lens — v0.6.0a5

OCR opcional executado sob demanda em subprocesso Tesseract, sem dependências Python adicionais. Reutiliza validações de Verify e Metadata, seleção explícita e permissão `lens.image.read`. Esquema 29 adiciona o módulo desativado por padrão. Sem captura de tela automática, persistência, rede pelo módulo ou integração direta com outros motores. Ver `lens.md` para os limites e a validação real em Linux. File Intelligence: 5/5 protótipos; próxima fase Daily Productivity. O corretor gramatical automático do Text continua requisito pendente.

## Focus — v0.7.0a1

Temporizador de sessão com relógio monotônico e modelo separado da interface. Um callback Tk a cada 250 ms somente durante execução; sem thread ou serviço adicional. Estado e contadores em memória, fechamento pausa, desativação e limpeza descartam. Sinal sonoro opcional local, desligado por padrão a cada abertura. Sem monitoramento de atividade, transição automática ou integração com notificações do Windows. Preferências esquema 30, Focus desativado por padrão. Daily Productivity: 1/5 protótipos. Ver `focus.md`.


## Checklist — v0.7.0a2

ChecklistStore guarda listas nomeadas e tarefas imutáveis com identificadores de sessão, título, prioridade e conclusão. ChecklistWindow usa Treeview, filtros e Progressbar; sem polling ou processos auxiliares. Hub controla o ciclo de vida e Privacy contabiliza as tarefas. O esquema 31 persiste apenas a ativação e favoritos, não as listas.


## Reminder — v0.7.0a3

ReminderStore mantém até 100 registros temporários; Hub agenda um callback Tk apenas enquanto há lembretes pendentes e apresenta alertas visuais opcionais genéricos. Esquema 32 para ativação e favoritos. Veja `reminder.md`. A futura edição Companion deverá converter comandos falados em propostas de operações validadas pelos módulos, com confirmação e retorno efetivo; veja `ai-companion-concept.md`.
