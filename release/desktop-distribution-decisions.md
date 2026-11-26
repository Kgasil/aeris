# Aeris Desktop — decisões de distribuição (pendentes de aprovação)

Este documento é uma minuta de revisão, não uma licença publicada ou aprovação em nome do titular. O RC3 permanece experimental.

## Direitos e termos
O arquivo PYTHON-LICENSE.txt efetivamente distribuído no RC3 contém a seção "Additional Conditions for this Windows binary build". Ela exige que redistribuidores e usuários finais concordem com condições que protejam Microsoft Distributable Code. O ZIP fonte RC3 não contém licença de primeira parte identificável pelo nome do arquivo. Disponibilidade gratuita e acesso ao código-fonte não equivalem, por si, a licença aberta nem comprovam titularidade dos recursos.

As orientações oficiais [Visual C++ REDIST](https://learn.microsoft.com/en-us/visualstudio/releases/2026/redistribution), [DLLs redistribuíveis](https://learn.microsoft.com/en-us/cpp/windows/determining-which-dlls-to-redistribute?view=msvc-170) e [Universal CRT](https://learn.microsoft.com/en-us/cpp/windows/universal-crt-deployment?view=msvc-170) limitam a redistribuição a arquivos e condições aplicáveis. O RC3 contém 43 API sets, ucrtbase.dll e dois VCRUNTIME140 DLLs. A comparação automatizada de hashes com REDIST é evidência técnica, não prova de autorização. Não copiar DLLs do System32 para redistribuição. Considerar remoção das cópias UCRT desnecessárias para Windows 10/11 em candidato separado, com nova validação; não alterar RC3.

O texto efetivo do Inno Setup 6.7.4 permite uso inclusive comercial e redistribuição sob condições; preservar avisos e origem. O [fornecedor solicita licença comercial](https://jrsoftware.org/inno-setup/purchase) quando há benefício em contexto comercial. O titular deve confirmar o enquadramento antes de concluir revisão.

## Minuta de termos ao usuário final — NÃO VIGENTE
Aeris Desktop é planejado para uso gratuito em Windows. O titular deve aprovar a concessão de uso, limites da licença do código próprio e termos aplicáveis antes de publicar. Componentes de terceiros permanecem regidos por suas licenças; nada nestes termos restringe direitos concedidos por elas.

Quanto ao Microsoft Distributable Code incluído, preservar avisos de copyright, marca e patente; não apresentar Microsoft como autora ou patrocinadora do Aeris; não distribuir esse código para plataforma que não seja sistema operacional, runtime ou plataforma de aplicação da Microsoft; não o incluir em programas maliciosos, enganosos ou ilegais. A distribuição adicional deve respeitar as condições Microsoft aplicáveis, incluindo proteção equivalente e aceite quando exigido. Verificar o texto completo das licenças e termos efetivos, inclusive proteção de propriedade intelectual e exclusões de garantias aplicáveis, antes de aprovar esta minuta. Não apresentar esta minuta como parecer jurídico ou licença suficiente.

Recursos opcionais Ollama/Tesseract e seus modelos são instalados separadamente; não são redistribuídos pelo Setup. Documentar processamento local, permissões explícitas e dados preservados após desinstalação. Não garantir segurança absoluta; orientar backup e suporte. Qualquer termo de garantia/responsabilidade deve respeitar a legislação aplicável, inclusive direitos do consumidor.

## Decisões que exigem o titular
- Confirmar que possui ou obteve autorização para redistribuir código, marca, ícones, imagens e outros recursos próprios/externos; registrar fontes e licenças. Escolher licença de código próprio (não presumir open source) e aprovar termos gratuitos de uso.
- Confirmar enquadramento da licença Inno e termos Microsoft; revisar minuta com profissional qualificado quando necessário.
- Decidir assinatura Authenticode (recomendável para distribuição ampla; não enviar certificados, chaves, senhas ou tokens pelo chat). Uma eventual prévia sem assinatura deve ser claramente experimental, sem instrução de contornar proteções, após direitos e testes aplicáveis. A versão estável permanece bloqueada conforme roadmap.
- Disponibilizar evidências dos testes em Windows 10 e 11 suportados, conta comum, ambiente descartável e scanner ativo, sem dados pessoais.

## Correção documental do próximo candidato
O ZIP RC3 contém README.md e desktop/README.md ainda com o título/subtítulo histórico, versão RC1 e instruções de Python 3.12/3.13. O próximo build deve atualizar ambos para a versão interna efetiva, Python 3.14.10 de desenvolvimento, separar requisitos de execução por fonte e instalação Setup, e manter a distinção da extensão. Não editar o ZIP histórico nem substituir hashes já aprovados.

Sem confirmação de titularidade ou evidência de teste, nenhuma linha deste documento autoriza publicação.
