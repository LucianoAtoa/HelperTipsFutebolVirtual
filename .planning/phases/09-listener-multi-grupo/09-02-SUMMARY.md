---
phase: 09-listener-multi-grupo
plan: 02
subsystem: listener
tags: [telethon, asyncio, multi-grupo, telegram, env-config]

# Dependency graph
requires:
  - phase: 09-01
    provides: "Schema signals com group_id NOT NULL, UNIQUE(group_id, message_id), store.upsert_signal aceita group_id"
provides:
  - "listener.py multi-grupo: TELEGRAM_GROUP_IDS (CSV) com fallback TELEGRAM_GROUP_ID"
  - "Verificacao de acesso por grupo via get_entity loop no startup"
  - "Handler unico registrado com add_event_handler(chats=[group_ids]) apos filtragem"
  - "parsed['group_id'] = event.chat_id adicionado antes do upsert"
  - "print_startup_summary aceita lista de titulos (multi-grupo)"
  - ".env.example atualizado com TELEGRAM_GROUP_IDS"
  - "tests/test_queries.py: INSERTs diretos atualizados com group_id"
affects: [10-dashboard-redesign, deploy-scripts]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "client.add_event_handler() para registro dinamico de handler apos filtragem de grupos invalidos"
    - "Fallback de env var: os.environ.get('TELEGRAM_GROUP_IDS') or os.environ.get('TELEGRAM_GROUP_ID', '')"
    - "group_ids como lista de ints parseada de CSV — suporta 1..N grupos no mesmo processo"

key-files:
  created: []
  modified:
    - "helpertips/listener.py"
    - ".env.example"
    - "tests/test_queries.py"

key-decisions:
  - "Handler registrado via add_event_handler (nao decorator) para permitir registro apos filtragem dinamica de group_ids"
  - "Fallback para TELEGRAM_GROUP_ID garante compatibilidade retroativa (D-14) sem breaking change"
  - "group_id do signal = event.chat_id (nao lookup separado) — eficiente e correto por design do Telethon"
  - "Startup aborta se nenhum grupo valido (apos filtragem de invalidos) para evitar listener silencioso"

patterns-established:
  - "Multi-group listener: parse CSV env var -> verificar acesso -> registrar handler com lista"
  - "Test INSERT direto: sempre incluir group_id para compatibilidade com schema NOT NULL"

requirements-completed: [LIST-01, LIST-02]

# Metrics
duration: 8min
completed: 2026-04-04
---

# Phase 09 Plan 02: Listener Multi-Grupo Summary

**listener.py adaptado para escutar Over 2.5 e Ambas Marcam simultaneamente via TELEGRAM_GROUP_IDS (CSV), com verificacao de acesso por grupo, handler unico via add_event_handler e event.chat_id como group_id no upsert**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-04T13:24:00Z
- **Completed:** 2026-04-04T13:32:37Z
- **Tasks:** 1 (+ 1 desvio auto-corrigido)
- **Files modified:** 3

## Accomplishments

- listener.py agora parseia `TELEGRAM_GROUP_IDS=id1,id2` do .env com fallback para `TELEGRAM_GROUP_ID` (D-14)
- Startup verifica acesso a cada grupo individualmente via `get_entity(gid)`, remove invalidos, aborta se nenhum valido
- Handler unico registrado com `client.add_event_handler(chats=group_ids)` apos filtragem, capturando group_ids por closure
- `parsed['group_id'] = event.chat_id` garante que cada signal vai para o grupo correto no upsert
- `print_startup_summary` aceita lista de strings (`group_titles`) e junta com `', '.join()`
- `.env.example` atualizado: `TELEGRAM_GROUP_IDS=` com comentario de fallback deprecado
- Suite de 150 testes verde apos correcao de INSERTs diretos em `test_queries.py`

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: Listener multi-grupo + .env.example** - `c9e550e` (feat)

## Files Created/Modified

- `helpertips/listener.py` - Refatorado para multi-grupo: TELEGRAM_GROUP_IDS, add_event_handler, event.chat_id, group_titles list
- `.env.example` - TELEGRAM_GROUP_ID substituido por TELEGRAM_GROUP_IDS com fallback documentado
- `tests/test_queries.py` - Todos os INSERTs diretos na tabela signals atualizados para incluir group_id

## Decisions Made

- Handler registrado via `client.add_event_handler()` (nao `@client.on`) para permitir definicao da funcao e registro APOS a lista `group_ids` estar finalizada (filtragem de invalidos feita no loop `get_entity`).
- `event.chat_id` como source de `group_id` no dict do signal — direto, sem lookup adicional, correto pelo Telethon design.
- Fallback `os.environ.get('TELEGRAM_GROUP_ID')` mantido para zero breaking change em instancias existentes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrigidos INSERTs diretos em test_queries.py sem group_id**
- **Found during:** Task 1 (verificacao: `python3 -m pytest tests/ -x -q`)
- **Issue:** Schema atualizado no Plan 01 tornou `group_id` NOT NULL, mas `_insert_signal()` e varios `cur.execute("INSERT INTO signals ...")` em `test_queries.py` nao incluiam `group_id`, causando `NotNullViolation` e falha de 13+ testes.
- **Fix:** Adicionado `group_id=-1001000000001` (ID de teste fixo) em `_make_signal_dict()` e em todos os INSERTs diretos ao longo do arquivo (12 sites afetados).
- **Files modified:** `tests/test_queries.py`
- **Verification:** `python3 -m pytest tests/ -q` — 150 passed in 1.36s
- **Committed in:** `c9e550e` (parte do commit da Task 1)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug em testes causado por schema change do Plan 01)
**Impact on plan:** Fix necessario para suite verde (criterio de aceitacao do plano). Sem scope creep.

## Issues Encountered

- `test_queries.py` tinha 12+ INSERTs diretos sem `group_id` — todos corrigidos com ID de grupo de teste fixo `-1001000000001`.

## User Setup Required

Nenhuma configuracao externa necessaria.

Para ativar multi-grupo na EC2:
1. Obter o Group ID do grupo "Ambas Marcam" via `python3 -m helpertips.list_groups`
2. Atualizar `.env` na EC2: `TELEGRAM_GROUP_IDS=<over_id>,<ambas_id>`
3. Reiniciar: `sudo systemctl restart helpertips-listener`

(Pendente: Group ID do grupo Ambas Marcam ainda nao obtido — ver Pending Todos em STATE.md)

## Next Phase Readiness

- listener.py multi-grupo pronto para receber sinais de Over 2.5 e Ambas Marcam simultaneamente
- store.upsert_signal ja aceita group_id (Plan 01) — integracao completa
- Phase 10 (dashboard-redesign) pode comecar: schema e listener estao estabilizados

---
*Phase: 09-listener-multi-grupo*
*Completed: 2026-04-04*
