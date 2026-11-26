# Etapa 09 — IA local e integrações

## Escopo e evidência
Aeris Companion utiliza o endpoint fixo 127.0.0.1:11434/api/chat, sem proxy/redirect, com timeout de socket de 45 s, limites de mensagem/resposta, sem ferramentas do modelo. Copilot exige proposta e confirmação explícita; permissões são da aplicação, não sandbox do SO.

[Workflow](../../.github/workflows/aeris-local-ai-validation.yml) separado em dois jobs:
- Windows Server 2022: sete testes HTTP reais com servidor local sintético (não é IA), incluindo timeout reduzido apenas para teste, indisponibilidade, rejeição de redirect, chamada de ferramentas e modelo cloud, e escopo da solicitação. Também executa regressões existentes Companion, Copilot, Permissions e LocalWorker.
- Ubuntu 24.04: Ollama real v0.40.18, download oficial com SHA-256 fixado e verificado, porta loopback, OLLAMA_NO_CLOUD=1, cache temporário e sem conta. Modelo SmolLM2 135M (271 MB, Apache-2.0), pull apenas no runner e verificação do prefixo do digest publicado. Registra digest integral do modelo, versão, resultado, latência, tamanho e hash da resposta, sem armazenar texto da conversa. Confirma resposta real, modelo ausente e servidor parado.

Fontes: [release Ollama](https://github.com/ollama/ollama/releases/tag/v0.40.18), [FAQ sobre cloud](https://github.com/ollama/ollama/blob/main/docs/faq.mdx), [modelo](https://ollama.com/library/smollm2:135m). O teste com modelo real é leve em relação a modelos maiores, mas o runtime oficial Linux tem aproximadamente 1,65 GB; não integrar runtime/modelo ao instalador Aeris. Não avaliar qualidade linguística pelo smoke test. Desabilitar cloud é uma configuração do servidor, não prova de isolamento de rede de qualquer instalação de terceiros.

Resultados ainda pendentes. O teste em Linux usa o cliente fonte e não substitui execução do Ollama com interface instalada em Windows 10/11. Confirmar em VM cliente: consentimento explícito de chat e revisão, revogação durante solicitação, descarte de resultados de janela fechada, timeout padrão, ausência de acesso a dados não selecionados, comportamento offline após download, modelo de qualidade em português escolhido pelo usuário, e ausência de execução automática de comandos. Usar somente dados fictícios, sem API keys, sem publicar modelos, sem alterar proteções. A publicação permanece bloqueada.
