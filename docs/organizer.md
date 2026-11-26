# Aeris Organizer — v0.6.0a2

Protótipo de planejamento de organização de arquivos. Módulo opcional desativado por padrão. Permissão de sessão independente Organizer → Listar pasta, negada por padrão. Seleção explícita de pasta e confirmação antes de cada análise. Sem leitura do conteúdo, escrita, transferência, exclusão, renomeação, criação de pastas ou persistência do relatório.

## Escopo

- Uma única pasta absoluta, sem recursão. No Windows, reaproveita a validação de caminhos de Verify: unidades locais fixas, sem UNC ou pontos de nova análise conhecidos. Recusa componentes que não sejam diretórios regulares. Pula links simbólicos, pontos de nova análise, subpastas e entradas inacessíveis/não regulares.
- Limite de 2.000 entradas visitadas, incluindo entradas ignoradas. Relatório avisa se há entradas adicionais. A ordem inicial da leitura depende do sistema; se parcial, não é inventário completo nem amostra representativa. Resultado ordenado por categoria/nome.
- Sete categorias por extensão (Documentos, Imagens, Planilhas e dados, Compactados, Áudio e vídeo, Código, Outros). Não verifica o tipo real, não procura duplicatas, não mede espaço físico em disco. Tamanho lógico em bytes, totais referentes somente aos itens listados. Nomes com caracteres de controle/formato são representados por escapes no relatório.
- A análise ocorre sob demanda em thread separada. Cancelamento cooperativo entre entradas; chamadas do sistema podem bloquear. Revogar permissão, desativar, limpar sessão ou fechar cancela e descarta a prévia. Não é apagamento seguro de memória, sandbox ou defesa contra corridas de sistema de arquivos. A pasta pode mudar durante a leitura; não há snapshot atômico.
- No Linux, caminhos montados em rede não são identificados pelo verificador. O aplicativo não inicia requisições de rede próprias; o sistema de arquivos pode ter comportamento externo. Use apenas pastas locais fictícias.

## Validação

Linux: 156 testes unitários executáveis aprovados, 4 testes anteriores ignorados por exigirem Windows, 25 smoke tests gráficos aprovados em Xvfb. Seis novos testes unitários: categorias, inventário e preservação, limites/cancelamento, links e caminhos inválidos, exibição e migração 25→26. Novo smoke: ativação, autorização, confirmação recusada, inventário real, revogação durante análise simulada, desativação e limpeza. Sem validação nativa Windows nem benchmark de carga.

## Próximos passos

Planejamento de movimentações com revisão, detecção de conflitos, verificação de identidade, autorização de escrita separada e reversão; não implementados. Próximo módulo do roadmap: Aeris Drop.
