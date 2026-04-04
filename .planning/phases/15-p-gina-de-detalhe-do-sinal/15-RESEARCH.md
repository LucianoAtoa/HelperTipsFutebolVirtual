# Phase 15: Página de Detalhe do Sinal — Research

**Pesquisado:** 2026-04-04
**Domínio:** Dash Pages — nova página de detalhe por sinal com P&L breakdown (principal + complementares)
**Confiança:** HIGH

---

## Resumo

A Phase 15 cria `pages/sinal.py` — uma segunda página Dash Pages que recebe um query param `?id=<n>` via `dcc.Location` no shell, busca o sinal do banco por ID, recalcula P&L detalhado por complementar individual, e exibe um breakdown completo com card da entrada principal, tabela de complementares e totais no rodapé.

A navegação do AG Grid em `pages/home.py` para `/sinal?id=<n>` usa o evento `cellClicked` do dash-ag-grid (35.2.0) para escrever no `Output("url-nav", "href")` do `dcc.Location` já instalado no shell (`dashboard.py`). O botão "Voltar" usa `dcc.Link` ou `html.A` com href para `/`, preservando os filtros ativos via `dcc.Store` ou query params.

O principal gap de dados identificado: o `rowData` atual do AG Grid **não inclui o campo `id`** do sinal — ele precisa ser adicionado para que o cellClicked possa extrair o ID e navegar para `/sinal?id=<n>`.

A função `calculate_pl_por_entrada` em `queries.py` retorna totais agregados por sinal, mas **não** retorna o breakdown individual por complementar. Uma nova função `calculate_pl_detalhado_por_sinal(conn, signal_id, stake, gale_on)` é necessária para a página de detalhe.

**Recomendação principal:** Implementar em 2 plans: (1) TDD + nova função `get_sinal_detalhado` + `calculate_pl_detalhado_por_sinal` em `queries.py`; (2) `pages/sinal.py` com layout + callback + navegação AG Grid em `home.py` + verificação visual.

---

<phase_requirements>
## Phase Requirements

| ID | Descrição | Research Support |
|----|-----------|-----------------|
| SIG-01 | Usuário pode clicar em um sinal no histórico (AG Grid) e navegar para a página de detalhe | `cellClicked` do dag.AgGrid → `Output("url-nav", "href")` no shell; `id` precisa ser adicionado ao `rowData` |
| SIG-02 | Página exibe card da entrada principal com mercado, odd, stake, resultado (GREEN/RED), horário e lucro/prejuízo | Nova função `get_sinal_detalhado(conn, signal_id)` + `calculate_pl_detalhado_por_sinal` retorna dados do principal |
| SIG-03 | Página exibe lista de cada entrada complementar com nome, odd, stake, resultado validado pelo placar (GREEN/RED/N/A), horário e lucro/prejuízo | `calculate_pl_detalhado_por_sinal` retorna lista por complementar; `validar_complementar` já existe |
| SIG-04 | Página exibe totais consolidados: investido total, retorno total, lucro líquido | Soma de principal + complementares — calculado na mesma função nova |
| SIG-05 | Página tem botão para voltar ao dashboard | `dcc.Link(href="/")` ou `dcc.Location` write-back; preservação de filtros via `dcc.Store` |
| SIG-06 | Página trata sinais inexistentes/inválidos com mensagem amigável | Guard clause no callback: `if not sinal: return layout_not_found` |
</phase_requirements>

---

## Standard Stack

### Core (sem novas dependências)

| Biblioteca | Versão | Propósito | Por que |
|-----------|--------|-----------|---------|
| Plotly Dash | 4.1.0 (instalado) | Pages routing, callbacks, `dcc.Location` | `use_pages=True` já ativo; `pages/sinal.py` usa mesmo padrão de `pages/home.py` |
| dash-ag-grid | 35.2.0 (instalado) | Evento `cellClicked` para navegação do grid | Propriedade `cellClicked` nativa disponível como `Input` desde dag 2.x |
| dash-bootstrap-components | 2.0.x (instalado) | Cards, tabelas, botões para layout da página de detalhe | Mesma biblioteca usada em `home.py` |
| psycopg2-binary | 2.9.x (instalado) | Query por ID único no banco | Mesma conexão sync usada em todo o projeto |

