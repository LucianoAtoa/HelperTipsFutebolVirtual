# Phase 8: Dashboard & Proxy - Research

**Researched:** 2026-04-04
**Domain:** Gunicorn WSGI, nginx reverse proxy, HTTP Basic Auth, systemd service
**Confidence:** HIGH

## Summary

Esta fase conecta dois subsistemas simples e bem documentados: gunicorn como WSGI server para o Dash e nginx como proxy HTTP com Basic Auth. Ambas as tecnologias têm padrões estabelecidos em Ubuntu e integração direta com systemd — o mesmo padrão já usado no listener (Phase 7).

O único ponto de atenção crítico: `dashboard.py` não expõe `server = app.server`. Esta variável é obrigatória para gunicorn importar o WSGI callable — sem ela, o gunicorn falha na inicialização com `Failed to find attribute 'server' in 'helpertips.dashboard'`. A task 08-01 deve corrigir isso antes de criar o unit file.

O restante é aplicação direta dos padrões já estabelecidos: script deploy numerado em `deploy/`, unit file com `StartLimitBurst` em `[Unit]`, logs em `/var/log/helpertips/`, logrotate compartilhado. nginx é instalado via `apt`, htpasswd via `apache2-utils`, e o security group já tem porta 80 aberta (documentado no README-deploy.md).

**Primary recommendation:** Adicionar `server = app.server` ao `dashboard.py`, criar `deploy/06-setup-dashboard.sh` (gunicorn systemd) e `deploy/07-setup-nginx.sh` (nginx + Basic Auth), seguindo fielmente o padrão de `deploy/05-setup-listener.sh`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Gunicorn — 2 workers, bind `127.0.0.1:8050`, timeout 120s. t3.micro tem 2 vCPUs mas apenas 1GB RAM (com swap) — 2 workers é o máximo seguro.
- **D-02:** Nginx — Listen porta 80, `proxy_pass http://127.0.0.1:8050`. Headers: `X-Forwarded-For`, `X-Real-IP`, `X-Forwarded-Proto`, `Host`. Sem HTTPS nesta fase. Server name `_` (catch-all).
- **D-03:** HTTP Basic Auth — `.htpasswd` gerado com `htpasswd -c` do apache2-utils. Um único usuário. Username/password em `.env` como `DASHBOARD_USER` e `DASHBOARD_PASSWORD`. Arquivo em `/etc/nginx/.htpasswd`, permissões 640 (nginx:root).
- **D-04:** Scripts `deploy/06-setup-dashboard.sh` (gunicorn + logrotate) e `deploy/07-setup-nginx.sh` (nginx + Basic Auth + .htpasswd). Seguem padrão scripts 01-05. Idempotentes.
- **D-05:** Gunicorn access log em `/var/log/helpertips/dashboard-access.log`, error log em `/var/log/helpertips/dashboard-error.log`. Logrotate compartilha config com listener.

### Claude's Discretion

- ExecStart exato do gunicorn no unit file (module path, app variable name)
- Configuração exata do nginx server block (buffer sizes, timeouts)
- Formato da mensagem de erro 401 (página padrão nginx ou customizada)
- Ordem de instalação de pacotes (nginx, apache2-utils)
- Se dashboard.py precisa de ajuste para funcionar com gunicorn (app variable export)

### Deferred Ideas (OUT OF SCOPE)

