---
phase: 08-dashboard-proxy
plan: 01
subsystem: infra
tags: [gunicorn, systemd, wsgi, dash, logrotate, nginx]

# Dependency graph
requires:
  - phase: 07-listener-deployment
    provides: deploy/05-setup-listener.sh padrao de script idempotente com systemd unit file
provides:
  - WSGI callable server = app.server exposto em helpertips/dashboard.py
  - gunicorn>=25.0 como dependencia em pyproject.toml
  - deploy/06-setup-dashboard.sh com systemd service helpertips-dashboard e logrotate
affects: [08-02-nginx-proxy, deploy]

# Tech tracking
tech-stack:
  added: [gunicorn>=25.0]
  patterns: [WSGI callable exposto via server = app.server, systemd unit file com gunicorn ExecStart]

key-files:
  created:
    - deploy/06-setup-dashboard.sh
  modified:
    - helpertips/dashboard.py
    - pyproject.toml

key-decisions:
  - "server = app.server em dashboard.py — gunicorn importa WSGI callable sem precisar alterar o bloco __main__"
  - "StartLimitBurst e StartLimitIntervalSec em [Unit] (nao [Service]) — pitfall critico documentado Phase 7"
  - "Logrotate compartilhado listener + dashboard — substitui configuracao anterior, evita dois arquivos em /etc/logrotate.d/"
  - "postrotate USR1 para helpertips-dashboard — graceful log reopen sem matar workers gunicorn"

patterns-established:
  - "Script deploy/0N-setup-*.sh: set -euo pipefail, header, secoes numeradas, instrucoes finais"
  - "WSGI callable sempre exposto como server = app.server logo apos app = dash.Dash(...)"

requirements-completed: [DEP-02]

# Metrics
duration: 2min
completed: 2026-04-04
---

# Phase 8 Plan 01: Dashboard WSGI + systemd Service Summary

**gunicorn configurado como WSGI server para o Dash dashboard, rodando como systemd service com 2 workers em 127.0.0.1:8050 e logrotate compartilhado com o listener**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-04-04T04:36:14Z
- **Completed:** 2026-04-04T04:37:56Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- dashboard.py expoe `server = app.server` — gunicorn pode importar o WSGI callable sem erro
- gunicorn>=25.0 adicionado como dependencia em pyproject.toml
- deploy/06-setup-dashboard.sh criado com unit file completo (2 workers, bind 127.0.0.1:8050, timeout 120, Restart=on-failure, StartLimitBurst em [Unit]) e logrotate com postrotate USR1

## Task Commits

1. **Task 1: Expor WSGI callable e adicionar gunicorn como dependencia** - `fa02cf5` (feat)
2. **Task 2: Criar script deploy/06-setup-dashboard.sh com systemd service e logrotate** - `d686115` (feat)

## Files Created/Modified

- `helpertips/dashboard.py` - Adicionado `server = app.server` apos inicializacao do app Dash
- `pyproject.toml` - Adicionado `gunicorn>=25.0` ao array dependencies
- `deploy/06-setup-dashboard.sh` - Script idempotente para systemd service + logrotate do dashboard

## Decisions Made

- `server = app.server` posicionado logo apos o bloco `app = dash.Dash(...)` para clareza — o bloco `if __name__ == "__main__"` permanece intacto para uso como script direto
- Logrotate compartilhado substitui `/etc/logrotate.d/helpertips` em vez de criar arquivo separado — consolida listener + dashboard em um unico arquivo de configuracao
- `postrotate` envia USR1 para gunicorn para reabrir arquivos de log sem reiniciar workers (zero downtime)

## Deviations from Plan

Nenhuma — plano executado exatamente como especificado.

## Issues Encountered

Nenhum — verificacao `python -c "from helpertips.dashboard import server; print(type(server))"` retornou `<class 'flask.app.Flask'>` na primeira tentativa.

## User Setup Required

Nenhum — sem configuracao externa necessaria neste plano. O script `deploy/06-setup-dashboard.sh` deve ser executado na EC2 como root apos gunicorn instalado no venv.

## Next Phase Readiness

- WSGI callable pronto para gunicorn importar: `helpertips.dashboard:server`
- Script de deploy criado seguindo padrao estabelecido em Phase 7
- Phase 08-02 pode configurar nginx como reverse proxy apontando para `127.0.0.1:8050`

---
*Phase: 08-dashboard-proxy*
*Completed: 2026-04-04*
