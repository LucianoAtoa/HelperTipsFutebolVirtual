---
phase: 17
slug: p-gina-de-configura-es
status: draft
shadcn_initialized: false
preset: none
created: 2026-04-04
---

# Phase 17 — UI Design Contract

> Visual and interaction contract para a Página de Configurações (/config).
> Gerado por gsd-ui-researcher. Verificado por gsd-ui-checker.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (Python/Dash — shadcn não aplicável) |
| Preset | not applicable |
| Component library | dash-bootstrap-components 2.0 (Bootstrap 5), tema DARKLY |
| Icon library | none (texto puro + Bootstrap classes) |
| Font | padrão DARKLY — Source Sans Pro / system-ui stack |

**Fonte:** CLAUDE.md stack + dashboard.py `external_stylesheets=[dbc.themes.DARKLY]`

---

## Spacing Scale

Declarado via Bootstrap 5 utility classes (equivalência ao 8-point scale):

| Token | Valor Bootstrap | Valor px | Uso |
|-------|----------------|----------|-----|
| xs | `gap-1` / `p-1` | 4px | Gaps de ícone, padding inline |
| sm | `mb-2` / `p-2` | 8px | Espaçamento compacto entre elementos |
| md | `mb-3` / `p-3` | 16px | Espaçamento padrão entre elementos |
| lg | `mb-4` / `p-4` | 24px | Padding de seção |
| xl | `mb-5` / `p-5` | 32–48px | Gaps de layout |

Exceções: nenhuma para esta fase.

**Fonte:** Bootstrap 5 spacing system (base 4px, escala x0.25rem)

---

## Typography

| Role | Tamanho | Weight | Line Height | Elemento Bootstrap |
|------|---------|--------|-------------|-------------------|
| Display (título da página) | 24px | 600 (semibold) | 1.2 | `html.H2` com `className="mt-4 mb-3"` |
| Heading (título de seção/card) | 18px | 600 (semibold) | 1.2 | `html.H5` ou `dbc.CardHeader` |
| Body (labels, descrições) | 14px | 400 (regular) | 1.5 | `html.Label`, `dbc.FormText` |
| Caption (avisos, help text) | 12px | 400 (regular) | 1.4 | `dbc.FormText`, `html.Small` |

Apenas 2 weights usados: **400 (regular)** e **600 (semibold)**.

**Fonte:** Padrão DARKLY + padrões estabelecidos em pages/home.py e pages/sinal.py

---

## Color

| Role | Valor DARKLY | Uso |
|------|--------------|-----|
| Dominant (60%) | `#222` / `#2b2b2b` (bg-dark) | Fundo da página, container principal |
| Secondary (30%) | `#303030` / `#3a3f44` (dbc.Card bg) | Cards de seção (Mercado Principal, Complementares, Preview) |
| Accent (10%) | `#375a7f` (Bootstrap `primary` no DARKLY) | Botão "Salvar Configurações" exclusivamente |
| Success | `#00bc8c` (Bootstrap `success`) | Alert de confirmação após salvar com sucesso |
| Destructive | `#e74c3c` (Bootstrap `danger`) | Alert de erro ao falhar persistência no banco |
| Muted | `#6c757d` | Labels de campos, FormText de ajuda |

Accent reservado para: **exclusivamente o botão primário "Salvar Configurações"** — nenhum outro elemento usa `color="primary"`.

**Fonte:** DARKLY theme tokens + custom.css existente + padrão pages/sinal.py

---

## Layout da Página /config

A página é dividida em 3 blocos verticais dentro de `dbc.Container(fluid=True)`:

### Bloco 1 — Campos de Progressão (por mercado)

Um `dbc.Card` por mercado (Over 2.5, Ambas Marcam), lado a lado em row com `lg=6`:

```
[ Card: Over 2.5                    ]  [ Card: Ambas Marcam               ]
  Stake Base (R$): [input numérico]      Stake Base (R$): [input numérico]
  Fator Progressão: [input numérico]     Fator Progressão: [input numérico]
  Máx. Tentativas: [input numérico]      Máx. Tentativas: [input numérico]
```

### Bloco 2 — Complementares (tabela por mercado)

Para cada mercado, uma tabela `dbc.Table` com colunas:

```
Complementar | Percentual (%) | Odd de Referência
```

Cada célula da coluna Percentual e Odd é um `dbc.Input` editável inline.

### Bloco 3 — Preview em Tempo Real

`dbc.Card` de largura total com 2 sub-seções side by side (`lg=6` cada):

**Preview de Stakes T1–T4 (CFG-03 — sem salvar)**
```
Complementar | T1 | T2 | T3 | T4
```
Recalcula via Dash callback sem round-trip ao banco ao alterar Bloco 1.

**Total em Risco por Tentativa (CFG-03)**
```
Tentativa | Principal | Complementares | Total
T1        |  R$ X     |  R$ Y          | R$ Z
T2        |  ...      |  ...           | ...
```
Recalcula ao alterar qualquer percentual do Bloco 2.

