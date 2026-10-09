# Plano 0010 — Sanitização e publicação

**Status:** concluído

## Objetivo

Disponibilizar uma versão pública do projeto sem dados pessoais, credenciais ou conteúdo do backup.

## Etapas executadas

- Auditoria do conteúdo e de todo o histórico Git.
- Remoção de nomes de usuário, caminhos locais, hashes e estatísticas específicas do backup.
- Substituição do autor do commit por `erocha` com e-mail `noreply` do GitHub.
- Padronização do modelo como `config.toml.example`; `config.toml` permanece local e ignorado.
- Inclusão da licença GNU Affero General Public License v3.0.
- Reescrita do único commit do repositório privado.
- Criação e publicação de `erocha/whatsapp-mon-public`.
- Validação de que bancos, mídias, contatos, certificados e credenciais não estão versionados.

## Resultado

Os repositórios privado e público mantêm a mesma árvore sanitizada. O desenvolvimento local continua acompanhando `origin/main`, enquanto o remoto `public` aponta para a distribuição pública.
