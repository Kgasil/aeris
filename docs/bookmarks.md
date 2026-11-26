# Aeris Bookmarks — escopo a4

## Fluxo e proteção
- Ativar no Hub; abrir no Hub, painel rápido ou Spotlight; desbloquear explicitamente.
- Registro com título de até 120 caracteres, categoria de até 60 e URL de até 4096. Até 100 registros, duplicatas exatas recusadas.
- Armazenamento separado `%LOCALAPPDATA%/Aeris/bookmarks.bin`, reutilizando a proteção DPAPI e trava exclusiva do Vault. Não há fallback sem criptografia. Erros de leitura não substituem arquivo existente.
- Acesso externo: autorização de sessão mais confirmação de cada URL salva. Nenhuma consulta de rede, pré-visualização remota, abertura automática, importação, sincronização ou indexação pelo Search. O navegador pode registrar histórico e acessar a rede.
- URL HTTP/HTTPS sem credenciais, espaços, controles ou barras invertidas. Validação sintática não identifica phishing, redirecionamentos, destinos locais ou conteúdo malicioso.
- Fechar, bloquear, desativar e limpar sessão descartam rascunhos e bloqueiam os dados; registros salvos são preservados. Não se promete apagamento seguro de memória. DPAPI de escopo do usuário não substitui senha mestra e não protege contra todos os processos da mesma conta.

## Validação
Testes de armazenamento usam backend simulado sem valor criptográfico, e lançamento do navegador usa callback falso. Abertura nativa, DPAPI, escalas de tela e painel compacto ainda requerem validação em Windows 10/11. Use somente dados fictícios nesta pré-alpha. Backup/recuperação pendentes.
