# Aeris Desktop 1.0.0 — preparação de lançamento

**Não publicado.** O RC4 experimental está aprovado na CI de build e instalação limpa, mas não equivale a 1.0.0 estável. A extensão 1.0.0 continua independente e disponível.

## Checklist de liberação
| Gate | Situação | Evidência ou ação |
| --- | --- | --- |
| Compilação integrada RC3 | PASS | [413 testes, 409 aprovados, quatro skips](../downloads/windows-integrated-rc3-evidence.json) |
| Integridade e origem do código | PASS RC3 | ZIP de 352 arquivos, 91 hashes do manifesto, 71 binários e 17 avisos |
| Revisão dos quatro skips e desempenho exato RC3 | PASS | [Evidência complementar](../downloads/rc3-final-review-evidence.json): quatro testes em Ubuntu; desempenho RC3 aprovado |
| Direitos de distribuição | Pendente | Confirmar autoria/licenças de código, imagens e marca; resolver obrigações de terceiros e proveniência Microsoft |
| Antimalware | Pendente | Executar [procedimento de scan](../validation/installer/SCAN.md) no candidato exato, com proteção ativa |
| Assinatura digital | Pendente | Definir processo de Authenticode e verificar assinatura; não afirmar certificação. RC3 unsigned |
| Windows 10/11 | Pendente | Executar [kit cliente](../validation/windows-client/README.md) em duas VMs suportadas, contas comuns |
| Atualização, recuperação e funções nativas | Parcial | [RC3→RC4](../downloads/rc3-rc4-upgrade-evidence.json) passou; 44 DLLs permanecem após atualização direta. Reinstalação limpa preservou dados fictícios; testar cliente, interrupção, outra conta e ACLs |
| IA, áudio, OCR e acessibilidade cliente | Parcial | Validar funções opcionais, consentimento, dispositivos, Tesseract Windows, Narrator e escala |
| Versão estável 1.0.0 | Bloqueada | Criar build versionado somente com gates anteriores encaminhados; repetir testes e scan no binário final |

## Ordem de lançamento
1. Encerrar as pendências técnicas e de direitos, documentar evidências.
2. Gerar o candidato 1.0.0 real: versão interna, metadados, Setup e ZIP; manter AppId e dados. Atualizar validação de versão para permitir especificamente 1.0.0 após aprovação. Não apenas renomear RC3.
3. Verificar e testar os bytes finais; se assinar, recalcular os hashes e repetir as verificações aplicáveis depois da assinatura. Vincular autorização ao run, artifact ID, commit, digest e hashes de cada asset. Guardar cópia verificável antes da expiração.
4. Publicar somente os assets aprovados, sem recompilar, em uma release versionada; manter releases antigas. Conferir o download e o SHA-256 em sessão externa.
5. Atualizar site, status, README e GRAAL somente com fatos confirmados; manter Extension 1.0.0 separada. Botão direto deve abrir o Setup aprovado, não um ZIP ou artefato temporário.

## Minuta de notas de lançamento (não publicar ainda)
Aeris Desktop 1.0.0 — Eficiência e Simplicidade. Primeira versão estável planejada para Windows x64, com 50 ferramentas locais, instalação por usuário com runtime incluído, IA opcional via Ollama, recursos opcionais de voz e OCR. Sem Python ou terminal para instalar. Edição gratuita. Antes de publicar, substituir esta minuta por resultados reais de compatibilidade, limites, hashes, assinatura e requisitos. Informar dados preservados na desinstalação e instruções de backup. Linkar o canal de relato de bugs: https://github.com/Kgasil/aeris/issues.

**Ações necessárias do titular:** confirmar direitos de redistribuição dos recursos próprios, decidir assinatura e disponibilizar ambiente de teste Windows apropriado. Não tratar autorização para trabalhar no roadmap como autorização para distribuir bibliotecas sem seus direitos comprovados. Nenhuma publicação foi executada.

