# Phase 09: Listener Multi-Grupo - Research

**Pesquisado:** 2026-04-04
**Domínio:** Telethon multi-grupo, migração PostgreSQL de constraint única, mapeamento entrada→mercado_id
**Confiança:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Handler único com `chats=[id1, id2]` — Telethon aceita lista nativamente. `event.chat_id` identifica o grupo de origem dentro do handler. Não duplicar handlers.
- **D-02:** Variável de ambiente muda de `TELEGRAM_GROUP_ID` (singular) para `TELEGRAM_GROUP_IDS=id1,id2` (CSV). Listener parseia a string em lista de ints no startup.
- **D-03:** Verificação de acesso (`get_entity`) expandida para iterar sobre cada ID da lista no startup, logando erro se algum for inválido.
- **D-04:** Dicionário de normalização em `store.py` resolve `entrada` (texto do parser) → `mercado_id` (FK para tabela `mercados`) no momento do upsert. Single responsibility — resolução concentrada em um ponto.
- **D-05:** Campo `mercado_id INTEGER REFERENCES mercados(id)` adicionado à tabela `signals`. Habilita JOIN direto para P&L e complementares nas fases 10-13.
- **D-06:** Se `entrada` não mapear para nenhum mercado conhecido, logar warning mas ainda inserir o sinal (mercado_id = NULL). Não rejeitar dados.
- **D-07:** Coluna `group_id BIGINT NOT NULL` adicionada à tabela `signals`.
- **D-08:** Constraint `UNIQUE(group_id, message_id)` substitui a atual `UNIQUE(message_id)`. No Telegram, message_id é único por chat, não globalmente.
- **D-09:** Upsert muda para `ON CONFLICT (group_id, message_id) DO UPDATE`. Listener passa `event.chat_id` como `group_id` no dict do parsed signal.
- **D-10:** Migration SQL idempotente: `ALTER TABLE signals ADD COLUMN IF NOT EXISTS group_id BIGINT` + `ALTER TABLE signals ADD COLUMN IF NOT EXISTS mercado_id INTEGER REFERENCES mercados(id)`.
- **D-11:** UPDATE retroativo: dados históricos recebem `group_id` do grupo original (valor do `TELEGRAM_GROUP_ID` atual no .env).
- **D-12:** Drop da constraint antiga `UNIQUE(message_id)` e criação da nova `UNIQUE(group_id, message_id)` na mesma migration.
- **D-13:** Deploy via `systemctl restart` simples — gap de ~2s aceitável dado frequência baixa de sinais.
- **D-14:** Fallback temporário no código: ler `TELEGRAM_GROUP_IDS` com fallback para `TELEGRAM_GROUP_ID` para segurança durante transição.

### Claude's Discretion

- Ordem dos passos dentro da migration SQL
- Índices adicionais em `group_id` (se necessário para performance)
- Formato do log de warning para mercado desconhecido

### Deferred Ideas (OUT OF SCOPE)

Nenhuma — discussão ficou dentro do escopo da fase.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LIST-01 | Listener escuta grupos Over 2.5 e Ambas Marcam simultaneamente via lista de group IDs no .env (TELEGRAM_GROUP_IDS=id1,id2) | Telethon `events.NewMessage(chats=[id1,id2])` — padrão nativo verificado em docs oficiais. `event.chat_id` disponível para identificar origem. |
| LIST-02 | Parser identifica mercado principal pelo conteúdo da "Entrada recomendada" na mensagem — campo `entrada` armazena "Over 2.5" ou "Ambas Marcam" | Parser já extrai `entrada` do campo "Entrada recomendada". Dicionário de normalização em `store.py` faz o mapeamento `entrada → mercado_id`. Schema já tem tabela `mercados` com seeds corretos. |
</phase_requirements>

---

## Summary

A Phase 09 expande o listener atual (single-group) para receber sinais de dois grupos Telegram simultaneamente — Over 2.5 e Ambas Marcam — sem duplicar processos. O Telethon suporta isso nativamente: `events.NewMessage(chats=[id1, id2])` aceita lista e `event.chat_id` identifica a origem dentro do mesmo handler. Isso elimina a necessidade de qualquer nova dependência.

