# Project Aeris — Discreto e Eficiente.
## Candidato de código-fonte 1.0.0rc1

Este marco congela o escopo inicial de 50 ferramentas. É um pacote de testes, não um instalador, versão estável, certificação ou garantia de segurança. Edição única gratuita do Aeris, sem anúncios ou conta obrigatória. A extensão Chromium ainda não foi implementada. Modelos Ollama, Tesseract e dependências opcionais são externos, com requisitos e licenças próprios.

### Executar a partir do código-fonte

1. Em uma VM Windows x64 ou ambiente de teste descartável, instale Python 3.12 ou 3.13 x64 com Tcl/Tk a partir da fonte oficial.
2. Extraia o ZIP. Na pasta `desktop`, execute `py -3 main.py` ou `iniciar.bat`. Use somente dados fictícios.
3. Ative módulos desejados no Hub. Para permissões, use a central de Privacidade. Não há restauração automática na abertura; o salvamento automático dos sete módulos é opt-in por sessão e deve ser finalizado com salvamento imediato antes de sair.
4. IA: instale Ollama e um modelo local compatível separadamente, desative os recursos de nuvem e confirme permissões. Os fluxos de voz/IA precisam de validação nativa. Não envie informações sensíveis. Argos experimental só funciona por código-fonte; Lens requer Tesseract opcional.

### Compilar a distribuição

Siga `windows-distribution.md` e `windows-distribution-ii.md`. Em Windows x64 com CPython 3.12 x64 e Inno Setup 6.3+ instalado, execute, na raiz extraída:

```powershell
.\distribution\build.ps1
```

O build deverá gerar `Aeris-1.0.0rc1-Windows-x64-portable.zip`, `Aeris-1.0.0rc1-Windows-x64-Setup.exe`, `SHA256SUMS.txt`, `AERIS-EXE-SHA256.txt` e inventário de dependências. São saídas esperadas, não arquivos produzidos nesta entrega. Não desative a proteção do Windows. O build é preliminar, sem assinatura. Não redistribua binários antes da revisão de licenças e confiança.

### Evidência e decisão de lançamento

Execute `py -3 distribution/release-gate.py` na raiz. O código de saída 1 é esperado enquanto houver itens pendentes. Registre cada resultado com referência ao relatório, versão e hash dos artefatos testados. Um campo `passed` sem evidência não libera o item. O script apenas valida o registro local; não atesta evidências, não assina e não impede uploads. O responsável deve conferir a evidência antes de publicar.

| Item | Evidência necessária |
|---|---|
| Build | Logs do build real x64, inventário, hashes e autocheck do executável |
| Windows 10 e Windows 11 | Resultados em VMs limpas, conta comum, sem Python externo |
| Instalação e atualização | Instalação, reinstalação, atalhos, mutex, desinstalação preservando dados de teste |
| DPAPI | Seis testes nativos e recuperação de dados fictícios no mesmo perfil |
| IA, voz e OCR | Teste real de modelo local, fala masculina, microfone, OCR e erros de dependência |
| Desempenho e acessibilidade | Medições de CPU, RAM, latência, tamanho e avaliação de navegação por teclado |
| Licenças e confiança | Revisão de todos componentes distribuídos, avisos, estratégia de assinatura e análise antimalware |
| Publicação | Artefatos validados, hashes correspondentes, descrição honesta da prévia e links conferidos |

### Publicação do código-fonte

Mantenha `main` como branch do site e `develop` como código desktop. Para publicar o pacote-fonte, clone o repositório `https://github.com/Kgasil/aeris`, selecione `develop`, faça cópia dos diretórios `desktop`, `docs`, `distribution` e do README do pacote, preservando os arquivos do website que já existirem. Revise `git diff` e `git status` antes de commit/push; não inclua dados pessoais, caches, ambiente virtual ou resultados privados. Não force o push. O site pode oferecer o ZIP-fonte com rótulo de prévia; não deve apontar para um executável inexistente. A futura release binária é condicionada à revisão acima. Não há licença pública de redistribuição do código definida nesta entrega.
