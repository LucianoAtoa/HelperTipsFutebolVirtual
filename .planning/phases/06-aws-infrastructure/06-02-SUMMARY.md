---
phase: 06-aws-infrastructure
plan: 02
subsystem: infra
tags: [aws, postgresql, bash, ubuntu, pgdg, budget, scram-sha-256]

# Dependency graph
requires: [06-01]
provides:
  - Script bash de instalacao PostgreSQL 16 via PGDG com role/banco/pg_hba/shared_buffers
  - Script bash de criacao de budget alert AWS de $15/mes via CLI
affects: [06-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "PostgreSQL 16 via PGDG em Ubuntu 24.04 (apt.postgresql.org)"
    - "scram-sha-256 no pg_hba.conf para autenticacao psycopg2"
    - "shared_buffers 64MB para t3.micro com 1GB RAM"
    - "aws budgets create-budget via CLI com threshold percentual"

key-files:
  created:
    - deploy/02-setup-postgres.sh
    - deploy/03-setup-budget-alert.sh
  modified: []

key-decisions:
  - "shared_buffers reduzido de 128MB para 64MB — t3.micro tem apenas 1GB RAM, default 128MB deixa pouca margem para Telethon+Dash"
  - "scram-sha-256 em vez de peer auth no pg_hba.conf — peer auth so funciona com conexao local via socket Unix como usuario postgres, psycopg2 usa autenticacao por senha"
  - "Budget alert a 80% ($12) em vez de 100% ($15) — antecipacao para dar tempo de reagir antes de ultrapassar o limite"
  - "Senha definida interativamente no script — nao fica em historico de shell nem em variavel de ambiente exposta"

patterns-established: []

requirements-completed: [AWS-02, AWS-03]

# Metrics
duration: 1min
completed: 2026-04-04
---

# Phase 6 Plan 02: PostgreSQL Setup & Budget Alert Summary

**Scripts bash para instalar PostgreSQL 16 via PGDG, configurar role/banco/auth com scram-sha-256, ajustar shared_buffers para 64MB e criar budget alert de $15/mes no AWS Budgets**

## Performance

- **Duration:** 1 min
- **Started:** 2026-04-04T01:12:19Z
- **Completed:** 2026-04-04T01:13:xx Z
- **Tasks:** 1 completa, 1 aguardando acao humana (Task 2 — checkpoint:human-action)
- **Files modified:** 2

## Accomplishments

- `deploy/02-setup-postgres.sh` criado com instalacao PGDG, criacao de role `helpertips_user` e banco `helpertips`, configuracao de `scram-sha-256` no `pg_hba.conf`, reducao de `shared_buffers` para 64MB, e verificacao final
- `deploy/03-setup-budget-alert.sh` criado com verificacao de budget preexistente, criacao via AWS CLI de budget `HelperTips-Monthly` ($15/mes) com alerta de email a 80% ($12)
- Ambos os scripts validados com `bash -n` (sintaxe sem erros)
- Todos os 12 criterios de aceitacao confirmados

## Task Commits

1. **Task 1: Criar scripts de setup PostgreSQL e budget alert** - `0bb6b03` (feat)
2. **Task 2: Instalar PostgreSQL, migrar schema e configurar budget alert** - aguardando acao humana (checkpoint:human-action)

## Files Created/Modified

- `deploy/02-setup-postgres.sh` — Instala PG16 via PGDG, cria role/banco helpertips, configura pg_hba.conf scram-sha-256, ajusta shared_buffers 64MB
- `deploy/03-setup-budget-alert.sh` — Cria budget alert HelperTips-Monthly ($15/mes) com alerta a 80% via AWS CLI

## Decisions Made

- `scram-sha-256` no `pg_hba.conf` — peer auth invalida para psycopg2 que autentica por senha
- `shared_buffers = 64MB` para t3.micro — o default de 128MB consome muita RAM em instancia de 1GB
- Senha definida interativamente (sem expor em env/historico)
- Budget alert a 80% do limite para antecipacao de custos

## Deviations from Plan

None — plano executado exatamente como especificado.

## Issues Encountered

None.

## User Setup Required

**Task 2 requer acao manual no EC2.** O usuario deve:

1. SSH no EC2: `ssh -i ~/.ssh/helpertips-key.pem ubuntu@ELASTIC_IP`
2. Navegar para o repositorio clonado e executar:
   ```bash
   sudo bash deploy/02-setup-postgres.sh
   ```
   Definir senha para `helpertips_user` quando solicitado

3. Criar `.env` no servidor:
   ```bash
   cp .env.example /home/helpertips/.env
   # Editar: DB_PASSWORD=<senha-definida-acima>, DB_HOST=localhost
   chmod 600 /home/helpertips/.env
   chown helpertips:helpertips /home/helpertips/.env
   ```

4. Clonar repositorio (se ainda nao feito):
   ```bash
   sudo -u helpertips git clone https://github.com/USER/helpertips.git /home/helpertips/helpertips
   ```

5. Criar venv e instalar dependencias:
   ```bash
   sudo -u helpertips bash -c 'cd /home/helpertips/helpertips && python3 -m venv /home/helpertips/.venv && source /home/helpertips/.venv/bin/activate && pip install -r requirements.txt'
   ```

6. Migrar schema:
   ```bash
   sudo -u helpertips bash -c 'source /home/helpertips/.venv/bin/activate && cd /home/helpertips/helpertips && python3 -c "from helpertips.db import get_connection, ensure_schema; c=get_connection(); ensure_schema(c); c.close(); print(\"Schema OK\")"'
   ```

7. Na maquina local (requer AWS CLI configurado):
   ```bash
   bash deploy/03-setup-budget-alert.sh
   ```

**Verificacao apos Task 2:**
```bash
# No EC2 — verificar schema
sudo -u postgres psql -d helpertips -c "SELECT COUNT(*) FROM signals; SELECT COUNT(*) FROM mercados;"
# Deve retornar sem erro (0 registros e 2 mercados respectivamente)

# Verificar budget no Console AWS
# https://console.aws.amazon.com/billing/home#/budgets
```

## Known Stubs

None.

---

## Self-Check: PASSED

- `deploy/02-setup-postgres.sh` EXISTS: FOUND
- `deploy/03-setup-budget-alert.sh` EXISTS: FOUND
- Commit `0bb6b03` EXISTS: FOUND

---

*Phase: 06-aws-infrastructure*
*Completed: 2026-04-04*