O principal trabalho técnico é uma migração de schema PostgreSQL em dois eixos: (1) adicionar `group_id BIGINT` à tabela `signals` e trocar a constraint `UNIQUE(message_id)` por `UNIQUE(group_id, message_id)` — necessário porque message_id é único *por chat*, não globalmente; (2) adicionar `mercado_id INTEGER REFERENCES mercados(id)` resolvido por um dicionário de normalização em `store.py`. Ambas as colunas se tornam NOT NULL logicamente mas a migration usa `ADD COLUMN IF NOT EXISTS` para idempotência, com um UPDATE retroativo para dados históricos.

A variável de ambiente `TELEGRAM_GROUP_ID` (singular) é substituída por `TELEGRAM_GROUP_IDS=id1,id2` (CSV), com fallback temporário no código (D-14). O deploy é `systemctl restart` simples — nenhuma mudança na unit file, nenhuma nova dependência pip.

**Recomendação principal:** Executar os passos na ordem: migration SQL → UPDATE retroativo → troca de variável no .env → deploy do listener atualizado. Não inverter essa ordem — o listener novo precisa do schema novo para funcionar.

---

## Standard Stack

### Core

| Library | Version | Purpose | Por que é padrão |
|---------|---------|---------|-----------------|
| Telethon | 1.42.0 (instalado) | Listener MTProto | `chats=[list]` em `NewMessage`/`MessageEdited` é suportado nativamente; `event.chat_id` identifica origem |
| psycopg2-binary | >=2.9 (instalado) | Driver PostgreSQL sync | Já em uso; nenhuma mudança necessária |
| python-dotenv | >=1.0 (instalado) | Leitura de `.env` | Já em uso; parse de CSV é stdlib |
| PostgreSQL | 16 | Banco de dados | `ALTER TABLE ... IF NOT EXISTS`, `DROP CONSTRAINT IF EXISTS` — todos suportados |

### Sem novas dependências

Esta fase não requer instalação de nenhum pacote novo. Toda a implementação usa o stack já instalado.

---

## Architecture Patterns

### Padrão 1: Handler Único Multi-Grupo (D-01)

**O que é:** Um único decorador `@client.on(events.NewMessage(chats=[...]))` cobre múltiplos grupos. O handler usa `event.chat_id` para identificar de qual grupo veio a mensagem.

**Quando usar:** Sempre que um único processo precisa ouvir mais de um chat Telegram sem duplicar lógica.

**Implementação:**

```python
# listener.py — substituir o handler atual por esta versão multi-grupo

group_ids_str = os.environ.get('TELEGRAM_GROUP_IDS') or os.environ.get('TELEGRAM_GROUP_ID', '')
group_ids = [int(g.strip()) for g in group_ids_str.split(',') if g.strip()]

@client.on(events.NewMessage(chats=group_ids))
@client.on(events.MessageEdited(chats=group_ids))
async def handle_signal(event):
    group_id = event.chat_id  # identifica qual grupo enviou
    parsed = parse_message(event.message.text, event.message.id)
    if parsed:
        parsed['group_id'] = group_id
        await asyncio.to_thread(upsert_signal, conn, parsed)
```

**Fonte:** Telethon docs — `chats` aceita `list | tuple` de IDs, peers ou entidades. Verificado via WebSearch contra docs oficiais 1.42.0.

### Padrão 2: Verificação de Acesso Multi-Grupo no Startup (D-03)

**O que é:** Iterar sobre todos os IDs no startup, chamando `get_entity` para cada um. Falha hard apenas se TODOS falharem (um grupo inválido não deve bloquear o outro).

**Implementação:**

```python
group_titles = []
invalid_ids = []
for gid in group_ids:
    try:
        entity = await client.get_entity(gid)
        group_titles.append(f"{entity.title} ({gid})")
    except Exception as e:
        logger.error("Não foi possível acessar grupo %s: %s", gid, e)
        invalid_ids.append(gid)

if invalid_ids:
    logger.warning("Grupos inválidos ignorados: %s", invalid_ids)
    # Remover IDs inválidos da lista ativa
    group_ids = [g for g in group_ids if g not in invalid_ids]

if not group_ids:
    logger.error("Nenhum grupo válido encontrado. Encerrando.")
    sys.exit(1)
```

