---
phase: 09-listener-multi-grupo
verified: 2026-04-04T13:37:22Z
status: passed
score: 13/13 must-haves verified
re_verification: false
---

# Phase 09: Listener Multi-Grupo — Relatório de Verificação

**Goal da Phase:** Listener captura sinais dos dois grupos Telegram simultaneamente sem perda de dados
**Verificado:** 2026-04-04T13:37:22Z
**Status:** PASSOU
**Re-verificação:** Não — verificação inicial

---

## Conquista do Goal

### Truths Observáveis

#### Plan 09-01 (Schema Migration)

| # | Truth | Status | Evidência |
|---|-------|--------|-----------|
| 1 | Schema signals tem colunas `group_id BIGINT` e `mercado_id INTEGER REFERENCES mercados(id)` | VERIFICADO | `db.py` linha 162-163: `ADD COLUMN IF NOT EXISTS group_id BIGINT` e `ADD COLUMN IF NOT EXISTS mercado_id INTEGER REFERENCES mercados(id)` |
| 2 | Constraint `UNIQUE(group_id, message_id)` substitui `UNIQUE(message_id)` | VERIFICADO | `db.py` linhas 195-206: `DROP CONSTRAINT IF EXISTS signals_message_id_key` + `ADD CONSTRAINT signals_group_message_unique UNIQUE (group_id, message_id)` |
| 3 | `upsert_signal` usa `ON CONFLICT (group_id, message_id)` e insere `mercado_id` | VERIFICADO | `store.py` linha 87: `ON CONFLICT (group_id, message_id) DO UPDATE SET` + `mercado_id = COALESCE(EXCLUDED.mercado_id, signals.mercado_id)` |
| 4 | `_resolve_mercado_id('Over 2.5')` retorna 1, `'Ambas Marcam'` retorna 2, desconhecido retorna None | VERIFICADO | `store.py` linhas 21-25: `ENTRADA_PARA_MERCADO_ID` dict + `_resolve_mercado_id()` com lookup normalizado. 6 testes unitários passando. |
| 5 | Dados históricos recebem `group_id` do grupo original via UPDATE retroativo | VERIFICADO | `db.py` linhas 165-175: UPDATE retroativo com `TELEGRAM_GROUP_IDS` ou fallback `TELEGRAM_GROUP_ID` |
| 6 | `ensure_schema()` é idempotente — pode rodar N vezes sem erro | VERIFICADO | `db.py`: `IF NOT EXISTS` em todos os DDL; teste `test_migration_idempotent_with_new_columns` passando |

#### Plan 09-02 (Listener Multi-Grupo)

| # | Truth | Status | Evidência |
|---|-------|--------|-----------|
| 7 | Listener parseia `TELEGRAM_GROUP_IDS=id1,id2` do .env em lista de ints | VERIFICADO | `listener.py` linha 133: `group_ids = [int(g.strip()) for g in group_ids_str.split(',') if g.strip()]` |
| 8 | Fallback lê `TELEGRAM_GROUP_ID` se `TELEGRAM_GROUP_IDS` não existe (D-14) | VERIFICADO | `listener.py` linha 132: `os.environ.get('TELEGRAM_GROUP_IDS') or os.environ.get('TELEGRAM_GROUP_ID', '')` |
| 9 | Handler único registrado com `chats=group_ids` para NewMessage e MessageEdited | VERIFICADO | `listener.py` linhas 223-224: `client.add_event_handler(handle_signal, events.NewMessage(chats=group_ids))` + `events.MessageEdited(chats=group_ids)` |
| 10 | `event.chat_id` é passado como `group_id` no dict do parsed signal antes do upsert | VERIFICADO | `listener.py` linha 205: `parsed['group_id'] = event.chat_id` |
| 11 | Startup verifica acesso a cada grupo via `get_entity`, remove inválidos, aborta se nenhum válido | VERIFICADO | `listener.py` linhas 163-179: loop `for gid in group_ids:`, `get_entity(gid)`, filtragem de `invalid_ids`, `sys.exit(1)` se `group_ids` vazio |
| 12 | Startup summary mostra nomes de todos os grupos conectados | VERIFICADO | `listener.py` linha 107: `f"[bold]HelperTips[/bold] - {', '.join(group_titles)}"` + `', '.join(group_titles)` no logger |
| 13 | `.env.example` documenta `TELEGRAM_GROUP_IDS` no lugar de `TELEGRAM_GROUP_ID` | VERIFICADO | `.env.example` linha 6: `TELEGRAM_GROUP_IDS=` como variável principal; `TELEGRAM_GROUP_ID` aparece apenas como comentário de fallback deprecado |

