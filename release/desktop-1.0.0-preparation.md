# Aeris Desktop 1.0.0 — preparação de lançamento

**Não publicado.** O RC3 experimental está aprovado na CI, mas não equivale a 1.0.0 estável. A extensão 1.0.0 continua independente e disponível.

## Checklist de liberação
| Gate | Situação | Evidência ou ação |
| --- | --- | --- |
| Compilação integrada RC3 | PASS | [413 testes, 409 aprovados, quatro skips](../downloads/windows-integrated-rc3-evidence.json) |
| Integridade e origem do código | PASS RC3 | ZIP de 352 arquivos, 91 hashes do manifesto, 71 binários e 17 avisos |
| Revisão dos quatro skips e desempenho exato RC3 | Em andamento | [CI de revisão](../.github/workflows/aeris-rc3-final-review.yml) |
| Direitos de distribuição | Pendente | Confirmar autoria/licenças de código, imagens e marca; resolver obrigações de terceiros e proveniência Microsoft |
| Antimalware | Pendente | Executar [procedimento de scan](../validation/installer/SCAN.md) no candidato exato, com proteção ativa |
| Assinatura digital | Pendente | Definir processo de Authenticode e verificar assinatura; não afirmar certificação. RC3 unsigned |
| Windows 10/11 | Pendente | Executar [kit cliente](../validation/windows-client/README.md) em duas VMs suportadas, contas comuns |
| Atualização, recuperação e funções nativas | Parcial | Revalidar no candidato exato; falhas durante instalação, outra conta, ACLs e UI instalada pendentes |
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
