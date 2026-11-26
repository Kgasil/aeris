# Project Aeris — Eficiência e Simplicidade.

> **Branch desktop-experience — candidato 1.1.0rc1, não publicado.** Consulte [preparação e critérios de lançamento](../docs/experience-release-candidate.md). As seções históricas abaixo descrevem versões anteriores, não evidências deste candidato.

**by K&G Vision · Desktop v1.0.0rc5 · candidato de código-fonte**

Pacote candidato de código-fonte para testes com dados fictícios; não é uma versão Windows validada ou um instalador. Site e Web Lab em https://kgasil.github.io/aeris/.
50 ferramentas em protótipo. A publicação binária permanece bloqueada.

## Execução futura no Windows

Plataforma-alvo: Windows 10/11 de 64 bits. Python 3.14.10 com Tcl/Tk instalado. Em PowerShell, na pasta desktop:

```powershell
py -3 main.py
```

Ou execute `iniciar.bat`. Não requer dependências Python externas. Lens requer Tesseract e modelos opcionais instalados manualmente.

## Fluxo

1. No Hub, escolha Capture, Snippets, Search, Vault, Clipboard ou Bookmarks no catálogo e ative os desejados.
2. Capture e Snippets: crie textos fictícios, edite, pesquise e exclua.
3. Search: escolha as fontes; por padrão só pesquisa o catálogo. Os textos das fontes ativadas só entram na pesquisa mediante autorização em Permissões e seleção explícita da fonte.
4. Configurações: habilite o Spotlight, escolha canto, tamanho, opacidade e sobreposição opcional. Clique esquerdo no ícone para abrir/fechar. Clique direito para opções. Escape fecha o painel.
5. Oculte o ícone manualmente antes de jogos; encerre pelo Hub para fechar o processo.

## Limitações

Textos do Capture, Snippets e Clipboard apenas em memória; desaparecem ao desativar o módulo ou encerrar. Vault e Bookmarks possuem arquivos separados protegidos via DPAPI no Windows. Não use dados pessoais reais. O botão de cópia de snippets exige autorização na sessão e confirmação e pode permanecer no clipboard/histórico do sistema. Preferências não sensíveis em `%LOCALAPPDATA%/Aeris/settings.json` (Windows); migração de esquemas 1–48 para 49 na próxima gravação. Sem requisições externas pelo núcleo por padrão; Companion opcional utiliza HTTP loopback. Sem conta, captura global, envio de formulários ou colagem automática. Bookmarks pode encaminhar um endereço ao navegador, que poderá acessar a rede. Não há proteção contra captura de memória/swap pelo sistema. Sem validação Windows, benchmark completo de desempenho, instalador, tema automático do sistema, arraste livre, múltiplos monitores, preenchimento contextual ou detecção automática de tela cheia.

## Verificação

392 testes unitários e 60 testes gráficos aprovados em Linux com Xvfb; seis testes nativos foram ignorados por exigir Windows. Os testes dos fluxos do Vault e Bookmarks usam um backend simulado, sem valor criptográfico; o acionamento do navegador também é simulado. A simulação de confirmação em testes não substitui validação humana. Consulte `../docs/architecture.md` para a estratégia e limites.

## Refinamento a8

Em Configurações, selecione tema claro ou escuro, marque ferramentas favoritas e, opcionalmente, mostre apenas favoritos ativos nos painéis. Os favoritos não ativam módulos. A prévia reflete as escolhas de tamanho, tema e posição; as preferências são gravadas somente ao salvar. Os editores podem abrir pelo Spotlight sem restaurar explicitamente o Hub; comportamento com janelas minimizadas no Windows ainda não validado.

Em Privacidade, é possível ocultar o Spotlight nesta sessão e, mediante confirmação, limpar textos e rascunhos de Capture, Snippets e Clipboard, fechando a pesquisa e os editores. A limpeza lógica não é apagamento seguro de memória, swap ou histórico de clipboard; os módulos continuam ativados. A revisão de privacidade é preliminar, não auditoria ou garantia de segurança.

## Permissions (0.2.0a1)

No Hub, abra Permissões para autorizar separadamente Search → Capture, Search → Snippets, Snippets → Clipboard, Clipboard → Ler e Clipboard → Escrever. Tudo negado por padrão, sem persistência de autorizações. Revogar remove imediatamente resultados e prévias de fontes revogadas; desativar módulos retira as autorizações correspondentes. Limpar a sessão revoga todas. As autorizações são controles internos das funções do Aeris, não permissões de sistema operacional. A cópia manual por seleção de texto, o histórico do clipboard e outros aplicativos não são controlados pelo Aeris. Revogação não apaga cópias já realizadas.

## Vault (0.2.0a2)

Ative Vault no Hub, abra a ferramenta e clique em Desbloquear. Cadastre somente notas fictícias, salve, edite, exclua e bloqueie. O arquivo `%LOCALAPPDATA%/Aeris/vault.bin` é produzido somente por DPAPI de escopo do usuário Windows; não há fallback para texto claro. O módulo não abre em outros sistemas. Os dados persistem ao bloquear, fechar ou desativar Vault. Limpar a sessão bloqueia o cofre e descarta rascunhos, mas preserva registros salvos. Nenhum outro módulo pode pesquisar o conteúdo por meio das interfaces atuais.

O desbloqueio é um controle interno, não nova autenticação do Windows. Outros processos com o mesmo usuário podem acessar DPAPI; não há senha mestra, bloqueio por inatividade, recuperação, exportação, perfis estruturados ou backup nesta entrega. A perda da conta/perfil pode tornar os dados irrecuperáveis. Não armazene informações reais, senhas ou dados bancários antes da validação nativa e revisão de segurança. Veja a documentação do Vault.

## Clipboard (0.2.0a3)

Ative o módulo no Hub, autorize separadamente leitura e escrita em Permissões e abra pelo Hub ou Spotlight. Clique em Capturar texto atual e confirme para ler somente o texto disponível no clipboard. Nenhum monitoramento contínuo ou captura automática é feito. Até 50 itens de 20.000 caracteres cada; duplicatas são agrupadas, itens fixados ficam no topo e não são removidos automaticamente. Pesquise, selecione, copie com confirmação, fixe, exclua ou limpe. Nenhum texto é gravado em disco pelo módulo. Revogar leitura/escrita bloqueia novas operações correspondentes; itens já capturados continuam visíveis até limpeza. Desativar, limpar sessão ou encerrar remove o histórico do Aeris. O clipboard atual e seu histórico nativo não são apagados. Não capture senhas ou dados reais. Search não indexa Clipboard. O comportamento nativo do Windows ainda precisa ser testado, inclusive Unicode, formatos não textuais e histórico do sistema.

