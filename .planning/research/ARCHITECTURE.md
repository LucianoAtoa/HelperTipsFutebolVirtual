# Architecture Patterns

**Project:** HelperTips — Futebol Virtual
**Domain:** Telegram signal capture + PostgreSQL + analytics dashboard
**Researched:** 2026-04-02
**Confidence:** HIGH (core patterns verified against official Telethon docs and FastAPI docs)

---

## Recommended Architecture

The system is three cooperating components inside a single Python process (or two processes for clean separation):

```
┌──────────────────────────────────────────────────────┐
│  Telegram (MTProto via Telethon)                     │
│    Group: {VIP} ExtremeTips                          │
└──────────────┬───────────────┬──────────────────────┘
               │ NewMessage    │ MessageEdited
               ▼               ▼
┌──────────────────────────────────────────────────────┐
│  LISTENER (async, long-running)                      │
│  telethon.TelegramClient + asyncio event loop        │
│  - @client.on(events.NewMessage)                     │
│  - @client.on(events.MessageEdited)                  │
│  - Routes raw text → Parser                          │
└──────────────────────┬───────────────────────────────┘
                       │ parsed dict
                       ▼
┌──────────────────────────────────────────────────────┐
│  PARSER (pure function, stateless)                   │
│  - Regex extraction: liga, entrada, horario, placar  │
│  - Detects signal type: new signal vs result update  │
│  - Returns structured dict or None (unrecognized)    │
└──────────────────────┬───────────────────────────────┘
                       │ structured signal
                       ▼
┌──────────────────────────────────────────────────────┐
│  STORE (repository layer)                            │
│  psycopg2-binary + PostgreSQL 16                     │
│  - INSERT ... ON CONFLICT (message_id) DO UPDATE     │
│  - Handles both: new signal insert + result upsert   │
│  - Connection pool (thread-safe: psycopg2 pool)      │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  PostgreSQL 16                                       │
│  Table: signals                                      │
│  Table: (future) sessions, config                    │
└──────────────────────┬───────────────────────────────┘
                       │ SQL queries
                       ▼
┌──────────────────────────────────────────────────────┐
│  DASHBOARD API (FastAPI)                             │
│  - GET /api/stats — aggregate stats JSON             │
│  - GET /api/signals — paginated signal list          │
│  - GET /api/signals/filters — filter options         │
│  - Jinja2 templates serve HTML shell                 │
│  - Chart.js or Plotly renders in browser             │
└──────────────────────────────────────────────────────┘
```

---

## Component Boundaries

| Component | Responsibility | Inputs | Outputs | Communicates With |
|-----------|---------------|--------|---------|-------------------|
| **Listener** | Maintain persistent Telegram connection; receive events | MTProto events (NewMessage, MessageEdited) | Raw message text + message_id | Parser |
| **Parser** | Transform raw text into structured data | Raw message string | `dict` with fields or `None` | Store |
| **Store** | Persist and deduplicate signals | Structured dict | Confirmation / row | PostgreSQL |
| **PostgreSQL** | Durable storage + query engine | SQL | Result sets | Store, Dashboard API |
| **Dashboard API** | Serve analytics over HTTP | HTTP GET requests with filter params | JSON + HTML | Browser |
| **Browser** | Render charts, handle filter interactions | HTML + JSON | User events (filter changes) | Dashboard API |

### Boundary rules

- Parser has **zero** database imports. It is a pure function: `parse_message(text: str) -> dict | None`.
- Store has **zero** Telethon imports. It receives dicts and speaks only SQL.
- Listener has **zero** SQL. It calls Parser, then Store.
- Dashboard API is **read-only** against the database. It never writes.

---

## Data Flow

### New signal arrives (forward flow)

```
Telegram group message
  → Telethon fires events.NewMessage
  → Listener receives event.message.text + event.message.id
  → Parser.parse(text) → { liga, entrada, horario, tipo, raw_text, message_id }
  → Store.upsert_signal(parsed) → INSERT ON CONFLICT (message_id) DO NOTHING
  → PostgreSQL row created
```

### Result update arrives (edit flow)

