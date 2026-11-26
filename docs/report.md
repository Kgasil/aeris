# Aeris Report — v0.8.0a3

1. Ative Report no Hub, autorize Report → Ler CSV em Permissões e selecione um CSV local fictício.
2. Configure separadores de campo e decimal, clique em Analisar CSV e confirme a leitura.
3. Confira a prévia: resumo da base, qualidade e estatísticas por coluna, indicadores opcionais por categoria e pontos de revisão. Selecione categoria, Contagem/Soma/Média e métrica numérica se aplicável. Sem agregação é o padrão.
4. Para copiar, autorize separadamente Report → Clipboard, revise a prévia e confirme. O clipboard do sistema pode reter dados; revogar permissões não apaga cópias anteriores. As permissões do Aeris não são um sandbox do sistema operacional.

O Report reutiliza a leitura validada do Data e a agregação Decimal do Dashboard; não exige que os dois módulos estejam ativos. Nenhum arquivo original é alterado. Limites: CSV 1 MiB, 5.000 registros, 50 colunas, 100.000 células, 4.096 caracteres por campo e 100 categorias válidas. Todos os grupos válidos aparecem no relatório, em ordem decrescente do indicador. Ausentes são campos vazios ou somente espaços; registros sem categoria/métrica necessária são ignorados apenas na agregação. Duplicatas exatas adicionais são contabilizadas e permanecem nos cálculos. Média global ponderada pelo número de registros. Rótulos acima de 120 caracteres são abreviados e controles representados visivelmente; números exibidos com até 12 algarismos significativos.

Prévia textual determinística, sem LLM, exportação PDF/DOCX, formatação avançada ou auditoria de negócios. Não grava relatórios em disco. O dataset e a prévia são temporários: limpeza, fechamento, desativação ou revogação de leitura descartam os resultados; revogar a cópia desabilita o botão sem remover a prévia. A leitura utiliza worker cancelável, a agregação limitada ocorre na interface. O exemplo report-example.txt foi gerado a partir de desktop/tests/fixtures/data_example.csv. Use somente dados fictícios até a validação de segurança e do Windows.

Validação em Linux: 224 testes unitários aprovados, quatro ignorados por plataforma, 36 smoke tests gráficos aprovados. Windows 10/11 x64, desempenho sob carga e auditoria independente ainda pendentes.
