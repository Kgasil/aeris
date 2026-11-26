# Aeris Drop — v0.6.0a3

## Escopo
Prateleira temporária de até 100 referências a arquivos locais. Guarda em memória caminho, tamanho lógico em bytes no momento da seleção e categoria por extensão. Não lê conteúdo, não cria cópias, não move, não exclui e não executa arquivos. Não abre arquivos a partir da lista. Seleção múltipla por diálogo nativo, ainda sem arrastar e soltar. Não é um gerenciador de transferências de arquivos do Windows.

## Fluxo e permissões
1. Ativar Drop no catálogo e abrir pelo Hub, Spotlight ou Workspace.
2. Autorizar Drop → Adicionar, selecionar arquivos fictícios, confirmar a consulta de metadados.
3. Revisar lista; Ctrl/Shift permite selecionar várias referências. Remover apenas as referências ou limpar a prateleira, sem alterar originais.
4. Para copiar caminhos como texto (um por linha), conceder Drop → Clipboard, selecionar e confirmar. Não copia os arquivos e não garante existência ou identidade atual do caminho. Caminhos podem conter dados pessoais e permanecer no histórico do sistema.

Fechar a janela mantém a prateleira na sessão, mas cancela a adição pendente. Revogar Adicionar limpa a prateleira mesmo com janela fechada e descarta adições em andamento. Revogar Clipboard bloqueia novas cópias. Desativar, limpar sessão ou encerrar descarta referências. Privacy contabiliza os itens em memória; não armazena seus valores. Preferências de ativação e favoritos (esquema 27) são persistidas, sem persistir caminhos ou permissões.

## Limites e segurança
O motor reutiliza classificação do Organizer e validação de caminhos locais do Verify. Recusa caminhos relativos, links simbólicos, pontos de nova análise, arquivos não regulares, caminhos com quebras de linha e unidades não fixas/UNC no Windows. Inspeção é feita em thread sob demanda, com cancelamento cooperativo. O diálogo do sistema pode exibir outros locais; a validação do motor ocorre depois da seleção. Uma referência não é um identificador imutável: arquivos podem mudar, desaparecer ou ser substituídos. Nenhuma vigilância do sistema de arquivos; não há garantia contra mudanças concorrentes, memória residual, cópias externas ou histórico de clipboard. Use dados fictícios até validação Windows e auditoria. Integração direta com Documents, Metadata, Verify e Organizer, drag-and-drop e transferência real permanecem pendentes.

## Validação
Linux: 162 testes unitários aprovados, 4 ignorados por dependerem de Windows; 26 testes gráficos aprovados com Xvfb (Voice e Workspace executados separadamente após timeout da suíte em lote). O diálogo e a confirmação do Drop foram simulados; cópia textual exercitada no clipboard da sessão gráfica Linux. Sem validação nativa no Windows ou medição de desempenho desta versão.

Próximo: Compare.
