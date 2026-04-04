# Project Research Summary

**Project:** HelperTips — Futebol Virtual (Telegram Signal Capture + Betting Analytics Dashboard)
**Domain:** Telegram user-client listener + PostgreSQL storage + Plotly Dash analytics dashboard + Análise Individual de Sinais
**Researched:** 2026-04-02 (v1.0 stack + pitfalls) / 2026-04-03 (cloud deploy v1.1) / 2026-04-04 (milestone v1.3 — Dash Pages + signal detail)
**Confidence:** HIGH

## Executive Summary

HelperTips é uma ferramenta pessoal de três camadas: (1) um listener Telethon que captura sinais do grupo VIP no Telegram em tempo real, (2) PostgreSQL que armazena os sinais com upsert por `message_id` para lidar com o padrão edição-como-resultado do grupo, e (3) um dashboard Plotly Dash com callbacks reativos para análise de ROI, filtros dinâmicos e visualizações históricas. O milestone v1.3 adiciona uma quarta camada: página de detalhe individual por sinal (P&L completo de principal + complementares), implementada via Dash Pages — funcionalidade embutida no Dash 4.1.0 sem novas dependências. Todos os padrões são bem documentados em fontes oficiais.

A abordagem recomendada mantém separação estrita de processos: listener Telethon em processo dedicado, dashboard Dash em processo separado, ambos se comunicando exclusivamente via PostgreSQL. Em produção, Docker Compose em EC2 t4g.micro (~$7.82/mês) orquestra os serviços. A evolução do produto para v1.3 requer uma refatoração moderada de `dashboard.py` para `pages/home.py` (Dash Pages) — cirúrgica e com impacto zero na funcionalidade existente.

Os riscos principais são de integridade de dados na camada de captura (bloqueio asyncio, duplicatas, parser silencioso) e de segurança antes do deploy (secrets no histórico Git, session Telethon vazar). No lado da v1.3, o principal risco técnico é o gap de granularidade: `calculate_pl_por_entrada` retorna totais agrupados de complementares, mas a página de detalhe precisa de uma linha por complementar — requer nova função em `queries.py`. Todos os riscos são preveníveis com padrões definidos.

---

## Key Findings

### Recommended Stack

Stack Python-only sem JavaScript. Nenhuma nova dependência necessária para o milestone v1.3 — `use_pages=True` está embutido no Dash 4.1.0 desde a versão 2.5 (junho 2022). Ver [STACK.md](.planning/research/STACK.md) para rationale completo, estratégia de pinning e custos AWS detalhados.

**Core technologies:**
- **Telethon 1.42.0** — user-client MTProto — única opção para grupos privados sem ser admin; `events.MessageEdited` nativo cobre padrão resultado-por-edição
- **psycopg2-binary 2.9.x** — driver sync PostgreSQL — suficiente para baixo volume de escrita; `asyncio.to_thread()` obrigatório dentro de handlers Telethon
- **PostgreSQL 16** — storage relacional — upsert `ON CONFLICT`, JSONB para metadados, window functions para ROI
- **Plotly Dash 4.1.0** — dashboard interativo — pure-Python, callbacks reativos, `use_pages=True` para multi-page sem dep adicional
- **dash-bootstrap-components 2.0.x** — layout Bootstrap 5 — sem CSS manual, componentes `dbc.Modal`, `dbc.Card`, `dbc.Progress`
- **python-dotenv 1.x** — gestão de secrets — padrão de indústria
- **Python 3.12+** — runtime — suportado por todas as dependências; melhor performance
- **Docker Compose 2.x + EC2 t4g.micro** — deploy em produção — ~$7.82/mês total (listener + dashboard + PostgreSQL + Caddy)
- **Caddy 2** — reverse proxy com TLS automático — 3 linhas de config vs 50+ linhas Nginx + Certbot

**Versões a fixar:** `telethon~=1.42`, `dash>=4.1,<5`, `psycopg2-binary>=2.9`, `python-dotenv>=1.0`, `dash-bootstrap-components>=2.0`

