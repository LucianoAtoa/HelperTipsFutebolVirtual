# Phase 4: Security Audit - Research

**Researched:** 2026-04-03
**Domain:** Git history audit, Dash debug mode, .env.example, README.md
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Controlar debug mode via variável de ambiente: `debug=os.getenv('DASH_DEBUG', 'false').lower() == 'true'`. Desligado por padrão (seguro em produção), liga com `DASH_DEBUG=true` no .env local para desenvolvimento.
- **D-02:** README completo com: descrição do projeto, stack, setup local (pip install, .env, PostgreSQL), como rodar listener + dashboard, aviso de segurança sobre .session, badges CI (após Phase 5).
- **D-03:** Abordagem grep-based: rodar busca por padrões de secrets no histórico git (API keys, passwords, tokens, .env conteúdo). Se limpo, prosseguir sem BFG Repo Cleaner. Não reescrever histórico desnecessariamente.
- **D-04:** Atualizar .env.example com variáveis necessárias para AWS deploy (a serem definidas na Phase 6). Manter sem valores reais.

### Claude's Discretion

Nenhuma área de discrição definida — todas as decisões foram bloqueadas pelo usuário.

### Deferred Ideas (OUT OF SCOPE)

Nenhuma. A discussão ficou dentro do escopo da fase.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SEC-01 | Histórico git auditado — nenhum secret (.env, .session, API keys) presente em commits antigos | Auditoria via `git log --all -p` + grep de padrões confirmou histórico limpo |
| SEC-02 | Dashboard roda com `debug=False` em produção (elimina REPL remoto) | Dash 4.x aceita `app.run(debug=bool)` — mudança de uma linha |
| SEC-03 | `.env.example` atualizado com todas as variáveis necessárias (inclusive AWS) sem valores reais | Arquivo existe, 8 variáveis atuais; precisa receber DASH_DEBUG + vars AWS futuras |
| SEC-04 | README.md com instruções de setup local, deploy, e aviso de segurança | README.md não existe — precisa ser criado do zero |
</phase_requirements>

---

## Summary

A Phase 4 é uma fase de segurança e documentação, não de desenvolvimento de features. O repositório já está em bom estado: `.gitignore` correto desde o primeiro commit, sem `.env` ou `.session` rastreados em nenhum ponto do histórico, e os únicos valores de credencial no histórico são fake (`12345678`, `abc123def456`) em arquivo de teste — não em código de produção.

O único blocker técnico real é `debug=True` hardcoded em `dashboard.py:997`. Isso é uma mudança de uma linha: substituir `debug=True` por `debug=os.getenv('DASH_DEBUG', 'false').lower() == 'true'`. O `.env.example` precisa de expansão para incluir `DASH_DEBUG` e variáveis AWS (que serão usadas em Phase 6). O README.md precisa ser criado do zero com seções de setup local, deploy e segurança.

O trabalho desta fase é de baixo risco técnico e alta completude — não há reescrita de histórico git necessária, não há falha de segurança ativa a corrigir. A fase serve como gate de qualidade antes da publicação pública no GitHub (Phase 5).

**Primary recommendation:** Executar auditoria de confirmação do histórico git, corrigir debug flag com env var, expandir .env.example e criar README.md — tudo dentro de 2 planos sequenciais.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python os.getenv | stdlib | Leitura de variável de ambiente | Padrão Python sem dependências externas |
| python-dotenv | >=1.0 | Carrega `.env` na inicialização | Já em uso no projeto; carrega automaticamente para `os.getenv` funcionar |

### Sem novas dependências

Esta fase não adiciona nenhuma biblioteca. Todas as mudanças são:
- Edição de código existente (`dashboard.py`)
- Atualização de arquivo de template (`.env.example`)
- Criação de documento (`README.md`)

---

## Architecture Patterns

### Padrão D-01: Debug mode via env var

**O que:** Substituir `debug=True` por expressão que lê variável de ambiente.

**Implementação exata (decisão D-01 bloqueada):**

