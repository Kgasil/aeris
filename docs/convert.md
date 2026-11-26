# Aeris Convert — v0.8.0a5

Ative Convert no Hub, selecione uma categoria, as unidades de origem e destino, informe o valor e clique Converter. Inverter unidades troca origem e destino, preservando a entrada e invalidando o resultado. Nenhum acesso a arquivos, rede ou clipboard pelo motor. Resultados e entradas são temporários; fechar a janela, desativar o módulo ou limpar a sessão descarta o estado da ferramenta (não é garantia de eliminação da memória/swap).

## Categorias e convenções

- Comprimento: m, km, cm, mm, ft, in, mi (pé, polegada e milha internacionais).
- Massa: kg, g, mg, t, lb, oz (libra e onça avoirdupois).
- Área: m², km², cm², ha, ft².
- Volume: L, mL, m³, cm³, gal US (galão líquido americano, não imperial).
- Velocidade: m/s, km/h, mph, nó (milha náutica de 1852 m).
- Pressão: Pa, kPa, MPa, bar, atm, psi (gravidade padrão de 9,80665 m/s² para libra-força).
- Energia: J, kJ, MJ, Wh, kWh, cal (caloria termoquímica, 4,184 J).
- Tempo: s, ms, min, h, dia (24 h; sem calendário ou horário de verão).
- Dados: bit, B, kB, MB, GB, TB, KiB, MiB, GiB, TiB (1 B = 8 bits; decimal 10^3, binário 2^10).
- Temperatura: °C, °F, K. Somente temperatura absoluta, não intervalos; rejeita abaixo de zero kelvin.

O motor usa Fraction para fatores racionais e operações afins, com saída Decimal de 34 dígitos significativos, arredondada quando necessário. Aceita ponto ou vírgula decimal, sem agrupamento de milhares, expressões ou notação científica na entrada, até 64 caracteres. As demais grandezas aceitam valores com sinal, inclusive diferenças negativas; não valida se representam uma situação fisicamente possível. Não converte moedas, grandezas incompatíveis ou taxas em tempo real. Não é instrumento certificado de metrologia.

## Validação

Exemplos: 1 in = 2,54 cm; 36 km/h = 10 m/s; 1 atm = 101325 Pa; 100 °C = 212 °F; -459,67 °F = 0 K; 1 MB = 1000000 B; 1 MiB = 1048576 B. Testes em Linux/Xvfb; validação nativa Windows pendente. O catálogo mantém a categoria histórica Quick Actions para Convert, embora a fase de entrega seja Business Intelligence.
