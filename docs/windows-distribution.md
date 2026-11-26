# Windows Distribution I — v0.13.0a1

## Estado

Receita de build e instalação implementadas, **não compiladas no Windows**. O ZIP desta entrega contém código-fonte, scripts e testes, não um executável. Não há certificação, assinatura digital, instalador público ou resultado medido de tamanho de instalação. As ferramentas atuais continuam pré-alpha, para dados fictícios.

## Escolhas

- Windows 10/11 x64 (CPU AMD64), CPython 3.12 x64 para construção. PyInstaller 6.19.0 fixado como dependência direta de build; Inno Setup 6.3 ou superior da série 6. Transitividade ainda não travada por hashes. O bundle onedir contém o runtime Python/Tcl/Tk, sem necessidade de Python separado no computador de destino; essa propriedade precisa ser demonstrada em VM limpa. O pacote portátil requer extrair toda a pasta, incluindo `_internal`.
- Inno Setup: instalação por usuário, sem elevação solicitada, caminho padrão `%LOCALAPPDATA%\Programs\KGVision\Aeris`; arquivos de dados `%LOCALAPPDATA%\Aeris` separados, sem regra de exclusão na desinstalação. Atalho no menu Iniciar e atalho opcional na área de trabalho. Não cria serviços, inicialização automática, atualização automática nem associação de extensões. Não inicia o aplicativo automaticamente.
- Mutex nomeado `Local\KGVision.Aeris.Desktop` para instâncias empacotadas na sessão Windows; Inno usa o mesmo nome para pedir que o usuário encerre o programa antes de instalar/desinstalar. Não é isolamento de segurança, não cobre outras sessões ou execução por código-fonte. A instalação não força fechamento nem reinício.
- O catálogo JSON é incluído explicitamente. A distribuição usa janela sem console e ícone da marca. O modo `--self-test` inicializa Hub oculto em pasta temporária, valida os 50 nomes do catálogo e retorna código de saída 0/1. Não consulta dados reais. Isso não comprova funcionamento de todos os módulos empacotados.
- O guia de frases de Translate está incluído. Argos experimental depende de um interpretador independente e não está empacotado; a opção fica indisponível na edição empacotada (inclusive com seleção programática), evitando relançamento acidental do próprio exe. Continua disponível por código-fonte. Ollama, modelos, Tesseract e dados de idioma permanecem opcionais e externos. Microfone e TTS continuam dependentes de Windows/System.Speech.

## Construção em Windows (desenvolvedor)

Instale CPython 3.12 x64 com Tcl/Tk e Inno Setup 6 (6.3+), de fontes oficiais. Execute a partir da pasta extraída, em PowerShell:

```powershell
.\distribution\build.ps1
# Ou forneça o caminho explícito do compilador:
.\distribution\build.ps1 -Iscc 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
# Para produzir somente o ZIP portátil:
.\distribution\build.ps1 -PortableOnly
```

O script não altera a política de execução. Se a política local impedir a execução, examine o código e siga as regras da organização; não desabilite proteções globais. A construção faz download das dependências de empacotamento via pip no ambiente virtual isolado. Usa uma pasta de staging única em `distribution/out/`, interrompe em falhas de testes/compilação e testa a inicialização empacotada antes de produzir os artefatos. A compilação do Inno depende de `ISCC.exe`, instalado separadamente. O build não publica arquivos nem instala o resultado. Não use artefatos de uma execução incompleta.

Saídas esperadas (ainda não produzidas):

- `Aeris-0.13.0a1-Windows-x64-portable.zip`
- `Aeris-0.13.0a1-Windows-x64-Setup.exe` (exceto `-PortableOnly`)
- `SHA256SUMS.txt` (hashes dos artefatos; integridade, não autenticidade)
- `build-dependencies.txt` (inventário de versões)

O script coleta licença do Python, avisos do Tcl/Tk quando disponíveis e avisos de pacotes de build. Essa coleta não substitui auditoria completa de licenças e revisão dos componentes realmente distribuídos (inclusive bootloader, runtime e instalador). Não redistribuir publicamente antes dessa revisão. Sem assinatura Authenticode; não desative SmartScreen/antivírus. O código e os artefatos não devem conter dados pessoais.

## Validação Windows Distribution II (a executar)

Use VM Windows 10 e Windows 11 x64 limpas, sem Python, com conta comum, em snapshot descartável e dados fictícios. Registre versão do SO e do runtime, versão do build, hashes e resultado de cada cenário.

| Cenário | Critério esperado |
|---|---|
| Compilação | Script termina com código zero; arquivos e hashes presentes |
| Inicialização portátil | Extrair bundle completo e abrir Aeris.exe sem Python externo |
| Instalação | Wizard PT-BR/EN, caminho por usuário, sem solicitação de elevação por padrão |
| Catálogo | Hub lista 50 ferramentas; módulos abrem sob demanda |
| Mutex | Segunda instância avisa e termina; instalador pede encerramento manual se app ativo |
| Atualização | Preferências e cópias protegidas permanecem; sem encerramento forçado |
| Desinstalação | Remove arquivos instalados/atalhos; preserva `%LOCALAPPDATA%\Aeris` e outros arquivos pessoais |
| Reinstalação | Preferências anteriores continuam legíveis; cópias DPAPI recuperáveis no mesmo perfil |
| DPAPI | Executar testes nativos, corrupção e backup/restore com dados fictícios |
| Ferramentas externas | Ollama/Tesseract ausentes tratam falha; presença e operação real testadas separadamente |
| Voz | Ditado e voz masculina com permissões, interrupção, dispositivos indisponíveis |
| Consumo | Medir tamanho real do ZIP/setup, RAM/CPU, abertura e ociosidade |
| Distribuição | Inventário/licenças, análise antimalware, assinatura/estratégia de confiança, documentação |

A execução dos testes nativos do pacote-fonte em Windows não substitui testes do executável instalado. Modo silencioso, downgrade, múltiplas sessões, cancelamento de instalação e comportamento quando arquivo está bloqueado ainda requerem verificação. Não publicar como estável antes da validação.

## Referências técnicas

- https://pyinstaller.org/en/v6.19.0/usage.html
- https://pypi.org/project/pyinstaller/6.19.0/
- https://jrsoftware.org/inno-setup/documentation/topic_setup_privilegesrequired.htm
- https://jrsoftware.org/inno-setup/documentation/topic_setup_architecturesallowed.htm

## Atualização v0.13.0a2

A verificação de artefatos e o autocheck ampliado foram implementados. Veja `windows-distribution-ii.md`; os cenários nativos acima permanecem pendentes.
