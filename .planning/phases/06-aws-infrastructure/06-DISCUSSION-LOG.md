# Phase 6: AWS Infrastructure - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-04
**Phase:** 06-aws-infrastructure
**Areas discussed:** Tipo de instância e região, PostgreSQL local vs RDS, Gestão de credenciais, Sessão Telethon e persistência

---

## Tipo de Instância e Região

| Option | Description | Selected |
|--------|-------------|----------|
| t3.micro, us-east-1 | Free tier 12 meses, ~$12-13/mês depois. Melhor custo-benefício. | ✓ |
| t3.micro, sa-east-1 | Mais perto do Brasil (~5-20ms), sem free tier, ~$18-20/mês. | |
| t4g.micro, us-east-1 (ARM) | ~20% mais barato que t3 longo prazo, sem free tier. | |

**User's choice:** t3.micro, us-east-1
**Notes:** Free tier + latência imperceptível para 1 usuário com acesso esporádico.

---

## PostgreSQL: Local vs RDS

| Option | Description | Selected |
|--------|-------------|----------|
| EC2 local + backup S3 | PostgreSQL na EC2, pg_dump diário para S3. Custo quase zero. | ✓ |
| PostgreSQL só na EC2 | Sem backup automático. Simples mas risco de perda. | |
| Amazon RDS | Managed, backup automático, ~$15-25/mês (estoura budget). | |

**User's choice:** EC2 local + backup S3
**Notes:** RDS consome o budget inteiro. pg_dump + S3 oferece proteção adequada.

---

## Gestão de Credenciais

| Option | Description | Selected |
|--------|-------------|----------|
| .env no EC2 via SCP | Zero custo, zero deps novas. Funciona com python-dotenv. | ✓ |
| SSM Parameter Store | Grátis, auditável, sem arquivo em disco. Exige boto3 + IAM. | |
| Secrets Manager | Rotação automática, ~$1.60/mês. Overkill para projeto pessoal. | |

**User's choice:** .env no EC2 via SCP
**Notes:** Simplicidade máxima, mesmo padrão do dev local.

---

## Sessão Telethon e Persistência

| Option | Description | Selected |
|--------|-------------|----------|
| EBS root volume (padrão) | Zero config. Persiste entre reboots. Risco só se terminate. | ✓ |
| EBS root + backup S3 | Cron do pg_dump pode copiar .session também. Proteção extra. | |
| EBS data volume dedicado | Volume separado. Sobrevive terminate. Exige mount/fstab. | |

**User's choice:** EBS root volume (padrão)
**Notes:** Instância tratada como permanente (pet). Recriar = re-autenticar SMS.

---

## Claude's Discretion

- Security Group ports/CIDR, Elastic IP, pg_hba.conf, schema migration, systemd units, budget alert config, S3 bucket setup

## Deferred Ideas

None — discussion stayed within phase scope
