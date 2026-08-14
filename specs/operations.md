# Operação e manutenção

## Pasta principal

`web-apps/whatsapp-viewer`

## Comandos

```powershell
.\setup-local.ps1
.\setup-https.ps1
.\build-index.ps1
.\start-local.ps1
.\start-lan-https.ps1
```

## Atualização do backup

Depois de substituir os arquivos no diretório externo, execute `build-index.ps1`. A indexação é incremental. Use `--reset` somente para recriar o índice.

## Renovação HTTPS

Execute novamente `setup-https.ps1` se o hostname ou IP doméstico mudar. Reinstale a nova CA no Android somente se a autoridade local também tiver mudado.

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Diagnóstico

- Verifique se a porta 8765 está livre antes de iniciar.
- Uma mídia pode constar no banco e não existir na pasta; isso significa backup incompleto, não erro de codec.
- Use `Ctrl+F5` após alterações em JavaScript ou CSS.