## Revisão em andamento — 26/11/2026
[Comparação de origem e scanner](../downloads/rc3-distribution-review-evidence.json): 46 DLLs Microsoft não coincidiram byte a byte com REDIST disponível, e ClamAV não chegou a executar o scan por erro de configuração. [Reexecução](https://github.com/Kgasil/aeris/actions/runs/45852715374) pendente. [RC4 experimental](https://github.com/Kgasil/aeris/actions/runs/45852772215) em teste para reduzir cópias de bibliotecas do SO; não equivale ao binário estável. [Decisões do titular e minuta de termos](desktop-distribution-decisions.md). Nenhuma aprovação inferida; Windows cliente e confiança continuam pendentes.


## Revalidação RC4 e scanner — 26/11/2026

[RC4 45852772215](https://github.com/Kgasil/aeris/actions/runs/45852772215) falhou antes de empacotar: 413 testes, 408 aprovados, quatro ignorados e uma falha em `test_native_mutex_cross_process_and_abrupt_exit` após terminar o processo filho. Diagnóstico ZIP 15134333469, SHA-256 `ef8979dac1d89feccf9c127d50f4ed3a53699832a7902f353542d13164830a66`, conferido; fonte mostra que a criação do mutex usa CreateMutexW e detecta ERROR_ALREADY_EXISTS. Hipótese: o executável Python do venv Windows é um redirecionador, e encerrar o launcher pode deixar o detentor real vivo. Corrigido o teste (5fce70a) para usar sys._base_executable e exigir que o PID de prontidão seja o PID do filho antes de terminá-lo. Não alterada implementação do mutex nem removida asserção. [CI nativa 45853291522](https://github.com/Kgasil/aeris/actions/runs/45853291522) aprovada; [RC4 45853309017](https://github.com/Kgasil/aeris/actions/runs/45853309017) em revalidação completa, incluindo venv. Redução de DLLs ainda não comprovada; nenhum Setup RC4 disponível da execução falha.

[Scanner 45852715374](https://github.com/Kgasil/aeris/actions/runs/45852715374) voltou a falhar antes do scan (FreshClam não conseguiu ler configuração temporária). Correção 9c26883 usa configuração e base padrão do pacote Ubuntu, aguarda atualização existente ou chama FreshClam normalmente, exige data de build das definições diárias de até 24 h. [CI 45853334717](https://github.com/Kgasil/aeris/actions/runs/45853334717) iniciada. Não desativar proteções nem alegar scan limpo. RC3 preservado; Windows cliente, direitos, decisão de assinatura e scan do candidato final permanecem pendentes. Não publicar.

## Situação atual do RC4 — 26/11/2026
[Build RC4](../downloads/windows-rc4-reduced-runtime-evidence.json): 409/413 testes Windows, quatro skips, 47 hashes, 27 binários e 17 avisos. Dois VCRUNTIME correspondem à instalação Python de build, sem autorização legal implícita. [Atualização exata](../downloads/rc3-rc4-upgrade-evidence.json): oito manifestos idênticos, reinstalação limpa aprovada, 44 arquivos antigos em atualização direta. Migração documentada, sem exclusão automática. ClamAV RC3 bloqueado por definições com mais de 24h; scan RC4 ainda não executado. Revisão complementar RC4 aprovada em CI. Não gerar ou publicar estável até decisões de direitos, assinatura e testes em Windows cliente; nenhum certificado ou credencial deve ser compartilhado no chat.

- [Revisão complementar RC4 45854218340](https://github.com/Kgasil/aeris/actions/runs/45854218340): quatro testes anteriormente ignorados aprovados em Ubuntu com Tesseract; 413 testes distintos aprovados nos ambientes aplicáveis (409 Windows + 4 Linux). Performance RC4 portátil exato aprovada: inicializações 1,031/0,229/0,234 s, máximo 41.566.208 bytes de working set, CPU ociosa amostrada 0%, encerramento ≤0,055 s. [Evidência verificada](../downloads/rc4-final-review-evidence.json). Gates de segurança, direitos, assinatura e Windows cliente permanecem abertos; nenhuma autorização de publicação.
