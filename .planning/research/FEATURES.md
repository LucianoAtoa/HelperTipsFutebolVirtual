# Feature Research

**Domain:** Signal detail page — sports betting analytics dashboard (futebol virtual)
**Researched:** 2026-04-04
**Confidence:** HIGH (for table stakes from domain patterns) / MEDIUM (for differentiators)

## Context

This milestone adds a dedicated signal detail page to the existing HelperTips dashboard. The
existing dashboard already has an AG Grid with signal history (data/hora, liga, mercado,
resultado, tentativa, placar, lucro_total). The detail page is reached by clicking a row in that
grid.

The "competitors" here are general-purpose bet tracker tools (Bet-Analytix, BettorEdge, OddsJam
Bet Tracker, Bettin.gs) since no direct equivalent for Telegram signal groups with complementary
market systems exists. Patterns from these tools define what feels complete.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that feel obviously missing if absent. The user is accustomed to bet trackers and knows
what a "bet detail" should show.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Identificacao do sinal (liga, mercado, data/hora, tentativa) | Todo tracker mostra o que foi apostado antes do resultado | LOW | Ja existe em `get_signal_history` — id, liga, entrada, horario, tentativa, received_at |
| Resultado principal com badge GREEN/RED | Ponto focal de qualquer detalhe de aposta | LOW | Campo `resultado` ja no banco |
| Placar final da partida | Context critico para futebol virtual — valida complementares | LOW | Campo `placar` ja no banco |
| Odd de referencia do principal | Usuario precisa saber o preco da aposta | LOW | Disponivel em `get_mercado_config` via mercado_slug |
| Stake do principal (com progressao Gale se tentativa > 1) | Quanto foi apostado no principal | LOW | Calculado por `calculate_pl_por_entrada` — investido_principal |
| Retorno e lucro/prejuizo do principal | P&L explicitamente separado do principal | LOW | Ja calculado: retorno_principal, lucro_principal |
| Lista de cada entrada complementar com resultado individual | Sistema de complementares e o diferencial do produto — usuario precisa ver cada um | MEDIUM | validar_complementar ja existe; complementares_config ja no banco |
| Odd, stake e resultado de cada complementar | Mesma logica do principal, por linha de complementar | MEDIUM | Requer iterar complementares_por_mercado com placar do sinal especifico |
| Totais consolidados (investido total, lucro total) | Visao financeira completa do sinal como unidade | LOW | Ja em `calculate_pl_por_entrada`: investido_total, lucro_total |
| Botao/link para voltar ao historico | Navegacao basica — sem isso a pagina e um beco sem saida | LOW | dcc.Link para '/' ou fechar modal |

### Differentiators (Competitive Advantage)

Features que vao alem do esperado dado o sistema especifico de sinais com Gale e complementares.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Decomposicao visual: principal vs complementares | Mostra claramente como o lucro e composto — algo que nenhum tracker generico faz pois nao conhece esse modelo | MEDIUM | dbc.Progress ou go.Bar dividido por componente |
| Badge de Gale com progressao acumulada | Tentativa 3 significa 7x stake acumulado — exibir "T3 = R$400 atual / R$700 acumulado total" da contexto que a lista nao da | LOW | Calculo ja em `calculate_pl_por_entrada` com gale_on=True |
| Destaque visual de complementar com odd alta que converteu | Ex: "Over 5+ converteu @ 10.46x — lucro R$+XX.XX" em destaque — raridade vale atencao | LOW | Condicional em resultado_comp == GREEN para comp com odd_ref > 10.0 |
| Timestamp horario_sinal vs received_at | Mostra quando o sinal foi emitido pelo grupo (horario) vs quando chegou no banco (received_at) — util para auditoria de latencia do listener | LOW | Ambos campos ja no banco |
| Link direto por URL com signal_id | Permite bookmarkar ou compartilhar um sinal especifico via /sinal/123 | MEDIUM | Requer Dash Pages ou dcc.Location com pathname parsing |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Edicao de resultado/placar inline na pagina de detalhe | Usuario quer corrigir erros do parser | Abre inconsistencia com fonte de verdade (Telegram); logica de reconciliacao complexa; fora de escopo do produto pessoal | Exibir o message_id do Telegram para referencia manual se necessario |
| Grafico de equity curve "com e sem este sinal" | Curiosidade natural — e se eu nao tivesse apostado aqui? | Requer recalcular curva inteira sem o sinal — JOIN e calculo pesado para beneficio cosmetico | Mostrar posicao do sinal na equity curve global ja existente no dashboard principal |
| Copiar bet slip formatado para clipboard | Util para compartilhar resultados | Complexidade JS inject no Dash; edge case de formatacao; nao e uso primario desta ferramenta pessoal | N/A — nao implementar |
| Historico de edicoes (audit trail) | Curiosidade sobre quantas vezes o parser editou o sinal | Requer tabela de auditoria separada; nao existe hoje | O message_id unico ja garante rastreabilidade no Telegram |

