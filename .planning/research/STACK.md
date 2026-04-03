# Technology Stack

**Project:** HelperTips — Futebol Virtual (Telegram Signal Capture + Betting Analytics Dashboard)
**Researched:** 2026-04-02 (application stack) / 2026-04-03 (cloud deployment stack)
**Overall confidence:** HIGH (all primary choices verified against official sources/PyPI)

---

## Recommended Stack

### Telegram Listener

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Telethon | **1.42.0** (current, not 1.37) | User-client MTProto Telegram listener | Only Python library that connects as a user account (not bot), enabling listening to groups without admin rights. `events.MessageEdited` handles the group's edit-based result pattern natively. Async/await first-class. |

**Version note (HIGH confidence):** The project's constraints document pins Telethon 1.37, but the current release is 1.42.0 (released Nov 5, 2025). No breaking changes between 1.37 and 1.42 for the use cases here. Pin to `~=1.42` to stay on latest stable without auto-upgrading to a hypothetical v2 alpha.

**Why not Pyrogram:** Also a user-client library, but Telethon has better documentation, a larger community, and explicit `events.MessageEdited` support. Pyrogram is a valid alternative but offers no advantage for this use case.

**Why not Bot API:** Bots cannot join private groups without being invited as admins. The group is VIP/private. Telethon's user-client mode is the only viable path.

---

### Database Driver

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| psycopg2-binary | **2.9.x** (latest stable) | PostgreSQL sync driver | Simple, battle-tested, no build dependencies. Sync is fine here — the listener is async (Telethon) but writes are infrequent (one per signal) and don't need async I/O. Dashboard reads are also low-frequency. |
| PostgreSQL | **16** | Relational storage | JSONB support for raw message metadata, array types, window functions for ROI simulation, partitioning if historical data grows. AWS RDS-ready. |

**Why psycopg2-binary and not psycopg2 (compiled):** psycopg2-binary is explicitly fine for single-user personal tools and containerized deploys. The official warning about binary packages applies to published libraries and high-concurrency production services — not this use case. Using the binary eliminates the need for `libpq-dev` on the host and keeps deployment trivial.

**Why not asyncpg:** asyncpg is 5x faster but requires async all the way down, which forces SQLAlchemy 2.0 async session management or raw asyncpg connection pools. That complexity is unjustified for a listener that writes a few rows per hour. Keep it simple.

**Why not psycopg3 (psycopg):** psycopg3 is the future but psycopg2 is still the dominant deployed version and has zero risk of API surprises. Migrate to psycopg3 in a future phase if async writes become necessary.

**Why not SQLite:** Project constraints already ruled this out correctly — PostgreSQL is required for AWS RDS migration readiness and concurrent access from listener + dashboard.

**Why not SQLAlchemy ORM:** This project's schema is simple (signals table, maybe a results table). Raw SQL via psycopg2 is less abstraction, easier to debug, and faster to write for a personal tool. SQLAlchemy adds value when schema complexity or multiple ORM models justify the overhead. Not here.

---

### Web Dashboard

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Plotly Dash | **4.1.0** (current) | Interactive analytics dashboard | Pure-Python dashboards with no JavaScript required. Built-in Plotly charts (bar, line, scatter, heatmap) cover all analytics views needed. Callbacks handle interactive filters reactively. Runs as a standalone web server. |
| dash-bootstrap-components | **2.0.x** (current, Bootstrap 5) | Responsive layout and UI components | Cards, grids, navbars, modals without writing CSS. Bootstrap 5 responsive grid means the dashboard works on mobile and desktop. Standard pairing with Dash in the community. |
| plotly | **bundled with Dash 4.1.0** | Chart rendering | Installed automatically as Dash dependency. No separate install needed. |

**Why not Streamlit:** Streamlit is faster for prototyping ML demos, but its execution model (full script re-run on every interaction) creates awkward state management for multi-filter analytics dashboards. Dash's callback graph is a better mental model for "filter this chart independently from that chart." Streamlit also has weaker support for complex cross-filter interactions.

