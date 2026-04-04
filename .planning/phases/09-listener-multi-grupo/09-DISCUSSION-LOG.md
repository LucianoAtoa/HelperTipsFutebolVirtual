# Phase 9: Listener Multi-Grupo - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-04
**Phase:** 09-listener-multi-grupo
**Areas discussed:** Arquitetura multi-grupo, Identificação de mercado, Schema e deduplicação, Deploy e migração

---

## Arquitetura multi-grupo

| Option | Description | Selected |
|--------|-------------|----------|
| Handler único com lista | chats=[id1, id2] — Telethon nativo, event.chat_id identifica grupo. Menor mudança possível. | ✓ |
| Handlers separados por grupo | Um @client.on para cada grupo. Mais isolação, mais duplicação. | |
| Você decide | Claude escolhe a melhor abordagem técnica. | |

**User's choice:** Handler único com lista (Recommended)
**Notes:** Ambos os grupos usam o mesmo formato de sinal, parser funciona para os dois.

---

## Identificação de mercado

| Option | Description | Selected |
|--------|-------------|----------|
| mercado_id no upsert | Dicionário de normalização em store.py resolve entrada → mercado_id no momento do INSERT. FK pronta para P&L. | ✓ |
| String livre + lookup em query | Mantém entrada como TEXT, resolve mercado via JOIN dinâmico nas queries. | |
| Você decide | Claude escolhe a melhor abordagem técnica. | |

**User's choice:** mercado_id no upsert (Recommended)
**Notes:** Fases 10-13 são iminentes e precisam de JOIN confiável por mercado.

---

## Schema e deduplicação

| Option | Description | Selected |
|--------|-------------|----------|
| group_id NOT NULL + UNIQUE composta | Adiciona group_id BIGINT NOT NULL, UNIQUE(group_id, message_id). Dados antigos recebem group_id do grupo original via UPDATE. | ✓ |
| group_id nullable + NULLS NOT DISTINCT | Dados antigos ficam NULL, constraint PG16 trata NULLs. Menos invasivo. | |
| Você decide | Claude escolhe a melhor abordagem. | |

**User's choice:** group_id NOT NULL + UNIQUE composta (Recommended)
**Notes:** Volume de dados baixo, migration de baixo risco.

---

## Deploy e migração

| Option | Description | Selected |
|--------|-------------|----------|
| Migration + retroativo + restart | ALTER TABLE + UPDATE histórico com group_id original + systemctl restart. Gap de ~2s aceitável. | ✓ |
| Migration NULL + restart | Sem UPDATE retroativo. Dados antigos ficam NULL, queries tratam com IS NULL. | |
| Você decide | Claude escolhe a melhor estratégia de deploy. | |

**User's choice:** Migration + retroativo + restart (Recommended)
**Notes:** Gap de ~2s aceitável para frequência baixa de sinais.

---

## Claude's Discretion

- Ordem dos passos na migration SQL
- Índices adicionais em group_id
- Formato do log de warning para mercado desconhecido

## Deferred Ideas

None — discussion stayed within phase scope
