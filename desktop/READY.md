# Aeris Ready — primeiro acesso (branch desktop-experience)

Esta é uma versão de desenvolvimento, não um instalador validado. A versão pública permanece separada.

## Iniciar pelo código-fonte

Windows 10/11, Python 3.12 ou superior com Tcl/Tk. Abra a pasta desktop e execute iniciar.bat, ou use py -3 main.py. O inicializador verifica a presença de Python e Tk e preserva o código de saída. Não exige administrador nem altera o Defender.

O núcleo usa a biblioteca padrão. Não é necessário instalar IA para utilizar ferramentas locais. Não há instalação automática de dependências.

## Configurar a IA

1. Instale Ollama por https://ollama.com/download e abra o aplicativo. Configure OLLAMA_NO_CLOUD=1 e reinicie o serviço antes de usar.
2. Instale manualmente um modelo local compatível com os recursos do computador. Para visão, escolha um modelo multimodal. O tamanho e a qualidade dependem do modelo.
3. Abra Configurar IA → Detectar modelos. Autorize a consulta ao endpoint local 127.0.0.1:11434. Se houver um único modelo elegível, ele é selecionado quando o campo está vazio. Se houver vários, escolha um.
4. Clique Testar IA. O teste envia exclusivamente uma saudação fictícia, sem histórico, captura ou arquivos.
5. Um teste de texto aprovado não certifica visão, áudio, velocidade, privacidade do serviço local ou funcionamento futuro.

Se o Ollama não responder, verifique se está aberto. Se não houver modelos locais elegíveis, instale um antes de repetir a consulta. Não altere proteções de segurança.

## Recursos opcionais

- Voz: reconhecimento pt-BR e voz de síntese masculina pt-BR instalados no Windows; verificar com dados fictícios.
- Visão: captura Windows e modelo local multimodal. Não é streaming.
- Áudio interno: somente código-fonte Windows nesta fase; veja MEETING_EXPERIMENTAL.md. Dependências opcionais soundcard, numpy e faster-whisper e modelo Whisper convertido local. A descoberta de pacotes não confirma que a captura funciona.
- Tradução local: Argos opcional, conforme README. OCR: Tesseract opcional.
- Instalação binária, dependências opcionais, licenças e testes reais no Windows permanecem sujeitos a validação antes do lançamento.

Não utilize informações pessoais reais antes da validação. Nenhuma permissão de microfone ou tela é concedida pelo diagnóstico.