### Padrão 3: Dicionário de Normalização entrada→mercado_id (D-04)

**O que é:** Mapa estático em `store.py` que converte o texto livre do campo `entrada` para o `mercado_id` FK correspondente. Concentra a lógica de mapeamento em um único ponto.

**Implementação:**

```python
# store.py — adicionar no topo do módulo

# Normalização de entrada para mercado_id
# Chave: texto como vem do parser (case-insensitive depois do .lower().strip())
# Valor: mercado_id da tabela mercados (Over 2.5 = 1, Ambas Marcam = 2)
ENTRADA_PARA_MERCADO_ID = {
    "over 2.5": 1,
    "ambas marcam": 2,
    "ambas as equipes marcam": 2,  # variante possível
}

def _resolve_mercado_id(entrada: str | None) -> int | None:
    """Resolve texto de entrada para mercado_id FK. Retorna None se não mapeado."""
    if not entrada:
        return None
    normalized = entrada.lower().strip()
    mercado_id = ENTRADA_PARA_MERCADO_ID.get(normalized)
    if mercado_id is None:
        logger.warning(
            "Mercado desconhecido para entrada '%s' — inserindo com mercado_id=NULL", entrada
        )
    return mercado_id
```

**Nota:** Os IDs 1 e 2 correspondem à ordem de inserção dos seeds em `db.py` (`over_2_5` e `ambas_marcam`). Para robustez, uma alternativa é fazer lookup por slug na tabela `mercados` no startup e popular o dicionário dinamicamente — porém, dado que os seeds são fixos e idempotentes, hardcoded IDs são aceitáveis para esta fase.

### Padrão 4: Migration SQL Idempotente (D-10, D-11, D-12)

**O que é:** A migration é executada dentro do `ensure_schema()` existente (que já é idempotente). A ordem de operações importa para evitar erros de constraint.

**Ordem correta:**

```sql
-- Passo 1: Adicionar novas colunas (seguro repetir com IF NOT EXISTS)
ALTER TABLE signals ADD COLUMN IF NOT EXISTS group_id  BIGINT;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS mercado_id INTEGER REFERENCES mercados(id);

-- Passo 2: Preencher dados históricos (UPDATE retroativo — D-11)
-- Executar apenas se group_id ainda está NULL (proteção para re-execução)
UPDATE signals
SET group_id = %(original_group_id)s
WHERE group_id IS NULL;

-- Passo 3: Tornar group_id NOT NULL (só após o UPDATE retroativo)
ALTER TABLE signals ALTER COLUMN group_id SET NOT NULL;
-- ATENÇÃO: Esse passo falha se ainda existir algum NULL — garante consistência

-- Passo 4: Drop da constraint antiga (IF EXISTS para idempotência)
ALTER TABLE signals DROP CONSTRAINT IF EXISTS signals_message_id_key;

-- Passo 5: Criar nova constraint composta
ALTER TABLE signals ADD CONSTRAINT signals_group_message_unique
    UNIQUE (group_id, message_id);

-- Passo 6: Índice em group_id (opcional para performance — Claude's Discretion)
CREATE INDEX IF NOT EXISTS idx_signals_group_id ON signals(group_id);
```

**Pitfall crítico:** O `ALTER COLUMN SET NOT NULL` no passo 3 DEVE vir após o UPDATE retroativo do passo 2. Se invertidos, a migration falha com `column "group_id" contains null values`.

**Nome da constraint atual:** O PostgreSQL gera automaticamente `signals_message_id_key` para a declaração `message_id BIGINT UNIQUE NOT NULL` (convenção: `{tabela}_{coluna}_key`).

### Padrão 5: Upsert com group_id (D-09)

