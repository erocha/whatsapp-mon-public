# Memory — WhatsApp local

## Estado atual — 13/08/2026

O projeto ativo é o visualizador local em `web-apps/whatsapp-viewer`. Ele consulta um backup descriptografado configurado pelo operador somente em modo leitura e oferece interface HTTPS protegida por senha.

- Backend FastAPI; interface responsiva; SQLite FTS5.
- `viewer-data.db` guarda somente índice, senha Argon2, sessão/configuração, VCF e apelidos.
- A indexação é incremental e mantém seus dados exclusivamente no banco auxiliar local.
- A integridade do `msgstore.db` deve ser validada antes e depois de operações de alto risco.
- HTTPS gerado com mkcert para localhost, hostname e IP local.
- A LAN é opt-in e a regra de firewall é limitada ao perfil Privado e `LocalSubnet`.
- Importação de contatos VCF e apelidos estão disponíveis nas configurações.
- Exportação complementar gera vCard 3.0 apenas para JIDs que revelam telefone; `@lid` sem telefone associado é excluído.
- O importador CSV aceita `Phone;Name;PushName;ShortName;IsBusiness`, usa `;`, guarda metadados no banco auxiliar e associa telefones a `@lid` por `jid_map`.
- Caminhos de mídia `Media/...` foram corrigidos. Alguns registros não possuem arquivo físico no backup.
- Links HTTP/HTTPS nas mensagens abrem em nova aba com `noopener noreferrer`.
- Telefones são mostrados junto aos nomes; JIDs `@lid` são resolvidos pela tabela `jid_map` quando possível.
- O painel de contato mostra miniatura histórica disponível, telefone, JID, mídias e grupos em comum.
- Imagens das mensagens e do painel de contato abrem em visualizador local de tela cheia por clique ou toque.
- Planos e status: consulte `plan/`. Especificações: consulte `specs/`. Instruções aos agentes: consulte `CLAUDE.md`.
- O histórico Git foi sanitizado para remover caminhos, estatísticas e metadados pessoais. O repositório público `erocha/whatsapp-mon-public` usa AGPL-3.0 e recebe apenas arquivos genéricos; configurações locais permanecem ignoradas.

## Arquitetura anterior — substituída

O conteúdo abaixo registra a concepção antiga de logger ativo por dispositivo vinculado. **Não é a arquitetura atual e não deve ser implementado sem nova decisão explícita.**

> Contexto acumulado desta conversa, para uso como referência/memória em ferramentas de desenvolvimento (ex.: Google Antigravity) ao especificar ou construir este projeto.

## Objetivo

Aplicação pessoal que acompanha grupos específicos do WhatsApp (dos quais o usuário já participa) e registra dados das mensagens para uso próprio — não é um bot de atendimento, não responde nem interage ativamente nos grupos.

## Decisões técnicas já tomadas

- **Não usar a API oficial do WhatsApp (Business Cloud API)** — ela é voltada a negócios conversando com clientes individuais, não a monitorar grupos existentes dos quais o usuário já é membro.
- **Usar uma biblioteca não oficial que reimplementa o protocolo de "dispositivo vinculado"** do WhatsApp Web/Desktop. Duas opções avaliadas:
  - **Baileys** (recomendada) — conecta via WebSocket direto, sem navegador. Mais leve, mais popular, mantida pela organização WhiskeySockets.
  - **whatsapp-web.js** — controla um Chrome headless via Puppeteer. Mais pesado em recursos.
- **Autenticação:** QR code escaneado uma vez com o número real do usuário. O script passa a aparecer como mais um "dispositivo conectado" no WhatsApp do celular (igual ao WhatsApp Web do navegador).
- **Comportamento do bot: 100% passivo / read-only.**
  - Apenas escuta o evento de novas mensagens e filtra pelos grupos de interesse.
  - Não envia mensagens, não entra/sai de grupos automaticamente, não realiza ações em volume alto.
  - Esse é o padrão de uso considerado mais seguro dentro do universo de bibliotecas não oficiais.
- **Número a usar:** pode ser o número principal do usuário. Risco de flag/ban existe (é um protocolo de engenharia reversa, não sancionado oficialmente pela Meta), mas é considerado baixo para uso passivo e de baixo volume. O risco sobe bastante se o bot também enviar mensagens ou automatizar ações ativas.
- **Dados a capturar: tudo, incluindo mídia baixada.** Texto, remetente, timestamp, grupo/JID, e o conteúdo de imagens/áudios/vídeos das mensagens.
  - Implicação direta: aumenta a superfície de LGPD (ver "Riscos conhecidos") e exige um destino de armazenamento para binários, já que planilhas não guardam blobs — ver arquitetura abaixo.
