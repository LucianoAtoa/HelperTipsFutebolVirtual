# Phase 14: Migração Multi-Page - Research

**Researched:** 2026-04-04
**Domain:** Dash Pages (`use_pages=True`) — refatoração de app single-file para estrutura `pages/`
**Confidence:** HIGH

---

## Summary

A Phase 14 é uma refatoração cirúrgica de `helpertips/dashboard.py` para a estrutura Dash Pages. O objetivo é migrar o dashboard existente (1003 LOC, um callback master, sem URL routing) para um app multi-page onde `dashboard.py` vira um shell mínimo e o conteúdo atual migra integralmente para `pages/home.py`. Nenhuma funcionalidade existente é alterada — o resultado visual e funcional pré e pós-migração deve ser idêntico.

A migração é necessária para desbloquear a Phase 15 (página de detalhe individual por sinal), que requer URL routing (`/sinal?id=<n>`) e um segundo arquivo de página. A estrutura Dash Pages é o padrão oficial desde Dash 2.5 (junho 2022) e está disponível no Dash 4.1.0 já instalado no projeto — sem novas dependências.

Os riscos desta fase são baixos mas específicos: `suppress_callback_exceptions=True` é obrigatório (callbacks de `pages/home.py` são "dinâmicos" do ponto de vista do shell), o gunicorn resolve `pages/` via `__name__` (já correto no projeto), e os testes atuais de `test_dashboard.py` importam `from helpertips.dashboard import app` e funções auxiliares diretamente — eles precisam de ajuste de import após a migração.

**Recomendação principal:** Migrar `dashboard.py` → `pages/home.py` em um único plano atômico com verificação imediata de que `pytest tests/test_dashboard.py` continua 34/34 verde após o move.

---

<phase_requirements>
## Phase Requirements

| ID | Descrição | Research Support |
|----|-----------|-----------------|
| MPA-01 | Dashboard migrado para Dash Pages (`use_pages=True`) com layout principal + `dash.page_container` | Padrão oficial Dash 4.x documentado; `use_pages=True` + `dash.page_container` no shell; `suppress_callback_exceptions=True` obrigatório |
| MPA-02 | Página home (`pages/home.py`) renderiza o dashboard atual sem regressões visuais ou funcionais | Todo o conteúdo de `app.layout` + callbacks + helpers migrados para `pages/home.py`; `dash.register_page(__name__, path="/")` no topo do arquivo |
</phase_requirements>

---

## Standard Stack

### Core (sem mudança — zero novas dependências)

| Biblioteca | Versão | Propósito | Por que |
|-----------|--------|-----------|---------|
| Plotly Dash | 4.1.0 (instalado) | Framework dashboard + `use_pages` routing | `use_pages=True` disponível desde Dash 2.5; nenhuma nova dep necessária |
| dash-bootstrap-components | 2.0.x (instalado) | Layout Bootstrap 5 | Sem mudança de API para esta fase |
| dash-ag-grid | 31.x (instalado) | Tabela histórico de sinais | Sem mudança de API para esta fase |

### Verificação de versão instalada

```bash
python3 -c "import dash; print(dash.__version__)"
# Output atual: 4.1.0 — confirma use_pages disponível
```

### Instalação necessária

Nenhuma. O stack existente cobre completamente a Phase 14.

---

## Architecture Patterns

### Estrutura de arquivos: estado alvo

```
helpertips/
├── dashboard.py           # MODIFICADO — vira shell mínimo (use_pages, page_container, dcc.Location)
├── pages/                 # NOVA pasta — criada nesta fase
│   └── home.py            # NOVO arquivo — recebe TODO o conteúdo atual de dashboard.py
├── queries.py             # SEM MUDANÇA
├── db.py                  # SEM MUDANÇA
├── store.py               # SEM MUDANÇA
└── assets/                # SEM MUDANÇA
```

### Pattern 1: Shell mínimo em `dashboard.py`

**O que é:** Após a migração, `dashboard.py` contém apenas a inicialização do app e um layout container. Todo conteúdo visual e todos os callbacks vão para `pages/home.py`.

