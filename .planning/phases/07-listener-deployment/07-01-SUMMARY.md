---
phase: 07-listener-deployment
plan: 01
subsystem: listener, deploy
tags: [systemd, logging, telethon, deploy, tdd]
dependency_graph:
  requires: [Phase 06 (EC2 + PostgreSQL), deploy/01-provision-ec2.sh]
  provides: [listener systemd service config, conditional logging, deploy script]
  affects: [helpertips/listener.py, deploy/]
tech_stack:
  added: []
  patterns: [RotatingFileHandler daemon logging, systemd EnvironmentFile, OnFailure= template service, logrotate]
key_files:
  created:
    - deploy/05-setup-listener.sh
    - tests/test_listener_logging.py
  modified:
    - helpertips/listener.py
    - .env.example
decisions:
  - configure_logging() com LOG_PATH como constante de modulo para testabilidade
  - StartLimitBurst/StartLimitIntervalSec na secao [Unit] (nao [Service]) — pitfall critico systemd
  - StandardOutput=null no unit file — logs vao para RotatingFileHandler, evita duplicacao no journald
  - Script de notificacao com exit 0 quando variaveis vazias — sem loop de falha
  - Servico NAO habilitado pelo script — requer autenticacao interativa primeiro
metrics:
  duration: 189s
  completed_date: "2026-04-04"
  tasks_completed: 2
  tasks_total: 3
  files_changed: 4
---

# Phase 07 Plan 01: Listener Deployment Prep Summary

**One-liner:** Logging condicional TTY/daemon com RotatingFileHandler + script systemd completo (unit file, logrotate, notificacao Telegram) sem habilitar servico antes da autenticacao.

## What Was Built

### Task 1: Logging condicional TTY + testes unitarios (TDD)

Substituiu o `logging.basicConfig()` fixo com `RichHandler` por uma funcao `configure_logging()` que detecta `sys.stdout.isatty()`:

- **TTY (desenvolvimento local):** `RichHandler` com rich tracebacks — comportamento identico ao anterior
- **Daemon (systemd/sem TTY):** `RotatingFileHandler` para `/var/log/helpertips/listener.log` (10MB por arquivo, 7 backups, encoding UTF-8)

Constante `LOG_PATH = "/var/log/helpertips/listener.log"` exposta no modulo para permitir mock nos testes.

Todos os usos de `console.print()` com Rich markup agora verificam `sys.stdout.isatty()` antes de renderizar — `print_startup_summary`, `handle_signal`, shutdown block e `selecionar_grupo` fallback usam `logger.info()` em modo daemon.

4 testes unitarios em `tests/test_listener_logging.py`:
- `test_daemon_mode_uses_rotating_file_handler` — verifica tipo do handler em modo daemon
- `test_tty_mode_uses_rich_handler` — verifica RichHandler em modo TTY
- `test_rotating_file_handler_config` — verifica maxBytes=10MB e backupCount=7
- `test_rotating_file_handler_format` — verifica formato com asctime/levelname/name/message

### Task 2: Script deploy/05-setup-listener.sh + .env.example

Script bash `set -euo pipefail` que cria 4 artefatos:

1. `/etc/systemd/system/helpertips-listener.service` — unit file principal com:
   - `StartLimitBurst=5` e `StartLimitIntervalSec=300` na secao `[Unit]` (pitfall critico — silenciosamente ignorados em `[Service]`)
   - `Restart=on-failure`, `RestartSec=60`
   - `OnFailure=helpertips-notify-failure@%n.service`
   - `StandardOutput=null` — logs vao para RotatingFileHandler, nao journald
   - `StandardError=journal` — erros criticos preservados
   - `NoNewPrivileges=true`, `PrivateTmp=true` — hardening basico

2. `/etc/systemd/system/helpertips-notify-failure@.service` — template service invocado pelo `OnFailure=`

3. `/usr/local/bin/helpertips-notify-failure.sh` — script curl para Telegram Bot API; `exit 0` quando variaveis vazias (evita loop de falha)

4. `/etc/logrotate.d/helpertips` — rotacao diaria, 14 dias, compress+delaycompress

Script finaliza com `systemctl daemon-reload` e imprime instrucoes de autenticacao. NAO executa `systemctl enable` ou `systemctl start` — requer autenticacao interativa primeiro.

`.env.example` atualizado com `TELEGRAM_NOTIFY_TOKEN` e `TELEGRAM_NOTIFY_CHAT_ID` (comentados — opcionais).

## Commits

| Task | Commit | Descricao |
|------|--------|-----------|
| Task 1 | `6c1e416` | feat(07-01): logging condicional TTY vs daemon com testes unitarios |
| Task 2 | `994ebca` | feat(07-01): script de deploy systemd + logrotate + notificacao de falha |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing functionality] TTY guard para selecionar_grupo fallback**
- **Found during:** Task 1
- **Issue:** O bloco `if not group_id_str:` usava `console.print()` sem verificar TTY — em modo daemon sem TELEGRAM_GROUP_ID, tentaria renderizar Rich markup sem TTY
- **Fix:** Adicionado `sys.stdout.isatty()` guard nos prints do bloco de selecao de grupo, com logger.warning/error como fallback
- **Files modified:** helpertips/listener.py
- **Commit:** 6c1e416

**2. [Rule 2 - Missing functionality] TTY guard para KeyboardInterrupt handler**
- **Found during:** Task 1
- **Issue:** O handler de `KeyboardInterrupt` no loop de reconexao usava `console.print()` sem guard
- **Fix:** Adicionado `sys.stdout.isatty()` guard com `logger.info()` fallback
- **Files modified:** helpertips/listener.py
- **Commit:** 6c1e416

## Test Results

```
tests/test_listener_logging.py: 4 passed
tests/ (suite completa): 138 passed
ruff check helpertips/: 0 violations
bash -n deploy/05-setup-listener.sh: Syntax OK
```

## Known Stubs

Nenhum stub. Task 3 (autenticacao interativa + ativacao do servico na EC2) e um checkpoint human-action pendente — requer SSH na EC2.

## Checkpoint Pendente

**Task 3** e um `checkpoint:human-action` aguardando execucao manual na EC2:
- Atualizar codigo na EC2 (`git pull`)
- Executar `sudo bash deploy/05-setup-listener.sh`
- Autenticacao interativa Telethon via SSH (`sudo -u helpertips bash`, `python -m helpertips.listener`)
- Verificar `.session` e `TELEGRAM_GROUP_ID` no `.env`
- `sudo systemctl enable --now helpertips-listener`
- Verificar `systemctl status helpertips-listener` = `active (running)`

## Self-Check: PASSED

- [x] `helpertips/listener.py` existe com `configure_logging()`, `LOG_PATH`, `sys.stdout.isatty()`
- [x] `tests/test_listener_logging.py` existe com 4 testes
- [x] `deploy/05-setup-listener.sh` existe com sintaxe valida
- [x] `.env.example` contem `TELEGRAM_NOTIFY_TOKEN` e `TELEGRAM_NOTIFY_CHAT_ID`
- [x] Commits 6c1e416 e 994ebca existem no historico
