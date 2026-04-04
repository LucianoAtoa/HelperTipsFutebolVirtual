---
phase: 07-listener-deployment
verified: 2026-04-04T12:00:00Z
status: human_needed
score: 5/7 must-haves verified (automated); 2/3 success criteria require human confirmation
re_verification: false
human_verification:
  - test: "Verificar que systemctl status helpertips-listener mostra active (running) na EC2"
    expected: "Active: active (running) — servico ativo e capturando mensagens"
    why_human: "Requer SSH na EC2 (32.194.158.134) — nao verificavel programaticamente"
  - test: "Verificar que sinais aparecem no banco apos reboot da EC2"
    expected: "systemctl status helpertips-listener active (running) apos sudo reboot + SELECT COUNT(*) FROM signals retorna > 0"
    why_human: "Requer reboot do servidor e verificacao pos-boot — operacao destrutiva nao automatizavel"
---

# Phase 07: Listener Deployment — Verification Report

**Phase Goal:** Listener capturando sinais do Telegram 24/7 na EC2, sobrevivendo a crashes e reboots
**Verified:** 2026-04-04
**Status:** human_needed
**Re-verification:** Nao — verificacao inicial

---

## Goal Achievement

### Success Criteria (do ROADMAP.md)

| #   | Criterio                                                                  | Status          | Evidencia                                              |
| --- | ------------------------------------------------------------------------- | --------------- | ------------------------------------------------------ |
| 1   | Autenticacao Telethon interativa completada via SSH — .session gerado     | ? HUMAN_NEEDED  | SUMMARY afirma conclusao; nao verificavel sem SSH      |
| 2   | `systemctl status helpertips-listener` mostra `active (running)` apos reboot | ? HUMAN_NEEDED  | SUMMARY afirma ativo; requer verificacao na EC2        |
| 3   | Sinal capturado localmente aparece no banco na EC2                        | ? HUMAN_NEEDED  | SUMMARY afirma smoke test concluido; requer verificacao |

**Score dos criterios de sucesso:** 0/3 verificaveis automaticamente — todos requerem acesso SSH a EC2.

### Observable Truths (do must_haves do PLAN)

| #   | Truth                                                                          | Status     | Evidencia                                                 |
| --- | ------------------------------------------------------------------------------ | ---------- | --------------------------------------------------------- |
| 1   | listener.py usa RotatingFileHandler quando nao ha TTY (daemon/systemd)        | VERIFIED   | Linhas 39-52: RotatingFileHandler no branch `not isatty()` |
| 2   | listener.py usa RichHandler quando ha TTY (desenvolvimento local)              | VERIFIED   | Linhas 34-38: RichHandler no branch `isatty()`           |
| 3   | deploy/05-setup-listener.sh cria unit file com Restart=on-failure/RestartSec=60 | VERIFIED  | Linhas 29-30 do script; bash -n retorna 0                |
| 4   | Script de notificacao envia alerta via Telegram Bot API                        | VERIFIED   | Linhas 67-87: curl para api.telegram.org com exit 0 se vars vazias |
| 5   | logrotate configurado para /var/log/helpertips/listener.log                    | VERIFIED   | Linhas 98-108: logrotate diario, rotate 14, compress      |
| 6   | Servico systemd depende de network.target e postgresql.service                 | VERIFIED   | Linha 17: `After=network.target postgresql.service`       |
| 7   | .env.example documenta variaveis de notificacao Telegram                       | VERIFIED   | Linhas 23-27 do .env.example: TELEGRAM_NOTIFY_TOKEN e TELEGRAM_NOTIFY_CHAT_ID |

**Score must-haves:** 7/7 truths VERIFIED (codigo local)

---

## Required Artifacts

| Artifact                        | Expected                                  | Status     | Detalhes                                             |
| ------------------------------- | ----------------------------------------- | ---------- | ---------------------------------------------------- |
| `helpertips/listener.py`        | Logging condicional TTY vs daemon         | VERIFIED   | configure_logging() com sys.stdout.isatty() + RotatingFileHandler |
| `deploy/05-setup-listener.sh`   | Setup completo systemd/logrotate/notificacao | VERIFIED | 139 linhas, set -euo pipefail, 4 artefatos criados   |
| `tests/test_listener_logging.py` | 4 testes unitarios para configure_logging() | VERIFIED | 4 testes passando (pytest 0.14s)                    |
| `.env.example`                  | Template com variaveis de notificacao      | VERIFIED   | TELEGRAM_NOTIFY_TOKEN e TELEGRAM_NOTIFY_CHAT_ID presentes |

---

## Key Link Verification

| From                          | To                                          | Via                           | Status   | Detalhes                                                    |
| ----------------------------- | ------------------------------------------- | ----------------------------- | -------- | ----------------------------------------------------------- |
| `deploy/05-setup-listener.sh` | `/etc/systemd/system/helpertips-listener.service` | cat heredoc                | WIRED    | Linhas 14-38: heredoc cria unit file completo               |
| `helpertips/listener.py`      | `/var/log/helpertips/listener.log`          | RotatingFileHandler           | WIRED    | LOG_PATH="/var/log/helpertips/listener.log" linha 24; handler linha 41 |
| unit file systemd             | `helpertips-notify-failure@.service`        | OnFailure= directive          | WIRED    | Linha 20: `OnFailure=helpertips-notify-failure@%n.service`  |

