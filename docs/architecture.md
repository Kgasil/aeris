# Architecture 001 — Foundation

- Monorepo público Kgasil/aeris: website na raiz, aplicativo em desktop/, futura extensão em extension/.
- Branch develop para experimentação; main preserva o GitHub Pages.
- Python/Tkinter como prova de conceito; catálogo declarativo com 50 ferramentas em 10 categorias.
- Hub parcial, 49 módulos planejados. Não criar engines vazias ou processos residentes.
- Sem rede, conta, captura automática, persistência de dados pessoais ou atalhos globais nesta entrega.
- Validar Windows, DPI, teclado, acessibilidade, encerramento e desempenho antes de distribuir.
- Metas experimentais: núcleo até 10 MB, interface simples até 30 MB, CPU ociosa próxima de zero. Ainda sem medições. Avaliar Rust/Tauri apenas após evidência.
- Antes de persistir dados pessoais, avaliar criptografia, retenção e consentimento. Revisar licença e dependências antes de distribuição.

## Sequência Foundation

1. Hub: validar no Windows, definir contrato de módulos e gerenciamento.
2. Capture: entrada voluntária, edição e exclusão em memória com dados fictícios.
3. Snippets: modelo de dados e gerenciamento local.
4. Search: pesquisa de conteúdo autorizado.
5. Spotlight: atalhos explícitos e autorizados.