- HTTPS com Let's Encrypt (INFRA-01) — requer domínio próprio, fase futura v2
- Rate limiting no nginx — desnecessário para 1 usuário
- Página de erro 401 customizada — padrão nginx é suficiente
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEP-02 | Dashboard rodando via gunicorn como systemd service com `Restart=on-failure` | gunicorn 25.x como WSGI para Dash; `server = app.server` é o WSGI callable; unit file idêntico ao listener com `ExecStart=.venv/bin/gunicorn` |
| DEP-03 | Nginx configurado como reverse proxy para o dashboard (porta 80 → localhost:8050) | nginx `proxy_pass http://127.0.0.1:8050`; headers X-Forwarded-*; server_name _ catch-all |
| DEP-04 | HTTP Basic Auth no nginx protege dashboard de acesso público não autorizado | `auth_basic` + `auth_basic_user_file` no server block; htpasswd via apache2-utils; credenciais lidas do .env |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| gunicorn | 25.3.0 (latest) | WSGI HTTP server para Dash/Flask | Padrão industry para Python WSGI em produção; suporta múltiplos workers; integra com systemd via unit file |
| nginx | 1.24.x (Ubuntu 24.04 LTS) | Reverse proxy + HTTP Basic Auth | Padrão de mercado para proxy; `auth_basic` built-in sem módulo extra; alta performance estática |
| apache2-utils | 2.4.x (Ubuntu 24.04) | Gera arquivo .htpasswd | Pacote apt padrão Ubuntu; provê `htpasswd` CLI; independente do Apache (não instala httpd) |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| systemd | (Ubuntu 24.04 built-in) | Process supervisor para gunicorn | Sempre — mesma abordagem do helpertips-listener |
| logrotate | (Ubuntu built-in) | Rotaciona logs gunicorn | Sempre — logs em /var/log/helpertips/ crescem indefinidamente sem rotação |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| gunicorn | uvicorn | Dash usa Flask (WSGI), não ASGI — uvicorn seria inadequado |
| gunicorn | waitress | gunicorn mais battle-tested em Linux, melhor controle de workers |
| nginx Basic Auth | Dash auth libs (dash-auth) | nginx Basic Auth é mais simples, zero código Python, protege antes do app processar |

**Installation (no EC2 via apt + pip):**
```bash
# No EC2 como root:
apt install -y nginx apache2-utils

# No venv do helpertips (adicionar ao pyproject.toml [project.dependencies]):
/home/helpertips/.venv/bin/pip install "gunicorn>=25.0"
```

**Versão verificada:** gunicorn 25.3.0 (PyPI, 2026-04-04)

## Architecture Patterns

### Recommended Project Structure

```
deploy/
├── 01-provision-ec2.sh       # Bootstrap (existente)
├── 02-setup-postgres.sh      # PostgreSQL (existente)
├── 03-setup-budget-alert.sh  # Budget (existente)
├── 04-setup-backup.sh        # S3 backup (existente)
├── 05-setup-listener.sh      # Listener systemd (existente — REFERÊNCIA)
├── 06-setup-dashboard.sh     # Gunicorn systemd + logrotate (NOVO)
└── 07-setup-nginx.sh         # Nginx + Basic Auth + .htpasswd (NOVO)

helpertips/
└── dashboard.py              # Adicionar: server = app.server  (MODIFICAÇÃO NECESSÁRIA)
```

### Pattern 1: Dash com Gunicorn — WSGI Callable

**What:** Gunicorn não chama `app.run()` — ele importa diretamente o objeto WSGI Flask que o Dash encapsula.
**When to use:** Sempre que rodar Dash com gunicorn (ou qualquer WSGI server).
**Obrigatório:** `server = app.server` deve ser adicionado ao `dashboard.py` logo após a criação do `app`.

```python
# helpertips/dashboard.py — após app = dash.Dash(...)
server = app.server   # WSGI callable para gunicorn
```

**ExecStart correspondente no unit file:**
```
ExecStart=/home/helpertips/.venv/bin/gunicorn \
    --workers 2 \
    --bind 127.0.0.1:8050 \
    --timeout 120 \
    --access-logfile /var/log/helpertips/dashboard-access.log \
    --error-logfile /var/log/helpertips/dashboard-error.log \
    helpertips.dashboard:server
```

### Pattern 2: Systemd Unit File — Gunicorn

**What:** Unit file para gunicorn seguindo exatamente o padrão do `helpertips-listener.service`.
**Key differences do listener:** Sem `OnFailure=` (dashboard downtime é tolerável), sem `StandardError=journal` (logs vão para arquivo).

