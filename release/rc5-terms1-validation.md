# Aeris RC5 — validação da revisão de instalação terms1

Candidato experimental, sem assinatura, não liberado ao público. A finalidade gratuita e não comercial e a autorização do titular para código e artes foram confirmadas. Os termos específicos continuam em revisão.

[CI 45866232131](https://github.com/Kgasil/aeris/actions/runs/45866232131) — artefato aeris-rc5-terms1-review-not-a-release, ID 15139892917. O ZIP de CI exige conta GitHub; não é link final do público.

| Arquivo | SHA-256 |
| --- | --- |
| ZIP da revisão terms1 | 74b6b7f76a3ac5dbc6ce3f926b979c020f001434a30937420664d2d30a069131 |
| Aeris-1.0.0rc5-Windows-x64-Setup-terms1.exe | f5499cc2383e4d3a0acee8a0d84e173fa1a44a098ac0ba478c1febbcfe4e774b |
| Executável instalado | 4cb9ed45a6e9cce9c1f86a9d71e6f915aba987ab3532e034e34bd9300b7d0025 |
| Portátil RC5 inalterado | ffbda95354b563e1d6a1b8f90fc43184a197585488c3da8609ac6970ffee9701 |

O portátil vem do [artefato original RC5](https://github.com/Kgasil/aeris/actions/runs/45863779585); ZIP externo SHA-256 09aa2076cac6f9bc8a543869027fe2617f0590fd4509a6f18261def0e797ba9a. Não usar o Setup original do RC5.

1. Revisar [minuta de termos](../validation/installer/RC5-TERMS-REVIEW.txt) e licenças de terceiros, inclusive Microsoft/Python. Alterar termos exige novos bytes e nova validação.
2. Usar ambiente cliente x64 descartável, atualizado, sem dados reais, sem Python externo; proteção ativa. Não comprar VM/licença. Verificar hashes com Get-FileHash e seguir [SCAN.md](../validation/installer/SCAN.md) para Setup revisado, ZIP portátil e pasta extraída verificada. Não executar se houver bloqueio ou scan incompleto. ClamAV CI não realizou scan por base vencida.
3. Depois da revisão de segurança, abrir Setup pelo Explorer. Conferir tela de aceite (recusa/cancelamento não instala; aceite permite avançar), opção de atalho, instalação por usuário, abertura do Hub e ferramentas básicas offline. Reinstalar e desinstalar com dados fictícios; confirmar preservação. Seguir [W01–W10](../validation/windows-client/README.md) e testes adicionais aplicáveis. Registrar versão Windows e resultados reais. A CI já passou em recusa silenciosa, aceite, instalação, reinstalação e desinstalação, mas não substitui a interação no cliente.
4. Após direitos, termos, revisão de segurança e evidências cliente aprovados, preparar nova Release com a tag aeris-desktop-1.0.0rc5-terms1-preview, exclusivamente com os bytes aprovados, e habilitar a configuração do botão. Conferir download sem login e hash. Nunca publicar o rascunho antigo. Sem aprovação automática.

[Registro da revisão](../downloads/rc5-terms1-installer-evidence.json). Nenhum custo assumido. Não desativar Defender ou contornar SmartScreen.