---

## Feature Dependencies

```
[Pagina de detalhe acessivel via click]
    └──requires──> [dcc.Store com signal_id OU dcc.Location com pathname]
                       └──requires──> [AG Grid selectionChanged callback]

[Lista de complementares com resultado individual]
    └──requires──> [Placar do sinal disponivel na pagina de detalhe]
                       └──requires──> [Query por signal_id retornando placar + mercado_slug]

[Totais consolidados]
    └──requires──> [Calculos de P&L por entrada complementar]
                       └──requires──> [get_complementares_config(mercado_slug)]

[Badge de Gale com acumulado]
    └──requires──> [Tentativa do sinal]
                       └──requires──> [Query por signal_id]

[Decomposicao visual principal vs complementares]
    └──requires──> [Lista de complementares com resultado individual]

[Botao voltar]
    (nenhuma dependencia tecnica — dcc.Link ou fechar modal)
```

### Dependency Notes

- **Pagina de detalhe requires AG Grid row click:** O componente `dag.AgGrid` ja tem
  `selectionChanged` como property observavel via callback. O signal_id pode ser passado via
  `dcc.Store` para um modal, sem necessidade de URL routing.

- **Lista de complementares requires placar:** `validar_complementar` ja existe em `queries.py`
  e aceita `(regra_validacao, placar, resultado)`. Precisa apenas do sinal completo por ID.

- **get_complementares_config requires mercado_slug:** ja disponivel via JOIN na query de sinais
  (`mercado_slug` retornado por `get_signals_com_placar`). Uma nova query `get_signal_by_id`
  precisa ser criada em `queries.py`.

---

## MVP Definition

### Launch With (v1 — Milestone v1.3)

Minimo que torna a pagina util e justifica a navegacao a partir do AG Grid.

- [ ] Header do sinal: liga, mercado, data/hora, tentativa, placar, badge GREEN/RED
- [ ] Card principal: odd, stake (com Gale), retorno, lucro — com coloracao verde/vermelho
- [ ] Lista de complementares: nome, odd, stake, resultado (GREEN/RED/N/A), lucro por linha
- [ ] Totais consolidados: investido total, retorno total, lucro liquido
- [ ] Botao voltar ao historico (ou fechar modal)

### Add After Validation (v1.x)

Features a adicionar se o MVP for validado como util no uso diario.

- [ ] Badge Gale com acumulado explicado ("T3: atual R$400 / acumulado R$700") — trigger: usuario
  confundir stake atual com acumulado ao revisar uma tentativa 3 ou 4
- [ ] Decomposicao visual principal vs complementares (stacked bar) — trigger: usuario querer
  entender visualmente a distribuicao do lucro
- [ ] Destaque de complementar de odd alta que converteu — trigger: ocorrer na pratica e usuario
  notar valor em ter destaque

### Future Consideration (v2+)

