# Aeris Context — v0.10.0a2

Contextualização manual, local e temporária. Não é um motor de IA, memória persistente ou monitoramento de atividades.

## Uso

1. Ative Context no Hub. Abra a janela e informe título, categoria e texto voluntário. Use dados fictícios na pré-alpha.
2. Salve. Cada registro começa excluído da prévia, inclusive se a permissão global já estiver concedida.
3. Em Permissões, conceda Context → Prévia. Selecione um registro na tabela, clique em Incluir / retirar e confirme sua inclusão. Repita somente para registros desejados.
4. Clique em Gerar prévia local autorizada. A prévia contém exclusivamente os registros salvos selecionados. Não é enviada ao Copilot ou a qualquer modelo. Nenhum conteúdo é interpretado como comando.
5. Para retirar um registro, selecione-o e use Incluir / retirar. Revogar seleção retira todos da prévia. Revogar Context → Prévia nas permissões também limpa seleções e prévia, mesmo com a janela fechada. Voltar a conceder a permissão não restaura as seleções.

## Limites e ciclo de vida

Até 50 registros, título de 160 caracteres, corpo de 4.000 caracteres, cinco categorias (Profissional, Estudos, Documentos, Agenda, Outros), prévia de até 20.000 caracteres. Exceder esse limite gera erro sem prévia parcial. Não há importação de arquivos, clipboard, agenda ou outros módulos. Editar um registro invalida sua inclusão; alterações nas seleções ou registros invalidam a prévia. Fechar a janela preserva os registros e seleções da sessão, mas destrói a prévia. Desativar ou limpar a sessão descarta os registros e revoga a permissão. Encerrar descarta os dados temporários. Revogação de acesso não apaga registros privados, nem cópias manuais feitas pelo usuário. A limpeza é lógica, não apagamento seguro da memória do sistema.

## Fronteira de integração futura

`ContextStore.preview()` consulta a permissão de sessão e retorna somente os registros selecionados. A revogação é propagada pelo Hub, inclusive com a janela fechada. O Copilot atual não consome esse contexto. Uma futura integração deverá revisar a seleção no momento do uso, delimitar os dados como conteúdo não confiável, tratar instruções inseridas no contexto como texto e validar operações separadamente. Nenhum envio externo sem consentimento explícito próprio. Não é sandbox nem defesa comprovada contra prompt injection.

## Validação

Linux: 284 testes unitários aprovados (288 executados, 4 ignorados por exigir Windows) e 45 scripts gráficos aprovados com Xvfb, incluindo criação, seleção, recusa, revogação, reabertura, limpeza e desativação. Sem novas dependências externas Python. Validação Windows, auditoria independente, persistência protegida e teste de integração IA pendentes.