**Observacao critica verificada:** `StartLimitBurst=5` e `StartLimitIntervalSec=300` estao corretamente posicionados na secao `[Unit]` (linhas 18-19), nao em `[Service]`. Conforme pitfall documentado no RESEARCH — systemd ignora silenciosamente se em `[Service]`.

---

## Data-Flow Trace (Level 4)

Nao aplicavel — phase nao produz componentes que renderizam dados do banco. Os artefatos sao: script de configuracao de deploy, modulo de logging e testes unitarios.

---

## Behavioral Spot-Checks

| Comportamento                              | Comando                                          | Resultado         | Status    |
| ------------------------------------------ | ------------------------------------------------ | ----------------- | --------- |
| 4 testes de logging passando               | `python3 -m pytest tests/test_listener_logging.py -x -v` | 4 passed in 0.14s | PASS  |
| Suite completa verde (138 testes)          | `python3 -m pytest tests/ -x -q`               | 138 passed in 0.66s | PASS    |
| Syntax do script de deploy valida          | `bash -n deploy/05-setup-listener.sh`           | Syntax OK         | PASS      |
| Lint do listener.py sem violacoes           | `ruff check helpertips/listener.py`             | All checks passed | PASS      |
| Commits do plano existem no historico      | `git log --oneline 6c1e416 994ebca`             | Ambos encontrados | PASS      |

---

## Requirements Coverage

| Requirement | Plano    | Descricao                                                               | Status         | Evidencia                                            |
| ----------- | -------- | ----------------------------------------------------------------------- | -------------- | ---------------------------------------------------- |
| DEP-01      | 07-01    | Listener rodando como systemd service com Restart=on-failure e RestartSec=60 | PARTIAL    | Script com unit file correto (verificado localmente); ativacao na EC2 requer confirmacao humana |
| DEP-05      | 07-01    | Primeira autenticacao Telethon feita interativamente via SSH no EC2     | HUMAN_NEEDED   | SUMMARY afirma conclusao; .session gerado; nao verificavel sem SSH |

**Mapeamento no REQUIREMENTS.md:** Ambos DEP-01 e DEP-05 estao marcados como `[x] Complete` e mapeados para Phase 7 — consistente com o PLAN.

**Requisitos orfaos desta fase:** Nenhum. REQUIREMENTS.md lista DEP-01 e DEP-05 para Phase 7 — exatamente os mesmos que o PLAN declara.

---

## Anti-Patterns Found

| Arquivo                          | Linha | Padrao    | Severidade | Impacto                |
| -------------------------------- | ----- | --------- | ---------- | ---------------------- |
| Nenhum encontrado                | —     | —         | —          | —                      |

Busca por TODO/FIXME/PLACEHOLDER/return null/return []/return {} retornou zero resultados nos arquivos modificados nesta fase.

**Nota:** `systemctl enable` aparece apenas dentro de uma instrucao `echo` (linha 137 do script) — nao e um comando executado. O unico `systemctl` executado diretamente e `daemon-reload` (linha 117). Correto — servico nao deve ser habilitado antes da autenticacao interativa.

---

## Human Verification Required

### 1. Servico systemd ativo na EC2

**Teste:** SSH em `ubuntu@32.194.158.134` e executar:
```bash
sudo systemctl status helpertips-listener
```
**Esperado:** Output com `Active: active (running)` e timestamp recente
**Por que humano:** Requer acesso SSH a EC2 em 32.194.158.134 — nao verificavel programaticamente

### 2. Arquivo .session gerado com permissoes corretas

**Teste:** Via SSH:
```bash
ls -la /home/helpertips/helpertips_listener.session
```
**Esperado:** Arquivo existe, owner `helpertips:helpertips`
**Por que humano:** Arquivo na EC2 — nao acessivel localmente

### 3. Sinais no banco (smoke test)

**Teste:** Via SSH:
```bash
sudo -u helpertips psql -h localhost -U helpertips_user -d helpertips -c "SELECT COUNT(*) FROM signals;"
```
**Esperado:** Retorna valor > 0
**Por que humano:** Banco de dados na EC2 — nao acessivel localmente

### 4. Logs em arquivo (nao journald)

**Teste:** Via SSH:
```bash
sudo tail -5 /var/log/helpertips/listener.log
```
**Esperado:** Linhas com formato `2026-04-04 HH:MM:SS INFO helpertips: ...`
**Por que humano:** Arquivo de log na EC2 — nao acessivel localmente

### 5. Sobrevivencia a reboot (criterio de sucesso principal)

**Teste:** Via SSH:
```bash
sudo reboot
# Aguardar 2-3 minutos, reconectar
sudo systemctl status helpertips-listener
```
**Esperado:** `active (running)` apos reboot — confirma `WantedBy=multi-user.target` e `enable` corretos
**Por que humano:** Requer reboot do servidor — operacao destrutiva que precisa de decisao consciente do usuario

---

## Gaps Summary

Nenhum gap de implementacao encontrado. Todos os 7 must-haves de codigo estao VERIFIED. Os 4 artefatos existem, sao substantivos e estao conectados corretamente. Os 138 testes passam. Ruff sem violacoes.

O status `human_needed` nao indica falha — e a natureza desta fase: a parte critica (autenticacao interativa Telethon + ativacao systemd na EC2) e por definicao uma acao humana que nao pode ser verificada automaticamente. O SUMMARY documenta que o usuario completou os passos em 2026-04-04 com resultado `deployed`. A verificacao humana acima serve para confirmar o estado atual da EC2.

---

_Verified: 2026-04-04_
_Verifier: Claude (gsd-verifier)_