**Decisão de deploy:** Docker Compose + Caddy (recomendado) vs systemd + nginx (alternativa equivalente). Escolher antes de planejar tasks de deploy.

### Expected Features

A pesquisa de features cobre o milestone v1.3 (página de detalhe individual por sinal) com referência ao produto completo. Ver [FEATURES.md](.planning/research/FEATURES.md) para árvore completa, grafo de dependências e análise competitiva.

**Must have (P1 — table stakes v1.3):**
- Header do sinal: liga, mercado, data/hora, tentativa, placar, badge GREEN/RED
- Card principal com financeiro: odd, stake (com progressão Gale quando tentativa > 1), retorno, lucro
- Lista de complementares com resultado individual por linha (GREEN/RED/N/A), odd, stake, lucro
- Totais consolidados: investido total, retorno total, lucro líquido
- Botão/link de volta ao histórico

**Should have (P2 — diferenciadores v1.3):**
- Badge Gale com contexto acumulado ("T3: atual R$400 / acumulado R$700")
- Decomposição visual principal vs complementares (stacked bar)
- Destaque de complementar com odd alta que converteu (odd_ref > 10.0 + GREEN)

**Defer (P3 / v2+):**
- Deep-link URL por signal_id (`/sinal/123` via path params em vez de query params) — modal é suficiente para MVP
- Navegação sequencial entre sinais (anterior/próximo)
- Timestamp de latência (horario_sinal vs received_at) — dado técnico de auditoria

**Anti-features a não implementar:**
- Edição inline de resultado/placar — abre inconsistência com fonte de verdade (Telegram)
- Equity curve "sem este sinal" — recálculo costoso para benefício cosmético
- Copiar bet slip para clipboard — complexidade JS inject sem uso primário justificado

**Abordagem de implementação recomendada para v1.3:**
Option A (modal `dbc.Modal` + `dcc.Store`) para MVP — zero refatoração de routing, signal_id passado via AG Grid `cellClicked`. Option B (Dash Pages com `/sinal?id=<n>`) como evolução se deep-link for requerido.

### Architecture Approach

A arquitetura atual (pré-v1.3) é um único arquivo `dashboard.py` com ~970 LOC e um callback master com 10 inputs e 13 outputs. O milestone v1.3 requer migração para Dash Pages: `dashboard.py` vira shell com `dcc.Location(refresh="callback-nav")` + `dash.page_container`; o conteúdo atual migra para `pages/home.py`; a nova página de detalhe fica em `pages/sinal.py`. Dois métodos novos em `queries.py`. Ver [ARCHITECTURE.md](.planning/research/ARCHITECTURE.md) para código concreto, build order por etapas e anti-patterns documentados.

**Major components (estado alvo v1.3):**
1. **`listener.py`** — processo Telethon, captura `NewMessage` + `MessageEdited`, escreve via `asyncio.to_thread()`, upsert único como caminho de escrita
2. **`dashboard.py` (shell)** — inicializa Dash com `use_pages=True`, layout com `dcc.Location` + `dash.page_container`, expõe `server` para gunicorn
3. **`pages/home.py`** — todo layout e callbacks existentes (migração do `dashboard.py` atual) + navigation callback (`cellClicked → url-nav.href`)
4. **`pages/sinal.py`** — `def layout(id=None)` + callback `render_signal_detail` que chama `get_signal_by_id` e `calculate_pl_por_entrada`
5. **`queries.py`** — toda lógica SQL + cálculos P&L; recebe `get_signal_by_id` e `calculate_pl_detalhado_por_sinal`
6. **`db.py`** — `get_connection()` sem mudanças

**Padrões arquiteturais confirmados:**
- `dcc.Location(refresh="callback-nav")` no shell — navegação programática sem full page reload (desde Dash 2.9.2)
- `def layout(id=None)` em `sinal.py` — recebe query params da URL como kwargs (padrão oficial)
- `dcc.Store` como state scoped à página — layout function escreve id no Store, callback lê e renderiza
- Navigation callback em `pages/home.py`, não no shell — evita `ID not found in layout` errors

