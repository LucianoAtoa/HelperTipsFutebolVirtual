# Phase 9: Listener Multi-Grupo - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Listener captura sinais dos dois grupos Telegram (Over 2.5 e Ambas Marcam) simultaneamente, armazenando-os no PostgreSQL com identificação de grupo de origem e vínculo ao mercado. Processo único, configuração via .env.

</domain>

<decisions>
## Implementation Decisions

### Arquitetura Multi-Grupo
- **D-01:** Handler único com `chats=[id1, id2]` — Telethon aceita lista nativamente. `event.chat_id` identifica o grupo de origem dentro do handler. Não duplicar handlers.
- **D-02:** Variável de ambiente muda de `TELEGRAM_GROUP_ID` (singular) para `TELEGRAM_GROUP_IDS=id1,id2` (CSV). Listener parseia a string em lista de ints no startup.
- **D-03:** Verificação de acesso (`get_entity`) expandida para iterar sobre cada ID da lista no startup, logando erro se algum for inválido.

### Identificação de Mercado
- **D-04:** Dicionário de normalização em `store.py` resolve `entrada` (texto do parser) → `mercado_id` (FK para tabela `mercados`) no momento do upsert. Single responsibility — resolução concentrada em um ponto.
- **D-05:** Campo `mercado_id INTEGER REFERENCES mercados(id)` adicionado à tabela `signals`. Habilita JOIN direto para P&L e complementares nas fases 10-13.
- **D-06:** Se `entrada` não mapear para nenhum mercado conhecido, logar warning mas ainda inserir o sinal (mercado_id = NULL). Não rejeitar dados.

### Schema e Deduplicação
- **D-07:** Coluna `group_id BIGINT NOT NULL` adicionada à tabela `signals`.
- **D-08:** Constraint `UNIQUE(group_id, message_id)` substitui a atual `UNIQUE(message_id)`. No Telegram, message_id é único por chat, não globalmente.
- **D-09:** Upsert muda para `ON CONFLICT (group_id, message_id) DO UPDATE`. Listener passa `event.chat_id` como `group_id` no dict do parsed signal.

### Deploy e Migração
- **D-10:** Migration SQL idempotente: `ALTER TABLE signals ADD COLUMN IF NOT EXISTS group_id BIGINT` + `ALTER TABLE signals ADD COLUMN IF NOT EXISTS mercado_id INTEGER REFERENCES mercados(id)`.
- **D-11:** UPDATE retroativo: dados históricos recebem `group_id` do grupo original (valor do `TELEGRAM_GROUP_ID` atual no .env).
- **D-12:** Drop da constraint antiga `UNIQUE(message_id)` e criação da nova `UNIQUE(group_id, message_id)` na mesma migration.
- **D-13:** Deploy via `systemctl restart` simples — gap de ~2s aceitável dado frequência baixa de sinais.
- **D-14:** Fallback temporário no código: ler `TELEGRAM_GROUP_IDS` com fallback para `TELEGRAM_GROUP_ID` para segurança durante transição.

### Claude's Discretion
- Ordem dos passos dentro da migration SQL
- Índices adicionais em `group_id` (se necessário para performance)
- Formato do log de warning para mercado desconhecido

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Código do Listener
- `helpertips/listener.py` — Handler atual com `events.NewMessage(chats=group_id)`, lógica de startup e event loop
- `helpertips/parser.py` — Parser regex que extrai liga, entrada, horário, resultado, placar, tentativa
- `helpertips/store.py` — `upsert_signal()` com ON CONFLICT e `log_parse_failure()`
- `helpertips/db.py` — Schema DDL (signals, parse_failures, mercados, complementares), seeds, validate_config()
- `helpertips/list_groups.py` — Seleção interativa de grupo e `_salvar_group_id()`

### Deploy
- `deploy/` — Scripts bash idempotentes de deploy (01-07)

### Requisitos
- `.planning/REQUIREMENTS.md` §LIST-01, §LIST-02 — Requisitos específicos desta fase

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `parser.py`: Parser já extrai `entrada` do texto — funciona para ambos os mercados sem mudança
- `store.py`: `upsert_signal()` já usa dict — basta adicionar `group_id` e `mercado_id` ao dict
- `db.py`: `ensure_schema()` já é idempotente com `CREATE TABLE IF NOT EXISTS` e `ADD COLUMN IF NOT EXISTS`
- `list_groups.py`: `selecionar_grupo()` pode ser útil para listar IDs dos grupos disponíveis

### Established Patterns
- `asyncio.to_thread()` para wrapping de chamadas sync (psycopg2) dentro do event loop async
- `validate_config()` para fail-fast se variáveis de ambiente estiverem faltando
- `ensure_schema()` roda migration idempotente no startup — novo schema pode seguir mesmo padrão
- Logging dual: RichHandler em TTY, RotatingFileHandler em daemon

### Integration Points
- `.env` no servidor: mudar `TELEGRAM_GROUP_ID` → `TELEGRAM_GROUP_IDS`
- `systemd` unit file: nenhuma mudança necessária (mesmo processo, mesmo script)
- `REQUIRED_VARS` em `db.py`: atualizar validação para nova variável
- Tabela `mercados`: já existe com seeds para `over_2_5` e `ambas_marcam`

</code_context>

<specifics>
## Specific Ideas

- Blocker no STATE.md: Group ID do grupo "Ambas Marcam" precisa ser obtido antes de testar
- EC2 t3.micro ~650MB headroom: monitorar RAM com dois grupos (impacto esperado mínimo — mesmo processo, mesmo event loop)
- `TELEGRAM_GROUP_ID` na validação de config (`REQUIRED_VARS`) deve ser removido/substituído por `TELEGRAM_GROUP_IDS`

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-listener-multi-grupo*
*Context gathered: 2026-04-04*
