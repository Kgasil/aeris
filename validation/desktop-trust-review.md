# Aeris Desktop — revisão de segurança e licenciamento (etapa 04)

Data: 26/11/2026. Estado: **BLOQUEADO PARA PUBLICAÇÃO**. Este documento registra revisão técnica, não autorização jurídica, certificação ou resultado antimalware.

## Artefato auditado
O [artefato 15130517282](../downloads/windows-simplified-preview-evidence.json) passou em CI Server 2022, com 395 testes aprovados e 1.002 hashes conferidos após download. Setup.exe e Aeris.exe não assinados. O pacote permanece experimental.

## Decisões técnicas e fontes oficiais
| Componente | Achado | Decisão |
| --- | --- | --- |
| CPython 3.12.10 | Último instalador binário oficial da série 3.12; 3.12.16 contém correções posteriores (incluindo CVE-2024-3220). | Testar 3.14.10, versão com binário Windows e correções de segurança, em CI separada. Não substituir histórico. |
| OpenSSL 3.0.16 | A versão é atingida, por exemplo, por CVE-2025-9232 e CVE-2025-9230; a série 3.0 perdeu suporte público em 07/09/2026. | Exigir runtime candidato com série suportada 3.5 ou superior e revisar versão efetiva e advisories antes de aprovar. Não alegar exploração no Aeris sem análise de alcançabilidade. |
| Inno Setup 6.7.1 | 6.7.4 de 28/10/2026 inclui correções, inclusive de RedirectionGuard. | Registrar versão, hash, assinatura e licença do compilador atual; avaliar atualização para 6.7.4 ou versão posterior suportada com origem oficial verificada. Não instalar compilador sem verificar origem. |
| CPython / Tcl/Tk / PyInstaller | PSF v2, termos Tcl/Tk e exceção de empacotamento PyInstaller permitem distribuição condicionada aos termos aplicáveis. | Preservar avisos exatos; verificar licença do runtime candidato e das dependências realmente distribuídas, não apenas freeze do build. |
| OpenSSL / zlib / libffi / bzip2 / expat / XZ / mpdecimal / Unicode | Bibliotecas com termos distintos; inventário anterior tem lacunas de versão e avisos. | Reconciliar versão e texto integral de cada componente com a origem real no novo pacote. |
| UCRT e API sets | Microsoft informa que Windows 10/11 usam o UCRT do sistema mesmo com cópia local; arquivos app-local redistribuíveis provêm do SDK redist. | Planejar teste separado de remoção apenas das cópias app-local desnecessárias; verificar origem de MSVC runtime e direitos; manter validação em Windows limpo. |
| Inno Setup | O fornecedor solicita aquisição de licença para uso comercial, inclusive CI. | Confirmar enquadramento comercial e termos da versão efetiva; não declarar licença comprada ou autorização presumida. |
| Aeris e recursos próprios | README não especifica licença própria; uso gratuito não equivale a autorização irrestrita. | O titular precisa confirmar direitos sobre código/ícones/recursos e os termos de uso da distribuição gratuita. Não atribuir licença sem autorização. |
| Authenticode | Instalação e hashes aprovados não equivalem a assinatura. | Recomendar assinatura verificável antes da versão estável; prévia sem assinatura somente se risco e termos aceitos explicitamente após demais gates. Não desativar proteções. |

Fontes: [Python 3.12.16](https://www.python.org/downloads/release/python-31216/), [Python 3.14.10](https://www.python.org/downloads/release/python-31410/), [OpenSSL advisories 3.0](https://openssl-library.org/news/vulnerabilities-3.0/), [EOL OpenSSL 3.0](https://openssl-library.org/post/2026-09-16-eol30/), [Inno Setup 6](https://jrsoftware.org/files/is6-whatsnew.htm), [licenciamento comercial Inno Setup](https://jrsoftware.org/inno-setup/purchase), [PSF](https://docs.python.org/3.12/license.html), [PyInstaller](https://pyinstaller.org/en/stable/license.html), [UCRT](https://learn.microsoft.com/en-us/cpp/windows/universal-crt-deployment), [Microsoft VC redist](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files). Consulta em 26/11/2026; reavaliar advisories quando o candidato estiver pronto.

## Candidato de atualização
[Workflow separado](../.github/workflows/aeris-windows-security-candidate.yml), commit 26ed9ac, [run 45845715571](https://github.com/Kgasil/aeris/actions/runs/45845715571). Python 3.14.10 x64 fixado, verificação da série OpenSSL, adaptação limitada da receita e do validador, regressão e testes de instalação iguais aos do candidato anterior. Inventário de hashes, versões e assinaturas dos binários e tentativa de coleta da licença do compilador. Estado do Defender é coletado quando disponível, mas isso **não é** um scan. A CI não publica releases e não altera o ZIP histórico. Resultados ainda pendentes.

## Revisão obrigatória para o artefato final
- Identificar o SHA-256 exato de Setup.exe, ZIP e arquivo de CI; verificar manifesto completo e preservar evidências.
- Comparar avisos, versões, proveniência dos DLLs e termos reais com o inventário atualizado. Registrar os textos integrais e aprovação do titular; não usar este documento como aprovação.
- Em VM descartável Windows atualizada, com proteção ativa e definições recentes, verificar o instalador e o conteúdo extraído do ZIP por scanner confiável, sem executar o instalador para fazer a análise. Guardar versão do motor, definições, data, escopo, resultado e hashes. Se houver detecção ou scanner indisponível, bloquear e investigar; não desligar antivírus, adicionar exclusões ou orientar bypass de SmartScreen.
- Rever vulnerabilidades conhecidas do runtime e demais bibliotecas. Registrar risco residual e decisão de confiança/assinatura. Scan limpo não prova ausência de malware.
- Publicar apenas os bytes analisados (sem rebuild após aprovação). Caso assine ou altere o instalador, conferir novos hashes e reavaliar o artefato resultante. Não criar release estável antes da validação restante.

**Conclusão:** revisão documental e ação corretiva de runtime iniciadas. Licenças, malware scan, atualização do compilador e decisão de assinatura continuam pendentes. A etapa 05 não foi autorizada.
