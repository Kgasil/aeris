# Aeris Experience 1.1.0rc1 — candidato de desenvolvimento

**Não publicado; não aprovado para distribuição binária.** Branch desktop-experience. A versão pública e os instaladores anteriores não foram alterados. Este identificador separa os artefatos esperados dos anteriores (1.0.0rc5). Não houve build Windows nesta revisão.

## Preparação
- Windows x64 em VM descartável, conta comum para teste de instalação, CPython 3.14 x64 com Tcl/Tk para compilação. Inno Setup 6.3+ de fonte oficial, assinatura válida, somente se gerar instalador.
- Execute `distribution/build.ps1` em PowerShell. Para apenas pacote portátil: `distribution/build.ps1 -PortableOnly`. Não desative proteções do Windows.
- O build deve compilar as fontes, executar regressão e autoteste integrado, criar a distribuição e executar novamente o autoteste no executável. Saídas esperadas: ZIP portátil, instalador (quando solicitado), SHA256SUMS.txt, AERIS-EXE-SHA256.txt, build-dependencies.txt, runtime-reduction.json e build-info.json. Saídas ainda não produzidas.
- PyInstaller fixado no arquivo requirements-build.txt; dependências transitivas ainda não estão integralmente travadas por hash. O corte de DLLs exige inventário e assinaturas válidas; não equivale a aprovação de redistribuição. Argos e áudio interno experimental não são distribuídos no executável; veja desktop/READY.md e desktop/MEETING_EXPERIMENTAL.md.
- O instalador existente mantém AppId e caminho por usuário. Teste de atualização deve ocorrer apenas em VM isolada, com backup de dados fictícios. Não instale sobre uma cópia de trabalho antes da validação. Desinstalação pretende preservar dados; confirme na VM.

## Correções
- Localização e validação do ISCC antes do build, sem exigência no modo portátil.
- Verificação estrutural de cabeçalho PE do instalador; rejeição de links e reparse points nos caminhos verificados.
- Identificação do candidato e atualização do registro de evidências.
- Metadados do build declaram pacote não assinado e sem aprovação para publicação.

## Evidências executadas nesta revisão
Linux, Python 3.13.5, cópias locais. 3 testes do registro de lançamento e 4 testes de cabeçalho PE com dados sintéticos: 7 aprovados, 0 falhas/erros. Os hashes Git do script release-gate.py (ff37f1b2f05f49fee3358306726ef55187aff3e8), do JSON (929ea66ea7fa8e5c2a24e2f5d290466d02ac609e) e do __init__.py (3b4ec64b0c4bde81b6653c5cf6323c3b63e971cd) correspondem ao repositório. Os testes de PE usaram o recorte da função nova, não o verificador completo. A função pending_checks retornou os nove critérios pendentes. Não é teste do instalador real.

A clonagem direta falhou por DNS. GitHub Actions consultado: havia execuções enfileiradas; sem confirmação de regressão integral. O conector permite revisar fontes, não executar o instalador neste ambiente. Não houve assinatura, teste antimalware, auditoria completa de licenças ou hashes de um novo binário.

## Portão de lançamento
Todos os nove critérios de distribution/release-gate.json continuam pendentes. Antes de publicar: build Windows real; testes em Windows 10/11 limpos; atualização, desinstalação e preservação de dados; DPAPI/mutex; dispositivos e Ollama reais; desempenho/acessibilidade; licenças e confiança; verificação de artefatos, hashes e evidências. O gate é um controle de registro, não impede sozinho uploads. Revisão humana obrigatória. Não publicar nem substituir a versão pública nesta fase.
