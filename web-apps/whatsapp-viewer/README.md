# Arquivo WhatsApp local

Visualizador local e responsivo para os bancos Android `msgstore.db` e `wa.db`.
Os bancos são abertos em modo somente leitura; configurações e o índice de busca
ficam em `data/viewer-data.db`.

## Instalação

Abra o PowerShell nesta pasta:

```powershell
.\setup-local.ps1
.\setup-https.ps1
.\build-index.ps1
```

Na primeira execução, `setup-local.ps1` cria `config.toml` a partir de
`config.toml.example`. Ajuste nesse arquivo local os caminhos do seu backup.

A indexação inicial percorre as mensagens de texto e pode demorar. Ela é
incremental: nas execuções seguintes, somente mensagens novas são adicionadas.
Use `.\build-index.ps1 --reset` apenas para recriar todo o índice.

## Iniciar

Somente neste computador:

```powershell
.\start-local.ps1
```

Abra `https://localhost:8765/`. No primeiro acesso, crie uma senha com no mínimo
10 caracteres.

Na rede local, abra o PowerShell como Administrador e execute:

```powershell
.\start-lan-https.ps1
```

O script mostra o endereço IP que deve ser aberto no celular. A porta é liberada
somente no perfil de rede **Privado** do Firewall do Windows.

## Confiar no certificado no Android

1. Execute `.\setup-https.ps1`.
2. Copie `certs/rootCA-for-android.pem` para o celular por um meio privado.
3. No Android/Samsung: **Configurações → Segurança e privacidade → Mais
   configurações de segurança → Instalar do armazenamento → Certificado CA**.
4. Selecione o arquivo e confirme o aviso do Android.
5. Abra no celular o endereço HTTPS/IP mostrado por `start-lan-https.ps1`.

Remova essa CA do celular se deixar de usar o visualizador. Se o IP do computador
mudar, execute `setup-https.ps1` novamente e use o novo certificado.

## Contatos e pesquisa

- Importe um `.vcf` pelo botão de configurações.
- Defina apelidos no painel de detalhes de uma conversa.
- Precedência: apelido → VCF → banco → telefone/JID.
- Pressione `/` para pesquisar mensagens. A pesquisa requer `build-index.ps1`.

## Privacidade

- Nenhum dado é enviado à internet.
- A chave de 64 caracteres não é usada pela aplicação.
- Mídias exigem sessão autenticada e caminhos externos são bloqueados.
- `certs/`, `data/` e `.venv/` não entram no Git.