**Gap de granularidade identificado:** `calculate_pl_por_entrada` retorna totais agrupados de complementares (`investido_comp`, `lucro_comp`), não uma linha por complementar. A página de detalhe precisa da lista individual. Solução: nova função `calculate_pl_detalhado_por_sinal` em `queries.py` que reutiliza o loop interno e retorna `list[dict]` por complementar.

**Build order para v1.3 (6 etapas sequenciais):**
1. Adicionar `id` ao `rowData` do AG Grid + coluna hidden
2. Adicionar `get_signal_by_id(conn, id)` em `queries.py`
3. Refatorar `dashboard.py` → `pages/` (etapa bloqueante para as demais)
4. Adicionar navigation callback em `pages/home.py`
5. Criar `pages/sinal.py` com layout + callback de detalhe
6. Adicionar `calculate_pl_detalhado_por_sinal` em `queries.py` (opcional mas recomendado)

### Critical Pitfalls

Research identificou 16 pitfalls total (6 críticos app + 5 moderados app + 5 cloud) mais pitfalls específicos de v1.3. Ver [PITFALLS.md](.planning/research/PITFALLS.md) para padrões de prevenção e detecção completos.

**Top 5 — devem ser endereçados antes de qualquer outra coisa:**

1. **psycopg2 bloqueia o event loop do Telethon** — descarte silencioso de mensagens em burst; `asyncio.to_thread()` obrigatório em todo handler; Fase 1 (listener foundation)

2. **Arquivo `.session` ou `.env` no histórico Git** — credenciais Telegram sem expiração; verificar com `git ls-files | grep -E '\.(env|session)$'` e `git log --all --full-diff -p -- .env` antes de qualquer `git push`; Pré-deploy

3. **Duplicatas por ausência de upsert em edit events** — INSERT em vez de `ON CONFLICT DO UPDATE` corrompe ROI e win rate; upsert como único caminho de escrita desde o design do schema; Fase 1

4. **Parser regex falha silenciosamente** — dados corrompidos acumulam sem alerta; coluna `raw_text TEXT` no schema (permite reprocessamento), log de parse failures, contador no dashboard; Fase 1

5. **Dashboard exposto sem autenticação + debug=True** — `debug=True` com porta aberta = debugger Flask acessível na internet (RCE); Security Group restrito + `debug=False` via env var; antes de qualquer deploy

**Pitfall específico de v1.3 — gunicorn + `pages/` folder resolution:**
Gunicorn em Linux resolve `pages/` a partir de `__main__`, que pode diferir do diretório real. Resultado: `A folder called pages does not exist` em produção. Mitigação: `dash.Dash(__name__, ...)` já é o padrão do projeto — o `__name__` como primeiro argumento é exatamente a correção necessária. A pasta `pages/` deve ficar dentro de `helpertips/` (ao lado de `dashboard.py`), não na raiz.

---

## Implications for Roadmap

Baseado no grafo de dependências da ARCHITECTURE.md, na árvore de features da FEATURES.md e nos avisos por fase da PITFALLS.md, a estrutura de fases recomendada é:

### Phase 1: Fundação — Listener Pipeline + Data Model

**Rationale:** Tudo downstream depende de sinais chegando corretamente ao PostgreSQL. Os pitfalls mais críticos da aplicação (event loop blocking, upsert, parser silencioso) ocorrem aqui. Dashboard analytics são inúteis se a camada de captura tem problemas de integridade. Nenhum trabalho de dashboard deve começar antes desta fase ser validada com dados Telegram reais.

**Delivers:** Listener Telethon rodando localmente, schema PostgreSQL com upsert por `(chat_id, message_id)`, parser com coluna `raw_text`, log de parse failures, testes unitários do parser, sumário de terminal no startup.

**Addresses:** Captura em tempo real, deduplicação, result tracking, persistência (table stakes de aplicação do FEATURES.md).

**Avoids:** Pitfall 1 (asyncio.to_thread), Pitfall 2 (session collision), Pitfall 3 (messages offline), Pitfall 4 (session no git), Pitfall 5 (parse failures), Pitfall 7 (duplicatas por edit events).

### Phase 2: Core Dashboard — Stats Agregadas + Filtros + AG Grid