**Quando usar:** Sempre que `use_pages=True` estiver ativo. O shell persiste entre navegações; as páginas são montadas/desmontadas.

```python
# dashboard.py — estado alvo após migração
import dash
import dash_bootstrap_components as dbc
from dash import dcc

app = dash.Dash(
    __name__,                                     # MANTER — gunicorn resolve pages/ via __name__
    use_pages=True,                               # NOVO — ativa roteamento automático
    suppress_callback_exceptions=True,            # NOVO — obrigatório para callbacks em pages/
    external_stylesheets=[dbc.themes.DARKLY],
    title="HelperTips \u2014 Futebol Virtual",
)
server = app.server  # WSGI callable para gunicorn — sem mudança

app.layout = dbc.Container([
    dcc.Location(id="url-nav", refresh="callback-nav"),  # NOVO — para navegação programática (Phase 15)
    dash.page_container,                                  # NOVO — renderiza página ativa
], fluid=True)

if __name__ == "__main__":
    import os
    debug = os.getenv("DASH_DEBUG", "false").lower() == "true"
    app.run(debug=debug)
```

### Pattern 2: Registro de página em `pages/home.py`

**O que é:** O arquivo de página começa com `dash.register_page(__name__, path="/")`. Todo o restante do conteúdo atual de `dashboard.py` (imports, helpers, MERCADOS_CONFIG, layout, callbacks) é movido para cá sem alteração.

**Quando usar:** Em todo arquivo dentro de `pages/`. O `path="/"` registra esta página como a rota raiz.

```python
# pages/home.py — primeiras linhas obrigatórias
import dash
from dash import dcc, html, callback, Input, Output, State, ctx, no_update
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
# ... todos os imports que estavam em dashboard.py ...

dash.register_page(__name__, path="/")   # NOVO — registra como rota "/"

# Todo o resto de dashboard.py vai aqui:
# - _ENTRADA_SLUG_MAP, _calcular_stakes_gale, _agregar_por_entrada, ...
# - MERCADOS_CONFIG, _get_colunas_visiveis, ...
# - layout = dbc.Container([...])   ← era app.layout
# - @callback toggle_datepicker(...)
# - @callback update_dashboard(...)
```

**Atenção crítica:** `layout` (não `app.layout`). Em `pages/home.py`, o layout é uma variável `layout`, não atribuição em `app.layout`.

### Pattern 3: `dcc.Location(refresh="callback-nav")` no shell

**O que é:** Componente no shell layout que serve como target de navegação programática. Callbacks em qualquer página podem escrever em `Output("url-nav", "href")` para navegar sem full page reload.

**Por que no shell:** Componentes do shell persistem entre navegações. Se `dcc.Location` estivesse dentro de `pages/home.py`, seria desmontado ao navegar — o callback de navegação não funcionaria.

**Disponibilidade:** `refresh="callback-nav"` disponível desde Dash 2.9.2. Confirmar com Dash 4.1.0: suportado.

### Pattern 4: `@callback` (não `@app.callback`) em `pages/home.py`

**O que é:** Em arquivos `pages/`, usa-se o decorator `@callback` importado de `dash` diretamente, não `@app.callback`.

**Por que:** `@app.callback` cria um acoplamento ao objeto `app` específico. Em `pages/`, a prática recomendada é `from dash import callback` e usar `@callback` — funciona com qualquer instância de app Dash Pages.

```python
# CORRETO em pages/home.py:
from dash import callback
@callback(Output(...), Input(...))
def minha_funcao(...):
    ...

# ERRADO em pages/home.py:
from helpertips.dashboard import app
@app.callback(Output(...), Input(...))
def minha_funcao(...):
    ...
```

**Status atual no projeto:** O `dashboard.py` existente já usa `@callback` (não `@app.callback`) — zero mudança necessária neste aspecto. Confirmar: linha 31 do dashboard.py tem `from dash import Input, Output, State, callback, ctx, dash_table, dcc, html, no_update`.

### Anti-Patterns a Evitar

