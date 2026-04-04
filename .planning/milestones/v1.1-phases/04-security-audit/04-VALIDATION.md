---
phase: 4
slug: security-audit
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-03
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >= 7.0 |
| **Config file** | `pyproject.toml` — `[tool.pytest.ini_options]` |
| **Quick run command** | `python3 -m pytest tests/ -q` |
| **Full suite command** | `python3 -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/ -q`
- **After every plan wave:** Run `python3 -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | SEC-01 | smoke (bash) | `[ "$(git log --all --full-diff -p -- .env '*.session' \| wc -l \| tr -d ' ')" = "0" ]` | N/A — bash check | ⬜ pending |
| 04-01-02 | 01 | 1 | SEC-02 | unit | `python3 -m pytest tests/test_dashboard.py -k "debug" -x` | ✅ (criado em 04-01 Task 2) | ⬜ pending |
| 04-01-03 | 01 | 1 | SEC-03 | smoke (bash) | `grep "DASH_DEBUG" .env.example` | N/A — bash check | ⬜ pending |
| 04-02-01 | 02 | 1 | SEC-04 | smoke (bash) | `grep -E "Setup Local\|Deploy\|session" README.md` | N/A — bash check | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_dashboard.py` — `test_debug_mode_off_by_default` e `test_debug_mode_on_with_env` criados inline no plano 04-01 Task 2 (cobre SEC-02)

*Todos os outros requirements (SEC-01, SEC-03, SEC-04) sao verificacoes bash/smoke — nao requerem novos arquivos de teste.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| README.md legibilidade e completude | SEC-04 | Qualidade de documentacao requer revisao humana | Ler README.md e verificar se as 5 secoes obrigatorias estao presentes e claras |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved
