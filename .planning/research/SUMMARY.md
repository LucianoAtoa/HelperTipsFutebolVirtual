# Project Research Summary

**Project:** HelperTips — Futebol Virtual
**Domain:** Telegram signal capture + betting analytics dashboard + cloud deployment (AWS)
**Researched:** 2026-04-02 (aplicação v1.0) / 2026-04-03 (cloud deploy v1.1)
**Confidence:** HIGH

## Executive Summary

HelperTips é uma ferramenta pessoal de captura e análise de sinais de apostas em futebol virtual. O padrão estabelecido para esse tipo de sistema é: (1) um processo daemon long-running que conecta ao Telegram via MTProto e persiste dados em PostgreSQL, e (2) um dashboard web Python-only que transforma esses dados em estatísticas acionáveis. A pesquisa confirma que a stack original (Telethon + psycopg2 + Plotly Dash) é sólida, com um ajuste de versão — Telethon 1.42 (não 1.37) e Dash 4.1 como releases atuais estáveis. Para deploy em produção, a arquitetura recomendada é dois processos systemd separados em uma única EC2 t3.micro, com PostgreSQL self-hosted na mesma instância, fronteados por nginx como reverse proxy. Custo total: ~$9-12/mês vs ~$28/mês se usasse RDS separado.

Os dois riscos mais graves são: (1) a sincronização incorreta entre o loop asyncio do Telethon e as chamadas bloqueantes do psycopg2, que silenciosamente descarta sinais sob carga — resolvida com `asyncio.to_thread()`; e (2) vazar o arquivo `.session` do Telethon ou credenciais no histórico Git antes de tornar o repositório público — credenciais Telegram comprometem a conta inteira e não expiram automaticamente. Ambos são evitáveis com padrões simples definidos desde o início.

A ordem de construção é ditada por dependências concretas: a fundação de dados (listener + storage) deve ser validada antes de construir analytics; a auditoria de segurança e publicação no GitHub deve preceder qualquer deploy na AWS; e a autenticação interativa do Telethon deve ocorrer antes de configurar o serviço systemd, pois requer TTY e código SMS. Não há ambiguidade nas dependências de fase.

---

## Key Findings

### Recommended Stack

A stack é Python-only sem JavaScript, mantendo escopo mínimo para uma ferramenta pessoal. Telethon 1.42.0 é a única biblioteca que conecta como user-client (não bot) em grupos privados. psycopg2-binary (sync) é suficiente para a frequência de escrita — poucos registros por hora — desde que as chamadas sejam wrapped em `asyncio.to_thread()`. Plotly Dash 4.1.0 entrega dashboards interativos com callbacks reativas sem exigir JavaScript. Para produção, dois processos Python separados são mandatórios: Telethon bloqueia o asyncio loop; Dash bloqueia o processo via Flask. Não é possível rodar ambos no mesmo processo. Ver [STACK.md](.planning/research/STACK.md) para rationale completo e estratégia de pinning de versões.

**Core technologies:**
- **Telethon 1.42.0**: user-client MTProto — única opção para grupos privados sem ser admin; `events.MessageEdited` nativo cobre o padrão de resultado-por-edição
- **psycopg2-binary 2.9.x**: driver sync PostgreSQL — zero build-tooling; sync é aceitável na frequência de escrita atual; `asyncio.to_thread()` é obrigatório
- **PostgreSQL 16**: storage relacional — JSONB para metadados, upsert `ON CONFLICT`, window functions para ROI e streak analytics
- **Plotly Dash 4.1.0 + dash-bootstrap-components 2.0**: dashboard Python-only — callbacks reativas para filtros cruzados; Bootstrap 5 responsive
- **python-dotenv 1.x**: gestão de secrets — padrão de indústria para ferramentas pessoais
- **Python 3.12+**: runtime — suportado por todas as dependências; melhor performance e mensagens de erro da versão atual

**Stack de deploy (produção):**
- **Docker Compose 2.x OU systemd**: orquestração de processos — ambas as abordagens são equivalentes; escolher uma antes de planejar deploy
- **Caddy 2 (Docker) ou nginx (systemd)**: reverse proxy com TLS automático
- **EC2 t3.micro**: compute ($7.59/mês); t3.small ($15.18) como fallback se RAM for limitante
- **EBS gp3 20GB**: storage persistente ($1.60/mês); `.session` e dados PostgreSQL vivem aqui