### Instalação necessária

Nenhuma. O stack existente cobre completamente a Phase 15.

---

## Architecture Patterns

### Estrutura de arquivos: estado alvo

```
helpertips/
├── dashboard.py           # SEM MUDANÇA — shell com dcc.Location(id="url-nav") já presente
├── pages/
│   ├── __init__.py        # SEM MUDANÇA
│   ├── home.py            # MODIFICADO — rowData inclui "id"; callback de cellClicked adicionado
│   └── sinal.py           # NOVO — página de detalhe do sinal
├── queries.py             # MODIFICADO — novas funções: get_sinal_detalhado, calculate_pl_detalhado_por_sinal
└── tests/
    ├── test_dashboard.py  # SEM MUDANÇA
    ├── test_queries.py    # MODIFICADO — testes para as novas funções de queries
    └── test_sinal_page.py # NOVO — testes estruturais da página de detalhe
```

### Pattern 1: Registro da nova página

**O que é:** `pages/sinal.py` começa com `dash.register_page(__name__, path="/sinal")`. O callback lê `dcc.Location.search` (a parte `?id=<n>` da URL) para extrair o ID.

```python
# pages/sinal.py — primeiras linhas
import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
from urllib.parse import parse_qs, urlparse

dash.register_page(__name__, path="/sinal")

layout = html.Div([
    dcc.Location(id="sinal-url", refresh=False),
    html.Div(id="sinal-content"),
])

@callback(
    Output("sinal-content", "children"),
    Input("sinal-url", "search"),   # recebe "?id=42"
)
def render_sinal(search):
    # parse search param
    params = parse_qs((search or "").lstrip("?"))
    signal_id = params.get("id", [None])[0]
    ...
```

**Atenção:** `dcc.Location` com `id="sinal-url"` é colocado DENTRO de `pages/sinal.py` (diferente do `url-nav` do shell). Este componente local captura a URL da página corrente quando `sinal.py` está renderizado — padrão documentado para leitura de query params em páginas Dash Pages.

### Pattern 2: Navegação do AG Grid via `cellClicked`

**O que é:** Em `pages/home.py`, um novo `@callback` lê `Input("history-table", "cellClicked")` e escreve `Output("url-nav", "href")`.

```python
# Em pages/home.py — NOVO callback
@callback(
    Output("url-nav", "href"),
    Input("history-table", "cellClicked"),
    prevent_initial_call=True,
)
def navigate_to_sinal(cell_clicked):
    if not cell_clicked:
        return no_update
    row_data = cell_clicked.get("rowData", {})
    signal_id = row_data.get("id")
    if signal_id is None:
        return no_update
    return f"/sinal?id={signal_id}"
```

**Dependência crítica:** O campo `id` precisa estar em `rowData` do AG Grid. Atualmente NÃO está — o loop em `home.py` (linha 919–929) monta `row_data` sem incluir `"id": sig.get("id")`. Isso DEVE ser corrigido nesta fase.

### Pattern 3: `url-nav` no shell para navegação cross-page

**O que é:** O componente `dcc.Location(id="url-nav", refresh="callback-nav")` já está instalado em `dashboard.py` (Phase 14). Qualquer página pode escrever `Output("url-nav", "href")` para navegar sem full page reload.

**Por que funciona:** `url-nav` está no shell, que persiste entre páginas. Não é desmontado ao navegar para `/sinal`.

**Validação:** `refresh="callback-nav"` foi adicionado na Phase 14 exatamente para este padrão.

### Pattern 4: Botão "Voltar" preservando filtros

Duas abordagens possíveis:

**Opção A (simples):** `dcc.Link("← Voltar", href="/")` — navega para home sem estado de filtros. Dashboard reinicializa com valores default.

