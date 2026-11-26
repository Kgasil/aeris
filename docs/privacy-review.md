# Revisão preliminar de privacidade — Foundation a8

| Área | Controle atual | Limite / próximo passo |
| --- | --- | --- |
| Permissões | Capture, Snippets e Search desativados inicialmente; ativação explícita | Permissions ainda planejado; revisar permissões nativas |
| Busca | Catálogo por padrão; conteúdo somente de fontes selecionadas e ativas | Não há busca externa nem histórico de consultas |
| Armazenamento | Textos em memória; JSON de preferências sem textos | Não equivale a criptografia ou apagamento seguro; dados reais proibidos nesta pré-alpha |
| Clipboard | Cópia explícita com aviso e confirmação; sem leitura automática | Sistema pode manter histórico/sincronizar; limpeza da sessão não altera clipboard |
| Limpeza | Confirmação antes de remover notas, snippets e rascunhos; pesquisa fechada | Remoção lógica; resíduos em memória/swap e cópias externas fora do controle |
| Spotlight | Opt-in, sobreposição opcional, ocultação manual, sem hooks globais | Sem detecção automática de jogos; validar no Windows |
| Dependências | Biblioteca padrão Python e Tcl/Tk | Revisão de licenças, distribuição e runtime pendentes |
| Rede | Nenhum cliente de rede implementado | Medição de tráfego real pendente |

Revisão de código e testes funcionais limitados. Não constitui auditoria independente, teste de intrusão ou certificação.
