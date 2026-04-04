# Phase 12: Dashboard Mercados e Performance - Research

**Pesquisado:** 2026-04-04
**Dominio:** Plotly Dash 4.x — layout extension, callbacks, tabelas de dados
**Confianca:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Layout Config Mercados (DASH-03)**
- D-01: Cards separados por mercado — um card para Over 2.5 e outro para Ambas Marcam. Cada card tem header com principal (odd referencia, stake base, progressao Gale T1-T4) e tabela interna de complementares (slug, nome, percentual, odd ref, stakes T1-T4 calculados).
- D-02: Dados carregados via `get_mercado_config()` (principal) e `get_complementares_config()` (complementares) — queries ja existem em queries.py.
- D-03: Stakes T1-T4 calculados on-the-fly a partir do stake base do card de simulacao: T1=stake*%, T2=T1*2, T3=T1*4, T4=T1*8.

**Toggle Performance (DASH-04)**
- D-04: Toggle implementado com `dbc.RadioItems` usando `input_class_name="btn-check"` e labels `btn btn-outline-secondary` — mesmo pattern dos filtros de periodo da Phase 11.
- D-05: Modo "Percentual" mostra taxa green (%), taxa red (%), ROI (%). Modo "Quantidade" mostra greens (n), reds (n), total (n). Modo "P&L (R$)" mostra investido, retorno, P&L, ROI em reais.

**Visao Geral vs Por Mercado (DASH-04)**
- D-06: Reusar o filtro global de mercado existente (Dropdown de Phase 11) para controlar a granularidade da tabela de performance. Quando "Todos" selecionado -> visao geral (linhas agrupadas por entrada). Quando mercado especifico selecionado -> visao por mercado com principal + cada complementar como linha separada.
- D-07: Sem UI adicional para visao geral vs por mercado — o filtro global ja faz isso naturalmente.

**Posicionamento no Layout**
- D-08: Novas secoes substituem o `html.Div(id="analytics-placeholder")` existente. Ordem: Config Mercados -> Performance -> placeholder para Phase 13. Scroll continuo (sem accordions ou collapse).
- D-09: AG Grid de historico de sinais permanece apos as novas secoes. Ordem final: filtros globais -> KPIs -> simulacao -> config mercados -> performance -> historico -> (Phase 13 placeholder).

### Claude's Discretion

- Organizacao interna dos callbacks (se um callback master atualiza tudo ou callbacks separados por secao)
- CSS para estilos dos cards de config e tabela de performance
- Nomes dos IDs dos novos componentes
- Se tabela de performance usa AG Grid ou dash_table.DataTable
- Formatacao dos valores monetarios (R$ com 2 casas decimais, cores verde/vermelho)

### Deferred Ideas (OUT OF SCOPE)

- Grafico de barras empilhadas P&L por liga — Phase 13 (DASH-05)
- Equity curve com 3 linhas (principal, complementar, total) — Phase 13 (DASH-06)
- Donut chart de gale com distribuicao por tentativa — Phase 13 (DASH-07)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Descricao | Suporte da Pesquisa |
|----|-----------|---------------------|
| DASH-03 | Secao configuracao de mercados: painel read-only com principal (odd, stake, progressao) e tabela complementares (mercado, %, odd ref, stakes T1-T4) | `get_mercado_config()` e `get_complementares_config()` ja retornam todos os dados necessarios. Stakes T1-T4 calculados em Python puro no callback. Renderizacao via `dbc.Table` dentro de `dbc.Card`. |
| DASH-04 | Secao performance das entradas: tabela P&L por mercado (greens, reds, taxa, investido, retorno, P&L, ROI) com toggle percentual/quantidade/R$ e visao geral vs por mercado | `calculate_pl_por_entrada()` retorna lista de dicts com todos os campos necessarios. Agregacao por entrada (grupo) feita em Python. Toggle via `dbc.RadioItems` btn-check ja padronizado. Controle de granularidade via `filter-mercado` existente. |
</phase_requirements>

