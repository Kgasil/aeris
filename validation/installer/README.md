# Aeris Desktop — Instalador simplificado (etapa 02)

A receita [Aeris.iss](Aeris.iss) é um overlay do pacote Fix 1 verificado. A CI copia a receita somente após conferir o ZIP original e os identificadores críticos; o ZIP histórico não é alterado.

## Experiência prevista

1. Baixar e abrir o Setup.exe. O Windows pode apresentar avisos de segurança; não desabilite proteções.
2. Ler a informação de prévia experimental (sem assinatura e somente dados fictícios).
3. Na tela de atalhos, clicar em Instalar. O atalho da área de trabalho vem selecionado e pode ser desmarcado; o menu Iniciar é criado sempre.
4. Concluir. A opção de abrir Project Aeris é voluntária e desmarcada por padrão; não abre em instalação silenciosa.

O idioma é selecionado automaticamente quando reconhecido (PT-BR/EN); a caixa de idioma aparece se não houver correspondência. Não há tela de boas-vindas, seleção de pasta ou grupo e confirmação redundante de Ready. A tela de atalhos é a confirmação explícita de instalação. A tela de avisos permanece.

A pasta do programa, AppId, mutex, arquitetura, versão mínima e instalação por usuário foram preservados. Sem autorun, privilégios administrativos exigidos, download de dependências, associações de arquivo, exclusão de dados ou reinício forçado. O Python está no pacote; Ollama e OCR reais permanecem opcionais e separados. A desinstalação deve preservar %LOCALAPPDATA%\Aeris.

## Validação

- [x] Revisão do código original da receita e do build no ZIP Fix 1.
- [x] Overlay e verificações de invariantes adicionados ao workflow.
- [ ] Compilar a receita modificada no Inno Setup/Windows.
- [ ] Verificar atalhos de menu Iniciar e Desktop, destino correto, remoção e ausência de abertura silenciosa em CI.
- [ ] Testar a experiência gráfica PT-BR/EN, opção de desmarcar atalho e abrir aplicativo, usuário comum e aviso de prévia no Windows 10/11.
- [ ] Verificar atualização entre versões distintas e direitos de redistribuição.

Referência Inno Setup: https://jrsoftware.org/ishelp/topic_setup_disablereadypage.htm ; https://jrsoftware.org/ishelp/topic_setup_showlanguagedialog.htm ; https://jrsoftware.org/inno-setup/documentation/topic_runsection.htm

Nenhum novo binário publicado nesta etapa. O próximo passo é confirmar a compilação e a CI (etapa 03); a liberação do download permanece condicionada à auditoria e confiança.