**Opção B (filtros preservados):** `dcc.Store(id="filtros-ativos", storage_type="session")` no shell armazena o estado dos filtros. `pages/sinal.py` lê o Store e gera href de volta com filtros como query params.

**Recomendação:** Opção A para Phase 15. Os filtros têm valores default funcionais (Toda a Vida, Todos os mercados). Preservar estado de filtros é complexidade desnecessária — o SIG-05 diz "retorna ao dashboard", não "retorna com filtros preservados". Opção B pode ser implementada em v1.4 se o usuário solicitar.

### Anti-Patterns a Evitar

- **Anti-pattern: `dcc.Location` no shell com `refresh=True`:** Causa full page reload. O shell já tem `refresh="callback-nav"` — não alterar.
- **Anti-pattern: buscar todos os sinais e filtrar em Python:** A página de detalhe deve fazer `SELECT ... WHERE id = %s` — uma query por ID, não carregar todos os sinais.
- **Anti-pattern: reutilizar `calculate_pl_por_entrada` para detalhe individual:** Essa função retorna totais agregados por sinal — sem breakdown por complementar individual. Não serve para SIG-03.
- **Anti-pattern: `id` como campo oculto via columnDefs hidden:** Melhor incluir `id` no `rowData` mas não no `columnDefs` — o AG Grid inclui campos extras no `rowData` sem exibi-los.

---

## Don't Hand-Roll

| Problema | Não Construir | Usar Sim | Por Que |
|----------|--------------|---------|---------|
| URL routing para `/sinal?id=N` | Callback manual `dcc.Location.pathname` → switch/case | `dash.register_page(__name__, path="/sinal")` + `dcc.Location.search` | Dash Pages gerencia roteamento; menos boilerplate |
| Navegar de AG Grid sem reload | `window.location.href` via clientside callback | `Input("history-table", "cellClicked")` → `Output("url-nav", "href")` | Padrão nativo dag + dcc.Location `callback-nav` |
| Validação de complementares | Reimplementar regras de placar | `validar_complementar()` já em `queries.py` | Risco de divergência se reimplementado |
| Parse de query params | Regex manual | `urllib.parse.parse_qs` (stdlib) | Robusto, trata edge cases (arrays, encoding) |

---

## Novas Funções Necessárias em `queries.py`

### `get_sinal_detalhado(conn, signal_id: int) -> dict | None`

Busca um sinal por ID com todos os campos necessários para a página de detalhe.

```python
def get_sinal_detalhado(conn, signal_id: int) -> dict | None:
    """
    Retorna sinal completo por ID para a página de detalhe.

    Retorna None se o sinal não existir (para SIG-06).

    Returns dict com: id, liga, entrada, resultado, placar, tentativa,
    received_at, mercado_id, mercado_slug
    """
    sql = """
        SELECT s.id, s.liga, s.entrada, s.resultado, s.placar,
               s.tentativa, s.received_at, s.mercado_id,
               m.slug AS mercado_slug
        FROM signals s
        LEFT JOIN mercados m ON s.mercado_id = m.id
        WHERE s.id = %s
    """
    with conn.cursor() as cur:
        cur.execute(sql, (signal_id,))
        row = cur.fetchone()
    if row is None:
        return None
    columns = ["id", "liga", "entrada", "resultado", "placar",
               "tentativa", "received_at", "mercado_id", "mercado_slug"]
    return dict(zip(columns, row))
```

### `calculate_pl_detalhado_por_sinal(sinal, complementares_config, stake, odd_principal, gale_on) -> dict`

Calcula P&L detalhado com linha por complementar (necessário para SIG-02, SIG-03, SIG-04).

A diferença de `calculate_pl_por_entrada`:
- Recebe **um único sinal** (dict), não uma lista
- Retorna um dict com `principal` (dict) e `complementares` (list[dict] — uma linha por complementar)
- Cada complementar inclui: nome_display, odd_ref, stake_comp, resultado_comp (GREEN/RED/N/A), lucro