**Why not FastAPI + custom frontend:** FastAPI + React/Vue would give maximum control but triples the implementation scope — frontend build tooling, JavaScript state management, API serialization layer. A personal analytics tool doesn't need this. Dash serves HTML directly.

**Why not FastAPI + Dash mounted together:** The WSGIMiddleware approach to embed Dash inside FastAPI adds complexity with no benefit here. Dash runs its own server. There are no REST endpoints needed separately — the dashboard IS the product.

**Why not Grafana:** Grafana with PostgreSQL plugin could work for basic charts, but custom ROI simulation logic and dimension-crossing filters require Python code. Grafana is a monitoring tool, not an analytics computation tool.

---

### Configuration & Secrets

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| python-dotenv | **1.x** (current stable) | Load `.env` file | Zero-dependency, industry standard for dev environments. Keeps API credentials out of source code. |

**Why not pydantic-settings:** pydantic-settings is the better choice when building a FastAPI service with type-validated config. For a personal script + Dash app, the added dependency and class definition boilerplate is overkill. python-dotenv + `os.environ.get()` is sufficient. If this grows into a deployed service, migrate to pydantic-settings then.

---

### Python Runtime

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python | **3.12+** | Runtime | Telethon requires 3.8+; psycopg2-binary supports 3.12; Dash 4.1.0 requires 3.8+. Python 3.12 gives better performance (interpreter speedups), improved error messages, and is the current LTS-equivalent stable release. |

---

## Cloud Deployment Stack (v1.1 — Milestone: AWS + GitHub)

> This section covers additions needed for cloud deployment. The application stack above is unchanged.

### AWS Infrastructure

| Service | Tier/Config | Monthly Cost (us-east-1) | Why |
|---------|------------|--------------------------|-----|
| EC2 t4g.micro | On-Demand, arm64 | ~$6.13/mês | Cheapest always-on compute outside free tier. 2 vCPUs burstable, 1 GiB RAM — sufficient for listener + dashboard + PostgreSQL running as Docker containers. $0.0084/hora. |
| EBS gp3 | 20 GB | ~$1.60/mês | Root volume for OS + Docker images + PostgreSQL data. gp3 is $0.08/GB-mês, 20 GB cobre tudo com margem. 3,000 IOPS e 125 MB/s incluídos sem custo adicional. |
| Elastic IP | 1 IP estático | Grátis quando associado | IP fixo para apontar DNS e configurar regras de firewall. Cobrado apenas se a instância estiver parada (~$0.005/hora). |
| **Total estimado** | | **~$7.73/mês** | Listener + dashboard + PostgreSQL em um único host. Sem RDS, sem ECS, sem ALB. |

**Por que não RDS PostgreSQL:** RDS db.t4g.micro custa ~$21.90/mês — 3x mais caro que rodar PostgreSQL no próprio EC2. Para uso pessoal de baixo tráfego, o overhead operacional do PostgreSQL auto-hospedado em Docker é mínimo e o saving mensal é ~$14. RDS faz sentido quando você precisa de backups automatizados gerenciados, réplicas de leitura, ou failover. Nenhum desses é necessário aqui.

**Por que não ECS/Fargate:** ECS Fargate para dois containers custaria ~$20-30/mês, eliminando o benefício de custo. EC2 com Docker Compose é suficiente e mais simples de operar.

**Por que não App Runner/Lambda:** Telethon é um processo long-running que mantém conexão MTProto persistente. Lambda/serverless não suporta esse padrão. App Runner também não.

---

### Containerização

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Docker | **27.x** (current stable) | Container runtime | Encapsula Python 3.12, dependências e configuração em imagem reproduzível. Elimina "funciona na minha máquina". Disponível via Amazon Linux 2023 package manager. |
| Docker Compose | **2.x** (plugin embutido) | Orquestração multi-serviço | Define listener + dashboard + PostgreSQL como serviços declarativos com restart policies, volumes e variáveis de ambiente. `docker compose up -d` é o único comando de deploy. |

