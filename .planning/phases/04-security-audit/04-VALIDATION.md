---
phase: 4
slug: security-audit
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| 04-01-01 | 01 | 1 | SEC-01 | smoke (bash) | `git log --all --full-diff -p -- .env '*.session' \| wc -l` retorna 0 | N/A — bash check | ⬜ pending |
| 04-02-01 | 02 | 1 | SEC-02 | unit | `python3 -m pytest tests/test_dashboard.py -k "debug" -x` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 1 | SEC-03 | smoke (bash) | `grep "DASH_DEBUG" .env.example` | N/A — bash check | ⬜ pending |
| 04-02-03 | 02 | 1 | SEC-04 | smoke (bash) | `grep -E "Setup Local\|Deploy\|session" README.md` | N/A — bash check | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_dashboard.py` — adicionar `test_debug_mode_off_by_default` e `test_debug_mode_on_with_env` (cobre SEC-02)

*Todos os outros requirements (SEC-01, SEC-03, SEC-04) são verificações bash/smoke — não requerem novos arquivos de teste.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| README.md legibilidade e completude | SEC-04 | Qualidade de documentação requer revisão humana | Ler README.md e verificar se as 5 seções obrigatórias estão presentes e claras |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