### Expected Features

A pesquisa de features cobre duas camadas: features da aplicação (v1.0) e features de deploy/segurança (v1.1). Ver [FEATURES.md](.planning/research/FEATURES.md) para árvore completa e grafo de dependências.

**Must have (table stakes) — aplicação:**
- Captura em tempo real (Telethon NewMessage + MessageEdited)
- Deduplicação via upsert — sem isso, stats são inválidas
- Rastreamento de resultado (GREEN/RED) via edit events
- Win rate + total sinais — primeira coisa que qualquer apostador verifica
- Simulação de ROI com stake fixo — pergunta base de lucratividade
- Filtro por liga e por entrada
- Histórico de sinais paginado e filtrável
- Sinais pendentes (resultado NULL, excluídos do denominador de win rate)
- Sumário de terminal no startup — valida pipeline antes do dashboard

**Must have (table stakes) — deploy/segurança:**
- `debug=False` em produção — `debug=True` com porta aberta = execução remota de código
- gunicorn como WSGI server — Werkzeug não é production-safe
- systemd units para listener e dashboard — processos morrem sem gerenciamento
- Security Group EC2 restrito — porta 8050 e SSH limitados ao IP pessoal
- Auditoria de histórico Git — secrets em commits antigos ficam públicos para sempre
- EnvironmentFile com `chmod 600` — secrets nunca no repositório

**Should have (diferenciadores):**
- Win rate por horário (heatmap), dia da semana, e período (1T/2T/FT)
- Equity curve (bankroll acumulado ao longo do tempo)
- Filtro cruzado multi-dimensional (liga + entrada + período)
- nginx + HTTP Basic Auth — camada adicional de proteção
- GitHub Actions CI — pytest no push
- Dependabot alerts

**Defer (v2+):**
- Streak tracking — requer 300+ sinais para ser significativo
- Análise de Gale — requer mudanças de schema; validar demanda primeiro
- HTTPS/Certbot — só necessário se dashboard migrar para domínio público
- AWS RDS — PostgreSQL self-hosted é $15-25/mês mais barato sem perda funcional

### Architecture Approach

A arquitetura é single-instance deliberada: dois processos Python (listener asyncio + dashboard gunicorn) e PostgreSQL na mesma EC2, acessando banco via `localhost:5432`. Não há rede interna entre serviços além do PostgreSQL. O reverse proxy (nginx ou Caddy) é o único ponto de entrada público. Cada processo tem seu próprio systemd unit com restart independente — crash do listener não reinicia o dashboard. Todo estado persistente (`.session`, dados PostgreSQL, `.env`) vive no volume EBS root. Ver [ARCHITECTURE.md](.planning/research/ARCHITECTURE.md) para diagrams, SQL schema, e build order detalhado.

**Major components:**
1. **Telegram Listener** (`listener.py`) — daemon asyncio, Telethon 1.42, escreve via `asyncio.to_thread()`, `RestartSec=60` para evitar FloodWait loop
2. **Parser** — função pura stateless, regex extraction, zero imports de DB ou Telethon, testável isoladamente
3. **Store** — repository layer, upsert único, connection pool, wrapping asyncio
4. **Analytics Dashboard** (`dashboard.py`) — Plotly Dash servido por gunicorn (2 workers), leitura apenas, porta 8050 localhost-only
5. **PostgreSQL 16** — single source of truth, binds em `127.0.0.1`, acessado pelos dois processos
6. **Reverse Proxy** (nginx ou Caddy) — termina TLS, proxy para gunicorn, Basic Auth opcional
7. **EBS root volume** — single source of truth para `.session`, dados PostgreSQL, `.env`

### Critical Pitfalls

Research identificou 16 pitfalls total (6 críticos, 5 moderados, 5 menores). Ver [PITFALLS.md](.planning/research/PITFALLS.md) para padrões de prevenção e detecção completos.

**Top 5 — devem ser endereçados antes de qualquer outra coisa:**

