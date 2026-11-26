# Aeris Desktop — procedimento de análise antimalware

Status: procedimento implementado; execução e revisão humana pendentes. O scanner não certifica o aplicativo e não aprova publicação.

## Pré-requisitos
- VM Windows descartável, atualizada, sem dados pessoais, com Microsoft Defender ativo e definições atualizadas (máximo de 24 horas).
- Obter artefato da execução de CI aprovada e comparar seu SHA-256 com o digest registrado pelo GitHub. Conferir hashes individuais do Setup e ZIP contra evidências independentes; não usar hashes calculados exclusivamente a partir de uma cópia desconhecida.
- Manter todas as proteções ativas e revisar exclusões existentes. Não adicionar exclusões, desligar SmartScreen, iniciar o aplicativo ou executar o instalador para analisar o pacote.

## Coleta de evidências
Em PowerShell com privilégios apropriados na VM de teste, executar o script local versionado [scan-candidate.ps1](scan-candidate.ps1), passando os caminhos e hashes previamente verificados:

```powershell
.\validation\installer\scan-candidate.ps1 -SetupPath $setup -SetupSha256 $expectedSetup -PortablePath $portable -PortableSha256 $expectedPortable -EvidenceDirectory .\scan-evidence
```

As variáveis devem ser definidas pelo responsável pela auditoria com os valores do artefato efetivamente revisado. Não executar se houver divergência. O script não baixa artefatos, não inicia o Aeris nem altera a configuração do Defender. Coleta status do motor e definições, logs das duas análises, códigos de saída, detecções recentes e hashes pós-scan. Um retorno zero pode incluir ameaças remediadas; por isso não é aprovação. A saída ARCHIVE_SCAN_COMPLETED_REVIEW_REQUIRED exige revisão dos logs e das exclusões.

Adicionalmente, validar o manifesto com [audit-desktop-bundle.py](../audit-desktop-bundle.py), extrair somente após verificar os caminhos e hashes, em diretório novo da VM, e analisar todo o conteúdo extraído com o Defender. Registrar resultado, escopo e hashes; não executar os binários. Se a análise falhar, houver exclusões relevantes, detecção, remoção ou alteração de arquivo, bloquear e investigar.

## Registro de aprovação
Registrar ID de execução/artefato, hashes SHA-256 do ZIP externo, Setup e portátil, versão/definições do scanner, data, logs e resultado da revisão, avisos e direitos de distribuição, decisão de assinatura e risco residual. Não incluir dados privados. Não publicar artefato diferente; se recompilar ou assinar, repetir a verificação.

Fontes oficiais consultadas em 26/11/2026:
- https://learn.microsoft.com/en-us/defender-endpoint/command-line-arguments-microsoft-defender-antivirus
- https://learn.microsoft.com/en-us/defender-endpoint/use-powershell-cmdlets-microsoft-defender-antivirus
- https://learn.microsoft.com/powershell/module/defender/get-mpcomputerstatus

Nenhum scan nativo executado nesta revisão; script ainda precisa de validação em Windows.