**Rationale:** Com dados confiáveis na base, o dashboard entrega o valor primário ao usuário. MVP read-only com filtros dinâmicos — sem analytics complexos ainda. AG Grid com coluna `id` hidden desde o início prepara terreno para v1.3.

**Delivers:** Dashboard Plotly Dash com win rate, ROI simulado, filtros liga/entrada/período carregados dinamicamente de `SELECT DISTINCT`, tabela AG Grid com histórico (incluindo coluna `id` hidden).

**Uses:** Plotly Dash 4.1.0, dash-bootstrap-components 2.0.x, dash-ag-grid; processo separado do listener.

**Avoids:** Pitfall 6 (sample size sem aviso — anotação de N em cada stat card), Pitfall 8 (filtros hardcoded — SELECT DISTINCT), Pitfall 10 (connection pool ao adicionar dashboard ao listener).

### Phase 3: Analytics Depth — Breakdowns Dimensionais + Equity Curve

**Rationale:** Após MVP validar o pipeline com dados reais (100+ sinais), adicionar analytics diferenciadores. Features requerem acúmulo de dados para ser estatisticamente significativas.

**Delivers:** Win rate por horário (heatmap), dia da semana, período (1T/2T/FT). Equity curve. Filtro cruzado multi-dimensional.

**Addresses:** Todos os diferenciadores v1.1 do FEATURES.md.

**Avoids:** Pitfall 6 — avisos de sample size em cada view de breakdown.

### Phase 4: Segurança + Publicação GitHub

**Rationale:** Auditoria de segurança é pré-requisito estrito para publicação. Deve ocorrer antes de criar qualquer recurso AWS para evitar vazar secrets em repositório público. gunicorn adicionado aqui pois é requisito do deploy na Fase 5.

**Delivers:** Histórico Git auditado (sem secrets), `.gitignore` verificado, `.env.example` documentado, README.md, repositório público no GitHub, gunicorn no requirements.txt.

**Avoids:** Pitfall 11 (secrets no histórico Git), Pitfall 13 (dashboard exposto + debug=True).

### Phase 5: Deploy AWS — Infraestrutura + Processos

**Rationale:** Listener e dashboard devem rodar 24/7 sem depender do computador local. A autenticação interativa do Telethon é um constraint crítico — deve ocorrer via SSH antes de configurar Docker Compose (requer TTY para código SMS). Billing alert deve ser o primeiro passo.

**Delivers:** EC2 t4g.micro provisionada, Elastic IP, Security Group configurado, billing alert ativo, PostgreSQL no EC2, listener + dashboard rodando via Docker Compose, Caddy com HTTPS, secrets no SSM Parameter Store, `StringSession` eliminando arquivo `.session`.

**Uses:** Docker Compose 2.x, Caddy 2, SSM Parameter Store (grátis), GitHub Actions (CI + SSH deploy).

**Avoids:** Pitfall 12 (sessão duplicada local/EC2), Pitfall 14 (surpresas de custo — billing alert primeiro), Pitfall 15 (credenciais em logs), Pitfall 16 (listener sem restart policy).

### Phase 6: Análise Individual de Sinais (Dash Pages + Página de Detalhe)

**Rationale:** Com histórico acumulado e deploy estável, o próximo salto de valor é drill-down por sinal individual — ver P&L completo (principal + cada complementar) ao clicar no AG Grid. Fase 5 estável é pré-requisito para não refatorar um target em movimento.

**Delivers:** Migração para Dash Pages (`use_pages=True`), `pages/home.py` com conteúdo existente, `pages/sinal.py` com detalhe completo, `get_signal_by_id` e `calculate_pl_detalhado_por_sinal` em `queries.py`.

**Features implementadas:** Todos os P1 (header, card principal, lista complementares, totais, botão voltar). P2 (badge Gale, decomposição visual) se couber no escopo.

**Avoids:** Anti-pattern navigation callback no shell, anti-pattern fetch de 500 linhas para um sinal, anti-pattern P&L logic duplicada fora de `queries.py`, pitfall gunicorn + pages/ folder resolution.

### Phase Ordering Rationale

