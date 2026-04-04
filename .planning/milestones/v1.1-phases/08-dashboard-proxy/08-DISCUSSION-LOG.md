# Phase 8: Dashboard & Proxy - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-04
**Phase:** 08-dashboard-proxy
**Areas discussed:** Gunicorn config, Nginx reverse proxy, HTTP Basic Auth, Deploy scripts
**Mode:** auto (all recommended defaults selected)

---

## Gunicorn Config

| Option | Description | Selected |
|--------|-------------|----------|
| 2 workers, bind 127.0.0.1:8050 | Recommended for t3.micro (2 vCPU, 1GB RAM) | ✓ |
| 4 workers, bind 127.0.0.1:8050 | Standard formula (2*CPU+1) but may OOM on 1GB | |
| 1 worker, bind 127.0.0.1:8050 | Ultra-safe memory but no concurrency | |

**User's choice:** [auto] 2 workers (recommended default)
**Notes:** t3.micro has 1GB RAM + 1GB swap. 2 workers keeps memory safe while allowing some concurrency.

---

## Nginx Reverse Proxy

| Option | Description | Selected |
|--------|-------------|----------|
| HTTP only (port 80) | Simple setup, no domain needed | ✓ |
| HTTPS with self-signed cert | Encrypted but browser warnings | |
| HTTPS with Let's Encrypt | Requires domain, more setup | |

**User's choice:** [auto] HTTP only (recommended default)
**Notes:** HTTPS is INFRA-01 (v2 scope). HTTP with Basic Auth is sufficient for personal tool.

---

## HTTP Basic Auth

| Option | Description | Selected |
|--------|-------------|----------|
| .htpasswd with credentials from .env | Simple, one user, credentials managed centrally | ✓ |
| Dash-level auth (dash-auth) | App-level, adds dependency | |
| IP whitelist only | No password, relies on network | |

**User's choice:** [auto] .htpasswd from .env (recommended default)
**Notes:** REQUIREMENTS.md explicitly requires HTTP Basic Auth (DEP-04). Single user tool.

---

## Deploy Scripts

| Option | Description | Selected |
|--------|-------------|----------|
| 06 + 07 separate scripts | Follows existing numbered pattern | ✓ |
| Single combined script | Less files but breaks pattern | |
| Extend 05-setup-listener.sh | Overloads one script | |

**User's choice:** [auto] Separate 06 + 07 scripts (recommended default)
**Notes:** Matches deploy/01-05 pattern. Each script is idempotent and focused.

---

## Claude's Discretion

- ExecStart path and gunicorn module syntax
- Nginx buffer sizes and proxy timeouts
- Error page formatting
- Package installation order
- Dashboard app variable export for gunicorn

## Deferred Ideas

- HTTPS with Let's Encrypt (INFRA-01, v2)
- Rate limiting (unnecessary for 1 user)
- Custom 401 error page