## Bookmarks (0.2.0a4)

Ative Bookmarks no catálogo e abra pelo Hub ou Spotlight. Desbloqueie o arquivo local, cadastre título, categoria e endereço HTTP/HTTPS, pesquise, edite ou exclua. Até 100 registros. Duplicatas exatas de URL são recusadas. Não são consultados favicons, páginas ou metadados externos. O armazenamento usa `%LOCALAPPDATA%/Aeris/bookmarks.bin`, protegido por DPAPI, separado do Vault. Use somente exemplos; a validação de formato não atesta segurança de sites.

Para abrir um link salvo, conceda Bookmarks → Navegador em Permissões e confirme o endereço a cada abertura. O Windows encaminha o endereço ao aplicativo padrão associado ao protocolo. Nenhum navegador foi acionado nos testes. Não há abertura automática, nem suporte a esquemas file, javascript, data ou URLs com credenciais. Não são feitas importação, sincronização, exportação ou indexação de links pelo Search. Bloquear, fechar, desativar ou limpar a sessão descarta rascunhos e preserva registros gravados. Autorizações expiram ao encerrar; desativação e limpeza também revogam o acesso.

Backup está integrado. Validação Windows e instalador continuam pendentes.

## Backup (0.2.0a5)

Ative Backup pelo catálogo, abra pelo Hub ou Spotlight e conceda as permissões de criação e restauração separadamente. Bloqueie Vault e Bookmarks antes de exportar ou restaurar. Escolha um novo arquivo `.aerisbackup` para exportar os blobs protegidos existentes e as preferências de aparência. O formato contém SHA-256 por item para detectar corrupção acidental, não assinatura de autenticidade. A aparência é legível, não criptografada; as informações do Vault, Bookmarks e sete módulos Storage continuam no formato DPAPI original.

Selecione um backup, confira os itens e restaure um por vez. A restauração de registros valida DPAPI e a estrutura antes de substituir o arquivo; se já houver um arquivo, cria uma cópia local de recuperação `.recovery-*.bin` para Vault/Bookmarks (recuperação manual orientada) ou `.previous.bin` para Storage (recuperação na sessão via Privacy). A restauração da aparência não altera flags de módulos nem permissões. Capture, Snippets, Clipboard, rascunhos e permissões de sessão não são exportados. Não há backup automático ou sincronização. Guarde cópias em local confiável; DPAPI normalmente depende da conta e do ambiente Windows original, não é solução de recuperação portátil.

Validação a5: execute `py -3 -m unittest discover -v` e `py -3 -m tests.smoke_backup` dentro de desktop. Testes em Linux com backend fictício não comprovam criptografia real ou compatibilidade Windows. Use dados fictícios.

## Translate (0.3.0a1)

Ative Translate e abra pelo Hub ou Spotlight. O guia incluído contém 12 frases em português, inglês e espanhol, com correspondência exata normalizada; não traduz textos arbitrários. Escolha uma frase na lista ou digite uma das frases conhecidas. O modo Modelo local é experimental: utiliza Argos Translate opcional e modelos previamente instalados, em processo filho com limite de 90 segundos. Não instala pacotes, não possui fallback remoto e bloqueia operações de socket Python no processo filho (não é sandbox de rede do SO). Se faltarem recursos locais, falha sem apresentar tradução inventada.

Para preparar o motor opcional, consulte https://argos-translate.readthedocs.io/en/latest/source/troubleshooting.html e https://argos-translate.readthedocs.io/en/latest/source/examples.html fora do Aeris, em ambiente Python compatível. Instale somente pacotes/modelos de fontes confiáveis; o setup pode exigir internet e recursos de segmentação. O núcleo segue sem dependências externas; a compatibilidade, qualidade, licenças de modelos, tamanho e consumo do motor opcional ainda precisam ser verificados. Não há modelos incluídos no ZIP.

Entrada máxima 4.000 caracteres; resultado em memória; limpar/fechar/desativar cancela o processo e descarta textos. Copiar tradução requer Translate → Clipboard e confirmação. Não há indexação pelo Search. A limpeza não apaga cópias no clipboard do sistema. Use dados fictícios; não é apagamento seguro. Testes: 63 unitários aprovados, dois ignorados (Windows), nove gráficos em Linux. Motor real Argos não instalado/testado; apenas o guia e o retorno de falha sem motor foram verificados. Próximo: Voice.

## Text (0.3.0a3)

Ative Text no catálogo. Use as seis operações locais com prévia, contagem de caracteres, palavras e linhas. A entrada original permanece inalterada. Copiar requer autorização Text → Clipboard e confirmação. Não há correção gramatical por IA; cuidado com indentação e formatação. Preferências migradas para esquema 13.

AI Companion integra a edição única sem cobrança do Aeris; cliente Ollama local, ditado e síntese Windows experimentais. Veja docs/ai-companion-concept.md. Modelo e recursos de voz não incluídos; validação real pendente.

## Validação mais recente — a3

74 testes unitários aprovados, 3 ignorados por exigir Windows; 11 testes gráficos em Linux/Xvfb aprovados. Windows 10/11 e motores nativos ainda não validados.

## Email (0.3.0a4)

Ative Email no catálogo. Escolha português, inglês ou espanhol; tom formal ou direto; solicitação, acompanhamento, agradecimento ou atualização. Informe detalhes fictícios no idioma escolhido, nome, assunto e assinatura opcionais. Gere e revise o rascunho. Copie assunto e corpo separadamente com autorização Email → Clipboard e confirmação. A edição de qualquer campo invalida a prévia. Os dados ficam somente na janela e são descartados ao limpar, fechar, desativar ou encerrar. O clipboard pode manter cópias. Não há envio, leitura de caixa postal, tradução dos detalhes, conta, IA ou conexão com serviço de e-mail. Preferências no esquema 14.

Validação a4: 80 testes unitários aprovados, três reservados para Windows, 12 testes gráficos aprovados em Linux/Xvfb. Próximo: Pronounce.

## Pronounce (0.3.0a5)

Ative Pronounce no catálogo e autorize Pronounce → Áudio na central de permissões. Selecione português, inglês ou espanhol, uma frase de exemplo ou escreva até 500 caracteres fictícios. Liste as vozes instaladas do idioma e selecione uma voz compatível; sem voz adequada a reprodução não é iniciada. Ajuste velocidade, volume e de uma a cinco repetições, com pausa de 700 ms entre leituras. Parar, trocar idioma, fechar, desativar, limpar sessão ou revogar a permissão interrompe o processo. A voz usa o motor compartilhado System.Speech; não há microfone, gravação, transcrição ou avaliação da fala. A autorização é independente de Voice. As preferências migram para o esquema 15 e os painéis de ferramentas e permissões ganharam rolagem.