- **Anti-pattern: callback cross-page no shell:** Colocar `Input("history-table", "cellClicked")` no `dashboard.py` shell quando `history-table` está em `pages/home.py` levanta `ID not found in layout`. Callbacks que leem de componentes de página devem ficar na mesma página.
- **Anti-pattern: `app.layout = dbc.Container([...todo conteúdo...])` no shell:** O shell deve conter apenas `dcc.Location` e `dash.page_container`. Todo o conteúdo visual vai em `pages/home.py` como variável `layout`.
- **Anti-pattern: `refresh=True` em `dcc.Location`:** Causa full page reload em toda navegação. Usar `refresh="callback-nav"`.
- **Anti-pattern: copiar em vez de mover:** O conteúdo de `dashboard.py` deve ser movido (não duplicado) para `pages/home.py`. Deixar o layout antigo em `dashboard.py` cria dois layouts conflitantes.

---

## Don't Hand-Roll

| Problema | Não Construir | Usar Sim | Por Que |
|----------|--------------|---------|---------|
| URL routing entre páginas | Callback manual `pathname → layout` com `dcc.Location` | `use_pages=True` + `pages/` folder | Padrão pré-Dash 2.5; mais boilerplate, nenhuma vantagem |
| Navegação sem reload | `refresh=True` ou `refresh=False` em `dcc.Location` | `refresh="callback-nav"` | Full reload perde estado dos filtros no home |
| Descoberta de páginas | Registry manual de rotas | `dash.register_page(__name__, path="/")` | Auto-descoberta no startup; menos código, zero risco de erro de registro |

---

## Common Pitfalls

### Pitfall 1: `suppress_callback_exceptions=True` ausente

**O que dá errado:** Sem `suppress_callback_exceptions=True`, o Dash valida ao iniciar que todos os `Input`/`Output` de todos os callbacks existem no `app.layout`. Com `pages/`, o layout de `pages/home.py` só é montado quando a URL é `/`. No startup, o Dash não encontra os IDs (ex: `"history-table"`) no shell layout mínimo e levanta `Exception: Callback references IDs not found in layout`.

**Por que acontece:** Dash Pages monta/desmonta layouts de página dinamicamente. O framework precisa ser instruído a não validar callbacks contra o layout estático do shell.

**Como evitar:** Adicionar `suppress_callback_exceptions=True` ao construtor `dash.Dash(...)` junto com `use_pages=True`.

**Sinal de alerta:** `Exception: Callback references ...` no startup após adicionar `use_pages=True`.

### Pitfall 2: `pages/` na raiz do projeto em vez de dentro de `helpertips/`

**O que dá errado:** Gunicorn em Linux resolve a pasta `pages/` relativa ao diretório do módulo declarado em `__name__`. Se `pages/` estiver em `/app/pages/` mas `__name__` aponta para `helpertips.dashboard` (cujo arquivo está em `/app/helpertips/`), o Dash não encontra a pasta e lança `A folder called pages does not exist`.

**Por que acontece:** `dash.Dash(__name__, use_pages=True)` usa `__name__` para determinar onde procurar `pages/`. `__name__` de `helpertips/dashboard.py` resolve para o diretório `helpertips/`.

**Como evitar:** Criar `helpertips/pages/` (ao lado de `dashboard.py`), não `pages/` na raiz. O projeto já passa `__name__` como primeiro argumento — isso está correto.

**Verificação:** `pages/home.py` deve estar em `helpertips/pages/home.py`.

### Pitfall 3: `app.layout` em vez de `layout` em `pages/home.py`

**O que dá errado:** Se `pages/home.py` contiver `app.layout = dbc.Container([...])`, o arquivo tentará importar o objeto `app` de `dashboard.py`, criando um import circular ou sobrescrevendo o shell layout do app com o conteúdo de home — quebrando `dash.page_container`.

**Como evitar:** Em `pages/home.py`, a variável de layout é `layout = dbc.Container([...])` — sem prefixo `app.`.

### Pitfall 4: Testes que importam diretamente de `dashboard.py` podem quebrar

**O que dá errado:** `tests/test_dashboard.py` atualmente importa `from helpertips.dashboard import app` e funções auxiliares como `_resolve_periodo`, `_agregar_por_entrada`, `_build_config_card_mercado`, etc. Após a migração, essas funções estarão em `pages/home.py`, não em `dashboard.py`. Os testes quebrarão com `ImportError`.

