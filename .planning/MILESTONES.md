# Milestones

## v1.3 Análise Individual de Sinais (Shipped: 2026-04-04)

**Phases completed:** 7 phases, 13 plans, 13 tasks

**Key accomplishments:**

- Migration idempotente PostgreSQL com group_id + mercado_id em signals, constraint composta UNIQUE(group_id, message_id) e store._resolve_mercado_id() mapeando entrada para FK de mercado
- listener.py adaptado para escutar Over 2.5 e Ambas Marcam simultaneamente via TELEGRAM_GROUP_IDS (CSV), com verificacao de acesso por grupo, handler unico via add_event_handler e event.chat_id como group_id no upsert
- One-liner:
- One-liner:
- Testes TDD red-first para layout v1.2 com 17 IDs de componentes novos e CSS de contraste DARKLY para RadioItems
- One-liner:
- Funcoes helper puras _calcular_stakes_gale, _agregar_por_entrada e _get_colunas_visiveis com testes TDD red-first e placeholders de layout para Config Mercados (DASH-03) e Performance (DASH-04)
- 1. [Rule 1 - Bug] dbc.Table nao aceita parametro dark=True em dbc 2.0.4
- Funcoes puras de agregacao por liga/tentativa em queries.py + 3 builders Plotly (stacked bar, equity curve, donut gale) com 17 testes TDD verdes
- 3 secoes visuais (liga, equity curve, gale) integradas no callback master via _build_phase13_section, substituindo phase13-placeholder com dbc.Cards reativos aos filtros globais
- Dashboard migrado para Dash Pages com shell mínimo em dashboard.py e todo o conteúdo (layout, callbacks, helpers) em pages/home.py, desbloqueando URL routing para Phase 15
- Duas novas funcoes em queries.py: get_sinal_detalhado (SELECT com JOIN mercados) e calculate_pl_detalhado_por_sinal (breakdown principal + complementares individuais + totais), com 6 testes TDD cobrindo GREEN/RED/Gale/N/A

---

## v1.1 Cloud Deploy (Shipped: 2026-04-04)

**Phases completed:** 5 phases, 10 plans, 17 tasks

**Key accomplishments:**

- Auditoria git confirma historico limpo, dashboard passa a usar DASH_DEBUG env var (off por padrao), e .env.example documenta 12 variaveis incluindo AWS para Phase 6
- README.md com 160 linhas criado do zero: setup local em 9 passos, stack completa, deploy AWS placeholder e aviso explícito de segurança sobre o arquivo .session do Telethon
- One-liner:
- Repositório LucianoAtoa/HelperTipsFutebolVirtual tornado público com CI verde (lint + 132 testes) em primeiro push
- Script bash idempotente de bootstrap EC2 (swap 1GB, usuario helpertips, pacotes base) + guia de 6 passos para provisionamento via AWS Console com Security Group restrito e Elastic IP
- Scripts bash para instalar PostgreSQL 16 via PGDG, configurar role/banco/auth com scram-sha-256, ajustar shared_buffers para 64MB e criar budget alert de $15/mes no AWS Budgets
- Script de backup diario pg_dump + .session para S3 via IAM instance profile sem access keys estaticos, com cron as 03:00 UTC e rotacao automatica de 30 dias
- One-liner:
- gunicorn configurado como WSGI server para o Dash dashboard, rodando como systemd service com 2 workers em 127.0.0.1:8050 e logrotate compartilhado com o listener
- nginx configurado como reverse proxy com HTTP Basic Auth protegendo o dashboard gunicorn: porta 80 -> 127.0.0.1:8050 com credenciais via .htpasswd bcrypt lidas do .env

---

## v1.0 MVP (Shipped: 2026-04-03)

**Phases completed:** 4 phases, 18 plans, 26 tasks
**Timeline:** 2 dias (2026-04-02 → 2026-04-03)
**Codebase:** 5,050 LOC Python | 97 commits | 132 testes passando

**Key accomplishments:**

1. Pipeline Telegram → PostgreSQL completo: Telethon listener com captura em tempo real de sinais e resultados (NewMessage + MessageEdited), parser regex para formato real do {VIP} ExtremeTips, upsert com deduplicação e proteção contra overwrite de resultado
2. Dashboard web Plotly Dash: Interface dark theme (DARKLY) com 5 KPI cards, filtros interativos (liga/entrada/data), simulação ROI com Gale, AG Grid com histórico paginado e highlight de pendentes
3. Sistema de mercados complementares: 14 entradas complementares com validação por placar, stakes Martingale, ROI breakdown por mercado e ROI Total Combinado no dashboard
4. Analytics avançados em 3 abas: Temporal (heatmap, equity curve, DOW), Gale & Streaks (análise por nível, sequências), Volume (sinais/dia, período, cross-dimensional)
5. Badge de cobertura do parser com modal de falhas — visibilidade operacional direto no dashboard

**Known Gaps (from audit):**

- MKT-04, MKT-05: Gap de documentação — sem VERIFICATION.md para Phase 2.1 (implementação confirmada pelo integration checker)
- Nyquist validation não completada (todas as fases em draft)

---
