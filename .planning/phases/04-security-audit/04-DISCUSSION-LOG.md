# Phase 4: Security Audit - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-03
**Phase:** 04-security-audit
**Areas discussed:** Fix debug=True, README scope, Limpeza do histórico git

---

## Fix debug=True

| Option | Description | Selected |
|--------|-------------|----------|
| Env var (Recomendado) | debug=os.getenv('DASH_DEBUG', 'false').lower() == 'true' — liga com DASH_DEBUG=true no .env local, desligado por padrão | ✓ |
| Hardcode False | Simplesmente mudar para debug=False — mais simples, para debug local usa flag manual | |
| Claude decide | Escolher a melhor abordagem | |

**User's choice:** Env var (Recomendado)
**Notes:** Desligado por padrão é seguro em produção. Desenvolvedor liga localmente via .env.

---

## README scope

| Option | Description | Selected |
|--------|-------------|----------|
| Completo (Recomendado) | Descrição do projeto, stack, setup local (pip install, .env, PostgreSQL), como rodar listener + dashboard, aviso de segurança (.session), badges CI | ✓ |
| Mínimo | Descrição + setup básico apenas, sem screenshots ou badges | |
| Com screenshots | Completo + screenshots do dashboard dark theme e abas de analytics | |

**User's choice:** Completo (Recomendado)
**Notes:** Sem screenshots por enquanto — badges CI serão adicionados após Phase 5.

---

## Limpeza do histórico git

| Option | Description | Selected |
|--------|-------------|----------|
| Grep + confirmar (Recomendado) | Rodar grep no histórico por padrões de secrets. Se limpo, prosseguir sem BFG | ✓ |
| BFG preventivo | Rodar BFG Repo Cleaner mesmo que pareça limpo — reescreve histórico | |

**User's choice:** Grep + confirmar (Recomendado)
**Notes:** Histórico já parece limpo (git log -- .env *.session retornou vazio). Grep confirmatório é suficiente.

---

## Claude's Discretion

Nenhuma área delegada a Claude nesta discussão.

## Deferred Ideas

Nenhuma — discussão ficou dentro do escopo da fase.
