---
phase: 06-aws-infrastructure
plan: 03
subsystem: infra
tags: [aws, s3, iam, bash, backup, cron, pg_dump, instance-profile]

# Dependency graph
requires:
  - phase: 06-02
    provides: PostgreSQL 16 rodando com role helpertips_user e banco helpertips
provides:
  - Script bash de backup diario (pg_dump + .session para S3 via IAM instance profile)
  - Script bash de setup do cron (instala AWS CLI v2, configura /etc/cron.d/helpertips-backup)
  - Instrucoes de IAM role helpertips-ec2-role e bucket S3 no output do setup
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "IAM instance profile sem access keys estaticos — credenciais via IMDS automaticamente"
    - "pg_dump formato custom (-Fc) para backup comprimido e restauravel com pg_restore"
    - "Rotacao de backups por data no S3 com limpeza automatica >30 dias"
    - "Cron /etc/cron.d com usuario dedicado — isolamento de privilegios"

key-files:
  created:
    - deploy/backup-helpertips.sh
    - deploy/04-setup-backup.sh
  modified: []

key-decisions:
  - "IAM instance profile em vez de access keys estaticos no .env — credenciais temporarias via IMDS, sem segredo em disco"
  - "ACCOUNT_ID descoberto dinamicamente via aws sts get-caller-identity — bucket name consistente sem hardcode"
  - "pg_dump formato custom (-Fc) — comprimido automaticamente, restauravel seletivamente com pg_restore"
  - "Limpeza S3 >30 dias no proprio script de backup — sem custo adicional de Lambda ou lifecycle policy"

patterns-established: []

requirements-completed: [AWS-04, AWS-05]

# Metrics
duration: 3min
completed: 2026-04-04
---

# Phase 6 Plan 03: Backup & Credentials Summary

**Script de backup diario pg_dump + .session para S3 via IAM instance profile sem access keys estaticos, com cron as 03:00 UTC e rotacao automatica de 30 dias**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-04T02:16:43Z
- **Completed:** 2026-04-04T02:19:xx Z
- **Tasks:** 1 completa, 1 aguardando acao humana (Task 2 — checkpoint:human-action)
- **Files modified:** 2

## Accomplishments

- `deploy/backup-helpertips.sh` criado com: source do `.env` para DB_PASSWORD, pg_dump formato custom (-Fc), copia do `.session`, upload para S3 via IAM instance profile, limpeza de backups >30 dias
- `deploy/04-setup-backup.sh` criado com: instalacao AWS CLI v2 (idempotente), instalacao do script em `/usr/local/bin/`, criacao do cron `/etc/cron.d/helpertips-backup` as 03:00 UTC, instrucoes completas de IAM role e bucket S3
- Ambos os scripts validados com `bash -n` sem erros de sintaxe
- Todos os 12 criterios de aceitacao confirmados

## Task Commits

1. **Task 1: Criar scripts de backup e setup do cron** — `6c332b7` (feat)
2. **Task 2: Configurar S3 bucket, IAM role e ativar backup** — aguardando acao humana (checkpoint:human-action)

## Files Created/Modified

- `deploy/backup-helpertips.sh` — Script de backup: pg_dump + .session para S3 via IAM instance profile, limpeza 30 dias
- `deploy/04-setup-backup.sh` — Script de setup: AWS CLI v2, cron 03:00 UTC, instrucoes IAM role e bucket S3

## Decisions Made

- IAM instance profile em vez de access keys estaticos no `.env` — credenciais temporarias via IMDS, sem segredo adicional em disco
- ACCOUNT_ID descoberto dinamicamente via `aws sts get-caller-identity` — bucket name consistente sem hardcode no script
- pg_dump formato custom (-Fc) — comprimido automaticamente, restauravel seletivamente via `pg_restore -t tabela`
- Limpeza S3 >30 dias implementada no proprio script — sem custo adicional de Lambda ou configuracao de lifecycle policy

## Deviations from Plan

None — plano executado exatamente como especificado.

## Issues Encountered

None.

## User Setup Required

**Task 2 requer acao manual no EC2 e AWS Console.** O usuario deve:

1. Verificar `.env` no servidor: `stat -c '%a' /home/helpertips/.env` deve retornar `600`
2. No EC2: `sudo bash deploy/04-setup-backup.sh` (instala AWS CLI, copia script, cria cron)
3. No AWS Console, criar S3 bucket `helpertips-backups-ACCOUNT_ID` em us-east-1 com Block all public access habilitado
4. No AWS Console, criar IAM Role `helpertips-ec2-role` com policy inline para `s3:PutObject/GetObject/ListBucket/DeleteObject` no bucket
5. Associar IAM Role a instancia: EC2 Console > Actions > Security > Modify IAM Role
6. Testar: `sudo -u helpertips /usr/local/bin/backup-helpertips.sh`
7. Verificar: `aws s3 ls s3://helpertips-backups-ACCOUNT_ID/backups/`

**Verificacao apos Task 2:**
```bash
# Cron configurado
cat /etc/cron.d/helpertips-backup      # deve mostrar "0 3 * * *"

# IAM role funcionando
aws sts get-caller-identity             # deve retornar ARN da role

# Backup no S3
aws s3 ls s3://helpertips-backups-ACCOUNT_ID/backups/  # deve listar o dump
```

## Next Phase Readiness

- Scripts de backup prontos para execucao pos-Task 2
- Infraestrutura de backup completa (cron + S3 + IAM) uma vez que Task 2 seja executada
- Phase 06 completa apos execucao manual da Task 2

## Known Stubs

None.

---

## Self-Check: PASSED

- `deploy/backup-helpertips.sh` EXISTS: FOUND
- `deploy/04-setup-backup.sh` EXISTS: FOUND
- Commit `6c332b7` EXISTS: FOUND

---

*Phase: 06-aws-infrastructure*
*Completed: 2026-04-04*
