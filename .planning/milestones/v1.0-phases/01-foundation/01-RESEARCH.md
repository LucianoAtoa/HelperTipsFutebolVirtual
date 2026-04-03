# Phase 1: Foundation - Research

**Researched:** 2026-04-02
**Domain:** Telethon user-client listener + PostgreSQL schema + regex message parser + project bootstrap
**Confidence:** HIGH

---

## Summary

Phase 1 builds the entire data pipeline from scratch: a Telethon-based listener that connects to the VIP Telegram group, parses signal messages using regex, and persists them to PostgreSQL using an upsert-only write path. No dashboard is involved — the output is reliable data in the database and a terminal startup summary.

The stack is fully resolved from prior research: Python 3.12+, Telethon 1.42.0 (current, not 1.37 as pinned in CLAUDE.md constraints), psycopg2-binary, python-dotenv. PostgreSQL 17 is installed at `/Applications/PostgreSQL 17/` and its server is running and accepting connections on port 5432. Telethon 1.40.0 is already installed; upgrading to 1.42.0 is required before starting.

The critical technical risk for this phase is the asyncio/psycopg2 boundary: every database write from within a Telethon event handler MUST be wrapped in `asyncio.to_thread()`. Missing this causes silent signal drops when two signals arrive in rapid succession. The second-most important constraint is the upsert-only write path — `INSERT ... ON CONFLICT (message_id) DO UPDATE` handles both new signals and result edits atomically, eliminating duplicates by design.

**Primary recommendation:** Build in this order: schema → parser (pure function, unit-testable) → store (repository layer) → listener (Telethon integration) → terminal stats. Validate each layer independently before connecting the next.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

No CONTEXT.md exists for this phase. Constraints are sourced from CLAUDE.md and project research documents.

### Locked Decisions (from CLAUDE.md + STATE.md)

- **Stack**: Python 3.12+, Telethon 1.42.0, PostgreSQL 16+, psycopg2-binary, python-dotenv
- **Telegram API**: User-client (Telethon), NOT Bot API — required to listen to private group without admin rights
- **Session file**: Generates `.session` file that MUST be in `.gitignore` before first commit
- **Message format**: Parsing depends on current format of {VIP} ExtremeTips group — regex against real messages
- **Two separate processes**: listener.py (Telethon + writes) and dashboard.py (Dash + reads) — never mix in one process
- **Upsert-only write path**: `ON CONFLICT` upsert — no SELECT-then-INSERT; handles new signals and result edits atomically
- **asyncio safety**: psycopg2 writes MUST be wrapped in `asyncio.to_thread()` — must not block event loop

### Claude's Discretion

- Project structure / file layout (suggested: `src/` or flat layout)
- Session name string (suggested: `helpertips_listener`)
- Process lock file implementation details
- Startup summary formatting style
- Whether to use `SimpleConnectionPool` or single persistent connection in Phase 1
- `.env` variable naming conventions
- Logging format and verbosity

### Deferred Ideas (OUT OF SCOPE for Phase 1)

