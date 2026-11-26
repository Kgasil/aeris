# Aeris Data — v0.8.0a1

Perfil local de qualidade de CSV, somente leitura. Ative Data no Hub, conceda Data → Ler CSV em Permissões, selecione o arquivo, configure separador de campos (vírgula, ponto e vírgula ou TAB) e decimal (ponto ou vírgula), e confirme a análise. Experimente `desktop/tests/fixtures/data_example.csv` com ponto e vírgula e vírgula decimal.

## Motor

- Cabeçalho obrigatório, não vazio, com nomes distintos após remoção de espaços nas extremidades. Registros retangulares; linhas irregulares são rejeitadas. Campos entre aspas e quebras de linha dentro de campos são aceitos pelo parser CSV.
- UTF-8, UTF-8 com BOM ou UTF-16 com BOM; máximo 1 MiB, 5.000 registros, 50 colunas, 100.000 células de dados e 4.096 caracteres por campo. Limites excedidos invalidam a análise em vez de retornar estatísticas parciais.
- Contagens de registros, colunas, valores ausentes (vazios ou só espaços), duplicatas adicionais exatas (tuplas de campos; preserva diferenças de espaços e caixa) e valores distintos não ausentes por coluna. Duplicatas permanecem nas estatísticas.
- Inferência conservadora de números decimais simples: todos os valores não ausentes precisam corresponder ao formato escolhido, com até 32 caracteres. Sem separador de milhares, notação científica, interpretação de datas, NA/NULL especiais ou avaliação de fórmulas. Identificadores numéricos podem ser classificados como números. Mínimo, máximo e média com Decimal; a média é exibida com até 10 dígitos significativos. Não há limpeza, exportação ou edição.
- Usa os validadores locais e verificação de alterações do Verify, decodificação do Documents, `csv` e `decimal` da biblioteca padrão. Rejeita links finais e pais detectados; não é sandbox nem elimina todas as condições de corrida. Leitura e análise em thread auxiliar sob demanda, cancelamento cooperativo; revogação descarta o relatório e a seleção. Fechar, desativar ou limpar sessão descarta o relatório. Nenhum conteúdo é persistido; não equivale a apagamento seguro de memória.

## Validação

212 testes unitários aprovados e 34 testes gráficos aprovados em Linux/Xvfb; quatro testes Windows anteriores ignorados. Sete novos testes unitários e um gráfico. Não há validação Windows nativa, benchmark de carga ou auditoria independente. Use somente CSV fictício. O módulo não oferece suporte a XLSX, SQL, BI externo ou integração com Dashboard nesta entrega.
