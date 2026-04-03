---
phase: 4
slug: security-audit
status: draft
shadcn_initialized: false
preset: none
created: 2026-04-03
---

# Phase 4 — UI Design Contract

> Visual and interaction contract para Phase 4: Security Audit.
> Gerado por gsd-ui-researcher. Verificado por gsd-ui-checker.

---

## Nota de Escopo

Esta fase é exclusivamente de **segurança e documentação** — não há UI nova, telas novas, componentes novos ou interações de usuário a construir. Os 4 requisitos desta fase (SEC-01..04) produzem:

- Resultado de auditoria (bash output — sem UI)
- Uma linha de código Python alterada (`dashboard.py:997`)
- Um arquivo de texto atualizado (`.env.example`)
- Um arquivo Markdown criado (`README.md`)

O contrato de UI desta fase cobre exclusivamente: (1) o sistema de design já existente que não deve ser alterado, e (2) o contrato de copywriting do README.md como documento de usuário.

---

## Design System

| Property | Value | Source |
|----------|-------|--------|
| Tool | none (não-React) | RESEARCH.md — stack Python/Dash |
| Preset | not applicable | Stack não é React/Next.js/Vite — shadcn gate não se aplica |
| Component library | dash-bootstrap-components 2.x (Bootstrap 5) | dashboard.py imports |
| Theme | dbc.themes.DARKLY | dashboard.py linha 55 — não alterar nesta fase |
| Icon library | none | Codebase scan — sem uso de icon library |
| Font | System default (Bootstrap DARKLY herda) | Nenhuma fonte customizada detectada |

**shadcn gate:** Não executado. Projeto usa Python/Plotly Dash, não React/Next.js/Vite.

---

## Spacing Scale

> Aplicável ao README.md como documento Markdown e ao dashboard existente (sem alteração).

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Gaps inline de ícone (Bootstrap `gap-1`) |
| sm | 8px | Espaçamento compacto entre elementos (Bootstrap `p-2`, `m-2`) |
| md | 16px | Espaçamento padrão entre elementos (Bootstrap `p-3`) |
| lg | 24px | Padding de seção (Bootstrap `p-4`) |
| xl | 32px | Gaps de layout (Bootstrap `mb-4`) |
| 2xl | 48px | Quebras de seção maiores |
| 3xl | 64px | Espaçamento de página (não usado na fase atual) |

Exceptions: none — dashboard existente mantém Bootstrap spacing sem alteração.

---

## Typography

> Dashboard existente — não alterar nesta fase. Declarado para referência do executor.

| Role | Size | Weight | Line Height | Usage |
|------|------|--------|-------------|-------|
| Body | 14px | 400 (regular) | 1.5 | Texto de parágrafo, labels de filtro, células de tabela |
| Label | 14px | 600 (semibold) | 1.4 | Labels de KPI card, cabeçalhos de coluna de tabela |
| Heading | 20px | 600 (semibold) | 1.2 | Títulos de seção do dashboard (H4/H5 Bootstrap) |
| Display | 28px | 600 (semibold) | 1.1 | Valores numéricos de KPI (H3 Bootstrap) |

Source: Inferido do tema Bootstrap DARKLY — escala tipográfica padrão do Bootstrap 5.

**Weights system:** 400 (regular) + 600 (semibold) — 2 weights total. Display visual dominance is established by size (28px vs 20px heading), not by extra weight.

**Para o README.md (Markdown):**

| Role | Markdown Syntax | Equivalent Size |
|------|-----------------|-----------------|
| Title (H1) | `# Título` | ~28px (display) |
| Section (H2) | `## Seção` | ~22px (heading) |
| Subsection (H3) | `### Subseção` | ~18px |
| Body | Parágrafo | 16px (padrão GitHub) |
| Code | `` `inline` `` / code block | 13px monospace |

---

## Color

> Paleta do tema DARKLY (Bootstrap 5 dark). Não alterar nesta fase.

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `#222222` (DARKLY bg) | Background do container, superfície principal |
| Secondary (30%) | `#303030` (DARKLY card bg) | Cards, navbar, sidebars |
| Accent (10%) | `#375a7f` (DARKLY primary blue) | Botão primário, badges de status |
| Success | `#00bc8c` (DARKLY success) | KPI Greens, lucro positivo, win rate alto |
| Danger | `#e74c3c` (DARKLY danger) | KPI Reds, lucro negativo, alertas |
| Warning | `#f39c12` (DARKLY warning) | KPI Pendentes, linhas de benchmark |
| Info | `#3498db` (DARKLY info) | KPI Win Rate, equity curve |
| Muted | `#aaaaaa` | Texto secundário, labels de eixo em gráficos |

