# Aeris Pronounce — v0.3.0a5

## Objetivo
Prática de escuta e repetição de frases em português, inglês e espanhol. Quatro exercícios por idioma e texto livre até 500 caracteres. Seleção explícita de voz compatível, velocidade e volume. De 1 a 5 repetições, com pausa de 700 ms.

## Integração e privacidade
Reutiliza o motor do Voice e System.Speech do Windows PowerShell, sem dependências Python adicionais. O texto vai ao processo filho via stdin em JSON ASCII; o script PowerShell é fixo. A permissão Pronounce → Áudio é independente de Voice, negada por padrão, revogável e volátil. Não há leitura de microfone, gravação, reconhecimento, pontuação de pronúncia, armazenamento de textos ou transmissão por rede. A síntese pode ter sotaque e qualidade variáveis. A reprodução usa uma voz instalada com o idioma selecionado; não tenta baixar vozes.

## Validação
Testes de payload, limites, exercícios, migração, permissões e fluxo gráfico passaram em Linux com simulador de processo. Windows 10/11: verificar lista de culturas, caracteres acentuados, repetição audível, ajuste de velocidade, cancelamento durante fala e intervalo, ausência de vozes compatíveis, e revogação. Nenhum teste nativo novo foi executado neste ambiente.
