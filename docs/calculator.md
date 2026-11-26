# Aeris Calculator — v0.8.0a4

## Uso
Ative Calculator no Hub e abra pelo Hub, Spotlight ou Workspace. Escolha uma operação, preencha os campos e clique em Calcular (ou Enter). Alterar a entrada invalida o resultado anterior. Limpar, fechar, desativar ou limpar sessão descarta entradas/resultados. Preferências de ativação e favoritos são gravadas no esquema 38; nenhum cálculo é gravado. Não há serviço de fundo, rede, leitura de arquivo ou botão de cópia. Seleção/cópia manual depende do sistema.

## Operações
- Expressão: +, -, *, /, %, **, parênteses e sinais unários. `%` é resto Decimal, não porcentagem. Exponenciação apenas com expoente inteiro de -100 a 100. Ex.: `(2+3)*4` = 20; `0,1+0,2` = 0,3. A precedência segue a sintaxe aritmética do Python; zeros à esquerda em inteiros não nulos podem ser recusados.
- Científica: raiz quadrada, ln e log10, com verificação do domínio. Não há trigonometria nesta versão.
- Financeira: margem = (receita − custo)/receita × 100; markup percentual = (receita − custo)/custo × 100; montante composto = capital × (1 + taxa/100)^períodos, sem aportes, taxas adicionais ou impostos. Taxa por período, em porcentagem, maior que -100% e até 1.000%; até 1.200 períodos inteiros. Receita/custo/capital não negativos; denominador não pode ser zero.
- Estatística: média, mediana e desvio padrão populacional (divisor n), até 200 valores separados por ponto e vírgula. Não há desvio amostral nesta versão.

## Implementação e limites
`calculator.py`: `ast.parse` apenas para produzir árvore sintática; visita explicitamente constantes decimais e operadores permitidos. Não executa `eval`, `exec`, funções fornecidas pelo usuário, nomes, atributos, subscritos ou importações. Expressão até 256 caracteres e 64 nós AST; literal até 64 caracteres; lista até 8.000 caracteres. Vírgula ou ponto decimal, sem separador de milhares nem notação científica na entrada. Resultados em Decimal com contexto de 34 dígitos, expoentes do contexto entre -200 e 200 e magnitude máxima de 10^100. Arredondamento e limites intermediários podem rejeitar cálculos; raízes, logs e divisões podem ser aproximados. Underflow inexato rejeitado. Saída em notação científica quando necessário. Não é um motor certificado para engenharia, contabilidade ou operações financeiras críticas.

`calculator_ui.py`: interface Tkinter sob demanda, integrada aos temas, favoritos e limpeza de sessão. Não é sandbox do sistema operacional. A limpeza é lógica, não apagamento seguro de memória ou clipboard.

## Validação
232 testes unitários executáveis (8 novos), 4 ignorados por exigir Windows; 37 scripts de smoke gráfico aprovados em Linux/Xvfb. Testes cobrem precedência, vírgula decimal, entradas não permitidas, limites, domínio, finanças, estatística, formatação, migração e fluxo da janela. Windows 10/11 x64 e desempenho ainda não validados. Nenhuma publicação no GitHub nesta entrega.
