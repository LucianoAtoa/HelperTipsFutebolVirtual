# Phase 1: Foundation - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Pipeline de captura de sinais do grupo Telegram {VIP} ExtremeTips para PostgreSQL. Inclui: listener Telethon, parser regex, store com upsert, e saída terminal com resumo na inicialização. Dashboard é Fase 2.

</domain>

<decisions>
## Implementation Decisions

### Formato das mensagens
- **D-01:** Copiar 10-20 mensagens reais manualmente do grupo antes de escrever regex — testes e fixtures ancorados em dados reais, não em formato assumido
- **D-02:** Mensagens copiadas vão para `tests/fixtures/sample_signals.txt` como fixture do pytest

### Saída do terminal
- **D-03:** Usar `rich` library para output formatado — startup summary como Table/Panel, sinais com cores por resultado (GREEN=verde, RED=vermelho)
- **D-04:** `RichHandler` integrado com `logging` stdlib para compatibilidade com logs internos do Telethon
- **D-05:** Nível de verbosidade: INFO no startup summary, INFO por sinal capturado, WARNING/ERROR para falhas de parse e desconexão

### Estrutura do projeto
- **D-06:** Package Python `helpertips/` com `__init__.py` e `pyproject.toml` mínimo
- **D-07:** `pip install -e .` para desenvolvimento, pytest resolve imports automaticamente
- **D-08:** Estrutura: `helpertips/listener.py`, `helpertips/parser.py`, `helpertips/store.py`, `helpertips/db.py`
- **D-09:** Tests em `tests/` na raiz, fixtures em `tests/fixtures/`

### Tratamento de falhas do parser
- **D-10:** Abordagem combinada: log warning no terminal + armazenar raw_text no banco
- **D-11:** Tabela `parse_failures` com colunas: `raw_text`, `received_at`, `failure_reason`
- **D-12:** Permite diagnóstico de mudanças de formato e atualização retroativa do parser
- **D-13:** Taxa de cobertura (PARS-07) calculada como parseados / (parseados + falhas)

### Claude's Discretion
- Nomes exatos de colunas da tabela `signals` (além dos obrigatórios: liga, entrada, horario, resultado, placar)
- Formato exato do startup summary Panel/Table com `rich`
- Estratégia de limpeza/housekeeping da tabela `parse_failures`
- Configuração de logging levels por módulo

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements are fully captured in decisions above and in:

### Projeto
- `CLAUDE.md` — Stack definida (Telethon 1.42, psycopg2-binary, python-dotenv), padrão asyncio.to_thread para DB writes, processos separados listener/dashboard
- `.planning/REQUIREMENTS.md` — Requisitos LIST-01..05, PARS-01..07, DB-01..04, TERM-01..03, OPER-02..03
- `.planning/ROADMAP.md` — Phase 1 success criteria e dependências

### Research
- `.planning/phases/01-foundation/01-RESEARCH.md` — Pesquisa técnica sobre Telethon, parser, DB schema, bootstrap

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Nenhum — projeto greenfield, sem código existente

### Established Patterns
- Nenhum padrão estabelecido ainda — Fase 1 define os padrões base

### Integration Points
- `helpertips/db.py` → PostgreSQL (psycopg2-binary)
- `helpertips/listener.py` → Telegram API (Telethon)
- `helpertips/store.py` → `db.py` (usa get_connection)
- `helpertips/listener.py` → `parser.py` + `store.py` (pipeline: mensagem → parse → upsert)

</code_context>

<specifics>
## Specific Ideas

- Mensagens reais do grupo devem ser copiadas pelo usuário antes do Wave 1 (plan 01-02) — são o input crítico para o parser
- `rich` adiciona dependência mínima (~2MB) mas transforma a experiência do terminal de "log wall" para interface legível
- Tabela `parse_failures` serve como "safety net" — se o formato do grupo mudar, os dados não se perdem

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-04-03*
