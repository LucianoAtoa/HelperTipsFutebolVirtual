---
phase: 6
slug: aws-infrastructure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | AWS-01 | smoke manual | SSH interativo | N/A (infra) | ⬜ pending |
| 06-01-02 | 01 | 1 | AWS-01 | manual (nmap) | `nmap -p 22,80,443,8050 ELASTIC_IP` | N/A (infra) | ⬜ pending |
| 06-02-01 | 02 | 1 | AWS-02 | smoke manual | `psql -U helpertips_user -d helpertips -c "SELECT 1"` | N/A (infra) | ⬜ pending |
| 06-02-02 | 02 | 1 | AWS-02 | smoke manual | `psql -c "SELECT COUNT(*) FROM signals"` | N/A (infra) | ⬜ pending |
| 06-02-03 | 02 | 1 | AWS-02 | unit (existente) | `pytest tests/test_db.py -x` | ✅ | ⬜ pending |
| 06-02-04 | 02 | 1 | AWS-03 | manual verificacao | Verificar AWS Budgets Console | N/A (config AWS) | ⬜ pending |
| 06-03-01 | 03 | 2 | AWS-04 | smoke manual | `ssh EC2 "stat -c '%a' ~/.env"` | N/A (config servidor) | ⬜ pending |
| 06-03-02 | 03 | 2 | AWS-04 | unit (existente) | `pytest tests/test_config.py -x` | ✅ | ⬜ pending |
| 06-03-03 | 03 | 2 | AWS-05 | smoke manual | Reiniciar instancia, verificar arquivo | N/A (infra) | ⬜ pending |
| 06-03-04 | 03 | 2 | AWS-05 | smoke manual | Executar backup script, checar S3 | N/A (infra) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. Testes unitarios existentes (test_db.py, test_config.py) cobrem os requisitos de codigo. Testes de infra (AWS-01, AWS-03, AWS-05) sao verificacoes manuais por natureza.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| EC2 acessivel via SSH | AWS-01 | Infraestrutura fisica | SSH para Elastic IP e verificar conexao |
| Security Group bloqueia portas nao autorizadas | AWS-01 | Regras de rede AWS | `nmap -p 22,80,443,8050 ELASTIC_IP` |
| PostgreSQL responde em localhost no EC2 | AWS-02 | Servico rodando na instancia | `psql -U helpertips_user -d helpertips -c "SELECT 1"` |
| Schema migrado — tabela sinais existe | AWS-02 | Estado do banco no servidor | `psql -c "SELECT COUNT(*) FROM signals"` |
| Budget alert ativo | AWS-03 | Configuracao no Console AWS | Verificar AWS Budgets Console |
| .env com chmod 600 | AWS-04 | Permissoes de arquivo no servidor | `stat -c '%a' /home/helpertips/.env` |
| .session persiste apos reboot | AWS-05 | Estado de volume EBS | Reiniciar instancia, verificar arquivo |
| Backup S3 funcional | AWS-05 | Integracao S3 | Executar script manualmente, checar bucket |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