```python
# store.py — upsert_signal atualizado

def upsert_signal(conn, data: dict) -> None:
    mercado_id = _resolve_mercado_id(data.get('entrada'))
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO signals (
                message_id, group_id, mercado_id, liga, entrada, horario, periodo,
                dia_semana, resultado, placar, tentativa, raw_text, received_at, updated_at
            ) VALUES (
                %(message_id)s, %(group_id)s, %(mercado_id)s, %(liga)s, %(entrada)s,
                %(horario)s, %(periodo)s, %(dia_semana)s, %(resultado)s, %(placar)s,
                %(tentativa)s, %(raw_text)s, NOW(), NOW()
            )
            ON CONFLICT (group_id, message_id) DO UPDATE SET
                resultado  = COALESCE(EXCLUDED.resultado, signals.resultado),
                placar     = COALESCE(EXCLUDED.placar, signals.placar),
                tentativa  = COALESCE(EXCLUDED.tentativa, signals.tentativa),
                mercado_id = COALESCE(EXCLUDED.mercado_id, signals.mercado_id),
                liga       = EXCLUDED.liga,
                entrada    = EXCLUDED.entrada,
                updated_at = NOW()
            WHERE
                EXCLUDED.resultado IS NOT NULL
                OR signals.resultado IS NULL
            """,
            {**data, 'mercado_id': mercado_id},
        )
    conn.commit()
```

### Estrutura de arquivos modificados

```
helpertips/
├── listener.py     — parse TELEGRAM_GROUP_IDS, handler multi-grupo, startup summary atualizado
├── db.py           — REQUIRED_VARS, ensure_schema() com migration novas colunas + constraint
├── store.py        — ENTRADA_PARA_MERCADO_ID dict, _resolve_mercado_id(), upsert_signal() atualizado
.env                — TELEGRAM_GROUP_ID → TELEGRAM_GROUP_IDS=id1,id2
.env.example        — idem
tests/
├── test_store.py   — testes para upsert com group_id e mercado_id
├── test_db.py      — testes para migration (novas colunas, constraint)
├── conftest.py     — fixtures _make_signal() atualizadas para incluir group_id
```

### Anti-Patterns a Evitar

- **Dois handlers separados:** Registrar `@client.on(events.NewMessage(chats=id1))` e `@client.on(events.NewMessage(chats=id2))` separadamente — funciona mas duplica lógica e torna difícil adicionar mais grupos. D-01 proíbe explicitamente.
- **Dois processos/services:** Um listener por grupo — violaria D-01 e dobraria o uso de RAM/conexões DB.
- **`SET NOT NULL` antes do UPDATE retroativo:** A migration falha com nulls existentes. Sempre UPDATE antes de SET NOT NULL.
- **Ignorar fallback D-14:** Em ambientes com `.env` antigo ainda apontando `TELEGRAM_GROUP_ID`, o listener quebraria sem o fallback.
- **mercado_id hardcoded no listener:** A resolução pertence ao `store.py` (D-04). O listener não deve saber de IDs de mercado.

---

## Don't Hand-Roll

| Problema | Não construir | Usar em vez disso | Por quê |
|---------|---------------|-------------------|---------|
| Multi-grupo Telegram | Sistema de dispatch customizado | `chats=[id1, id2]` do Telethon | Nativo, zero overhead, `event.chat_id` já disponível |
| Parser separado por mercado | Parser condicional por grupo | Parser atual (`parser.py`) sem modificação | Campo `entrada` já captura o mercado; parser é agnóstico ao grupo |
| Migração com downtime | Recriar tabela do zero | `ALTER TABLE ... IF NOT EXISTS` + `DROP CONSTRAINT IF EXISTS` | PostgreSQL 16 suporta operações in-place sem lock prolongado para ADD COLUMN |

---

## Common Pitfalls

### Pitfall 1: SET NOT NULL antes do UPDATE retroativo
**O que dá errado:** `ALTER COLUMN group_id SET NOT NULL` falha com `column "group_id" contains null values` se executado antes do UPDATE que preenche dados históricos.
**Por que acontece:** Dados históricos foram inseridos antes da coluna existir; ADD COLUMN cria com NULL nos registros existentes.
**Como evitar:** Ordem obrigatória: ADD COLUMN → UPDATE WHERE NULL → SET NOT NULL. A função `ensure_schema()` deve executar nessa sequência.
**Sinal de alerta:** Migration falha com mensagem de null values.

