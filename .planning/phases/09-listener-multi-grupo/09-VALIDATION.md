---
phase: 9
slug: listener-multi-grupo
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-04
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.0+ |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `python3 -m pytest tests/test_parser.py tests/test_config.py tests/test_store.py -x -q` |
| **Full suite command** | `python3 -m pytest tests/ -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/test_parser.py tests/test_config.py tests/test_store.py -x -q`
- **After every plan wave:** Run `python3 -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | LIST-01 | unit | `python3 -m pytest tests/test_config.py -x -q` | Parcial | ⬜ pending |
| 09-01-02 | 01 | 1 | LIST-01 | integration | `python3 -m pytest tests/test_store.py -x -q` | Parcial | ⬜ pending |
| 09-01-03 | 01 | 1 | LIST-01 | integration | `python3 -m pytest tests/test_store.py::test_upsert_two_groups_same_message_id -x` | ❌ W0 | ⬜ pending |
| 09-01-04 | 01 | 1 | LIST-01 | integration | `python3 -m pytest tests/test_db.py -x -q` | Parcial | ⬜ pending |
| 09-02-01 | 02 | 1 | LIST-02 | unit | `python3 -m pytest tests/test_store.py::test_resolve_mercado_id -x` | ❌ W0 | ⬜ pending |
| 09-02-02 | 02 | 1 | LIST-02 | unit | `python3 -m pytest tests/test_store.py::test_resolve_mercado_id_unknown -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_store.py::test_upsert_two_groups_same_message_id` — stubs for LIST-01 (deduplicação multi-grupo)
- [ ] `tests/test_store.py::test_resolve_mercado_id` — stubs for LIST-02 (normalização entrada → mercado_id)
- [ ] `tests/test_store.py::test_resolve_mercado_id_unknown` — stubs for LIST-02 (entrada desconhecida → NULL)

*Existing infrastructure covers framework and fixtures — only new test stubs needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Listener conecta e recebe de 2 grupos | LIST-01 | Requer credenciais Telegram e acesso aos grupos reais | SSH no EC2, configurar TELEGRAM_GROUP_IDS, observar logs |
| Group ID do grupo Ambas Marcam | LIST-01 | Requer listagem interativa via Telethon no EC2 | `python3 -m helpertips.list_groups` no EC2 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
