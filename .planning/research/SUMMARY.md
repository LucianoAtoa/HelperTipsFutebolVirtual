# Project Research Summary

**Project:** HelperTips — Futebol Virtual (Telegram Signal Capture + Betting Analytics Dashboard)
**Domain:** Telegram user-client listener + PostgreSQL signal store + Python analytics dashboard
**Researched:** 2026-04-02
**Confidence:** HIGH

## Executive Summary

HelperTips is a personal analytics tool for capturing and analyzing virtual football betting signals from a private Telegram group. The architecture follows a three-layer pipeline: an async Telethon listener captures raw messages and result edits, a stateless regex parser structures them into typed records, and a PostgreSQL database persists them via upsert. A read-only Plotly Dash dashboard then surfaces win rates, ROI simulations, and multi-dimensional filters over that data. Research confirms this is a well-trodden domain — comparable platforms (betr.pro, greenvirtual.com.br, Smartbet.io) validate the feature set. The technology choices are mature and low-risk individually, but their combination introduces one concrete async/sync integration hazard that must be resolved in Phase 1.

The recommended approach is to build and validate the listener pipeline before touching the dashboard. The listener is the irreplaceable core: if it drops messages, all downstream analytics are silently wrong. Once signals are flowing reliably into PostgreSQL, the dashboard is additive and can be extended incrementally without touching the data model. Plotly Dash is the correct framework choice for this problem — it handles multi-filter interactive analytics in pure Python, without the complexity of a JavaScript frontend or the weak callback model of Streamlit. Two separate processes (listener.py and dashboard.py) sharing a single PostgreSQL database is the recommended process model for fault isolation.

The primary risk is data integrity at the listener layer. Three pitfalls directly threaten it: psycopg2 blocking the asyncio event loop (silent message drops), missing messages during downtime (no automatic gap recovery in Telethon), and regex parser failures that store corrupt or null records silently. All three must be mitigated in Phase 1 before the data is trusted enough to build a dashboard on. Secondary risks — small-sample statistical overconfidence in the dashboard, Telegram session security — are real but lower urgency and map naturally to Phase 2 hardening.

---

## Key Findings

### Recommended Stack

The stack is deliberately minimal for a personal single-user tool. Telethon 1.42.0 (user-client MTProto) is the only viable path into a private Telegram group — bots cannot join without admin rights. psycopg2-binary handles PostgreSQL writes with zero build-tooling overhead; sync I/O is acceptable at the write frequency of this use case (tens of signals per day) provided writes are wrapped in `asyncio.to_thread()` to avoid blocking the event loop. Plotly Dash 4.1.0 with dash-bootstrap-components 2.0 delivers the full analytics dashboard in pure Python. Python 3.12+ is required to support all dependencies cleanly. See [STACK.md](.planning/research/STACK.md) for full rationale and version pinning strategy.

