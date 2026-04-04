# Phase 10: Lógica Financeira - Research

**Researched:** 2026-04-04
**Domain:** Pure-Python financial logic / `queries.py` extension — no new infrastructure
**Confidence:** HIGH

## Summary

Phase 10 é de extensão, não de construção. Toda a infraestrutura de P&L já existe em `queries.py`: `calculate_roi()`, `calculate_roi_complementares()`, `validar_complementar()`, `get_complementares_config()`, `calculate_equity_curve()` e `calculate_streaks()` estão funcionais e testados (150 testes passando). O trabalho desta phase é estender estas funções para suportar o breakdown por mercado que o dashboard redesign (Phases 11-13) vai consumir.

As duas mudanças estruturais necessárias são: (1) adicionar filtro por `mercado_id` em `_build_where()` — as colunas já existem no banco desde Phase 9 — e (2) criar variantes das funções de agregação que retornem breakdowns separados por mercado (principal, complementar, total). O cálculo de P&L por entrada individual (FIN-02) requer uma nova query SQL que retorna cada sinal resolvido com seus atributos financeiros calculados on-the-fly via Python, não colunas materializadas.

A lógica de Gale já está corretamente implementada: tentativa 1 = 1x stake, tentativa 2 = 2x, tentativa 3 = 4x, tentativa 4 = 8x. Complementares têm stakes proporcionais ao mercado (percentual × stake_base × fator_gale). Os percentuais por mercado já estão nos seeds do banco (Over 2.5: 20%/1%/10%/1%/1%/1%/1% vs Ambas Marcam: 10%/1%/5%/1%/1%/1%/1%).

**Primary recommendation:** Estender `_build_where()` com parâmetro `mercado_id`, criar `get_signals_com_placar()` (query para cálculo financeiro por entrada), e adicionar `calculate_pl_por_entrada()` e `calculate_equity_curve_complementares()` como funções puras. Manter zero schema changes.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** P&L permanece como cálculo on-the-fly (puro Python, sem tabela nova). Stake e gale_on são parâmetros dinâmicos do dashboard — materializar valores absolutos seria ineficaz pois qualquer mudança de stake invalidaria toda a tabela.
- **D-02:** Estender `calculate_roi_complementares()` e `calculate_equity_curve()` para suportar breakdown por mercado (principal, complementar, total) — 3 linhas na equity curve.
- **D-03:** Volume baixo (~dezenas de sinais/dia, single user) não justifica materialização. Se volume crescer, revisitar como otimização futura.
- **D-04:** Stake base continua como input do dashboard (status quo). Sem persistência no banco, sem variável .env adicional.
- **D-05:** Dashboard Phases 11-13 usarão o mesmo input com filtros globais — stake como parâmetro de simulação, não dado fixo.
- **D-06:** Cálculo acontece on-the-fly no dashboard, nos callbacks do Dash. Sem trigger no listener, sem batch job.
- **D-07:** `calculate_roi_complementares()` já existe e funciona. Estender callbacks sem schema change nem migration na EC2.
- **D-08:** Mesmos 7 slugs de complementares para Over 2.5 e Ambas Marcam (status quo). Seeds e validators já corretos.
- **D-09:** Percentuais já diferem por mercado no banco: Over 2.5 (20%, 1%, 10%, 1%, 1%, 1%, 1%) vs Ambas Marcam (10%, 1%, 5%, 1%, 1%, 1%, 1%).
- **D-10:** Redesenhar complementares de Ambas Marcam é decisão estratégica de apostas — backlog quando houver dados de produção suficientes para comparar rentabilidade.

### Claude's Discretion

- Organização interna das funções (refatorar vs estender existentes)
- Nomes de parâmetros e assinaturas das funções estendidas
- Estratégia de teste (quais cenários de P&L cobrir)
- Se queries.py deve ser dividido em módulos menores

### Deferred Ideas (OUT OF SCOPE)

