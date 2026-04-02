# Technology Stack

**Project:** HelperTips — Futebol Virtual (Telegram Signal Capture + Betting Analytics Dashboard)
**Researched:** 2026-04-02
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

- **Telethon session file:** The `.session` SQLite file generated by Telethon on first auth must be excluded from git (`.gitignore`) and persisted across restarts on the deployment host.

---

## Version Pinning Rationale

| Package | Pin Strategy | Reason |
|---------|-------------|--------|
| telethon | `~=1.42` | Allows patch updates; blocks accidental upgrade to v2 alpha |
| psycopg2-binary | `>=2.9` | Any 2.x is compatible; 2.9 brought Python 3.10+ support |
| python-dotenv | `>=1.0` | Stable API since 1.0; no upper bound needed |
| dash | `>=4.1,<5` | Blocks major version upgrade (Dash 5 will have breaking changes) |
| dash-bootstrap-components | `>=2.0` | Bootstrap 5 baseline; compatible with Dash 4.x |

---

## Sources

- Telethon latest version: [Telethon docs 1.42.0](https://docs.telethon.dev/) — HIGH confidence (official docs)
- Telethon PyPI: [pypi.org/project/Telethon](https://pypi.org/project/Telethon/) — HIGH confidence
- Dash 4.1.0 installation: [dash.plotly.com/installation](https://dash.plotly.com/installation) — HIGH confidence (official docs, verified via WebFetch)
- dash-bootstrap-components: [dash-bootstrap-components.com](https://www.dash-bootstrap-components.com/) — HIGH confidence
- psycopg2-binary vs psycopg2 production guidance: [psycopg.org/docs/install.html](https://www.psycopg.org/docs/install.html) — HIGH confidence (official docs)
- FastAPI vs Flask vs Dash for analytics: [blog.jetbrains.com/pycharm/2025/02/django-flask-fastapi](https://blog.jetbrains.com/pycharm/2025/02/django-flask-fastapi/) — MEDIUM confidence (JetBrains blog)
- psycopg2 vs psycopg3 vs asyncpg: [tigerdata.com/blog/psycopg2-vs-psycopg3-performance-benchmark](https://www.tigerdata.com/blog/psycopg2-vs-psycopg3-performance-benchmark) — MEDIUM confidence (benchmark blog, multiple sources agree)
- Streamlit vs Dash 2025: [squadbase.dev/en/blog/streamlit-vs-dash-in-2025](https://www.squadbase.dev/en/blog/streamlit-vs-dash-in-2025-comparing-data-app-frameworks) — MEDIUM confidence