**Estado atual:** 34 testes passando em `test_dashboard.py`. A migração deve manter todos 34 verdes.

**Como evitar:** Atualizar os imports em `tests/test_dashboard.py` para apontar para os novos locais após o move:
- `from helpertips.dashboard import app` — permanece válido (`app` fica em `dashboard.py`)
- `from helpertips.dashboard import _resolve_periodo, _agregar_por_entrada, ...` → `from helpertips.pages.home import _resolve_periodo, _agregar_por_entrada, ...`

**Sinal de alerta:** `ImportError: cannot import name '_resolve_periodo' from 'helpertips.dashboard'` após a migração.

### Pitfall 5: `dcc.Location` com `id="url"` conflita com IDs existentes

**O que dá errado:** Se `pages/home.py` tiver algum componente com `id="url"` (improvável mas possível), e o shell adicionar `dcc.Location(id="url-nav", ...)`, não há conflito — desde que os IDs sejam distintos.

**Como evitar:** Usar `id="url-nav"` no shell (não `id="url"`) para evitar qualquer potencial de conflito com `id="url"` comum em templates copiados.

---

## Code Examples

### Verificação da migração bem-sucedida

Após a migração, este snippet deve funcionar sem erros:

```python
# Verificação manual via Python REPL:
from helpertips.dashboard import app, server
print(app.config.use_pages)           # True
print(app.config.suppress_callback_exceptions)  # True
print(list(dash.page_registry.keys())) # ['pages.home']
```

### Estrutura mínima de `pages/home.py`

```python
# Source: https://dash.plotly.com/urls (oficial Plotly)
import dash
from dash import dcc, html, callback, Input, Output, State, ctx, no_update
import dash_bootstrap_components as dbc
# ... demais imports de dashboard.py ...

dash.register_page(__name__, path="/")

# Todos os helpers de dashboard.py aqui:
# _ENTRADA_SLUG_MAP, _calcular_stakes_gale, _agregar_por_entrada, ...
# MERCADOS_CONFIG, _get_colunas_visiveis, make_kpi_card, ...
# _resolve_periodo, _build_config_mercados_section, ...
# _build_performance_section, _build_phase13_section, ...

layout = dbc.Container([
    # Exatamente o mesmo conteúdo de app.layout atual
    # Apenas retirar o dbc.Container externo se já houver um
], fluid=True)

@callback(...)
def toggle_datepicker(...):
    ...

@callback(...)
def update_dashboard(...):
    ...
```

### Checklist de IDs que devem permanecer acessíveis após migração

IDs verificados atualmente em `test_dashboard.py` via `collect_ids()` (devem continuar presentes em `layout` de `pages/home.py`):

```python
# IDs esperados pelos testes — todos devem estar em pages/home.py layout:
required_ids = {
    "filter-periodo", "filter-mercado", "filter-liga",
    "collapse-datepicker", "date-range",
    "kpi-total", "kpi-winrate", "kpi-pl", "kpi-roi",
    "kpi-streak-green", "kpi-streak-red",
    "history-table",
    "config-mercados-container", "perf-table",
    "analytics-phase13-container",
    # + IDs de Phase 12, 13 conforme test_layout_has_phase12_component_ids
}
```

---

## Runtime State Inventory

> Fase de refatoração de arquivos Python — sem rename de strings de banco ou dados persistidos. Nenhum dado de runtime é afetado pela mudança de `dashboard.py` para `pages/home.py`.

| Categoria | Itens Encontrados | Ação Necessária |
|-----------|------------------|-----------------|
| Dados armazenados | Nenhum — renomeação não afeta schema PostgreSQL nem dados | Nenhuma |
| Config de serviço ao vivo | gunicorn WSGI entry: `helpertips.dashboard:server` — `server` permanece em `dashboard.py` | Nenhuma — entry point não muda |
| Estado registrado no SO | systemd/processo: sem mudança de módulo de entrada | Nenhuma |
| Secrets/env vars | Nenhuma referência a `dashboard.py` em `.env` | Nenhuma |
| Build artifacts | `helpertips.egg-info/` — instalação editable via `pip install -e .`; o pacote `helpertips.pages` precisa ser descoberto | Verificar que `pyproject.toml` `[tool.setuptools.packages.find]` inclui `helpertips*` (já está configurado como `include = ["helpertips*"]`) |

