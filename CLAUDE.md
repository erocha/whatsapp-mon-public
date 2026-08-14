# Instruções para Codex e Claude

## Contexto atual

Este repositório contém um visualizador local de backup do WhatsApp. A implementação ativa está em `web-apps/whatsapp-viewer`. Consulte primeiro `memory.md`, `specs/` e `plan/`.

## Regras obrigatórias

- Trate a pasta de backup configurada pelo operador como fonte externa sensível.
- Abra `msgstore.db` e `wa.db` somente com URI SQLite `mode=ro` e `PRAGMA query_only=ON`.
- Nunca copie bancos, mídias, certificados, senha ou chave de backup para o Git.
- Não altere nem apague arquivos do backup.
- Grave índices, configurações, contatos e autenticação somente em `data/viewer-data.db`.
- Não exponha mídia fora da raiz configurada e mantenha autenticação no endpoint.
- Preserve cookies seguros, CSRF, Argon2 e HTTPS.
- O acesso LAN deve permanecer opt-in e limitado à sub-rede privada.
- Use consultas paginadas; não carregue milhões de mensagens na memória.
- Antes e depois de mudanças de alto risco, valide que o hash do banco original não mudou.

## Fluxo de trabalho

1. Leia o plano mais recente e as especificações relacionadas.
2. Inspecione o esquema real antes de assumir nomes de tabelas ou colunas.
3. Faça mudanças pequenas e teste com `pytest`.
4. Atualize o plano correspondente e `memory.md` quando houver decisão ou resultado relevante.
5. Documente limitações reais, especialmente mídias ausentes.

## Estado conhecido

- Aplicação, índice FTS5, HTTPS, autenticação e importação VCF estão implementados.
- Cinco testes automatizados passam.
- Há registros de mídia sem arquivo físico no backup.
- A arquitetura antiga Baileys/Google Sheets foi abandonada e existe apenas como histórico.
