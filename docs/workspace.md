# Workspace — 0.4.0a5

## Escopo

- Até 20 ambientes em memória e oito links por ambiente. Somente ferramentas implementadas, sem autorizar ou ativar módulos automaticamente.
- Ativar troca temporariamente a lista de acesso rápido; mantém Workspace acessível e não altera favoritos gerais. Ao sair, o filtro geral volta.
- Ações individuais, sem execução em lote, shell, agendamento, monitoramento ou restauração de janelas do Windows.
- Links: HTTP/HTTPS validados, sem credenciais na autoridade da URL. A validação não atesta reputação ou segurança do destino. Autorização por sessão e confirmação por clique. Revogação bloqueia abertura futura.
- Nenhum conteúdo dos presets gravado em disco. Ao limpar a sessão, desativar o módulo ou encerrar, ambientes são descartados logicamente (não apagamento seguro da RAM).
- O lançamento nativo reutiliza os.startfile do Bookmarks. Testado com simulador em Linux; Windows real pendente.
- Requisito ainda pendente: persistência protegida e recuperação de ambientes, bem como restauração de janelas/aplicativos externos.

## Validação

5 testes novos de modelo e migração, 1 smoke gráfico; regressão completa 112 unitários aprovados, 3 ignorados por Windows, 18 smokes gráficos aprovados. Sem benchmark de consumo.
