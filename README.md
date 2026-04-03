# HelperTips — Futebol Virtual

Sistema que conecta ao grupo **{VIP} ExtremeTips** no Telegram, captura sinais de apostas de futebol virtual da Bet365 em tempo real, armazena no PostgreSQL e fornece um dashboard web com estatísticas completas, filtros interativos, gráficos dinâmicos e simulação de ROI. Feito para o próprio usuário que hoje acompanha e aposta manualmente.

<!-- CI badge será adicionado na Phase 5 -->

---

## Stack

| Tecnologia | Versão | Função |
|------------|--------|--------|
| Python | 3.12+ | Runtime |
| Telethon | ~=1.42 | Cliente Telegram (MTProto) — escuta o grupo como usuário |
| PostgreSQL | 16 | Banco de dados relacional |
| psycopg2-binary | >=2.9 | Driver PostgreSQL (sync) |
| Plotly Dash | >=4.1,<5 | Dashboard web interativo (pure-Python) |
| dash-bootstrap-components | >=2.0 | Layout responsivo (Bootstrap 5) |
| python-dotenv | >=1.0 | Variáveis de ambiente via `.env` |

---

## Setup Local

### Pré-requisitos

- Python 3.12+
- PostgreSQL 16 instalado e rodando localmente
- Credenciais do Telegram API (obtidas em [my.telegram.org](https://my.telegram.org))

### Passo a passo

1. **Clonar o repositório:**
   ```bash
   git clone <url-do-repositorio>
   cd helpertips
   ```

2. **Criar e ativar o ambiente virtual:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/macOS
   # venv\Scripts\activate   # Windows
   ```

3. **Instalar dependências:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Configurar variáveis de ambiente:**
   ```bash
   cp .env.example .env
   ```
   Abrir `.env` e preencher:
   - `TELEGRAM_API_ID` e `TELEGRAM_API_HASH` — obtidos em https://my.telegram.org
   - `TELEGRAM_GROUP_ID` — ID numérico do grupo {VIP} ExtremeTips
   - `DB_PASSWORD` — senha do usuário PostgreSQL
   - `DASH_DEBUG=true` — opcional, para hot-reload no desenvolvimento local

5. **Criar o banco de dados PostgreSQL:**
   ```bash
   createdb helpertips
   createuser helpertips_user
   psql -c "ALTER USER helpertips_user WITH PASSWORD 'sua_senha';"
   psql -c "GRANT ALL PRIVILEGES ON DATABASE helpertips TO helpertips_user;"
   ```

6. **Inicializar o schema do banco:**
   ```bash
   python -m helpertips.store --init-db
   ```

7. **Rodar o listener** (captura sinais do Telegram em tempo real):
   ```bash
   python -m helpertips.listener
   ```
   Na primeira execução, o Telethon solicitará o número de telefone e o código de verificação para autenticar a conta Telegram. Isso gera o arquivo `.session` — veja a seção [Segurança](#segurança--arquivo-session) abaixo.

8. **Rodar o dashboard** (em outro terminal, com o venv ativado):
   ```bash
   python -m helpertips.dashboard
   ```

9. **Acessar o dashboard:**
   ```
   http://localhost:8050
   ```

### Rodando os testes

```bash
python3 -m pytest tests/ -v
```

---

## Deploy (AWS)

O guia completo de deploy será adicionado após as Phases 6–8. A arquitetura planejada usa:

- **EC2 t3.micro** — instância de baixo custo para rodar listener + dashboard
- **systemd** — gerenciamento de processos (listener e dashboard como services)
- **nginx** — proxy reverso com HTTP Basic Auth para o dashboard
- **PostgreSQL self-hosted** na mesma EC2 (sem RDS — economia de ~R$ 75–125/mês)

**Status:** Aguardando Phase 6 (infra) e Phase 7 (deploy).

---

## Segurança — Arquivo .session

> **ATENÇÃO:** O arquivo `.session` gerado pelo Telethon é um banco SQLite que contém o **token de autenticação completo** da sua conta Telegram.
>
> **Qualquer pessoa com acesso a esse arquivo pode ler todas as mensagens da sua conta, incluindo grupos privados como o {VIP} ExtremeTips.**

### Regras obrigatórias

- **NUNCA commitar o `.session` no git** — já está no `.gitignore`, mas verifique sempre antes de um `git push`
- **Fazer backup seguro** do arquivo em local fora do repositório (será automatizado na Phase 6)
- **Se comprometido**, revogar a sessão imediatamente: Telegram → Settings → Devices → encerrar a sessão HelperTips

### Arquivos sensíveis protegidos pelo `.gitignore`

| Arquivo | Conteúdo | Por que não commitar |
|---------|----------|----------------------|
| `*.session` | Token de autenticação Telegram | Acesso total à conta |
| `*.session-journal` | Journal do SQLite de sessão | Contém fragmentos do token |
| `.env` | API keys, senha do banco | Credenciais de produção |

---

## Estrutura do Projeto

```
helpertips/
├── helpertips/
│   ├── listener.py      # Processo Telethon — captura sinais do Telegram
│   ├── dashboard.py     # Processo Dash — dashboard web
│   ├── store.py         # Camada de acesso ao PostgreSQL
│   ├── parser.py        # Parser regex dos sinais do grupo
│   └── config.py        # Configuração via variáveis de ambiente
├── tests/               # 132 testes pytest
├── .env.example         # Template de variáveis de ambiente
├── pyproject.toml       # Dependências e configuração do projeto
└── README.md            # Este arquivo
```

---

## Arquitetura

O sistema roda como **dois processos separados**:

```
Telegram → [listener.py] → PostgreSQL → [dashboard.py] → Browser
                ↑ Telethon event loop          ↑ Dash web server
```

Telethon e Dash bloqueiam seus event loops respectivos — não devem rodar no mesmo processo. O listener escreve no PostgreSQL via `asyncio.to_thread()` para não bloquear o loop assíncrono. O dashboard lê o PostgreSQL diretamente nas callbacks Dash.