- Materialização de P&L no banco como otimização de performance (se volume crescer significativamente)
- Redesenho dos complementares de Ambas Marcam com mercados específicos (resultado exato, handicap)
- Stake diferenciada por mercado (coluna `stake_base` na tabela mercados)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FIN-01 | Cada sinal gera entradas complementares com stake proporcional (% da principal) e odds de referência configuráveis por mercado | `calculate_roi_complementares()` já faz o cálculo; `get_complementares_config()` já lê config do banco por mercado_slug. Extensão: nova função `get_signals_com_placar()` que retorna sinais com `mercado_id` e `mercado_slug` para alimentar as funções de P&L separadas por mercado. |
| FIN-02 | Cálculo de P&L por entrada (investido, retorno, lucro/prejuízo líquido) com Martingale progressivo de 4 tentativas (1x, 2x, 4x, 8x) | Gale já implementado em `calculate_roi()` e `calculate_roi_complementares()`. Lacuna: nenhuma função retorna P&L por entrada individual (cada sinal como linha com: investido, retorno, lucro, mercado). Nova `calculate_pl_por_entrada()` cobre isso. |
| FIN-03 | Complementares têm configuração diferenciada por mercado — Over 2.5 vs Ambas Marcam com % distintos | Seeds já corretos no banco. `get_complementares_config(mercado_slug)` já diferencia. Lacuna: `_build_where()` não filtra por `mercado_id` ainda — extensão necessária para que DASH-01 possa filtrar por mercado. |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12+ | Runtime para funções puras de P&L | Já definido — sem mudança |
| psycopg2-binary | >=2.9 | Driver PostgreSQL para queries filtradas por mercado | Já instalado — sem mudança |
| pytest | >=7.0 | Testes unitários das funções puras | 150 testes existentes — mesma infraestrutura |

### Sem novas dependências
Esta phase não requer nenhuma instalação adicional. Toda a stack já está instalada e funcional.

---

## Architecture Patterns

### Estrutura de Arquivos (sem mudanças)
```
helpertips/
├── queries.py    # ESTENDER: _build_where, novas funções de P&L
├── db.py         # SOMENTE LEITURA: schema já correto
├── store.py      # SOMENTE LEITURA: upsert já correto
└── dashboard.py  # SOMENTE LEITURA nesta phase
tests/
└── test_queries.py   # ADICIONAR: testes das novas funções
```

### Pattern 1: Extensão de `_build_where()` com filtro por `mercado_id`

**O que é:** Adicionar parâmetro `mercado_id` ao builder de WHERE clause parameterizado.

**Quando usar:** Todas as queries que precisam filtrar por mercado (Over 2.5 vs Ambas Marcam). Usado pelo DASH-01 para filtros globais.

**Assinatura proposta:**
```python
def _build_where(liga=None, entrada=None, date_start=None, date_end=None, mercado_id=None):
    conditions = ["1=1"]
    params = []
    # ... filtros existentes ...
    if mercado_id is not None:
        conditions.append("mercado_id = %s")
        params.append(mercado_id)
    return " AND ".join(conditions), params
```

**Impacto:** Todas as funções existentes que chamam `_build_where` continuam funcionando pois `mercado_id=None` é o default — zero breaking change.

### Pattern 2: Query `get_signals_com_placar()` — dados base para P&L financeiro

**O que é:** Query SQL que retorna sinais resolvidos com `mercado_id`, `mercado_slug`, `placar`, `tentativa`, `resultado`. Esta query alimenta as funções puras de P&L por entrada.

**Por que separada de `get_signal_history()`:** `get_signal_history()` não inclui `mercado_id` nem `mercado_slug` (JOIN mercados). FIN-01 e FIN-02 precisam saber o mercado para carregar a config de complementares correta.

**Assinatura proposta:**
```python
def get_signals_com_placar(
    conn,
    liga=None, entrada=None, date_start=None, date_end=None, mercado_id=None
) -> list[dict]:
    """
    Retorna sinais resolvidos (GREEN/RED) com mercado_id e mercado_slug.
    Inclui sinais com placar=NULL (REDs sem placar — complementares recebem RED).
    Ordenado por received_at ASC para cálculo cronológico da equity curve.

    Retorna list[dict] com chaves:
        id, resultado, placar, tentativa, mercado_id, mercado_slug, entrada, liga
    """
```