**Score:** 13/13 truths verificadas

---

### Artifacts Requeridos

| Artifact | Status | Nível 1: Existe | Nível 2: Substantivo | Nível 3: Wired |
|----------|--------|-----------------|----------------------|----------------|
| `helpertips/db.py` | VERIFICADO | Sim | Migration Phase 09 completa (linhas 160-211) | Chamado por `listener.py` via `ensure_schema(conn)` |
| `helpertips/store.py` | VERIFICADO | Sim | `ENTRADA_PARA_MERCADO_ID`, `_resolve_mercado_id()`, `upsert_signal` atualizado | Importado e usado em `listener.py` |
| `tests/test_store.py` | VERIFICADO | Sim | `_make_signal` com `group_id=99999`; 6 testes `_resolve_mercado_id`; `test_upsert_two_groups_same_message_id` | Executado — 28 testes passando |
| `tests/test_db.py` | VERIFICADO | Sim | `test_migration_adds_group_id_column`, `test_migration_adds_mercado_id_column`, `test_migration_idempotent_with_new_columns` | Executado — todos passando |
| `helpertips/listener.py` | VERIFICADO | Sim | `TELEGRAM_GROUP_IDS`, `add_event_handler`, `event.chat_id`, `group_titles` como lista | Arquivo principal do listener — ponto de entrada |
| `.env.example` | VERIFICADO | Sim | `TELEGRAM_GROUP_IDS=` documentado com comentário de uso | Template de configuração |

---

### Verificação de Key Links

| De | Para | Via | Status | Detalhe |
|----|------|-----|--------|---------|
| `helpertips/store.py` | `helpertips/db.py` | `upsert_signal` usa `ON CONFLICT (group_id, message_id)` | WIRED | `store.py` linha 87 confirma constraint composta; `db.py` cria a constraint em linha 202 |
| `helpertips/store.py` | tabela `mercados` | `_resolve_mercado_id` mapeia entrada para `mercado_id` FK | WIRED | `ENTRADA_PARA_MERCADO_ID` em `store.py` usa IDs hardcoded (1, 2) compatíveis com seeds em `db.py` linhas 118-121 |
| `helpertips/listener.py` | `helpertips/store.py` | `parsed['group_id'] = event.chat_id` passado para `upsert_signal` | WIRED | `listener.py` linha 205-209: `parsed['group_id'] = event.chat_id` + `await asyncio.to_thread(upsert_signal, conn, parsed)` |
| `helpertips/listener.py` | `.env` | `os.environ.get('TELEGRAM_GROUP_IDS')` com fallback para `TELEGRAM_GROUP_ID` | WIRED | `listener.py` linha 132: fallback completo D-14 implementado |

---

### Data-Flow Trace (Nível 4)

O listener não renderiza dados (é um processo de captura, não componente web). O fluxo de dados é:

| Origem | Fluxo | Destino | Status |
|--------|-------|---------|--------|
| Evento Telegram `NewMessage`/`MessageEdited` | `event.chat_id` → `parsed['group_id']` | `upsert_signal(conn, parsed)` → tabela `signals` com `group_id` | FLOWING |
| `event.message.text` | `parse_message()` → dict com campos | `upsert_signal` → INSERT com `ON CONFLICT (group_id, message_id)` | FLOWING |
| `data.get('entrada')` | `_resolve_mercado_id()` → `mercado_id` int | INSERT `mercado_id` FK | FLOWING |

---

### Behavioral Spot-Checks