**`helpertips.egg-info` e `pages/` subpacote:** O `pyproject.toml` já tem `include = ["helpertips*"]`, que incluirá `helpertips.pages` automaticamente. Confirmar que `helpertips/pages/__init__.py` é criado (arquivo vazio) para tornar `pages/` um subpacote Python importável.

---

## Validation Architecture

### Test Framework

| Propriedade | Valor |
|-------------|-------|
| Framework | pytest 7.0+ |
| Config file | `pyproject.toml` — `[tool.pytest.ini_options]` |
| Comando rápido | `python3 -m pytest tests/test_dashboard.py -x -q` |
| Suite completa | `python3 -m pytest -x -q` |

### Phase Requirements → Test Map

| Req ID | Comportamento | Tipo de Teste | Comando Automatizado | Arquivo Existe? |
|--------|--------------|---------------|---------------------|-----------------|
| MPA-01 | `use_pages=True` ativo em `app`; `dash.page_container` no layout do shell; `suppress_callback_exceptions=True` configurado | unit | `python3 -m pytest tests/test_dashboard.py::test_app_uses_pages -x` | ❌ Wave 0 |
| MPA-01 | `dcc.Location(id="url-nav")` presente no layout do shell | unit | `python3 -m pytest tests/test_dashboard.py::test_shell_has_url_nav -x` | ❌ Wave 0 |
| MPA-02 | `pages/home.py` registrado com `path="/"` | unit | `python3 -m pytest tests/test_dashboard.py::test_home_page_registered -x` | ❌ Wave 0 |
| MPA-02 | Todos os IDs obrigatórios presentes no layout após migração | unit | `python3 -m pytest tests/test_dashboard.py::test_layout_has_required_component_ids -x` | ✅ (existente — deve passar sem mudança) |
| MPA-02 | 34 testes existentes continuam verdes após migração | regressão | `python3 -m pytest tests/test_dashboard.py -x -q` | ✅ (34 testes existentes) |

### Sampling Rate

- **Por commit de task:** `python3 -m pytest tests/test_dashboard.py -x -q`
- **Por merge de wave:** `python3 -m pytest -x -q`
- **Phase gate:** Suite completa verde antes de `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_dashboard.py` — adicionar `test_app_uses_pages`: verifica `app.config.use_pages == True`, `app.config.suppress_callback_exceptions == True`
- [ ] `tests/test_dashboard.py` — adicionar `test_shell_has_url_nav`: verifica que `app.layout` contém componente com `id="url-nav"` e `dash.page_container`
- [ ] `tests/test_dashboard.py` — adicionar `test_home_page_registered`: verifica que `dash.page_registry` contém entrada com `path="/"`
- [ ] `tests/test_dashboard.py` — atualizar imports de funções auxiliares de `helpertips.dashboard` para `helpertips.pages.home` após migração

---

## Environment Availability

| Dependência | Requerida Por | Disponível | Versão | Fallback |
|-------------|--------------|-----------|--------|---------|
| Python 3.12+ | Runtime | ✓ | 3.12.x | — |
| Dash 4.1.0 | `use_pages=True` | ✓ | 4.1.0 | — |
| pytest | Testes de regressão | ✓ | instalado via `dev` extras | — |

**Sem dependências bloqueantes:** Toda a fase é implementável com o ambiente atual.

---

## Open Questions

1. **`dcc.Location(id="url-nav")` na Phase 14 ou somente na Phase 15?**
   - O que sabemos: `url-nav` só é usado quando a Phase 15 adicionar o callback de navegação do AG Grid. Na Phase 14, o componente ficaria sem uso mas não causaria problemas.
   - O que está em aberto: Incluir na Phase 14 antecipa a Phase 15 (reduz mudança futura em `dashboard.py`) mas adiciona componente sem função ainda.
   - Recomendação: Incluir `dcc.Location(id="url-nav", refresh="callback-nav")` já na Phase 14. Custo zero, prepara o terreno. O sucesso criteria da Phase 14 exige explicitamente `use_pages=True` + `dash.page_container` — e o `dcc.Location` no shell é parte do padrão de arquitetura documentado.

