# Aeris Compare — v0.6.0a4

## Uso
- Ative Compare no Hub. O módulo é opcional e começa desativado.
- Modo Texto: insira os dois textos nos campos Original e Revisado. Clique em Comparar.
- Modo Arquivos: conceda a permissão independente `compare.files.read`, selecione dois arquivos locais fictícios e confirme a leitura. TXT, MD e CSV até 1 MiB, DOCX até 8 MiB (XML principal até 1 MiB), conforme Documents.
- O relatório utiliza `-` para remoções, `+` para adições e espaço para linhas mantidas. As colunas numéricas são os números das linhas originais e revisadas. Alterações são representadas por remoção e adição, não por um quarto tipo.
- Espaços e maiúsculas são significativos. CRLF e CR são normalizados em LF; a quebra final é significativa. A comparação não é byte a byte.

## Arquitetura e limites
`aeris.compare` reutiliza `aeris.documents.extract_file` e, indiretamente, as validações de leitura local de Verify. Não depende da ativação do módulo Documents. Usa `difflib.SequenceMatcher` com autojunk desativado, para preservar a comparação de linhas repetidas. Limite de 100.000 caracteres e 2.000 linhas por lado; prévia truncada é recusada. O algoritmo não garante o menor conjunto de edições e pode ficar mais lento em entradas repetitivas. O trabalho ocorre em thread daemon sob demanda, sem fila de tarefas persistente; cancelamento cooperativo não interrompe imediatamente a chamada interna do difflib nem uma leitura bloqueada.

Não há gravação, abertura de links, execução de macros, rede, histórico, comparação binária ou edição/mesclagem de arquivos. Para verificar bytes, use Verify. DOCX compara somente o texto que Documents consegue extrair; CSV compara linhas brutas, não registros ou células. Não use como prova de equivalência integral, autenticidade ou sanitização. A seleção de arquivos usa os limites e as verificações de caminho do Documents, ainda não testadas nativamente em Windows. Os dois arquivos são lidos sequencialmente; não é um snapshot atômico.

A permissão é temporária e não é um sandbox do SO. Revogar a leitura durante o modo Arquivos cancela e descarta caminhos e resultados; mudar de modo limpa a sessão da ferramenta. Limpar, fechar, desativar ou encerrar descarta a prévia. Não é apagamento seguro de memória. O aplicativo não oferece botão de cópia automática; os controles padrão de edição do sistema continuam disponíveis.

## Validação
Linux: 173 testes unitários descobertos, 169 aprovados e 4 ignorados por exigir Windows. 27 scripts gráficos em Xvfb aprovados. Testes específicos: substituição e numeração, textos vazios/repetidos, espaços e quebras, limites e cancelamento, arquivos preservados, truncamento/formato não suportado e migração de preferências; integração gráfica, edição invalida resultado, seleção autorizada, revogação durante leitura, desativação e limpeza. Sem validação Windows, auditoria independente ou benchmark de carga nesta entrega.
