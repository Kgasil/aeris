# Etapa 07 — Atualização e recuperação
Estado: RC1→RC2 e RC3→RC4 aprovados em CI quanto à preservação de dados sintéticos; migração RC3→RC4 exige reinstalação limpa para remoção de DLLs antigas. Nenhuma atualização automática, publicação ou rollback em produção autorizado.

## Candidatos
- RC1: artefato 15132975671, run 45848435777, [evidência](../../downloads/windows-inno674-notices-evidence.json), SHA-256 externo fixado. Não reconstruir RC1 nem substituir arquivo histórico; artefato temporário até 26/12/2026.
- RC2: candidato distinto de distribuição, com versão interna e AppVersion 1.0.0rc2 e instruções adicionais de recuperação. Usa o ZIP fonte histórico mais os overlays validados; mantém esquema de dados, AppId, diretório por usuário, mutex e políticas de desinstalação. Não é versão pública, nem nova funcionalidade de atualização automática.

## CI
O workflow [upgrade e recuperação](../../.github/workflows/aeris-windows-upgrade-recovery.yml) compila RC2 com os gates anteriores, baixa o artefato RC1 exato com token de leitura, verifica o digest externo e o hash do Setup e exige hashes distintos. O [script de teste](test-upgrade-recovery.ps1) só aceita runner Windows do GitHub e perfil inicialmente limpo. Testa:

1. Instalar RC1 e confirmar hash do EXE, versão registrada no Windows e autoteste.
2. Criar configuração fictícia com a implementação Settings e marcador; calcular manifesto e copiar backup para diretório separado.
3. Rejeitar hash inválido antes de executar o Setup e verificar que RC1 e dados permanecem intactos.
4. Atualizar para RC2 e confirmar versão, EXE, autoteste, preservação e leitura das configurações.
5. Desinstalar RC2, reinstalar RC1 exato, verificar dados, restaurar uma cópia isolada do backup e ler configurações restauradas; desinstalar RC1.
6. Registrar hashes e evidências. Falhas interrompem a CI, sem publicação.

A leitura das configurações utiliza a implementação fonte do candidato, não automação de todas as telas instaladas. O teste não prova recuperação após interrupção de energia, corrupção em meio à instalação, compatibilidade de futuras migrações de esquema, Windows 10/11 ou DPAPI entre contas. Esses casos permanecem pendentes.

## Procedimento manual de recuperação (apenas após aprovação do artefato)
Fechar o aplicativo. Fazer backup protegido da pasta %LOCALAPPDATA%\Aeris para local distinto sob controle do mesmo usuário; conferir integridade e manter o original. Não copiar credenciais para terceiros. O cofre DPAPI pode depender da mesma conta e máquina: backup não é garantia de portabilidade. Registrar a versão e o hash do instalador anterior. Se a atualização falhar, não apagar dados nem repetir instalação às cegas; preservar logs, verificar versão e integridade. Em ambiente de teste, restaurar primeiro em diretório separado e validar compatibilidade. Só reinstalar versão anterior confiável se dados/esquema forem compatíveis e as proteções permitirem. Não orientar downgrade para runtime vulnerável ou contornar SmartScreen. Se necessário, suporte deve decidir recuperação específica. A desinstalação preserva dados; exclusão é ação separada e voluntária.

Publicação continua bloqueada pelas etapas 01/04/05. Testes de cliente, falha intermediária e recuperação de dados reais requerem evidência adicional.

## RC3 → RC4: migração recomendada

[Evidência verificada](../../downloads/rc3-rc4-upgrade-evidence.json) · [CI](https://github.com/Kgasil/aeris/actions/runs/45853813602). A atualização direta passa no autoteste e preserva os dados, mas deixa as 44 DLLs antigas do RC3. Os 44 hashes correspondem ao manifesto RC3 e nenhum arquivo está no RC4. Reinstalação limpa e rollback controlado passaram; oito manifestos de perfil idênticos.

**Somente depois de aprovação de segurança dos artefatos:** fechar Aeris, fazer e conferir backup protegido do perfil, usar a desinstalação normal do Windows para remover a prévia anterior, confirmar que o programa foi removido (sem excluir dados), instalar a nova versão aprovada e verificar as configurações. Não apagar DLLs manualmente nem usar exclusão recursiva; se a desinstalação não remover o programa, registrar o defeito e procurar suporte. Não restaurar chaves DPAPI em outra conta/máquina esperando portabilidade. Windows 10/11 e falha no meio da instalação ainda não testados.