1. **psycopg2 bloqueia o event loop do Telethon** — descarte silencioso de mensagens sob burst; `asyncio.to_thread()` obrigatório desde o primeiro handler; Fase 1

2. **Arquivo `.session` ou `.env` no histórico Git** — credenciais Telegram sem expiração; `git log --all --full-diff -p -- .env *.session` antes de qualquer push público; usar BFG se já ocorreu; Pré-Fase de deploy

3. **Registros duplicados de edit events** — INSERT em vez de upsert corrompe ROI; `ON CONFLICT (message_id) DO UPDATE` é o único caminho de escrita; design da Fase 1

4. **Parser falha silenciosamente** — dados corrompidos acumulam sem alerta; armazenar `raw_text` em cada linha; logar mensagens que não matcham; Fase 1

5. **Dashboard exposto sem autenticação + debug=True** — `debug=True` com porta aberta = debugger Flask acessível na internet (RCE); Security Group restrito + `debug=False` via env var; antes de qualquer deploy

---

## Implications for Roadmap

Baseado no grafo de dependências do ARCHITECTURE.md, na árvore de features do FEATURES.md, e nos avisos por fase do PITFALLS.md, a estrutura de fases recomendada é:

### Phase 1: Fundação — Listener Pipeline + Data Model

**Rationale:** Tudo downstream depende de sinais chegando corretamente ao PostgreSQL. Dashboard analytics são inúteis se a camada de captura tem problemas de integridade. Todos os pitfalls críticos da aplicação são concerns da Fase 1. Nenhum trabalho de dashboard deve começar antes desta fase ser validada com dados Telegram reais.

**Delivers:** Listener rodando localmente capturando sinais e result edits do grupo VIP, armazenados via upsert, sumário de terminal no startup, survivable a restarts sem perda de dados.

**Addresses:** Captura de sinais, deduplicação, result tracking, persistência (todos os table stakes de aplicação do FEATURES.md).

**Avoids:** Pitfall 1 (asyncio blocking), Pitfall 2 (session collision), Pitfall 3 (messages offline), Pitfall 4 (session no git), Pitfall 5 (parse failures), Pitfall 7 (duplicatas por edit events).

**Decisões críticas de implementação:**
- `.gitignore` com `*.session` e `.env` antes do primeiro commit
- Parser como módulo separado com unit tests, zero dependências externas
- `asyncio.to_thread()` em toda chamada psycopg2 dentro de handlers
- Upsert como único caminho de escrita
- Coluna `raw_text` em cada linha

### Phase 2: Core Dashboard — Stats Agregadas + Filtros

**Rationale:** Com dados confiáveis na base, o dashboard entrega o valor primário ao usuário. O MVP dashboard é SQL read-only com filtros UI — sem analytics complexos ainda.

**Delivers:** Dashboard Plotly Dash com win rate, total de sinais, contagem de pendentes, simulação ROI, filtros de liga e entrada. Lista de histórico com paginação.

**Addresses:** Stats agregadas, filtros, ROI, histórico (todos os table stakes de dashboard do FEATURES.md).

**Uses:** Plotly Dash 4.1.0 + dash-bootstrap-components 2.0; queries PostgreSQL read-only; processo separado do listener.

**Avoids:** Pitfall 6 (sample size sem aviso) — anotação de contagem em cada stat card desde o início; Pitfall 8 (filtros hardcoded) — todas as opções carregadas dinamicamente de `SELECT DISTINCT`.

### Phase 3: Analytics Depth — Breakdowns Dimensionais + Equity Curve

**Rationale:** Após o MVP validar o pipeline com dados reais, adicionar os analytics diferenciadores que vão além de trackers genéricos. Essas features requerem dados acumulados suficientes (100+ sinais) para ser significativas.

**Delivers:** Win rate por horário (heatmap), dia da semana, período. Equity curve (bankroll acumulado). Filtro cruzado multi-dimensional. Gráfico de volume de sinais.

**Addresses:** Todos os diferenciadores v1.1 do FEATURES.md.

**Avoids:** Pitfall 6 — avisos de sample size em cada view de breakdown.

### Phase 4: Segurança + Publicação GitHub

**Rationale:** Auditoria de segurança é pré-requisito estrito para publicação. Deve ocorrer antes de criar qualquer recurso AWS para evitar vazamento em repositório público.

