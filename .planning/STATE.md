---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Completed 03-04-PLAN.md — ANAL-03 gap fechado, table-periodo wired ao dashboard
last_updated: "2026-04-03T21:46:55.246Z"
last_activity: 2026-04-03
progress:
  total_phases: 4
  completed_phases: 4
  total_plans: 18
  completed_plans: 18
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-02)

**Core value:** Capturar automaticamente todos os sinais do Telegram e transformar em estatísticas confiáveis para tomada de decisão nas apostas.
**Current focus:** Phase 02 — core-dashboard

## Current Position

Phase: 02.1
Plan: Not started
Status: Executing Phase 02
Last activity: 2026-04-03

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**

- Total plans completed: 0
- Average duration: —
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 01-foundation P01 | 2min | 2 tasks | 7 files |
| Phase 01-foundation P02 | 2 | 2 tasks | 4 files |
| Phase 01-foundation P03 | 2min | 1 tasks | 2 files |
| Phase 01-foundation P04 | 4min | 2 tasks | 1 files |
| Phase 01-foundation P05 | 2min | 2 tasks | 9 files |
| Phase 01-foundation P06 | 5min | 2 tasks | 4 files |
| Phase 01-foundation P07 | 8min | 1 tasks | 6 files |
| Phase 02-core-dashboard P01 | 8min | 2 tasks | 3 files |
| Phase 02-core-dashboard P02 | 3min | 3 tasks | 2 files |
| Phase 02.1-market-config P01 | 8min | 2 tasks | 2 files |
| Phase 02.1-market-config P02 | 8 | 2 tasks | 2 files |
| Phase 02.1-market-config P03 | 2min | 2 tasks | 2 files |
| Phase 02.1-market-config P04 | 79min | 2 tasks | 1 files |
| Phase 03-analytics-depth P01 | 3min | 2 tasks | 2 files |
| Phase 03-analytics-depth P02 | 2min | 2 tasks | 2 files |
| Phase 03-analytics-depth P03 | 8min | 2 tasks | 2 files |
| Phase 03-analytics-depth P03 | 15min | 3 tasks | 2 files |
| Phase 03-analytics-depth P04 | 5min | 1 tasks | 2 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Init]: Telethon user-client (not Bot API) — required to listen to private group without admin rights
- [Init]: psycopg2 wrapped in asyncio.to_thread() — must not block event loop or signals drop silently
- [Init]: Two separate processes (listener.py + dashboard.py) — Telethon blocks asyncio loop, Dash blocks process; no single-process mixing
- [Init]: Upsert-only write path (ON CONFLICT) — no SELECT-then-INSERT; handles both new signals and result edits atomically
- [Phase 01-foundation]: Upgraded Telethon from 1.40.0 to 1.42.0 (required by CLAUDE.md pin ~=1.42)
- [Phase 01-foundation]: validate_config() collects ALL missing vars before raising SystemExit — better UX than fail-on-first
- [Phase 01-foundation]: LIGA field is the signal gate in parser.py — returns None immediately if no LIGA match, preventing non-signal messages from being stored
- [Phase 01-foundation]: parser.py imports only re and datetime (stdlib) — zero external deps ensures listener integration requires no additional packages
- [Phase 01-foundation]: store.py is sync-only with no asyncio/telethon imports — listener.py wraps calls in asyncio.to_thread() per DB-04
- [Phase 01-foundation]: ON CONFLICT WHERE clause prevents overwriting GREEN/RED resultado with NULL — signals.resultado IS DISTINCT FROM EXCLUDED.resultado OR signals.resultado IS NULL
- [Phase 01-foundation]: validate_config() moved inside main() to allow safe module imports without .env — fail-fast preserved as first action in main()
- [Phase 01-foundation]: TelegramClient created inside main() with event handlers as nested decorator closures — requires env vars only at runtime
- [Phase 01-foundation]: Used setuptools.build_meta as build-backend (plan had invalid setuptools.backends._legacy:_Backend for setuptools 82)
- [Phase 01-foundation]: Removed pytest.ini — configuration migrated to pyproject.toml [tool.pytest.ini_options] (single config file)
- [Phase 01-foundation]: All inter-module imports use from helpertips.X import Y — no relative imports, no sys.path manipulation
- [Phase 01-foundation]: get_stats() changed return type from tuple to dict — enables named access to coverage and parse_failures count
- [Phase 01-foundation]: RichHandler replaces logging.basicConfig format string — all Telethon + helpertips logs rendered via rich
- [Phase 01-foundation]: log_parse_failure uses 'no_liga_match' reason — parser returns None only when LIGA regex fails
- [Phase 01-foundation]: Parser gate changed from LIGA_PATTERN to GATE_PATTERN (ExtremeTips|🏆 Liga:) — real messages always have group header
- [Phase 01-foundation]: tentativa field (SMALLINT, nullable) added to schema — captures which of 4 attempts triggered GREEN for future gale analysis
- [Phase 01-foundation]: horario is FIRST tentativa time (1️⃣ line), not a dedicated Horário: field — real format has no such label
- [Phase 01-foundation]: placar extracted from inline ✅ (X-Y) on tentativa line — real format does not use separate Placar: label
- [Phase 02-core-dashboard]: _build_where() helper centralizes WHERE clause construction — all query functions reuse it without duplication
- [Phase 02-core-dashboard]: calculate_roi is pure Python with no DB dependency — enables test-first development without PostgreSQL
- [Phase 02-core-dashboard]: get_distinct_values validates field name against frozenset allowlist before SQL interpolation — prevents SQL injection on column names
- [Phase 02-core-dashboard]: db_conn fixture truncates before AND after yield — test isolation against real listener data
- [Phase 02-core-dashboard]: received_at datetime objects converted to str() inside callback before returning rowData — psycopg2 returns Python datetime, AG Grid expects JSON-serializable values
- [Phase 02-core-dashboard]: Dash 4.x @callback decorator used at module level (not app.callback) — correct pattern for dashboard.py standalone module
- [Phase 02.1-market-config]: ensure_schema() usa INSERT ... SELECT com subquery VALUES para seed de complementares com FK — evita hardcode de IDs sequenciais
- [Phase 02.1-market-config]: Percentuais de complementares armazenados como NUMERIC(5,4) fração decimal (0.20 não 20) — fórmula multiplica diretamente sem divisão
- [Phase 02.1-market-config]: regra_validacao como TEXT enum-string (over_3_5, empate_3_3_4_4) — mapeado para lambdas em queries.py, nunca eval()
- [Phase 02.1-market-config]: empate_3_3_4_4 usa casa==fora AND total in (6,8) — exclui falsos-positivos como 2-4 ou 4-2
- [Phase 02.1-market-config]: validar_complementar retorna RED conservadoramente para regra desconhecida — sem excecao
- [Phase 02.1-market-config]: D-08 e D-09 implementados: principal RED propaga RED; principal None propaga None para complementares
- [Phase 02.1-market-config]: calculate_roi_complementares usa mesmo padrao de Gale que calculate_roi mas com stake_base = stake * percentual — consistencia com funcao existente
- [Phase 02.1-market-config]: Decimal do PostgreSQL convertido para float() antes de calculos em calculate_roi_complementares — evita TypeError silencioso com NUMERIC(5,4)
- [Phase 02.1-market-config]: Card ROI Complementares inserido apos card ROI Principal no layout; Output adicionado ao final do master callback; ROI Total Combinado calculado inline
- [Phase 03-analytics-depth]: calculate_equity_curve e calculate_streaks sao funcoes puras Python sem DB — seguem padrao de calculate_roi()
- [Phase 03-analytics-depth]: Heatmap inicializado com None (nao 0) — distingue 'sem dados' de win_rate real de 0% no go.Heatmap
- [Phase 03-analytics-depth]: get_winrate_by_periodo usa mesmo padrao WHERE periodo IS NOT NULL que get_gale_analysis usa para tentativa IS NOT NULL
- [Phase 03-analytics-depth]: db_conn fixture atualizada para limpar parse_failures entre testes alem de signals
- [Phase 03-analytics-depth]: update_tabs usa lazy render via active_tab gate — abas inativas retornam no_update para evitar queries desnecessarias
- [Phase 03-analytics-depth]: toggle_modal usa ctx.triggered_id para distinguir badge click vs btn-close — padrao canonico Dash 4.x
- [Phase 03-analytics-depth]: update_tabs usa lazy render via active_tab gate — abas inativas retornam no_update para evitar queries desnecessarias
- [Phase 03-analytics-depth]: toggle_modal usa ctx.triggered_id para distinguir badge click vs btn-close — padrao canonico Dash 4.x
- [Phase 03-analytics-depth]: Badge de cobertura sempre global sem filtros — get_stats() no master callback, nao no callback de abas
- [Phase 03-analytics-depth]: table-periodo card posicionado entre graph-volume e table-cross-dimensional — ordem logica: volume -> periodo -> cross-dimensional
- [Phase 03-analytics-depth]: _build_periodo_table helper segue padrao de _build_cross_table — recebe list[dict] e retorna dbc.Table ou html.P condicionalmente

### Pending Todos

None yet.

### Roadmap Evolution

- Phase 02.1 inserted after Phase 2: Configuração de mercados e entradas complementares com validação independente de GREEN/RED (INSERTED)

### Blockers/Concerns

- [Phase 1 — Research flag]: Parser regex must be written against real captured messages. Capture 10–20 real messages before finalizing the parser. Format assumed from general virtual football group patterns.
- [Phase 3 — Research flag]: ANAL-06 (streak tracking) and ANAL-07 (gale analysis) require 100+ signals to be meaningful. Validate data volume before planning Phase 3.

## Session Continuity

Last session: 2026-04-03T21:25:17.444Z
Stopped at: Completed 03-04-PLAN.md — ANAL-03 gap fechado, table-periodo wired ao dashboard
Resume file: None