**SQL base:**
```sql
SELECT s.id, s.resultado, s.placar, s.tentativa,
       s.mercado_id, m.slug AS mercado_slug, s.entrada, s.liga
FROM signals s
LEFT JOIN mercados m ON s.mercado_id = m.id
WHERE s.resultado IN ('GREEN', 'RED') AND {where}
ORDER BY s.received_at ASC
```

### Pattern 3: `calculate_pl_por_entrada()` — P&L por sinal (para FIN-02)

**O que é:** Função pura Python que recebe lista de sinais (com mercado_slug) e config de complementares agrupada por mercado_slug. Retorna lista de dicts — um por sinal — com P&L discriminado.

**Por que necessária:** DASH-04 precisa de tabela P&L por mercado (principal + complementar separados). A função atual `calculate_roi_complementares()` agrega tudo numa só cifra — não permite breakdown linha a linha.

**Assinatura proposta:**
```python
def calculate_pl_por_entrada(
    signals: list[dict],
    complementares_por_mercado: dict[str, list[dict]],
    stake: float,
    gale_on: bool,
) -> list[dict]:
    """
    Para cada sinal, calcula:
        - P&L do mercado principal (investido_principal, lucro_principal)
        - P&L dos 7 complementares (investido_comp, lucro_comp, detalhes_por_comp)
        - P&L total combinado

    Retorna list[dict] com uma linha por sinal resolvido.

    complementares_por_mercado: dict de mercado_slug -> list[dict config]
    Obtido via: {slug: get_complementares_config(conn, slug) for slug in slugs}
    """
```

**Cálculo do investido/retorno principal:**
- `invested_principal = stake * gale_factor(tentativa)` onde gale_factor = (2^N - 1) se gale_on else 1
- `retorno_principal = winning_stake * odd_ref` se GREEN, else 0
- `lucro_principal = retorno_principal - invested_principal`

**Cálculo do investido/retorno complementares (por sinal):**
- Para cada complementar: `stake_comp = stake * percentual * gale_factor_comp(tentativa)`
- `resultado_comp = validar_complementar(regra, placar, resultado_principal)`
- `lucro_comp = stake_comp * (odd_ref_comp - 1)` se GREEN, else `-stake_comp`

### Pattern 4: `calculate_equity_curve_breakdown()` — 3 linhas (FIN-02 / DASH-06)

**O que é:** Extensão de `calculate_equity_curve()` que retorna 3 séries temporais: principal, complementar, total.

**Por que não reutilizar direto:** A `calculate_equity_curve()` atual só calcula o mercado principal (usa `odd` como parâmetro scalar). Complementares têm odds diferentes por slug e precisam de lógica de `validar_complementar()`.

**Assinatura proposta:**
```python
def calculate_equity_curve_breakdown(
    signals: list[dict],
    complementares_config: list[dict],
    stake: float,
    odd_principal: float,
    gale_on: bool,
) -> dict:
    """
    Retorna dict com chaves:
        x             — índices cronológicos [1, 2, ...]
        y_principal   — equity acumulado só do mercado principal
        y_complementar — equity acumulado só dos complementares
        y_total       — soma y_principal + y_complementar
        colors        — "#28a745" (GREEN) ou "#dc3545" (RED) por sinal
    """
```

### Pattern 5: Odd de referência por mercado (para cálculo do principal)

**Problema:** `calculate_roi()` recebe `odd` como parâmetro externo (inputado no dashboard). Para `calculate_pl_por_entrada()` e `calculate_equity_curve_breakdown()`, a odd do principal pode vir do banco (tabela `mercados.odd_ref`) ou do input do usuário — a decisão cabe ao dashboard.

**Recomendação:** Manter `odd` como parâmetro externo (status quo). O dashboard passa a odd atual de entrada (mesmo que seja do banco). Evita acoplamento do módulo de queries com decisão de UX.

**Query para obter odd_ref do mercado principal:**
```python
def get_mercado_config(conn, mercado_slug: str) -> dict | None:
    """Retorna {id, slug, nome_display, odd_ref, ativo} para um mercado."""
```

### Anti-Patterns a Evitar