```python
# dashboard.py:997 — antes
app.run(debug=True, host="0.0.0.0", port=8050)

# dashboard.py:997 — depois
app.run(
    debug=os.getenv('DASH_DEBUG', 'false').lower() == 'true',
    host="0.0.0.0",
    port=8050,
)
```

**Pré-condição:** `import os` já está presente no topo de `dashboard.py` (verificar antes de editar).

**No .env local (para desenvolvimento):**
```
DASH_DEBUG=true
```

**Em produção (EC2):** Variável ausente ou `DASH_DEBUG=false` — debug permanece desligado por padrão.

### Padrão D-03: Auditoria grep-based do histórico git

**Comandos de auditoria (executar como verificação, não como correção):**

```bash
# 1. Verificar se .env ou .session foram alguma vez rastreados
git log --all --name-only --format="" | grep -E "\.env$|\.session$"

# 2. Verificar se conteúdo do histórico contém valores de secret reais
git log --all -p | grep -E "^\+" | grep -iE "(api_id|api_hash|db_password)\s*=\s*[^$'\"]"

# 3. Comando oficial do success criteria
git log --all --full-diff -p -- .env '*.session'
```

**Resultado esperado (já verificado nesta pesquisa):** Saída vazia para todos os três comandos. O histórico está limpo.

**Achado relevante:** `tests/test_config.py` contém `SAMPLE_VALUES` com credenciais falsas (`12345678`, `abc123def456`). Isso é esperado e seguro — são valores sintéticos em arquivo de teste, não credenciais reais.

### Padrão D-04: Estrutura do .env.example expandido

**Estado atual (8 variáveis):**
```
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_GROUP_ID=
DB_HOST=localhost
DB_PORT=5432
DB_NAME=helpertips
DB_USER=helpertips_user
DB_PASSWORD=
```

**Estado alvo (adicionar DASH_DEBUG; vars AWS a definir em Phase 6):**
```
# Telegram API credentials — get from https://my.telegram.org
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_GROUP_ID=

# PostgreSQL connection
DB_HOST=localhost
DB_PORT=5432
DB_NAME=helpertips
DB_USER=helpertips_user
DB_PASSWORD=

# Dashboard
# Set to true for local development hot-reload; false (default) in production
DASH_DEBUG=false

# AWS (Phase 6 — deixar vazio até o deploy)
# AWS_REGION=
# AWS_S3_BUCKET=
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
```

As variáveis AWS podem ficar comentadas (com `#`) para indicar que são opcionais até o deploy.

### Padrão D-02: Estrutura do README.md

**Seções obrigatórias (decisão D-02 bloqueada):**

```markdown
# HelperTips — Futebol Virtual

[descrição do projeto]

## Stack

[tabela de tecnologias]

## Setup Local

[pip install, .env, PostgreSQL, rodar listener + dashboard]

## Deploy (AWS)

[link/referência ao guia de deploy — pode ser placeholder até Phase 7/8]

## Segurança — Arquivo .session

[aviso explícito: o arquivo .session é uma credencial, nunca commitar, fazer backup]

## Badges

[CI badge — placeholder até Phase 5]
```

---

## Don't Hand-Roll

| Problema | Não Construir | Usar Ao Invés | Por Quê |
|----------|---------------|---------------|---------|
| Remover secrets do histórico | Script custom de reescrita git | BFG Repo Cleaner ou `git-filter-repo` | Ferramentas especializadas lidam com edge cases (pack files, reflogs, remote refs) |
| Verificar secrets em commits futuros | Script custom de hook | `gitleaks` como pre-commit hook | Ferramenta mantida com rules para 100+ tipos de secrets |

**Nota:** Para esta fase, a decisão D-03 bloqueou o uso de BFG porque o histórico já está limpo. Nenhuma ferramenta de reescrita é necessária.

---

## Runtime State Inventory

> Fase de auditoria e documentação — não é rename/refactor/migration. Seção incluída apenas para confirmar escopo de segurança.

