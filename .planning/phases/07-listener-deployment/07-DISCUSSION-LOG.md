# Phase 7: Listener Deployment - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-04
**Phase:** 07-listener-deployment
**Areas discussed:** Fluxo de autenticação, Gestão de logs, Comportamento em falha, Localização do .session

---

## Fluxo de autenticação

| Option | Description | Selected |
|--------|-------------|----------|
| SSH interativo | Rodar listener uma vez via SSH, digitar phone + SMS code, selecionar grupo. Zero mudança de código. | ✓ |
| Auth local + SCP | Autenticar na máquina local, copiar .session via SCP para o EC2. | |
| StringSession + env var | Refatorar listener para aceitar session string como variável de ambiente. | |

**User's choice:** SSH interativo (Recomendado)
**Notes:** Código já suporta, zero alterações necessárias.

---

## Gestão de logs

| Option | Description | Selected |
|--------|-------------|----------|
| journald via stdout | StreamHandler padrão em produção, RichHandler só local. journalctl para diagnóstico. | |
| Arquivo em /var/log/ | RotatingFileHandler com rotação manual. Independente do systemd. | ✓ |
| JournaldHandler estruturado | Logs com campos customizados via dep extra python3-systemd. | |

**User's choice:** Arquivo em /var/log/
**Notes:** Preferência por logs em arquivo independente do systemd.

---

## Comportamento em falha

| Option | Description | Selected |
|--------|-------------|----------|
| Limitar retries + alerta | StartLimitBurst=5, RestartSec=60, OnFailure envia mensagem via Telegram Bot API. | ✓ |
| Restart infinito sem limite | StartLimitIntervalSec=0, tenta reiniciar para sempre. Simples mas falha silenciosa. | |
| Restart infinito + alerta cada falha | Não limita retries mas notifica a cada queda. Risco de flood de mensagens. | |

**User's choice:** Limitar retries + alerta (Recomendado)
**Notes:** Perder sinais sem saber contradiz o objetivo do sistema.

---

## Localização do .session

| Option | Description | Selected |
|--------|-------------|----------|
| /home/helpertips/ | Home do user dedicado. Simples, servidor single-purpose. | ✓ |
| /home/helpertips/helpertips/ | Pasta do projeto. Junto do código. Risco de commit acidental. | |
| /var/lib/helpertips/ | Padrão FHS para estado de daemon. Mais setup inicial. | |

**User's choice:** /home/helpertips/ (Recomendado)
**Notes:** Backup S3 já cobre esse path.

## Claude's Discretion

- Configuração exata do unit file systemd
- Script de notificação de falha
- Configuração do logrotate
- Ajuste do listener.py para detectar TTY
- Ordem dos passos no script de deploy

## Deferred Ideas

None — discussion stayed within phase scope