Validação a5: 85 testes unitários aprovados, 3 ignorados por dependerem do Windows e 13 testes gráficos aprovados em Linux/Xvfb, incluindo simuladores de síntese de voz. A reprodução real, a filtragem de vozes por cultura e a repetição exigem validação em Windows 10/11. Próximo: Smart Automation / Autofill.

## Autofill (0.4.0a1)

Ative Autofill no catálogo e abra pelo Hub ou Spotlight. Desbloqueie, cadastre um perfil fictício, salve, selecione os campos e revise. Copiar um campo exige autorização Autofill → Clipboard por sessão e confirmação. A colagem é manual. Campos permitidos: nome completo, e-mail, telefone, empresa e cargo; não insira senhas, dados bancários, documentos ou informações pessoais reais nesta pré-alpha. Até 100 perfis, 250 caracteres por campo. O arquivo autofill.bin usa o mesmo backend DPAPI do Vault, mas é separado e não está incluído no Backup desta versão. A limpeza de sessão, fechamento e desativação bloqueiam os perfis; não equivalem a apagamento seguro de memória. A integração contextual com navegadores e a extensão Chromium ainda não existem. Esquema 16 de preferências.

Validação local: 90 testes unitários aprovados, 3 testes nativos Windows ignorados, 14 testes gráficos em Linux/Xvfb aprovados. DPAPI e clipboard real no Windows ainda precisam de validação. Nenhuma alteração publicada no GitHub.

Aeris Text: correção ortográfica e gramatical automática passa a ser requisito de produto; ver docs/text.md. Este era o estado histórico; a v0.11.0a4 inclui revisão por regras e modo automático opt-in (ver seção final).

## Expand (0.4.0a2)

Ative Expand no Hub e abra pelo catálogo ou Spotlight. Crie abreviações como `;att`, edite ou exclua regras e digite um texto no editor. Clique em Expandir e revisar; o original permanece intacto. Para copiar, conceda Expand → Clipboard nesta sessão e confirme. Regras personalizadas e textos ficam em memória; ao fechar a janela, regras salvas permanecem até encerrar o aplicativo, desativar o módulo ou limpar a sessão. As três regras de exemplo são recriadas ao abrir um novo armazenamento. Sem monitoramento de teclado ou expansão em aplicativos externos. Preferências em esquema 17; leitura compatível com esquemas anteriores.

Validação a2: 95 testes unitários aprovados, 3 específicos do Windows ignorados e 15 testes gráficos aprovados em Linux/Xvfb. Windows 10/11 e desempenho real pendentes. Próximo: Bridge.

## Bridge (0.4.0a3)

Ative Bridge e os módulos envolvidos no catálogo. Na central de permissões, autorize somente os acessos desejados: importar Capture, importar Snippets, executar fluxos, criar anotação no Capture ou copiar a prévia. A fonte padrão é Manual; para importar, selecione uma fonte ativa, liste seus registros e confirme a seleção. Execute e revise a prévia antes de copiar ou salvar.

Fluxos disponíveis: Expand → Text (expansão seguida de remoção de espaços excedentes); Translate → Email (guia integrado de frases, seguido de modelo formal de atualização no idioma de destino); Text → Capture (remoção de espaços, criação explícita de nova anotação). Os fluxos são fixos, não executam comandos, não enviam mensagens e não acionam voz. Não utilizam Argos ou correção gramatical automática. O motor de integração não é uma sandbox.

Entradas e prévias em memória; importações são cópias explícitas dos registros salvos, não sincronizações. Revogar leitura limpa a entrada importada; alterar permissões invalida prévias. Desativar módulo participante fecha Bridge e revoga permissões do Bridge. Limpar sessão fecha a janela e revoga permissões. Uma anotação salva deliberadamente no Capture permanece na sessão até ser apagada, e o clipboard pode reter cópias. Limpeza lógica não equivale a apagamento seguro. Preferências esquema 18, compatível com anteriores.

Validação a3: 101 testes unitários aprovados, 3 ignorados por dependerem de Windows, 16 testes gráficos em Linux/Xvfb aprovados. Windows, DPI e desempenho ainda não validados. Próximo: Routine. Nenhuma publicação nesta etapa.

## Routine (v0.4.0a4)

Crie até 30 sequências temporárias de uma a cinco etapas no Routine. Ative Bridge e os módulos participantes e conceda Routine → Executar e Bridge → Executar. Copie a prévia somente com autorização e confirmação. Sem agendamento, shell, envio ou gravação automática. Consulte `../docs/routine.md`.

Validação a4: 107 testes unitários aprovados, 3 ignorados por exigir Windows e 17 testes gráficos aprovados em Linux/Xvfb. Windows e desempenho permanecem pendentes.

## Workspace (v0.4.0a5)

Ative Workspace no Hub. Crie até 20 ambientes temporários, com ferramentas do catálogo já implementadas e até oito links HTTP/HTTPS por ambiente. Salve e selecione Ativar salvo para filtrar o painel rápido e Spotlight; somente módulos previamente ativados são exibidos, e Workspace permanece disponível para sair do filtro. Enquanto um ambiente estiver ativo, seu filtro prevalece sobre os favoritos gerais; nenhuma preferência é sobrescrita. Selecione uma ferramenta ou link salvo para abrir individualmente. Links exigem Workspace → Navegador e confirmação, usando o navegador padrão do Windows. Não abre nada automaticamente ao ativar. Não há execução de comandos, restauração de janelas do sistema, agendamento ou armazenamento permanente. Desativar Workspace, limpar a sessão ou encerrar descarta os ambientes. Preferências gerais em esquema 20, compatível com anteriores. Use dados fictícios.

Validação a5: 112 testes unitários aprovados, 3 ignorados por exigir Windows e 18 testes gráficos aprovados em Linux/Xvfb. Abertura de links simulada; Windows, DPI e desempenho pendentes. Próximo: Digital Security — Privacy.

## Privacy (v0.5.0a1)

Central sempre disponível pelo botão Privacidade ou pelo catálogo, independentemente dos módulos ativos. Inventário parcial de presença dos quatro arquivos conhecidos, sem leitura de conteúdo; contagem de itens de seis stores em memória; estado dos três cofres e das 23 permissões de sessão. Atualize manualmente quando necessário. Permite revogar acessos, bloquear cofres com confirmação, ocultar Spotlight e limpar a sessão. A limpeza agora inclui consulta do Hub, janela Backup e texto de mascaramento; preserva registros protegidos e clipboard do sistema. Não é apagamento seguro.

