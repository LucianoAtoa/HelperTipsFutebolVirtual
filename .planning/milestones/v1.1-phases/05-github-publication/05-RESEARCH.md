# Phase 5: GitHub Publication — Research

**Researched:** 2026-04-03
**Domain:** GitHub repository setup, GitHub Actions CI para projeto Python
**Confidence:** HIGH

## Summary

A fase 5 tem dois objetivos claros e independentes: (1) publicar o repositório existente no GitHub com `.gitignore` correto, e (2) criar um workflow de GitHub Actions que rode lint e testes automaticamente a cada push, com badge de status visível no README.

O repositório `LucianoAtoa/HelperTipsFutebolVirtual` já existe no GitHub mas está **privado** e aparentemente vazio (defaultBranchRef sem nome, pushed at 2026-04-03T22:44:24Z sem branch padrão definida). O repositório local tem 134 testes passando com `pytest 9.0.2` e Python 3.12. Os testes de banco de dados (`test_db.py`) usam `pytest.skip()` automaticamente quando PostgreSQL não está disponível — ou seja, **o CI pode rodar sem banco de dados** e os testes de parser, config, dashboard e queries ainda passarão.

Para lint, nenhum dos linters comuns (flake8, ruff, black) está instalado localmente. O `pyproject.toml` não tem seção `[tool.ruff]` ou `[tool.flake8]`. **Ruff** é a escolha moderna e recomendada para Python em 2025-2026: mais rápido, substituição drop-in de flake8+isort, configurado via `pyproject.toml`, e é o padrão emergente da comunidade.

**Recomendação primária:** Tornar o repo público, adicionar o remote ao git local, fazer push de `main`, criar `.github/workflows/ci.yml` com ruff lint + pytest, adicionar badge ao README.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GH-01 | Repositório publicado no GitHub com .gitignore correto (*.session, .env, __pycache__, *.pyc) | `.gitignore` existente já cobre esses patterns; repo existe mas está privado/vazio — precisa tornar público e push |
| GH-02 | GitHub Actions workflow roda lint + testes automaticamente em cada push | CI com ruff + pytest; testes DB skipam automaticamente sem PostgreSQL; 134 testes passing localmente |
</phase_requirements>

---

## Project Constraints (from CLAUDE.md)

- **Stack**: Python 3.12+, Telethon ~=1.42, PostgreSQL 16, psycopg2-binary, python-dotenv
- **Idioma**: Toda comunicação em pt-BR (commits com prefixos convencionais em inglês são OK)
- **GSD Workflow**: Usar `/gsd:execute-phase` para trabalho de fase planejado
- **Segurança**: `.session` e `.env` NUNCA no git — já cobertos pelo `.gitignore` atual

---

## Standard Stack

### Core — CI/CD

| Ferramenta | Versão | Propósito | Por que padrão |
|------------|--------|-----------|----------------|
| GitHub Actions | N/A (serviço) | Runner de CI | Nativo do GitHub, zero config de infra, free tier suficiente para projeto pessoal |
| ruff | `>=0.9` (atual: 0.11.x) | Lint Python | Drop-in replacement de flake8+isort+pycodestyle; ~100x mais rápido; configurado no `pyproject.toml`; padrão 2025 |
| pytest | `>=7.0` (instalado: 9.0.2) | Testes | Já em uso no projeto, 134 testes passando |
| actions/checkout | `v4` | Checkout repo no runner | Versão atual estável do action oficial |
| actions/setup-python | `v5` | Setup Python no runner | Versão atual estável do action oficial |

### .gitignore — Estado Atual vs. Requerido

O `.gitignore` atual JÁ cobre todos os patterns de GH-01:

| Pattern GH-01 | Presente no .gitignore? | Linha |
|---------------|------------------------|-------|
| `*.session` | Sim | `*.session` (linha 2) |
| `.env` | Sim | `.env` (linha 5) |
| `__pycache__` | Sim | `__pycache__/` (linha 8) |
| `*.pyc` | Sim | `*.py[cod]` (linha 9, cobre .pyc, .pyo, .pyd) |

**Conclusão:** `.gitignore` não precisa de modificação para satisfazer GH-01.

### Situação do Repositório GitHub

