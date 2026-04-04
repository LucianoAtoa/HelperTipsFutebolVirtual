---
phase: 09-listener-multi-grupo
plan: 01
subsystem: database
tags: [postgresql, psycopg2, schema-migration, multi-group, mercados, upsert]

# Dependency graph
requires: []
provides:
  - "Coluna group_id BIGINT na tabela signals (migration idempotente)"
  - "Coluna mercado_id INTEGER FK para tabela mercados na tabela signals"
  - "Constraint UNIQUE(group_id, message_id) substituindo UNIQUE(message_id)"
  - "_resolve_mercado_id() mapeando string de entrada para mercado_id"
  - "ENTRADA_PARA_MERCADO_ID dicionário com Over 2.5 -> 1, Ambas Marcam -> 2"
  - "upsert_signal atualizado com ON CONFLICT(group_id, message_id)"
  - "Seed de mercados com IDs fixos (id=1 over_2_5, id=2 ambas_marcam)"
affects: [09-02, listener, store, dashboard]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Migration idempotente via ALTER TABLE ... ADD COLUMN IF NOT EXISTS"
    - "Seed com IDs fixos via INSERT OVERRIDING SYSTEM VALUE para garantir FK hardcoded"
    - "ON CONFLICT (group_id, message_id) para deduplicação multi-grupo"
    - "_resolve_mercado_id: lookup por dicionário normalizado (lower().strip())"

key-files:
  created: []
  modified:
    - helpertips/db.py
    - helpertips/store.py
    - tests/test_store.py
    - tests/test_db.py

key-decisions:
  - "IDs fixos nos seeds de mercados (1=over_2_5, 2=ambas_marcam) via OVERRIDING SYSTEM VALUE para compatibilidade com ENTRADA_PARA_MERCADO_ID hardcoded"
  - "mercado_id=NULL permitido no schema (NOT NULL não aplicado) para sinais com entrada desconhecida"
  - "_resolve_mercado_id registra warning mas não rejeita entradas desconhecidas (D-06)"
  - "Constraint UNIQUE(group_id, message_id) permite mesmo message_id em grupos diferentes (LIST-01)"

patterns-established:
  - "Migration idempotente: ADD COLUMN IF NOT EXISTS + DO $$ BEGIN IF NOT EXISTS ... END $$"
  - "UPDATE retroativo: group_id NULL -> valor de TELEGRAM_GROUP_IDS env var ao rodar ensure_schema()"

requirements-completed: [LIST-01, LIST-02]

# Metrics
duration: 15min
completed: 2026-04-04
---

# Phase 9 Plan 1: Schema Migration Multi-Grupo Summary

**Migration idempotente PostgreSQL com group_id + mercado_id em signals, constraint composta UNIQUE(group_id, message_id) e store._resolve_mercado_id() mapeando entrada para FK de mercado**

## Performance

- **Duration:** 15 min
- **Started:** 2026-04-04T13:10:00Z
- **Completed:** 2026-04-04T13:25:31Z
- **Tasks:** 1 (TDD: RED -> GREEN)
- **Files modified:** 4

## Accomplishments

- Migration idempotente adicionou group_id BIGINT e mercado_id INTEGER FK à tabela signals
- Constraint composta UNIQUE(group_id, message_id) garante deduplicação por grupo (LIST-01)
- ENTRADA_PARA_MERCADO_ID e _resolve_mercado_id() adicionados ao store com lookup normalizado
- upsert_signal atualizado com ON CONFLICT(group_id, message_id) e mercado_id no DO UPDATE
- Seed de mercados com IDs fixos via OVERRIDING SYSTEM VALUE garante FK hardcoded confiável
- 12 novos testes (6 unitários _resolve_mercado_id, 3 integração upsert, 3 migration): 28 total passando

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: Migration SQL + store._resolve_mercado_id + upsert atualizado** - `bd7ae68` (feat, TDD GREEN)

**Plan metadata:** (a ser adicionado após commit de docs)

_Nota: Task TDD executada com RED phase (testes falhando) seguida de GREEN phase (implementação)._

## Files Created/Modified

- `helpertips/db.py` - Migration Phase 09: ADD COLUMN group_id/mercado_id, constraint composta, índices, seed com IDs fixos
- `helpertips/store.py` - ENTRADA_PARA_MERCADO_ID, _resolve_mercado_id(), upsert atualizado ON CONFLICT(group_id, message_id)
- `tests/test_store.py` - _make_signal com group_id=99999, 6 testes _resolve_mercado_id, 3 testes upsert multi-grupo
- `tests/test_db.py` - 3 testes de migration (group_id, mercado_id, idempotência)

