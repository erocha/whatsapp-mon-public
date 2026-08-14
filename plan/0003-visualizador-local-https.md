# Plano 0003 — Visualizador local HTTPS

**Status:** implementado e validado

## Objetivo

Criar uma aplicação web Python responsiva para consultar o backup sob demanda no computador e, opcionalmente, pelo celular na rede doméstica com HTTPS.

## Etapas executadas

- Criação de `web-apps/whatsapp-viewer` com FastAPI, Jinja2, CSS responsivo e JavaScript local.
- Abertura de `msgstore.db` e `wa.db` exclusivamente em modo somente leitura.
- Criação de `data/viewer-data.db` para autenticação, contatos, apelidos e índice FTS5.
- Implementação de conversas, grupos, participantes, mensagens paginadas, respostas, reações, chamadas, mídias e pesquisa.
- Autenticação Argon2, CSRF e cookie `Secure`, `HttpOnly`, `SameSite=Strict`.
- Scripts de instalação, indexação, HTTPS, execução local e execução na LAN.
- Certificado mkcert para localhost, hostname e IPs locais; CA exportada para Android.
- Firewall limitado ao perfil privado e `LocalSubnet`.
- Interface de importação VCF e apelidos locais.

## Validação realizada

- Mensagens com texto indexadas incrementalmente.
- Índice FTS5 armazenado apenas no banco auxiliar local.
- 69.807 resultados numa busca de validação por termo comum.
- HTTPS e login responderam corretamente.
- API sem sessão retornou HTTP 401.
- Hash do banco original permaneceu inalterado.

## Pendências conhecidas

- Instalar manualmente a CA no Android antes do acesso HTTPS sem alerta.
- Reservar o IP do computador no roteador ou renovar o certificado após mudança de IP.
- Importar um VCF para melhorar os nomes, pois `wa.db` não contém perfis úteis neste backup.
