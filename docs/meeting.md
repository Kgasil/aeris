# Aeris Meeting — v0.10.0a5

Registro manual de reuniões. Nenhum acesso a câmera, microfone, calendário, rede ou aplicativos externos. Não é transcrição, assistente de reunião ao vivo ou agendador.

## Uso

1. Ative Meeting no Hub e abra a ferramenta.
2. Informe título (obrigatório, 160 caracteres) e data opcional no formato AAAA-MM-DD. Use as abas para participantes (2.000 caracteres), pauta (4.000) e anotações/decisões (8.000).
3. Em Plano de ação, informe atividade (200 caracteres), responsável opcional (120) e prazo opcional (AAAA-MM-DD). Adicione. Para editar uma atividade existente, selecione, carregue e atualize. Alterne a conclusão ou exclua mediante confirmação. Limpe campos não utilizados antes de salvar.
4. Salve a reunião. A pesquisa local ignora acentos e inclui título, data, participantes, pauta, notas, nomes de atividades e responsáveis. Selecione um resultado e abra para editar.
5. Gere a prévia da ata salva. Para usar o botão de cópia, autorize Meeting → Clipboard em Permissions e confirme cada operação. Revise o conteúdo: clipboard e histórico do sistema podem preservar o texto. Nenhuma ata é enviada a terceiros pelo módulo.

Até 50 reuniões e 50 atividades por reunião. Datas são validadas, incluindo anos bissextos; não disparam notificações. Nenhum dado é inventado quando campos opcionais estão vazios. Atas são texto simples, não arquivos assinados nem transcrições. Alterações só entram na ata após salvar. O botão de cópia revalida o estado do registro e a permissão antes de escrever. Editores de entrada têm os recursos normais de seleção/cópia do Tk; permissões de aplicativo não constituem sandbox do sistema operacional.

## Sessão e privacidade

Registros salvos sobrevivem ao fechamento da janela, não ao encerramento do processo. Desativação e limpeza de sessão descartam os registros; o Privacy apresenta apenas contagem. Não há persistência criptografada para Meeting, exportação em arquivo, integração com Checklist ou Reminder ou AI Companion. Utilize dados fictícios nesta pré-alpha. A limpeza lógica não é apagamento seguro de memória ou clipboard.

## Verificação

Seis testes unitários novos: operações, pesquisa, limites, datas, atomicidade, ata e migração. Smoke gráfico cobre abertura, edição de atividades, confirmação, cópia e revogação, preservação na sessão, desativação e limpeza. Regressão: 303 unitários aprovados, 4 ignorados por exigir Windows, 48 scripts gráficos aprovados em Linux/Xvfb. Health no processo de smoke: 111,96 MiB RSS, não equivale ao consumo isolado do aplicativo. Sem auditoria independente ou teste Windows nativo.


**Atualização da consolidação (v0.11.0a2):** registros confirmados podem ser salvos/restaurados manualmente por Privacy → Cópias protegidas. Rascunhos e alterações não copiadas continuam temporários. Consulte `protected-storage.md` para permissões, prazos, limitações e validação.