```ini
[Unit]
Description=HelperTips Dashboard
After=network.target postgresql.service
StartLimitBurst=5
StartLimitIntervalSec=300

[Service]
Type=simple
User=helpertips
Group=helpertips
WorkingDirectory=/home/helpertips
EnvironmentFile=/home/helpertips/.env
ExecStart=/home/helpertips/.venv/bin/gunicorn \
    --workers 2 \
    --bind 127.0.0.1:8050 \
    --timeout 120 \
    --access-logfile /var/log/helpertips/dashboard-access.log \
    --error-logfile /var/log/helpertips/dashboard-error.log \
    helpertips.dashboard:server
Restart=on-failure
RestartSec=60
StandardOutput=null
StandardError=null
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

**Nota:** `StartLimitBurst` e `StartLimitIntervalSec` DEVEM ficar em `[Unit]`, não em `[Service]` — pitfall documentado na Phase 7 STATE.md.

### Pattern 3: Nginx Server Block com Basic Auth

**What:** Servidor nginx que faz proxy para gunicorn e exige autenticação antes de qualquer conteúdo.
**Arquivo:** `/etc/nginx/sites-available/helpertips` + symlink em `sites-enabled/`.

```nginx
server {
    listen 80;
    server_name _;

    auth_basic "HelperTips";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass         http://127.0.0.1:8050;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }
}
```

**Desabilitar default site:**
```bash
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/helpertips /etc/nginx/sites-enabled/helpertips
nginx -t && systemctl reload nginx
```

### Pattern 4: Geração do .htpasswd via .env

**What:** Script lê `DASHBOARD_USER` e `DASHBOARD_PASSWORD` do `.env` e gera `/etc/nginx/.htpasswd`.

```bash
# Em deploy/07-setup-nginx.sh — dentro de set -euo pipefail
source /home/helpertips/.env

# Gera .htpasswd com o usuário definido no .env
htpasswd -cbB /etc/nginx/.htpasswd "$DASHBOARD_USER" "$DASHBOARD_PASSWORD"
chmod 640 /etc/nginx/.htpasswd
chown root:www-data /etc/nginx/.htpasswd
```

**Flag `-b`:** Aceita password no CLI (necessário para scripting não-interativo).
**Flag `-B`:** Usa bcrypt (mais seguro que MD5 padrão do `htpasswd`).
**Idempotência:** `-c` recria o arquivo — re-executar atualiza a senha sem erro.

**Nota sobre permissões:** O nginx no Ubuntu 24.04 roda como `www-data`. A decisão D-03 especifica `640 nginx:root` mas o grupo correto é `www-data` (nome do usuário nginx no Ubuntu). O owner pode ser root, grupo www-data, permissões 640.

### Pattern 5: Logrotate compartilhado

**What:** Adicionar entradas do dashboard ao `/etc/logrotate.d/helpertips` existente (ou script `06-setup-dashboard.sh` pode criar separado).

```
/var/log/helpertips/dashboard-access.log
/var/log/helpertips/dashboard-error.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    missingok
    create 0640 helpertips helpertips
    postrotate
        systemctl kill -s USR1 helpertips-dashboard.service 2>/dev/null || true
    endscript
}
```

**Nota:** gunicorn responde a `SIGUSR1` reabrindo arquivos de log após rotação.

### Anti-Patterns to Avoid

- **Bind em 0.0.0.0:8050 em produção:** Exposição direta sem proxy — o nginx deve ser o único ponto de entrada externo. Porta 8050 no Security Group deve ser removida após nginx ativo.
- **`server = app.server` ausente:** gunicorn falha silenciosamente em importar o módulo (`AttributeError: module 'helpertips.dashboard' has no attribute 'server'`).
- **`StartLimitBurst` em `[Service]`:** Ignorado silenciosamente pelo systemd — deve ser em `[Unit]` (pitfall Phase 7).
- **`-c` sem `-b` no htpasswd em script:** `htpasswd -c` sem `-b` pede senha interativamente — trava o script.
- **`app.run()` ainda chamado por gunicorn:** O bloco `if __name__ == "__main__"` com `app.run()` é ignorado quando gunicorn importa o módulo — não é problema, mas o desenvolvedor deve entender por que `DASH_DEBUG` não tem efeito via gunicorn sem configuração adicional.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Autenticação web | Middleware Python custom ou Dash callbacks de auth | nginx `auth_basic` | nginx autentica antes de proxying — zero código Python, menos superfície de ataque |
| Process supervisor | Script shell com `while true; do python ...; done` | systemd unit file | Restart automático, boot integration, journald logging, cgroups — tudo built-in |
| Log rotation | Script cron que move arquivos | logrotate | Handles compression, retention, signal-to-reopen — padrão Linux |
| Múltiplos workers Dash | Threading manual ou multiprocessing Python | gunicorn `--workers` | gunicorn gerencia fork, signal handling, graceful restart automaticamente |

**Key insight:** Toda a complexidade de produção (auth, process management, log rotation, multi-worker) tem solução Linux padrão — não há nada a implementar em Python.

## Common Pitfalls

### Pitfall 1: `server = app.server` ausente no dashboard.py

**What goes wrong:** `gunicorn helpertips.dashboard:server` falha com `Failed to find attribute 'server' in 'helpertips.dashboard'`. O serviço systemd entra em restart loop.
**Why it happens:** Dash encapsula uma app Flask internamente. `app.run()` funciona como script direto mas gunicorn precisa do objeto WSGI explicitamente.
**How to avoid:** Adicionar `server = app.server` ao `dashboard.py` imediatamente após `app = dash.Dash(...)`. Esta é a task pré-requisito da 08-01.
**Warning signs:** Logs mostram `AttributeError` em vez de "Listening at: http://127.0.0.1:8050".

### Pitfall 2: Usuário nginx no Ubuntu é `www-data`, não `nginx`

**What goes wrong:** `chown nginx:root /etc/nginx/.htpasswd` cria ownership inválido — nginx não consegue ler o arquivo, retorna 500 em vez de 401.
**Why it happens:** Ubuntu usa `www-data` como usuário do nginx (diferente de CentOS/RHEL que usa `nginx`).
**How to avoid:** `chown root:www-data /etc/nginx/.htpasswd && chmod 640 /etc/nginx/.htpasswd`.
**Warning signs:** `nginx -t` passa mas requests retornam 500; logs mostram `open() "/etc/nginx/.htpasswd" failed (13: Permission denied)`.

### Pitfall 3: Porta 8050 permanece aberta no Security Group

**What goes wrong:** Gunicorn fica acessível diretamente sem autenticação em `http://<IP>:8050`, bypassando nginx Basic Auth completamente.
**Why it happens:** O Security Group foi configurado com porta 8050 aberta temporariamente (Phase 6, documentado no README-deploy.md) — "aberta temporariamente até Phase 8 nginx".
**How to avoid:** Após nginx ativo e verificado, fechar porta 8050 no AWS Security Group. O script `07-setup-nginx.sh` deve documentar este passo manual no output final.
**Warning signs:** `curl http://<IP>:8050` retorna conteúdo Dash sem pedir autenticação.

