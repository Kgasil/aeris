# Aeris Desktop RC1 — Auditoria de distribuição / Distribution audit
Data: 2026-11-26. Status: inventário histórico verificado; autorização de redistribuição PENDENTE. Este documento não é aprovação jurídica, de segurança ou de lançamento.

## Evidência inspecionada
- [CI run 45730507059](https://github.com/Kgasil/aeris/actions/runs/45730507059), artifact 15076935274, commit cdb8163c4d7e2afb7969b0ae59c9f6641a77058f.
- Arquivo de CI, ZIP portátil e Setup.exe conferidos contra [evidência publicada](../downloads/windows-preview-evidence.json): SHA-256 respectivamente 67f3a5aa1131ce612d82627e7e500dfed64305a03f9a806a97173625ed8d33a7, f076ab5d766121f318847d803295796ba32022c0f27092542a9911dd120a3a08 e 20a5f376e62f67e941dba3e4027814992c03165008ea309581e442543d425830.
- 1.003 entradas no ZIP portátil: manifesto mais 1.002 arquivos listados. Todos os 1.002 hashes conferem, sem entradas adicionais além do próprio manifesto. Aeris.exe SHA-256 007d397c3c7f20329043414b3c2cb3f2009a5ad109b34374f0efeb8946e96f4f.
- O log de instalação confirma cópia de PYTHON-LICENSE.txt e quatro avisos em NOTICES. O instalador não foi extraído nem executado nesta auditoria; a evidência do conteúdo instalado vem do log. O runner usava conta administrativa em modo de instalação por usuário, não uma conta comum validada.
- Versões abaixo extraídas de recursos PE, strings de binários, build-dependencies.txt e install.log; não inferir versões não verificadas.

## Inventário de distribuição (artefato histórico)
| Componente | Versão/evidência | Termos e ação |
| --- | --- | --- |
| Aeris.exe, catálogo e recursos próprios | 1.0.0rc1 | README informa que licença própria não foi especificada. Autorizar distribuição de binários e definir termos de uso; verificar titularidade de todos os recursos. Gratuito não equivale a código aberto. |
| CPython e extensões padrão, base_library.zip | 3.12.10 (strings de python312.dll); PE 3.12.10150.1013 | PSF e termos de componentes incluídos; PYTHON-LICENSE.txt presente, preservar texto e conferir com versão exata. |
| Tcl/Tk | 8.6.15 (strings), tcl86t.dll/tk86t.dll; scripts Tcl/Tk | Licença permissiva Tcl/Tk; duas cópias de license.terms em NOTICES, além de _tk_data/license.terms. Preservar. |
| PyInstaller bootloader | 6.19.0 no freeze | GPL-2.0 com exceção de empacotamento e arquivos específicos Apache-2.0; COPYING presente. Não implica GPL para o aplicativo por si só. |
| PyInstaller hooks contrib | 2026.10 no freeze | LICENSE presente; distinguir hooks de build e código efetivamente distribuído. |
| OpenSSL | 3.0.16 (libcrypto-3.dll/libssl-3.dll) | Apache-2.0. PYTHON-LICENSE.txt contém texto Apache mas não menciona OpenSSL nominalmente; adicionar/verificar avisos e LICENSE/NOTICE da versão correspondente. Revisar atualizações de segurança. |
| libffi | libffi-8.dll; versão exata não confirmada | Texto libffi presente no PYTHON-LICENSE.txt; identificar versão e origem. |
| zlib | 1.3.1.0 no recurso de zlib1.dll | zlib license; nome não encontrado no arquivo PYTHON-LICENSE.txt. Incluir/verificar aviso da versão. |
| bzip2 | _bz2.pyd; licença incluída cita 1.0.8, binário não confirmou versão | Preservar aviso; confirmar versão efetivamente vinculada. |
| expat, liblzma/XZ, mpdecimal, Unicode data | pyexpat.pyd, _lzma.pyd, _decimal.pyd, unicodedata.pyd | Verificar versões e termos de terceiros no build CPython; nomes não encontrados no PYTHON-LICENSE.txt. Não presumir que a licença PSF cobre todos os componentes. |
| MSVC runtime | VCRUNTIME140.dll e VCRUNTIME140_1.dll 14.42.34438.0 | Confirmar origem e direito de redistribuição (incluindo termos repassados pelo Python, quando aplicáveis). |
| Microsoft UCRT / API sets | ucrtbase.dll 10.0.26100.1742 + 42 api-ms-*.dll | Confirmar proveniência de cada DLL e se redistribuição app-local é permitida/necessária. Preferir componentes do Windows quando compatíveis; não copiar DLLs arbitrárias do sistema. Validar em VM limpa se remover qualquer arquivo. |
| Inno Setup | 6.7.1 (install.log), instalador e desinstalador gerados | Revisar licença da versão específica, componentes incorporados e pedido de licença comercial se houver uso comercial. Não assumir obrigação de compra apenas por distribuir freeware. |
| Ollama/modelos, Tesseract/dados de idioma, Argos | PREVIEW.txt declara instalação separada ou opção source-only; não encontrados como executáveis/modelos no ZIP portátil | Não incorporar sem revisão independente dos modelos, bibliotecas e assets; validar funcionalidades reais depois. |
| Áudio, fontes, ícones, outros recursos | titularidade e versões ainda não completamente estabelecidas | Revisar código-fonte, manifesto de módulos empacotados, arquivos incorporados e proveniência de recursos. |

## Ambiente de build (não presumir que todos os pacotes são distribuídos)
altgraph 0.17.5; packaging 26.4; pefile 2024.8.26; pip 25.0.1; pyinstaller 6.19.0; pyinstaller-hooks-contrib 2026.10; pywin32-ctypes 0.2.3; setuptools 84.2.1. Inventariar módulos incluídos em PYZ e base_library.zip na próxima compilação; freeze não prova presença em runtime. Fixar versões de build e registrar versão de Python e ferramentas no próximo CI.

## Fontes oficiais consultadas
- https://docs.python.org/3.12/license.html — PSF, termos de bibliotecas e código Microsoft redistribuível.
- https://pyinstaller.org/en/stable/license.html — exceção de empacotamento; o COPYING da versão efetiva está no artefato.
- https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files — restrições de redistribuição do runtime.
- https://learn.microsoft.com/en-us/cpp/porting/upgrade-your-code-to-the-universal-crt — opções e recomendações de implantação UCRT.
- https://jrsoftware.org/files/is6-whatsnew.htm e https://jrsoftware.org/inno-setup/purchase — termos e política de licenças comerciais Inno Setup. Conferir LICENSE.TXT da versão 6.7.1 antes de aprovar.

## Gates / ações corretivas
1. Coletar licença e avisos oficiais das versões exatas (incluindo avisos incorporados no CPython e dependências de bootloader/instalador); documentar proveniência e hashes. Não substituir avisos completos por esta tabela.
2. Registrar licença/termos próprios e autorização expressa do titular, inclusive recursos gráficos. Confirmar uso não comercial/comercial e direitos Microsoft/Inno Setup.
3. Adicionar inventário e verificação de avisos ao build, validar conteúdo real do próximo Setup.exe/ZIP, revisar binários e vulnerabilidades. Não publicar antes de revisão de confiança e redistribuição específica do artefato.
4. Manter o gate de publicação fechado. Não usar este arquivo como referência de aprovação; ele registra lacunas, não uma liberação.

Conclusão: inventário histórico produzido, hashes conferidos, lacunas identificadas. Revisão final de componentes incorporados, direitos e termos próprios permanece aberta. A etapa 02 (instalador simplificado) pode avançar de forma independente sem publicar binários.

## Etapa 04 — novo instalador simplificado (26/11/2026)

[Run 45844861678](https://github.com/Kgasil/aeris/actions/runs/45844861678), artifact 15130517282: [evidência e hashes](../downloads/windows-simplified-preview-evidence.json). O arquivo externo, o Setup.exe, o ZIP portátil, o executável interno e todos os 1.002 arquivos do manifesto foram verificados independentemente após download. Comparação de manifestos com o artefato histórico: nenhuma entrada adicionada ou removida; somente Aeris.exe e _internal/base_library.zip mudaram. Os 68 binários e seis avisos continuam presentes. Portanto, as lacunas de licença da etapa 01 permanecem; não há aprovação implícita por igualdade de inventário.

- Setup.exe e Aeris.exe não possuem tabela de certificados PE; a CI também relata NotSigned para Aeris.exe. Não há comprovação de assinatura. Não contornar SmartScreen/Defender.
- Log de instalação: modo administrativo **No**, raiz HKEY_CURRENT_USER, modo 64-bit **Yes**. A conta da CI tinha privilégios administrativos; teste com usuário comum em Windows 10/11 permanece pendente.
- A CI comprovou instalação, reinstalação, desinstalação, atalhos, ausência de abertura silenciosa e preservação de dados fictícios. Não comprova segurança completa, instalação interativa ou atualização entre versões.
- Não foi realizado malware scan: ambiente sem scanner configurado e atualizado. A análise estática de integridade não substitui antivírus ou análise de vulnerabilidades.
- Publicação deve usar **exatamente** os bytes revisados, sem recompilar depois da aprovação. Registrar SHA-256 do artefato e dos dois downloads, evidência de scanner, licença/avisos e decisão de assinatura vinculada àquele artefato. Um campo de texto genérico não constitui aprovação.

Status: revisão técnica inicial concluída; autorização de redistribuição, análise de vulnerabilidades/malware e decisão formal de confiança continuam pendentes. Não publicar a prévia permanente até fechar esses gates.

## Candidato de segurança aprovado em CI — 26/11/2026

[CI 45846890963](https://github.com/Kgasil/aeris/actions/runs/45846890963), artifact 15130134767, commit 1b3106a; [evidência independente e hashes](../downloads/windows-security-candidate-evidence.json). 401 testes (397 aprovados, quatro ignorados), autotestes de interface, instalação/reinstalação/desinstalação, atalhos e preservação de dados fictícios passaram. O verificador independente foi testado no artefato histórico e no novo e rejeitou digest externo incorreto; os 78 arquivos e os hashes dos 71 binários conferiram com o manifesto. A redução de arquivos frente ao pacote antigo é consistente com os recursos Tcl/Tk 9 incorporados nas DLLs, não perda comprovada de funcionalidade.

Inventário efetivo: Python 3.14.10, OpenSSL 3.5.9, Tcl/Tk 9.0.4, zlib 1.3.2; PyInstaller 6.22.3 no freeze; MSVC 14.51.36247.0, UCRT 10.0.26100.1742 e 43 API sets. 66 binários com Authenticode Valid na CI e cinco NotSigned (Aeris.exe, libtommath.dll, tcl90.dll, tcl9tk90.dll, zlib1.dll); Linux não revalidou a cadeia Authenticode. Inno Setup 6.7.1 confirmado no log (recurso FileVersion do compilador reporta 0.0.0.0), assinatura do compilador Valid. A licença efetivamente coletada do compilador concede uso, inclusive comercial, e redistribuição condicionada; conferir condições e política comercial do fornecedor antes da aprovação. Quatro arquivos de avisos: Python, Tcl/Tk, PyInstaller e hooks contrib. PYTHON-LICENSE menciona libffi, bzip2 e Microsoft, mas não nominalmente OpenSSL, zlib, expat, lzma, mpdecimal ou Unicode; revisar avisos específicos e incluir libtommath e zstd no inventário (DLL e extensão _zstd.pyd). Não presumir cobertura completa por licença agregada. Os 43 API sets e UCRT continuam exigindo confirmação de proveniência e direitos.

Defender no runner: AntivirusEnabled=true, RealTimeProtectionEnabled=false, definições 1.463.480.0. **Scan não executado**, proteção não alterada; o procedimento existente exige proteção ativa e deve ser executado em VM apropriada. Assinatura do aplicativo, direitos de distribuição, atualização do compilador e aprovação final pendentes. Não usar CI aprovada como autorização para publicação.