| Aspecto | Estado Atual | Ação Necessária |
|---------|-------------|-----------------|
| Repo existe | Sim (`LucianoAtoa/HelperTipsFutebolVirtual`) | — |
| Visibilidade | **Privado** | Tornar público (GH-01 diz "repositório público") |
| Branch padrão | Indefinida (repo vazio) | Push de `main` local |
| Remote no git local | Não configurado | `git remote add origin` |
| CI workflow | Não existe | Criar `.github/workflows/ci.yml` |

---

## Architecture Patterns

### Estrutura de Arquivos a Criar

```
.github/
└── workflows/
    └── ci.yml       # Workflow lint + pytest
README.md            # Badge de CI já tem placeholder: "<!-- CI badge será adicionado na Phase 5 -->"
pyproject.toml       # Adicionar [tool.ruff] config
```

### Pattern: GitHub Actions Workflow para Python

**Trigger:** push para qualquer branch + pull_request
**Runner:** `ubuntu-latest`
**Python:** `3.12` (match do projeto)

```yaml
# Source: https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python
name: CI

on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install ruff pytest
          pip install -e .

      - name: Lint with ruff
        run: ruff check .

      - name: Run tests
        run: pytest --tb=short -q
```

**Nota sobre testes de DB:** `test_db.py` faz `pytest.skip()` automaticamente quando PostgreSQL não está disponível. No runner GitHub Actions não há PostgreSQL — os 6 testes de DB serão skipped. Os demais 128+ testes passam sem banco. **Não é necessário configurar PostgreSQL no CI para o projeto funcionar.**

### Pattern: Badge de Status no README

```markdown
[![CI](https://github.com/LucianoAtoa/HelperTipsFutebolVirtual/actions/workflows/ci.yml/badge.svg)](https://github.com/LucianoAtoa/HelperTipsFutebolVirtual/actions/workflows/ci.yml)
```

O README já tem um placeholder comentado para o badge na linha 5:
```markdown
<!-- CI badge será adicionado na Phase 5 -->
```

### Pattern: Configuração Ruff no pyproject.toml

```toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I"]
# E/W: pycodestyle, F: pyflakes, I: isort
ignore = []
```

### Anti-Patterns a Evitar

- **Não use flake8 + isort separados:** Ruff substitui ambos com uma única ferramenta mais rápida
- **Não configure PostgreSQL no CI como serviço:** Testes de DB já têm skip automático; adicionar um service PostgreSQL complica o workflow sem benefício real para este projeto
- **Não use `actions/checkout@v3` ou `setup-python@v4`:** Versões desatualizadas; v4/v5 são as atuais estáveis
- **Não faça push force de `main` para o repo remoto** sem verificar que o repo está vazio
- **Não coloque `TELEGRAM_API_ID`, `TELEGRAM_API_HASH` como secrets de Actions:** Não são necessários para rodar os testes (parser/config/dashboard não fazem conexão real ao Telegram)

---

## Don't Hand-Roll

| Problema | Não construir | Usar em vez | Por que |
|----------|---------------|-------------|---------|
| Lint Python | Script de verificação manual | ruff | Cobre 50+ regras, integra com CI, configurável |
| Badge de status | HTML customizado | URL padrão do GitHub Actions badge | GitHub gera automaticamente a partir do workflow |
| Cache de pip no CI | Script de cache manual | `cache: 'pip'` no `actions/setup-python@v5` | Action já tem suporte nativo; reduz tempo de CI de ~40s para ~10s em runs subsequentes |

---

## Common Pitfalls

### Pitfall 1: Repo remoto privado x público

**O que dá errado:** GH-01 requer repositório **público**. O repo atual é **privado**. Se o push for feito sem mudar a visibilidade, o requisito não é satisfeito.

**Por que acontece:** O repo foi criado sem especificar visibilidade (default privado no GitHub).

**Como evitar:** Mudar visibilidade via `gh repo edit --visibility public` ANTES ou DURANTE o push. Confirmar com usuário antes de tornar público — contém histórico de commits com mensagens em pt-BR e código de sistema de apostas.

**Warning sign:** `gh repo view` mostra `visibility: PRIVATE`.

---