Accent reserved for: botão "Aplicar Filtros", badges de mercado no header — nunca para elementos puramente informativos.

Source: dashboard.py — `dbc.themes.DARKLY` + usos explícitos de `#28a745`, `#ffc107`, `#fd7e14`, `#dc3545`, `#17a2b8`, `#aaa` nos traces Plotly.

---

## Copywriting Contract

> Esta fase produz um README.md novo. O contrato abaixo especifica as seções obrigatórias e o tom de cada uma. Fonte: decisão D-02 (bloqueada pelo usuário).

| Elemento | Conteúdo Prescrito | Source |
|----------|-------------------|--------|
| README título | `# HelperTips — Futebol Virtual` | D-02 (CONTEXT.md) |
| README descrição | 2-3 linhas: o que o sistema faz, para quem, por quê | D-02 |
| README seção Stack | Tabela com: Python 3.12, Telethon, PostgreSQL, psycopg2-binary, Plotly Dash, dash-bootstrap-components, python-dotenv | RESEARCH.md stack |
| README seção "Setup Local" | Passos: clone, `pip install -e .`, copiar `.env.example` → `.env`, preencher variáveis, criar DB, rodar listener, rodar dashboard | D-02 |
| README seção "Deploy (AWS)" | Placeholder: "Consulte o guia de deploy completo (em elaboração — Phase 6-8)" | D-02 |
| README seção "Segurança — Arquivo .session" | Aviso explícito: o arquivo `.session` é um SQLite com o token de autenticação completo do Telegram. Qualquer pessoa com esse arquivo pode ler todas as mensagens da conta, incluindo grupos privados. Nunca commitar. Fazer backup separado. | RESEARCH.md Pitfall 4 |
| README seção Badges | `![CI](badge-placeholder)` — a ser preenchido após Phase 5 | D-02 |
| .env.example DASH_DEBUG comment | `# Set to true for local development hot-reload; false (default) in production` | RESEARCH.md D-04 |
| dashboard.py debug comment | `# Controlled via DASH_DEBUG env var — false by default (safe for production)` | RESEARCH.md D-01 |

**Tom do README:** Técnico e direto. Sem marketing. Público-alvo é o próprio desenvolvedor em 6 meses. Português brasileiro.

**Empty state:** Não aplicável — fase não cria telas com estados vazios.

**Error state:** Não aplicável — fase não cria flows interativos.

**Destructive actions:** Nenhuma ação destrutiva nesta fase. A auditoria git (SEC-01) é somente leitura. Nenhuma reescrita de histórico (BFG) foi aprovada — decisão D-03.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | not applicable — projeto não usa shadcn |
| npm / PyPI third-party | none | not applicable — fase não adiciona dependências |

Nenhuma nova dependência de biblioteca ou registry nesta fase. Ver RESEARCH.md: "Esta fase não adiciona nenhuma biblioteca."

---

## Interaction Contracts

> Nenhuma interação nova de usuário nesta fase. Referência dos pontos de interação existentes que não devem ser alterados.

| Interaction | Current Behavior | Change in Phase 4 |
|-------------|-----------------|-------------------|
| Dashboard hot-reload | `debug=True` — Dash DevTools ativo, REPL remoto exposto | Removido: `debug=True` → `os.getenv('DASH_DEBUG', 'false').lower() == 'true'` |
| Todas as outras interações | Inalteradas | Nenhuma alteração — fora do escopo |

---

## Component Inventory

> Componentes existentes que o executor DEVE conhecer mas NÃO alterar nesta fase.

| Component | File | Relevant to Phase 4 |
|-----------|------|---------------------|
| `app.run(debug=True, ...)` | `helpertips/dashboard.py:997` | Única linha de código a ser editada (SEC-02) |
| `.env.example` | `.env.example` | Arquivo a ser expandido (SEC-03) |
| `README.md` | `README.md` | Arquivo novo a ser criado (SEC-04) |
| `git history` | N/A | Verificação bash somente-leitura (SEC-01) |

Nenhum componente de UI novo será criado nesta fase.

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
