# Etapa 08 — segurança nativa Windows

O workflow independente executa os cinco novos testes e dois testes nativos existentes em Windows Server 2022, Python 3.14.10 x64, usando o ZIP fonte verificado. Não publica instaladores.

- DPAPI do usuário atual: proteção e leitura por outro processo da mesma conta, rejeição de blob inválido e adulterado.
- Vault: persistência criptografada de conteúdo fictício, ausência do marcador em UTF-8/UTF-16 no arquivo, erro de leitura sem apagar ciphertext, reabertura após restaurar cópia sintética.
- Mutex do aplicativo: nome exclusivo de teste, bloqueio entre processos e recuperação após encerramento abrupto do processo filho criado pelo teste.
- Lock de Vault: exclusão entre processos e reabertura após liberação.
- Testes nativos anteriores: DPAPI e mutex no processo.

O código fonte usa as APIs Windows reais; o teste força o modo frozen apenas para exercitar application_lock, não executa o aplicativo empacotado. Não existe prova de ausência de plaintext em RAM, paginação ou todos os arquivos. Dados exclusivamente sintéticos, pastas temporárias, nenhum segredo de usuário.

## Pendências obrigatórias
1. Em VM cliente descartável, duas contas locais comuns distintas: proteger blob fictício na primeira conta, transferir somente ciphertext via canal controlado, confirmar que a segunda conta não consegue descriptografar, e a primeira continua capaz de ler. Não transferir chaves ou dados reais.
2. Confirmar ACLs efetivas de diretórios de programa, dados e backups (sem conceder privilégios para o teste). Testar acesso de outra conta comum e documentar limites de administradores.
3. Após revisão de segurança do artefato exato, executar duas instâncias do Aeris instalado, conferir mensagem de duplicidade e recuperação após encerramento normal ou falha em VM; verificar mutex durante tentativa de instalar com aplicativo aberto. Não matar processo de produção.
4. Verificar ciclo de vida e limpeza do cofre na UI instalada, e confirmar o comportamento de DPAPI no backup/rollback sem presumir portabilidade entre contas/máquinas.

Registrar PASS/FAIL/NOT_TESTED com OS, hash do artefato, escopo e evidência, sem dados pessoais. A CI não substitui estas pendências, análise antimalware ou aprovação de distribuição.