---

## Sumario

A Phase 12 estende o layout v1.2 do dashboard (criado na Phase 11) com duas novas secoes que substituem o `html.Div(id="analytics-placeholder")`. Todo o codigo de dados necessario ja existe em `queries.py` — nenhuma nova query SQL e necessaria. O trabalho e essencialmente de composicao de UI em Dash + Python puro para agregacao dos dados.

A secao Config Mercados (DASH-03) e puramente read-only: busca config do banco via queries existentes, calcula stakes T1-T4 em Python, e renderiza dois cards (um por mercado) com header + tabela interna. A secao Performance (DASH-04) agrega a saida de `calculate_pl_por_entrada()` por entrada/complementar, exibe em tabela com colunas condicionais controladas pelo toggle de visualizacao, e muda sua granularidade com o filtro global de mercado.

**Recomendacao principal:** Estender o callback master existente (`update_dashboard`) adicionando novos `Output` para as duas secoes. Isso evita duplicacao de chamadas ao banco e mantem consistencia com os filtros globais ja implementados.

---

## Standard Stack

### Core (ja instalado no projeto)

| Biblioteca | Versao | Proposito | Motivo |
|-----------|--------|-----------|--------|
| plotly dash | `>=4.1,<5` | Layout, callbacks, componentes | Stack definido no pyproject.toml |
| dash-bootstrap-components | `>=2.0` | Cards, tabelas, RadioItems | Stack definido, ja usado nos filtros de periodo |
| dash-ag-grid | `>=31.0` | Tabela de historico (ja existente) | Ja usado, opcional para tabela de performance |

### Sem novas instalacoes necessarias

Nenhum pacote novo e necessario. Todos os componentes usados nesta fase ja estao disponíveis nas dependencias atuais:
- `dbc.Card`, `dbc.CardBody`, `dbc.CardHeader`, `dbc.Table` — inclusos no dash-bootstrap-components
- `dbc.RadioItems` com btn-check — ja usado e testado (filtros de periodo)
- `dash.html.Div`, `dash.html.Span` — inclusos no dash core

---

## Architecture Patterns

### Estrutura de arquivos afetados

```
helpertips/
├── dashboard.py      # MODIFICAR: layout + callback master
├── queries.py        # NAO ALTERAR: funcoes ja existem
└── assets/
    └── custom.css    # MODIFICAR: adicionar estilos para tabela de performance (opcional)
tests/
└── test_dashboard.py # MODIFICAR: adicionar testes para novos IDs e logica de agregacao
```

### Pattern 1: Extensao do Callback Master

**O que e:** Adicionar novos `Output` ao callback `update_dashboard` existente em vez de criar callbacks separados.

**Quando usar:** Sempre que novos componentes dependam dos mesmos Inputs que o callback master ja recebe (filtros globais + parametros de simulacao).

**Por que:** Evita multiplas chamadas ao banco para os mesmos dados. O callback master ja tem `conn = get_connection()` e calcula `history`, `date_start`, `date_end`, `entrada`, `stake`, `odd`, `gale_on`. As novas secoes dependem de TODOS esses valores.

**Exemplo (baseado no codigo existente em dashboard.py):**

```python
# Adicionar novos Outputs na lista existente:
@callback(
    # ... outputs existentes (10 atualmente) ...
    Output("config-mercados-section", "children"),   # novo: DASH-03
    Output("performance-table",       "children"),   # novo: DASH-04
    # ... inputs existentes inalterados ...
)
def update_dashboard(periodo, custom_start, custom_end, mercado, liga, stake, odd, gale_on, _n):
    # ... logica existente inalterada ...

    # NOVO: Config Mercados (DASH-03)
    config_section = _build_config_mercados_section(conn, stake)

    # NOVO: Performance (DASH-04)
    perf_section = _build_performance_section(conn, history, entrada, stake, odd, gale_on, toggle_mode)

    return (
        # ... 10 valores existentes ...
        config_section,
        perf_section,
    )
```