- Fase 1 antes de Fase 2: dados corrompidos não se corrigem com polimento de UI
- Fase 2 antes de Fase 6: a página de detalhe pressupõe o AG Grid existente com coluna `id` e os cálculos de P&L consolidados
- Fase 4 antes de Fase 5: repositório público com secrets é dano imediato às credenciais Telegram
- Fase 5 antes de Fase 6: refatorar Dash Pages em codebase em movimento (deploy instável) é risco desnecessário
- Fases 3 e 4 podem ser paralelas entre si (analytics depth e auditoria Git são ortogonais)

### Research Flags

**Fases que provavelmente precisam de pesquisa adicional durante o planejamento:**
- **Fase 1 — Parser de mensagens:** O formato exato das mensagens do grupo `{VIP} ExtremeTips` não foi verificado com mensagens reais. A pesquisa baseou-se em padrões gerais. Capturar 10–20 mensagens reais antes de finalizar o schema e o parser. Risco de mudança de formato em produção é alto — `raw_text` é a rede de segurança.
- **Fase 6 — `calculate_pl_detalhado_por_sinal`:** O gap de granularidade (P&L agrupado vs. por complementar) precisa de análise do código atual de `calculate_pl_por_entrada` para decidir entre nova função vs. inline no callback. Decisão durante planejamento da Fase 6.

**Fases com padrões estabelecidos (dispensam pesquisa adicional):**
- **Fase 2 — Dashboard Dash:** Callbacks reativos, filtros dinâmicos e connection pooling são amplamente documentados; sem unknowns
- **Fase 3 — Analytics queries:** GROUP BY e window functions SQL são padrão; sem unknowns de domínio
- **Fase 4 — Auditoria Git:** Processo determinístico com comandos específicos documentados em PITFALLS.md
- **Fase 5 — Docker Compose + Caddy:** Configuração padrão com custos verificados; todas as configs documentadas em STACK.md
- **Fase 6 — Dash Pages:** `use_pages=True`, `def layout(id=None)`, `dcc.Location(refresh="callback-nav")` todos confirmados em docs oficiais com exemplos de código concretos

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Todas as escolhas verificadas em docs oficiais e PyPI. Telethon 1.42.0, Dash 4.1.0 confirmados como releases estáveis atuais. Custos AWS verificados em múltiplas fontes. `use_pages=True` confirmado disponível no Dash 4.1.0. |
| Features | HIGH (P1) / MEDIUM (P2) | P1 validados contra trackers de apostas reais (Bet-Analytix, BettorEdge). P2 são diferenciadores específicos do sistema Gale + complementares — alta confiança por conhecimento de domínio, MEDIUM por ser proprietário do produto. |
| Architecture | HIGH | Dash Pages documentado oficialmente. `cellClicked`, `dcc.Location(refresh="callback-nav")`, `def layout(id=None)` confirmados em docs Plotly e community. Análise direta do codebase (`dashboard.py` ~970 LOC, `queries.py`) HIGH confidence. Build order de 6 etapas verificado por análise de dependências. |
| Pitfalls | HIGH (críticos + cloud) | Pitfalls 1–5 têm fontes oficiais (Telethon docs, GitHub issues numerados). Cloud pitfalls têm múltiplas fontes secundárias concordando. Pitfall gunicorn + pages/ confirmado em Plotly Community forum com solução reproduzida. |

**Overall confidence: HIGH**

### Gaps to Address

- **Formato exato das mensagens do grupo:** O parser regex deve ser validado contra mensagens reais capturadas antes de finalizar o schema. Reservar iteração de refinamento de parser após primeiros dados reais.
- **Tipo do grupo (megagroup vs channel):** Comportamento do backfill e do `catch_up` diferem. Confirmar antes de implementar o utilitário de gap-recovery na Fase 1.
- **Escolha Docker Compose vs systemd:** STACK.md favorece Docker + Caddy; ARCHITECTURE.md (versão anterior) mencionava systemd + nginx como equivalente. Escolher Docker Compose + Caddy como padrão único para eliminar ambiguidade nas tasks da Fase 5.
- **`calculate_pl_detalhado_por_sinal`:** Gap de granularidade identificado mas implementação não resolvida. Decisão na Fase 6: nova função isolada em `queries.py` (preferido — single source of truth) vs. inline no callback `sinal.py` (aceitável para MVP se a função existente puder ser adaptada).
- **Autenticação do dashboard em produção:** `dash-auth` com HTTP Basic Auth é a recomendação, mas compatibilidade com Dash 4.1.0 + Caddy não foi validada explicitamente. Verificar durante Fase 5.