- **Materializar P&L no banco:** Explicitamente proibido por D-01 e D-03.
- **Adicionar `mercado_id` como coluna nova:** Já existe desde Phase 9.
- **Criar novos arquivos de módulo:** `queries.py` continua como arquivo único (D-07 prioriza zero schema change; por simetria, zero estrutura nova).
- **Calcular Gale diferente do existente:** A fórmula em `calculate_roi()` é a correta e testada — replicar o mesmo padrão nas novas funções.
- **Filtrar por `entrada` string para mercado:** Usar `mercado_id` (int FK) nas queries SQL, não comparação textual de `entrada`.

---

## Don't Hand-Roll

| Problema | Não Construir | Usar Em Vez | Por Que |
|---------|-------------|-------------|-----|
| Lógica de Gale | Nova implementação | Padrão existente em `calculate_roi()` | Já correto, testado, formula: `stake * (2^N - 1)` |
| Validação de complementar | Nova lógica de placar | `validar_complementar()` + `_REGRA_VALIDATORS` | 7 validators corretos, edge cases cobertos |
| Config de complementares | Query manual em linha | `get_complementares_config(conn, mercado_slug)` | Já com JOIN mercados, filter ativo=TRUE |
| Builder de WHERE | f-string manual | `_build_where()` (estendido com `mercado_id`) | Parameterizado, sem f-string injection |
| Conversão Decimal→float | `Decimal(str(x))` | `float(comp["percentual"])` | Padrão existente em `calculate_roi_complementares()` |

---

## Common Pitfalls

### Pitfall 1: Gale aplicado ao acumulado vs à tentativa vencedora

**O que dá errado:** Calcular retorno sobre o acumulado total em vez de sobre a stake da tentativa vencedora.

**Por que acontece:** Confundir "total investido" com "stake apostada na última tentativa".

**Como evitar:** Replicar exatamente o padrão de `calculate_roi()`:
```python
accumulated_stake = stake * (2 ** tentativa - 1)   # total investido
winning_stake = stake * (2 ** (tentativa - 1))      # stake da tentativa que ganhou
net = winning_stake * (odd - 1) - (accumulated_stake - winning_stake)
```
**Sinal de alerta:** P&L positivo em GREEN T4 maior que em GREEN T1 com a mesma odd — indica cálculo correto. Se forem iguais, Gale não foi aplicado.

### Pitfall 2: RED sem placar em complementares

**O que dá errado:** Tentar fazer `validar_complementar()` com `placar=None` e esperar que o resultado seja `None`.

**Por que acontece:** Sinais RED do grupo Telegram não incluem placar (confirmado no conftest: `signal_red_with_placar` não tem placar no fixture). `validar_complementar()` retorna `"RED"` quando `placar=None` e `resultado_principal="RED"` (D-08).

**Como evitar:** Comportamento já correto — não alterar. Confirmar no teste que RED sem placar resulta em RED para todos os complementares.

### Pitfall 3: `mercado_id=NULL` em sinais históricos

**O que dá errado:** Filtrar por `mercado_id = 1` e não encontrar sinais históricos que têm `mercado_id IS NULL`.

**Por que acontece:** Phase 9 faz UPDATE retroativo de `group_id`, mas `mercado_id` de sinais históricos pode estar NULL se a entrada não mapeou.

**Como evitar:** Queries com filtro `mercado_id` devem funcionar bem — só sinais com o mercado especificado são retornados. O dashboard "Todos" omite filtro de `mercado_id` (default `None` em `_build_where()`). Documentar comportamento nos testes.

### Pitfall 4: Decimal do PostgreSQL em operações aritméticas

**O que dá errado:** `TypeError` ao multiplicar `Decimal` por `float` diretamente.

**Por que acontece:** `psycopg2` retorna campos `NUMERIC` do PostgreSQL como `decimal.Decimal`, não `float`.

**Como evitar:** Já tratado na implementação atual — `float(comp["percentual"])` e `float(comp["odd_ref"])` antes de qualquer aritmética. Replicar nas novas funções.

### Pitfall 5: Equity curve com sinais em ordem DESC vs ASC

**O que dá errado:** Curva de equity com P&L acumulado "decrescendo" visualmente quando deveria crescer.