### Rodapé

Botão único `dbc.Button("Salvar Configuracoes", color="primary")` alinhado à direita.
`dbc.Alert` de feedback (success/danger) exibido abaixo do botão após callback de salvar.

---

## Estados de Interação

| Estado | Componente | Comportamento |
|--------|------------|---------------|
| Loading inicial | Toda a página | `dcc.Loading` wrapper no container de conteúdo; exibe spinner DARKLY até dados do banco carregarem |
| Edição (sem salvar) | Inputs Bloco 1 e 2 | Preview (Bloco 3) atualiza imediatamente via callback — sem debounce, sem round-trip ao banco |
| Salvando | Botão "Salvar" | `disabled=True` durante o callback de persistência; restaura após conclusão |
| Sucesso ao salvar | Alert success | `dbc.Alert("Configuracoes salvas com sucesso.", color="success", dismissable=True)` abaixo do botão; duração visual: persiste até próxima interação ou dismiss manual |
| Erro ao salvar | Alert danger | `dbc.Alert("Erro ao salvar. Tente novamente.", color="danger", dismissable=True)` com orientação de ação |
| Página carregada com defaults | Qualquer input | Nenhum badge ou indicador — defaults carregados silenciosamente (CFG-05) |

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Título da página | "Configuracoes de Mercado" |
| Primary CTA | "Salvar Configuracoes" |
| Success feedback | "Configuracoes salvas com sucesso." |
| Error feedback | "Erro ao salvar. Verifique a conexao com o banco e tente novamente." |
| Empty state (sem config no banco) | Nenhum estado vazio visível — defaults são carregados transparentemente nos inputs (CFG-05) |
| Label stake base | "Stake Base (R$)" |
| Label fator progressao | "Fator de Progressao" |
| Label max tentativas | "Max. Tentativas" |
| Label percentual | "Percentual (%)" |
| Label odd referencia | "Odd de Referencia" |
| Header preview stakes | "Preview de Stakes por Tentativa" |
| Header total risco | "Total em Risco por Tentativa" |
| Ações destrutivas | Nenhuma nesta fase — salvar sobrescreve config mas sem prompt de confirmação (ferramenta pessoal, 1 usuário) |

**Fonte:** Requirements CFG-01 a CFG-05 + decisão de escopo (ferramenta pessoal sem múltiplos perfis)

---

## Componentes dbc Utilizados

| Componente | Prop relevante | Uso na página |
|------------|---------------|---------------|
| `dbc.Container` | `fluid=True` | Container raiz da página |
| `dbc.Row` / `dbc.Col` | `lg=6` | Dois cards de mercado lado a lado |
| `dbc.Card` + `dbc.CardHeader` + `dbc.CardBody` | — | Seções Over 2.5, Ambas Marcam, Preview |
| `dbc.Label` | `html_for` | Labels de formulário acessíveis |
| `dbc.Input` | `type="number"`, `min`, `step`, `id` | Inputs editáveis stake/fator/max/percentual/odd |
| `dbc.FormText` | — | Texto de ajuda abaixo dos inputs |
| `dbc.Table` | `striped=True`, `hover=True`, `size="sm"` | Tabela de complementares e tabelas de preview |
| `dbc.Button` | `color="primary"`, `id="btn-salvar"` | CTA único de salvar |
| `dbc.Alert` | `color="success"/"danger"`, `dismissable=True`, `is_open` | Feedback após salvar |
| `dcc.Loading` | `type="default"` | Spinner no carregamento inicial |
| `dcc.Store` | `storage_type="memory"` | Estado efêmero dos campos antes de salvar (se necessário) |

**Nota:** `dbc.Input type="number"` é suficiente para todos os campos numéricos. Não usar `dcc.Input` — manter consistência com DARKLY.

---

## Callback Architecture (guia para executor)

Esta seção documenta o contrato de interação sem prescrever implementação interna:

| Trigger | Output | Banco? | Notas |
|---------|--------|--------|-------|
| `dcc.Location` pathname=="/config" | Popula todos os inputs com valores do banco | Sim (leitura) | `get_mercado_config` + `get_complementares_config` para cada mercado |
| Qualquer input do Bloco 1 muda | Atualiza tabela Preview T1–T4 | Não | Função pura testável (STATE.md: Phase 17 concern) |
| Qualquer input do Bloco 2 muda | Atualiza tabela Total em Risco | Não | Função pura testável |
| Clique "btn-salvar" | Persiste no banco + exibe Alert | Sim (escrita) | UPDATE mercados + UPDATE complementares |

**Restrição crítica (STATE.md):** Preview T1–T4 deve ser calculado via função pura Python sem round-trip ao banco — o callback deve ser leve o suficiente para atualizar a cada keystroke sem lag perceptível.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | not applicable | not applicable — stack Python/Dash |
| third-party | none | not applicable |

Stack Python/Dash não usa npm registry. Todos os componentes são pacotes PyPI já instalados.

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