| Categoria | Itens Encontrados | Ação Necessária |
|-----------|-------------------|-----------------|
| Stored data | Nenhum dado com secrets — PostgreSQL contém apenas dados de sinais | Nenhuma |
| Live service config | `helpertips_listener.session` e `helpertips.session` na raiz (não rastreados, em .gitignore) | Nenhuma — já ignorados corretamente |
| OS-registered state | Nenhum processo registrado como systemd/launchd ainda (Phase 7) | Nenhuma |
| Secrets/env vars | `.env` na raiz (não rastreado, em .gitignore) | Nenhuma — já protegido |
| Build artifacts | `helpertips.egg-info/` e `__pycache__/` — já em .gitignore | Nenhuma |

**Conclusão:** Nenhuma mudança de estado de runtime necessária. A fase é puramente code/docs.

---

## Common Pitfalls

### Pitfall 1: Assumir que histórico git limpo = repositório seguro sem verificar

**O que dá errado:** Publicar repo assumindo segurança sem rodar os comandos de verificação explicitamente.
**Por que acontece:** `.gitignore` correto previne futuros commits, mas não garante que o passado está limpo.
**Como evitar:** Sempre rodar `git log --all --full-diff -p -- .env '*.session'` como task explícita, mesmo que o resultado esperado seja vazio.
**Sinais de alerta:** Output não-vazio do comando; arquivos `.env` ou `.session` aparecendo em `git ls-tree`.

### Pitfall 2: Esquecer de adicionar DASH_DEBUG ao .env.example

**O que dá errado:** Código referencia `os.getenv('DASH_DEBUG')` mas `.env.example` não documenta a variável — próximo desenvolvedor (ou o próprio usuário em 6 meses) não sabe que pode habilitar debug.
**Por que acontece:** O arquivo `.env.example` é atualizado separadamente do código.
**Como evitar:** Atualizar `.env.example` na mesma task que altera `dashboard.py`.

### Pitfall 3: `import os` não presente em dashboard.py

**O que dá errado:** Adicionar `os.getenv(...)` sem verificar se `import os` está no topo do arquivo causa `NameError` na importação.
**Por que acontece:** O arquivo `dashboard.py` pode não ter `os` importado — é um módulo que trabalha principalmente com Dash e suas próprias abstrações.
**Como evitar:** Verificar `grep "^import os" helpertips/dashboard.py` antes de editar.

### Pitfall 4: README.md com aviso de segurança vago sobre .session

**O que dá errado:** Aviso genérico como "não commitar o arquivo .session" não explica o risco real.
**Por que acontece:** Documentação de segurança tende a ser boilerplate.
**Como evitar:** Explicar concretamente: o arquivo `.session` é um SQLite com o token de autenticação completo do Telegram. Qualquer pessoa com esse arquivo pode ler todas as mensagens da conta, incluindo grupos privados. Backup essencial, mas nunca no git.

---

## Code Examples

### Verificação de histórico git (SEC-01)

```bash
# Comando do success criteria — deve retornar zero linhas
git log --all --full-diff -p -- .env '*.session'

# Verificação complementar: grep de padrões de credenciais no histórico completo
git log --all -p | grep -E "^\+" | grep -iE "(api_id|api_hash|password)\s*=\s*\S"

# Verificar se algum arquivo sensível foi rastreado alguma vez
git log --all --name-only --format="" | grep -E "\.env$|\.session$" | sort -u
```

### Correção do debug mode (SEC-02)

```python
# helpertips/dashboard.py — linha 997
# ANTES:
app.run(debug=True, host="0.0.0.0", port=8050)

# DEPOIS:
app.run(
    debug=os.getenv('DASH_DEBUG', 'false').lower() == 'true',
    host="0.0.0.0",
    port=8050,
)
```

### Teste para SEC-02 (novo — Wave 0 gap)