### Pitfall 4: gunicorn não instalado no venv

**What goes wrong:** `ExecStart=/home/helpertips/.venv/bin/gunicorn` falha com "No such file or directory".
**Why it happens:** `gunicorn` não está em `pyproject.toml` nem instalado no venv atual.
**How to avoid:** Adicionar `"gunicorn>=25.0"` ao `pyproject.toml [project.dependencies]` e rodar `pip install -e .` ou `pip install gunicorn` no venv antes de criar o serviço.
**Warning signs:** `ls /home/helpertips/.venv/bin/gunicorn` não existe.

### Pitfall 5: Dash debug mode com múltiplos workers

**What goes wrong:** `debug=True` com `--workers 2` causa comportamento imprevisível (hot-reload em múltiplos processos, conflito de portas internas).
**Why it happens:** O hot-reloader do Dash/Flask tenta fazer bind em portas adicionais que colidem entre workers.
**How to avoid:** `DASH_DEBUG=false` já é o padrão (Phase 4 decision). gunicorn deve ignorar o env var `DASH_DEBUG` — o bloco `if __name__ == "__main__"` não é executado por gunicorn, então `app.run(debug=...)` nunca é chamado. Sem risco se `server = app.server` for o único callable exposto.

### Pitfall 6: `proxy_read_timeout` menor que timeout do gunicorn

**What goes wrong:** Nginx retorna 504 Gateway Timeout para callbacks Dash lentos, mesmo quando gunicorn ainda está processando.
**Why it happens:** `proxy_read_timeout` nginx padrão é 60s; gunicorn timeout é 120s (D-01).
**How to avoid:** Configurar `proxy_read_timeout 120s` no nginx server block — igual ao timeout do gunicorn.