Mascaramento de até 20.000 caracteres de texto colado ou digitado, sob demanda, preservando o original e gerando prévia separada. Reconhece padrões de e-mail, CPF/CNPJ numéricos formatados e telefone BR formatado. Não valida dígitos verificadores, não cobre todos os formatos nem todos os dados pessoais, e não garante anonimização. Sem inspeção automática de outros programas, sem rede e sem persistência do texto pelo módulo. Use somente dados fictícios.

Validação a1: 117 testes unitários aprovados, 3 ignorados por exigir Windows, 19 testes gráficos aprovados em Linux/Xvfb. Inventário, bloqueio, revogação, mascaramento e descarte testados; validação Windows e desempenho pendentes. Próximo: Link.

## Link (v0.5.0a2)

Análise manual de URLs HTTP/HTTPS sem visitar endereços, com indicação de host interpretado e alertas estruturais. Não é verificação de reputação nem garantia de segurança. Nenhuma informação é persistida pelo módulo. Consulte `../docs/link.md`.

Validação a2: 124 testes unitários aprovados, 3 ignorados (Windows), 20 testes gráficos aprovados em Linux/Xvfb. Próximo: Verify.

## Verify (v0.5.0a3)

Ative Verify e autorize Verify → Ler arquivo na sessão. Escolha um arquivo local, SHA-256 ou SHA-512 e opcionalmente informe o digest esperado. Confirme a leitura. A operação usa blocos de 1 MiB em thread separada, com cancelamento cooperativo e descarte ao revogar, fechar ou desativar. Não altera o conteúdo, não executa o arquivo e não guarda histórico. Correspondência de hashes não comprova autenticidade ou ausência de malware. O Windows e suas verificações de caminhos ainda não foram testados. Consulte `../docs/verify.md` na raiz do pacote.

Validação a3: 130 testes unitários aprovados, 3 ignorados por exigir Windows, 21 testes gráficos em Linux/Xvfb. Próximo: Metadata.

## Metadata (v0.5.0a4)

Ative Metadata e conceda Metadata → Ler arquivo em Permissões. Escolha um arquivo local fictício e confirme a inspeção. PNG: dimensões e campos tEXt pequenos; JPEG: dimensões, comentários e campos EXIF ASCII selecionados, presença de referência GPS; Office: propriedades principais de DOCX/XLSX/PPTX. O relatório é parcial, temporário e não altera o original. Limite de 32 MiB por arquivo, 40 campos e 500 caracteres por valor. A leitura ocorre sob demanda em thread separada, com cancelamento cooperativo e descarte por revogação. Não há remoção de metadados, leitura de PDF, validação de imagens, decodificação de coordenadas ou análise completa de conteúdo. Consulte `../docs/metadata.md` na raiz.

Validação a4: 137 testes unitários aprovados, 3 ignorados por exigir Windows e 22 testes gráficos aprovados em Linux/Xvfb. Arquivos sintéticos; ainda não há validação em Windows ou corpus amplo de documentos reais. Próximo: Health.

## Health (v0.5.0a5)

Ative Health no catálogo, abra a ferramenta e clique em Medir. Uma amostra de aproximadamente dois segundos informa CPU do processo (100% = um núcleo lógico), memória residente atual e módulos opcionais ativos. Não mede processos filhos, memória privada, consumo de sistema ou latência de atalhos. Sem monitoramento residente, persistência de resultados ou rede. Cancelar, desativar, fechar e limpar sessão cancelam a amostra. Windows usa GetProcessMemoryInfo; Linux usa /proc/self/statm. A execução nativa Windows ainda não foi testada.

Validação: 143 testes unitários executáveis e 23 smoke tests gráficos aprovados em Linux; quatro testes Windows ignorados. Diagnóstico preliminar limpo Linux/Xvfb, Python 3.13.5 com -S: três amostras de ~2 s por condição. Hub: 26,50–26,53 MiB e 0,111–0,184% de um núcleo; Hub + Health: 26,55 MiB e 0,084–0,151%. O processo de smoke test com ambiente Python padrão apresentou ~112 MiB, incluindo infraestrutura do teste/ambiente; não representa a execução limpa. Não há comprovação das metas no Windows. Consulte docs/health.md e docs/health-baseline-linux.json na raiz. Próxima fase: File Intelligence (Documents).

## Documents (v0.6.0a1)

Ative Documents no catálogo. Autorize Documents → Ler arquivo, selecione um arquivo fictício em unidade local fixa e confirme a extração. TXT, MD e CSV são tratados como texto bruto (UTF-8, UTF-8 com BOM ou UTF-16 com BOM; até 1 MiB). DOCX: extração parcial do corpo Word (até 8 MiB de pacote e 1 MiB de XML principal). A prévia tem até 100.000 caracteres e contagens referentes somente à prévia. Sem renderização, macros, fórmulas, abertura de links, edição ou gravação do original. Cancelamento cooperativo; revogação/limpeza descarta o caminho e a prévia. Não há exportação ou integração automática com outras ferramentas. Não use para redigir ou sanitizar documentos. PDF, OCR, XLSX/PPTX e extração integral de Word estão pendentes. Veja `../docs/documents.md` no pacote.

## Organizer (v0.6.0a2)

Ative Organizer e autorize Organizer → Listar pasta. Selecione uma pasta fictícia e confirme a análise. Classificação por extensão (sete categorias), tamanho lógico em bytes e totais por categoria. Lista até 2.000 entradas diretas, incluindo as ignoradas; não percorre subpastas, não lê conteúdo, não cria pastas, não move nem exclui arquivos. Prévia temporária, cancelamento cooperativo e descarte após revogação ou limpeza. Veja `../docs/organizer.md` na raiz. Validação Linux: 156 testes unitários aprovados, quatro ignorados por exigir Windows e 25 smoke tests gráficos aprovados. Próximo: Drop.

## Drop (v0.6.0a3)

Ative Drop, autorize Drop → Adicionar, selecione até 100 arquivos fictícios e confirme. A prateleira contém caminhos, tamanhos na seleção e categoria por extensão; não lê nem duplica conteúdo. Selecione itens para remover referências ou copiar caminhos como texto mediante permissão separada e confirmação. Fechar mantém referências na sessão; revogar Adicionar, desativar, limpar sessão ou encerrar descarta a lista. Sem arraste, movimentação, abertura ou integração direta com outros módulos nesta versão. Caminhos podem ficar desatualizados; cópias no clipboard podem permanecer. Veja `../docs/drop.md` na raiz. Validação Linux: 162 unitários e 26 gráficos aprovados, quatro testes Windows ignorados. Próximo: Compare.


## Compare (v0.6.0a4)

