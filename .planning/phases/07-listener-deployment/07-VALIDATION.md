---
phase: 7
slug: listener-deployment
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-04
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pytest.ini` or "none — Wave 0 installs" |
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
| 07-01-01 | 01 | 1 | DEP-05 | manual | SSH interactive auth | N/A | ⬜ pending |
| 07-01-02 | 01 | 1 | DEP-01 | integration | `systemctl status helpertips-listener` | N/A | ⬜ pending |
| 07-01-03 | 01 | 1 | DEP-01 | integration | `sudo systemctl restart helpertips-listener && sleep 5 && systemctl is-active helpertips-listener` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements. This phase is deployment/infra — automated tests are replaced by systemd verification commands.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Telethon interactive auth | DEP-05 | Requires human input (phone code/2FA) | SSH to EC2, run `python listener.py`, enter code when prompted |
| Service survives reboot | DEP-01 | Requires server reboot | `sudo reboot`, wait, check `systemctl status helpertips-listener` |
| Signal capture end-to-end | DEP-01 | Requires real Telegram signal | Send test message in group, verify in DB |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
