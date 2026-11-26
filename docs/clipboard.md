# Clipboard — 0.2.0a3

## Modelo e escopo

`ClipboardStore` é uma coleção limitada em memória; recebe funções de leitura/escrita somente de ações explícitas. `ClipboardWindow` usa Tkinter para integração com o clipboard do sistema e confirma operações. Não usa listener, polling, hooks globais, captura de teclado ou acesso a arquivos de histórico. Não há captura de imagens, arquivos, senhas ou formatos ricos como funcionalidades; o módulo aceita apenas texto fornecido pelo sistema e não consegue classificar com segurança se ele contém segredo. Use conteúdo fictício.

## Permissões e retenção

Leitura e escrita são capacidades distintas de sessão. Revogar bloqueia novas operações correspondentes; a consulta local aos itens já capturados continua permitida até limpeza. A remoção lógica não garante apagamento físico de RAM/swap, nem afeta Win+V ou sincronização do Windows. Clipboard não é fonte do Search e não é persistido no Vault.

## Validação

43 unitários e 6 smoke tests gráficos aprovados no Linux (um teste DPAPI nativo ignorado). Verificar no Windows 10/11 x64: captura de texto e Unicode, clipboard vazio/ocupado, formatos não textuais, cópia após fechar janela, DPI, comportamento com Win+V e sincronização, foco e tamanhos. Não é auditoria de segurança.
