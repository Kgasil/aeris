# Personal Memory — Permissions v0.2.0a1

- Controle central em memória: negar por padrão; autorização explícita por sessão; revogação individual e total.
- Search verifica fontes autorizadas na pesquisa e verifica novamente antes de abrir resultados. Desativação de módulo e limpeza da sessão revogam acessos aplicáveis.
- Snippets verifica autorização antes e depois da confirmação de cópia. O controle abrange o botão de cópia do Aeris, não as operações nativas de edição do sistema nem aplicativos externos.
- Não armazenar autorizações, consultas ou conteúdo em disco. Não há sandbox de segurança do sistema, auditoria independente ou garantia contra acesso ao processo.
- Windows 10/11 x64 é a plataforma-alvo. O código usa Tkinter e biblioteca padrão, com tratamento Win32 da área de trabalho no Spotlight. Testes reais no Windows, incluindo o BAT, DPI, clipboard, tela cheia, instalador e desempenho, ainda pendentes.
- Validação executada: Python 3.13.5/Linux, 31 testes unitários e quatro testes gráficos Xvfb. Não implica compatibilidade certificada no Windows.
