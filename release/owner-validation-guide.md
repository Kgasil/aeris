# Aeris Desktop — guia final do titular

**Candidato RC5 experimental. Não é release pública.** As validações devem ocorrer em VMs cliente x64 descartáveis, atualizadas, sem dados pessoais. Não instalar em máquina de produção, desativar proteção, criar exclusões ou contornar SmartScreen.

**Orçamento zero:** não compre Windows, VM, certificado ou conta em loja para estes testes. Use apenas ambientes já disponíveis ou voluntários qualificados. Se indisponível, registre NOT_TESTED e mantenha o lançamento estável adiado. [Plano sem custos](zero-cost-plan.md).

## 1. Obter e verificar o pacote

[CI RC5 45863779585](https://github.com/Kgasil/aeris/actions/runs/45863779585), artefato 15138829732, nome aeris-functional-integrated-rc5-not-a-release. Expiração registrada 26/12/2026 17:03:32 UTC. [Evidência](../downloads/functional-rc5-integrated-evidence.json).

Em PowerShell na pasta do download, use Get-FileHash -Algorithm SHA256 -LiteralPath com o caminho de cada arquivo. Comparar com:

| Arquivo | SHA-256 |
| --- | --- |
| ZIP externo da CI | 09aa2076cac6f9bc8a543869027fe2617f0590fd4509a6f18261def0e797ba9a |
| Aeris-1.0.0rc5-Windows-x64-Setup.exe | 54ab3ab65672a32dc944259bb291f5c66ed735d4c5d5876641725131c9915aa8 |
| Aeris-1.0.0rc5-Windows-x64-portable.zip | ffbda95354b563e1d6a1b8f90fc43184a197585488c3da8609ac6970ffee9701 |
| Aeris.exe | 4cb9ed45a6e9cce9c1f86a9d71e6f915aba987ab3532e034e34bd9300b7d0025 |

Só extrair o ZIP externo se seu hash corresponder; não executar nada. Divergência ou detecção = BLOQUEADO. O hash confirma identidade com o candidato, não ausência de malware.

## 2. Defender (antes da execução)
Na VM, Segurança do Windows > Proteção contra vírus e ameaças > Atualizações de proteção: verificar atualizações e confirmar proteção em tempo real ativa e definições de até 24h. Revisar exclusões. Registrar versão/horário das definições e resultados sem dados pessoais.
Analisar o Setup e ZIP portátil exatos; após verificar a identidade do ZIP portátil, extrair para uma pasta nova na VM e analisar todos os arquivos extraídos. Usar verificação personalizada do Defender ou [coletor oficial do projeto](../validation/installer/scan-candidate.ps1) segundo [SCAN.md](../validation/installer/SCAN.md). Conferir logs, detecções e hashes após exame; zero detecções não garante segurança absoluta. Não executar se qualquer proteção bloquear, houver detecção, divergência, exclusão relevante ou análise incompleta.

## 3. Windows cliente
Executar [protocolo W01–W10](../validation/windows-client/README.md) em Windows 11 e Windows 10 suportado/atualizado, duas VMs limpas, conta comum, sem Python externo. Guardar evidências separadas por edição/build e hash. 
- Instalação via Explorer, sem elevação inesperada, atalhos e opção de abrir desmarcada.
- Abrir Hub, conferir 50 ferramentas e testar funções locais, configurações fictícias e segunda instância.
- Reinstalar mesma versão, conferir dados; desinstalar e confirmar atalhos/programa removidos, dados preservados. Repetir com opção de atalho desmarcada.
- Migração de prévia anterior: somente em ambiente descartável e após análise dos dois artefatos; RC4→RC5 passou em CI com zero DLLs obsoletas, oito manifestos idênticos e rollback controlado. RC3→RC4 histórico deixou 44 DLLs; reinstalação limpa passou em CI. Fazer backup, usar desinstalação normal quando aplicável, nunca exclusão manual. [Procedimento](../validation/installer/UPGRADE-RECOVERY.md).
- Repetir [segurança nativa](../validation/native-security/README.md), [IA local](../validation/local-ai/README.md), [áudio/OCR](../validation/audio-ocr/README.md) e [acessibilidade/desempenho](../validation/performance/README.md) aplicáveis: dados fictícios, consentimento, DPAPI entre duas contas comuns, mutex, ACL, voz pt-BR, microfone autorizado, Tesseract local, Ollama opcional, teclado/Narrator/alto contraste/escalas 100/150/200%. Registrar bloqueios e não testar recursos que exigem dados reais. Teste breve não substitui checklist completo.

## 4. Decisões do titular (não presumidas)
- Confirmar autoria ou autorização para código, marca, imagens, ícones e demais recursos; listar origem/licença de cada recurso externo. Escolher licença do código próprio e licença de uso do aplicativo. Gratuito não implica open source.
- Confirmar finalidade e enquadramento Inno Setup; revisar condições Microsoft do PYTHON-LICENSE e licença das duas DLLs VCRUNTIME remanescentes. Aprovar termos compatíveis e mecanismo de aceite quando exigido. Não confundir decisão do titular com prova de direitos de terceiros.
- Decidir assinatura Authenticode: recomendada para distribuição estável. Sem assinatura, considerar somente prévia explicitamente experimental após os demais gates, sem bypass. Não compartilhar certificado/chave/token/senha. Ver [decisões](desktop-distribution-decisions.md).
- Confirmar escopo de suporte Windows 10/11 conforme testes e suporte de segurança; não prometer compatibilidade não testada.

## 5. Resposta do titular (modelo)
Windows edição/build: 
VM limpa, conta comum, sem Python: PASS/FAIL/NOT_TESTED
Hash externo / Setup / portátil / EXE: PASS/FAIL/NOT_TESTED
Defender ativo, versão e data das definições:
Scan Setup / ZIP / pasta extraída: PASS/FAIL/NOT_TESTED
Detecções ou bloqueios:
Instalação / abertura / atalhos:
Reinstalação / dados / desinstalação:
IA / OCR / voz / microfone / permissões:
DPAPI entre contas / mutex / ACL:
Teclado / Narrator / alto contraste / escala:
Direitos próprios e recursos de terceiros (fontes/licenças):
Licença desejada:
Assinatura digital:
Observações / IDs dos relatórios:
Cada PASS precisa de observação real; enviar apenas evidência técnica de ambiente sintético, sem dados pessoais.

## 6. Próximo candidato estável
Após revisão dos bloqueios, preparar versão interna 1.0.0 real, termos e assinatura conforme decisão, gerar e verificar seus próprios hashes; repetir testes aplicáveis e scan nos bytes finais. Publicar somente artefato exato aprovado. RC5 não pode ser renomeado como 1.0.0; extension 1.0.0 permanece independente. Atualizar ecossistema GRAAL após lançamento.

Status: instruções e modelo preparados. Nenhum teste cliente executado ou direito confirmado por este documento.

## 7. Download direto após aprovação

O site está preparado para exibir o botão público somente quando a prévia `aeris-desktop-1.0.0rc5-preview` for efetivamente publicada com o Setup exato, tamanho 12.792.748 bytes e SHA-256 indicado acima, conforme metadados da API de Releases. Não publicar sem revisar direitos, scan e testes cliente aplicáveis. A publicação não exige recompilar o RC5. Testar o download sem login e sem redirecionamento para Actions, conferir bytes e testar instalação em ambiente cliente limpo. Se for adotado um candidato diferente, atualizar a configuração para os novos bytes verificados. O scan ClamAV RC5 foi bloqueado por definições vencidas; não há resultado antimalware válido.
