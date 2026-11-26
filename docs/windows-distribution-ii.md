# Windows Distribution II — v0.13.0a2

## Evidências disponíveis

Linux/Xvfb: 394 unitários executados (388 aprovados, 6 ignorados por dependerem de Windows), 60 scripts gráficos aprovados. Nove novos testes unitários (oito do verificador, um de dispatch). O teste gráfico de distribuição agora usa `--self-test-full` por chamada à função: 43 ferramentas opcionais não dependentes de DPAPI, Privacy, Permissions e Spotlight, além do Hub. Vault, Bookmarks e Autofill são abertos por esse autocheck em Windows, não em Linux; outros testes gráficos usam dublês. Sem modelo real, captura de áudio, execução nativa ou instalação nesta entrega.

## Controles de build

- `aeris.release_check` constrói ZIP portátil com inventário SHA-256 de cada arquivo, incluindo arquivos ocultos, e o verifica antes de continuar. Rejeita caminhos não relativos ao bundle, componentes reservados, colisões de nomes sem distinção de maiúsculas, membros não regulares, arquivos/membros ausentes, manifesto inválido, limite de 512 MiB descompactado/10 mil entradas e hashes divergentes. A validação confere a assinatura e máquina AMD64 dos cabeçalhos PE do executável principal e da DLL Python 3.12; não é análise completa do PE nem detecção de malware.
- A construção verifica os hashes externos dos artefatos após a compilação. O bootstrapper do Inno pode ter outra arquitetura, portanto apenas sua assinatura MZ é conferida. O verificador não autentica a origem dos arquivos. SHA-256 não substitui assinatura digital ou manifesto obtido por canal confiável.
- O autocheck `--self-test-full` usa diretório de preferências temporário, sem abrir arquivos pessoais, acionar microfone, gerar lembretes, consultar IA ou acessar clipboard. Abre e fecha as 46 janelas opcionais no Windows, além das três interfaces centrais e do Hub. Não valida as operações internas de cada ferramenta. O build interrompe se o autocheck retornar erro ou exceder 90 s.
- O build registra `AERIS-EXE-SHA256.txt` para comparação da cópia portátil/instalada com a origem confiável.

## Procedimento de validação ainda a executar

1. Em VM de construção Windows x64, seguir `windows-distribution.md` e executar `distribution/build.ps1`. Não usar artefatos parciais. Preservar hashes, dependências, avisos de licença e log do build. Verificar os hashes externos com uma origem confiável e realizar análise de segurança/licenças antes de redistribuir.
2. Em VM descartável Windows 10 x64 e outra Windows 11 x64, com conta comum e sem Python externo, testar a versão portátil extraída de ZIP verificado. Executar o script fornecido de validação (somente em VM e com hash do EXE obtido no build confiável):

```powershell
.\distribution\validate-windows.ps1 -AerisExe 'C:\Test\Aeris\Aeris.exe' -ExpectedExeSha256 '<HASH DO BUILD>' -Mode Portable -ConfirmTestVM
```

3. Instalar manualmente pelo wizard, verificar ausência de elevação por padrão, destino e atalhos. Rodar a mesma verificação em `-Mode Installed`, apontando para o EXE instalado. O script não instala nem desinstala, não altera políticas de segurança e não verifica o conteúdo completo do bundle instalado; isso deve ser feito por comparação com os arquivos do build. Registrar JSON e capturas do wizard. Não desabilitar SmartScreen/antivírus.
4. Com dados fictícios, seguir a matriz de instalação, atualização, reinstalação e desinstalação do documento anterior. Confirmar que os arquivos `%LOCALAPPDATA%\Aeris` permanecem e são legíveis após reinstalação. Testar DPAPI real, permissões, mutex, gravação e recuperação; verificar que arquivos pessoais não são removidos. Testar IA local e áudio separadamente. Medir tamanho, RAM/CPU e latência.

| Evidência | Estado |
|---|---|
| Código-fonte e autocheck gráfico Linux | Aprovado |
| Verificador de artefatos com dados sintéticos | Aprovado |
| Execução dos scripts PowerShell e Inno | Pendente |
| Artefatos Windows reais | Não construídos |
| VM Windows 10 e 11, instalação e desinstalação | Pendente |
| Criptografia, voz, IA reais | Pendente |
| Revisão de licenças e confiança do executável | Pendente |
| Publicação de binários | Bloqueada pela validação |

Não apresentar a pré-alpha como release candidate instalável sem os resultados acima. A próxima entrega pode consolidar documentação e preparação da publicação, mas o lançamento depende de execução nativa e correções necessárias.
