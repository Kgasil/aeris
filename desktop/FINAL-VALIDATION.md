# Aeris Final Validation — 1.1.0rc1

Branch desktop-experience; nenhuma publicação, merge ou substituição dos binários públicos.

## Evidência do GitHub Actions

Consulta à API de runs e logs: run 45876938170, commit a7852e76cd9a59b12a0801e9f45b66606501e543, job 140106315039. Oito testes específicos da experiência passaram; regressão histórica Windows: 504 testes, 499 aprovados, 1 falha, 4 ignorados. A captura da interface foi ignorada após a falha. Falha: test_dashboard_coverage_and_weighted_global_mean, AssertionError: (19,) is not false. Runs 45875996697 e 45875523552 registraram a mesma falha. Link: https://github.com/Kgasil/aeris/actions/runs/45876938170

## Correções
- f47b9090e89f1d2ffc1fd0041f02c363c654dda3: Dashboard não recria item do Canvas quando dataset foi invalidado.
- 37c14e2ea14979bdbd2f8037cbf0661a50572039: teste de reunião atualizado para o fluxo atual, verificando falta de modelo, autorização negada, rascunho não salvo e revogação. Não executado localmente.
- 89ed2befb60035c7b5b44595b68d055efd7b537a: CI cancela execuções substituídas e fixa revisões de ações já utilizadas no workflow de revisão.
- 26c7cf3bad702d6ee8e4a41aea17d7c550baf0b4: mantém a asserção original de limpeza do Canvas e acrescenta redimensionamento e novo dataset.
- c47506bae2ef7fe540bbbe8e97cff4217f1fe3c9: captura real do runner deve verificar controles visíveis em cada área; inclui captura separada do contexto de tela.

## Testes locais
Python 3.13.5, Linux, Xvfb. Executei quatro testes com Canvas Tk real e uma cópia do método draw corrigido, utilizando dados, tema e Hub sintéticos: invalidar limpa o gráfico, redimensionar não repõe itens, dataset válido vazio mostra mensagem, novo dataset volta a desenhar. Resultado: 4/4, 0 falhas, 0 ignorados, 0,141 s. Não é execução de DashboardWindow completo nem regressão integral. O código do teste integrado existente foi preservado e ampliado para CI.

## Decisão de lançamento
Git ls-remote continua falhando por DNS. A regressão integral da versão atual não foi confirmada; uma execução de revisão em commit intermediário 89ed2be estava em andamento na consulta. Os nove critérios em distribution/release-gate.json continuam pendentes. Não houve compilação de novo instalador, validação em VMs limpas, assinatura ou análise antimalware. Não publicar. As capturas reais dependem do sucesso do workflow. Prévia conceitual não equivale a captura do aplicativo.