Ative Compare no catálogo. Compare dois textos inseridos manualmente ou dois arquivos locais fictícios (TXT, MD, CSV, DOCX). Para arquivos, conceda Compare → Ler arquivos, selecione ambos e confirme. O motor reutiliza Documents e `difflib.SequenceMatcher`, preserva espaços, normaliza CRLF/CR para LF, distingue ausência de quebra final e mostra números de linha e totais de mantidas, removidas e adicionadas. Até 100.000 caracteres e 2.000 linhas por lado; extração truncada é recusada. DOCX é parcial e CSV é texto bruto. Não compara bytes, formatação, imagens, fórmulas ou significado. Nenhum arquivo é escrito; processamento em thread sob demanda e cancelamento cooperativo, que pode aguardar a etapa de diff. Limpar, fechar, desativar ou revogar leitura descarta os dados correspondentes. Consulte `../docs/compare.md` na raiz. Validação Linux: 169 unitários executáveis aprovados, quatro ignorados por exigir Windows, 27 smoke tests gráficos aprovados. Próximo: Lens.


## Lens (v0.6.0a5)

OCR local opcional com Tesseract 5.x. Ative Lens, autorize Lens → Ler imagem, selecione PNG/JPEG fictício, escolha português, inglês ou espanhol e confirme. Limites de 8 MiB, 12 megapixels declarados, 12.000 pixels por dimensão, 30 s de OCR e 100.000 caracteres na prévia. Motor externo não incluso, sem instalação ou download automático. Cancelamento encerra o subprocesso de forma cooperativa e revogação descarta a prévia. Consulte `../docs/lens.md` na raiz para configuração, limitações e resultados reais em Linux. 175 testes unitários e 28 gráficos aprovados, quatro testes Windows pendentes. A fase File Intelligence tem cinco protótipos; próxima fase: Daily Productivity (Focus).

## Focus (v0.7.0a1)

Ative Focus no catálogo e abra pelo Hub, Spotlight ou Workspace. Escolha Concentração (25 min sugeridos) ou Intervalo (5 min sugeridos), ajuste entre 1 e 120 minutos, inicie, pause, retome ou reinicie. A conclusão apresenta estado visual e, opcionalmente, sinal sonoro do Tk mediante seleção explícita na janela. Não há transição automática entre modos. O relógio monotônico determina o tempo restante; uma atualização Tk de 250 ms é programada apenas enquanto a contagem está ativa. Fechar a janela pausa a contagem; reabrir permite retomar. Minimizar não pausa. Desativar Focus, limpar a sessão ou encerrar descarta a contagem e os totais. Nenhuma atividade ou conteúdo do computador é monitorado; sem gravação em disco de sessões, rede ou serviço residente. O inventário de privacidade não inclui os contadores de Focus. O comportamento em suspensão e o sinal sonoro dependem da plataforma e precisam de validação Windows. Consulte `../docs/focus.md` na raiz. Validação: 181 testes unitários executáveis, 29 gráficos em Linux; quatro testes nativos Windows ignorados. Próxima ferramenta: Checklist.


## Checklist (v0.7.0a2)

Ative Checklist no catálogo e abra pelo Hub, Spotlight ou Workspace. Digite o nome da lista ao lado do seletor e escolha Criar. Selecione uma lista para adicionar tarefas (até 200 caracteres), com prioridade Baixa, Normal ou Alta. Selecione uma tarefa para editar, alternar sua conclusão ou excluir. Os filtros Todas, Pendentes e Concluídas não alteram a contagem global da lista. Até 20 listas e 100 tarefas por lista. Renomear mantém as tarefas; excluir uma lista exige confirmação. As listas permanecem na memória ao fechar a janela, mas são descartadas ao desativar o módulo, limpar a sessão ou encerrar. Privacy contabiliza tarefas, sem mostrar seu conteúdo no inventário. Somente preferências não sensíveis são persistidas (esquema 31). Sem prazos, lembretes, sincronização, integração direta com Focus ou armazenamento permanente. Consulte `../docs/checklist.md`. Validação em Linux: 187 testes unitários executáveis e 30 gráficos; quatro testes Windows ignorados. Próxima ferramenta: Reminder.


## Reminder (v0.7.0a3)

Ative Reminder e crie lembretes relativos de 1 a 10.080 minutos, com descrição e alerta visual genérico opcional. Até 100 registros de sessão; reprogramação, cancelamento e exclusão. Fechar a janela mantém o agendamento enquanto o Aeris estiver aberto. Desativar, limpar sessão ou encerrar cancela e descarta os registros. Sem integração de calendário, datas absolutas, recorrência, armazenamento permanente ou serviço adicional. Consulte `../docs/reminder.md`. Validação Linux: 193 testes unitários executáveis e 31 gráficos aprovados; quatro testes Windows ignorados. Comandos de voz foram registrados como requisito futuro em `../docs/ai-companion-concept.md`; não implementados. Próxima ferramenta: Ideas.


## Ideas (v0.7.0a4)

Ative Ideas no catálogo e abra pelo Hub, Spotlight ou Workspace. Cadastre título (160 caracteres), categoria personalizada (60), descrição opcional (4.000) e estado Nova, Em desenvolvimento, Concluída ou Arquivada. Até 200 ideias por sessão. Pesquise título, categoria e descrição sem distinção de acentos ou maiúsculas; filtre por estado. Abra uma ideia para editar ou excluir mediante confirmação. Fechar a janela preserva registros salvos na memória, mas rascunhos não salvos exigem confirmação de descarte. Desativar, limpar a sessão ou encerrar descarta os dados. Privacy contabiliza registros; não há gravação de conteúdo, pesquisa global, integração por voz ou serviço adicional. Consulte `../docs/ideas.md`. Validação Linux: 199 testes unitários executáveis e 32 gráficos aprovados; quatro testes Windows ignorados. Próxima ferramenta: Timeline.

## Timeline (v0.7.0a5)

Ative Timeline no catálogo. Registre voluntariamente uma atividade com data/hora local no formato AAAA-MM-DD HH:MM, título, categoria e descrição opcional. Até 300 registros em memória, ordenados do mais recente ao mais antigo. Pesquise texto, filtre categoria exata sem distinção de acentos e defina um intervalo inclusivo de datas. Edite ou exclua registros selecionados; a exclusão e o descarte de rascunhos exigem confirmação. Fechar a janela mantém os registros salvos nesta sessão. Desativar o módulo, limpar sessão ou encerrar descarta todos os registros. O Privacy inclui a contagem sem expor conteúdo. Nenhum evento é capturado automaticamente; integrações com Focus, Checklist, Ideas, Reminder e AI Companion permanecem planejadas. Não há persistência, notificações, exportação ou normalização de fusos.


## Data (v0.8.0a1)

