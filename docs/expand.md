# Aeris Expand — v0.4.0a2

## Escopo
Expansão de abreviações explicitamente fornecidas no editor. Três regras de exemplo, até 100 regras por sessão; código ASCII minúsculo iniciado por ponto e vírgula, até 32 caracteres após o prefixo. Texto por regra até 2.000 caracteres, entrada até 20.000 e saída até 100.000. Uma única passagem, sem expansão recursiva. Preserva desconhecidas e evita correspondências parciais em palavras. Não interpreta comandos nem executa o texto.

## Privacidade
Regras em memória; não armazena textos em disco. Cópia com autorização de sessão e confirmação; histórico nativo do clipboard pode manter cópias. Limpeza e desativação descartam as regras personalizadas, não constituem apagamento seguro de memória. Uso de dados fictícios até validação. Sem hooks globais, rede, leitura automática do clipboard ou colagem externa.

## Próximos passos
Integração contextual autorizada e persistência protegida de regras após avaliação de segurança. Bridge deverá oferecer ações explícitas entre módulos. Aeris Text mantém o requisito de correção automática configurável; não implementado nesta entrega.

## Testes
95 unitários aprovados, 3 ignorados por dependerem do Windows; 15 smoke tests gráficos aprovados no Linux. Windows nativo ainda pendente.