- Web dashboard (Phase 2)
- ROI simulation (Phase 2)
- Filter UI (Phase 2)
- Advanced analytics — streaks, equity curve, gale analysis (Phase 3)
- Backfill utility for offline gaps (v2/RESIL-01)
- Connection pool (Phase 2 concern)
- Multiple Telegram groups
- Bet automation
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LIST-01 | Sistema captura sinais novos do grupo Telegram em tempo real (events.NewMessage) | Telethon `@client.on(events.NewMessage(chats=GROUP_ID))` — verified in official docs |
| LIST-02 | Sistema detecta edições de mensagens com resultado (events.MessageEdited) | Telethon `@client.on(events.MessageEdited(chats=GROUP_ID))` — same client, distinct event type |
| LIST-03 | Sistema deduplica sinais por telegram_msg_id (ON CONFLICT upsert) | PostgreSQL `INSERT ... ON CONFLICT (message_id) DO UPDATE` — single write path covers both LIST-01 and LIST-02 |
| LIST-04 | Sistema ignora mensagens sem texto (imagens, stickers) | `event.message.text` check — empty/None means skip; Telethon exposes this on every message event |
| LIST-05 | Sistema reconecta automaticamente após perda de conexão | Telethon `client.run_until_disconnected()` + `asyncio.sleep` retry loop in main; `try/except` in handlers |
| PARS-01 | Parser extrai liga da mensagem do sinal | Regex against real message format — requires sample messages captured from the group |
| PARS-02 | Parser extrai entrada recomendada (tipo de aposta) | Regex — same format dependency as PARS-01 |
| PARS-03 | Parser extrai horários dos jogos | Regex — time pattern e.g. `\d{2}:\d{2}` |
| PARS-04 | Parser extrai resultado (GREEN/RED) de mensagens editadas | Regex on edited message text — "GREEN" / "RED" literals or emoji markers |
| PARS-05 | Parser extrai placares individuais quando disponíveis | Regex for score pattern e.g. `\d+-\d+` |
| PARS-06 | Parser armazena texto original (raw_text) para recuperação em caso de falha | `raw_text TEXT NOT NULL` column in schema — always stored regardless of parse success |
| PARS-07 | Parser registra taxa de cobertura (% de mensagens parseadas vs descartadas) | In-memory counter in listener process; print on startup and on each parse failure |
| DB-01 | Schema PostgreSQL para sinais com campos: liga, entrada, horários, resultado, placares, timestamps | `CREATE TABLE signals (...)` with `message_id BIGINT UNIQUE` — full schema in Architecture Patterns section |
| DB-02 | Upsert de sinais com deduplicação por telegram_msg_id | `INSERT ... ON CONFLICT (message_id) DO UPDATE SET ...` — atomic, no pre-check SELECT needed |
| DB-03 | Update de resultado quando mensagem é editada | Same upsert path: `DO UPDATE SET resultado = EXCLUDED.resultado, placar = EXCLUDED.placar` |
| DB-04 | Chamadas ao banco não bloqueiam o event loop do asyncio (asyncio.to_thread) | `await asyncio.to_thread(blocking_fn, conn, data)` — wraps sync psycopg2 in thread pool |
| TERM-01 | Ao iniciar, exibe resumo: total de sinais, greens, reds, taxa de acerto | `SELECT COUNT(*), SUM(resultado='GREEN'), SUM(resultado='RED') FROM signals` on startup |
| TERM-02 | Ao iniciar, confirma conexão com grupo Telegram | Print group title + id after `await client.get_entity(GROUP_ID)` succeeds |
| TERM-03 | Encerramento limpo com Ctrl+C | `KeyboardInterrupt` caught in main; call `client.disconnect()` before exit |
| OPER-02 | Arquivo .session no .gitignore antes do primeiro commit | `*.session` + `*.session-journal` + `.env` entries in `.gitignore` — must exist before `git add` |
| OPER-03 | Configuração via .env com validação de variáveis obrigatórias | `python-dotenv` loads `.env`; startup validates all required keys are non-empty and exits with clear error if missing |
</phase_requirements>

---

## Project Constraints (from CLAUDE.md)

All directives extracted from CLAUDE.md that the planner MUST enforce:

| Directive | Category | Enforcement |
|-----------|----------|-------------|
| Python 3.12+ | Stack | Verify `python3 --version >= 3.12` in Wave 0 |
| Telethon `~=1.42` | Stack | Pin in `requirements.txt`; current installed is 1.40.0 — upgrade required |
| PostgreSQL 16 | Stack | Running PostgreSQL 17 is acceptable (superset); DB-01 schema must target PG 16+ syntax |
| psycopg2-binary | Stack | Use binary package, not compiled psycopg2 |
| python-dotenv | Stack | Use for all credential/config loading |
| `.session` in `.gitignore` | Security | OPER-02: must be done before first `git commit` |
| Two separate processes | Architecture | listener.py + dashboard.py — never import Dash into listener |
| Upsert-only write path | Architecture | No SELECT-then-INSERT anywhere in store layer |
| asyncio.to_thread() for DB writes | Architecture | Every psycopg2 call from async handler uses this |

