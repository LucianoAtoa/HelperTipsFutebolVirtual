<!-- GSD:project-start source:PROJECT.md -->
## Project

**HelperTips — Futebol Virtual**

Sistema que conecta ao grupo **{VIP} ExtremeTips** no Telegram, captura sinais de apostas de futebol virtual da Bet365 em tempo real, armazena no PostgreSQL e fornece um dashboard web elaborado com estatísticas completas, filtros interativos, gráficos dinâmicos e simulação de ROI. Feito para o próprio usuário que hoje acompanha e aposta manualmente.

**Core Value:** Capturar automaticamente todos os sinais do Telegram e transformar em estatísticas confiáveis para tomada de decisão nas apostas.

### Constraints

- **Stack**: Python 3.12+, Telethon 1.37, PostgreSQL 16, psycopg2-binary, python-dotenv — definido no guia
- **Telegram API**: Requer API ID e Hash do my.telegram.org — credenciais do próprio usuário
- **Sessão Telethon**: Gera arquivo .session que deve ficar no .gitignore
- **Formato mensagens**: Parsing depende do formato atual do grupo — se mudar, parser precisa atualizar
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Telegram Listener
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Telethon | **1.42.0** (current, not 1.37) | User-client MTProto Telegram listener | Only Python library that connects as a user account (not bot), enabling listening to groups without admin rights. `events.MessageEdited` handles the group's edit-based result pattern natively. Async/await first-class. |
### Database Driver
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| psycopg2-binary | **2.9.x** (latest stable) | PostgreSQL sync driver | Simple, battle-tested, no build dependencies. Sync is fine here — the listener is async (Telethon) but writes are infrequent (one per signal) and don't need async I/O. Dashboard reads are also low-frequency. |
| PostgreSQL | **16** | Relational storage | JSONB support for raw message metadata, array types, window functions for ROI simulation, partitioning if historical data grows. AWS RDS-ready. |
### Web Dashboard
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Plotly Dash | **4.1.0** (current) | Interactive analytics dashboard | Pure-Python dashboards with no JavaScript required. Built-in Plotly charts (bar, line, scatter, heatmap) cover all analytics views needed. Callbacks handle interactive filters reactively. Runs as a standalone web server. |
| dash-bootstrap-components | **2.0.x** (current, Bootstrap 5) | Responsive layout and UI components | Cards, grids, navbars, modals without writing CSS. Bootstrap 5 responsive grid means the dashboard works on mobile and desktop. Standard pairing with Dash in the community. |
| plotly | **bundled with Dash 4.1.0** | Chart rendering | Installed automatically as Dash dependency. No separate install needed. |
### Configuration & Secrets
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| python-dotenv | **1.x** (current stable) | Load `.env` file | Zero-dependency, industry standard for dev environments. Keeps API credentials out of source code. |
### Python Runtime
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python | **3.12+** | Runtime | Telethon requires 3.8+; psycopg2-binary supports 3.12; Dash 4.1.0 requires 3.8+. Python 3.12 gives better performance (interpreter speedups), improved error messages, and is the current LTS-equivalent stable release. |
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
## Installation
# Core listener dependencies
# Dashboard
# Dev / testing
## Key Dependency Interactions
- **Telethon + asyncio:** Telethon runs an `asyncio` event loop. Database writes from event handlers must be wrapped in `asyncio.to_thread()` or a threadpool executor to avoid blocking the event loop when calling sync psycopg2. Example pattern:
- **Dash + Telethon process separation:** Dash runs its own blocking web server (`app.run()`). The Telethon listener runs a separate asyncio loop via `client.run_until_disconnected()`. These must run in **separate processes** (two scripts, or subprocess launch), not in the same process. Do not attempt to share a single event loop between them.
- **Telethon session file:** The `.session` SQLite file generated by Telethon on first auth must be excluded from git (`.gitignore`) and persisted across restarts on the deployment host.
## Version Pinning Rationale
| Package | Pin Strategy | Reason |
|---------|-------------|--------|
| telethon | `~=1.42` | Allows patch updates; blocks accidental upgrade to v2 alpha |
| psycopg2-binary | `>=2.9` | Any 2.x is compatible; 2.9 brought Python 3.10+ support |
| python-dotenv | `>=1.0` | Stable API since 1.0; no upper bound needed |
| dash | `>=4.1,<5` | Blocks major version upgrade (Dash 5 will have breaking changes) |
| dash-bootstrap-components | `>=2.0` | Bootstrap 5 baseline; compatible with Dash 4.x |
## Sources
- Telethon latest version: [Telethon docs 1.42.0](https://docs.telethon.dev/) — HIGH confidence (official docs)
- Telethon PyPI: [pypi.org/project/Telethon](https://pypi.org/project/Telethon/) — HIGH confidence
- Dash 4.1.0 installation: [dash.plotly.com/installation](https://dash.plotly.com/installation) — HIGH confidence (official docs, verified via WebFetch)
- dash-bootstrap-components: [dash-bootstrap-components.com](https://www.dash-bootstrap-components.com/) — HIGH confidence
- psycopg2-binary vs psycopg2 production guidance: [psycopg.org/docs/install.html](https://www.psycopg.org/docs/install.html) — HIGH confidence (official docs)
- FastAPI vs Flask vs Dash for analytics: [blog.jetbrains.com/pycharm/2025/02/django-flask-fastapi](https://blog.jetbrains.com/pycharm/2025/02/django-flask-fastapi/) — MEDIUM confidence (JetBrains blog)
- psycopg2 vs psycopg3 vs asyncpg: [tigerdata.com/blog/psycopg2-vs-psycopg3-performance-benchmark](https://www.tigerdata.com/blog/psycopg2-vs-psycopg3-performance-benchmark) — MEDIUM confidence (benchmark blog, multiple sources agree)
- Streamlit vs Dash 2025: [squadbase.dev/en/blog/streamlit-vs-dash-in-2025](https://www.squadbase.dev/en/blog/streamlit-vs-dash-in-2025-comparing-data-app-frameworks) — MEDIUM confidence
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Idioma

**Toda comunicação deve ser em português brasileiro (pt-BR).** Isso inclui:
- Respostas, explicações e perguntas ao usuário
- Outputs de progresso, banners, relatórios
- Mensagens de commit (prefixos convencionais em inglês como `feat`, `fix`, `docs` são OK)
- Conteúdo de artefatos GSD (PLAN.md, SUMMARY.md, CONTEXT.md, etc.)
- Comentários no código quando necessário

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