**Por que acontece:** `get_signal_history()` retorna DESC (mais recente primeiro). `calculate_equity_curve()` reverte para ASC internamente. `get_signals_com_placar()` deve retornar ASC direto para simplificar.

**Como evitar:** `get_signals_com_placar()` usa `ORDER BY received_at ASC` — não requer reversão posterior.

---

## Code Examples

### Exemplo: P&L de um sinal GREEN tentativa 2 com Gale, stake=100

```python
# Fonte: padrão de calculate_roi() em helpertips/queries.py
stake = 100.0
tentativa = 2
odd = 2.30  # odd_ref Over 2.5 do banco

accumulated_stake = stake * (2 ** tentativa - 1)  # 100 * 3 = 300
winning_stake = stake * (2 ** (tentativa - 1))    # 100 * 2 = 200

net = winning_stake * (odd - 1) - (accumulated_stake - winning_stake)
# net = 200 * 1.30 - 100 = 260 - 100 = 160

invested = accumulated_stake  # 300
retorno = winning_stake * odd  # 200 * 2.30 = 460
```

### Exemplo: P&L de complementar over_3_5 (Over 2.5, 20%) GREEN tentativa 2

```python
# Fonte: padrão de calculate_roi_complementares() em helpertips/queries.py
percentual = 0.20  # float(comp["percentual"])
odd_ref = 4.00     # float(comp["odd_ref"])
tentativa = 2

stake_comp = stake * (2 ** tentativa - 1) * percentual  # 100 * 3 * 0.20 = 60
winning_comp = stake * (2 ** (tentativa - 1)) * percentual  # 100 * 2 * 0.20 = 40
net_comp = winning_comp * (odd_ref - 1) - (stake_comp - winning_comp)
# net_comp = 40 * 3.0 - 20 = 120 - 20 = 100
```

### Exemplo: P&L sinal RED tentativa 4 (Gale), stake=100

```python
tentativa = 4
accumulated_stake = stake * (2 ** tentativa - 1)  # 100 * 15 = 1500
net = -accumulated_stake  # -1500
invested = accumulated_stake  # 1500
retorno = 0
```

### Exemplo: Filtro por mercado via `_build_where()`

```python
# Após extensão desta phase
where, params = _build_where(mercado_id=1)  # 1 = over_2_5
# where = "1=1 AND mercado_id = %s"
# params = [1]
```

### Exemplo: Mapeamento de mercado_slug para mercado_id

