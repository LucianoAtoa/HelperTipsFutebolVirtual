# Feature Research — v1.1 Cloud Deploy

**Domain:** Cloud deployment + security hardening + GitHub publication for a personal Python tool (Telegram listener + Plotly Dash dashboard)
**Researched:** 2026-04-03
**Confidence:** HIGH for security (official docs + well-established patterns), HIGH for deployment patterns (AWS EC2 + systemd widely documented), MEDIUM for "minimal personal tool" tradeoffs (community consensus, not one official source)

---

## Context: What is Being Deployed

Two long-running Python processes on a single server:

1. **listener.py** — Telethon asyncio loop, never terminates, reconnects automatically, writes to PostgreSQL
2. **dashboard.py** — Plotly Dash web server (gunicorn in production), serves HTTP on port 8050, reads-only from PostgreSQL

Both need to be:
- Running 24/7 on an AWS EC2 instance
- Managed by the OS (auto-start on boot, auto-restart on crash)
- Protected against secrets leaking to GitHub
- Secured before exposing the dashboard to the internet

---

## Table Stakes

Features the deployment MUST have. Missing any of these = broken or insecure in production.

| Feature | Why Required | Complexity | Notes |
|---------|--------------|------------|-------|
| `debug=False` in production dashboard | `debug=True` exposes a Python REPL accessible via browser — critical security hole. Currently `dashboard.py` runs `app.run(debug=True, host="0.0.0.0", port=8050)` | LOW | Toggle via `DEBUG` env var; never hardcode True in production |
| gunicorn as WSGI server | Dash's built-in Flask dev server is single-threaded, not production-grade; gunicorn handles concurrent requests, worker management, and graceful restarts | LOW | `gunicorn helpertips.dashboard:server -w 2 -b 0.0.0.0:8050`; expose `server = app.server` in dashboard.py |
| systemd unit for listener | Without systemd, the Telethon listener dies on terminal close or crash and never restarts; signals are lost permanently | LOW | Two unit files: `helpertips-listener.service` and `helpertips-dashboard.service`, both `Restart=always` |
| systemd unit for dashboard | Same rationale as listener; gunicorn must restart on crash | LOW | `After=helpertips-listener.service` ordering is optional but clean |
| EC2 Security Group: restrict Dash port | Port 8050 open to `0.0.0.0/0` means anyone on the internet can access the dashboard; restrict to user's home IP CIDR | LOW | AWS Console > Security Group > Custom TCP 8050 > My IP. Update when IP changes. |
| EC2 Security Group: SSH only from known IPs | Default `0.0.0.0/0` on port 22 is a brute-force magnet | LOW | Restrict inbound SSH (22) to user's IP /32 |
| `.session` files in .gitignore | Telethon `.session` file contains complete Telegram account auth state — leaking it grants full account access to the attacker. Already in .gitignore but must be verified before first public push | LOW | Verify `.gitignore` contains `*.session` and `*.session-journal` before `git push` |
| `.env` in .gitignore | Telegram API_ID, API_HASH, DB_PASSWORD, etc. Already in .gitignore; must be confirmed clean before public push | LOW | Already present in current .gitignore |
| `.env.example` committed | Documents all required env vars without values; onboarding without leaking credentials. Already exists. | LOW | Verify it has no real values; keep in sync when new vars are added |
| Audit git history for secrets before first public push | Even if current tree is clean, secrets may exist in old commits; scan history before making repo public | MEDIUM | Use `git log -p | grep -E "API_ID|API_HASH|password"` or `gitleaks detect --source . --log-opts="HEAD"` |
| RDS or local PostgreSQL reachable from EC2 | The app reads/writes PostgreSQL; must be accessible from the EC2 instance. Simplest: run PostgreSQL on the same EC2 instance (t3.small has enough RAM) | MEDIUM | Option A: PostgreSQL on same EC2 (simple, lowest cost). Option B: RDS t3.micro (managed, +$15-25/mo). For personal tool, same-instance is fine. |
| Environment variables injected at runtime on EC2 | `.env` must NOT be committed or SCP'd to server with credentials embedded; use `systemd` `EnvironmentFile=` pointing to a file created manually on the server | LOW | Create `/etc/helpertips/secrets.env` on EC2 manually; `EnvironmentFile=/etc/helpertips/secrets.env` in unit file |

