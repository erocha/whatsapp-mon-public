# Plano 0005 — Exportação complementar de contatos

**Status:** implementado

## Objetivo

Gerar um VCF local com números identificáveis no banco do WhatsApp para complementar a exportação da agenda do Android/Google.

## Etapas executadas

- Exportação padrão dos JIDs de conversas diretas e opção separada para todos os participantes identificáveis.
- Validação de números entre 7 e 15 dígitos.
- Exclusão de grupos, canais e identificadores opacos `@lid`.
- Aplicação de apelidos manuais e nomes anteriormente importados por VCF.
- Geração de vCard 3.0 em UTF-8 com telefone internacional e JID de origem.
- Endpoint autenticado com `Cache-Control: no-store`.
- Botão de download nas configurações.
- Teste de escape de caracteres especiais do vCard.

## Limitações

- Não recupera telefone de contato presente apenas como `@lid`.
- Quando não existe nome conhecido, usa o número como nome.
- A exportação ampla contém aproximadamente 78 mil números neste backup; deve ser revisada antes de importar.
- É complementar e não substitui a exportação da agenda do celular.