```python
def calculate_pl_detalhado_por_sinal(
    sinal: dict,
    complementares_config: list[dict],
    stake: float,
    odd_principal: float,
    gale_on: bool,
) -> dict:
    """
    Calcula P&L breakdown completo de um sinal individual.

    Retorna:
    {
        "principal": {
            "stake": float, "odd": float, "resultado": str, "lucro": float,
            "investido": float, "retorno": float
        },
        "complementares": [
            {"nome": str, "odd": float, "stake": float, "resultado": str,
             "lucro": float, "investido": float, "retorno": float},
            ...
        ],
        "totais": {
            "investido": float, "retorno": float, "lucro": float
        }
    }
    """
```

---

## Common Pitfalls

### Pitfall 1: `id` ausente no rowData do AG Grid

**O que dá errado:** O callback `navigate_to_sinal` lê `cell_clicked["rowData"]["id"]` mas o campo não existe — `row_data` em `home.py` não inclui `"id"` atualmente. O callback retorna `no_update` silenciosamente, sem navegação.

**Por que acontece:** O loop atual (linha 919) monta dicts sem incluir o `id` do sinal. Foi uma omissão intencional (o ID não é exibido na tabela), mas precisa estar presente para a navegação.

**Como evitar:** Adicionar `"id": sig.get("id")` ao dict de cada row em `row_data`. O AG Grid inclui campos extras no `rowData` mas só exibe os campos declarados em `columnDefs` — sem impacto visual.

**Sinal de alerta:** Clicar em linha do grid não navega, mas também não dá erro no console.

### Pitfall 2: `dcc.Location` em `sinal.py` x `url-nav` no shell — confusão de responsabilidades

**O que dá errado:** Usar `Output("url-nav", "search")` para ler o query param em vez de um `dcc.Location` local em `sinal.py`. O `url-nav` no shell tem `refresh="callback-nav"` — ele é para **escrita** (navegação), não para leitura do estado atual da URL.

**Como evitar:** `pages/sinal.py` tem seu próprio `dcc.Location(id="sinal-url", refresh=False)`. O callback usa `Input("sinal-url", "search")` para ler `?id=<n>`. O shell `url-nav` é somente Output para escrita.

### Pitfall 3: ID inexistente retorna erro 500 sem guard

**O que dá errado:** `get_sinal_detalhado(conn, signal_id)` retorna `None` quando o ID não existe. Sem guard, o callback tenta acessar `sinal["entrada"]` e levanta `TypeError`.

**Como evitar:** Guard clause logo no início do callback de render:

```python
if sinal is None:
    return html.Div([
        html.H4("Sinal não encontrado"),
        html.P(f"O sinal #{signal_id} não existe ou foi removido."),
        dcc.Link("← Voltar", href="/"),
    ])
```

**Sinal de alerta:** Acessar `/sinal?id=999999` retorna página em branco ou erro no console.

### Pitfall 4: `signal_id` como string (não int) ao passar para query

**O que dá errado:** `parse_qs("?id=42")` retorna `{"id": ["42"]}` — string, não int. Passar string para `WHERE s.id = %s` no PostgreSQL pode funcionar (cast implícito) mas é frágil e deve ser explicitado.

**Como evitar:** `signal_id = int(params.get("id", [None])[0])` com try/except:

```python
try:
    signal_id = int(params.get("id", [None])[0])
except (TypeError, ValueError):
    return layout_not_found
```

### Pitfall 5: `prevent_initial_call=True` ausente no callback de navegação

**O que dá errado:** Sem `prevent_initial_call=True`, o callback `navigate_to_sinal` dispara com `cellClicked=None` ao carregar a página — retorna `no_update` mas pode gerar log de warning.

**Como evitar:** Sempre usar `prevent_initial_call=True` em callbacks acionados por eventos de usuário (click, input) que não devem rodar no carregamento inicial.

---

## Code Examples

### Leitura de query param em Dash Pages

```python
# Source: https://dash.plotly.com/urls (oficial Plotly)
from urllib.parse import parse_qs

@callback(
    Output("sinal-content", "children"),
    Input("sinal-url", "search"),
)
def render_sinal(search):
    params = parse_qs((search or "").lstrip("?"))
    try:
        signal_id = int(params.get("id", [None])[0])
    except (TypeError, ValueError):
        return html.P("ID de sinal inválido.")
    # ...
```