**Delivers:** Repositório limpo de secrets (histórico auditado), `.gitignore` verificado, `.env.example` documentado, README.md, repositório público no GitHub, gunicorn adicionado ao requirements.txt.

**Addresses:** Todos os table stakes de segurança do FEATURES.md v1.1.

**Avoids:** Pitfall 11 (secrets no histórico Git), Pitfall 13 (dashboard exposto + debug=True).

### Phase 5: Deploy AWS — Infraestrutura + Listener

**Rationale:** Infraestrutura deve estar provisionada antes do deploy dos processos. A autenticação interativa do Telethon é um constraint crítico — deve ocorrer interativamente via SSH antes de converter o listener em serviço systemd.

**Delivers:** EC2 t3.micro provisionada (ou t3.small), Elastic IP, Security Group configurado, billing alert ativo, PostgreSQL no EC2, EnvironmentFile `chmod 600`, listener rodando via systemd com sessão autenticada.

**Uses:** Docker Compose OU systemd (escolher antes de planejar); PostgreSQL 16 self-hosted; Caddy ou nginx.

**Avoids:** Pitfall 12 (sessão duplicada local+EC2), Pitfall 14 (surpresas de custo), Pitfall 15 (credenciais em logs), Pitfall 16 (listener sem systemd).

### Phase 6: Deploy AWS — Dashboard + Reverse Proxy

**Rationale:** Dashboard só pode ser deployado após infraestrutura base estar estável (PostgreSQL acessível, listener funcional na EC2).

**Delivers:** gunicorn servindo o dashboard, nginx ou Caddy como reverse proxy, `debug=False` via env var, porta 8050 acessível apenas via proxy, opcionalmente HTTP Basic Auth.

**Implements:** Componente Reverse Proxy da arquitetura.

**Avoids:** Pitfall 13 (debug=True em produção), anti-pattern de rodar Dash dev server na porta 80.

### Phase Ordering Rationale

- Schema e Parser antes de Store e Listener: unit tests validam sem banco ou Telegram rodando
- Listener validado antes do dashboard: dados corrompidos não se corrigem com polimento de UI
- Fase 4 (segurança + GitHub) antes das Fases 5 e 6 (deploy AWS): repositório público com secrets é dano imediato às credenciais Telegram
- Autenticação interativa do Telethon é hard constraint de ordering dentro da Fase 5: requer TTY, não pode ser automatizado
- Fase 6 (dashboard) depende de gunicorn adicionado na Fase 4 e PostgreSQL acessível da Fase 5

### Research Flags

Fases que provavelmente precisam de pesquisa adicional durante o planejamento:
- **Fase 1 — Parser:** O formato exato das mensagens do grupo `{VIP} ExtremeTips` não foi verificado. A pesquisa baseou-se em padrões gerais de grupos de futebol virtual. Capturar 10–20 mensagens reais antes de finalizar o parser. Risco de mudança de formato em produção é alto.
- **Fase 5 — Docker vs systemd:** STACK.md favorece Docker+Caddy; ARCHITECTURE.md favorece systemd+nginx. Ambos chegam ao mesmo resultado. O roadmapper deve escolher uma única abordagem antes de detalhar as tasks da Fase 5.

Fases com padrões estabelecidos (dispensam pesquisa adicional):
- **Fase 2 — Dashboard:** Padrões de callback Dash, filtros dinâmicos e connection pooling são amplamente documentados
- **Fase 3 — Analytics queries:** GROUP BY e window functions SQL são padrão; sem unknowns de domínio
- **Fase 4 — Auditoria Git:** Processo determinístico com comandos específicos já documentados em PITFALLS.md
- **Fase 6 — nginx/Caddy + gunicorn:** Configuração padrão amplamente documentada

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Todas as escolhas verificadas contra docs oficiais e PyPI. Telethon 1.42.0 e Dash 4.1.0 confirmados como releases estáveis atuais. Stack de deploy (EC2, Docker, Caddy) com custos verificados em múltiplas fontes. |
| Features | HIGH (table stakes) / MEDIUM (diferenciadores) | Table stakes validados contra 5 plataformas comparáveis. Diferenciadores de analytics (horário, gale) são específicos do domínio futebol virtual — fonte primária brasileira (greenvirtual.com.br). |
| Architecture | HIGH | Padrões de EC2 + systemd + PostgreSQL self-hosted amplamente documentados. Build order validado por análise de dependências de componentes. Custos verificados em fontes múltiplas (oficial AWS + comparativos). |
| Pitfalls | HIGH (app + deploy) | Pitfalls da aplicação têm fontes oficiais (Telethon docs, GitHub issues com números confirmados). Pitfalls de cloud têm múltiplas fontes secundárias concordando. Pitfall de secrets no Git tem estatísticas de 2025 do Snyk. |