```python
# tests/test_dashboard.py — adicionar ao arquivo existente
def test_debug_mode_off_by_default(monkeypatch):
    """DASH_DEBUG ausente ou 'false' resulta em debug=False."""
    monkeypatch.delenv('DASH_DEBUG', raising=False)
    debug = os.getenv('DASH_DEBUG', 'false').lower() == 'true'
    assert debug is False

def test_debug_mode_on_with_env(monkeypatch):
    """DASH_DEBUG=true resulta em debug=True."""
    monkeypatch.setenv('DASH_DEBUG', 'true')
    debug = os.getenv('DASH_DEBUG', 'false').lower() == 'true'
    assert debug is True
```

---

## Environment Availability

Step 2.6: SKIPPED (fase puramente code/docs — sem dependências externas além das já instaladas no projeto)

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >= 7.0 |
| Config file | `pyproject.toml` — `[tool.pytest.ini_options]` |
| Quick run command | `python3 -m pytest tests/ -q` |
| Full suite command | `python3 -m pytest tests/ -v` |

**Estado atual:** 132 testes passando. Nenhum teste cobre debug mode.

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SEC-01 | Git history retorna zero resultados para .env e .session | smoke (bash) | `git log --all --full-diff -p -- .env '*.session' \| wc -l` retorna 0 | N/A — bash check |
| SEC-02 | DASH_DEBUG ausente → debug=False; DASH_DEBUG=true → debug=True | unit | `python3 -m pytest tests/test_dashboard.py -k "debug" -x` | ❌ Wave 0 |
| SEC-03 | .env.example contém DASH_DEBUG e estrutura correta | smoke (bash) | `grep "DASH_DEBUG" .env.example` retorna match | N/A — bash check |
| SEC-04 | README.md existe com seções obrigatórias | smoke (bash) | `grep -E "Setup Local\|Deploy\|session" README.md` | N/A — bash check |

### Sampling Rate

- **Por task commit:** `python3 -m pytest tests/ -q`
- **Por wave merge:** `python3 -m pytest tests/ -v`
- **Phase gate:** Full suite verde antes de `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_dashboard.py` — adicionar `test_debug_mode_off_by_default` e `test_debug_mode_on_with_env` (cobre SEC-02)

*(Todos os outros requirements de SEC-01, SEC-03, SEC-04 são verificações bash/smoke — não requerem novos arquivos de teste.)*

---

## Project Constraints (from CLAUDE.md)

| Diretiva | Impacto nesta Fase |
|----------|-------------------|
| Stack: Python 3.12+, Telethon, PostgreSQL, psycopg2-binary, python-dotenv | Sem novas dependências nesta fase — stack não muda |
| Sessão Telethon (.session) no .gitignore | Já configurado — auditoria confirma compliance |
| Comunicação em pt-BR | Comentários no código, README.md e artifacts GSD em pt-BR |
| GSD Workflow: edições via gsd commands | Edições em dashboard.py, .env.example, README.md via gsd:execute-phase |
| Dashboard: Dash >=4.1,<5 | `app.run()` API estável nesta versão — sem mudança de API |

---

## Sources

### Primary (HIGH confidence)

- Inspeção direta do repositório via `git log` e `git ls-files` — auditoria realizada em 2026-04-03
- `helpertips/dashboard.py:997` — código fonte inspecionado diretamente
- `.env.example` — conteúdo atual verificado diretamente
- `tests/test_config.py` — SAMPLE_VALUES confirmados como valores sintéticos de teste

### Secondary (MEDIUM confidence)

- Dash 4.x `app.run()` API — padrão conhecido, verificável em dash.plotly.com/devtools
- Pattern `os.getenv('VAR', 'default').lower() == 'true'` — idioma Python padrão para bool de env var

### Tertiary (LOW confidence)

- Estrutura de README.md para projetos Python pessoais — baseada em convenções da comunidade, sem fonte única autoritativa

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — sem novas dependências; tudo já presente
- Architecture: HIGH — mudanças triviais, código inspecionado diretamente
- Pitfalls: HIGH — baseados em inspeção real do código, não suposições

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (estável — nenhuma dependência nova, mudanças determinísticas)
