# Phase 6: AWS Infrastructure - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Provisionar infraestrutura AWS para rodar o HelperTips (listener Telethon + dashboard Dash + PostgreSQL) 24/7 com custo mínimo, billing controlado e credenciais seguras.

</domain>

<decisions>
## Implementation Decisions

### Instância e Região
- **D-01:** EC2 t3.micro em us-east-1 (N. Virginia). Free tier elegível por 12 meses. Custo estimado pós-free-tier: ~$12-13/mês (instância + Elastic IP + EBS 20GB gp3). Latência de ~120ms é imperceptível para 1 usuário com acesso esporádico ao dashboard.

### PostgreSQL
- **D-02:** PostgreSQL 16 instalado direto na EC2 (apt install), conectando em localhost. Sem RDS — custo zero adicional. Backup diário via `pg_dump` com cron job salvando no S3 (custo ~$0.01/mês). Script de restore documentado.

### Gestão de Credenciais
- **D-03:** Arquivo `.env` copiado para o EC2 via SCP. Funciona direto com python-dotenv existente, zero dependências novas. Proteger com `chmod 600` e usuário dedicado. Não incluir `.env` em snapshots/AMIs.

### Sessão Telethon
- **D-04:** Arquivo `.session` armazenado no EBS root volume padrão — persiste automaticamente entre reboots. Instância tratada como permanente (pet, not cattle). Se necessário recriar, re-autenticar com SMS.

### Claude's Discretion
- Security Group: portas exatas e CIDR ranges para SSH + HTTP/HTTPS
- Elastic IP: alocação e associação
- PostgreSQL: configuração de pg_hba.conf e roles
- Schema migration: como rodar o CREATE TABLE no servidor
- Systemd units: configuração dos serviços listener e dashboard
- Budget alert: configuração exata no AWS Console ou CLI
- S3 bucket: nome, região, política de lifecycle para backups

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above and REQUIREMENTS.md (AWS-01..05).

### Código relevante
- `helpertips/db.py` — conexão DB via os.environ (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
- `helpertips/dashboard.py:1001` — bind em 0.0.0.0:8050, debug controlado por DASH_DEBUG
- `helpertips/listener.py` — Telethon listener, gera .session
- `.env.example` — template com 12 variáveis (Telegram, DB, DASH_DEBUG, AWS comentadas)
- `.gitignore` — já bloqueia *.session, .env, __pycache__

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- python-dotenv já carrega .env automaticamente — funciona identicamente no EC2
- db.py usa os.environ direto — basta ter as variáveis no .env do servidor
- dashboard.py bind em 0.0.0.0 — já acessível externamente com security group correto

### Established Patterns
- Listener e dashboard são processos separados — precisam de 2 systemd units
- DB connection string montada de variáveis individuais (DB_HOST, DB_PORT, etc.)

### Integration Points
- .env no EC2 é o único ponto de configuração (mesmo padrão do dev local)
- .session gerado na primeira execução do listener — requer autenticação interativa com SMS

</code_context>

<specifics>
## Specific Ideas

- Budget alert configurado para $15/mês com notificação por email
- pg_dump diário para S3 pode incluir o .session no mesmo cron como backup extra
- Primeiro run do listener no EC2 requer SSH interativo para inserir código SMS do Telegram

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-aws-infrastructure*
*Context gathered: 2026-04-04*
