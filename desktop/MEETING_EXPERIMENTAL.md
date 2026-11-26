# Aeris Meeting — áudio interno experimental

Disponível inicialmente apenas na branch desktop-experience, em execução por código-fonte no Windows. Não está habilitado no instalador público.

- Instale manualmente as dependências opcionais: soundcard, numpy e faster-whisper, em um ambiente Python isolado.
- Prepare previamente um modelo Whisper multilíngue convertido para CTranslate2, incluindo model.bin, config.json e tokenizer.json. Selecione sua pasta local no aplicativo.
- Abra Reunião → Transcrever áudio interno. Informe todos os participantes e obtenha consentimento antes de iniciar. A saída padrão contém todos os sons reproduzidos, não somente a chamada. Feche outras fontes de áudio e não reproduza informações confidenciais.
- O worker captura blocos de 30 segundos e os transcreve em memória. Há lacunas durante o carregamento do modelo e a transcrição; não é gravação integral nem streaming. Até 20 blocos, cada worker com timeout de 180 segundos. Não há diarização nem combinação simultânea com microfone.
- O indicador flutuante permite parar; revogar a permissão também interrompe a sessão. Nenhum arquivo de áudio é criado intencionalmente.
- Após parar, revise o texto. Selecione até 4.000 caracteres e clique Gerar ata e tarefas com IA. A consulta usa Ollama local, sem histórico. Revise e edite resumo, decisões e tarefas antes de salvar.
- As tarefas salvas na ata ainda não são tarefas do Checklist: transfira individualmente na janela Reuniões, com a permissão de integração.
- Não use em reuniões reais até a validação de captura, transcrição, cancelamento e permissões no Windows. O resultado da IA pode conter erros.

Referências técnicas: https://soundcard.readthedocs.io/ ; https://github.com/SYSTRAN/faster-whisper ; https://learn.microsoft.com/en-us/windows/win32/coreaudio/loopback-recording