## Decisions Made

- **IDs fixos nos mercados:** ENTRADA_PARA_MERCADO_ID usa IDs hardcoded (1=over_2_5, 2=ambas_marcam). Para garantir compatibilidade, seed alterado para INSERT OVERRIDING SYSTEM VALUE com IDs explícitos. Alternativa (lookup dinâmico no banco) descartada por adicionar acoplamento e uma query extra por upsert.
- **mercado_id NULL permitido:** Sinais com entrada desconhecida inserem com mercado_id=NULL em vez de rejeitar (D-06). Simples, não bloqueia captura.
- **_make_signal padrão group_id=99999:** Testes existentes não precisaram ser reescritos — o default 99999 é aceito pelo schema sem conflito.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Seed de mercados com IDs fixos via OVERRIDING SYSTEM VALUE**
- **Found during:** Task 1 (GREEN phase — execução dos testes)
- **Issue:** O banco de desenvolvimento já tinha mercados com id=3225/3226 (SERIAL auto-incrementado). _resolve_mercado_id retorna id=1 e id=2 hardcoded. ForeignKeyViolation ao tentar inserir signal com mercado_id=1 quando o banco tinha over_2_5 com id=3225.
- **Fix:** Alterado seed em db.py para usar `INSERT INTO mercados (id, slug, ...) OVERRIDING SYSTEM VALUE VALUES (1, ...), (2, ...)` garantindo IDs fixos após qualquer DELETE+reinsert.
- **Files modified:** helpertips/db.py
- **Verification:** Após DELETE FROM mercados + ensure_schema(), mercados têm id=1 e id=2. Todos os 28 testes passam.
- **Committed in:** bd7ae68 (Task 1 commit)

**2. [Rule 1 - Bug] Linha duplicada `OR signals.resultado IS NULL` removida do upsert**
- **Found during:** Task 1 (análise do código existente em store.py)
- **Issue:** store.py tinha `OR signals.resultado IS NULL` duplicado duas vezes no WHERE clause do upsert, o que é inofensivo mas indica bug de copiar/colar.
- **Fix:** Removida linha duplicada — a cláusula WHERE agora tem apenas `EXCLUDED.resultado IS NOT NULL OR signals.resultado IS NULL`.
- **Files modified:** helpertips/store.py
- **Committed in:** bd7ae68 (Task 1 commit, já estava planejado no PLAN.md action)

---

**Total deviations:** 2 auto-fixed (2 Rule 1 - Bug)
**Impact on plan:** Fix 1 necessário para corretude da FK constraint com IDs hardcoded. Fix 2 era bug existente removido conforme indicado no PLAN.md. Sem scope creep.

## Issues Encountered

- ForeignKeyViolation no primeiro run dos testes: mercado_id=1 não existia no banco de dev (IDs eram 3225/3226 por SERIAL). Resolvido via seed com IDs explícitos — veja Deviations acima.

## User Setup Required

Nenhum. A migration é automática via `ensure_schema()`. Em produção (EC2), o próximo deploy que executar o listener ou o dashboard chamará `ensure_schema()` automaticamente:
- Se `TELEGRAM_GROUP_IDS` estiver configurado: dados históricos receberão group_id do primeiro grupo da lista via UPDATE retroativo.
- Se `TELEGRAM_GROUP_ID` (legado) estiver configurado: usado como fallback.
- Se nenhum estiver configurado: group_id permanece NULL até reinserção (constraint NOT NULL não aplicada).

## Next Phase Readiness

- Schema pronto: group_id, mercado_id, constraint composta funcionando
- store._resolve_mercado_id e upsert atualizado prontos para o listener multi-grupo (Plan 09-02)
- 28 testes passando (16 existentes + 12 novos)
- Pendente: configurar TELEGRAM_GROUP_IDS no .env da EC2 com o Group ID do grupo Ambas Marcam

## Self-Check: PASSED

- helpertips/db.py: FOUND
- helpertips/store.py: FOUND
- tests/test_store.py: FOUND
- tests/test_db.py: FOUND
- 09-01-SUMMARY.md: FOUND
- Commit bd7ae68: FOUND
- 28 testes passando: CONFIRMED

---
*Phase: 09-listener-multi-grupo*
*Completed: 2026-04-04*
