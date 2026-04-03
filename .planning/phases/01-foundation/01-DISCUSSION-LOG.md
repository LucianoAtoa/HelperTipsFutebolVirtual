# Phase 1: Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-03
**Phase:** 01-foundation
**Areas discussed:** Formato das mensagens, Saída do terminal, Estrutura do projeto, Tratamento de falhas

---

## Formato das Mensagens

| Option | Description | Selected |
|--------|-------------|----------|
| Copiar exemplos manualmente | Fornecer 10-20 mensagens reais do grupo para ancorar os regex. Menor risco. | ✓ |
| Regex best-effort, calibrar depois | Avançar com formato assumido, ajustar quando rodar com dados reais | |
| Script dump-only primeiro | Rodar listener em modo captura antes de implementar parser | |

**User's choice:** Copiar exemplos manualmente (Recomendado)
**Notes:** Usuário já monitora o grupo manualmente, custo mínimo para copiar exemplos. Testes ficam ancorados em realidade.

---

## Saída do Terminal

| Option | Description | Selected |
|--------|-------------|----------|
| rich library | Startup summary como Table/Panel, sinais com cores por resultado (green/red), integra com logging | ✓ |
| logging stdlib + plain text | Zero deps extras, fácil redirecionar para arquivo, sem cores | |
| print() + ANSI manual | Sem deps, controle total mas sem níveis de severidade | |

**User's choice:** rich library (Recomendado)
**Notes:** Terminal é a interface principal de operação. Rich oferece legibilidade superior para sessões longas.

---

## Estrutura do Projeto

| Option | Description | Selected |
|--------|-------------|----------|
| Package Python | Diretório helpertips/ com __init__.py, pyproject.toml mínimo, pytest resolve imports automaticamente | ✓ |
| Flat na raiz | listener.py, parser.py, store.py, db.py direto na raiz. Simples mas frágil | |
| Hybrid | Flat com tests/ separado. Meio-termo mas com débito técnico | |

**User's choice:** Package Python (Recomendado)
**Notes:** pytest está no plano desde a Fase 1. Fase 2 (Dash) importa helpertips.db como processo separado.

---

## Tratamento de Falhas

| Option | Description | Selected |
|--------|-------------|----------|
| Log + armazenar no banco | Warning imediato no terminal + tabela parse_failures com raw_text para análise posterior | ✓ |
| Só armazenar no banco | Tabela parse_failures sem log ativo. Menos ruído no terminal | |
| Só log warning | Alerta no terminal sem persistência. Contador perdido em restart | |

**User's choice:** Log + armazenar no banco (Recomendado)
**Notes:** Formato do grupo pode mudar sem aviso. Combinação garante visibilidade imediata + histórico para diagnóstico.

---

## Claude's Discretion

- Nomes exatos de colunas da tabela signals
- Formato exato do startup summary Panel/Table
- Estratégia de limpeza da tabela parse_failures
- Configuração de logging levels por módulo

## Deferred Ideas

None — discussion stayed within phase scope