---

## Standard Stack

### Core (Phase 1 only — no Dash needed yet)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.13.6 (installed) | Runtime | 3.13 is superset of required 3.12+; already on machine |
| Telethon | 1.42.0 (PyPI latest) | Telegram user-client | User-account MTProto; only way to listen to private groups without admin |
| psycopg2-binary | 2.9.x | PostgreSQL sync driver | Battle-tested, no build deps; sync fine for low-frequency writes |
| python-dotenv | 1.x | `.env` loading | Industry standard; zero deps |
| pytest | latest | Unit testing parser | Pure function testing before any Telegram connection |

**Version note:** Telethon 1.40.0 is installed; latest is 1.42.0. Must upgrade before starting.

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| asyncio | stdlib | Event loop for Telethon | Always — Telethon requires async |
| re | stdlib | Regex for message parsing | In parser module |
| logging | stdlib | Structured log output | Listener events and parse failures |
| signal | stdlib | Graceful SIGINT handling | TERM-03 |

### Installation

```bash
# Upgrade Telethon to latest (1.42.0 — currently 1.40.0 is installed)
pip3 install "telethon~=1.42" --upgrade

# Core dependencies
pip3 install "psycopg2-binary>=2.9" "python-dotenv>=1.0"

# Testing
pip3 install pytest

# Lock
pip3 freeze > requirements.txt
```

**Version verification (confirmed 2026-04-02):**
- telethon latest: `1.42.0` (PyPI confirmed)
- psycopg2-binary latest: `2.9.x` (CLAUDE.md confirmed, HIGH confidence)
- python-dotenv: `>=1.0` (stable since 1.0)

---

## Architecture Patterns

### Recommended Project Structure

```
helpertips/
├── .env                    # Secrets — NOT committed (in .gitignore)
├── .gitignore              # Must exist before first commit
├── requirements.txt        # Pinned dependencies
├── listener.py             # Entry point: Telethon + asyncio event loop
├── parser.py               # Pure function: parse_message(text) -> dict | None
├── store.py                # Repository: upsert_signal(conn, data), get_stats(conn)
├── db.py                   # Database: connection factory, ensure_schema()
└── tests/
    └── test_parser.py      # Unit tests for parser.py (no DB, no Telegram needed)
```

Phase 1 does NOT include: `dashboard.py`, `app/`, `static/`, templates.

### Pattern 1: Telethon Event Handler with asyncio.to_thread

**What:** Register async handlers for `NewMessage` and `MessageEdited`. Both call the same parser + upsert path.
**When to use:** Every incoming Telegram event that needs database persistence.

```python
# Source: CLAUDE.md + ARCHITECTURE.md (STACK.md pattern)
import asyncio
from telethon import TelegramClient, events
from parser import parse_message
from store import upsert_signal

@client.on(events.NewMessage(chats=GROUP_ID))
@client.on(events.MessageEdited(chats=GROUP_ID))
async def handle_signal(event):
    if not event.message.text:
        return  # LIST-04: ignore media/stickers
    parsed = parse_message(event.message.text, event.message.id)
    if parsed is None:
        # PARS-07: increment parse failure counter
        parse_failures += 1
        return
    await asyncio.to_thread(upsert_signal, conn, parsed)  # DB-04
```

### Pattern 2: Upsert-Only Write Path

**What:** Single SQL statement handles both initial insert and result update.
**When to use:** Every signal write — new messages and edited messages use identical code.

```sql
-- Source: ARCHITECTURE.md schema
INSERT INTO signals (
    message_id, liga, entrada, horario, periodo,
    dia_semana, resultado, placar, raw_text, received_at, updated_at
) VALUES (
    %(message_id)s, %(liga)s, %(entrada)s, %(horario)s, %(periodo)s,
    %(dia_semana)s, %(resultado)s, %(placar)s, %(raw_text)s,
    NOW(), NOW()
)
ON CONFLICT (message_id) DO UPDATE SET
    resultado  = EXCLUDED.resultado,
    placar     = EXCLUDED.placar,
    liga       = EXCLUDED.liga,
    entrada    = EXCLUDED.entrada,
    updated_at = NOW()
WHERE
    -- Only update if result changed from NULL → value (prevents stomping a known result)
    signals.resultado IS DISTINCT FROM EXCLUDED.resultado
    OR signals.resultado IS NULL;
```