- [ ] Deep-link URL por signal_id (/sinal/123) — defer pois requer refatoracao para Dash Pages
- [ ] Navegacao entre sinais (anterior/proximo) — conveniencia de browse sequencial
- [ ] Timestamp de latencia (horario_sinal vs received_at) — valor baixo, dado analitico tecnico

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Header do sinal (liga, mercado, data, tentativa, placar, resultado) | HIGH | LOW | P1 |
| Card principal com financeiro (odd, stake, retorno, lucro) | HIGH | LOW | P1 |
| Lista complementares com resultado por linha | HIGH | MEDIUM | P1 |
| Totais consolidados | HIGH | LOW | P1 |
| Botao voltar / fechar | HIGH | LOW | P1 |
| Badge Gale com acumulado explicado | MEDIUM | LOW | P2 |
| Decomposicao visual principal vs complementares | MEDIUM | MEDIUM | P2 |
| Destaque complementar odd alta que converteu | LOW | LOW | P2 |
| Deep-link URL por signal_id | LOW | MEDIUM | P3 |
| Navegacao anterior/proximo entre sinais | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have para o milestone v1.3
- P2: Should have, adicionar na mesma milestone se couber no escopo
- P3: Deferir para milestone futura

---

## Competitor Feature Analysis

| Feature | Bet-Analytix / BettorEdge | OddsJam Bet Tracker | Nossa Abordagem |
|---------|---------------------------|---------------------|-----------------|
| Identificacao da aposta | Sport, league, bet type, date | Sport, market, date | Liga, mercado, data/hora, tentativa |
| Resultado e P&L | WIN/LOSS + profit/loss | WIN/LOSS + profit | GREEN/RED + lucro em R$ |
| Breakdown por componente | Nao (trackers genericos nao tem complementares) | Nao | Sim — principal + cada complementar individualmente |
| Odds e stake | Sim | Sim | Sim — com progressao Gale quando tentativa > 1 |
| Placar da partida | Nao (trackers de odds nao rastreiam placar) | Nao | Sim — critico para validacao de complementares |
| Closing Line Value (CLV) | Sim (diferencial de trackers profissionais) | Sim | Fora de escopo — futebol virtual tem odds fixas |
| Deep-link / URL persistente | Sim | Sim | P3 — MVP usa modal sem URL routing |

---

## Implementation Approach for Dash

Duas opcoes identificadas para abrir a pagina de detalhe a partir do AG Grid:

### Option A: Modal — recomendado para MVP

Ao clicar em uma linha do AG Grid, um `dbc.Modal` se abre com o conteudo do detalhe do sinal.
O signal_id fica em `dcc.Store`. Zero mudancas no layout de multi-page.

```
AG Grid selectionChanged → dcc.Store(signal_id) → dbc.Modal opens → callback popula modal
```

**Pro:** Implementacao mais simples, sem tocar em routing. Consistente com o restante do app.
Zero refatoracao do callback master existente.
**Con:** URL nao muda — sem deep-link. Modal menor que uma pagina full.

### Option B: Dash Pages com /sinal/<signal_id>

Migrar `dashboard.py` para Dash Pages: `pages/home.py` + `pages/sinal.py`.

```
AG Grid row click → dcc.Location.href = f"/sinal/{signal_id}" → pages/sinal.py renderiza
```

**Pro:** URL persistente, back/forward do browser funciona, estrutura extensivel para futuras paginas.
**Con:** Refatoracao significativa de `dashboard.py`; callback master precisa ser dividido.

**Recomendacao para v1.3:** Option A (modal). Routing completo deferido para quando deep-link
for explicitamente necessario.

---

## Sources

- Bet-Analytix feature set: [bet-analytix.com](https://www.bet-analytix.com/) — MEDIUM confidence (marketing page)
- BettorEdge ROI breakdown: [bettoredge.com/post/top-bet-tracking-apps](https://www.bettoredge.com/post/top-bet-tracking-apps) — MEDIUM confidence
- Dash multi-page apps e URL routing: [dash.plotly.com/urls](https://dash.plotly.com/urls) — HIGH confidence (official docs)
- Dash AG Grid row selection: [dash.plotly.com/dash-ag-grid/row-selection](https://dash.plotly.com/dash-ag-grid/row-selection) — HIGH confidence (official docs)
- Dash Pages path_template: [dash.plotly.com/urls](https://dash.plotly.com/urls) — HIGH confidence (official docs)
- Codebase existente: `helpertips/queries.py`, `helpertips/dashboard.py` — HIGH confidence (fonte de verdade)

---
*Feature research for: Signal detail page — HelperTips Futebol Virtual*
*Researched: 2026-04-04*
