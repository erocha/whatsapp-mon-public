# Plano 0004 — Correções de mídia e links

**Status:** implementado

## Objetivo

Corrigir reprodução de mídia e tornar URLs das mensagens clicáveis.

## Etapas executadas

- Correção de caminhos que começavam por `Media/`, evitando a procura incorreta em `Media/Media/`.
- Suporte aos formatos `Media/...`, `WhatsApp/Media/...` e caminho Android absoluto.
- Validação do áudio da mensagem `2898460` no arquivo físico correspondente.
- Detecção de registros cujo arquivo de mídia não existe no backup.
- Remoção do player enganoso quando a mídia está ausente.
- Conversão segura de URLs HTTP/HTTPS em links que abrem em nova aba.
- Uso de `noopener noreferrer` nos links externos.
- Ampliação dos testes automatizados para cinco casos.

## Diagnóstico relevante

O áudio da mensagem `2898323` está registrado no banco como `PTT-20260530-WA0022.opus`, com 227.411 bytes e 95 segundos, mas o arquivo não existe na cópia local. Esse conteúdo só poderá ser recuperado copiando novamente a mídia do celular, caso ainda esteja disponível nele.