```
Telegram group edits message (GREEN/RED + placar added)
  → Telethon fires events.MessageEdited
  → Same Listener handler (reuse parse logic)
  → Parser.parse(text) → same dict + { resultado: "GREEN", placar: "2-1" }
  → Store.upsert_signal(parsed) → INSERT ON CONFLICT (message_id) DO UPDATE
    SET resultado = EXCLUDED.resultado, placar = EXCLUDED.placar
  → PostgreSQL row updated in-place
```

### Dashboard query flow (read path)

```
Browser loads dashboard URL
  → FastAPI serves HTML shell (Jinja2)
  → Browser JS calls GET /api/stats?liga=&entrada=&periodo=
  → FastAPI queries PostgreSQL (aggregate SQL)
  → Returns JSON { total, greens, reds, taxa, roi_simulado, ... }
  → Chart.js renders graphs from JSON
```

### Startup flow

```
python main.py
  → DB.ensure_schema() → CREATE TABLE IF NOT EXISTS
  → Store.print_summary() → console stats (total, greens, reds, taxa)
  → FastAPI starts on background thread (or subprocess)
  → Telethon client.start() → prompts phone/code if no .session file
  → client.run_until_disconnected() → blocks, processing events
```

---

## Process Model

Two valid options. Option B is recommended for this project:

### Option A: Single Python process (asyncio + thread)

```
main.py
  asyncio event loop (Telethon)
  + threading: FastAPI via uvicorn.run() in daemon thread
  + psycopg2 SimpleConnectionPool (thread-safe)
```

Pros: one command to run, simpler deployment.
Cons: uvicorn and asyncio share process — must use `loop.run_in_executor` carefully for blocking DB calls. psycopg2 is synchronous, so DB writes from asyncio handlers need `asyncio.to_thread()` (Python 3.9+).

### Option B: Two separate processes (recommended)

```
python listener.py   ← Telethon + Parser + Store (writes)
python dashboard.py  ← FastAPI + uvicorn (reads only)
```

Started with a simple shell script or `Procfile`. Both connect to same PostgreSQL.

Pros: total isolation — Telethon crash does not kill dashboard and vice versa. No async/sync bridging complexity. Easier to debug each separately. Matches how the project will likely be deployed (listener as systemd service, dashboard as web server).
Cons: two processes to manage locally.

**Verdict: Use Option B.** The listener must stay running 24/7 uninterrupted. Mixing it with a web server in one process increases crash risk. psycopg2 sync I/O fits naturally in a synchronous listener loop with Telethon's `client.run_until_disconnected()`.

---

## Suggested Build Order

Dependencies between components dictate this order:

```
1. Database schema (signals table, indexes)
   └─ Prerequisite for everything else

2. Parser (pure function, no dependencies)
   └─ Can be built and unit-tested with no DB, no Telegram

3. Store (repository layer)
   └─ Depends on: schema (1)
   └─ Testable with a local PostgreSQL and known dicts

4. Listener (Telethon integration)
   └─ Depends on: Parser (2), Store (3)
   └─ Once this runs, signals flow into the DB

5. Terminal stats (startup summary)
   └─ Depends on: Store (3)
   └─ Validates the pipeline is capturing correctly

6. Dashboard API + UI
   └─ Depends on: populated DB (4+5 running first)
   └─ Read-only, can be built incrementally
```

This order ensures you can validate each layer independently before adding the next. By step 4, the core value (signal capture) is working. Steps 5-6 are display layers on top of proven data.

---

## Database Schema (Core Table)