### Pitfall 2: Remote não configurado localmente

**O que dá errado:** O git local não tem remote `origin` apontando para o GitHub. `git push` vai falhar.

**Por que acontece:** O repo GitHub foi criado separadamente sem clonar ou vincular ao repo local.

**Como evitar:** Verificar com `git remote -v` antes. Se vazio, executar:
```bash
git remote add origin https://github.com/LucianoAtoa/HelperTipsFutebolVirtual.git
git push -u origin main
```

**Warning sign:** `git remote -v` retorna vazio (confirmado — sem remotes atualmente).

---

### Pitfall 3: Ruff falha em código existente na primeira execução

**O que dá errado:** O código do projeto nunca foi lintado. Ruff pode encontrar violações (imports não ordenados, linhas longas, variáveis não usadas) e o CI falha imediatamente no primeiro push.

**Por que acontece:** Linting está sendo adicionado retroativamente ao código existente.

**Como evitar:** Rodar `ruff check .` localmente ANTES de fazer push do workflow. Se houver erros: usar `ruff check --fix .` para auto-correção dos fixáveis, e ajustar manualmente os restantes. Fazer commit das correções junto com o workflow.

**Warning sign:** `ruff check .` com saída não-vazia localmente.

---

### Pitfall 4: Badge URL incorreta

**O que dá errado:** O badge no README aponta para um arquivo de workflow com nome diferente ou branch errada.

**Por que acontece:** A URL do badge inclui o nome exato do arquivo `.yml`.

**Como evitar:** O formato correto é:
```
https://github.com/{owner}/{repo}/actions/workflows/{filename}.yml/badge.svg
```
Se o arquivo for `ci.yml`, a URL deve conter `ci.yml`. Não usar o nome do job.

---

### Pitfall 5: `pip install -e .` sem `psycopg2-binary` pré-instalado falha em ubuntu-latest

**O que dá errado:** `psycopg2-binary` pode falhar a instalação em algumas versões do ubuntu-latest se as bibliotecas do sistema não estiverem disponíveis.

**Por que acontece:** O pacote `-binary` normalmente inclui as libs, mas versões antigas podem precisar de `libpq-dev`.

**Como evitar:** Usar `psycopg2-binary` (não `psycopg2`). Em 2025-2026, o ubuntu-latest (ubuntu-24.04) tem suporte nativo. Verificar que `requirements.txt` ou `pyproject.toml` especifica `psycopg2-binary`, não `psycopg2`. **Já confirmado:** `pyproject.toml` usa `psycopg2-binary>=2.9`.

---

## Code Examples

### ci.yml completo recomendado

```yaml
# Source: https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python
name: CI

on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - name: Instalar dependências
        run: |
          python -m pip install --upgrade pip
          pip install ruff pytest
          pip install -e .

      - name: Lint com ruff
        run: ruff check .

      - name: Testes com pytest
        run: pytest --tb=short -q
```

### pyproject.toml — adição para ruff

```toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I"]
ignore = []
```

### Badge para README (substituir placeholder)

```markdown
[![CI](https://github.com/LucianoAtoa/HelperTipsFutebolVirtual/actions/workflows/ci.yml/badge.svg)](https://github.com/LucianoAtoa/HelperTipsFutebolVirtual/actions/workflows/ci.yml)
```

### Comandos para publicar o repositório

```bash
# 1. Tornar repo público
gh repo edit LucianoAtoa/HelperTipsFutebolVirtual --visibility public

# 2. Adicionar remote (se não existe)
git remote add origin https://github.com/LucianoAtoa/HelperTipsFutebolVirtual.git

# 3. Push
git push -u origin main
```

---

## Environment Availability

| Dependência | Necessária para | Disponível | Versão | Fallback |
|-------------|----------------|-----------|--------|----------|
| gh CLI | Criar/configurar repo, mudar visibilidade | Sim | 2.89.0 | Fazer via GitHub UI |
| git | Push para remote | Sim | (sistema) | — |
| ruff | Lint local antes do push | Não | — | Instalar com `pip install ruff` |
| pytest | Testes locais | Sim (via python -m) | 9.0.2 | — |
| Python 3.12 | Runtime | Sim (3.13.6 no macOS, 3.12 no CI) | 3.13.6 local | Python 3.12 especificado no CI |