Ative Data, autorize Data → Ler CSV, escolha um CSV fictício, selecione separadores de campo e decimal e confirme. Perfil de qualidade com ausentes, duplicatas exatas, distintos e inferência numérica com mínimo, máximo e média. Até 1 MiB, 5.000 registros, 50 colunas e 100.000 células; falhas ou limites rejeitam o arquivo. Somente leitura, sem exportação ou limpeza automática. Relatório temporário descartado ao revogar, fechar, desativar ou limpar sessão. Veja `../docs/data.md`. Próxima ferramenta: Dashboard.

## Dashboard (v0.8.0a2)

Ative Dashboard e autorize Dashboard → Ler CSV na sessão. Selecione CSV, configure separadores, confirme a leitura e selecione categoria, agregação e métrica numérica. Contagem, soma e média; até 100 categorias válidas, gráfico e relatório das 12 maiores por valor decrescente, total global de todas. Registros sem categoria ou métrica necessária são ignorados e contabilizados; duplicatas mantidas. Média global por registro, não média das médias. Dados em memória, descartados ao limpar, revogar, fechar ou desativar. Consulte docs/dashboard.md (na raiz). Sem exportação, XLSX, SQL ou edição dos arquivos.

## Report (v0.8.0a3)

Ative Report, autorize a leitura de CSV e confirme a análise. Prévia textual de qualidade, estatísticas e agregações opcionais por categoria, reutilizando Data e Dashboard. Cópia mediante permissão separada e confirmação; o clipboard pode reter dados. Resultados temporários, sem alteração do CSV ou exportação de arquivo. Consulte `../docs/report.md`. Exemplo gerado em `docs/report-example.txt` (raiz). Próxima ferramenta: Calculator.


## Calculator (v0.8.0a4)

Ative Calculator no catálogo. Calcule expressões aritméticas, raízes, logaritmos, margem, markup, juros compostos, média, mediana e desvio padrão populacional. Decimal com 34 dígitos de precisão; operadores permitidos explicitamente, sem execução arbitrária de código. Use ponto ou vírgula decimal, sem separadores de milhares; listas separadas por ponto e vírgula. Entradas e resultados temporários, descartados ao fechar, limpar ou desativar. Consulte `../docs/calculator.md` para limites e fórmulas. Próxima ferramenta: Convert.

## Convert (v0.8.0a5)

Ative Convert no catálogo. Conversões locais em dez categorias, com fatores racionais e resultado Decimal de 34 dígitos significativos. Temperaturas absolutas, MB decimal e MiB binário. Entradas temporárias, sem rede ou arquivos. Consulte `../docs/convert.md`. Business Intelligence em protótipo; próxima fase de entrega: Learning & Research, iniciando por Learn.

## Learn (v0.9.0a1)

Ative Learn no catálogo. Crie trilhas, tópicos e estimativas de duração, reordene e marque conclusões. Progresso por tópicos e minutos estimados, sem monitoramento; cópia protegida manual disponível em Privacy. Consulte `../docs/learn.md`. Próxima ferramenta: Research.


## Research (v0.9.0a2)

Ative Research para cadastrar referências e notas, agrupadas por nome de projeto. Pesquise por texto, filtre por projeto e estado de leitura. Prévia bibliográfica descritiva sem inventar autoria ou ano; sem consulta externa e sem conformidade ABNT/APA. Registros temporários, descartados ao limpar a sessão, desativar com confirmação ou encerrar. Consulte `docs/research.md` na raiz. Próxima ferramenta: Flashcards.

## Flashcards (v0.9.0a3)

Ative Flashcards no catálogo. Cadastre até 500 cartões em baralhos por nome, pesquise por pergunta/resposta e filtre cartões disponíveis. Revele a resposta antes de avaliar. Difícil: 10 minutos; Médio: mínimo de 1 dia ou dobro do intervalo anterior; Fácil: mínimo de 3 dias ou triplo do intervalo anterior; máximo de 365 dias. Alterar pergunta ou resposta reinicia o progresso. Registros e prazos ficam em memória; desde v0.11.0a2, podem ser preservados por cópia protegida manual em Privacy. Consulte `docs/flashcards.md` na raiz. Próxima ferramenta: Accessibility.

## Accessibility (v0.9.0a4)

Ative Accessibility no catálogo. Digite ou cole texto fictício e selecione Preparar leitura (Ctrl+Enter). A prévia aceita até 20.000 caracteres, tamanho de 12–30 pontos, contraste Natural, Escuro ou Alto contraste, espaçamento ampliado e guia por linha lógica (Alt+↑/↓). Tab e Shift+Tab percorrem controles, inclusive nos campos de texto. A paleta do leitor é independente do tema geral. Texto e opções de leitura são temporários; fechar, desativar ou limpar a sessão descarta o conteúdo. Sem leitura automática da tela, microfone ou alteração das configurações do Windows. Consulte `docs/accessibility.md` na raiz. Próxima ferramenta: Decision.

## Decision (v0.9.0a5)

Ative Decision e preencha uma matriz de 2–6 critérios e 2–6 alternativas, pesos de 0–100 e notas de 0–10 (maior é melhor). A soma dos pesos não precisa ser 100, mas deve ser positiva. Clique em Calcular ranking: média ponderada com aritmética racional exata, empates com posição compartilhada e exibição em quatro casas decimais. Editar invalida o ranking. Redimensionar preserva campos que permanecem e pede confirmação antes de reduzir uma matriz preenchida. Dados temporários descartados ao fechar, limpar ou desativar; sem persistência, IA ou rede. Consulte `../docs/decision.md`. Validação Linux: 270 testes unitários executáveis e 43 gráficos aprovados, quatro testes Windows ignorados. Learning & Research consolidada; próxima fase: Intelligent Assistance — Copilot.

## Copilot (v0.10.0a1)

Interpretador local por regras de comandos em português: Reminder (inclusive hoje/amanhã HH:MM), Checklist (lista existente), Focus e Ideas. Ative os módulos, conceda Copilot → Executar, prepare a prévia e confirme cada ação. O motor de comandos não usa IA, microfone ou rede diretamente; o Companion opcional é acessível pela janela Copilot. Dados temporários; não cria eventos em calendários externos. Consulte `../docs/copilot.md`. Validação Linux: 278 testes unitários aprovados, 4 ignorados por Windows, 44 scripts gráficos aprovados. Próxima ferramenta: Context.

## Context (v0.10.0a2)

Registros manuais e temporários, com cinco categorias, até 50 itens e autorização individual de inclusão em prévia local. A permissão Context → Prévia é negada por padrão; alterar um registro revoga sua inclusão; revogar a permissão limpa seleções mesmo com a janela fechada. Nenhum envio ao Copilot, IA ou rede. Consulte `../docs/context.md`. Validação Linux: 284 testes unitários aprovados, 4 ignorados por Windows, 45 scripts gráficos aprovados. Próxima ferramenta: Interview.


