# Phase 7: Listener Deployment - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Listener Telethon capturando sinais do grupo {VIP} ExtremeTips 24/7 na EC2 como systemd service, sobrevivendo a crashes e reboots. Inclui primeira autenticação interativa via SSH e configuração operacional completa.

</domain>

<decisions>
## Implementation Decisions

### Fluxo de Autenticação
- **D-01:** SSH interativo + `client.start()` padrão. Rodar listener uma vez via SSH, digitar phone + SMS code, selecionar grupo via `selecionar_grupo`. Zero mudança de código. Depois configurar TELEGRAM_GROUP_ID no .env com o ID selecionado para evitar prompt interativo em restarts automáticos.

### Gestão de Logs
- **D-02:** RotatingFileHandler em `/var/log/helpertips/listener.log`. Logs em arquivo independente do systemd. Detectar `sys.stdout.isatty()` para manter RichHandler no desenvolvimento local e usar logging padrão em produção. Configurar logrotate para rotação automática.

### Comportamento em Falha
- **D-03:** `Restart=on-failure` com `RestartSec=60`, `StartLimitBurst=5`, `StartLimitIntervalSec=300` (5 falhas em 5 min). `OnFailure=` dispara script que envia alerta via Telegram Bot API (curl simples). Se cair repetidamente, para e notifica — perder sinais sem saber contradiz o objetivo do sistema.

### Localização do .session
- **D-04:** Arquivo `.session` em `/home/helpertips/` (home do user dedicado). Servidor single-purpose, permissões já corretas para user helpertips. Backup S3 diário já cobre esse path (script `backup-helpertips.sh` referencia `/home/helpertips/helpertips_listener.session`). WorkingDirectory do systemd aponta para `/home/helpertips/`.

### Claude's Discretion
- Configuração exata do unit file systemd (ExecStart, Environment, etc.)
- Script de notificação de falha (formato da mensagem Telegram)
- Configuração do logrotate (tamanho, retenção)
- Ajuste do listener.py para detectar TTY e trocar handler de logging
- Ordem exata dos passos no script de deploy

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Código do listener
- `helpertips/listener.py` — Listener Telethon, usa `client.start()`, `selecionar_grupo`, RichHandler
- `helpertips/list_groups.py` — Função `selecionar_grupo` para seleção interativa de grupo
- `helpertips/db.py` — Conexão DB via os.environ (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
- `helpertips/store.py` — `upsert_signal`, `log_parse_failure`, `get_stats`

### Infraestrutura existente (Phase 6)
- `deploy/01-provision-ec2.sh` — Bootstrap EC2 (user helpertips, swap, pacotes)
- `deploy/backup-helpertips.sh` — Backup S3 referencia `/home/helpertips/helpertips_listener.session`
- `.env.example` — Template com variáveis Telegram (API_ID, API_HASH, GROUP_ID)

### Requirements
- `.planning/REQUIREMENTS.md` — DEP-01 (systemd Restart=on-failure RestartSec=60), DEP-05 (auth interativa via SSH)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `listener.py` já tem `client.start()` com `input()` nativo — funciona via SSH sem mudança
- `selecionar_grupo` lista grupos e retorna ID — usado na primeira execução
- RichHandler configurado em `listener.py:26-30` — precisa swap condicional para produção
- Diretório `/var/log/helpertips/` já criado pelo `01-provision-ec2.sh`

### Established Patterns
- Processos separados: listener e dashboard rodam independentes (processos distintos)
- python-dotenv carrega `.env` automaticamente
- User dedicado `helpertips` criado no bootstrap

### Integration Points
- systemd unit → `python3 -m helpertips.listener` como ExecStart
- `.env` em `/home/helpertips/.env` → carregado via EnvironmentFile ou python-dotenv
- `.session` gerado em WorkingDirectory → `/home/helpertips/`
- `OnFailure=` → script de notificação via Telegram Bot API

</code_context>

<specifics>
## Specific Ideas

- Alerta de falha via Telegram Bot API (curl) — usa o mesmo canal que o usuário já monitora
- TELEGRAM_GROUP_ID deve ser preenchido no .env após primeira seleção interativa — evita prompt em restarts

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-listener-deployment*
*Context gathered: 2026-04-04*