**Arquitetura Docker Compose proposta:**
```yaml
services:
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    volumes:
      - pg_data:/var/lib/postgresql/data
    env_file: .env

  listener:
    build: .
    command: python listener.py
    restart: unless-stopped
    depends_on: [postgres]
    volumes:
      - telethon_session:/app/sessions
    env_file: .env

  dashboard:
    build: .
    command: python dashboard.py
    restart: unless-stopped
    depends_on: [postgres]
    ports:
      - "127.0.0.1:8050:8050"  # só localhost; Caddy faz o proxy
    env_file: .env

  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data

volumes:
  pg_data:
  telethon_session:
  caddy_data:
```

**Por que usar a mesma imagem para listener e dashboard:** Ambos usam o mesmo `requirements.txt` e código base. Um único `Dockerfile` com `CMD` diferente por serviço evita duplicação de build. Imagem final ~300 MB (python:3.12-slim).

**Sessão Telethon:** Montar volume nomeado `telethon_session` em `/app/sessions`. Na primeira execução, autenticar interativamente (`docker compose run --rm listener python listener.py`) e o arquivo `.session` persiste no volume. Após isso, `restart: unless-stopped` mantém o listener rodando sem re-autenticação.

**Por que não Kubernetes:** K8s é 10x mais complexidade operacional para rodar dois processos Python. Docker Compose em uma EC2 é o teto certo para ferramenta pessoal.

---

### HTTPS e Reverse Proxy

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Caddy | **2.x** (current) | Reverse proxy + TLS automático | Obtém e renova certificados Let's Encrypt automaticamente via ACME. Configuração em 3 linhas (Caddyfile). Sem certbot, sem cron, sem renovação manual. Alternativa Nginx requer Certbot separado, cron para renovação, e 50+ linhas de config. |

**Caddyfile mínimo:**
```
helpertips.seudominio.com {
    reverse_proxy dashboard:8050
}
```

Caddy lida com: redirect HTTP→HTTPS, TLS certificate provisioning, TLS renewal, HTTP/2. Zero configuração adicional.

**Pré-requisito:** Ter um domínio apontando para o Elastic IP da EC2. Sem domínio, rodar só em HTTP via IP direto (não recomendado por segurança, mas funciona para testes).

**Por que não Nginx:** Nginx é mais performático para alta carga, mas Caddy tem TLS automático out-of-the-box. Para uso pessoal com ~1 usuário simultâneo, a diferença de performance não existe. O custo de configuração do Nginx (Certbot setup, renewal cron, redirect rules) não compensa.

---

### Secrets em Produção

| Approach | Cost | Why |
|----------|------|-----|
| SSM Parameter Store (SecureString) | **Grátis** (standard parameters) | Armazena segredos criptografados com KMS. Instância EC2 com IAM role lê os segredos via AWS CLI ou SDK ao iniciar. Sem custo para <= 10.000 parâmetros standard. |

**Fluxo recomendado:**
1. Armazenar no SSM: `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_SESSION_STRING`, `POSTGRES_PASSWORD`, `TELEGRAM_PHONE`
2. Script de inicialização na EC2 lê SSM e popula `.env` em `/app/.env` (fora do git)
3. `docker compose --env-file /app/.env up -d`

**Por que não AWS Secrets Manager:** Secrets Manager custa $0.40/segredo/mês — para 5 segredos, $2/mês. SSM Parameter Store padrão é gratuito. A funcionalidade de rotação automática do Secrets Manager não agrega valor aqui (credenciais Telegram não rotacionam automaticamente).

**Por que não hardcodar no docker-compose.yml:** O `docker-compose.yml` vai para o git. Segredos no arquivo de compose vazam quando o repositório é publicado no GitHub.