**Alternativa descartada:** Callbacks separados por secao. Custaria 2-3 chamadas extras ao banco por refresh, duplicaria logica de `_resolve_periodo` e `_entrada_para_slug`.

### Pattern 2: Funcoes Helper de Construcao de Layout

**O que e:** Funções Python auxiliares que retornam componentes Dash, extraidas do callback para manter o callback legivel.

**Quando usar:** Quando a construcao de uma secao de layout e complexa (multiplos cards, tabelas aninhadas).

**Exemplo:**

```python
def _build_config_card_mercado(mercado_slug: str, nome: str, odd_ref: float, stake: float, comps: list[dict]) -> dbc.Card:
    """Constroi o card de config de um mercado (Over 2.5 ou Ambas Marcam)."""
    # header: odd ref, stake base, progressao T1-T4
    # body: dbc.Table com complementares e stakes calculados
    rows = []
    for comp in comps:
        pct = float(comp["percentual"])
        t1 = stake * pct
        rows.append(html.Tr([
            html.Td(comp["nome_display"]),
            html.Td(f"{pct*100:.0f}%"),
            html.Td(f"{comp['odd_ref']:.2f}"),
            html.Td(f"R$ {t1:.2f}"),
            html.Td(f"R$ {t1*2:.2f}"),
            html.Td(f"R$ {t1*4:.2f}"),
            html.Td(f"R$ {t1*8:.2f}"),
        ]))
    return dbc.Card([
        dbc.CardHeader(html.H6(nome, className="mb-0")),
        dbc.CardBody([
            html.P(f"Odd ref: {odd_ref:.2f} | Stake base: R$ {stake:.2f} | Progressao: 1x 2x 4x 8x",
                   className="text-muted small"),
            dbc.Table([html.Tbody(rows)], bordered=True, dark=True, hover=True, size="sm"),
        ])
    ], className="mb-3")
```

### Pattern 3: Agregacao de P&L por Entrada em Python Puro

**O que e:** Agrupar a lista de dicts retornada por `calculate_pl_por_entrada()` por entrada ou por complementar, dependendo do filtro de mercado ativo.

**Quando usar:** Sempre. A query retorna uma linha por sinal, a tabela de performance exibe uma linha por entrada agregada.

**Visao Geral (mercado = "Todos"):**
Agrupar por `entrada` (ex: "Over 2.5", "Ambas Marcam"). Cada grupo vira uma linha na tabela.

**Por Mercado (mercado especifico selecionado):**
Principal = uma linha. Cada complementar = uma linha separada. Dados de `calculate_roi_complementares()` com `por_mercado` ja retorna isso.

**Implementacao de referencia para agregacao:**

```python
from collections import defaultdict

def _agregar_por_entrada(pl_lista: list[dict]) -> list[dict]:
    """Agrega P&L por entrada (visao geral)."""
    grupos: dict[str, dict] = defaultdict(lambda: {
        "greens": 0, "reds": 0,
        "investido": 0.0, "retorno": 0.0, "lucro": 0.0
    })
    for row in pl_lista:
        g = grupos[row["entrada"] or "?"]
        g["greens"] += 1 if row["resultado"] == "GREEN" else 0
        g["reds"]   += 1 if row["resultado"] == "RED"   else 0
        g["investido"] += row["investido_total"]
        g["retorno"]   += row["retorno_principal"] + row["retorno_comp"]
        g["lucro"]     += row["lucro_total"]
    result = []
    for entrada_nome, g in grupos.items():
        total = g["greens"] + g["reds"]
        taxa = g["greens"] / total * 100 if total > 0 else 0
        roi = g["lucro"] / g["investido"] * 100 if g["investido"] > 0 else 0
        result.append({"entrada": entrada_nome, "taxa": taxa, "roi": roi, **g})
    return result
```

### Pattern 4: Toggle de Visualizacao com RadioItems btn-check

**O que e:** `dbc.RadioItems` com `input_class_name="btn-check"` para controlar quais colunas mostrar na tabela de performance.