## Interview (v0.10.0a3)

Treinamento individual offline: 12 perguntas fixas em quatro áreas, orientações de estudo, respostas de até 4.000 caracteres e quatro critérios de autoavaliação voluntária. Respostas salvas permanecem em memória durante a sessão; sem IA, microfone ou assistência oculta em entrevistas reais. Consulte `../docs/interview.md`. Validação Linux: 290 testes unitários aprovados, 4 ignorados por Windows, 46 scripts gráficos aprovados. Próxima ferramenta: Debug.


## Debug (v0.10.0a4)

Ative Debug, informe código Python fictício e selecione Analisar. Diagnósticos de sintaxe e escopo com linha, coluna e sugestões; três avisos heurísticos (except sem tipo, importação com asterisco e valores padrão mutáveis literais). Nenhum código é executado ou importado. Limite de 20.000 caracteres, 1.000 linhas, 8.000 nós AST e profundidade 100. Código e diagnósticos temporários. Consulte `../docs/debug.md`. Validação Linux: 297 testes unitários aprovados, 4 ignorados por Windows, 47 scripts gráficos aprovados. Próxima ferramenta: Meeting.


## Meeting (v0.10.0a5)

Ative Meeting para criar até 50 reuniões por sessão, com título, data opcional, participantes, pauta, anotações e decisões. Cada reunião aceita até 50 atividades com responsável, prazo opcional e estado de conclusão. Salve a reunião antes de gerar a prévia da ata. O botão de cópia exige permissão Meeting → Clipboard e confirmação individual; o histórico do sistema pode reter cópias. Fechar a janela preserva registros na sessão. Desativar, limpar sessão ou encerrar descarta os registros em memória; cópias protegidas manuais permanecem. Não grava áudio/vídeo nem acessa calendários. Consulte `../docs/meeting.md` e `../docs/consolidation-roadmap.md`.

Marco: 50/50 ferramentas do catálogo inicial em protótipo. Regressão Linux: 303 testes unitários aprovados, 4 ignorados por exigir Windows, 48 scripts gráficos aprovados. Não é versão estável nem instalador. Próxima etapa: consolidação de segurança, persistência protegida, assistência textual e desempenho.

## Protected Storage (v0.11.0a3)

Privacy → Cópias protegidas permite salvar, restaurar e excluir snapshots manuais de Checklist, Ideas, Learn, Meeting, Research, Flashcards e Reminder usando DPAPI do usuário Windows, com permissões separadas e confirmação. Até v0.11.0a8 não havia persistência automática; veja a seção Protected Storage IV. Feche a ferramenta e Copilot antes de restaurar. Datas UTC dos cartões e horários absolutos dos lembretes são preservados; lembretes vencidos não repetem alertas. A limpeza de sessão preserva os arquivos e descarta as alterações não copiadas. Sem fallback em texto claro; não use dados reais antes dos testes nativos e da revisão de segurança. Backup inclui as sete cópias atuais desde v0.11.0a3. Consulte [`Protected Storage`](../docs/protected-storage.md) para limitações e procedimentos.


## Protected Storage III e AI Companion

Privacy permite preservar e recuperar uma versão anterior de cada snapshot manual; Backup inclui as sete cópias atuais protegidas mediante confirmação. Sem autosave. Consulte `docs/protected-storage.md` e `docs/ai-companion-concept.md` na raiz. Companion é parte da edição única, acessível pelo Copilot. Não instala modelo automaticamente. A validação do modelo real e da voz no Windows permanece pendente.

## Intelligent Text (v0.11.0a4)

Ative Text e selecione Português (BR), English ou Español. Desligado é o padrão; Revisar agora gera prévia sob demanda. Sugerir gera prévia 450 ms após edição; Automático aplica somente substituições ortográficas de palavras completas e mantém regras gramaticais como sugestões. Aplicar revisão substitui o texto pela prévia atual; Desfazer revisão recupera a alteração mais recente enquanto o texto não tiver mudado e desliga o modo automático. Ctrl+Z é o histórico do editor; desligue o modo automático antes de desfazer edições antigas. Não há corretor linguístico completo nem acesso a outros aplicativos; nomes, termos técnicos e contexto podem produzir falsos positivos. Nenhuma rede, modelo de IA ou persistência é usada pelo Text. Consulte a documentação `docs/text.md` na raiz.


## Integration Engine I (v0.11.0a5)

Meeting → Checklist e Meeting → Reminder: transfira uma atividade pendente salva, com permissão de sessão, destino explícito, prévia e confirmação. O título vira tarefa de prioridade Normal ou lembrete na data e horário escolhidos (até sete dias). Sem sincronização automática ou persistência implícita. Ver documentação `docs/integration-engine.md`.

## Integration Engine II (v0.11.0a6)

Learn → Flashcards e Research → Learn: transferências individuais mediante permissão, prévia e confirmação. Copilot aceita prefixo Aeris e horários 14h/14h30. Sem sincronização automática ou execução de respostas da IA. Consulte ../docs/study-integration.md.

## Eco Engine I (v0.11.0a7)

O Companion não consulta sua fila de resultados enquanto ocioso. Durante uma operação, consulta a cada 100 ms; após conclusão, para. Cancelamentos invalidam resultados atrasados e destruir a janela cancela o callback. Benchmark Linux/Xvfb sem inferência: três amostras de dois segundos com Hub + Copilot + Companion ociosos; média de CPU de 0,347% para 0,017% de um núcleo, 20 para zero callbacks por amostra. Amostra curta, não garante economia de bateria, consumo Windows ou cumprimento das metas de memória. Consulte `../docs/eco-engine.md`.

## Eco Engine II (v0.11.0a8)

Liberação de referências de janelas fechadas, remoção de callbacks Tcl estáticos e limpeza de callbacks de campos dinâmicos no Calculator e Decision. Os registros confirmados permanecem na sessão. Em 3 processos por versão, com 65 aberturas e fechamentos por processo, os objetos retidos após GC caíram de 61 para zero; RSS não apresentou melhora demonstrável. Consulte `../docs/eco-engine-ii.md`. Windows ainda não validado.

## Protected Storage IV (v0.11.0a9)

Privacy → Automático: autorize Storage → Salvar e Storage → Automático em Permissões, abra uma das sete ferramentas com registros fictícios e ative o salvamento para ela individualmente. A autorização expira na sessão. A cada 10 s, apenas módulos autorizados são consultados; alterações confirmadas são copiadas com DPAPI e versão anterior. Nenhum rascunho é copiado. Cópia divergente exige reconciliação manual antes de ativar. Sessão vazia, falha de gravação ou conflito externo interrompem a operação; revogação, desativação, limpeza e operações manuais desarmam o módulo conforme aplicável. Não há salvamento final ao encerrar: use Salvar alterações agora antes de sair. Não há restauração automática. 352 testes unitários e 56 gráficos executáveis passaram em Linux; cinco testes Windows ignorados. O backend simulado não comprova criptografia real. Consulte a documentação protected-storage.md.