### Pitfall 2: Nome da constraint antiga incorreto no DROP
**O que dá errado:** `DROP CONSTRAINT IF EXISTS signals_message_id_key` não encontra a constraint se o nome real for diferente.
**Por que acontece:** PostgreSQL usa convenção `{tabela}_{coluna}_key` para constraints implícitas (`BIGINT UNIQUE NOT NULL`), mas o nome pode ter sido customizado. No caso atual, a declaração `message_id BIGINT UNIQUE NOT NULL` em `db.py` gera `signals_message_id_key`.
**Como evitar:** Verificar o nome real antes do deploy: `SELECT conname FROM pg_constraint WHERE conrelid = 'signals'::regclass AND contype = 'u';`
**Sinal de alerta:** Após a migration, ainda existe a constraint antiga (upsert de dois grupos com mesmo message_id não conflita corretamente).

### Pitfall 3: message_id duplicado entre grupos
**O que dá errado:** Dois grupos diferentes podem ter mensagens com o mesmo `message_id` (os IDs são sequenciais por chat, não globais). Com a constraint antiga `UNIQUE(message_id)`, o segundo sinal de um grupo diferente seria ignorado (ON CONFLICT) ou rejeitado.
**Por que acontece:** message_id no Telegram é uma sequência por chat. `message_id=1000` pode existir no grupo A e no grupo B.
**Como evitar:** A constraint `UNIQUE(group_id, message_id)` é a correção. Não implantar o listener multi-grupo sem essa migration.

### Pitfall 4: `TELEGRAM_GROUP_IDS` vazio sem fallback
**O que dá errado:** `int(g.strip()) for g in ''.split(',') if g.strip()` produz lista vazia, causando `chats=[]` que o Telethon interpreta como "nenhum filtro de chat" — recebendo mensagens de TODOS os chats.
**Por que acontece:** `.env` antigo com `TELEGRAM_GROUP_ID` em vez de `TELEGRAM_GROUP_IDS`.
**Como evitar:** Implementar D-14 (fallback). Após parse da lista, adicionar validação: `if not group_ids: sys.exit("TELEGRAM_GROUP_IDS vazio ou inválido")`.

### Pitfall 5: mercado_id baseado em IDs numéricos assume ordem de seed
**O que dá errado:** O dicionário `ENTRADA_PARA_MERCADO_ID = {"over 2.5": 1, "ambas marcam": 2}` assume que os seeds sempre geram IDs 1 e 2 na tabela `mercados`. Se o seed tiver sido executado em banco limpo após delete manual, os IDs podem ser diferentes (PostgreSQL SERIAL não reseta).
**Por que acontece:** SERIAL/SEQUENCE em PostgreSQL não reseta no truncate ou delete.
**Como evitar:** Para maior robustez, o dicionário pode fazer lookup por slug no startup: `SELECT id, slug FROM mercados` e popular o dict dinamicamente. Porém, dado que o banco nunca teve dados de mercados deletados (apenas dados de signals em testes), IDs fixos são aceitáveis. Documentar a suposição.

### Pitfall 6: `get_entity` com lista de grupos bloqueia o startup se um grupo for lento
**O que dá errado:** `get_entity` é uma chamada de rede; com dois grupos, a verificação leva o dobro do tempo e pode timeout se a rede estiver instável.
**Como evitar:** Chamadas são sequenciais com try/except por grupo (D-03) — falha de um não bloqueia o outro. Sem necessidade de asyncio.gather aqui; a simplicidade é preferível.

---

## Existing Code Analysis

### O que está no listener.py atual

O listener atual tem uma única variável `group_id = int(group_id_str)` e usa:

