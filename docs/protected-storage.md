# Protected Storage — v0.11.0a9

Consolidação pré-alpha, com salvamento automático opt-in desde v0.11.0a9; não é lançamento estável.

## Uso com dados fictícios (Windows 10/11)

1. Ative Checklist, Ideas, Learn, Meeting, Research, Flashcards ou Reminder e confirme os registros dentro da ferramenta.
2. Abra Hub → Permissões e autorize Storage → Salvar somente na sessão atual.
3. Abra Privacy → Cópias protegidas. Selecione a ferramenta e clique em Salvar cópia protegida. Confirme a substituição caso já exista uma cópia. Rascunhos não são gravados.
4. Após reiniciar, ative a ferramenta, se necessário, mas deixe sua janela fechada. Feche também o Copilot. Autorize Storage → Restaurar e confirme a substituição da sessão. Abra a ferramenta para ver os registros restaurados.
5. Storage → Excluir permite remover a cópia do disco, mediante confirmação. A exclusão não afeta a sessão em memória e não equivale a apagamento seguro.

Não existe carregamento automático. O salvamento automático opcional é descrito na seção IV. A limpeza de sessão, desativação de módulos e encerramento preservam as cópias do disco e descartam alterações não copiadas. Não use dados pessoais reais antes da validação nativa e auditoria. Não armazene senhas ou credenciais.

## Formato e segurança

- Um arquivo por módulo no diretório de Settings (`%LOCALAPPDATA%/Aeris` por padrão): `storage-checklist.bin`, `storage-ideas.bin`, `storage-learn.bin`, `storage-meeting.bin`, `storage-research.bin`, `storage-flashcards.bin`, `storage-reminder.bin`.
- Cabeçalho público `AERIS-STORAGE-1` seguido de blob DPAPI no escopo do usuário Windows. O envelope JSON interno inclui schema 1, módulo e registros; é protegido antes de qualquer gravação. Sem fallback em texto aberto. O backend injetável é exclusivamente para testes; o dublê não é criptografia.
- Limite de 8 MiB para o envelope e para o arquivo. Validação estrita das chaves, tipos, quantidade, duplicidade de chaves JSON, versão e módulo. Reconstrução pelos métodos dos stores originais, preservando ordem, títulos, conteúdo e estados; IDs internos são regenerados. Falhas de validação não substituem registros em memória.
- Lock não bloqueante por arquivo, arquivo temporário contendo apenas blob protegido, flush/fsync e os.replace. Falhas antes da substituição preservam a versão anterior. Cópias inválidas ou incompatíveis não são sobrescritas pelo fluxo normal. Não há garantia absoluta contra perda de energia, armazenamento defeituoso ou alterações externas. Os arquivos .lock não contêm registros.
- As três permissões são independentes, negadas por padrão e não persistidas. Após confirmação a permissão é revalidada. Restaurar exige janela do módulo e Copilot fechadas para evitar referências antigas. A cópia é um snapshot manual: sessões concorrentes podem ter versões diferentes e uma gravação confirmada substitui a última versão; não há merge ou controle de conflitos.
- DPAPI não protege contra processos maliciosos que atuem com o mesmo usuário, comprometimento do sistema, memória/swap, nem garante recuperação após perda do perfil Windows. A exclusão não garante remoção de cópias externas ou resíduos. Não há migração de schema nem backup automático. Recuperação manual e Backup integrados conforme seção abaixo.

## Escopo

Checklist: até 20 listas, 100 tarefas/lista, incluindo listas vazias, prioridade e conclusão. Ideas: até 200 registros, categoria, texto e estado. Learn: até 20 trilhas, 100 tópicos/trilha, estimativas, ordem e conclusão. Meeting: até 50 reuniões, 50 ações por reunião, participantes, pauta, notas e prazos. Research: até 300 referências, metadados fornecidos e estado de leitura. Flashcards: até 500 cartões, data UTC absoluta, intervalo e número de revisões. Reminder: até 100 lembretes, horário absoluto, estado e opção de alerta. Outros stores continuam com suas políticas anteriores. Autorizações do Context e Clipboard não entram neste mecanismo.

## Validação