**Ja implementado:** Exatamente este pattern e usado nos filtros de periodo em dashboard.py (L123-138). O CSS em `helpertips/assets/custom.css` ja faz override do contraste para DARKLY.

**ID do novo toggle:** `perf-toggle-view` (sugestao)

**Opcoes:**
```python
dbc.RadioItems(
    id="perf-toggle-view",
    options=[
        {"label": "Percentual", "value": "pct"},
        {"label": "Quantidade", "value": "qty"},
        {"label": "P&L (R$)",   "value": "pl"},
    ],
    value="pct",
    inline=True,
    input_class_name="btn-check",
    label_class_name="btn btn-outline-secondary btn-sm",
    label_checked_class_name="active",
)
```

**Atencao:** O toggle `perf-toggle-view` precisa ser registrado como `Input` no callback master para que a troca de modo re-renderize a tabela.

### Pattern 5: Tabela de Performance — dash_table.DataTable vs dbc.Table

**Decisao (Claude's Discretion):** Usar `dash_table.DataTable` para a tabela de performance, por tres razoes:

1. Suporta `style_data_conditional` para colorir P&L verde/vermelho sem JavaScript customizado
2. Suporta `hidden_columns` para implementar o toggle de modo sem reconstruir o layout
3. Ja e dependencia transitiva do Dash (sem instalacao extra)

**Alternativa AG Grid:** Mais poderoso mas requer mais configuracao JavaScript para coloracao condicional. Preferivel para tabelas grandes e editaveis; overengineering para tabela pequena (2-14 linhas).

**Exemplo de style_data_conditional para P&L:**

```python
style_data_conditional=[
    {
        "if": {"filter_query": "{lucro} > 0", "column_id": "lucro"},
        "color": "#28a745",
        "fontWeight": "bold",
    },
    {
        "if": {"filter_query": "{lucro} < 0", "column_id": "lucro"},
        "color": "#dc3545",
        "fontWeight": "bold",
    },
]
```

### Anti-Patterns a Evitar

- **Callback separado para cada secao:** Resulta em 3-4 chamadas ao banco por trigger. O callback master ja tem os dados necessarios.
- **Recalcular `get_signals_com_placar` separadamente:** `get_signal_history` ja e chamado no callback master; `get_signals_com_placar` e necessario para P&L e deve ser chamada unica dentro do mesmo `conn`.
- **Construir layout estaticamente com dados do banco no topo do modulo:** Dash executa o modulo em import time — dados do banco so devem ser buscados dentro de callbacks.
- **IDs de componentes repetidos:** `analytics-placeholder` precisa ser SUBSTITUIDO (D-08), nao ter filhos adicionados depois — Dash nao suporta multiplos componentes com o mesmo ID.

---

## Don't Hand-Roll

| Problema | Nao Construir | Usar | Motivo |
|----------|---------------|------|--------|
| Coloracao condicional de celulas | CSS class condicional manual | `dash_table.DataTable` `style_data_conditional` | API declarativa, suporta filter_query para valores positivos/negativos |
| Toggle de colunas | Esconder/mostrar com CSS | `dash_table.DataTable` `hidden_columns` | Prop nativa, zero JavaScript |
| Formatacao de moeda | f-string em cada celula | `dash_table.DataTable` `format` com `dash_table.FormatTemplate` | Ou f-string simples no dicionario de dados antes de passar para `data=` — mais simples |
| Agrupamento de dados | SQL GROUP BY novo | Python `defaultdict` sobre lista existente | `calculate_pl_por_entrada` ja retorna tudo; agrupamento em Python evita nova query |

---

## Pitfalls Comuns

### Pitfall 1: `analytics-placeholder` deve ser substituido, nao usado como container

**O que acontece:** Se `html.Div(id="analytics-placeholder")` for mantido como Output com `children=` recebendo a nova secao, o layout funciona. MAS se o planner tentar adicionar filhos via `app.layout` estaticamente E via callback, Dash pode entrar em conflito.

**Como evitar:** O `html.Div(id="analytics-placeholder")` vira o hook. O Output do callback aponta para `analytics-placeholder` e retorna a lista completa de componentes filhos. Nao adicionar componentes estaticos ao div apos a inicializacao.

### Pitfall 2: `calculate_pl_por_entrada` requer `get_signals_com_placar`, nao `get_signal_history`

**O que acontece:** O callback master usa `get_signal_history` para o AG Grid do historico. Para calcular P&L por entrada, e necessario `get_signals_com_placar` (que inclui `mercado_slug`, `placar`, e filtra apenas GREEN/RED resolvidos). Usar `get_signal_history` diretamente nao retorna `mercado_slug`.

**Como evitar:** Dentro do callback master, chamar `get_signals_com_placar(conn, ...)` como chamada adicional (mesma conexao), separada de `get_signal_history`.

**Referencia:** `get_signals_com_placar` esta em queries.py L457, recebe os mesmos parametros de filtro que `get_signal_history`.

### Pitfall 3: Visao "Por Mercado" requer tanto `calculate_pl_por_entrada` quanto `calculate_roi_complementares`

**O que acontece:** Quando mercado especifico selecionado, a tabela deve mostrar principal + cada complementar como linha separada. `calculate_pl_por_entrada` retorna dados por sinal, nao por complementar. `calculate_roi_complementares` retorna `por_mercado` (lista por complementar slug) com greens, reds, lucro, investido.

**Como evitar:** Para visao por mercado, usar `calculate_roi_complementares(...)[por_mercado]` para as linhas de complementares, e `calculate_roi` para a linha do principal. Para visao geral, usar `calculate_pl_por_entrada` agregado por entrada.

### Pitfall 4: Toggle `perf-toggle-view` como Input do callback master aumenta Output count

**O que acontece:** Adicionar `perf-toggle-view` como Input faz com que qualquer troca de modo de visualizacao re-execute TODO o callback master (incluindo queries ao banco).

**Alternativa mais performatica:** Callback separado apenas para o toggle, que recebe o output da tabela de performance como `State` e apenas reordena/esconde colunas sem re-query. Porem isso requer armazenar dados intermediarios em `dcc.Store`.

**Recomendacao:** Para esta fase (dados pequenos, dashboard pessoal), aceitar o re-fetch completo ao trocar o toggle. Usar `dcc.Store` e callback separado so se performance se tornar problema observavel.

### Pitfall 5: `mercado_slug` None para sinais sem mercado_id

**O que acontece:** `get_signals_com_placar` faz LEFT JOIN em mercados. Sinais historicos sem `mercado_id` retornam `mercado_slug=None`. `calculate_pl_por_entrada` faz fallback para `"over_2_5"` (L677: `mercado_slug = signal.get("mercado_slug") or "over_2_5"`).

**Como evitar:** Nao e um bug — o fallback esta correto. Mas a tabela de performance deve agrupar `None` como "Over 2.5" para consistencia visual.

### Pitfall 6: Stakes T1-T4 no card de config sao funcao do stake-input

**O que acontece:** O card de Config Mercados exibe stakes T1-T4 calculados (D-03: `T1=stake*%`, etc.). Esses valores mudam quando o usuario altera o `stake-input`. Logo o card NAO e estatico — precisa ser um Output do callback master.

**Como evitar:** Garantir que `config-mercados-over`, `config-mercados-ambas` (ou o container comum) sejam Outputs do callback master. Nao colocar esses componentes como layout estatico.

---

## Code Examples

### Calculo de Stakes T1-T4 para tabela de config

```python
# Source: CONTEXT.md D-03 + logica do projeto
def _calcular_stakes_gale(stake_base: float, percentual: float) -> tuple[float, float, float, float]:
    """Retorna (T1, T2, T3, T4) para um complementar dado stake base e percentual."""
    t1 = stake_base * percentual
    return t1, t1 * 2, t1 * 4, t1 * 8
```

### Verificar mercados disponiveis para cards de config

```python
# Source: queries.py get_mercado_config (L421)
# Ambos slugs sao seeds garantidos por ensure_schema() / db.py
MERCADOS_CONFIG = [
    ("over_2_5",   "Over 2.5"),
    ("ambas_marcam", "Ambas Marcam"),
]

def _build_config_mercados(conn, stake: float) -> list:
    """Retorna lista de componentes dbc.Card para cada mercado."""
    cards = []
    for slug, nome in MERCADOS_CONFIG:
        config = get_mercado_config(conn, slug)
        if config is None:
            continue
        comps = get_complementares_config(conn, slug)
        cards.append(_build_config_card_mercado(slug, nome, float(config["odd_ref"]), stake, comps))
    return cards
```

### Construcao da tabela de performance com toggle

```python
# Source: CONTEXT.md D-05
COLUNAS_PCT = ["entrada", "greens_pct", "reds_pct", "roi_pct"]
COLUNAS_QTY = ["entrada", "greens", "reds", "total"]
COLUNAS_PL  = ["entrada", "investido", "retorno", "lucro", "roi"]

def _get_colunas_visives(modo: str) -> list[str]:
    mapa = {"pct": COLUNAS_PCT, "qty": COLUNAS_QTY, "pl": COLUNAS_PL}
    return mapa.get(modo, COLUNAS_PCT)
```

### IDs sugeridos para novos componentes

```python
# IDs recomendados para novos componentes (Claude's Discretion)
"config-mercados-container"   # div substituindo analytics-placeholder (ou usar analytics-placeholder diretamente)
"perf-toggle-view"            # RadioItems toggle
"perf-table"                  # dash_table.DataTable de performance
```

---

## Validation Architecture

### Framework de Testes

| Propriedade | Valor |
|-------------|-------|
| Framework | pytest 7.x |
| Config | `pyproject.toml` `[tool.pytest.ini_options]` |
| Comando rapido | `python3 -m pytest tests/test_dashboard.py tests/test_queries.py -q` |
| Suite completa | `python3 -m pytest tests/ -q` |

### Mapeamento Requisitos -> Testes

| Req ID | Comportamento | Tipo | Comando | Arquivo existe? |
|--------|--------------|------|---------|----------------|
| DASH-03 | Layout tem IDs dos novos cards de config mercados | unit | `python3 -m pytest tests/test_dashboard.py::test_layout_has_required_component_ids -x` | Existente — precisa expandir `required_ids` |
| DASH-03 | `_build_config_card_mercado` calcula T1=stake*pct, T2=T1*2, T3=T1*4, T4=T1*8 | unit | `python3 -m pytest tests/test_dashboard.py::test_config_stakes_calculo -x` | Nao existe — Wave 0 gap |
| DASH-04 | Layout tem ID do toggle `perf-toggle-view` | unit | `python3 -m pytest tests/test_dashboard.py::test_layout_has_required_component_ids -x` | Existente — precisa expandir `required_ids` |
| DASH-04 | `_agregar_por_entrada` agrupa greens/reds/investido/lucro corretamente | unit | `python3 -m pytest tests/test_dashboard.py::test_agregar_por_entrada_visao_geral -x` | Nao existe — Wave 0 gap |
| DASH-04 | Modo "Percentual" retorna colunas corretas, modo "P&L (R$)" retorna colunas corretas | unit | `python3 -m pytest tests/test_dashboard.py::test_performance_toggle_colunas -x` | Nao existe — Wave 0 gap |
| DASH-04 | Valores P&L positivos recebem CSS text-success, negativos text-danger | unit | `python3 -m pytest tests/test_dashboard.py::test_performance_pl_color_logic -x` | Nao existe — Wave 0 gap |

### Taxa de Amostragem

- **Por commit de task:** `python3 -m pytest tests/test_dashboard.py tests/test_queries.py -q`
- **Por merge de wave:** `python3 -m pytest tests/ -q`
- **Phase gate:** Suite completa verde antes do `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_dashboard.py` — expandir `required_ids` com IDs dos novos componentes (DASH-03, DASH-04)
- [ ] `tests/test_dashboard.py::test_config_stakes_calculo` — verificar logica T1-T4
- [ ] `tests/test_dashboard.py::test_agregar_por_entrada_visao_geral` — verificar agregacao Python
- [ ] `tests/test_dashboard.py::test_performance_toggle_colunas` — verificar selecao de colunas por modo
- [ ] `tests/test_dashboard.py::test_performance_pl_color_logic` — verificar logica de cores (mesma logica dos KPIs existentes, apenas adaptar)

---

## State of the Art

| Abordagem Anterior | Abordagem Atual | Mudanca | Impacto |
|-------------------|-----------------|---------|---------|
| `analytics-placeholder` como div vazio | `analytics-placeholder` como Output do callback master retornando secoes novas | Phase 12 | Correto — sem breaking change |
| Nenhuma tabela de performance | `dash_table.DataTable` com `style_data_conditional` | Phase 12 | Coloracao declarativa sem JS |
| Toggle de periodo apenas | Toggle de periodo + toggle de modo de performance | Phase 12 | Mesmo pattern reutilizado |

---

## Open Questions

1. **Layout order — analytics-placeholder vs historico**
   - CONTEXT.md D-09 define: filtros -> KPIs -> simulacao -> config mercados -> performance -> historico -> placeholder Phase 13
   - O `html.Div(id="analytics-placeholder")` esta DEPOIS do AG Grid no layout atual (L242, apos L239 que fecha o card de historico)
   - O que sabe: o historico esta ANTES do placeholder no codigo atual
   - O que precisa ser verificado: se D-09 esta em conflito com D-08 (substituir placeholder)
   - **Recomendacao:** Reordenar o layout: mover o AG Grid de historico para DEPOIS das novas secoes, conforme D-09. O placeholder vira container das novas secoes e um novo placeholder menor ficara apos elas para Phase 13.

2. **`get_signals_com_placar` vs `get_signal_history` — overhead de duas queries**
   - O que sabe: `get_signal_history` e chamada para o AG Grid. `get_signals_com_placar` tem schema diferente (inclui `mercado_slug`, filtra apenas GREEN/RED)
   - O que e claro: precisam ser duas chamadas separadas (retornam dados diferentes)
   - **Recomendacao:** Aceitar duas queries na mesma conexao. Para ~1000 sinais o overhead e desprezivel.

---

## Environment Availability

Step 2.6: SKIPPED (sem dependencias externas novas — phase e puramente de codigo Python/Dash sobre stack ja instalado e funcional)

---

## Fontes

### Primarias (HIGH confidence)

- `helpertips/dashboard.py` L1-427 — layout v1.2 completo, callback master, helpers existentes
- `helpertips/queries.py` L379-760 — `get_mercado_config`, `get_complementares_config`, `calculate_pl_por_entrada`, `calculate_roi_complementares`
- `helpertips/assets/custom.css` — CSS de override DARKLY para btn-check
- `.planning/phases/12-dashboard-mercados-e-performance/12-CONTEXT.md` — decisoes bloqueadas D-01..D-09
- `tests/test_dashboard.py` — 20 testes existentes, suite completa em 0.73s

### Secundarias (MEDIUM confidence)

- `.planning/REQUIREMENTS.md` — DASH-03, DASH-04 requirements completos
- `.planning/helpertips_v1.2_spec.md` — especificacao de percentuais e odds dos complementares por mercado

---

## Metadata

**Breakdown de confianca:**
- Stack: HIGH — nenhuma dependencia nova, tudo ja instalado e funcional
- Architecture: HIGH — baseado em leitura direta do codigo existente
- Pitfalls: HIGH — identificados por analise estatica do codigo e das decisoes de contexto

**Data da pesquisa:** 2026-04-04
**Valido ate:** 2026-05-04 (stack estavel, sem dependencias de servicos externos em evolucao)
