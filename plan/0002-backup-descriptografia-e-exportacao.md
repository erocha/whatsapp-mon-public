# Plano 0002 — Backup, descriptografia e exportação

**Status:** concluído

## Objetivo

Obter uma cópia local utilizável do WhatsApp pessoal, preservando os arquivos originais e permitindo análise local.

## Etapas executadas

- Confirmação de posse do celular e da senha do backup criptografado.
- Desativação orientada da criptografia ponta a ponta do backup.
- Geração de novo backup local no aparelho.
- Cópia dos dados para uma pasta local externa ao repositório.
- Localização de `msgstore.db`, `wa.db` e da pasta `Media`.
- Instalação e configuração local do WhatsApp Chat Exporter.
- Diagnóstico da geração HTML demorada para backups de grande volume.

## Resultado

Os bancos descriptografados estão disponíveis e são lidos somente em modo read-only pelo visualizador. A exportação HTML completa deixou de ser o fluxo principal por custo de tempo e volume.

## Dados relevantes

- `msgstore.db`: definido no arquivo local `config.toml`
- `wa.db`: definido no arquivo local `config.toml`
- mídias: definidas no arquivo local `config.toml`
- O hash de integridade deve ser registrado fora do repositório.
