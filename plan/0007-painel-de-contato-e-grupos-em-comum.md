# Plano 0007 — Painel de contato e grupos em comum

**Status:** implementado

## Objetivo

Exibir um painel inspirado nas informações de contato do WhatsApp Web ao clicar em telefone, identificador, participante ou remetente.

## Etapas executadas

- Painel lateral responsivo com foto disponível, iniciais, nome, telefone e JID.
- Resolução de identidades equivalentes por `jid_map`.
- Contagem e prévia das 12 mídias mais recentes da conversa direta.
- Consulta e listagem de grupos em comum.
- Navegação do painel para conversa direta ou grupo comum.
- Cliques em nomes/números da lista, cabeçalho, participantes e remetentes.
- Endpoints autenticados para perfil e miniatura histórica de foto.
- Links de mídia em nova aba com `noopener noreferrer`.

## Dados disponíveis

- A pasta `WhatsApp Profile Photos` deste backup está vazia.
- Miniaturas históricas de alteração de foto são usadas quando associáveis ao contato.
- Sem foto disponível, o painel mostra as iniciais.

## Limitações

- Voz e vídeo aparecem apenas como referência visual e ficam desativados: o arquivo local não inicia chamadas.
- “Grupos em comum” reflete os participantes registrados no backup, não necessariamente o estado atual no WhatsApp.
- Mídias ausentes da cópia local podem não gerar miniatura.