```sql
CREATE TABLE signals (
    id              SERIAL PRIMARY KEY,
    message_id      BIGINT UNIQUE NOT NULL,      -- Telegram message ID, dedup key
    liga            TEXT,                         -- Liga name e.g. "World League"
    entrada         TEXT,                         -- Bet type e.g. "Ambas Marcam"
    horario         TEXT,                         -- Match time e.g. "14:30"
    periodo         TEXT,                         -- "1T" / "2T" / "FT"
    dia_semana      SMALLINT,                     -- 0=Mon..6=Sun (derived at insert)
    resultado       TEXT,                         -- "GREEN" / "RED" / NULL (pending)
    placar          TEXT,                         -- e.g. "2-1" or NULL
    raw_text        TEXT NOT NULL,                -- Original message for re-parsing
    received_at     TIMESTAMPTZ DEFAULT NOW(),    -- When listener captured it
    updated_at      TIMESTAMPTZ DEFAULT NOW()     -- Last upsert timestamp
);

CREATE INDEX idx_signals_liga        ON signals(liga);
CREATE INDEX idx_signals_entrada     ON signals(entrada);
CREATE INDEX idx_signals_resultado   ON signals(resultado);
CREATE INDEX idx_signals_received_at ON signals(received_at);
```

The `message_id` UNIQUE constraint is the deduplication key. The upsert pattern `INSERT ... ON CONFLICT (message_id) DO UPDATE` handles both new signals and result edits with a single code path.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Parsing inside the Listener handler

**What goes wrong:** Business logic (regex) bleeds into the event handler function. When the message format changes, you modify Telethon event handler code.
**Instead:** Listener calls `Parser.parse(text)` — a separate module. If parse returns None, log and skip. Parser is independently testable.

### Anti-Pattern 2: Writing from Dashboard API

**What goes wrong:** Dashboard endpoints that write state (e.g., "mark as manually verified") create a two-writer problem (listener + dashboard both write). Race conditions.
**Instead:** Dashboard is read-only in v1. Any write path (future feature) belongs to a dedicated admin endpoint with explicit lock semantics.

### Anti-Pattern 3: Using Telethon's file-based session with concurrent workers

**What goes wrong:** Two Telethon instances sharing the same `.session` file → corruption.
**Instead:** Single listener process, single `.session` file. If scaling is needed later, use PostgreSQL session storage (`telethon_postgres_sessionstorage`).

### Anti-Pattern 4: Re-querying PostgreSQL on every message edit for dedup check

**What goes wrong:** Checking `SELECT EXISTS` before every insert when message edits are frequent → unnecessary round trips.
**Instead:** Let PostgreSQL's `ON CONFLICT` clause handle dedup atomically. No pre-check needed.

### Anti-Pattern 5: Building the dashboard before the listener is validated

**What goes wrong:** Spending time on UI when the core parser may have edge cases that corrupt the data model.
**Instead:** Follow the build order above. Run the listener for at least one real session before building charts.

---

## Scalability Considerations

This is a single-user personal tool. The scalability table below is for awareness, not action:

| Concern | At current scale (1 user) | If productized |
|---------|--------------------------|----------------|
| Telegram API rate limits | Not a concern (single account) | Use multiple accounts or Bot API |
| DB write throughput | psycopg2 sync is fine (<100 signals/day) | Move to asyncpg + connection pool |
| Dashboard query performance | Full table scans fine (<100k rows) | Add materialized views for aggregates |
| Session management | File-based `.session` is fine | Move to PostgreSQL session storage |
| Listener restarts | Manual restart is acceptable | Add systemd service + retry logic |

---

## Sources

- Telethon Events Reference: https://docs.telethon.dev/en/stable/quick-references/events-reference.html
- Telethon Update Events (NewMessage, MessageEdited): https://docs.telethon.dev/en/stable/modules/events.html
- Telethon PostgreSQL session storage: https://github.com/alozovskoy/telethon_postgres_sessionstorage
- FastAPI + PostgreSQL + WebSockets (real-time dashboard pattern): https://testdriven.io/blog/fastapi-postgres-websockets/
- FastAPI + Jinja2 + HTMX server-rendered dashboards: https://www.johal.in/fastapi-templating-jinja2-server-rendered-ml-dashboards-with-htmx-2025-3/
- asyncpg (async PostgreSQL alternative): https://github.com/MagicStack/asyncpg
- PostgreSQL LISTEN/NOTIFY with asyncio: https://gist.github.com/kissgyorgy/beccba1291de962702ea9c237a900c79
- PostgreSQL upsert (INSERT ON CONFLICT): https://www.geeksforgeeks.org/postgresql/postgresql-upsert/