**StringSession do Telethon:** Em produção, trocar SQLiteSession por StringSession. A string de sessão (gerada uma vez via `StringSession.save()`) é armazenada como variável de ambiente no SSM, eliminando a necessidade de persistir o arquivo `.session` em volume Docker. Isso simplifica deploys e backups.

---

### CI/CD

| Technology | Purpose | Why |
|------------|---------|-----|
| GitHub Actions | Pipeline de CI (testes) + CD (deploy) | Grátis para repositórios públicos, 2.000 min/mês para privados. Integração nativa com GitHub onde o código já está. |

**Pipeline recomendado (minimalista para ferramenta pessoal):**

```yaml
# .github/workflows/deploy.yml
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r requirements.txt && pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ec2-user
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd /app/helpertips
            git pull origin main
            docker compose build
            docker compose up -d
```

**Por que SSH direto e não ECR + ECS:** ECR push + ECS service update é o padrão corporativo mas adiciona 3 serviços AWS e 30+ minutos de setup. Para uma pessoa e um servidor, `git pull + docker compose up` é equivalente e 10x mais simples.

**Por que não AWS CodePipeline/CodeDeploy:** Mais serviços AWS para gerenciar, não se integra naturalmente com GitHub sem webhooks extras. GitHub Actions é mais simples para quem já tem o código no GitHub.

---

### Segurança e Publicação GitHub

| Prática | Implementação | Por quê |
|---------|--------------|---------|
| `.gitignore` completo | `*.session`, `.env`, `*.pyc`, `__pycache__/`, `.pytest_cache/`, `*.log` | Impede vazamento de credenciais Telegram e sessão no repositório público |
| `.env.example` no git | Arquivo com chaves mas sem valores: `TELEGRAM_API_ID=`, `TELEGRAM_API_HASH=` | Documenta quais variáveis são necessárias sem expor valores reais |
| EC2 Security Group | Portas abertas: 22 (SSH, só seu IP), 80 (HTTP), 443 (HTTPS). Porta 8050 fechada externamente. | Dashboard exposto só via Caddy/HTTPS, não diretamente |
| IAM Role na EC2 | Role com permissão `ssm:GetParameter` no path `/helpertips/*` | Instância lê segredos sem credentials hardcodadas |
| SSH Key Pair | Par de chaves Ed25519 dedicado para a instância | Acesso seguro à EC2 sem senha |

**O que NÃO adicionar para ferramenta pessoal:**
- WAF (custo sem benefício para 1 usuário)
- CloudFront (latência não é problema)
- VPC privada complexa (EC2 pública com security group restrito é suficiente)
- Autenticação no dashboard (fora de escopo — acesso só pelo próprio usuário)
- CloudWatch Alarms avançados (logs do Docker são suficientes)

---

## Resumo de Custos AWS (us-east-1)

| Item | Custo/mês |
|------|-----------|
| EC2 t4g.micro (On-Demand, 24/7) | ~$6.13 |
| EBS gp3 20 GB | ~$1.60 |
| Elastic IP (associado) | Grátis |
| SSM Parameter Store (standard) | Grátis |
| Transferência de dados (saída, <1 GB/mês) | ~$0.09 |
| GitHub Actions (repo público) | Grátis |
| **Total** | **~$7.82/mês** |

