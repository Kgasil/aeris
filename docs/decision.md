# Aeris Decision — v0.9.0a5

Apoio local à decisão por matriz de critérios ponderados. Não produz recomendação objetiva nem substitui avaliação profissional.

## Uso

Ative Decision no catálogo e abra pelo Hub, Spotlight ou Workspace. A matriz inicia vazia, com três critérios e três alternativas. Selecione a quantidade (2–6 em cada dimensão) e clique em Redimensionar. Os campos que permanecem na matriz são preservados; reduzir uma matriz preenchida exige confirmação. Informe nomes únicos de critérios e alternativas (até 60 caracteres), pesos de 0 a 100 e notas de 0 a 10. Aceita ponto ou vírgula decimal, sem separador de milhares. Todos os campos são obrigatórios, inclusive notas de critérios com peso zero. Notas mais altas sempre representam uma avaliação melhor; para custo, converta o custo em uma nota de preferência antes de preencher. Exemplo carrega dados fictícios, com confirmação se houver conteúdo.

Clique em Calcular ranking. A nota de cada alternativa é a soma de peso × nota dividida pela soma dos pesos. Não é necessário que os pesos somem 100, mas pelo menos um deve ser positivo. O motor usa Fraction e reutiliza a validação numérica do Calculator. A ordenação usa valores racionais exatos; empates compartilham a posição (1, 1, 3), preservando a ordem de entrada entre empatados. A apresentação arredonda para quatro casas decimais, de modo que notas exibidas iguais podem ter posições diferentes. Editar qualquer campo invalida os resultados até um novo cálculo. A ferramenta não verifica a qualidade das notas ou a independência dos critérios.

## Privacidade e limites

Sem leitura de arquivos, rede, IA, gravação de matrizes ou processos auxiliares. Fechar, desativar ou limpar a sessão descarta a matriz; fechamento, substituição e desativação com conteúdo pedem confirmação. Limpeza lógica não equivale a apagamento seguro de memória. Preferências de ativação e favoritos são persistidas no esquema 44; matrizes não são contabilizadas como registros no inventário de Privacy. Não use dados pessoais reais nesta pré-alpha. Exportação, histórico protegido, análise automática de sensibilidade, métodos AHP/TOPSIS e integração por voz ainda não implementados. O catálogo mantém a categoria histórica Business para Decision; a entrega pertence à fase Learning & Research.

## Validação

Linux: 270 testes unitários aprovados (4 ignorados por exigir Windows) e 43 scripts gráficos aprovados em dois lotes com Xvfb. Seis novos testes unitários incluem migração do esquema 43, normalização, empates, arredondamento, limites e nomes inválidos. O smoke Decision verifica edição, recálculo, expansão, confirmação de redução, desativação e limpeza de sessão. No exemplo, pesos 40/35/25 produzem C = 8,2500, A = 7,7000, B = 7,6500. Health registrou 111,92 MiB no processo de teste, não equivalente a execução limpa do aplicativo; sem novo benchmark isolado. Windows, DPI, auditoria independente e desempenho real continuam pendentes.