## Code Examples

### Adição obrigatória ao dashboard.py

```python
# Source: Plotly Dash official deployment docs + gunicorn WSGI spec
# Adicionar após: app = dash.Dash(__name__, ...)

server = app.server   # WSGI callable — obrigatório para gunicorn
```

### Comando htpasswd scriptável (não-interativo)

```bash
# Source: apache2-utils htpasswd man page
# -c: cria/recria arquivo, -b: aceita password no CLI, -B: bcrypt
htpasswd -cbB /etc/nginx/.htpasswd "$DASHBOARD_USER" "$DASHBOARD_PASSWORD"
```

### Verificação do serviço gunicorn

```bash
# Testar que gunicorn responde localmente (antes de nginx)
curl -s http://127.0.0.1:8050 | head -5
# Esperado: HTML do Dash

# Testar via nginx com autenticação
curl -s -u "$DASHBOARD_USER:$DASHBOARD_PASSWORD" http://localhost/ | head -5
# Esperado: HTML do Dash

# Testar rejeição sem credenciais
curl -I http://localhost/
# Esperado: HTTP/1.1 401 Unauthorized
```

### Idempotência no script deploy

```bash
# Padrão já usado nos scripts 01-05: guard com || true para operações idempotentes
systemctl is-enabled helpertips-dashboard &>/dev/null || systemctl enable helpertips-dashboard
systemctl is-active helpertips-dashboard &>/dev/null && systemctl reload helpertips-dashboard || systemctl start helpertips-dashboard
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `app.run(host='0.0.0.0')` direto em produção | gunicorn WSGI + nginx proxy | Plotly Dash docs sempre recomendaram gunicorn | Multi-worker, sem debug exposure |
| Senha hardcoded no script | Lida do .env | Padrão do projeto desde Phase 4 | Sem secrets no git |
| Certificado autoassinado para HTTPS | HTTP em IP direto (v1) | Decisão D-02 desta fase | Adequado para uso pessoal sem domínio |

**Não deprecated nesta fase:** Tudo que está sendo instalado (nginx 1.24, gunicorn 25.x) é atual e estável.

## Open Questions

1. **Fechar porta 8050 no Security Group**
   - O que sabemos: A porta 8050 está aberta no Security Group (`helpertips-sg`) desde a Phase 6 — documentado como "aberta temporariamente até Phase 8 nginx" no STATE.md.
   - O que não está claro: Se o script `07-setup-nginx.sh` deve tentar fechar via AWS CLI (requer aws cli + permissões IAM) ou apenas documentar o passo manual.
   - Recomendação: Documentar como passo manual no output do script (padrão simples, sem dependência de AWS CLI), com instrução clara no SUCCESS block do script.

2. **`DASHBOARD_USER` / `DASHBOARD_PASSWORD` ausentes no `.env.example`**
   - O que sabemos: `.env.example` não tem essas variáveis ainda (verificado). D-03 diz para adicioná-las.
   - O que não está claro: A task 08-02 ou 08-01 deve atualizar o `.env.example`?
   - Recomendação: Task 08-02 (nginx) atualiza `.env.example` como parte do setup, já que as variáveis são usadas pelo `07-setup-nginx.sh`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| nginx | DEP-03, DEP-04 | Instalação via apt | apt install nginx | — |
| apache2-utils (htpasswd) | DEP-04 | Instalação via apt | apt install apache2-utils | — |
| gunicorn | DEP-02 | Instalação via pip no venv | pip install gunicorn>=25.0 | — |
| systemd | DEP-02 | Ubuntu 24.04 built-in | nativo | — |
| logrotate | DEP-02 (logs) | Ubuntu built-in | nativo | — |
| /var/log/helpertips/ | Logs | Criado na Phase 6 | — | Criar no script se ausente |
| .env com DASHBOARD_USER/PASSWORD | DEP-04 | Não existe ainda | — | Scripts falham sem essas vars — devem verificar |

**Missing dependencies with no fallback:**
- gunicorn não está em `pyproject.toml` nem instalado no venv — deve ser adicionado antes de criar o service (task 08-01)

**Missing dependencies with fallback:**
- nginx e apache2-utils: não instalados ainda, mas instalam trivialmente via `apt install -y nginx apache2-utils`

**Nota crítica — porta 8050 no Security Group:** Aberta na Phase 6 "temporariamente até Phase 8". Após nginx ativo, deve ser fechada manualmente no AWS Console. Não é uma dependência de software, mas é um passo de hardening que o planner deve incluir.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 (conforme requirements.txt) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEP-02 | gunicorn importa dashboard:server sem erro | smoke | `python -c "from helpertips.dashboard import server; print('OK')"` | ❌ Wave 0 (verificação inline no script) |
| DEP-02 | systemd service helpertips-dashboard ativo após enable | manual | `systemctl is-active helpertips-dashboard` | manual |
| DEP-03 | nginx proxy retorna 401 sem credenciais | smoke | `curl -s -o /dev/null -w "%{http_code}" http://localhost/` == 401 | manual |
| DEP-04 | nginx com credenciais retorna 200 | smoke | `curl -s -u user:pass -o /dev/null -w "%{http_code}" http://localhost/` == 200 | manual |

