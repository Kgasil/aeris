# Aeris Extension 1.0.0 — Como instalar / Installation

**Eficiência e Simplicidade. · by K&G Vision**

Extensão gratuita, Manifest V3, com 16 ferramentas. Distribuição manual para avaliação, fora das lojas de extensões. Os ZIPs 1.0.0 estão publicados no GitHub. [**Baixar extensão / Download extension**](https://github.com/Kgasil/aeris/raw/refs/heads/main/downloads/Aeris-Extension-v1.0.0-install.zip) · [Código-fonte completo / Full source](https://github.com/Kgasil/aeris/raw/refs/heads/main/downloads/Aeris-Extension-v1.0.0-completa.zip). Não use arquivos de terceiros.

**Marco 1.0 do Project Aeris:** esta versão refere-se à extensão; o código-fonte público Desktop permanece em RC1, o RC4 foi validado em CI e o RC5 consolidado (50 ferramentas refinadas) está em validação; lançamento estável adiado. [Visão geral do projeto](../README.md).

## Chrome

1. Extraia `Aeris-Extension-v1.0.0-install.zip` em uma pasta permanente, por exemplo `Documentos/AerisExtension`.
2. Abra `chrome://extensions/` na barra de endereços.
3. Ative **Modo do desenvolvedor**.
4. Clique em **Carregar sem compactação** (Load unpacked).
5. Selecione a pasta extraída que contém diretamente `manifest.json`, não o ZIP.
6. Abra o menu de extensões (ícone de quebra-cabeça) e fixe o Aeris se desejar.

## Microsoft Edge

1. Extraia o mesmo ZIP.
2. Abra `edge://extensions/`.
3. Ative **Modo de desenvolvedor**.
4. Clique em **Carregar descompactado** (Load unpacked) e selecione a pasta com `manifest.json`.
5. Abra o Aeris pelo menu de extensões.

## Opera

1. Extraia o ZIP e abra `opera://extensions/`.
2. Ative **Modo de desenvolvedor**.
3. Se disponível, clique em **Carregar descompactado** (Load unpacked) e selecione a pasta com `manifest.json`.
4. Abra a extensão pelo menu de extensões.

Os nomes dos comandos podem variar conforme idioma e versão. Se a opção estiver indisponível por política administrativa, não tente contorná-la. A compatibilidade independente nos três navegadores ainda não foi confirmada.

## Primeiro teste

Abra o [laboratório de validação](https://kgasil.github.io/aeris/extension-validation.html), selecione um texto fictício e experimente Capture ou Reading. Para Autofill, use apenas dados inventados, confira a prévia e confirme manualmente. Não utilize senhas, dados pessoais ou formulários reais de produção.

## Atualizar ou remover

- Atualizar: extraia a versão nova, substitua os arquivos na pasta permanente e clique em **Recarregar** na página de extensões. Selecione a pasta correta caso seja necessário instalar novamente. Dados locais podem ser perdidos.
- Remover: abra a página de extensões, localize Aeris e clique em **Remover**. A remoção pode apagar dados locais; não apaga textos já copiados para a área de transferência.

## Solução de problemas

- Manifesto não encontrado: escolha a pasta onde está `manifest.json`.
- Erro de pacote: extraia novamente e compare o SHA-256 com [os hashes publicados](../downloads/Aeris-Extension-v1.0.0-SHA256SUMS.txt).
- Sem acesso a uma página: use uma página HTTPS comum; páginas internas do navegador e páginas restritas podem não aceitar ferramentas contextuais.
- IA opcional: requer Ollama instalado separadamente e autorização explícita. As outras ferramentas não exigem Ollama.

## English quick start

Extract the official install ZIP into a permanent folder. Open `chrome://extensions/`, `edge://extensions/` or `opera://extensions/`; enable Developer mode and choose Load unpacked, if available and permitted. Select the directory containing manifest.json. Open Aeris from the browser extension menu. Test using synthetic data only. Do not bypass administrative policies. The ZIPs are available on GitHub. Independent native compatibility checks remain pending.

[Release notes](../release/extension-1.0.0-notes.md) · [Project website](https://kgasil.github.io/aeris/) · [Report a problem](https://github.com/Kgasil/aeris/issues).