Linux: 323 testes unitários executáveis aprovados, 5 ignorados por exigirem Windows; 50 scripts gráficos aprovados em Xvfb. O teste de roundtrip DPAPI nativo foi adicionado, mas não executado. Testes de fluxo usam dados fictícios e backend simulado. Testes de falha verificam preservação da cópia anterior, recusa de schema inválido, bloqueio concorrente, ausência de fallback e exclusão independente da sessão. Seis novos testes cobrem roundtrip, datas, estados, validação e compatibilidade do schema; o smoke existente agora também verifica o reagendamento do Reminder. Próximo incremento: avaliar salvamento opcional, conflitos, recuperação e backup protegido antes de ampliar a distribuição.

## Datas e restauração

Flashcards preserva o vencimento UTC e a contagem de revisões sem recomeçar o intervalo. Reminder preserva o instante Unix, não a duração relativa: pendências já vencidas tornam-se `due` sem alerta retroativo. Cancelados e vencidos permanecem nesses estados. Pendências futuras são reagendadas pelo Hub, inclusive com a janela fechada; não há alertas enquanto o Aeris estiver encerrado. A restauração substitui registros da sessão e fecha alertas antigos; o arquivo original não é atualizado automaticamente. Restaurar uma cópia antiga pode reintroduzir tarefas ou estados antigos. O schema 1 e as cópias dos três módulos anteriores permanecem compatíveis.


## Recuperação e Backup (a3)

Marque «Preservar uma versão anterior ao salvar» antes de salvar. Se existir cópia válida, o blob protegido anterior é gravado atomicamente como `storage-<módulo>.previous.bin`; apenas uma versão anterior por módulo, substituída em novo salvamento com esta opção. Recuperar versão anterior carrega os registros em memória sem modificar os arquivos. Excluir atual e anterior são ações separadas. A recuperação não oferece reparo automático de uma cópia atual corrompida. Backup inclui os sete blobs atuais existentes, além dos itens tradicionais; não inclui as versões anteriores ou Autofill. A restauração pelo Backup valida via DPAPI, preserva a cópia atual válida como anterior e substitui somente o arquivo selecionado; depois carregue o arquivo via Privacy. O limite de arquivo de backup passa a 170 MiB; arquivos antigos continuam aceitos. As cópias ainda dependem do perfil Windows original. Operações entre vários arquivos não são uma transação única. Até v0.11.0a8, salvamento e carregamento eram manuais.

## IV — Salvamento automático opcional

- Duas permissões de sessão: `storage.auto` e `storage.save`. Ativação individual, confirmação explícita e módulo ativo com registros confirmados não vazios. Não há preferência persistente nem ativação no início do aplicativo.
- Se houver cópia atual, os registros reconstruídos precisam coincidir com os registros em memória para ativar. Caso contrário, reconciliar manualmente com salvar/restaurar. Reminder pode exigir reconciliação quando o estado de um prazo mudar. Se não houver cópia atual, a primeira gravação ocorre no próximo ciclo ou em Salvar alterações agora.
- Um único callback Tk a cada 10 segundos enquanto houver módulos armados; nenhum callback periódico quando desarmado. Compara hashes de snapshots em memória e só grava quando houver mudança. O hash dos bytes protegidos anteriores é conferido dentro da mesma trava da escrita, evitando sobrescrever alterações feitas por outra instância cooperativa ou Backup. Não monitora o disco sem alterações da sessão.
- Validação, proteção DPAPI, limite de 8 MiB e substituição atômica de cada arquivo mantidos. Uma versão anterior protegida é preservada antes de substituir a atual. A gravação da versão anterior e da atual não constitui uma transação de dois arquivos.
- Se a coleção de registros ficar totalmente vazia, a operação é desarmada e a cópia preservada. Exclusões parciais confirmadas podem ser salvas; para salvar uma coleção vazia, use a operação manual explícita.
- Revogar uma das permissões, desativar ferramenta, limpar sessão, encerrar ou confirmar operação manual de armazenamento desarma o automático correspondente (limpeza/encerramento desarmam todos). Não há flush final ao encerrar ou limpar. Pode haver perda de mudanças desde o último ciclo, portanto use Salvar alterações agora antes de sair.
- Conflito, arquivo corrompido ou falha desarma o módulo e exibe aviso. Não há resolução automática, sincronização, garantia contra modificações externas que ignorem a trava, serviço residente, armazenamento de rascunhos ou fallback em texto aberto. O trabalho ocorre na thread Tk e pode atrasar a interface com cópias grandes; requer avaliação no Windows.
- Testes Linux: oito novos casos unitários com backend simulado e um smoke gráfico; regressão 352 unitários aprovados, cinco ignorados, 56 gráficos aprovados. Não comprova DPAPI real.