**Nota:** Os testes de DEP-03 e DEP-04 requerem EC2 com nginx rodando — são verificações manuais via SSH, não pytest automatizado. O critério de sucesso da fase ("acessar `http://<IP>` pede usuário e senha") é verificado interativamente pelo operador no browser.

### Sampling Rate

- **Por task:** Verificação inline no script de deploy (output `echo "OK"` após cada passo)
- **Por wave:** `systemctl status helpertips-dashboard` + `curl` tests na EC2
- **Phase gate:** Três critérios de sucesso da fase verificados antes de `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `server = app.server` adicionado ao `dashboard.py` — pré-requisito para DEP-02
- [ ] `gunicorn>=25.0` adicionado a `pyproject.toml [project.dependencies]` — pré-requisito para DEP-02
- [ ] `DASHBOARD_USER` e `DASHBOARD_PASSWORD` adicionados ao `.env.example` — pré-requisito para DEP-04

*(Estes não são gaps de test infrastructure — são code changes necessárias antes de poder criar os scripts de deploy)*

## Sources

### Primary (HIGH confidence)

- Plotly Dash deployment docs — `server = app.server` é o padrão oficial para gunicorn
- [nginx HTTP Basic Auth official docs](https://docs.nginx.com/nginx/admin-guide/security-controls/configuring-http-basic-authentication/) — configuração `auth_basic` e `auth_basic_user_file`
- [nginx ngx_http_auth_basic_module](https://nginx.org/en/docs/http/ngx_http_auth_basic_module.html) — módulo nativo do nginx
- gunicorn PyPI — versão 25.3.0 verificada em 2026-04-04
- `deploy/05-setup-listener.sh` — padrão de unit file do projeto (lido diretamente)
- `helpertips/dashboard.py` — código fonte (lido diretamente) — confirmado ausência de `server = app.server`
- `.planning/phases/08-dashboard-proxy/08-CONTEXT.md` — decisões locked (lido diretamente)

### Secondary (MEDIUM confidence)

- [Plotly Community Forum — Gunicorn + AWS EC2](https://community.plotly.com/t/deploying-dash-app-to-aws-server-using-gunicorn/81009) — padrão `helpertips.dashboard:server` confirmado por múltiplos usuários
- [Plotly Community Forum — Dash + nginx + gunicorn](https://community.plotly.com/t/dash-plotly-in-production-with-nginx-gunicorn/82863) — configuração nginx para Dash

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — gunicorn/nginx/apache2-utils são tecnologias maduras, versões verificadas no PyPI e apt Ubuntu
- Architecture: HIGH — padrões copiados diretamente dos scripts existentes (05-setup-listener.sh) e documentação oficial nginx
- Pitfalls: HIGH — pitfalls 1, 2, 4 verificados no código fonte real; pitfalls 3, 5, 6 verificados no STATE.md do projeto e docs oficiais

**Research date:** 2026-04-04
**Valid until:** 2026-07-04 (tecnologias estáveis; nginx e gunicorn não têm breaking changes frequentes)