2. **`helpertips/pages/__init__.py` necessário?**
   - O que sabemos: Python requer `__init__.py` para tratar diretório como pacote importável. `pyproject.toml` tem `include = ["helpertips*"]` que inclui subpacotes.
   - Recomendação: Criar `helpertips/pages/__init__.py` vazio. Custo: zero. Risco de omitir: `ImportError` em algumas configurações de import/test.

---

## State of the Art

| Abordagem Antiga | Abordagem Atual | Quando Mudou | Impacto |
|-----------------|----------------|-------------|---------|
| `dcc.Location` + callback manual `pathname → layout` | `use_pages=True` + `pages/` folder | Dash 2.5, junho 2022 | Pages auto-descobre arquivos, URL routing automático, callbacks isolados por arquivo |
| `@app.callback` em arquivos de página | `from dash import callback; @callback` | Dash 2.x (recomendação atual) | Sem acoplamento ao objeto `app`; páginas são portáveis |

---

## Sources

### Primary (HIGH confidence)

- [Dash Multi-Page Apps — documentação oficial Plotly](https://dash.plotly.com/urls) — `use_pages=True`, `dash.register_page`, `def layout()`, query params, `page_container`
- [Dash Installation 4.1.0](https://dash.plotly.com/installation) — confirmação versão 4.1.0 instalada (`python3 -c "import dash; print(dash.__version__)"` → 4.1.0)
- Codebase direto: `helpertips/dashboard.py` (1003 LOC), `tests/test_dashboard.py` (34 testes, todos verdes), `pyproject.toml` — análise direta

### Secondary (MEDIUM confidence)

- [Plotly Community: gunicorn + pages/ folder fix](https://community.plotly.com/t/multi-page-app-pages-folder-undiscoverable-by-gunicorn-on-linux/67788) — pitfall crítico de deploy; solução via `__name__` reproduzida pela comunidade
- [Plotly Community: `dcc.Location` com `refresh="callback-nav"`](https://community.plotly.com/t/sharing-examples-of-navigation-without-refreshing-the-page-when-url-is-updated-in-a-callback-in-dash-2-9-2/74260) — navegação programática sem full reload; feature confirmada no PR oficial #2068

### Tertiary (LOW confidence)

- Nenhuma fonte de baixa confiança usada como base para recomendações críticas.

---

## Project Constraints (from CLAUDE.md)

| Diretiva | Impacto na Phase 14 |
|---------|---------------------|
| Stack: Dash `>=4.1,<5` | `use_pages=True` disponível nesta versão — confirmado |
| Stack: Python 3.12+ | Sem restrição nova |
| GSD Workflow Enforcement: usar GSD antes de editar arquivos | Planner deve respeitar — esta fase é executada via `/gsd:execute-phase` |
| Comunicação em pt-BR | RESEARCH.md, PLAN.md e outputs em português |
| `server = app.server` como WSGI callable para gunicorn | Permanece em `dashboard.py` — zero mudança no entry point do gunicorn |
| `__name__` como primeiro argumento em `dash.Dash(...)` | Já correto no projeto; obrigatório para `pages/` resolution via gunicorn |

---

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH — Dash 4.1.0 instalado e verificado; `use_pages=True` disponível desde Dash 2.5
- Architecture: HIGH — padrão documentado em docs oficiais; codebase analisado diretamente (1003 LOC, 34 testes verdes)
- Pitfalls: HIGH — pitfalls 1-3 de Dash Pages documentados em fontes oficiais e fórum Plotly; pitfall 4 (testes) por análise direta do código

**Research date:** 2026-04-04
**Valid until:** 2026-07-04 (90 dias — Dash Pages API é estável desde 2.5; mudanças de breaking são improváveis no 4.x)
