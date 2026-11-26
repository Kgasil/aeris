# Etapa 12 — revisão integrada do Aeris Desktop

## Candidato e rastreabilidade
O candidato RC3 (1.0.0rc3) é experimental, não publicado. O [workflow integrado](../.github/workflows/aeris-integrated-candidate.yml) parte do ZIP histórico Fix 1 com hash verificado, aplica os overlays previamente testados (runtime, Timeline, PyInstaller, verificador, Inno, avisos), integra testes nativos e loopback ao conjunto de regressão e gera um ZIP do código-fonte efetivamente preparado antes do build. A receita de avisos usa arquivos locais dentro desse ZIP, não um checkout externo. O ZIP fonte registra SHA-256 e commit do workflow; não é garantia de reprodução bit a bit. Preservar RC1/RC2, AppId, esquema, dados e identidade visual. Extension 1.0.0 não alterada.

## Matriz de evidências
| Área | Evidência anterior | Critério no RC3 |
| --- | --- | --- |
| Instalador e 50 ferramentas | [RC1 atualizado](../downloads/windows-inno674-notices-evidence.json), [RC2](../downloads/windows-rc2-upgrade-evidence.json) | Regressão completa, catálogo de 50 ferramentas, autoteste de construção de janelas, instalação/reinstalação/desinstalação e hashes |
| Atualização | [RC1→RC2](../downloads/windows-rc2-upgrade-evidence.json) | Repetir atualização entre versões do candidato final; falha durante instalação ainda não testada |
| Segurança nativa | [7 testes](../downloads/windows-native-security-evidence.json) | Reexecutar cinco novos testes e regressão existente; outras contas, ACL e instância instalada ainda pendentes |
| IA | [29 testes e Ollama real](../downloads/local-ai-validation-evidence.json) | Reexecutar protocolo e regressão; inferência e UI Windows ainda exigem evidência específica |
| Áudio e OCR | [20 testes](../downloads/audio-ocr-validation-evidence.json) | Regressão; Tesseract Windows e dispositivos físicos exigem VM cliente |
| Desempenho e acessibilidade | [RC2 e fonte](../downloads/performance-accessibility-evidence.json) | Reexecutar smoke do leitor; medir RC3 exato após build; Narrator, escala e contraste do SO pendentes |
| Distribuição | [Auditoria](desktop-distribution-audit.md), [confiança](desktop-trust-review.md) | Verificar binários e avisos do RC3, direitos, scan real, decisão de assinatura, sem publicação automática |

O workflow mantém a lista de testes ignorados visível por meio de unittest -v. Testes de UI confirmam construção de janelas e smoke específico, não uso completo de todas as ferramentas. Resultados de versões anteriores não certificam o RC3. Todos os artefatos são temporários e não são releases.

## Gates obrigatórios para etapa 13
- Windows 10 e 11 cliente com conta comum e evidência do pacote exato.
- Revisão de todas as falhas e skips, incluindo dependências opcionais e cobertura funcional.
- Revisão de distribuição e direitos de primeira e terceira partes, proveniência Microsoft, scan antimalware efetivo com proteções ativas e decisão documentada de assinatura. App não assinado até prova em contrário.
- Candidato final aprovado, sem diferenças de bytes depois da revisão. Publicação em versão estável exigirá novo candidato 1.0.0 e repetição das verificações aplicáveis. Não renomear RC3 como 1.0.0.
- Checklist de site, README, download, hashes, canal de reporte e documentação das limitações.

Status: revisão integrada iniciada, resultados do RC3 pendentes. Sem acesso às VMs cliente ou aprovação de distribuição, a etapa 13 permanece bloqueada.
