---
phase: 8
slug: dashboard-proxy
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-04
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x + bash syntax check |
| **Config file** | `pytest.ini` or none |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | DEP-02 | unit | `bash -n deploy/06-setup-dashboard.sh` | N/A | ⬜ pending |
| 08-01-02 | 01 | 1 | DEP-02 | integration | `python3 -c "from helpertips.dashboard import server"` | N/A | ⬜ pending |
| 08-02-01 | 02 | 2 | DEP-03, DEP-04 | unit | `bash -n deploy/07-setup-nginx.sh` | N/A | ⬜ pending |
| 08-02-02 | 02 | 2 | DEP-03, DEP-04 | manual | `curl -s -o /dev/null -w "%{http_code}" http://<EC2-IP>/` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements. Deploy scripts are validated by bash syntax checks.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| HTTP Basic Auth blocks unauthenticated access | DEP-04 | Requires real nginx + browser | Access http://<EC2-IP>/, verify 401 without credentials |
| Dashboard loads with real data | DEP-02 | Requires real DB connection | Login, verify KPI cards show correct counts |
| Service survives reboot | DEP-02 | Requires server reboot | `sudo reboot`, check `systemctl status helpertips-dashboard` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