- **Persistência: Google Sheets** (por linha = 1 mensagem, com colunas grupo, remetente, timestamp, texto, tipo de mídia, link da mídia).
  - Trade-off aceito conscientemente: Sheets tem rate limits de API e fica menos prático em volumes muito altos de mensagens, mas ganha em facilidade de visualização/edição manual sem precisar de outra ferramenta.

## Riscos conhecidos

- **Instabilidade do protocolo:** updates do WhatsApp podem quebrar a conexão da biblioteca, exigindo novo escaneamento de QR code.
- **Risco de ban do número:** baixo mas não nulo para uso passivo; maior se o número usado for o principal (perda de acesso ao WhatsApp do dia a dia seria a consequência, diferente de usar um número descartável).
- **LGPD:** mensagens de outras pessoas nos grupos são dados pessoais de terceiros. Com a decisão de capturar mídia (fotos, áudios com voz, vídeos), esse risco aumenta bastante — imagem e voz são dados biométricos/sensíveis em potencial. Vale considerar anonimização, retenção limitada (auto-expurgo após X dias) ou avisar os participantes do grupo sobre o registro.
- **Custo de API do Google:** Sheets API (e Drive API, se usada para mídia — ver abaixo) tem cotas gratuitas generosas para uso pessoal, mas exigem projeto no Google Cloud Console + credenciais (service account ou OAuth).

## Arquitetura proposta (MVP)

- Script Node.js/TypeScript usando Baileys.
- Listener no evento `messages.upsert`, filtrando por JID dos grupos escolhidos.
- **Pipeline de mídia:** ao chegar uma mensagem com mídia, o Baileys expõe uma função de download do binário.
  - Opção recomendada: subir o arquivo para uma pasta no **Google Drive** (mesma conta usada para o Sheets, reaproveitando as mesmas credenciais/escopo), organizada por grupo/data, e gravar o link/ID do arquivo do Drive na linha correspondente do Sheets.
  - Alternativa mais simples (sem Drive API): salvar a mídia em pasta local (ex.: `./media/<grupo>/<data>/`) e gravar o caminho local na coluna de mídia do Sheets. Mais fácil de implementar no MVP, mas os arquivos só existem na máquina onde o script roda.
- **Persistência dos metadados/texto:** Google Sheets API, uma linha por mensagem.
- Lógica de reconexão automática tratada no próprio código.

## Alternativas avaliadas (não escolhidas como base, mas servem de referência)

- [WhiskeySockets/Baileys](https://github.com/WhiskeySockets/Baileys) — biblioteca base recomendada.
- [fun-with-serverless/whatsapp-logger](https://github.com/fun-with-serverless/whatsapp-logger) — exemplo completo (whatsapp-web.js + AWS Lambda/Fargate + Google Sheets + resumos via ChatGPT). Funcional, mas com infraestrutura AWS embutida (~US$18/mês) e maior complexidade do que o necessário para um MVP pessoal.
- [chyke007/whatsapp-group-bot](https://github.com/chyke007/whatsapp-group-bot) — bot simples de monitoramento/comparação de valores em mensagens.
- [hoodini/whatsapp-public-logan](https://github.com/hoodini/whatsapp-public-logan) — bot com capacidades de IA para grupos.
- [marcoh00/walog](https://github.com/marcoh00/walog) — logger de conversas minimalista.

## Em aberto / próximos passos

- [ ] Decidir entre mídia no Google Drive (mais robusto, exige Drive API + credenciais) vs. mídia em pasta local (mais simples, menos portável) — ver "Arquitetura proposta" acima.
- [ ] Criar projeto no Google Cloud Console e gerar credenciais (service account) com acesso à Sheets API (e Drive API, se aplicável).
- [ ] Definir estrutura exata da planilha (nomes de colunas, uma aba por grupo ou uma aba única com coluna de grupo).
- [ ] Definir política de retenção/anonimização dos dados de terceiros, dado o aumento do risco de LGPD com captura de mídia.
- [ ] Montar o script inicial de conexão (QR code) + listener de mensagens filtrado por grupo + escrita no Sheets.
- [ ] (Opcional, fase 2) Pipeline de estruturação/enriquecimento dos dados capturados usando um LLM — encaixa com o interesse do usuário em engenharia de contexto e especificação de sistemas em linguagem natural.
