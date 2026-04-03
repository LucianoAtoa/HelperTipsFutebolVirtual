# Phase 2: Core Dashboard - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-03
**Phase:** 02-core-dashboard
**Areas discussed:** Layout e visual, Simulação de ROI, Filtros, Tabela de histórico

---

## Layout e Visual

| Option | Description | Selected |
|--------|-------------|----------|
| Tema escuro fixo (DARKLY) | Visual de trading, sem fadiga visual, zero config extra | ✓ |
| Tema claro fixo (FLATLY) | Melhor em ambientes claros, template Plotly padrão funciona | |
| Toggle claro/escuro | Flexível, dep extra (dash-bootstrap-templates) | |

**User's choice:** Tema escuro fixo (DARKLY)
**Notes:** Layout vertical com KPI cards → filtros → gráficos → tabela

---

## Simulação de ROI

| Option | Description | Selected |
|--------|-------------|----------|
| Stake fixa sem Gale | Baseline conservador, simples | |
| Stake fixa + toggle Gale | Reflete comportamento real do grupo com 4 tentativas | ✓ |
| Tabela de odds por tentativa | Máxima flexibilidade, UI complexo | |

**User's choice:** Stake fixa com toggle Gale
**Notes:** Defaults R$10 stake, odd 1.90. Campo tentativa já existe no banco.

---

## Comportamento dos Filtros

| Option | Description | Selected |
|--------|-------------|----------|
| Dropdowns horizontais reativos + Reset | Compacto, reatividade imediata, padrão Dash | ✓ |
| Sidebar fixa lateral | Espaço ilimitado, padrão BI | |
| Dropdowns com botão Apply + Reset | Evita queries intermediárias | |

**User's choice:** Dropdowns horizontais reativos com Reset
**Notes:** Filtros compostos liga + entrada simultâneos. DatePickerRange opcional.

---

## Tabela de Histórico

| Option | Description | Selected |
|--------|-------------|----------|
| DataTable nativo (todas as colunas) | Zero deps extras, sort nativo | |
| DataTable com colunas seletivas | Tabela mais limpa, oculta algumas | |
| Dash AG Grid | Substituto oficial, preparado para Dash 5 | ✓ |

**User's choice:** Dash AG Grid
**Notes:** 20 linhas/página, todas as 6 colunas, pendentes destacados, sort por coluna.

---

## Claude's Discretion

- Cores exatas dos KPI cards
- Formato dos números no ROI
- Largura relativa das colunas no AG Grid
- Posição do DatePickerRange
- Gráficos específicos da Fase 2

## Deferred Ideas

Nenhuma — discussão ficou dentro do escopo da fase.