---

## Sources

### Primary (HIGH confidence)

- [Dash Multi-Page Apps — documentação oficial Plotly](https://dash.plotly.com/urls) — `use_pages=True`, `def layout(id=None)`, query params, path templates
- [Dash AG Grid — cell selection](https://dash.plotly.com/dash-ag-grid/cell-selection) — `cellClicked` properties (rowData, colId, value)
- [Dash 4.1.0 installation](https://dash.plotly.com/installation) — versão atual, `use_pages` disponível desde Dash 2.5
- [Telethon docs 1.42.0](https://docs.telethon.dev/) — versão 1.42.0, `events.MessageEdited`, `StringSession`, `FloodWaitError`
- [Telethon PyPI](https://pypi.org/project/Telethon/) — confirmação de versão 1.42.0
- [psycopg.org/docs/install.html](https://www.psycopg.org/docs/install.html) — psycopg2-binary vs compiled
- [dash-bootstrap-components official](https://www.dash-bootstrap-components.com/) — versão 2.0.x, Bootstrap 5
- Telethon GitHub issues #1488 (AuthKeyDuplicated), #3041 #4535 (catch_up bugs) — pitfalls confirmados
- Codebase existente: `helpertips/dashboard.py` (~970 LOC), `helpertips/queries.py` — análise direta

### Secondary (MEDIUM confidence)

- [Plotly Community — dcc.Location refresh="callback-nav"](https://community.plotly.com/t/sharing-examples-of-navigation-without-refreshing-the-page-when-url-is-updated-in-a-callback-in-dash-2-9-2/74260) — navegação programática sem full reload
- [Plotly Community — gunicorn + pages/ folder fix](https://community.plotly.com/t/multi-page-app-pages-folder-undiscoverable-by-gunicorn-on-linux/67788) — pitfall crítico de deploy v1.3
- [instances.vantage.sh — EC2 t4g.micro](https://instances.vantage.sh/aws/ec2/t4g.micro) — pricing ~$6.13/mês
- [economize.cloud — RDS db.t4g.micro](https://www.economize.cloud/resources/aws/pricing/rds/db.t4g.micro/) — pricing RDS ~$21.90/mês vs EC2 self-hosted
- [ranthebuilder.cloud — SSM vs Secrets Manager](https://ranthebuilder.cloud/blog/secrets-manager-vs-parameter-store-which-one-should-you-really-use/) — SSM standard grátis
- [selfhostwise.com — Caddy vs Nginx 2026](https://selfhostwise.com/posts/traefik-vs-caddy-vs-nginx-proxy-manager-which-reverse-proxy-should-you-choose-in-2026/) — TLS automático
- [squadbase.dev — Streamlit vs Dash 2025](https://www.squadbase.dev/en/blog/streamlit-vs-dash-in-2025-comparing-data-app-frameworks) — callback model comparison
- [tigerdata.com — psycopg2 vs psycopg3 benchmark](https://www.tigerdata.com/blog/psycopg2-vs-psycopg3-performance-benchmark) — async overhead analysis
- [Bet-Analytix](https://www.bet-analytix.com/), [BettorEdge](https://www.bettoredge.com/post/top-bet-tracking-apps) — competitive feature analysis para signal detail
- [GitHub Docs — removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [AnnMarieW dash-multi-page-app-demos](https://github.com/AnnMarieW/dash-multi-page-app-demos) — exemplos community Dash Pages

### Tertiary (LOW confidence)

- Nenhuma fonte de baixa confiança foi usada como base para recomendações críticas.

---
*Research completed: 2026-04-04*
*Ready for roadmap: yes*
