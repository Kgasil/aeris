# Aeris Translate — protótipo

- Guia local: 12 frases por idioma, português/inglês/espanhol, seis direções; correspondência de frases, não tradução neural.
- Adaptador opcional Argos: CPU, OPENNMT, MINISBD, modelos preparados externamente; bloqueio de sockets Python via audit hook não constitui isolamento contra código nativo.
- Comunicação JSON por stdin/stdout, sem texto em argumentos de comando; timeout 90 s, cancelamento do processo, sem log de diagnósticos do motor pelo Aeris.
- Dependências e modelos não incluídos; validar disponibilidade, versões, licenças, qualidade e consumo no Windows antes de distribuir.
- Sem captura automática, sem histórico, sem indexação. Permissão explícita de cópia e revogação.
- 63 unitários aprovados, 2 ignorados (Windows), 9 testes gráficos em Linux. Verificação do caminho sem Argos; tradução neural real não verificada.