### Pattern 3: Parser as Pure Function

**What:** `parser.py` has zero imports from `store`, `db`, or `telethon`. Input: raw text string + message_id. Output: dict or None.
**When to use:** Called from both `NewMessage` and `MessageEdited` handlers.

```python
# Source: ARCHITECTURE.md boundary rules
import re

def parse_message(text: str, message_id: int) -> dict | None:
    """
    Returns structured dict or None if message is not a recognizable signal.
    The caller logs the None case for PARS-07 coverage tracking.
    """
    # Regex patterns filled in against real messages (see Open Questions)
    liga_match = re.search(r'LIGA_PATTERN', text, re.IGNORECASE)
    if liga_match is None:
        return None
    # ... extract all fields ...
    return {
        'message_id': message_id,
        'liga': liga_match.group(1),
        'entrada': ...,
        'horario': ...,
        'periodo': ...,
        'resultado': None,  # None = pending; will be updated by MessageEdited
        'placar': None,
        'raw_text': text,
        'dia_semana': ...,  # derived from received_at timestamp at call time
    }
```

### Pattern 4: .env Configuration with Startup Validation

**What:** Load all credentials from `.env`. Validate required keys on startup — fail fast with a clear error rather than crashing deep inside Telethon or psycopg2.
**When to use:** First thing `listener.py` does before any connections.

```python
# Source: OPER-03 requirement + python-dotenv standard usage
import os
from dotenv import load_dotenv

load_dotenv()

REQUIRED_VARS = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_GROUP_ID',
                 'DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']

def validate_config():
    missing = [k for k in REQUIRED_VARS if not os.environ.get(k)]
    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        print("Copy .env.example to .env and fill in all values.")
        raise SystemExit(1)
```

### Pattern 5: Terminal Startup Summary

**What:** On `listener.py` start, after DB connection succeeds, print a summary table of captured data.
**When to use:** TERM-01 and TERM-02 requirements.

```python
# Source: TERM-01/TERM-02 requirements
def print_startup_summary(conn, group_title):
    cur = conn.cursor()
    cur.execute("""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE resultado = 'GREEN') AS greens,
            COUNT(*) FILTER (WHERE resultado = 'RED')   AS reds,
            COUNT(*) FILTER (WHERE resultado IS NULL)   AS pending
        FROM signals
    """)
    total, greens, reds, pending = cur.fetchone()
    taxa = (greens / total * 100) if total > 0 else 0.0
    print(f"Connected to: {group_title}")
    print(f"Signals in DB: {total} | GREEN: {greens} | RED: {reds} | Pending: {pending}")
    print(f"Win rate: {taxa:.1f}%")
    print("Listening for new signals...")
```

### Recommended Database Schema

```sql
-- Source: ARCHITECTURE.md — DB-01
CREATE TABLE IF NOT EXISTS signals (
    id           SERIAL PRIMARY KEY,
    message_id   BIGINT UNIQUE NOT NULL,        -- Telegram msg ID, dedup key (LIST-03)
    liga         TEXT,                           -- PARS-01
    entrada      TEXT,                           -- PARS-02
    horario      TEXT,                           -- PARS-03 e.g. "14:30"
    periodo      TEXT,                           -- "1T" / "2T" / "FT"
    dia_semana   SMALLINT,                       -- 0=Mon..6=Sun (derived at insert)
    resultado    TEXT,                           -- PARS-04: "GREEN" / "RED" / NULL
    placar       TEXT,                           -- PARS-05: "2-1" or NULL
    raw_text     TEXT NOT NULL,                  -- PARS-06: original message
    received_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signals_liga        ON signals(liga);
CREATE INDEX IF NOT EXISTS idx_signals_entrada     ON signals(entrada);
CREATE INDEX IF NOT EXISTS idx_signals_resultado   ON signals(resultado);
CREATE INDEX IF NOT EXISTS idx_signals_received_at ON signals(received_at);
```

