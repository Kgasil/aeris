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