> Comparativo: t4g.micro + RDS db.t4g.micro custaria ~$28/mês. A opção self-hosted PostgreSQL no mesmo EC2 economiza ~$20/mês sem perda funcional para este caso de uso.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Telegram client | Telethon 1.42.0 | Pyrogram | No advantage; smaller community |
| Telegram client | Telethon 1.42.0 | Bot API (python-telegram-bot) | Cannot join private groups without admin |
| PostgreSQL driver | psycopg2-binary | asyncpg | Async overhead unjustified for low-write workload |
| PostgreSQL driver | psycopg2-binary | psycopg3 | Newer but no current advantage; psycopg2 is stable |
| PostgreSQL driver | psycopg2-binary | SQLAlchemy ORM | ORM abstraction not warranted for simple schema |
| Dashboard | Plotly Dash 4.1.0 | Streamlit | Weaker multi-filter callback model |
| Dashboard | Plotly Dash 4.1.0 | FastAPI + React | 3x scope increase, JavaScript required |
| Dashboard | Plotly Dash 4.1.0 | Grafana | Cannot run custom Python ROI simulation |
| Config | python-dotenv | pydantic-settings | Overkill for personal tool without type-validated config class |
| Compute | EC2 t4g.micro | EC2 t3.micro | t4g é 40% mais barato ($6.13 vs $8.47/mês), arm64 sem incompatibilidades para Python |
| Database hosting | PostgreSQL no EC2 | RDS db.t4g.micro | RDS custa $21.90/mês vs ~$0 incremental no mesmo EC2 |
| Reverse proxy | Caddy 2 | Nginx + Certbot | Caddy tem TLS automático, Nginx requer setup manual de certificado |
| Secrets | SSM Parameter Store | AWS Secrets Manager | Secrets Manager custa $0.40/segredo/mês; SSM standard é grátis |
| CI/CD | GitHub Actions | AWS CodePipeline | CodePipeline adiciona 3 serviços extras desnecessários; GH Actions é mais simples |
| Orchestration | Docker Compose | ECS Fargate | Fargate custa $20-30/mês vs $0 incremental; Docker Compose é suficiente |
| Session storage | Telethon StringSession | SQLiteSession em volume | StringSession como env var elimina gerenciamento de volume para o .session |

---

## Installation

```bash
# Core listener dependencies
pip install "telethon~=1.42" "psycopg2-binary>=2.9" "python-dotenv>=1.0"

# Dashboard
pip install "dash>=4.1,<5" "dash-bootstrap-components>=2.0"

# Dev / testing
pip install pytest
```

**Lock file:** Use `pip freeze > requirements.txt` after install and commit it. This project has no `pyproject.toml` requirement — a plain `requirements.txt` is appropriate for a personal tool.

---

## Key Dependency Interactions

- **Telethon + asyncio:** Telethon runs an `asyncio` event loop. Database writes from event handlers must be wrapped in `asyncio.to_thread()` or a threadpool executor to avoid blocking the event loop when calling sync psycopg2. Example pattern:

  ```python
  import asyncio
  @client.on(events.NewMessage(chats=GROUP_ID))
  async def handler(event):
      await asyncio.to_thread(save_signal, event.raw_text)
  ```

- **Dash + Telethon process separation:** Dash runs its own blocking web server (`app.run()`). The Telethon listener runs a separate asyncio loop via `client.run_until_disconnected()`. These must run in **separate processes** (two scripts, or subprocess launch), not in the same process. Do not attempt to share a single event loop between them.

- **Telethon session file:** The `.session` SQLite file generated by Telethon on first auth must be excluded from git (`.gitignore`) and persisted across restarts on the deployment host. In production, prefer `StringSession` stored as environment variable in SSM Parameter Store.

- **Docker Compose + restart policies:** `restart: unless-stopped` garante que listener e dashboard reiniciam após falha ou reboot da instância. O PostgreSQL deve iniciar antes dos outros serviços — `depends_on: [postgres]` garante a ordem de start, mas não que o PostgreSQL está pronto. Adicionar `healthcheck` no serviço postgres se necessário.

---

## Version Pinning Rationale

| Package | Pin Strategy | Reason |
|---------|-------------|--------|
| telethon | `~=1.42` | Allows patch updates; blocks accidental upgrade to v2 alpha |
| psycopg2-binary | `>=2.9` | Any 2.x is compatible; 2.9 brought Python 3.10+ support |
| python-dotenv | `>=1.0` | Stable API since 1.0; no upper bound needed |
| dash | `>=4.1,<5` | Blocks major version upgrade (Dash 5 will have breaking changes) |
| dash-bootstrap-components | `>=2.0` | Bootstrap 5 baseline; compatible with Dash 4.x |
| Docker image | `postgres:16-alpine` | Pin major version; alpine keeps image pequena (~80 MB) |
| Docker image | `caddy:2-alpine` | Pin major version; 2.x tem TLS automático; v3 não existe ainda |