---

## Differentiators

Features that improve operational quality and maintainability beyond "it just runs".

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| nginx reverse proxy in front of Dash | Terminates port 80/443, handles static file caching, adds HTTP Basic Auth layer, enables HTTPS later via Certbot — professional production pattern | MEDIUM | `proxy_pass http://127.0.0.1:8050;` — Dash needs `requests_pathname_prefix` or `routes_pathname_prefix` if serving from a subpath |
| HTTP Basic Auth via nginx htpasswd | Single-user password gate on the dashboard — protects against anyone stumbling onto the IP | LOW | `htpasswd -c /etc/nginx/.htpasswd user` — weak but sufficient for a personal tool at a known IP |
| GitHub Actions CI: run pytest on push | Catches regressions before they reach production; 132 tests already exist — just wire them up | MEDIUM | Use `services: postgres:` container in workflow; inject DB credentials from GitHub Secrets |
| Dependabot alerts enabled | GitHub automatically flags CVEs in requirements.txt dependencies | LOW | Enable via Settings > Security & Analysis > Dependabot alerts — one click |
| Structured README for GitHub publication | Documents what the project is, how to configure, how to run — makes the repo usable by someone else (or future self) | LOW | Sections: Overview, Architecture, Setup, Configuration, Running, Tests |
| `.env.example` with all vars documented | Already exists; ensure it has descriptions of what each var is | LOW | Add inline comments to `.env.example` |

---

## Anti-Features

Commonly suggested, but wrong for this context.

| Anti-Feature | Why Requested | Why Wrong for This Tool | Alternative |
|--------------|---------------|-------------------------|-------------|
| Full OAuth / login system on dashboard | "Production apps need auth" | This is a personal tool for one user; OAuth adds complexity (client secrets, callback URLs, token refresh) that far exceeds value of a password prompt | nginx HTTP Basic Auth is sufficient — one htpasswd file, done |
| Docker / docker-compose on EC2 | Perceived as "industry standard" | Adds a layer of abstraction for no benefit on a single-service personal tool; systemd does the same job natively with less overhead and simpler debugging | Two systemd unit files — OS manages processes natively |
| AWS Elastic Beanstalk or ECS | "Managed deployment platforms" | Massive overkill — these platforms add billing complexity, configuration overhead, and vendor abstraction for what is essentially `python listener.py` | Bare EC2 + systemd is simpler, cheaper, and fully under user control |
| Kubernetes | "Container orchestration" | A personal tool with 2 processes has zero need for orchestration, scheduling, or service mesh. K8s complexity would dwarf the project itself | Two systemd services on one EC2 instance |
| AWS Secrets Manager / HashiCorp Vault | "Secrets management platforms" | Secure but introduces IAM policy complexity and costs for what is a single-developer tool | `EnvironmentFile=` in systemd pointing to a file with restricted Unix permissions (`chmod 600`) |
| HTTPS / Let's Encrypt Certbot | "Every public web app needs HTTPS" | This dashboard is only accessible from the user's home IP (Security Group restriction). HTTPS is needed if you expose it publicly, which is explicitly out of scope. | If the IP restriction is removed, add Certbot then — but not now. |
| Multi-worker gunicorn (4+ workers) | "Production best practices" | Two gunicorn workers is plenty for one user — more workers means more RAM usage on a t3.small (2 GiB) | `--workers 2` is the right default; listener + DB also compete for RAM |
| Automated deploy pipeline (GitHub Actions → EC2) | "CI/CD is table stakes" | The deploy frequency is extremely low (days/weeks between deploys); an automated pipeline adds GitHub OIDC or SSH key secrets complexity for near-zero benefit | Manual `git pull && systemctl restart` on EC2 is fine for this cadence |
| gitleaks as pre-commit hook | "Prevent secrets in commits" | The project already has a clean .gitignore + .env.example pattern; pre-commit hooks fail silently on bypasses anyway. The real risk is the initial git history audit before going public. | One-time `git log -p` grep before making the repo public; then trust .gitignore |
| CloudWatch / DataDog monitoring | "Production needs observability" | A personal betting analysis tool that breaks is noticed in seconds by the user; structured monitoring is overkill | `systemctl status helpertips-listener` and `journalctl -u helpertips-listener -f` cover 100% of the need |

