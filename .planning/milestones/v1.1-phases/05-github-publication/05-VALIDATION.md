---
phase: 5
slug: github-publication
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `pyproject.toml` → `[tool.pytest.ini_options]` |
| **Quick run command** | `python -m pytest tests/ -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~0.53 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -q`
- **After every plan wave:** Run `python -m pytest tests/ -v && ruff check .`
- **Before `/gsd:verify-work`:** Full suite must be green + CI green on GitHub
- **Max feedback latency:** ~1 second

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | GH-01 | bash smoke | `git check-ignore -v helpertips.session .env __pycache__ dummy.pyc` | N/A | pending |
| 05-01-02 | 01 | 1 | GH-01 | bash smoke | `gh repo view --json visibility -q '.visibility'` | N/A | pending |
| 05-02-01 | 02 | 1 | GH-02 | bash smoke | `test -f .github/workflows/ci.yml && cat .github/workflows/ci.yml` | ❌ Wave 0 | pending |
| 05-02-02 | 02 | 1 | GH-02 | bash smoke | `gh run list --limit 3` | N/A | pending |
| 05-02-03 | 02 | 1 | GH-02 | visual | `grep 'badge' README.md` | N/A | pending |

---

## Wave 0 Gaps

- [ ] `.github/workflows/ci.yml` — created by Plan 05-02 Task 1
- [ ] `[tool.ruff]` in `pyproject.toml` — linter config for CI
- [ ] Lint fixes: `ruff check --fix .` before first CI push

---

## Sign-Off

- [ ] All tasks have automated verify commands
- [ ] Wave 0 gaps resolved by plan tasks
- [ ] Sampling rate achievable within estimated runtime

**Approval:** pending
