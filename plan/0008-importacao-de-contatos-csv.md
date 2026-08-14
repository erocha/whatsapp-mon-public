# Plano 0008 — Importação de contatos CSV

**Status:** implementado

## Formato

```text
Phone;Name;PushName;ShortName;IsBusiness
13135550002;Meta AI;;Meta AI;true
```

## Etapas executadas

- Importador CSV autenticado nas configurações.
- Separador obrigatório `;` e cabeçalho validado.
- Leitura UTF-8 com suporte a BOM.
- Validação e normalização de telefones entre 7 e 15 dígitos.
- Precedência de nome: `Name`, `PushName`, `ShortName`, telefone.
- Armazenamento de `PushName`, `ShortName` e `IsBusiness` no banco auxiliar.
- Associação automática do telefone aos identificadores `@lid` por `jid_map`.
- Limite de upload de 20 MB e proteção CSRF.
- Linhas duplicadas pelo telefone são consolidadas usando a última ocorrência.
- Registros internos sem telefone utilizável, como `0;WhatsApp`, são ignorados e contabilizados no resultado.

## Segurança

O importador grava somente em `data/viewer-data.db`. `msgstore.db` e `wa.db` permanecem somente leitura.
