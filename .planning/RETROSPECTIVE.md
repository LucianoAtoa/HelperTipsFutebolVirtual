# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-04-03
**Phases:** 4 | **Plans:** 18 | **Tasks:** 26

### What Was Built
- Pipeline completo Telegram → PostgreSQL: listener Telethon, parser regex, store com upsert, schema com 4 tabelas
- Dashboard web Plotly Dash: dark theme, 5 KPI cards, 3 filtros, ROI com Gale, AG Grid com histórico
- Sistema de mercados complementares: 14 entradas com validação por placar, Martingale, ROI breakdown
- 3 abas de analytics: heatmap temporal, equity curve, gale analysis, streaks, volume, cross-dimensional
- Badge de cobertura do parser com modal de falhas

### What Worked
- TDD-first para parser e queries — testes escritos antes do código aceleraram desenvolvimento
- Separação clara de camadas (parser → store → queries → dashboard) — cada módulo testável isoladamente
- Inserção de Phase 2.1 mid-milestone sem interrupção — decimal numbering funcionou bem
- Modo yolo com auto_advance acelerou execução sem perda de qualidade
- Pure-Python functions (calculate_roi, calculate_equity_curve, calculate_streaks) sem dependência de DB — testes rápidos

### What Was Inefficient
- Phase 2.1 Plan 04 (dashboard card) levou 79min — maior outlier do milestone, provavelmente por complexidade de callback Dash
- VERIFICATION.md nunca criado para Phase 2.1 — gerou gaps no audit que são apenas documentais
- Nyquist validation ficou em draft para todas as fases — processo adicionado mas nunca executado
- Alguns SUMMARY frontmatter sem requirements_completed — inconsistência entre planos

### Patterns Established
- `_build_where()` helper para construção de WHERE clauses parameterizadas — reutilizado em 9 query functions
- `_build_*_table()` helpers para renderização condicional de tabelas DBC
- Lazy render via `active_tab` gate em callbacks de abas — evita queries desnecessárias
- Processos separados: listener.py (asyncio/Telethon) + dashboard.py (Dash) — sem mixing de event loops
- store.py sync-only, chamado via `asyncio.to_thread()` no listener
- `validar_complementar()` retorna RED conservadoramente para regra desconhecida

### Key Lessons
1. Criar VERIFICATION.md para TODAS as fases, incluindo fases inseridas (decimal) — evita gaps documentais no audit
2. Parser regex deve ser escrito contra mensagens reais capturadas — não assumir formato baseado em documentação
3. Dashboard callbacks complexos (muitos Outputs) são o principal gargalo de tempo — considerar split em callbacks menores
4. ensure_schema() com seed idempotente (INSERT ... SELECT WHERE NOT EXISTS) é padrão confiável para tabelas de configuração

### Cost Observations
- Model mix: ~70% sonnet (subagents), ~30% opus (orchestration)
- Sessions: ~5 sessions across 2 days
- Notable: 18 plans em ~2.5 horas de execução efetiva — média de 8 min/plan

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | ~5 | 4 | First milestone — established TDD, layer separation, yolo mode |

### Cumulative Quality

| Milestone | Tests | LOC | Plans |
|-----------|-------|-----|-------|
| v1.0 | 132 | 5,050 | 18 |

### Top Lessons (Verified Across Milestones)

1. TDD-first com pure-Python functions acelera desenvolvimento e garante testabilidade
2. VERIFICATION.md é obrigatório para todas as fases — sem exceção
