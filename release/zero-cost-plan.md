# Aeris — Plano de distribuição sem custos (26/11/2026)

Decisão do titular: não incorrer em despesas para publicar no Windows ou em lojas. O projeto continuará gratuitamente pelo GitHub e GitHub Pages, dentro dos limites gratuitos disponíveis. Não adquirir certificados, assinaturas de serviços, licenças de ferramentas pagas, contas de loja ou infraestrutura de teste paga.

## O que muda
- Microsoft Store, Chrome Web Store e outras lojas: fora do escopo atual. Extension 1.0.0 permanece no GitHub, com instalação manual.
- Authenticode pago: adiado. Qualquer futura distribuição sem assinatura deve ser explicitamente experimental, com hashes e limitações, após revisão de direitos e segurança. Não alegar assinatura nem instruir desativar SmartScreen/antivírus. Uma opção gratuita legítima de assinatura poderá ser avaliada caso o projeto se qualifique; nenhuma contratação automática.
- Windows cliente: validação gratuita em ambiente descartável disponível ou por colaboradores voluntários, sem comprar licença/VM. Se indisponível, deixar NOT_TESTED e não prometer compatibilidade. Testes em Windows Server 2022 não substituem Windows 10/11.
- Revisão de direitos: continua indispensável, mesmo quando o software é gratuito. Não inferir aprovação de licença ou titularidade a partir da autorização de gastar zero.
- Antimalware: usar ferramentas gratuitas, definições recentes, hashes dos bytes exatos, sem bypass. A CI anterior bloqueou ClamAV por base antiga; Defender cliente ainda não realizado.
- Versão estável 1.0.0 Desktop fica adiada até evidências aplicáveis e decisão de confiança. Não renomear RC4 nem publicar instalador não aprovado. Disponibilizar informações, demonstrações web, extensão e prévia fonte RC1 já existente, sem ampliar direitos não confirmados.

## Entrega atual
RC4: 413 testes distintos aprovados entre Windows Server e Ubuntu; 47 hashes, 27 binários, 17 avisos. [Build](../downloads/windows-rc4-reduced-runtime-evidence.json), [revisão final](../downloads/rc4-final-review-evidence.json) e [migração](../downloads/rc3-rc4-upgrade-evidence.json). RC4 é candidato de CI, não download público aprovado. A migração limpa, e não atualização direta, remove os 44 DLLs antigas nos testes.

## Integração GRAAL antecipada
Sincronizar estado real nos materiais institucionais: extensão 1.0.0 disponível, Desktop RC4 experimental em CI, código-fonte público RC1. Manter três links por projeto no site central e identidade visual. Não declarar etapa de lançamento concluída; pós-lançamento estável fica pendente.

## Próximo passo sem custo
Consolidar o inventário de recursos próprios e terceiros para aprovação do titular; realizar scan gratuito quando houver base atualizada e ambiente adequado; solicitar testes voluntários somente após análise de segurança e autorização de distribuição. A versão estável será preparada quando os requisitos realmente puderem ser cumpridos. Sem compromissos financeiros assumidos.

- 26/11/2026 — [Refinamento funcional das 50 ferramentas](https://github.com/Kgasil/aeris/blob/main/validation/functional/ROADMAP.md): Security passou 473/477 testes Windows e 54 smokes, com dois avisos Tk em revisão; fonte RC5 de 362 arquivos e 54 hashes refinados verificada. [CI 45863779585](https://github.com/Kgasil/aeris/actions/runs/45863779585) valida o novo candidato; fonte pública RC1 e RC4 histórico preservados. Nenhum novo instalador aprovado, direitos/scan/Windows cliente pendentes, sem custos ou publicação automática.

- Integração funcional 11/11 concluída em CI no RC5 experimental: [evidência completa](https://github.com/Kgasil/aeris/blob/main/downloads/functional-rc5-integrated-evidence.json), [branch permanente](https://github.com/Kgasil/aeris/tree/desktop-rc5-source). 477 casos distintos aprovados e 60 smokes; instalação, hashes e desempenho aprovados em CI. Direitos, antimalware e cliente continuam gates; não há publicação binária estável.

**Revisão adicional RC5 (26/11/2026):** atualização RC4→RC5, reinstalação limpa, rollback e restauração de cópia PASS no Server 2022; oito manifestos idênticos, zero DLLs obsoletas. ClamAV 1.5.4, daily 28194: integridade e assinatura da base PASS, idade 124.817 s (>24 h), scan NOT_TESTED. Defender em tempo real inativo na CI. Não publicar instalador antes da revisão aplicável. [Evidência exata](https://github.com/Kgasil/aeris/blob/main/downloads/functional-rc5-integrated-evidence.json).

- [Entrega de distribuição RC5](rc5-distribution-handoff.md): Setup exato preservado no rascunho 459704032, oito testes simulados do botão de download aprovados, nenhuma nova funcionalidade. Release permanece não pública até direitos, termos e verificações de confiança aplicáveis.

## Decisão de disponibilização experimental (26/11/2026)

O titular solicitou explicitamente a implantação para instalação pública, após confirmação de finalidade gratuita não comercial e ciência das pendências informadas. Publicada exclusivamente a prévia experimental terms1, [Release 459713072](https://github.com/Kgasil/aeris/releases/tag/aeris-desktop-1.0.0rc5-terms1-preview), [CI 45866976810](https://github.com/Kgasil/aeris/actions/runs/45866976810), download sem login e SHA-256 verificados. O rascunho RC5 anterior permanece não publicado. As limitações de scan, cliente e termos não foram resolvidas nem marcadas PASS; o proprietário solicitou disponibilização experimental apesar delas. Não há aprovação de lançamento estável, certificação de segurança ou parecer jurídico. O pacote contém avisos históricos de revisão e não aprovação; o escopo público é exclusivamente avaliação em ambiente descartável, com dados fictícios e análise local prévia; não contornar proteções. Custo assumido zero. Esta atualização substitui somente o estado histórico de disponibilidade da prévia, não os gates de estabilidade.
