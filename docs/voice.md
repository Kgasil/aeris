# Aeris Voice — v0.3.0a2

## Contrato e limites

- Windows 10/11 x64, Windows PowerShell 5.1 e System.Speech; sem nova dependência Python. Não usar motor remoto.
- O processo nasce apenas após ação explícita e autorização de sessão. A consulta enumera vozes desktop instaladas e habilitadas. Vozes OneCore/Narrator não são garantidas.
- JSON ASCII por stdin, sem texto em argumentos, sem SSML e sem arquivo temporário. Rate -5..5, volume 0..100, texto até 4000 caracteres. Limite de 20 s para enumeração e 600 s para fala.
- Revogar, limpar, fechar ou desativar solicita término do processo. Não há captura de áudio/microfone, histórico, reconhecimento de fala ou download de vozes. Não há sandbox de SO; não usar dados reais nesta pré-alpha.

## Verificação futura Windows

1. Em desktop, execute `py -3 -m unittest discover -v` e `py -3 -m tests.smoke_voice`.
2. Ative Voice, autorize áudio, liste vozes e leia uma frase fictícia com acentos. Confirme áudio no dispositivo padrão; altere a velocidade e volume.
3. Durante uma leitura longa, clique Parar, revogue a permissão, feche a janela ou limpe sessão em ensaios separados. Confirme interrupção audível e ausência de PowerShell residual.
4. Teste sem dispositivo de áudio e sem vozes disponíveis. Confirme erro compreensível, ausência de download automático e responsividade do Hub.
5. Verifique tamanho do painel com todas as ferramentas e DPI elevado. Medir custo de inicialização do processo.

Linux: 68 testes unitários executáveis e 10 testes gráficos passaram; três testes nativos Windows ignorados. Smoke de Voice simula processo, não reproduz áudio. O teste nativo enumera vozes, não comprova qualidade ou saída audível.
