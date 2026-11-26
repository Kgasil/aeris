# Aeris Autofill — 0.4.0a1

Primeiro incremento desktop: perfis estruturados em autofill.bin, protegidos por DPAPI vinculada à conta Windows, sem fallback em claro. Utiliza Vault com bloqueio de arquivo, gravação atômica e limite de 100 perfis. Campos estritamente permitidos: name, email, tel, organization, organization-title. Conteúdo de campos não é classificado automaticamente como sensível, portanto utilizar somente dados fictícios. Não armazenar senhas, documentos ou dados bancários. Preview cruza campos selecionados e salvos; não detecta campos externos. Cópia manual de um campo por vez, somente com permissão de sessão e confirmação; não há colagem automática nem envio. Search não indexa perfis. Bloqueio no fechamento, desativação e limpeza de sessão. Backup ainda não inclui autofill.bin; não use para dados únicos importantes.

## Próximo incremento contextual

Extensão Chromium MV3, consentimento por origem, ícone discreto próximo a campo suportado, revisão por campo, confirmação antes de preencher, sem submissão automática, sem leitura de senhas, sem injeção em campos ocultos ou iframes não autorizados, sem escuta global. Integração com o cofre desktop precisa de canal autenticado e consentimento por operação; não exportar todo o cofre à extensão. Não implementado neste incremento. Avaliar permissões mínimas, política de distribuição e testes reais no Windows/Chromium antes de uso.

Testes: 90 unitários e 14 gráficos aprovados em Linux, 3 testes nativos Windows ignorados. Backend de cofre simulado nos testes novos; nenhum teste de browser ou DPAPI real executado. Windows 10/11 permanece plataforma-alvo.
