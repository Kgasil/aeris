# Architecture 001 — Foundation

- Monorepo público Kgasil/aeris: website na raiz, aplicativo em desktop/, futura extensão em extension/.
- Branch develop para experimentação; main preserva o GitHub Pages.
- Python/Tkinter como prova de conceito; catálogo declarativo com 50 ferramentas em 10 categorias.
- Hub, Capture e Snippets em protótipo, 47 módulos planejados. Capture é carregado sob demanda, desativado por padrão, e usa armazenamento volátil. Apenas preferências não sensíveis são persistidas em JSON fora do repositório. Não criar engines vazias ou processos residentes.
- Sem rede, conta, captura automática, persistência de dados pessoais ou atalhos globais nesta entrega.
- Validar Windows, DPI, teclado, acessibilidade, encerramento e desempenho antes de distribuir.
- Metas experimentais: núcleo até 10 MB, interface simples até 30 MB, CPU ociosa próxima de zero. Ainda sem medições. Avaliar Rust/Tauri apenas após evidência.
- Antes de persistir dados pessoais, avaliar criptografia, retenção e consentimento. Revisar licença e dependências antes de distribuição.

## Sequência Foundation

1. Hub: gerenciamento inicial implementado para Capture; validar no Windows e generalizar contrato de módulos.
2. Capture: entrada voluntária, edição e exclusão em memória com dados fictícios implementadas; validação pendente.
3. Snippets: modelo de dados, busca e gerenciamento volátil implementados; validação pendente.
4. Search: pesquisa de conteúdo autorizado.
5. Spotlight: atalhos explícitos e autorizados.

## Atualização a3 — experiência compacta

- Preferências de aparência em esquema 2, migração de leitura do esquema 1 e gravação por substituição atômica.
- Editor com prévia, restauração e persistência; painel rápido relativo ao Hub sob demanda.
- Ícone mostrado apenas na prévia. Sem integração global, sem captura de cliques.
- Próximos: Snippets, Search, Spotlight nativo e integração. Testes novos ainda não executados.

## Atualização a4 — textos reutilizáveis

- Snippets separa modelo de dados e interface; armazenado somente em memória, opt-in.
- Busca por título, categoria e corpo, com normalização de acentos e caixa.
- Cópia explícita confirmada para o clipboard, sem leitura ou colagem automatizada.
- Esquema 3 preserva preferências dos esquemas 1 e 2.
- Próximo: Search unificado sobre conteúdo salvo e autorizado dos módulos ativos.
- Testes a4 escritos, não executados.