```python
# Via store.py ENTRADA_PARA_MERCADO_ID (já existente)
MERCADO_SLUG_TO_ID = {
    'over_2_5': 1,
    'ambas_marcam': 2,
}
# Dashboard usa slug para get_complementares_config e id para _build_where
```

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >=7.0 |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `python3 -m pytest tests/test_queries.py -x -q` |
| Full suite command | `python3 -m pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FIN-01 | `get_signals_com_placar()` retorna mercado_id e mercado_slug | unit | `python3 -m pytest tests/test_queries.py::test_get_signals_com_placar -x` | ❌ Wave 0 |
| FIN-01 | Complementares Over 2.5: stakes 20%/1%/10%/1%/1%/1%/1% do principal | unit | `python3 -m pytest tests/test_queries.py::test_complementares_over_2_5_stakes -x` | ❌ Wave 0 |
| FIN-01 | Complementares Ambas Marcam: stakes 10%/1%/5%/1%/1%/1%/1% distintos | unit | `python3 -m pytest tests/test_queries.py::test_complementares_ambas_marcam_stakes -x` | ❌ Wave 0 |
| FIN-02 | GREEN T1: investido=stake, lucro=stake*(odd-1) | unit | `python3 -m pytest tests/test_queries.py::test_pl_green_t1 -x` | ❌ Wave 0 |
| FIN-02 | GREEN T2 (Gale): invested=3x stake, lucro=2x*(odd-1)-1x | unit | `python3 -m pytest tests/test_queries.py::test_pl_green_t2_gale -x` | ❌ Wave 0 |
| FIN-02 | GREEN T3 (Gale): invested=7x stake | unit | `python3 -m pytest tests/test_queries.py::test_pl_green_t3_gale -x` | ❌ Wave 0 |
| FIN-02 | GREEN T4 (Gale): invested=15x stake | unit | `python3 -m pytest tests/test_queries.py::test_pl_green_t4_gale -x` | ❌ Wave 0 |
| FIN-02 | RED T4: lucro=-15x stake (Gale), lucro=-1x stake (Fixa) | unit | `python3 -m pytest tests/test_queries.py::test_pl_red_t4 -x` | ❌ Wave 0 |
| FIN-02 | `calculate_equity_curve_breakdown()` retorna 3 séries (principal/comp/total) | unit | `python3 -m pytest tests/test_queries.py::test_equity_curve_breakdown -x` | ❌ Wave 0 |
| FIN-03 | `_build_where(mercado_id=1)` gera cláusula SQL correta | unit | `python3 -m pytest tests/test_queries.py::test_build_where_mercado_id -x` | ❌ Wave 0 |
| FIN-03 | `get_filtered_stats()` com mercado_id=1 filtra somente Over 2.5 | unit+db | `python3 -m pytest tests/test_queries.py::test_filtered_stats_por_mercado -x` | ❌ Wave 0 |

### Sampling Rate
- **Por commit de tarefa:** `python3 -m pytest tests/test_queries.py -x -q`
- **Por wave merge:** `python3 -m pytest tests/ -q`
- **Phase gate:** Full suite green (150 existentes + novos) antes do `/gsd:verify-work`

### Wave 0 Gaps

- [ ] Novos testes unitários para funções de P&L — todos em `tests/test_queries.py` (arquivo existente, só adicionar funções)
- [ ] Fixture de sinais com `mercado_id` e `mercado_slug` para testes de breakdown

Nota: não há gaps de framework ou configuração — infraestrutura de teste 100% existente.

---

## Environment Availability

Step 2.6: SKIPPED — phase é puramente code/config. Sem dependências externas novas. PostgreSQL já está disponível (testes DB passaram com 150 passed).

---

## Open Questions

1. **Assinatura de `calculate_pl_por_entrada()`: retornar lista de dicts ou dict de listas?**
   - O que sabemos: DASH-04 precisa de tabela P&L, DASH-06 precisa de séries temporais (equity curve).
   - O que está indefinido: se uma única função serve ambos os casos ou se faz sentido ter funções separadas.
   - Recomendação: duas funções separadas com responsabilidades distintas — `calculate_pl_por_entrada()` (lista de dicts, um por sinal) e `calculate_equity_curve_breakdown()` (dict de listas, uma por série).

2. **odd do mercado principal: banco ou input do dashboard?**
   - O que sabemos: tabela `mercados` tem `odd_ref` (2.30 para Over 2.5, 2.10 para Ambas Marcam). Dashboard atual tem input de odd como parâmetro livre.
   - O que está indefinido: D-04 diz stake continua como input — não menciona odd explicitamente.
   - Recomendação: manter `odd` como parâmetro externo (mesma assinatura de `calculate_roi()`). O planner pode optar por pré-popular com `mercados.odd_ref` como default.

---

## Sources

### Primary (HIGH confidence)

- `helpertips/queries.py` — lógica existente de Gale, validators, config de complementares — lido diretamente
- `helpertips/db.py` — schema `mercados` e seeds de percentuais por mercado — lido diretamente
- `tests/test_queries.py` — 79 testes cobrindo ROI e complementares — lido diretamente; 150 testes no total passando (confirmado via `python3 -m pytest`)
- `pyproject.toml` — config de pytest, versões das dependências — lido diretamente

### Secondary (MEDIUM confidence)

- `helpertips/store.py` — `ENTRADA_PARA_MERCADO_ID` confirma mapeamento de entrada para mercado_id — lido diretamente

---

## Metadata

**Confidence breakdown:**
- Funções existentes e suas assinaturas: HIGH — código lido diretamente
- Schema e seeds de complementares: HIGH — `db.py` lido diretamente, seeds confirmados
- Fórmula de Gale: HIGH — implementação lida e testes confirmados
- Assinaturas das novas funções propostas: MEDIUM — baseado em análise dos requisitos e código existente; Claude's Discretion autoriza ajuste

**Research date:** 2026-04-04
**Valid until:** 2026-05-04 (stack estável, sem dependências novas)