---

## Feature Dependencies

```
Security Review (secrets audit)
  └─ must complete before → GitHub publication (repo goes public)
       └─ enables → README + badges visible to public

systemd unit files
  └─ require → EC2 instance provisioned (Ubuntu 22.04+)
       └─ require → Python 3.12 + dependencies installed on EC2

gunicorn installed (add to requirements.txt)
  └─ enables → systemd dashboard unit (ExecStart uses gunicorn)

EC2 Security Group (IP restriction)
  └─ must configure before → starting gunicorn / exposing port 8050

PostgreSQL on EC2 (or RDS)
  └─ must be reachable before → listener and dashboard can start

EnvironmentFile on EC2 (manual secrets)
  └─ must exist before → systemd units can start (units will fail without it)

nginx (optional, Differentiator tier)
  └─ requires → gunicorn running on 127.0.0.1:8050
       └─ enables → HTTP Basic Auth password gate
       └─ enables → HTTPS via Certbot (future, not now)

GitHub Actions CI (optional, Differentiator tier)
  └─ requires → repo published on GitHub
       └─ requires → PostgreSQL service container in workflow
       └─ requires → GitHub Secrets: DB_USER, DB_PASSWORD, DB_NAME
```

---

## MVP Definition

### Ship with v1.1 (Table Stakes — required for a secure public deployment)

- [ ] `debug=False` in production — set via `DEBUG` env var, default to False
- [ ] `server = app.server` exposed in `dashboard.py` — enables gunicorn
- [ ] `gunicorn` added to `requirements.txt`
- [ ] `helpertips-listener.service` systemd unit — `Restart=always`, `EnvironmentFile=`
- [ ] `helpertips-dashboard.service` systemd unit — gunicorn invocation, `Restart=always`
- [ ] EC2 Security Group: port 8050 and 22 restricted to user's IP
- [ ] One-time git history audit for secrets before `git push --public`
- [ ] README.md: overview, architecture diagram (text), setup, config, run, tests
- [ ] Verify `.gitignore` covers `*.session`, `.env`, `__pycache__`, `.egg-info`
- [ ] PostgreSQL running and accessible on EC2 (same instance, port 5432 localhost-only)
- [ ] `EnvironmentFile` created manually on EC2 with real credentials (chmod 600)

### Add after deployment is stable (Differentiator tier)

- [ ] nginx reverse proxy + HTTP Basic Auth — adds a password gate for the dashboard
- [ ] GitHub Actions CI — pytest on push using postgres service container
- [ ] Dependabot alerts — one-click in GitHub Settings

### Defer indefinitely (Not in scope per PROJECT.md)

- [ ] HTTPS / Certbot — only relevant if dashboard moves to a public domain
- [ ] OAuth / proper auth system — personal tool, IP restriction + basic auth is sufficient
- [ ] Automated deploy pipeline — deploy cadence too low to justify
- [ ] AWS RDS — same-instance PostgreSQL is simpler and ~$15-25/mo cheaper

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| debug=False in production | HIGH (security) | LOW | P1 |
| gunicorn as WSGI server | HIGH (stability) | LOW | P1 |
| systemd unit files (both processes) | HIGH (24/7 uptime) | LOW | P1 |
| EC2 Security Group IP restriction | HIGH (security) | LOW | P1 |
| Git history secrets audit | HIGH (security, one-time) | LOW | P1 |
| README for GitHub publication | HIGH (usability) | LOW | P1 |
| PostgreSQL on EC2 | HIGH (data layer) | MEDIUM | P1 |
| EnvironmentFile on EC2 | HIGH (secrets management) | LOW | P1 |
| nginx + HTTP Basic Auth | MEDIUM (additional security layer) | MEDIUM | P2 |
| GitHub Actions CI | MEDIUM (regression safety) | MEDIUM | P2 |
| Dependabot alerts | LOW (passive, automatic) | LOW | P2 |
| HTTPS / Certbot | LOW (not publicly exposed) | MEDIUM | P3 |
| Automated deploy pipeline | LOW (low deploy frequency) | HIGH | P3 |