```python
@client.on(events.NewMessage(chats=group_id))
@client.on(events.MessageEdited(chats=group_id))
async def handle_signal(event):
    ...
    parsed = parse_message(event.message.text, event.message.id)
    ...
    await asyncio.to_thread(upsert_signal, conn, parsed)
```

Para a migração multi-grupo, `group_id` vira `group_ids` (lista) e `parsed['group_id'] = event.chat_id` é adicionado antes do `upsert_signal`.

### O que está no store.py atual

`upsert_signal` usa `ON CONFLICT (message_id)` — precisa ser trocado para `ON CONFLICT (group_id, message_id)`. O dict de dados não inclui `group_id` nem `mercado_id` — ambos precisam ser adicionados.

### O que está no db.py atual

- `REQUIRED_VARS` não inclui `TELEGRAM_GROUP_ID` nem `TELEGRAM_GROUP_IDS` (o comentário confirma que é opcional). Após D-02, `TELEGRAM_GROUP_IDS` continua opcional mas com fallback para `TELEGRAM_GROUP_ID`.
- `ensure_schema()` já é idempotente com `CREATE TABLE IF NOT EXISTS` e `ADD COLUMN IF NOT EXISTS` — o mesmo padrão aplica-se às novas colunas.
- Tabela `mercados` já existe com seeds para `over_2_5` e `ambas_marcam`.

### O que está nos testes atuais

- `tests/test_store.py`: `_make_signal()` não inclui `group_id`. Precisa ser atualizado.
- `tests/test_db.py`: Testa seeds de mercados e complementares — não precisará de mudanças significativas, mas pode receber testes para novas colunas.
- `tests/conftest.py`: Fixtures de parser não precisam de `group_id` (parser não o inclui — é adicionado pelo listener).

---

## Runtime State Inventory

Esta fase é uma expansão incremental, não um rename. Porém, há estado de runtime relevante:

| Categoria | Itens Encontrados | Ação Necessária |
|----------|-------------------|-----------------|
| Stored data | Tabela `signals` em PostgreSQL com dados históricos — `group_id` e `mercado_id` ainda não existem; `UNIQUE(message_id)` constraint ativa | Migration SQL + UPDATE retroativo + troca de constraint |
| Live service config | `.env` no EC2 (32.194.158.134) tem `TELEGRAM_GROUP_ID` (singular) — Group ID do grupo "Ambas Marcam" ainda desconhecido | Blocker: obter Group ID do Ambas Marcam antes de configurar `TELEGRAM_GROUP_IDS` |
| OS-registered state | systemd unit file `helpertips-listener.service` — sem mudança necessária (mesmo script, mesmo processo) | Nenhuma |
| Secrets/env vars | `TELEGRAM_GROUP_ID` → `TELEGRAM_GROUP_IDS` (renome de variável). Fallback D-14 garante transição segura | Atualizar `.env` e `.env.example` |
| Build artifacts | `helpertips.egg-info/` — não afetado por mudanças de schema ou lógica | Nenhuma |

**Blocker ativo:** O Group ID do grupo "Ambas Marcam" ainda não está disponível (listado em STATE.md Pending Todos). Precisa ser obtido via `list_groups.py` no EC2 antes de completar a configuração.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12+ | Runtime | Confirmado (pyproject.toml) | 3.12+ | — |
| Telethon | Listener multi-grupo | Confirmado | 1.42.0 | — |
| psycopg2-binary | Store/DB | Confirmado | >=2.9 | — |
| PostgreSQL 16 | Schema migration | Confirmado (EC2 deploy) | 16 | — |
| systemd | Service restart | Confirmado (EC2 Linux) | — | — |
| Group ID "Ambas Marcam" | Configurar TELEGRAM_GROUP_IDS | **AUSENTE** | — | Executar `list_groups.py` no EC2 para obter |