### Navegação programática via AG Grid cellClicked

```python
# Source: dash-ag-grid docs — cellClicked event
@callback(
    Output("url-nav", "href"),
    Input("history-table", "cellClicked"),
    prevent_initial_call=True,
)
def navigate_to_sinal(cell_clicked):
    if not cell_clicked:
        return no_update
    signal_id = (cell_clicked.get("rowData") or {}).get("id")
    if signal_id is None:
        return no_update
    return f"/sinal?id={signal_id}"
```

### Estrutura mínima de `pages/sinal.py`

```python
import dash
from dash import dcc, html, callback, Input, Output, no_update
import dash_bootstrap_components as dbc
from urllib.parse import parse_qs

from helpertips.db import get_connection
from helpertips.queries import (
    get_sinal_detalhado,
    get_complementares_config,
    get_mercado_config,
    calculate_pl_detalhado_por_sinal,
)

dash.register_page(__name__, path="/sinal")

layout = html.Div([
    dcc.Location(id="sinal-url", refresh=False),
    html.Div(id="sinal-content"),
])

@callback(
    Output("sinal-content", "children"),
    Input("sinal-url", "search"),
)
def render_sinal(search):
    params = parse_qs((search or "").lstrip("?"))
    try:
        signal_id = int(params.get("id", [None])[0])
    except (TypeError, ValueError):
        return _layout_not_found(None)
    conn = get_connection()
    try:
        sinal = get_sinal_detalhado(conn, signal_id)
        if sinal is None:
            return _layout_not_found(signal_id)
        # ... buscar config complementares e calcular P&L ...
    finally:
        conn.close()
```

---

## Mudanças no Código Existente

### `helpertips/pages/home.py` — 2 mudanças pontuais

1. **Adicionar `"id"` ao rowData:** No loop de construção de `row_data` (linha ~919), adicionar `"id": sig.get("id")` ao dict. O AG Grid não exibe o campo pois não está em `columnDefs`.

2. **Novo callback `navigate_to_sinal`:** Adicionar `@callback(Output("url-nav", "href"), Input("history-table", "cellClicked"), prevent_initial_call=True)` após os callbacks existentes. Usa `no_update` se `cellClicked` não tem `rowData.id`.

### `helpertips/queries.py` — 2 novas funções

1. `get_sinal_detalhado(conn, signal_id) -> dict | None`
2. `calculate_pl_detalhado_por_sinal(sinal, complementares_config, stake, odd_principal, gale_on) -> dict`

### `helpertips/pages/sinal.py` — arquivo novo

Layout + callback de render que lê `?id=`, busca sinal, calcula P&L, monta breakdown.

---

## Environment Availability

> Fase de código/lógica pura — sem novas dependências externas.

| Dependência | Requerida Por | Disponível | Versão | Fallback |
|-------------|--------------|-----------|--------|---------|
| Python 3.12+ | Runtime | ✓ | 3.12.x | — |
| Dash 4.1.0 | Pages routing + callbacks | ✓ | 4.1.0 | — |
| dash-ag-grid | `cellClicked` event | ✓ | 35.2.0 | — |
| dash-bootstrap-components | Layout da página de detalhe | ✓ | 2.0.x | — |
| psycopg2-binary | `get_sinal_detalhado` query | ✓ | 2.9.x | — |
| pytest | Testes da fase | ✓ | 7.0+ | — |

**Sem dependências bloqueantes.**

---

## Validation Architecture

### Test Framework

| Propriedade | Valor |
|-------------|-------|
| Framework | pytest 7.0+ |
| Config file | `pyproject.toml` — `[tool.pytest.ini_options]` |
| Comando rápido | `python3 -m pytest tests/test_queries.py tests/test_sinal_page.py -x -q` |
| Suite completa | `python3 -m pytest -x -q` |

### Phase Requirements → Test Map