**Priority key:**
- P1: Must have for v1.1 — without this, deployment is insecure or broken
- P2: Should have — improves operational quality significantly
- P3: Nice to have — defer, conditions for inclusion not yet met

---

## Phase-Specific Warnings (feeds PITFALLS.md)

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| First `git push` to public repo | `.session` file or `.env` in git history from early commits | Audit with `git log --all -- "*.session" ".env"` before push; use BFG if found |
| EC2 instance sizing | t3.micro (1 GiB RAM) may OOM with listener + dashboard + PostgreSQL all running | Use t3.small (2 GiB) — $15/mo vs $7/mo; the headroom is worth the cost |
| systemd EnvironmentFile path | Unit file silently ignores missing EnvironmentFile in some systemd versions | Use `EnvironmentFile=-/etc/helpertips/secrets.env` (dash prefix = optional); check `systemctl status` after start |
| gunicorn + Dash callback state | Multiple gunicorn workers do NOT share in-memory state; if dashboard uses `dcc.Store` with server-side data, workers produce inconsistent results | Set `--workers 2` (not 4+); confirm dashboard uses PostgreSQL (not in-memory) as truth source |
| Telethon session on server vs local | If the same session file is used on two machines simultaneously, Telegram may invalidate the session | Generate a NEW session on the EC2 instance via first-run auth; never copy the local `.session` to the server |
| debug=True with host="0.0.0.0" | Current code has this — exposes Python debugger to the network | Fix before any EC2 deployment, not just before adding nginx |

---

## Sources

- Plotly Dash official deployment docs: https://dash.plotly.com/deployment — HIGH confidence
- Dash + gunicorn community pattern: https://community.plotly.com/t/deploying-dash-app-to-aws-server-using-gunicorn/81009 — MEDIUM confidence
- AWS EC2 t3.micro vs t3.small pricing: https://instances.vantage.sh/aws/ec2/t3.micro — HIGH confidence (AWS-sourced data)
- AWS Security Groups — restrict by IP: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html — HIGH confidence (official docs)
- Telethon session file security risk: https://github.com/LonamiWebs/Telethon/issues/3753 — HIGH confidence (official Telethon issue tracker)
- Telethon .gitignore recommendation: https://docs.telethon.dev/en/stable/quick-references/faq.html — HIGH confidence (official docs)
- nginx HTTP Basic Auth setup: https://docs.nginx.com/nginx/admin-guide/security-controls/configuring-http-basic-authentication/ — HIGH confidence (official nginx docs)
- GitHub secrets management best practices: https://docs.github.com/code-security/secret-scanning/about-secret-scanning — HIGH confidence (official GitHub docs)
- detect-secrets (Yelp) for git history scanning: https://github.com/Yelp/detect-secrets — MEDIUM confidence (widely used OSS)
- systemd service management for multiple Python processes: https://saturncloud.io/blog/getting-started-with-ec2-1604-systemd-supervisord-and-python-a-comprehensive-guide-for-data-scientists/ — MEDIUM confidence
- GitHub Actions + PostgreSQL service container: https://til.simonwillison.net/github-actions/postgresq-service-container — MEDIUM confidence (well-regarded source)

---

*Feature research for: v1.1 Cloud Deploy — deployment, security, GitHub publication*
*Researched: 2026-04-03*
