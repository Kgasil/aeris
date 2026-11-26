# Aeris Copilot — v0.10.0a1

Motor de comandos local e determinístico, sem modelo de linguagem, microfone, rede, execução de código ou shell. Desde v0.11.0a3, a janela também abre o AI Companion opcional da edição única; consulte `ai-companion-concept.md`.

## Uso
1. Ative Copilot e a ferramenta de destino no catálogo.
2. Em Permissões, conceda `Copilot → Executar` (apenas nesta sessão).
3. Digite um comando conforme um dos modelos e clique em Preparar prévia.
4. Confira o destino e os parâmetros exatos. Confirme ou cancele. Cada prévia é de uso único. Editar o comando, alterar permissões, alterar o estado de módulos ou fechar o Copilot invalida a prévia.

| Modelo | Efeito |
| --- | --- |
| Lembre-me de revisar o relatório em 30 minutos | Reminder, alerta visual genérico, prazo fixado na prévia |
| Marque uma reunião amanhã às 14:00 | Reminder, horário local absoluto; também aceita hoje |
| Adicione estudar Python à lista Estudos | Checklist, lista existente com nome exato, prioridade Normal |
| Inicie uma concentração de 25 minutos | Focus, abre a janela e inicia; também aceita intervalo |
| Anote minha ideia de automatizar relatórios | Ideas, categoria Geral, estado Nova |

Não são interpretadas frases livres, horários escritos por extenso, múltiplas operações ou instruções para executar programas. Trechos descritivos permanecem apenas texto literal. O comando aceita até 500 caracteres, sem caracteres de controle; campos obedecem aos limites dos motores existentes. O agendamento usa relógio local do sistema, rejeita horários vencidos, inexistentes ou ambíguos e limita a sete dias. Não cria evento em calendários externos. A lista de tarefas deve existir previamente. Uma sessão Focus ativa ou pausada não será substituída.

## Segurança e limites
- Prévia não altera registros. Confirmação revalida permissão, módulo ativo e condições de destino. O executor aceita somente quatro operações predefinidas, não interpreta texto como código.
- Revogar permissão cancela prévias; desativar Copilot fecha sua janela e revoga a permissão. Registros já confirmados pertencem aos respectivos módulos e não são apagados pela revogação do Copilot. Limpar a sessão apaga os registros temporários e fecha Copilot.
- Não há histórico persistente de comandos. Os registros resultantes permanecem em memória e não sobrevivem ao encerramento do Aeris. Reminder exige que o aplicativo permaneça aberto; Focus pausa ao fechar sua janela.
- Não é um isolamento de segurança do sistema operacional, nem validação independente. O reconhecimento de voz, a interpretação de linguagem natural por IA e a voz masculina conversacional continuam planejados. A correção automática de texto também permanece pendente.
- A hora apresentada é local e depende do relógio/fuso do computador. Mudanças de fuso após a prévia não alteram o instante agendado.

## Validação
Linux: `python -m unittest discover -q` (278 aprovados, 4 ignorados por Windows); 44 scripts gráficos com Xvfb aprovados. Testes de ponta a ponta criam registros nos motores existentes, conferem a execução única, revogação, desativação e limpeza. A validação nativa Windows e otimização de memória continuam pendentes.
