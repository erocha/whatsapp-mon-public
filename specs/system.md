# Especificação do sistema

## Finalidade

Visualizador pessoal e local de um backup Android do WhatsApp. O sistema não conecta ao serviço do WhatsApp, não envia mensagens e não modifica os bancos originais.

## Arquitetura

- Backend: Python 3.12, FastAPI e Uvicorn.
- Interface: Jinja2, HTML, CSS responsivo e JavaScript local.
- Origem: `msgstore.db`, `wa.db` e pasta `Media`.
- Dados próprios: SQLite `viewer-data.db`.
- Pesquisa: SQLite FTS5 incremental.
- Transporte: HTTPS obrigatório, inclusive em localhost.

## Funcionalidades

- Login e logout.
- Listagem e filtro de contatos, grupos e canais.
- Conversas paginadas por cursor.
- Reações, respostas citadas, transcrições e mídias.
- Participantes e administradores de grupos.
- Histórico de chamadas.
- Pesquisa textual global ou por conversa.
- Importação VCF e apelidos manuais.
- Importação CSV `Phone;Name;PushName;ShortName;IsBusiness` com associação a `@lid`.
- Exportação VCF complementar de números identificáveis no backup.
- Exibição de telefone explícito ou resolvido pela associação `jid_map`.
- Painel de contato com foto histórica disponível, mídias recentes e grupos em comum.
- Visualização ampliada em tela cheia das imagens locais.
- Links externos clicáveis em nova aba.

## Restrições

- Nenhum banco ou arquivo de mídia deve ser copiado para o repositório.
- A chave do backup nunca deve ser armazenada.
- A aplicação não deve escrever em `msgstore.db` ou `wa.db`.
- Mídias somente podem ser servidas de dentro da raiz configurada.
- A LAN permanece desativada por padrão.