| Req ID | Comportamento | Tipo de Teste | Comando Automatizado | Arquivo Existe? |
|--------|--------------|---------------|---------------------|-----------------|
| SIG-01 | `navigate_to_sinal` retorna `/sinal?id=<n>` quando cellClicked tem rowData.id | unit | `python3 -m pytest tests/test_dashboard.py::test_navigate_to_sinal -x` | ❌ Wave 0 |
| SIG-01 | `navigate_to_sinal` retorna `no_update` quando rowData não tem id | unit | `python3 -m pytest tests/test_dashboard.py::test_navigate_to_sinal_no_id -x` | ❌ Wave 0 |
| SIG-01 | rowData do AG Grid inclui campo `id` | unit | `python3 -m pytest tests/test_dashboard.py::test_history_rowdata_includes_id -x` | ❌ Wave 0 |
| SIG-02/03/04 | `calculate_pl_detalhado_por_sinal` retorna principal + complementares + totais corretos (GREEN T1) | unit | `python3 -m pytest tests/test_queries.py::test_calculate_pl_detalhado_green_t1 -x` | ❌ Wave 0 |
| SIG-02/03/04 | `calculate_pl_detalhado_por_sinal` retorna principal + complementares + totais corretos (RED) | unit | `python3 -m pytest tests/test_queries.py::test_calculate_pl_detalhado_red -x` | ❌ Wave 0 |
| SIG-02/03/04 | `calculate_pl_detalhado_por_sinal` retorna N/A para complementares sem placar | unit | `python3 -m pytest tests/test_queries.py::test_calculate_pl_detalhado_sem_placar -x` | ❌ Wave 0 |
| SIG-05 | Página sinal.py tem link/button com href="/" | unit | `python3 -m pytest tests/test_sinal_page.py::test_sinal_page_has_back_button -x` | ❌ Wave 0 |
| SIG-06 | `get_sinal_detalhado` retorna None para ID inexistente | unit | `python3 -m pytest tests/test_queries.py::test_get_sinal_detalhado_not_found -x` | ❌ Wave 0 |
| SIG-06 | Callback `render_sinal` com ID inválido (string) retorna layout amigável sem exceção | unit | `python3 -m pytest tests/test_sinal_page.py::test_render_sinal_invalid_id -x` | ❌ Wave 0 |

### Sampling Rate

- **Por commit de task:** `python3 -m pytest tests/test_queries.py tests/test_sinal_page.py -x -q`
- **Por merge de wave:** `python3 -m pytest -x -q`
- **Phase gate:** Suite completa verde (212 existentes + novos) antes de `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_sinal_page.py` — novo arquivo; cobre SIG-05 e SIG-06 (testes estruturais sem DB)
- [ ] `tests/test_queries.py` — adicionar testes para `calculate_pl_detalhado_por_sinal` e `get_sinal_detalhado` (puro Python — sem DB para calculate_pl)
- [ ] `tests/test_dashboard.py` — adicionar testes para `navigate_to_sinal` callback e campo `id` no rowData

---

## State of the Art

| Abordagem Antiga | Abordagem Atual | Quando Mudou | Impacto |
|-----------------|----------------|-------------|---------|
| Modal/popup para detalhe (pre-Dash Pages) | Página separada via `dash.register_page` | Dash 2.5, junho 2022 | URL bookmarkável, componente isolado, sem callback cross-page |
| `window.location.href` via clientside callback | `Output("url-nav", "href")` com `refresh="callback-nav"` | Dash 2.9.2 | Navegação sem full page reload, sem JavaScript manual |
| Passar ID via `dcc.Store` entre páginas | Query param `?id=<n>` na URL | Dash 2.x (recomendação atual) | URL diretamente bookmarkável (preparação para NAV-01 em v1.4) |

---

## Open Questions