| Comportamento | Comando | Resultado | Status |
|---------------|---------|-----------|--------|
| `_resolve_mercado_id` retorna IDs corretos | `python3 -m pytest tests/test_store.py::test_resolve_mercado_id_over tests/test_store.py::test_resolve_mercado_id_ambas -q` | 2 passed | PASSOU |
| Deduplicação multi-grupo funciona | `python3 -m pytest tests/test_store.py::test_upsert_two_groups_same_message_id -q` | 1 passed | PASSOU |
| Migration idempotente | `python3 -m pytest tests/test_db.py::test_migration_idempotent_with_new_columns -q` | 1 passed | PASSOU |
| Suite completa de testes | `python3 -m pytest tests/ -q` | 150 passed in 1.04s | PASSOU |
| Sintaxe Python dos arquivos principais | `python3 -c "import ast; ast.parse(...)"` | Syntax OK (todos 3) | PASSOU |

---

### Cobertura de Requisitos

| Requisito | Plan(s) | Descrição | Status | Evidência |
|-----------|---------|-----------|--------|-----------|
| **LIST-01** | 09-01, 09-02 | Listener escuta grupos Over 2.5 e Ambas Marcam simultaneamente via `TELEGRAM_GROUP_IDS=id1,id2` | SATISFEITO | Constraint `UNIQUE(group_id, message_id)` permite mesmo `message_id` em grupos diferentes; `listener.py` registra handler com `chats=[group_ids]`; `test_upsert_two_groups_same_message_id` confirma 2 rows distintas |
| **LIST-02** | 09-01, 09-02 | Parser identifica mercado pelo campo `entrada` da mensagem — armazena "Over 2.5" ou "Ambas Marcam" | SATISFEITO | `_resolve_mercado_id()` em `store.py` mapeia `entrada` para `mercado_id` FK; campo `entrada` preservado no upsert; `test_upsert_with_mercado_id` confirma `mercado_id=1` para "Over 2.5" |

**Requisitos órfãos:** Nenhum. REQUIREMENTS.md mapeia LIST-01 e LIST-02 para Phase 9 — ambos cobertos pelos dois plans da fase.

---

### Anti-Patterns Encontrados

Nenhum anti-pattern encontrado nos arquivos modificados (`db.py`, `store.py`, `listener.py`, `.env.example`). Varredura completa confirmou ausência de:
- Comentários TODO/FIXME/PLACEHOLDER
- Implementações vazias (`return null`, `return {}`, `return []`)
- Handlers de formulário stub
- Retornos estáticos sem query de DB

---

### Verificação Humana Necessária

#### 1. Conectividade Real com Dois Grupos Telegram

**Teste:** Configurar `.env` com `TELEGRAM_GROUP_IDS=<over_id>,<ambas_id>` e executar `python3 -m helpertips.listener` (ou `python3 helpertips/listener.py`)
**Esperado:** Startup exibe panel com os dois nomes de grupo concatenados; mensagens de Over 2.5 e Ambas Marcam ambas persistidas na tabela `signals` com `group_id` correto de cada grupo
**Por que humano:** Requer credenciais Telegram reais (`TELEGRAM_API_ID`, `TELEGRAM_API_HASH`), sessão autenticada e acesso aos grupos privados. O Group ID do grupo "Ambas Marcam" ainda não foi obtido (pendente per SUMMARY 09-02).

#### 2. Comportamento de Fallback em Daemon (sem TTY)

**Teste:** Executar o listener como serviço systemd (ou redirecionar stdout para arquivo) com `TELEGRAM_GROUP_IDS` vazio e verificar comportamento de abort
**Esperado:** `logger.error("TELEGRAM_GROUP_IDS vazio ou invalido. Encerrando.")` no log + `sys.exit(1)`
**Por que humano:** Requer ambiente de serviço real ou simulação de `sys.stdout.isatty() == False`.

---

## Resumo

A Phase 09 atingiu completamente seu goal. Todos os 13 must-haves verificados, suite de 150 testes passando, commits atômicos documentados (`bd7ae68`, `c9e550e`), sem anti-patterns ou stubs. O único item pendente é operacional — obter o Group ID real do grupo "Ambas Marcam" no Telegram e configurar na EC2, o que requer acesso humano às credenciais.

---

_Verificado: 2026-04-04T13:37:22Z_
_Verificador: Claude (gsd-verifier)_
