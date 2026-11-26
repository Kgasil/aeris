# Aeris Metadata — v0.5.0a4

## Escopo
- PNG: assinatura, dimensões de IHDR, texto tEXt não comprimido até 8 KiB. Indicação genérica de outros blocos de metadados sem decodificação.
- JPEG: segmentos antes do primeiro scan, dimensões SOF, comentários e campos EXIF ASCII selecionados (fabricante, modelo, autor, datas, software, descrição e números de série). Referência GPS sinalizada sem coordenadas. EXIF parcial, sem miniaturas e sem XMP.
- DOCX, XLSX e PPTX: identificação estrutural simplificada por entradas ZIP e leitura de docProps/core.xml. Autor, título, assunto, descrição, palavras-chave, última edição por e datas. Não lê conteúdo, histórico, comentários, propriedades personalizadas ou relações externas.

## Controles e limites
Módulo desativado por padrão; permissão de sessão Metadata → Ler arquivo e confirmação individual. Sem rede, escrita, extração em disco ou execução de conteúdo. Limite 32 MiB por arquivo; 4096 segmentos, 40 campos com prévia de até 500 caracteres, diretório ZIP até 2 MiB e 10.000 entradas, XML até 128 KiB UTF-8. ZIP64, pacotes multidisco e XML com DTD/entidades declaradas são rejeitados. Não é verificador de formatos; PNG CRC e conteúdo de imagem não são validados. Reutiliza restrições de caminhos locais de Verify; não elimina todas as corridas de sistema de arquivos nem substitui isolamento do SO. Cancelamento é cooperativo, descarte de resultado após revogação, fechamento ou limpeza. Relatório em memória, sem apagamento seguro e sem controle de cópias manuais pelo usuário. Use dados fictícios.

## Validação
137 testes unitários executáveis, 3 ignorados (Windows), 22 smoke tests gráficos aprovados em Linux/Xvfb. Testes com estruturas sintéticas de PNG, EXIF nas duas ordens de bytes e três variantes OOXML; limites, XML não suportado, arquivo truncado, migração, permissão e descarte. Validação Windows 10/11, auditoria de segurança, corpus real e medições de desempenho pendentes. A ausência de campos no relatório não demonstra ausência de metadados. Remoção em cópias, PDF e outros formatos ficam para refinamentos futuros. Próximo: Health.
