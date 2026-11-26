# Aeris Debug — v0.10.0a4

## Uso
Ative Debug no Hub e abra a ferramenta. Digite ou cole código Python de teste (não use credenciais nem dados reais). Selecione Analisar. O resultado apresenta o primeiro erro de sintaxe/estrutura, ou até 50 avisos heurísticos para código sintaticamente válido. Ir ao primeiro diagnóstico posiciona o cursor na linha e coluna indicadas. Alterar código invalida a análise. Limpar, fechar ou desativar pede confirmação quando há código; a limpeza geral da sessão descarta a janela após confirmação global. Não há histórico, exportação automática, leitura de arquivos ou monitoramento de outros aplicativos.

## Motor
`aeris.debug.analyze` valida entradas, faz `ast.parse`, limita a árvore e chama `compile` apenas para validar regras de escopo. O objeto de código gerado é descartado, nunca executado; não há `eval`, `exec`, importação dos módulos fornecidos ou subprocessos. Usa a gramática do Python instalado (validação Linux com Python 3.13.5). Mensagens do interpretador podem aparecer em inglês, com orientação em português. A análise estática não é sandbox de segurança ou auditoria de código. Não foi avaliada contra todas as entradas adversariais possíveis.

Limites: 20.000 caracteres, 1.000 linhas, 8.000 nós, profundidade AST 100 e 50 avisos exibidos. Entradas nulas, vazias, Unicode inválido ou excessivamente complexas são rejeitadas. Avisos: `except:` sem tipo, `from ... import *`, valores padrão literais mutáveis (lista, conjunto ou dicionário). Os avisos são sugestões, não erros obrigatórios. Não identifica todas as falhas semânticas, problemas em tempo de execução, dependências ausentes, vulnerabilidades ou todas as formas de valor padrão mutável. Não executa testes do código colado e não corrige código automaticamente.

## Privacidade e integração
Somente a preferência de ativação e os favoritos são gravados em settings.json (esquema 48; migração preserva as preferências antigas). Código e resultados ficam na janela em memória; limpeza lógica não garante apagamento de RAM, swap ou clipboard. Hub, Spotlight, Workspace e temas utilizam o catálogo existente; não há integração com IA, rede ou acesso automático ao editor do usuário.

## Validação
Sete testes unitários novos: sintaxe, escopo, avisos, limites, não execução (tentativa de gravação não produz arquivo), código válido e migração. Um novo smoke gráfico testa abertura, edição, navegação e invalidação de diagnóstico, confirmação e limpeza de sessão. Regressão: 297 unitários aprovados, 4 ignorados por exigirem Windows; 47 scripts gráficos aprovados em Linux/Xvfb. Nenhuma validação nativa Windows ou auditoria independente realizada. Health no processo de smoke: 111,98 MiB RSS, não equivale à memória em execução isolada.