### .gitignore Minimum Content (OPER-02)

```
# Telegram session — contains full account auth state, NEVER commit
*.session
*.session-journal

# Credentials
.env

# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
```

### Anti-Patterns to Avoid

- **Parsing inside the event handler:** Business logic bleeds into Telethon code. Instead: call `parser.parse_message(text)` — a separate, independently testable module.
- **SELECT-then-INSERT for dedup:** Unnecessary round trip and race condition window. Instead: `ON CONFLICT` handles atomically.
- **Starting Dash in the same process as Telethon:** Both run blocking loops. Instead: two separate scripts.
- **Opening a psycopg2 connection inside each event handler:** Connection overhead per event. Instead: one persistent connection (or small pool) created once at startup, passed to store functions.
- **Using `event.raw_text` vs `event.message.text`:** `raw_text` includes markdown formatting markers; `message.text` is the plain string — use `message.text` for regex matching.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Telegram MTProto protocol | Custom Telegram client | Telethon 1.42.0 | 10,000+ lines of protocol handling, auth, encryption, session management |
| Signal deduplication | Custom SELECT+INSERT+lock | `ON CONFLICT (message_id) DO UPDATE` | Database handles atomicity, no application-level locking needed |
| Blocking I/O in asyncio | Thread management | `asyncio.to_thread()` (stdlib 3.9+) | Correct thread pool management is subtle; stdlib handles it |
| Env variable loading | File parser | `python-dotenv` | Handles quoting, comments, overrides, multiline values |
| Unit test runner | Test harness | `pytest` | Fixtures, parametrize, assertions — parser tests need none of this complexity |
| Telegram auth flow | Interactive prompts | `client.start()` | Telethon handles phone number prompt, code entry, 2FA on first run |

---

## Common Pitfalls

### Pitfall 1: psycopg2 Blocks the asyncio Event Loop (CRITICAL)

**What goes wrong:** Every `cur.execute()` call from inside an async Telethon event handler blocks the entire asyncio loop. If two signals arrive 50ms apart, the second is queued but not processed until the first database write completes. Under sustained load, the queue overflows and messages are silently dropped.

**Why it happens:** psycopg2 makes synchronous blocking socket calls. asyncio cannot multiplex while they run.

**How to avoid:** Wrap every psycopg2 call in `asyncio.to_thread(blocking_fn, conn, data)`. Never call `conn.cursor()` or `cur.execute()` directly from inside an `async def` event handler.

**Warning signs:** Log timestamp gaps between "message received" and "message saved" growing over time. Message count in DB diverges from actual group message count.

---

### Pitfall 2: Session File Committed to Git

**What goes wrong:** `.session` file in project root gets `git add .`-ed and pushed. Anyone with repo access has full Telegram account access.

**Why it happens:** `.session` is not in the default Python `.gitignore`.

**How to avoid:** Add `*.session` to `.gitignore` before `git init` or before first `git add`. Verify with `git ls-files | grep .session` — must return empty.

**Warning signs:** `git status` shows `helpertips_listener.session` as an untracked file that appears after first Telethon run — if not in `.gitignore`, it will be staged by `git add .`.

---

### Pitfall 3: Duplicate Records from NewMessage + MessageEdited

**What goes wrong:** Both handlers do a plain `INSERT`. The edit event creates a second row for the same signal. Win rate is double-counted.

**Why it happens:** Treating both events as independent "new signal" inserts.

**How to avoid:** Upsert-only write path from day one. `ON CONFLICT (message_id) DO UPDATE`. Both `NewMessage` and `MessageEdited` flow through the identical store function.

**Warning signs:** `SELECT message_id, COUNT(*) FROM signals GROUP BY message_id HAVING COUNT(*) > 1` returns rows.

---

### Pitfall 4: AuthKeyDuplicatedError from Concurrent Session Use

