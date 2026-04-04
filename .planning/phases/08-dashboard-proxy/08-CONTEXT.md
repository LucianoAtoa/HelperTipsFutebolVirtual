# Phase 8: Dashboard & Proxy - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning
**Source:** Auto-mode (recommended defaults selected)

<domain>
## Phase Boundary

Dashboard Dash acessível publicamente via HTTP com proteção por senha (HTTP Basic Auth), servido por gunicorn como WSGI server e nginx como reverse proxy. Ambos como systemd services sobrevivendo a reboots.

</domain>

<decisions>
## Implementation Decisions

### Gunicorn Config
- **D-01:** 2 workers, bind em `127.0.0.1:8050`, timeout 120s. t3.micro tem 2 vCPUs mas apenas 1GB RAM (com swap) — 2 workers é o máximo seguro. Bind em localhost porque nginx faz o proxy. Timeout alto porque callbacks Dash podem ser lentos com queries complexas.

### Nginx Reverse Proxy
- **D-02:** Listen porta 80, `proxy_pass http://127.0.0.1:8050`. Headers padrão: `X-Forwarded-For`, `X-Real-IP`, `X-Forwarded-Proto`, `Host`. Sem HTTPS nesta fase — INFRA-01 (Let's Encrypt) é v2. Server name com `_` (catch-all) já que não tem domínio.

### HTTP Basic Auth
- **D-03:** `.htpasswd` gerado com `htpasswd -c` do apache2-utils. Um único usuário. Username e password definidos como variáveis no `.env` (`DASHBOARD_USER`, `DASHBOARD_PASSWORD`) e o script de setup lê de lá para gerar o `.htpasswd`. Arquivo em `/etc/nginx/.htpasswd` com permissões 640 (nginx:root).

### Deploy Scripts
- **D-04:** `deploy/06-setup-dashboard.sh` cria unit file gunicorn + logrotate. `deploy/07-setup-nginx.sh` instala nginx, configura server block com Basic Auth, gera `.htpasswd`. Segue padrão dos scripts 01-05 existentes. Scripts idempotentes — podem ser re-executados.

### Logging Dashboard
- **D-05:** Gunicorn access log em `/var/log/helpertips/dashboard-access.log`, error log em `/var/log/helpertips/dashboard-error.log`. Logrotate compartilha config com listener (mesmo diretório). Dash app logging segue mesmo padrão de TTY detection do listener (Phase 7 D-02).

### Claude's Discretion
- ExecStart exato do gunicorn no unit file (module path, app variable name)
- Configuração exata do nginx server block (buffer sizes, timeouts)
- Formato da mensagem de erro 401 (página padrão nginx ou customizada)
- Ordem de instalação de pacotes (nginx, apache2-utils)
- Se dashboard.py precisa de ajuste para funcionar com gunicorn (app variable export)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Código do dashboard
- `helpertips/dashboard.py` — Dashboard Dash, bind 0.0.0.0:8050, debug via DASH_DEBUG, importa `get_connection` e queries
- `helpertips/queries.py` — Queries SQL usadas pelo dashboard
- `helpertips/db.py` — Conexão DB via os.environ

### Infraestrutura existente (Phase 6-7)
- `deploy/01-provision-ec2.sh` — Bootstrap EC2 (user helpertips, swap, pacotes)
- `deploy/05-setup-listener.sh` — Referência para padrão de systemd unit file + logrotate
- `.env.example` — Template com variáveis (precisa adicionar DASHBOARD_USER, DASHBOARD_PASSWORD)

### Requirements
- `.planning/REQUIREMENTS.md` — DEP-02 (gunicorn systemd), DEP-03 (nginx reverse proxy), DEP-04 (HTTP Basic Auth)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `deploy/05-setup-listener.sh` — Padrão completo de systemd unit file + logrotate, pode ser replicado para dashboard
- Dashboard já roda com `app.run_server()` — gunicorn precisa da variável `server` ou `app.server` exposta
- `helpertips/listener.py` `configure_logging()` — Padrão de logging TTY detection reutilizável

### Established Patterns
- Deploy scripts numerados em `deploy/` (01-05), idempotentes
- Systemd services com Restart=on-failure, StartLimitBurst em [Unit] (não em [Service])
- Logs em `/var/log/helpertips/` com logrotate
- User dedicado `helpertips` roda os serviços

### Integration Points
- Dashboard precisa da variável `app.server` exposta para gunicorn importar
- Nginx proxy_pass para 127.0.0.1:8050 (mesmo bind do dashboard)
- .env no servidor precisa de DASHBOARD_USER e DASHBOARD_PASSWORD adicionais

</code_context>

<specifics>
## Specific Ideas

No specific requirements — auto-mode selected recommended defaults for all areas.

</specifics>

<deferred>
## Deferred Ideas

- HTTPS com Let's Encrypt (INFRA-01) — requer domínio próprio, fase futura v2
- Rate limiting no nginx — desnecessário para 1 usuário
- Página de erro 401 customizada — padrão nginx é suficiente

</deferred>

---

*Phase: 08-dashboard-proxy*
*Context gathered: 2026-04-04 via auto-mode*
