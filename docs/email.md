# Aeris Email — 0.3.0a4

- Módulo opcional, com acesso pelo Hub/Spotlight e temas existentes.
- `email_draft.py`: composição pura, validação de campos e 24 combinações de modelos; sem tradução, fatos inventados ou envio.
- `email_ui.py`: entrada manual, prévia somente leitura, invalidação por alteração de qualquer campo, cópia separada de assunto/corpo mediante autorização e confirmação.
- Limites: destinatário 120, assunto 200, detalhes 8000, assinatura 1000 caracteres.
- Nenhuma persistência de rascunhos ou assinaturas. Não há limpeza segura da RAM ou do histórico do clipboard do Windows. Use dados fictícios.
- Testes: `python -m unittest tests.test_email` e `python -m tests.smoke_email`. Validação Linux/Xvfb realizada; Windows 10/11 ainda pendente.
- Futuro: modelos personalizados persistentes protegidos, correção gramatical opcional, revisão de acessibilidade; não enviar automaticamente.
