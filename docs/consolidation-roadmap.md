# Aeris — após os 50 protótipos

Marco v0.10.0a5: todos os 50 itens do catálogo têm status prototype; isso não é 100% de produto pronto. A distribuição continua local e pré-alpha. Não publicar como versão estável antes de validar os requisitos de segurança, recursos e usabilidade.

## Sequência proposta de consolidação

1. Revisão da arquitetura e inventário dos dados: testar limites de cada store, controles de permissão, cópia, descarte e atualização. Definir um modelo de persistência protegido no Windows (DPAPI, versionamento, gravação atômica, recuperação, retenção e backups com consentimento). Validar migrações; evitar dados reais antes disso.
2. Assistência textual: correção automática de ortografia/gramática com processamento local, opção de desligar, revisão e desfazer. Não usar monitoramento global da digitação nem alterar textos de outros aplicativos sem ação autorizada. Distinguir correção de reescrita.
3. Integrações: Meeting com Checklist e Reminder, Learn com Flashcards e Research. Operações tipadas, prévia, confirmação, permissões e testes de regressão. Não criar eventos externos implicitamente.
4. Eco Engine: medir processo isolado e módulos sob demanda em Windows 10/11 x64; investigar memória, CPU em repouso, latência e tamanho de distribuição. Metas originais são objetivos, não resultados validados.
5. Segurança e QA: teste nativo Windows, regressão manual, revisão de ameaças, dados sintéticos, acessibilidade, tratamento de falhas e revisão independente. Construir e testar instalador/desinstalador, sem exigir instalação manual de Python na versão distribuída.
6. AI Companion integrado à edição única sem cobrança do Aeris: voz masculina natural e profissional, microfone opt-in e indicador visível, interpretação de linguagem natural, executor restrito e confirmação de alterações. Custos, latência, privacidade e retenção do provedor deverão ser avaliados antes de qualquer integração externa. Nenhuma gravação oculta, nenhum uso romântico, validação de modelo e voz real antes de distribuição.

A correção automática textual iniciou na v0.11.0a4 com regras limitadas; a assistência conversacional iniciou na v0.11.0a3. A edição única deve continuar sem conta obrigatória, publicidade ou dependência de rede por padrão. A validação nativa e o instalador são condições para distribuição, não resultados desta etapa.

## Progresso v0.11.0a1

Primeiro incremento do Protected Storage implementado: snapshots explícitos de Checklist, Ideas e Learn, versionamento de envelope, DPAPI, gravação atômica e restauração validada. Ainda faltam adapters dos demais módulos, persistência opcional automática, recuperação e backup, validação nativa. Ver `protected-storage.md`.

## Progresso v0.11.0a2

Adapters adicionados: Meeting, Research, Flashcards e Reminder. Sete módulos com snapshots manuais, restauração validada e mesmo envelope schema 1. Prazos absolutos preservados; lembretes vencidos sem alerta retroativo. Próximo: política de salvamento opcional, recuperação e Backup, sem gravar dados automaticamente por padrão.


## Progresso v0.11.0a3

Protected Storage III: recuperação de uma versão anterior opcional, integração das sete cópias atuais ao Backup. Salvamento automático adiado até implementar política segura contra conflitos e limpeza de sessão. AI Companion antecipado por decisão do responsável: edição única, sem divisão paga, cliente Ollama local e voz Windows em protótipo. Ver `ai-companion-concept.md`. Próximos: persistência automática segura e Intelligent Text.

## Progresso v0.11.0a4

Intelligent Text I: revisão automática com regras locais, modo opt-in de substituição ortográfica, sugestões de concordância, revisão explícita e desfazer. Três idiomas iniciais; motor linguístico abrangente e validação em corpus pendentes. Sem captura global. Próximos: persistência automática segura e Integration Engine, iniciando por Meeting → Checklist/Reminder.

## Progresso v0.11.0a5

Integration Engine I: Meeting → Checklist/Reminder, operações tipadas, validação após confirmação e permissão independente. Próximos: integrações de aprendizagem, persistência automática segura, refinamento da IA e medição isolada de recursos. Ver `integration-engine.md`.

## Progresso v0.11.0a9

Protected Storage IV: salvamento automático de sete módulos, opt-in de sessão, intervalo de 10 s, comparação de conteúdo e controle de concorrência por hash do blob protegido sob trava. Sessão vazia, conflito, revogação e limpeza não sobrescrevem a cópia. Sem restauração automática ou flush final. Validação nativa Windows pendente. Próximo: Intelligent Text II e refinamento de AI Companion, segurança e distribuição.

## Security & Quality I (v0.12.0a1)

Revisão de entradas e arquivos implementada; 371 testes unitários e 58 gráficos aprovados. Restam Security & Quality II, Windows Distribution I, Windows Distribution II e Release Candidate como quatro entregas estimadas, condicionadas a validação e correções. Extensão Chromium separada.

## Security & Quality II (v0.12.0a2)

Serialização de workers de IA/Companion, JSON interno estrito, tratamento de falha de inicialização e confirmação de descarte de rascunhos do Text/Companion. 375 testes unitários e 59 gráficos aprovados; 5 testes nativos Windows ignorados. Próximas três entregas estimadas: Windows Distribution I, Windows Distribution II, Release Candidate. Validação real Windows e extensão Chromium continuam separadas.


## Windows Distribution I (v0.13.0a1)

Receitas de build PyInstaller/Inno Setup, instalação por usuário, autocheck temporário, mutex de instância empacotada, guia de tradução mantido e Argos experimental indisponível no exe. 379 unitários e 60 gráficos aprovados em Linux; seis nativos pendentes. Não houve compilação Windows. Restam duas entregas estimadas: Windows Distribution II (build e validação nativa) e Release Candidate (publicação após evidências). Sem ambiente Windows, essas entregas permanecem condicionais. Ver `windows-distribution.md`.

## Windows Distribution II (v0.13.0a2)

Verificação de artefatos e autocheck ampliado implementados; 388 testes unitários e 60 gráficos aprovados em Linux, seis testes Windows ignorados. A validação nativa, compilação, instalação/desinstalação e licenças continuam pendentes. Uma entrega de preparação (Release Candidate) resta no plano, mas a publicação como candidata instalável depende das evidências nativas e revisão. Ver `windows-distribution-ii.md`.

## Candidato de código-fonte v1.0.0rc1

Quinto marco de preparação concluído em código-fonte: identificação RC, validação de artefatos e registro de critérios de lançamento. 392 testes unitários e 60 gráficos aprovados em Linux; seis nativos ignorados. Nove condições binárias pendentes. A compilação e validação Windows, testes reais de IA e voz, revisão de licenças e confiança e disponibilização do executável são bloqueadores, não etapas concluídas. O ciclo desktop inicial está consolidado, não há versão estável.