## Intelligent Text II (v0.11.0a10)

61 substituições ortográficas e seis regras de concordância ilustrativas. Dicionário de exclusão por idioma (até 100 palavras), temporário na janela, apenas para as regras locais. Original e prévia destacam trechos modificados. A revisão contextual usa Text → Revisão por IA local, confirmação explícita e modelo Ollama instalado separadamente (desative cloud). Limite de 1.200 caracteres no original; bloqueia padrões técnicos reconhecidos; não envia histórico, outros módulos ou arquivos. A resposta JSON é validada e não executa ações; a prévia exige aplicação manual e pode ser desfeita. A IA pode alterar fatos ou estilo, portanto confira as diferenças. Revogação ou alteração do texto invalida respostas pendentes; não retira dados já enviados. Sem processamento de IA automático. 359 testes unitários e 57 gráficos aprovados em Linux; cinco testes Windows ignorados. O modelo de IA foi simulado nos testes novos; qualidade linguística real pendente. Consulte docs/text.md.

## AI Companion II (v0.11.0a11)

Ditado explícito, revisão da transcrição, sugestão opcional de comando pelo Ollama e prévia/confirmação independente no Copilot. A sugestão envia somente o pedido de até 500 caracteres, sem histórico. O resultado precisa passar pelo parser local; o usuário revisa, aceita no editor, prepara a ação e confirma no Copilot. Nenhuma resposta da IA é executada automaticamente. Leitura automática de respostas opcional na janela, desativada por padrão e condicionada às permissões de IA e voz. Parar solicitações/voz sem apagar histórico; a requisição HTTP enviada pode continuar no servidor. 362 testes unitários e 58 gráficos aprovados em Linux; cinco testes Windows ignorados. IA, ditado e reprodução testados com dublês, não com modelo/áudio reais. Consulte docs/ai-companion-concept.md.

## Security & Quality I (v0.12.0a1)

Validação compartilhada de JSON e leitura limitada de arquivos em `desktop/aeris/safe_input.py`. Configurações, Vault, Bookmarks, Autofill, Backup, Protected Storage e AI Companion rejeitam chaves duplicadas, números não finitos, dados excessivamente aninhados e entradas maiores que seus limites. Configurações limitadas a 64 KiB. Leituras de configurações, cofres e backups verificam arquivos regulares, tamanho e identidade/metadados antes e depois da leitura; links finais são rejeitados. Vault exige esquema inteiro 1 e campos exatos. Backups validam tipo e tamanho codificado antes de decodificar Base64. Formatos de gravação válidos permanecem compatíveis. 371 testes unitários e 58 gráficos aprovados em Linux; cinco testes Windows ignorados. Consulte docs/security-review.md.

## Security & Quality II (v0.12.0a2)

Uma operação local de IA/Companion por Hub (inclui chat, sugestão de comando, revisão contextual e voz do Companion). O bloqueio permanece até o worker retornar, mesmo se sua janela for fechada. Nenhuma nova consulta ou captura pelo Companion enquanto o bloqueio está ocupado; falha ao iniciar thread preserva texto e permite tentar novamente. Respostas tardias não são entregues a janelas novas. JSON interno da revisão e saída de ditado são limitados a 32 KiB e validados pelo parser estrito. Encerramento do Hub pede confirmação também para texto ou conversa em edição. 375 testes unitários e 59 scripts gráficos aprovados em Linux/Xvfb; cinco testes Windows ignorados. Sem garantia de cancelamento da inferência já enviada ao Ollama; bloqueio por instância, não global do sistema. Consulte docs/security-review.md.


## Windows Distribution I (v0.13.0a1)

Receita de empacotamento PyInstaller onedir e instalador Inno Setup por usuário em `../distribution/`. Inclui ícone, prévia de instalação, build isolado, teste de inicialização `--self-test`, mutex Windows para instância empacotada e geração de SHA-256. O guia de frases Translate funciona no modo empacotado simulado; Argos experimental permanece disponível apenas por código-fonte. Ollama e Tesseract opcionais externos. Não foi produzido executável Windows neste ambiente Linux; não há instalador pronto nem garantia de compatibilidade. 379 testes unitários e 60 gráficos passaram; seis nativos Windows pendentes, incluindo mutex. Consulte `../docs/windows-distribution.md` para compilação e matriz de validação.

## Windows Distribution II (v0.13.0a2)

O build verifica o ZIP portátil por inventário e SHA-256 por membro, rejeita caminhos inseguros, duplicatas e arquivos obrigatórios ausentes e confere o identificador AMD64 dos cabeçalhos PE do executável e da DLL Python. A validação final compara os hashes dos artefatos produzidos. `--self-test-full` abre/fecha as ferramentas em configuração temporária, sem solicitar operações de dados, áudio ou IA. `distribution/validate-windows.ps1` está preparado para executar a verificação do EXE portátil ou instalado em VM Windows com hash esperado do build confiável. 388 testes unitários e 60 scripts gráficos executáveis passaram em Linux, seis testes nativos ignorados. Os testes do verificador usam arquivos PE sintéticos, não executáveis reais. Os scripts PowerShell/Inno e a instalação ainda não foram executados em Windows. Não há instalador pronto. Ver `docs/windows-distribution-ii.md`.


## Candidato de código-fonte v1.0.0rc1

Consolidação do primeiro ciclo: 398 testes unitários executados (392 aprovados, 6 ignorados por dependerem de Windows), 60 scripts gráficos aprovados em Linux/Xvfb. A versão e os verificadores de distribuição aceitam `1.0.0rc1`. O ZIP é de código-fonte, sem executável Windows. As nove condições de distribuição binária permanecem pendentes no registro `distribution/release-gate.json`; `python distribution/release-gate.py` retorna 1 enquanto houver pendências. O registro deve ser atualizado apenas após evidências verificáveis e revisão humana. Não é uma certificação nem um bloqueio automático de upload. Consulte `docs/release-candidate.md` para instalação de teste, compilação, validação e publicação. A edição única inclui os recursos de IA opcionais e gratuitos do Aeris; modelos e componentes externos são instalados separadamente. A extensão Chromium permanece uma frente independente.

RC5 experimental: 50 ferramentas refinadas, 10 categorias; este snapshot nao e release publica. Os resultados de CI e limites de distribuicao devem ser conferidos no repositorio.
