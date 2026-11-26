# Aeris Learn — v0.9.0a1

Organizador de trilhas de aprendizagem, não um gerador de cursos nem um avaliador de conhecimento. Ative Learn no catálogo e abra pelo Hub, Spotlight ou Workspace. Crie uma trilha, adicione tópicos com estimativas em minutos, edite, reordene e marque a conclusão voluntariamente. A barra mostra a fração de tópicos concluídos; os minutos são estimativas dos tópicos marcados, não tempo medido. É possível reabrir tópicos. Nomes de trilhas são únicos sem distinção de maiúsculas ou acentos.

Limites: 20 trilhas, 100 tópicos por trilha; nomes de trilhas até 100 caracteres, títulos de tópicos até 200; estimativas inteiras de 1 a 1440 minutos. Sem acesso a arquivos, internet, microfone ou monitoramento. Registros em memória, preservados ao fechar a janela e descartados ao limpar a sessão, desativar com confirmação ou encerrar o aplicativo. Privacy conta trilhas, não tópicos. Não há garantia de apagamento físico da memória. Apenas preferências não sensíveis são persistidas (schema 40).

Motor LearnStore independente da UI, com registros imutáveis e operações explícitas. Integrações futuras: Focus (tempo efetivo opcional), Research, Flashcards e AI Companion (comandos confirmados); nenhuma dessas integrações diretas está implementada nesta entrega. Persistência protegida, importação e geração de planos também permanecem pendentes.

Validação: 6 novos testes unitários e smoke gráfico com diálogos simulados, em Linux/Xvfb; não substitui testes nativos no Windows.


**Atualização da consolidação (v0.11.0a2):** registros confirmados podem ser salvos/restaurados manualmente por Privacy → Cópias protegidas. Rascunhos e alterações não copiadas continuam temporários. Consulte `protected-storage.md` para permissões, prazos, limitações e validação.
