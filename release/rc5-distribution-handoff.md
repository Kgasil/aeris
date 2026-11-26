# Aeris Desktop — entrega de distribuição gratuita (26/11/2026)

**Estado: instalador existente preparado em rascunho; distribuição pública bloqueada.** Sem mudanças nas 50 ferramentas, sem recompilar, sem despesas, sem publicação automática.

## O que foi concluído
- [RC5 integrado](../downloads/functional-rc5-integrated-evidence.json): 477 testes distintos, 60 smokes, instalador de 12.792.748 bytes, atualização e rollback validados em CI.
- [Rascunho de Release 459704032](https://github.com/Kgasil/aeris/releases/edit/untagged-2fda91e3c1908b9d0a67), visível apenas a usuários autorizados. Tag prevista aeris-desktop-1.0.0rc5-preview; commit de fonte bfedb434358ce04d55827d7a057de3edf31c6728. Setup (asset 796911933) e SHA256SUMS.txt. [CI 45865669115](https://github.com/Kgasil/aeris/actions/runs/45865669115) SUCCESS: download do asset autenticado e SHA-256 conferidos; teste sem autenticação HTTP 404. Evidência 15139882369, SHA-256 d5a9ab9c862f6eb87281b8e7bd5f3e63bc77bb6b4da185ae8cd88326bcc9f6ce. Primeira tentativa 45865584588 rejeitada pela API (parâmetro make_latest boolean em vez de string), sem release criada; correção 6d25f28.
- Botão do site usa tag, nome, tamanho, SHA-256 e URL exatos, sem login. O script efetivo foi testado com oito respostas simuladas: release pública exata, draft, digest incorreto, tamanho incorreto, host incorreto, asset ausente, release ausente e tag incorreta; todos PASS. Não é teste de download público real, pois a release permanece draft.

## Direitos e confiança — revisão do pacote exato
ZIP externo SHA-256 09aa2076cac6f9bc8a543869027fe2617f0590fd4509a6f18261def0e797ba9a, Setup SHA-256 54ab3ab65672a32dc944259bb291f5c66ed735d4c5d5876641725131c9915aa8. Inspeção do ZIP confirma 17 avisos de terceiros, licença Python, manifesto e 27 binários. Fonte consolidada 362 arquivos; único recurso gráfico não textual da fonte é distribution/aeris.ico (SHA-256 26e178cded091a337a2d43bdb48b849df8976b7ac99685d0453ab1566851fa99). Site main tem assets/aeris-symbol.svg, assets/brand-banner.svg, assets/readme-cover.svg. Origem e direito de uso de código e artes devem ser confirmados pelo titular; inventário não comprova direitos.

- Python 3.14.10: o texto real PYTHON-LICENSE.txt inclui Additional Conditions for this Windows binary build, exigindo condições equivalentes de proteção ao código redistribuível Microsoft e concordância do usuário/distribuidor. Restam duas DLLs VCRUNTIME140 de origem Python confirmada; não confundir origem com direito. O script Inno atual tem InfoBeforeFile, mas não LicenseFile nem aceite de termos finais. Revisar direitos/termos e mecanismo de aceite antes de distribuir. Se necessário, modificar somente o empacotamento, criar novo candidato e repetir verificações dos bytes finais.
- Inno Setup 6.7.4: licença efetiva permite uso comercial sob condições; o [fornecedor pede compra em contexto comercial](https://jrsoftware.org/inno-setup/purchase). Confirmar enquadramento não comercial antes de decidir que não há custo. Não comprar.
- Assinatura gratuita: [SignPath Foundation](https://signpath.org/terms.html) exige projeto elegível de código aberto e outros critérios. Não presumir licença aberta, não solicitar certificado sem autorização.
- ClamAV: base assinada, porém acima do limite de 24h. Scan não realizado. Não repetir indefinidamente a mesma tentativa, nem desabilitar a proteção. [Instruções RC5](owner-validation-guide.md) para Defender em VM cliente disponível.
- [GitHub runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners): Windows cliente ARM disponível não substitui os clientes x64 necessários. Não contratar runner maior. Usar ambiente local descartável já licenciado ou voluntário qualificado.

## Ações restantes
1. Titular confirma autoria/autorização de código e artes, uso gratuito não comercial e aprova termos de distribuição após revisão dos terceiros.
2. Verificar o instalador exato com proteção ativa e definições recentes, em Windows cliente x64 disponível; registrar evidências e validação aplicável. Não instalar em máquina de produção sem aprovação. Ver guia do titular.
3. Se os termos exigirem uma página de aceite, alterar apenas instalador e repetir validação/scan no novo pacote. Manter 50 ferramentas intactas. Não publicar RC5 por conveniência.
4. Após aprovação dos direitos e segurança, publicar somente bytes aprovados como prévia claramente identificada; atualizar site com a versão/hash exatos, validar download anônimo e instalação. Versão estável continua sujeita às verificações aplicáveis.

**Não clicar em Publish release enquanto houver bloqueios.** Não há alegação de certificação antimalware, assinatura, compatibilidade cliente ou disponibilidade pública. Custo assumido R$ 0,00.
