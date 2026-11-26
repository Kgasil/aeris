# Aeris Desktop — guia final do titular

**Candidato RC4 experimental. Não é release pública.** As validações devem ocorrer em VMs cliente x64 descartáveis, atualizadas, sem dados pessoais. Não instalar em máquina de produção, desativar proteção, criar exclusões ou contornar SmartScreen.

**Orçamento zero:** não compre Windows, VM, certificado ou conta em loja para estes testes. Use apenas ambientes já disponíveis ou voluntários qualificados. Se indisponível, registre NOT_TESTED e mantenha o lançamento estável adiado. [Plano sem custos](zero-cost-plan.md).

## 1. Obter e verificar o pacote

[CI RC4 45853309017](https://github.com/Kgasil/aeris/actions/runs/45853309017), artefato 15134209156, nome aeris-reduced-runtime-rc4-not-a-release. Expiração registrada 26/12/2026 15:53:44 UTC. [Evidência](../downloads/windows-rc4-reduced-runtime-evidence.json).

Em PowerShell na pasta do download, use Get-FileHash -Algorithm SHA256 -LiteralPath com o caminho de cada arquivo. Comparar com:

| Arquivo | SHA-256 |
| --- | --- |
| ZIP externo da CI | 34e010bb31a574211185f9b6729669c1b7a794856fdbbf10ae425b665aba6d8b |
| Aeris-1.0.0rc4-Windows-x64-Setup.exe | eacbccd22ffeb8b2961fe838c321c61bc63445c08da6aea97b4ed3aa5e09452a |
| Aeris-1.0.0rc4-Windows-x64-portable.zip | 133ee4b5f861535740dca98639d6e4ed4c4fcc15079362434d203b61f498574f |
| Aeris.exe | 05272bdfa2be694cba686171a91a55d51c9ff014344b91ba33fe77a47be5b37e |

Só extrair o ZIP externo se seu hash corresponder; não executar nada. Divergência ou detecção = BLOQUEADO. O hash confirma identidade com o candidato, não ausência de malware.

## 2. Defender (antes da execução)
Na VM, Segurança do Windows > Proteção contra vírus e ameaças > Atualizações de proteção: verificar atualizações e confirmar proteção em tempo real ativa e definições de até 24h. Revisar exclusões. Registrar versão/horário das definições e resultados sem dados pessoais.
Analisar o Setup e ZIP portátil exatos; após verificar a identidade do ZIP portátil, extrair para uma pasta nova na VM e analisar todos os arquivos extraídos. Usar verificação personalizada do Defender ou [coletor oficial do projeto](../validation/installer/scan-candidate.ps1) segundo [SCAN.md](../validation/installer/SCAN.md). Conferir logs, detecções e hashes após exame; zero detecções não garante segurança absoluta. Não executar se qualquer proteção bloquear, houver detecção, divergência, exclusão relevante ou análise incompleta.

## 3. Windows cliente
Executar [protocolo W01–W10](../validation/windows-client/README.md) em Windows 11 e Windows 10 suportado/atualizado, duas VMs limpas, conta comum, sem Python externo. Guardar evidências separadas por edição/build e hash. 
- Instalação via Explorer, sem elevação inesperada, atalhos e opção de abrir desmarcada.
- Abrir Hub, conferir 50 ferramentas e testar funções locais, configurações fictícias e segunda instância.
- Reinstalar mesma versão, conferir dados; desinstalar e confirmar atalhos/programa removidos, dados preservados. Repetir com opção de atalho desmarcada.
- Migração de prévia anterior: somente em ambiente descartável e após análise dos dois artefatos; atualização direta RC3→RC4 deixa 44 DLLs. Reinstalação limpa passou em CI, com backup, desinstalação normal e instalação nova, sem exclusão manual. [Procedimento](../validation/installer/UPGRADE-RECOVERY.md).
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
Após revisão dos bloqueios, preparar versão interna 1.0.0 real, termos e assinatura conforme decisão, gerar e verificar seus próprios hashes; repetir testes aplicáveis e scan nos bytes finais. Publicar somente artefato exato aprovado. RC4 não pode ser renomeado como 1.0.0; extension 1.0.0 permanece independente. Atualizar ecossistema GRAAL após lançamento.

Status: instruções e modelo preparados. Nenhum teste cliente executado ou direito confirmado por este documento.
