# Etapa 06 — Validação em Windows 10 e Windows 11

Estado: protocolo e coletor implementados; **execução em Windows cliente pendente**. O resultado de Windows Server não substitui as duas validações. Não execute em computador de produção nem use dados reais.

## Ambiente e preparação

- Duas VMs x64 descartáveis, separadas, atualizadas e com suporte de segurança aplicável. Registrar edição e build; para Windows 10, confirmar cobertura de atualizações de segurança (ESU ou edição ainda suportada).
- Snapshot limpo, conta local comum sem participação no grupo Administradores, sem Python/Aeris instalados. Confirmar também ausência de intérprete portátil; o coletor verifica apenas launchers comuns e registros.
- Proteções do Windows ativas, definições recentes; não contornar bloqueios do SmartScreen, não adicionar exclusões. Antes de iniciar o candidato, cumprir [análise de segurança](../installer/SCAN.md). Se o pacote for bloqueado ou o scan não puder ser realizado, registrar BLOQUEADO, não executar.
- Usar o mesmo Setup.exe e SHA-256 aprovados na evidência independente, sem recompilar. O instalador é experimental, não assinado. Manter cada evidência separada por OS e hash.
- Transferir apenas o instalador verificado e o coletor para a VM. O teste do usuário final é pelo Explorer; PowerShell serve exclusivamente para a equipe de teste coletar evidência, não é requisito do aplicativo.

## Sequência interativa

| ID | Ação | Critério |
|---|---|---|
| W01 | Executar coletor Before | OS cliente, x64, conta comum, ausência de Python detectável, pasta/atalhos limpos |
| W02 | Abrir Setup.exe no Explorer | Sem elevação inesperada; texto de prévia legível; registrar idioma, telas e cliques; bloquear se proteção impedir |
| W03 | Confirmar instalação com atalho desktop selecionado | Menu Iniciar e desktop corretos; abertura automática desmarcada |
| W04 | Coletor Installed | SHA-256 do executável coincide; atalhos apontam para executável instalado |
| W05 | Abrir pelo Menu Iniciar | Hub visível, catálogo disponível, funcionamento offline de ferramentas simples; nenhum Python externo requerido |
| W06 | Criar dados sintéticos e marcador | Registrar opções e conteúdo fictício; fechar Aeris normalmente |
| W07 | Abrir mesmo Setup.exe e reinstalar | Dados preservados; coletor Reinstalled; comparar hash do marcador com Installed de referência após criação |
| W08 | Desinstalar pelo Windows | Aplicativo e atalhos removidos; dados conforme política documentada; coletor Uninstalled |
| W09 | Repetir em snapshot limpo com atalho desktop desmarcado | Sem atalho desktop, Menu Iniciar funcional; desinstalação limpa |
| W10 | Repetir no outro OS | Evidências independentes, sem usar os resultados da primeira VM |

O coletor não executa o instalador e não confirma interação gráfica, scanner, atualização entre versões ou política de dados. Observe e registre manualmente cada item. Se alguma ação for impedida, registre FAIL/BLOCKED/NOT_TESTED com motivo.

## Coleta sem Python

Abra PowerShell como usuário comum da VM. Defina os hashes esperados com base na evidência correspondente ao **artefato exato**, não em uma cópia desconhecida. Exemplo de chamada (variáveis previamente definidas pelo operador):

```powershell
.\collect-evidence.ps1 -Phase Before -SetupPath $setup -ExpectedSetupSha256 $setupHash -ExpectedExeSha256 $exeHash -OutputFile before.json
```

Repita com Installed, Reinstalled e Uninstalled e nomes de saída diferentes. Para W09, acrescente -DesktopShortcut NotSelected. O script não altera configurações do Windows nem lança o Aeris. Se a execução do script for bloqueada, não relaxar políticas da máquina: usar observações manuais autorizadas.

Para W06, somente dentro de VM descartável, criar o marcador de preservação em %LOCALAPPDATA%\Aeris\ci-client-synthetic-preserve.txt com texto fictício, sem sobrescrever arquivo existente; após criar, coletar outro Installed com saída nova. Comparar SHA-256 do marcador em Installed, Reinstalled e Uninstalled. O marcador não substitui teste de dados do aplicativo: verificar também configurações e recursos persistentes com dados fictícios.

## Entrega da evidência

Copiar o [modelo JSON](result-template.json) para cada VM e preencher IDs, hash, edição/build, resultado e evidências. Não incluir nomes de conta, dados privados ou capturas com informações pessoais. Usar PASS somente após observação real. O status OBSERVATIONS_MATCH_REVIEW_REQUIRED do script **não** equivale a aprovação da etapa.

A etapa 06 só termina quando ambas as VMs tiverem W01–W10 aplicáveis comprovados, sem falhas bloqueantes. O coletor ainda não foi executado em Windows cliente; resultados permanecem NOT_TESTED.
