# Aeris Vault — 0.2.0a2

## Escopo
Notas fictícias com título e corpo, até 100 registros, título de 120 e corpo de 20.000 caracteres. Criação, edição, exclusão, persistência e bloqueio explícitos. Sem perfis estruturados, integração com Capture/Snippets, autofill, recuperação ou backup.

## Arquitetura e riscos
- `dpapi.py` utiliza CryptProtectData/CryptUnprotectData (crypt32.dll) com CRYPTPROTECT_UI_FORBIDDEN e sem CRYPTPROTECT_LOCAL_MACHINE. Escopo do usuário Windows, não senha mestra ou reautenticação. Sem backend de produção em Linux.
- `vault.py` serializa todos os registros em memória, protege o payload e escreve somente o blob protegido em arquivo temporário no mesmo diretório, seguido de fsync e substituição atômica. Cabeçalho de formato não contém dados pessoais. Falha de proteção/leitura não deve substituir o cofre existente. Trava de arquivo cooperativa limita escritores Aeris concorrentes; não é defesa contra software malicioso.
- Ao fechar, bloquear, desativar ou limpar sessão, libera referências aos dados e fecha a trava. Sem garantia de eliminação segura da RAM/swap, sem bloqueio automático por inatividade. Registros gravados não são apagados pela limpeza da sessão. Exclusão é lógica, não apagamento seguro de disco.
- DPAPI não protege contra todos os processos executados com a mesma conta, administradores, malware, captura de tela ou cópia manual. A perda do perfil Windows pode impedir recuperação. Não transportar o arquivo como backup portável. Não usar dados reais nesta versão.
- O Search não acessa Vault e não existe rota de exportação ou cópia automatizada.

## Referências
https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata
https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptunprotectdata

## Validação
38 unitários aprovados, 1 teste DPAPI nativo ignorado, 5 smoke tests gráficos aprovados em Linux. TestBackend é um simulador reversível e NÃO criptográfico, restrito a tests/. Não comprova criptografia real. No Windows, executar `py -3 -m unittest discover -v` e os módulos smoke antes de testes manuais de persistência, corrupção, duas instâncias, encerramento e perda de acesso, utilizando dados fictícios. Verificar permissões do diretório, perfil e versão do sistema. Não distribuir antes de validar Windows 10/11 x64.