**Missing dependencies com blocker:**
- Group ID do grupo "Ambas Marcam" — sem esse ID, `TELEGRAM_GROUP_IDS` não pode ser configurado. Plano deve incluir task para obtê-lo antes de qualquer teste de integração.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 7.0+ |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `python3 -m pytest tests/test_parser.py tests/test_config.py tests/test_store.py -x -q` |
| Full suite command | `python3 -m pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Comportamento | Tipo de Teste | Comando Automatizado | Arquivo Existe? |
|--------|--------------|---------------|---------------------|-----------------|
| LIST-01 | Listener parseia `TELEGRAM_GROUP_IDS=id1,id2` para lista de ints | unit | `python3 -m pytest tests/test_config.py -x -q` | Parcial — novo teste necessário |
| LIST-01 | `upsert_signal` aceita `group_id` no dict e insere corretamente | integration | `python3 -m pytest tests/test_store.py -x -q` | Parcial — `_make_signal()` precisa de `group_id` |
| LIST-01 | `UNIQUE(group_id, message_id)` — dois grupos com mesmo message_id não conflitam | integration | `python3 -m pytest tests/test_store.py::test_upsert_two_groups_same_message_id -x` | NÃO — Wave 0 |
| LIST-01 | Migration idempotente — `ensure_schema()` pode ser chamado N vezes sem erro | integration | `python3 -m pytest tests/test_db.py -x -q` | Parcial — novo teste de colunas |
| LIST-02 | `_resolve_mercado_id("Over 2.5")` retorna 1 | unit | `python3 -m pytest tests/test_store.py::test_resolve_mercado_id -x` | NÃO — Wave 0 |
| LIST-02 | `_resolve_mercado_id("Ambas Marcam")` retorna 2 | unit | `python3 -m pytest tests/test_store.py::test_resolve_mercado_id -x` | NÃO — Wave 0 |
| LIST-02 | Entrada desconhecida → mercado_id=NULL sem rejeitar sinal (D-06) | unit | `python3 -m pytest tests/test_store.py::test_resolve_mercado_id_unknown -x` | NÃO — Wave 0 |

### Sampling Rate
- **Por task/commit:** `python3 -m pytest tests/test_parser.py tests/test_config.py -x -q`
- **Por wave merge:** `python3 -m pytest tests/ -x -q`
- **Phase gate:** Suite completa verde antes do `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_store.py::test_upsert_two_groups_same_message_id` — cobre LIST-01 (deduplicação por group+message)
- [ ] `tests/test_store.py::test_resolve_mercado_id` — cobre LIST-02 (Over 2.5 → 1, Ambas Marcam → 2)
- [ ] `tests/test_store.py::test_resolve_mercado_id_unknown` — cobre D-06 (entrada desconhecida → NULL)
- [ ] `tests/conftest.py::_make_signal()` — atualizar helper para incluir `group_id` como parâmetro
- [ ] `tests/test_db.py::test_migration_adds_group_id_column` — cobre D-10

---

## Sources

### Primary (HIGH confidence)
- [Telethon 1.42.0 docs — events.NewMessage chats parameter](https://docs.telethon.dev/en/stable/modules/events.html) — suporte a lista confirmado via WebSearch contra docs oficiais
- [PostgreSQL docs — ALTER TABLE DROP CONSTRAINT IF EXISTS](https://www.postgresql.org/docs/current/sql-altertable.html) — sintaxe `IF EXISTS` verificada para PG 16
- Código fonte do projeto (`listener.py`, `store.py`, `db.py`, `parser.py`) — leitura direta, HIGH confidence

### Secondary (MEDIUM confidence)
- WebSearch "Telethon events.NewMessage chats list multiple groups" — padrão `chats=[id1,id2]` e `event.chat_id` confirmados por múltiplas fontes que citam a documentação oficial

### Tertiary (LOW confidence)
- Nenhum item LOW confidence nesta fase — todas as afirmações técnicas foram verificadas contra o código existente ou docs oficiais.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — stack existente, sem novas dependências, versões verificadas no pyproject.toml
- Architecture patterns: HIGH — Telethon multi-chat nativo verificado, migration PostgreSQL verificada com `IF EXISTS`
- Pitfalls: HIGH — baseados em análise direta do código existente e comportamento conhecido do PostgreSQL SERIAL

**Research date:** 2026-04-04
**Valid until:** 2026-05-04 (stack estável; Telethon 1.x API não quebra em patches)