**Core technologies:**
- **Telethon 1.42.0**: Telegram user-client listener — only library that can join private groups without admin rights; native `events.MessageEdited` support covers the result-update pattern
- **psycopg2-binary 2.9.x**: PostgreSQL sync driver — zero build dependencies, appropriate for low-write personal tool, must be wrapped in `asyncio.to_thread()` in event handlers
- **PostgreSQL 16**: Relational store — JSONB for raw metadata, UNIQUE constraint on `message_id` enables atomic upsert deduplication, window functions support ROI/streak analytics
- **Plotly Dash 4.1.0 + dash-bootstrap-components 2.0**: Analytics dashboard — pure-Python multi-filter interactive charts, no JavaScript required, Bootstrap 5 responsive layout
- **python-dotenv 1.x**: Configuration — keeps `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, and DB credentials out of source code
- **Python 3.12+**: Runtime — supported by all dependencies, best performance and error messages in current stable

**Critical version/integration note:** Dash and Telethon must run in separate processes. Telethon's `client.run_until_disconnected()` blocks the asyncio loop; Dash's `app.run()` blocks the process. Do not attempt to run both in the same process.

### Expected Features

Research across five comparable betting analytics platforms confirms a clear division between table stakes and differentiators for this domain. See [FEATURES.md](.planning/research/FEATURES.md) for full feature tree and dependency graph.

**Must have (table stakes) — MVP:**
- Signal capture in real time (Telethon NewMessage + MessageEdited)
- Deduplication — ON CONFLICT upsert; without this, stats are meaningless
- Result tracking (GREEN / RED) from edit events
- Total signal count + win rate — first thing any bettor checks
- ROI simulation with fixed stake — baseline profitability question
- Filter by liga (league) and filter by entrada (bet type)
- Signal history list (paginated, filterable)
- Pending signals view (NULL resultado, excluded from win-rate denominator)
- Terminal startup summary — validates pipeline is running before dashboard is built

**Should have (differentiators) — v1.1 after MVP validation:**
- Win rate by time of day (horario heatmap) — tests RNG cycle hypothesis
- Win rate by day of week (dia_semana)
- Win rate by period (1T / 2T / FT)
- Equity curve chart (cumulative bankroll over time)
- Cross-dimensional analysis (liga + entrada + periodo combined filter)
- Signal volume chart by day/week
- Raw message viewer (for parser debugging)

**Defer to v2+:**
- Streak tracking — requires 100+ signals to be meaningful; add after data accumulates
- Gale analysis — requires schema changes for sequence grouping; validate demand first
- Parser coverage rate in dashboard — useful but low priority vs. actual signal data

**Anti-features (explicitly out of scope):** bet automation, multi-group support, odds tracking (not in Telegram messages), Kelly Criterion, social features, predictive/AI scoring, real-time WebSocket push.

### Architecture Approach

The system is three pipeline stages (Listener → Parser → Store) feeding one read-only consumer (Dashboard), deployed as two separate processes sharing a PostgreSQL database. The Listener maintains the Telegram connection and routes raw text to the Parser. The Parser is a pure function (`parse_message(text: str) -> dict | None`) with zero database or Telethon imports — independently testable. The Store executes a single upsert path (`INSERT ... ON CONFLICT (message_id) DO UPDATE`) that handles both new signals and result edits without branching logic. The Dashboard API is strictly read-only. See [ARCHITECTURE.md](.planning/research/ARCHITECTURE.md) for component boundary rules, full SQL schema, and process model comparison.

**Major components:**
1. **Listener** — maintains persistent Telethon connection; receives NewMessage and MessageEdited events; calls Parser then Store; never touches SQL directly
2. **Parser** — stateless pure function; regex extraction of liga, entrada, horario, periodo, resultado, placar from raw text; returns structured dict or None on no-match
3. **Store** — repository layer; psycopg2 upsert to PostgreSQL; owns connection pool; wraps all calls in `asyncio.to_thread()` for event-loop safety
4. **PostgreSQL 16** — single source of truth; signals table with UNIQUE(message_id); indexes on liga, entrada, resultado, received_at
5. **Dashboard (Plotly Dash)** — read-only; callbacks drive filter interactions; connects directly to PostgreSQL for aggregate queries

**Recommended build order:** Schema → Parser → Store → Listener → Terminal stats → Dashboard. This order lets each layer be validated independently before the next is added.

### Critical Pitfalls

Research identified 5 critical pitfalls (data loss or rewrite risk) and 5 moderate/minor pitfalls. See [PITFALLS.md](.planning/research/PITFALLS.md) for full prevention patterns and detection methods.

1. **psycopg2 blocks the asyncio event loop** — wrap every DB call in `asyncio.to_thread()` from day one; failure causes silent message drops under burst traffic; must address in Phase 1
2. **`.session` file committed to git** — add `*.session` and `.env` to `.gitignore` before the first commit; session file is equivalent to handing over the Telegram account
3. **Duplicate records from edit events** — use upsert-only write path (ON CONFLICT); treating NewMessage and MessageEdited as independent INSERTs corrupts ROI stats; design into Phase 1 schema
4. **Regex parser fails silently** — store `raw_text` in every row; log every unmatched message with a warning; parse failures are invisible without explicit logging; Phase 1 requirement
5. **Messages missed while listener is offline** — add crash-recovery `try/except` in all event handlers; build a startup backfill utility that replays from last known `message_id`; Telethon's `catch_up=True` has documented bugs and should not be relied upon
6. **Session invalidated by concurrent process** (`AuthKeyDuplicatedError`) — use a process lock file and a distinctive session name; never run two scripts against the same session simultaneously

---

## Implications for Roadmap

Based on the dependency graph from ARCHITECTURE.md, the feature tree from FEATURES.md, and the phase-specific warnings from PITFALLS.md, the following phase structure is recommended.

### Phase 1: Foundation — Listener Pipeline + Data Model

**Rationale:** Everything downstream depends on signals landing correctly in PostgreSQL. Dashboard analytics are meaningless if the capture layer has data integrity problems. All 5 critical pitfalls from research are Phase 1 concerns. No dashboard work should begin until this phase is validated with real Telegram data.

**Delivers:** A running listener that captures signals and result edits from the VIP group, stores them in PostgreSQL via upsert, prints a startup stats summary, and can survive process restarts without data loss.

**Addresses:** Signal capture, deduplication, result tracking, startup terminal summary, data persistence across restarts (all table stakes from FEATURES.md).

**Avoids:** Pitfall 1 (asyncio blocking), Pitfall 2 (session collision), Pitfall 3 (offline message gap), Pitfall 4 (session in git), Pitfall 5 (silent parse failures), Pitfall 7 (duplicate records from edit events).

**Key implementation decisions from research:**
- `.gitignore` must include `*.session` and `.env` before first commit
- Parser is a separate module with unit tests and no external dependencies
- `asyncio.to_thread()` wraps every psycopg2 call in the listener
- Upsert is the only write path — no SELECT-then-INSERT patterns
- `raw_text` column stored on every row for re-parsing

### Phase 2: Core Dashboard — Aggregate Stats + Filtering

**Rationale:** Once the listener is producing clean data, the dashboard delivers the primary user value: answering "are these signals profitable?" The MVP dashboard is read-only SQL queries with filter UI — no complex analytics yet.

**Delivers:** A Plotly Dash dashboard showing win rate, total signals, pending count, ROI simulation with fixed stake, and filter controls for liga and entrada. Signal history list with pagination.

**Addresses:** Dashboard aggregate stats, filter by liga, filter by entrada, ROI simulation, signal history list (all MVP table stakes from FEATURES.md MVP recommendation).

**Uses:** Plotly Dash 4.1.0 + dash-bootstrap-components; read-only PostgreSQL queries; separate process from listener.

**Avoids:** Pitfall 6 (small-sample overconfidence) — add signal count annotation to every stat card from day one; Pitfall 8 (hardcoded filter strings) — all filter options loaded dynamically from `SELECT DISTINCT`.

### Phase 3: Analytics Depth — Dimensional Breakdown + Equity Curve

**Rationale:** After the MVP dashboard validates the pipeline with real data, add the differentiating analytics that go beyond generic bet trackers. These features require enough accumulated data (100+ signals) to be meaningful.

**Delivers:** Win rate broken down by horario (time-of-day heatmap), dia_semana, and periodo. Equity curve chart (running bankroll). Cross-dimensional filter (liga + entrada + periodo combined). Signal volume chart.

**Addresses:** All v1.1 differentiators from FEATURES.md.

**Avoids:** Pitfall 6 — sample-size warnings on every breakdown view.

### Phase 4: Reliability Hardening + Backfill Utility

**Rationale:** After the tool has been running in production and data is accumulating, invest in operational reliability. These are not blockers for value delivery but become important for long-term trust in the dataset.

**Delivers:** Startup backfill utility that replays missed messages from last known `message_id`. `FloodWaitError` handling with exact-second sleep. Connection pool cap for concurrent listener + dashboard DB access. Raw message viewer in dashboard for parser debugging.

**Addresses:** Pitfall 3 (offline message gap recovery), Pitfall 9 (account ban from aggressive API calls), Pitfall 10 (connection pool exhaustion).

### Phase 5: Advanced Analytics (v2, Demand-Validated)

**Rationale:** Streak tracking and gale analysis require sufficient historical data and confirmed user demand before investing in schema changes.

**Delivers:** Streak tracking (current and historical win/loss streaks by league/entry). Gale analysis (win rate at gale-1, gale-2, gale-3 levels). Parser coverage rate in dashboard.

**Addresses:** v2+ features from FEATURES.md — deferred until 300+ signals exist and demand is confirmed.

### Phase Ordering Rationale

- Schema and Parser come before Store and Listener because unit tests validate them without a running database or Telegram connection
- Listener is validated before dashboard because corrupt input data cannot be fixed by UI polish
- Core dashboard (Phase 2) precedes analytics depth (Phase 3) because descriptive stats need sample validation before cross-dimensional breakdown is meaningful
- Reliability hardening (Phase 4) comes after the tool proves its value in production rather than front-loading infrastructure
- Two-process deployment model (listener.py + dashboard.py) is the correct default from Phase 2 onwards — do not attempt single-process async/sync mixing

### Research Flags

Phases needing deeper research during planning:
- **Phase 1 — Parser:** Actual Telegram message format from the VIP group must be sampled before writing regex. Research was based on general virtual football group patterns. If message format differs significantly, regex patterns need adjustment. Capture 10–20 real messages before finalizing the parser.
- **Phase 4 — Backfill utility:** Telethon's `client.get_messages()` gap-filling behavior on private megagroups needs validation against the actual group type. GitHub issues document inconsistencies. Test with the real group before relying on it.

Phases with standard patterns (no additional research needed):
- **Phase 2 — Dashboard:** Plotly Dash callback patterns for multi-filter dashboards are well-documented with official examples
- **Phase 3 — Analytics queries:** GROUP BY and window function SQL patterns are standard; no domain-specific unknowns
- **Phase 5 — Gale analysis:** Requires product decision before implementation, not research

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All primary choices verified against official PyPI pages and documentation. Telethon 1.42.0 and Dash 4.1.0 confirmed current stable releases. |
| Features | HIGH (table stakes) / MEDIUM (differentiators) | Table stakes validated against 5 comparable platforms. Differentiators (horario heatmap, gale analysis) are domain-specific to virtual football groups — community-sourced, one primary Brazilian source (greenvirtual.com.br). |
| Architecture | HIGH | Core patterns (upsert, two-process model, pure-function parser) verified against official Telethon docs and PostgreSQL documentation. Build order validated by component dependency analysis. |
| Pitfalls | HIGH (async/session), MEDIUM (statistics) | Async/session pitfalls sourced from official Telethon docs and GitHub issues with confirmed issue numbers. Small-sample statistics pitfall sourced from betting analytics community blogs. |

**Overall confidence:** HIGH

### Gaps to Address

- **Actual message format:** The parser regex must be written against real captured messages from the VIP group. No external source could verify the exact format. Reserve a parser iteration after first real data is captured.
- **Group type (megagroup vs channel):** Backfill behavior differs. Confirm whether the VIP group is a Telegram megagroup or broadcast channel before implementing the gap-recovery utility.
- **Odds availability:** Research confirmed that virtual football signal messages typically do not include odds. If odds appear in the actual group's messages, the ROI model can be upgraded to yield-based ROI without schema changes (add an `odds` column).

---

## Sources

### Primary (HIGH confidence)
- Telethon official docs 1.42.0 — events, sessions, errors, FAQ: https://docs.telethon.dev/
- Telethon PyPI (version confirmation): https://pypi.org/project/Telethon/
- Plotly Dash 4.1.0 installation docs: https://dash.plotly.com/installation
- dash-bootstrap-components official: https://www.dash-bootstrap-components.com/
- psycopg2 official installation guidance (binary vs compiled): https://www.psycopg.org/docs/install.html
- PostgreSQL upsert (INSERT ON CONFLICT): https://www.geeksforgeeks.org/postgresql/postgresql-upsert/
- Telethon GitHub issues (AuthKeyDuplicatedError #1488, catch_up bugs #3041 #4535 #746 #1125)

### Secondary (MEDIUM confidence)
- greenvirtual.com.br — virtual football time filters, gale analysis, league breakdown features
- betr.pro — equity curves, P&L tracking, Telegram signal integration features
- Pikkit — cross-league performance, bet type filtering
- HeatCheck HQ betting analytics overview 2026: https://heatcheckhq.io/blog/best-sports-betting-analytics-tools-2026
- Streamlit vs Dash 2025: https://squadbase.dev/en/blog/streamlit-vs-dash-in-2025-comparing-data-app-frameworks
- psycopg2 vs asyncpg benchmark: https://www.tigerdata.com/blog/psycopg2-vs-psycopg3-performance-benchmark
- Betting small-sample statistics: https://www.predictology.co/blog/how-to-build-and-test-your-own-profitable-football-betting-systems/

### Tertiary (LOW confidence)
- Kelly Criterion as advanced feature: https://en.wikipedia.org/wiki/Kelly_criterion — used only to justify deferring it to v2+

---

*Research completed: 2026-04-02*
*Ready for roadmap: yes*
