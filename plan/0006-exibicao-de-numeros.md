# Plano 0006 — Exibição de números

**Status:** implementado

## Objetivo

Mostrar na interface o telefone armazenado ou relacionável no banco, mesmo quando o contato possui nome ou JID interno `@lid`.

## Etapas executadas

- Leitura de telefone explícito em JIDs `@s.whatsapp.net`.
- Resolução de `@lid` por meio da tabela interna `jid_map`.
- Inclusão dos campos `phone` e `sender_phone` nas APIs.
- Exibição no formato `Nome · +telefone` em conversas, detalhes, participantes, chamadas e remetentes.
- Prevenção de duplicação quando o próprio nome já é o número.
- Testes unitários para apresentação do telefone.

## Limitação

Um `@lid` sem registro em `jid_map` não revela telefone e permanece apenas com o identificador/nome disponível.