1. **Mostrar `received_at` como "horário" no card principal (SIG-02)**
   - O que sabemos: `signals.received_at` é `timestamp with time zone` no banco. A coluna `horario` (texto como "20:15") também existe nos sinais mas pode ser NULL para sinais antigos.
   - O que está em aberto: Usar `received_at.strftime("%d/%m/%Y %H:%M")` como "horário"? Ou `horario` se disponível?
   - Recomendação: Usar `received_at` formatado — sempre presente. `horario` é campo de parse do Telegram e pode ser NULL.

2. **N/A vs RED para complementares sem placar**
   - O que sabemos: `validar_complementar` retorna `None` quando `placar` é NULL. SIG-03 menciona "GREEN/RED/N/A".
   - O que está em aberto: Exibir "N/A" (não disponível) ou "-" para complementares sem placar? Qual P&L mostrar (0.0 ou "-")?
   - Recomendação: Exibir "N/A" como resultado e "R$ 0,00" como lucro. Consistente com como o dashboard principal trata sinais pendentes.

3. **Preservação de filtros no botão "Voltar" (SIG-05)**
   - O que sabemos: SIG-05 diz "retorna ao dashboard". Não especifica preservar filtros.
   - O que está em aberto: `dcc.Link(href="/")` reseta filtros para valores default (Toda a Vida, Todos). O usuário pode querer os filtros preservados.
   - Recomendação: Implementar com `href="/"` simples (Opção A). Preservar filtros é escopo de v1.4 (NAV-01). Documentar como decisão no PLAN.

---

## Project Constraints (from CLAUDE.md)

| Diretiva | Impacto na Phase 15 |
|---------|---------------------|
| Stack: Dash `>=4.1,<5` | `dash.register_page` e `dcc.Location.search` disponíveis — confirmado |
| Stack: Python 3.12+ | `urllib.parse.parse_qs` disponível na stdlib — sem restrição |
| GSD Workflow Enforcement | Fase executada via `/gsd:execute-phase` |
| Comunicação em pt-BR | RESEARCH.md, PLAN.md e outputs em português |
| `suppress_callback_exceptions=True` já configurado | Necessário para callbacks em `pages/sinal.py` — já presente no shell |
| `server = app.server` como WSGI entry | Sem mudança — `pages/sinal.py` não afeta o shell |

---

## Sources

### Primary (HIGH confidence)

- Codebase direto analisado:
  - `helpertips/dashboard.py` (shell com `url-nav` já presente)
  - `helpertips/pages/home.py` (AG Grid `history-table`, rowData sem `id`, callbacks existentes)
  - `helpertips/queries.py` (`get_sinal_detalhado` ausente, `calculate_pl_por_entrada` retorna totais sem breakdown por complementar, `validar_complementar` disponível)
  - `tests/test_dashboard.py` (212 testes passando, padrão TDD estabelecido)
- `.planning/STATE.md` — nota explícita: "calculate_pl_por_entrada retorna totais agrupados (não por complementar individual) — Phase 15 precisa de nova função `calculate_pl_detalhado_por_sinal` em queries.py"
- [Dash Multi-Page Apps — documentação oficial](https://dash.plotly.com/urls) — `register_page`, `dcc.Location.search`, query params

### Secondary (MEDIUM confidence)

- [dash-ag-grid `cellClicked` event](https://dash.plotly.com/dash-ag-grid/cell-click-selection) — evento nativo disponível como `Input`
- `dash-ag-grid.__version__` verificado: 35.2.0 (instalado)
- `dash.__version__` verificado: 4.1.0 (instalado)

### Tertiary (LOW confidence)

- Nenhuma fonte de baixa confiança usada como base para recomendações críticas.

---

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH — verificado diretamente no ambiente instalado
- Architecture: HIGH — segue padrão idêntico de `pages/home.py` já implementado; `url-nav` no shell já preparado
- Pitfalls: HIGH — Pitfall 1 (id ausente no rowData) verificado diretamente no código; demais baseados em análise direta do codebase
- Novas funções: HIGH — gap documentado explicitamente em STATE.md e confirmado por leitura de `calculate_pl_por_entrada`

**Research date:** 2026-04-04
**Valid until:** 2026-07-04 (90 dias — Dash Pages API estável; ag-grid API estável no 35.x)
