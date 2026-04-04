---
phase: 06-aws-infrastructure
plan: 01
subsystem: infra
tags: [aws, ec2, bash, ubuntu, security-group, elastic-ip, swap]

# Dependency graph
requires: []
provides:
  - Script bash de bootstrap do EC2 (swap 1GB, usuario dedicado, pacotes base)
  - Guia de provisionamento AWS passo a passo (key pair, SG, EC2, EIP, SSH)
affects: [06-02, 06-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Script bootstrap idempotente com guards (if [ ! -f ], if ! id ...)"
    - "Security Group com SSH /32 restrito ao IP pessoal"

key-files:
  created:
    - deploy/01-provision-ec2.sh
    - deploy/README-deploy.md
  modified: []

key-decisions:
  - "Script bootstrap executa como root via sudo — unico metodo confiavel para criar swap e usuarios no EC2"
  - "SSH no SG restrito a IP /32 do desenvolvedor — bots escaneiam 24/7, /32 e obrigatorio"
  - "Porta 8050 aberta para 0.0.0.0/0 temporariamente — nginx com auth sera adicionado na Phase 8"

patterns-established:
  - "deploy/ como diretorio de scripts de infraestrutura separados por plano (01-, 02-, etc.)"

requirements-completed: [AWS-01]

# Metrics
duration: 2min
completed: 2026-04-04
---

# Phase 6 Plan 01: Provision EC2 Summary

**Script bash idempotente de bootstrap EC2 (swap 1GB, usuario helpertips, pacotes base) + guia de 6 passos para provisionamento via AWS Console com Security Group restrito e Elastic IP**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-04T00:39:03Z
- **Completed:** 2026-04-04T00:41:07Z
- **Tasks:** 1 completa, 1 aguardando acao humana (Task 2 — checkpoint)
- **Files modified:** 2

## Accomplishments

- `deploy/01-provision-ec2.sh` criado com swap 1GB idempotente, usuario `helpertips` dedicado, e instalacao de pacotes base (python3.12-venv, git, curl, ca-certificates, unzip)
- `deploy/README-deploy.md` criado com guia completo de 6 passos: key pair, Security Group (SSH /32 + HTTP 8050 + HTTP 80), lancamento EC2 t3.micro Ubuntu 24.04, alocacao Elastic IP, SSH + bootstrap, verificacao
- Script valida com `bash -n` sem erros de sintaxe

## Task Commits

1. **Task 1: Criar script de bootstrap e guia de provisionamento** - `e29d4bf` (feat)
2. **Task 2: Provisionar EC2 no AWS Console** - aguardando acao humana (checkpoint:human-action)

## Files Created/Modified

- `deploy/01-provision-ec2.sh` — Script bash de bootstrap inicial do EC2: swap 1GB, usuario helpertips, pacotes base
- `deploy/README-deploy.md` — Guia de provisionamento AWS: key pair, SG, EC2, EIP, SSH, verificacao e troubleshooting

## Decisions Made

- SSH no Security Group restrito ao IP /32 do desenvolvedor — documentado procedimento de atualizacao quando ISP muda o IP
- Porta 8050 aberta para 0.0.0.0/0 temporariamente ate Phase 8 adicionar nginx com HTTP Basic Auth
- Script usa guards idempotentes para permitir re-execucao segura sem duplicar swap ou usuario

## Deviations from Plan

None — plano executado exatamente como especificado.

## Issues Encountered

None.

## User Setup Required

**Task 2 requer acao manual.** O usuario deve seguir `deploy/README-deploy.md` para:

1. Criar key pair `helpertips-key` no AWS Console
2. Criar Security Group `helpertips-sg` com regras SSH /32 + HTTP 8050 + HTTP 80
3. Lancar EC2 t3.micro Ubuntu 24.04 LTS em us-east-1 com EBS 20GB gp3
4. Alocar Elastic IP e associar a instancia
5. SSH para instancia e executar `sudo bash deploy/01-provision-ec2.sh`
6. Verificar: `free -h` mostra swap 1GB, `id helpertips` retorna info do usuario

**Verificacao apos Task 2:**
```bash
ssh -i ~/.ssh/helpertips-key.pem ubuntu@ELASTIC_IP
free -h         # deve mostrar Swap: 1.0G
id helpertips   # deve retornar uid e gid do usuario
```

## Next Phase Readiness

- Script de bootstrap pronto para executar apos provisionamento no Console
- README-deploy.md cobre todos os passos necessarios para o usuario
- **Bloqueador para 06-02:** EC2 deve estar provisionado e acessivel via SSH com bootstrap executado
- Task 2 (checkpoint:human-action) ainda pendente — usuario deve executar os passos do guia

## Known Stubs

None.

---

## Self-Check: PASSED

- `deploy/01-provision-ec2.sh` EXISTS: FOUND
- `deploy/README-deploy.md` EXISTS: FOUND
- Commit `e29d4bf` EXISTS: FOUND

---

*Phase: 06-aws-infrastructure*
*Completed: 2026-04-04*