**What goes wrong:** Running `python listener.py` while another script already has the same `.session` file open causes Telegram to invalidate the auth key. Listener crashes and requires phone + SMS re-authentication.

**Why it happens:** MTProto detects two connections using the same auth key.

**How to avoid:** Add a process lock file check at startup. Write `/tmp/helpertips.lock` on start, remove on clean exit. Check for existence before starting.

**Warning signs:** `AuthKeyDuplicatedError` in logs. Listener crashes immediately on start after a previous crash (if previous run didn't clean up the lock file — need to handle stale locks).

---

### Pitfall 5: Parser Silently Fails on Format Changes

**What goes wrong:** The tipster group changes message format. Parser returns `None` for every message. Signals stop appearing in DB without any alert.

**Why it happens:** No coverage metric. No logging of unmatched messages.

**How to avoid:** (1) Always store `raw_text` — never lose the original. (2) Log every parse failure with the full message text. (3) Implement PARS-07 parse failure counter incremented on every `None` return. Print the counter in the startup summary.

**Warning signs:** Parse failure counter growing rapidly. DB row count not increasing while Telegram group is active.

---

### Pitfall 6: Regex Written Against Invented Format (Not Real Messages)

**What goes wrong:** Parser regex written against assumed message format doesn't match real messages from the group. Parser returns `None` for everything. Zero signals captured.

**Why it happens:** Parser is written before capturing any real messages from the group.

**How to avoid:** Capture 10–20 real messages from the group first (manual copy-paste into a `.txt` test fixture). Write regex against those exact strings. Commit the fixture alongside `tests/test_parser.py`.

**Warning signs:** PARS-07 counter showing 100% parse failure rate on first real-data run.

**Note:** This is flagged in STATE.md as a known research risk: "Parser regex must be written against real captured messages."

---

### Pitfall 7: Python 3.13 Installed, Telethon 1.40.0 Not Yet Upgraded

**What goes wrong:** Telethon 1.40.0 is installed. Latest is 1.42.0. CLAUDE.md pins `~=1.42`. If left on 1.40.0, the pin in `requirements.txt` would be wrong. Also, 1.42.0 may have bug fixes relevant to MessageEdited handling.

**How to avoid:** Wave 0 task: `pip3 install "telethon~=1.42" --upgrade` and `pip3 freeze > requirements.txt` before writing any listener code.

---

## Code Examples

### Verified Telethon Event Registration Pattern

```python
# Source: Telethon official docs https://docs.telethon.dev/en/stable/modules/events.html
from telethon import TelegramClient, events

client = TelegramClient('helpertips_listener', API_ID, API_HASH)

@client.on(events.NewMessage(chats=GROUP_ID))
async def on_new_message(event):
    ...

@client.on(events.MessageEdited(chats=GROUP_ID))
async def on_message_edited(event):
    ...

async def main():
    await client.start(phone=PHONE)
    entity = await client.get_entity(GROUP_ID)
    print(f"Connected to: {entity.title}")
    await client.run_until_disconnected()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
```

### Graceful Ctrl+C Shutdown (TERM-03)

```python
# Source: Python stdlib asyncio pattern
import asyncio
import signal

async def main():
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGINT, stop.set_result, None)

    async with client:
        await client.start(phone=PHONE)
        print("Listener started. Press Ctrl+C to stop.")
        try:
            await stop  # wait for SIGINT
        finally:
            print("Shutting down gracefully...")
            # cleanup here
```

### psycopg2 Connection Factory (db.py)

```python
# Source: psycopg2 official docs https://www.psycopg.org/docs/
import psycopg2
import os

def get_connection():
    return psycopg2.connect(
        host=os.environ['DB_HOST'],
        port=os.environ['DB_PORT'],
        dbname=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
    )

def ensure_schema(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id          SERIAL PRIMARY KEY,
                message_id  BIGINT UNIQUE NOT NULL,
                liga        TEXT,
                entrada     TEXT,
                horario     TEXT,
                periodo     TEXT,
                dia_semana  SMALLINT,
                resultado   TEXT,
                placar      TEXT,
                raw_text    TEXT NOT NULL,
                received_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at  TIMESTAMPTZ DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_signals_liga ON signals(liga);
            CREATE INDEX IF NOT EXISTS idx_signals_entrada ON signals(entrada);
            CREATE INDEX IF NOT EXISTS idx_signals_resultado ON signals(resultado);
            CREATE INDEX IF NOT EXISTS idx_signals_received_at ON signals(received_at);
        """)
    conn.commit()
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| CLAUDE.md pins Telethon 1.37 | Current stable is 1.42.0 | Nov 2025 | Upgrade required; no breaking changes |
| PROJECT.md references PostgreSQL 16 | Machine has PostgreSQL 17.6 | EnterpriseDB installer | PG 17 is a superset; schema syntax unchanged |
| Telethon 1.40.0 installed | 1.42.0 latest on PyPI | — | Must upgrade in Wave 0 |

---

## Open Questions

1. **Exact regex patterns for the message format**
   - What we know: Messages contain liga, entrada, horario with emojis; edits add GREEN/RED and placar
   - What's unclear: Exact field labels, emoji characters, line layout in real messages from {VIP} ExtremeTips
   - Recommendation: Plan Wave 0 or Wave 1 to include a "capture sample messages" task. The parser skeleton is built; regex patterns are filled in against real messages. Tests in `tests/test_parser.py` use the real samples as fixtures.

2. **GROUP_ID value for the VIP group**
   - What we know: Telethon identifies groups by integer ID or by username/invite link
   - What's unclear: Whether the group has a public username or requires numeric ID discovery via `get_entity()`
   - Recommendation: Plan a task to run `python3 -c "from telethon.sync import TelegramClient; ..."` interactively to discover the group ID and add it to `.env` as `TELEGRAM_GROUP_ID`.

3. **PostgreSQL database name and user to use**
   - What we know: PostgreSQL 17 is running on localhost:5432
   - What's unclear: Whether a dedicated DB/user should be created or the default `postgres` superuser is acceptable for a personal tool
   - Recommendation: Plan Wave 0 to create a dedicated database `helpertips` and user `helpertips_user`. Keeps credentials clean and mirrors future AWS RDS setup.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | Yes | 3.13.6 | — (3.12+ required, 3.13 is superset) |
| Telethon | LIST-01, LIST-02, LIST-03, LIST-04, LIST-05 | Yes (needs upgrade) | 1.40.0 installed / 1.42.0 required | — |
| psycopg2-binary | DB-01 through DB-04 | No | Not installed | Must install: `pip3 install psycopg2-binary>=2.9` |
| python-dotenv | OPER-03 | No | Not installed | Must install: `pip3 install python-dotenv>=1.0` |
| pytest | Test suite | No | Not installed | Must install: `pip3 install pytest` |
| PostgreSQL server | DB-01 through DB-04 | Yes | 17.6 at `/Library/PostgreSQL/17/` (localhost:5432, accepting connections) | — |
| psql CLI | Schema management | Available via full path | `/Library/PostgreSQL/17/bin/psql` | Add to PATH or use full path in commands |

**Missing dependencies with no fallback:**
- psycopg2-binary: install with `pip3 install "psycopg2-binary>=2.9"`
- python-dotenv: install with `pip3 install "python-dotenv>=1.0"`
- pytest: install with `pip3 install pytest`

**Missing dependencies with fallback:**
- None

**PATH note:** `/Library/PostgreSQL/17/bin/` is not in the default shell PATH. Commands in the plan should use the full path `/Library/PostgreSQL/17/bin/psql` or the plan should include a PATH export step.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (latest) |
| Config file | `pytest.ini` or `pyproject.toml` — none exists yet, Wave 0 creates it |
| Quick run command | `python3 -m pytest tests/test_parser.py -x -q` |
| Full suite command | `python3 -m pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PARS-01 | Parser extracts liga from signal message | unit | `python3 -m pytest tests/test_parser.py::test_parse_liga -x` | Wave 0 |
| PARS-02 | Parser extracts entrada from signal message | unit | `python3 -m pytest tests/test_parser.py::test_parse_entrada -x` | Wave 0 |
| PARS-03 | Parser extracts horario from signal message | unit | `python3 -m pytest tests/test_parser.py::test_parse_horario -x` | Wave 0 |
| PARS-04 | Parser extracts resultado from edited message | unit | `python3 -m pytest tests/test_parser.py::test_parse_resultado -x` | Wave 0 |
| PARS-05 | Parser extracts placar when present | unit | `python3 -m pytest tests/test_parser.py::test_parse_placar -x` | Wave 0 |
| PARS-06 | raw_text is always populated | unit | `python3 -m pytest tests/test_parser.py::test_raw_text_always_stored -x` | Wave 0 |
| PARS-07 | Parser returns None for unrecognized messages | unit | `python3 -m pytest tests/test_parser.py::test_parse_returns_none_for_garbage -x` | Wave 0 |
| LIST-04 | Listener ignores messages without text | unit | `python3 -m pytest tests/test_parser.py::test_empty_text_returns_none -x` | Wave 0 |
| DB-02 | Upsert inserts new signal without error | integration | Manual — requires live PostgreSQL | N/A |
| DB-03 | Upsert updates resultado on edit | integration | Manual — requires live PostgreSQL | N/A |
| DB-04 | asyncio.to_thread does not raise | integration | Manual — tested by running listener | N/A |
| OPER-02 | .session not tracked by git | smoke | `git ls-files \| grep -c .session` == 0 | Wave 0 |
| OPER-03 | Missing .env var causes clean exit | unit | `python3 -m pytest tests/test_config.py::test_missing_var_raises -x` | Wave 0 |
| TERM-03 | Ctrl+C exits cleanly | manual | Run `python listener.py`, send SIGINT, verify no traceback | N/A |

### Sampling Rate

- **Per task commit:** `python3 -m pytest tests/test_parser.py -x -q`
- **Per wave merge:** `python3 -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_parser.py` — covers PARS-01 through PARS-07, LIST-04
- [ ] `tests/test_config.py` — covers OPER-03
- [ ] `tests/conftest.py` — shared fixtures (sample message strings)
- [ ] `pytest.ini` or `pyproject.toml [tool.pytest.ini_options]` — test discovery config
- [ ] Package installs: `pip3 install "telethon~=1.42" --upgrade "psycopg2-binary>=2.9" "python-dotenv>=1.0" pytest`

---

## Sources

### Primary (HIGH confidence)

- Telethon official docs 1.42.0 — https://docs.telethon.dev/en/stable/modules/events.html (events.NewMessage, events.MessageEdited, client.start, run_until_disconnected)
- Telethon PyPI — https://pypi.org/project/Telethon/ (version 1.42.0 confirmed as latest)
- psycopg2 official docs — https://www.psycopg.org/docs/install.html (binary package guidance)
- PostgreSQL 17 on machine — `/Library/PostgreSQL/17/bin/pg_isready` returns "accepting connections" on localhost:5432
- Project research files in `.planning/research/` — STACK.md, ARCHITECTURE.md, PITFALLS.md, FEATURES.md (all researched 2026-04-02)

### Secondary (MEDIUM confidence)

- CLAUDE.md technology stack table — version pins and rationale verified against PyPI
- STATE.md accumulated decisions — asyncio/psycopg2 boundary, upsert write path, two-process model
- ARCHITECTURE.md build order — verified consistent with requirement dependencies

### Tertiary (LOW confidence)

- Parser regex patterns — not yet verifiable; depends on real message capture from the group (flagged in Open Questions)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified on PyPI, PostgreSQL confirmed running
- Architecture: HIGH — patterns sourced from official Telethon docs + psycopg2 docs + prior project research
- Parser patterns: LOW — regex cannot be verified until real messages are captured from the group
- Pitfalls: HIGH — sourced from official Telethon GitHub issues + psycopg2 blocking asyncio is well-documented

**Research date:** 2026-04-02
**Valid until:** 2026-05-02 (stable stack; Telethon 1.x is not actively changing)