**Dependências sem fallback:** nenhuma — todas têm solução ou não são críticas.

**Dependências com fallback:**
- `ruff`: não instalado localmente, mas `pip install ruff` resolve antes de rodar localmente.

---

## Validation Architecture

### Framework de Testes

| Propriedade | Valor |
|-------------|-------|
| Framework | pytest 9.0.2 |
| Config | `pyproject.toml` → `[tool.pytest.ini_options]` |
| Comando rápido | `python -m pytest tests/ -q` |
| Suite completa | `python -m pytest tests/ -v` |

### Mapeamento de Requisitos para Testes

| Req ID | Comportamento | Tipo de Teste | Comando Automatizado | Arquivo Existe? |
|--------|--------------|---------------|----------------------|-----------------|
| GH-01 | `.gitignore` bloqueia `*.session`, `.env`, `__pycache__`, `*.pyc` | Smoke / verificação manual | `git check-ignore -v helpertips.session .env __pycache__ dummy.pyc` | N/A — verificação de arquivo |
| GH-01 | Repo público no GitHub | Verificação manual | `gh repo view --json visibility` | N/A |
| GH-02 | CI roda ao fazer push | Verificação via GitHub Actions log | `gh run list --limit 3` | ❌ Wave 0: criar `.github/workflows/ci.yml` |
| GH-02 | Badge visível no README | Verificação visual | Abrir URL do badge no browser | N/A — verificação visual |

### Taxa de Amostragem

- **Por commit de tarefa:** `python -m pytest tests/ -q` (0.53s localmente)
- **Por merge de wave:** Suite completa + `ruff check .`
- **Gate da fase:** Push para main com CI verde no GitHub Actions

### Gaps para Wave 0

- [ ] `.github/workflows/ci.yml` — cobre GH-02
- [ ] `[tool.ruff]` em `pyproject.toml` — configuração de lint para o CI
- [ ] Correções de lint: rodar `ruff check --fix .` antes do primeiro push

---

## Open Questions

1. **Tornar repo público: confirmar com o usuário**
   - O que sabemos: GH-01 especifica "repositório público", repo atual é privado
   - O que não está claro: o usuário pode preferir manter privado por questões de privacidade (sistema de apostas pessoal)
   - Recomendação: O planner deve incluir uma nota para o executor confirmar com o usuário antes de executar `gh repo edit --visibility public`. Se o usuário quiser manter privado, GH-01 precisa ser revisado.

2. **Violações de lint no código existente**
   - O que sabemos: ruff não está instalado localmente, código nunca foi lintado
   - O que não está claro: quantas violações existem e de que tipo
   - Recomendação: Tarefa 05-01 deve incluir passo de rodar `ruff check .` e `ruff check --fix .` ANTES de criar o workflow. Caso contrário, o primeiro push vai fazer o CI falhar.

---

## Sources

### Primary (HIGH confidence)

- [GitHub Actions — Building and testing Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python) — workflow pattern e actions oficiais
- [actions/setup-python@v5](https://github.com/actions/setup-python) — versão atual do action
- [actions/checkout@v4](https://github.com/actions/checkout) — versão atual do action
- Análise direta do repositório local (`git remote -v`, `cat .gitignore`, `pytest --collect-only`, `gh repo view`)

### Secondary (MEDIUM confidence)

- [Ruff documentation](https://docs.astral.sh/ruff/) — configuração via pyproject.toml, seletores E/F/W/I
- [GitHub — Adding a workflow status badge](https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/adding-a-workflow-status-badge) — formato da URL do badge

### Tertiary (LOW confidence)

- Nenhuma fonte de baixa confiança utilizada.

---

## Metadata

**Confidence breakdown:**
- Stack (ruff + Actions): HIGH — baseado em documentação oficial e análise direta do projeto
- Situação do repo: HIGH — verificado via `gh repo view` e `git remote -v`
- Testes: HIGH — 134 testes passando confirmados localmente, skip de DB verificado no código
- Pitfalls: HIGH — baseados em análise direta do estado atual do repo e código

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (GitHub Actions API é estável; ruff evolui mas a config básica é estável)