**Overall confidence:** HIGH

### Gaps to Address

- **Formato exato das mensagens do grupo:** O parser regex deve ser escrito contra mensagens reais capturadas. Nenhuma fonte externa verificou o formato exato. Reservar uma iteração de parser após os primeiros dados reais serem capturados.
- **Tipo do grupo (megagroup vs channel):** Comportamento do backfill difere. Confirmar se o grupo VIP é megagroup ou broadcast channel antes de implementar o utilitário de gap-recovery.
- **Escolha Docker Compose vs systemd:** Ambas as abordagens estão documentadas com recomendações levemente divergentes entre STACK.md e ARCHITECTURE.md. Usuário ou roadmapper deve escolher antes de planejar as tasks da Fase 5.
- **Dimensionamento EC2:** ARCHITECTURE.md recomenda t3.micro (1 GB RAM); FEATURES.md alerta que t3.small pode ser necessário. Com baseline de ~350 MB (Telethon + Dash + PostgreSQL), t3.micro tem ~650 MB de headroom — deve ser suficiente, mas monitorar no primeiro dia.
- **Odds disponíveis nas mensagens:** A pesquisa confirmou que mensagens de futebol virtual tipicamente não incluem odds. Se aparecerem no grupo real, a coluna `odds` pode ser adicionada sem mudança de schema.

---

## Sources

### Primary (HIGH confidence)
- Telethon official docs 1.42.0 — events, sessions, errors, FAQ: https://docs.telethon.dev/
- Telethon PyPI (confirmação de versão): https://pypi.org/project/Telethon/
- Plotly Dash 4.1.0 official docs: https://dash.plotly.com/installation
- Dash DevTools (riscos de debug=True em produção): https://dash.plotly.com/devtools
- dash-bootstrap-components official: https://www.dash-bootstrap-components.com/
- psycopg2 official (binary vs compiled): https://www.psycopg.org/docs/install.html
- AWS EC2 docs (EBS, Security Groups): https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/
- AWS Blog — IPv4 charge (fevereiro 2024): https://aws.amazon.com/blogs/aws/new-aws-public-ipv4-address-charge-public-ip-insights/
- GitHub Docs — removing sensitive data: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
- Telethon GitHub issues #1488 (AuthKeyDuplicated), #3041 #4535 (catch_up bugs), #3753 (session security)

### Secondary (MEDIUM confidence)
- greenvirtual.com.br — features de filtro por horário, análise de gale, breakdown por liga
- betr.pro — equity curves, P&L tracking, integração Telegram
- Pikkit — filtros cross-liga e tipo de aposta
- EC2 t3.micro pricing: https://www.economize.cloud/resources/aws/pricing/ec2/t3.micro/
- RDS db.t4g.micro pricing: https://www.economize.cloud/resources/aws/pricing/rds/db.t4g.micro/
- Streamlit vs Dash 2025: https://squadbase.dev/en/blog/streamlit-vs-dash-in-2025-comparing-data-app-frameworks
- psycopg2 vs asyncpg benchmark: https://www.tigerdata.com/blog/psycopg2-vs-psycopg3-performance-benchmark
- Snyk State of Secrets 2025 (28.65M secrets vazados): https://snyk.io/articles/state-of-secrets/
- Plotly community — Dash + gunicorn + nginx production patterns

### Tertiary (LOW confidence)
- Nenhuma fonte de baixa confiança foi usada como base para recomendações críticas.

---
*Research completed: 2026-04-03*
*Ready for roadmap: yes*
