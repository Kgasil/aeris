# Aeris Quality II — evidências de desenvolvimento

Branch: desktop-experience. Não houve publicação ou merge na versão pública.

## Correções
- Índice pré-processado do catálogo, sem cache de consultas do usuário.
- Eventos Tk de modificação sem alteração não repetem o fluxo de atualização.
- Atualização da conversa retorna se a janela estiver encerrada.
- Blocos silenciosos não acrescentam texto vazio à transcrição; contam para o limite de blocos.

Commits: da8c393e2c4415f0da07094bf3e4fa9e9e4bc0f7, 307aef84c1cb9abb8f344742014e9cf6963f1e14, ffa3d2ea37b463a266693d0e8d04057413559bf5.

## Execução local
Python 3.13.5, Linux, cópias isoladas. Comando: python -m unittest discover -s tests -v.
Resultado: 27 testes, 0 falhas, 0 erros. São 5 de voz, 4 de visão, 5 de vínculo visual, 7 de prontidão, 3 de papéis cromáticos e 3 do catálogo. O teste de equivalência do catálogo inclui 84 combinações.

Hashes Git dos arquivos novos testados e conferidos com o repositório:
- aeris/catalog_index.py: 1ea18f7b6db00a4d0c55bd3090a535fa48e027b4
- tests/test_catalog_index.py: 18af43cc6b3360a77351990c6f0aacc2fa9398e1
- aeris/registry.py: be68e6cc93371427e9f67ef6b9083e4d0d843861

Os testes de cores utilizam um recorte local da lógica de tema, não o arquivo completo. Não houve teste gráfico.

## Microbenchmark
50 registros sintéticos; 6 consultas não vazias, repetidas 500 vezes por medição; 5 medições por método; timeit.repeat e mediana. Construção do índice fora da medição. Método anterior: 0,634441 s por 3000 consultas. Método indexado: 0,032490 s. Cerca de 19,5x neste cenário. Não representa tempo de resposta do Tk, memória, desempenho real da IA ou ganho do aplicativo inteiro.

## Bloqueios e próximos testes
A tentativa de git ls-remote falhou por DNS (Could not resolve host: github.com). O conector permite ler e modificar arquivos, mas não confirma a execução integral da CI neste turno. Regressão completa, GUI Windows, áudio, captura real, consumo de RAM, instalador e antivírus continuam pendentes. Não há certificação nem recomendação de lançamento com base nestes testes isolados.