---

## Sources

**Application Stack (2026-04-02)**
- Telethon latest version: [Telethon docs 1.42.0](https://docs.telethon.dev/) — HIGH confidence (official docs)
- Telethon PyPI: [pypi.org/project/Telethon](https://pypi.org/project/Telethon/) — HIGH confidence
- Dash 4.1.0 installation: [dash.plotly.com/installation](https://dash.plotly.com/installation) — HIGH confidence (official docs, verified via WebFetch)
- dash-bootstrap-components: [dash-bootstrap-components.com](https://www.dash-bootstrap-components.com/) — HIGH confidence
- psycopg2-binary vs psycopg2 production guidance: [psycopg.org/docs/install.html](https://www.psycopg.org/docs/install.html) — HIGH confidence (official docs)
- FastAPI vs Flask vs Dash for analytics: [blog.jetbrains.com/pycharm/2025/02/django-flask-fastapi](https://blog.jetbrains.com/pycharm/2025/02/django-flask-fastapi/) — MEDIUM confidence (JetBrains blog)
- psycopg2 vs psycopg3 vs asyncpg: [tigerdata.com/blog/psycopg2-vs-psycopg3-performance-benchmark](https://www.tigerdata.com/blog/psycopg2-vs-psycopg3-performance-benchmark) — MEDIUM confidence (benchmark blog, multiple sources agree)
- Streamlit vs Dash 2025: [squadbase.dev/en/blog/streamlit-vs-dash-in-2025](https://www.squadbase.dev/en/blog/streamlit-vs-dash-in-2025-comparing-data-app-frameworks) — MEDIUM confidence

**Cloud Deployment Stack (2026-04-03)**
- EC2 t4g.micro pricing: [economize.cloud — t4g.micro](https://www.economize.cloud/resources/aws/pricing/ec2/t4g.micro/) — MEDIUM confidence (pricing site, consistent with Vantage)
- EC2 t4g.micro specs: [instances.vantage.sh — t4g.micro](https://instances.vantage.sh/aws/ec2/t4g.micro) — MEDIUM confidence
- RDS db.t4g.micro pricing: [economize.cloud — db.t4g.micro](https://www.economize.cloud/resources/aws/pricing/rds/db.t4g.micro/) — MEDIUM confidence
- EBS gp3 pricing $0.08/GB-mês: [oreateai.com — EBS gp3](https://www.oreateai.com/blog/demystifying-ebs-gp3-pricing-understanding-the-008gbmonth-in-useast1/) — MEDIUM confidence (consistent com AWS official pricing page)
- SSM Parameter Store vs Secrets Manager: [ranthebuilder.cloud](https://ranthebuilder.cloud/blog/secrets-manager-vs-parameter-store-which-one-should-you-really-use/) — MEDIUM confidence (múltiplas fontes concordam)
- AWS SSM pricing (standard free): [AWS re:Post](https://repost.aws/questions/QUpBU6XmpzT0-W_AvtwaQQsQ/cost-of-secrets-manager) — MEDIUM confidence
- Caddy vs Nginx HTTPS: [selfhostwise.com 2026](https://selfhostwise.com/posts/traefik-vs-caddy-vs-nginx-proxy-manager-which-reverse-proxy-should-you-choose-in-2026/) — MEDIUM confidence
- Telethon StringSession: [docs.telethon.dev/sessions](https://docs.telethon.dev/en/stable/concepts/sessions.html) — HIGH confidence (official docs, acesso bloqueado por 403 mas conteúdo confirmado via múltiplas fontes secundárias)
- GitHub Actions EC2 deploy: [dev.to — Docker deploy EC2](https://dev.to/engrmark/how-to-set-up-github-actions-to-deploy-a-simple-docker-app-on-an-ec2-server-4d0h) — MEDIUM confidence
