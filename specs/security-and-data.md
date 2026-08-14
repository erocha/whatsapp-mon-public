# Segurança e dados

## Autenticação

- Senha com no mínimo 10 caracteres no primeiro acesso.
- Hash Argon2 armazenado apenas em `viewer-data.db`.
- Sessão com duração de 12 horas.
- Cookie `Secure`, `HttpOnly` e `SameSite=Strict`.
- CSRF obrigatório em operações de escrita.

## HTTPS e rede

- Certificados gerados por mkcert e ignorados pelo Git.
- Certificado inclui localhost, loopback, hostname e IPs locais presentes na geração.
- A CA deve ser instalada manualmente no Android.
- Regra do Firewall do Windows: porta TCP 8765, perfil Privado, origem `LocalSubnet`.

## Precedência de nomes

1. Apelido manual.
2. Contato importado de VCF.
3. Nome disponível no banco.
4. Número ou JID.

## Mídias

- Endpoint exige sessão autenticada.
- Caminhos são normalizados e verificados contra a raiz `Media`.
- Registros sem arquivo físico não devem exibir player funcional.
- URLs nas mensagens aceitam somente esquemas HTTP/HTTPS e usam `noopener noreferrer`.
- Perfil, foto histórica e grupos em comum exigem a mesma sessão autenticada da aplicação.
