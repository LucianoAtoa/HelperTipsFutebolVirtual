# Phase 6: AWS Infrastructure - Research

**Pesquisado:** 2026-04-03
**Domínio:** AWS EC2, PostgreSQL on-instance, IAM, Billing Alerts, S3 backups, systemd
**Confiança:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** EC2 t3.micro em us-east-1 (N. Virginia). Free tier elegível por 12 meses. Custo estimado pós-free-tier: ~$12-13/mês (instância + Elastic IP + EBS 20GB gp3). Latência de ~120ms é imperceptível para 1 usuário com acesso esporádico ao dashboard.
- **D-02:** PostgreSQL 16 instalado direto na EC2 (apt install), conectando em localhost. Sem RDS — custo zero adicional. Backup diário via `pg_dump` com cron job salvando no S3 (custo ~$0.01/mês). Script de restore documentado.
- **D-03:** Arquivo `.env` copiado para o EC2 via SCP. Funciona direto com python-dotenv existente, zero dependências novas. Proteger com `chmod 600` e usuário dedicado. Não incluir `.env` em snapshots/AMIs.
- **D-04:** Arquivo `.session` armazenado no EBS root volume padrão — persiste automaticamente entre reboots. Instância tratada como permanente (pet, not cattle). Se necessário recriar, re-autenticar com SMS.

### Claude's Discretion

- Security Group: portas exatas e CIDR ranges para SSH + HTTP/HTTPS
- Elastic IP: alocação e associação
- PostgreSQL: configuração de pg_hba.conf e roles
- Schema migration: como rodar o CREATE TABLE no servidor
- Systemd units: configuração dos serviços listener e dashboard
- Budget alert: configuração exata no AWS Console ou CLI
- S3 bucket: nome, região, política de lifecycle para backups

### Deferred Ideas (OUT OF SCOPE)

Nenhum — discussão ficou dentro do escopo da fase.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Descrição | Suporte da Pesquisa |
|----|-----------|----------------------|
| AWS-01 | EC2 t3.micro provisionado com Elastic IP e Security Group restrito (SSH + HTTP/HTTPS) | Padrões de SG documentados; Elastic IP allocation/association verificados; Ubuntu 24.04 AMI via SSM |
| AWS-02 | PostgreSQL instalado e rodando na instância EC2 com schema migrado | Instalação via apt do repositório oficial; ensure_schema() já idempotente no código |
| AWS-03 | Budget alert configurado em $15/mês para evitar surpresas de custo | AWS Budgets via Console ou CLI documentado; CloudWatch Billing Alarm como alternativa |
| AWS-04 | Credenciais (Telegram API, DB) armazenadas de forma segura no servidor | .env via SCP + chmod 600 + usuário dedicado; IAM instance profile para S3 sem access keys |
| AWS-05 | Backup periódico do arquivo .session para S3 ou volume persistente | .session persiste no EBS; cron job pg_dump + .session para S3 via IAM instance profile |
</phase_requirements>

---

## Summary

Esta fase provisiona a infraestrutura AWS mínima para rodar o HelperTips 24/7. O caminho principal é: criar EC2 t3.micro Ubuntu 24.04 em us-east-1 via Console ou CLI, alocar Elastic IP, configurar Security Group, instalar PostgreSQL 16 via apt do repositório oficial PGDG, migrar schema com `ensure_schema()` já existente no código, configurar credenciais via `.env` protegido por permissões Unix, criar IAM role com política S3 restrita para o cron de backup, e ativar budget alert no AWS Budgets.

O ponto mais crítico de risco é a RAM: t3.micro tem 1 GB. PostgreSQL (shared_buffers=128MB padrão), Telethon listener (~50-100MB) e Dash (~150-200MB) juntos ficam em ~400-500MB de uso real, deixando ~500MB de headroom — apertado mas viável com swap de 1GB configurado como safety net. O segundo risco é o Elastic IP: desde fevereiro de 2024, **todos** os IPv4 públicos custam $0.005/hora — inclusive EIP associado a instância rodando. Para uma nova conta AWS (free tier), o primeiro EIP numa instância running é isento nas primeiras 750h/mês. Pós free tier, o custo real é ~$3.60/mês pelo EIP.

**Recomendação principal:** Provisionar via AWS Console (não CLI) para a instância e SG — evita dependência de AWS CLI local que não está instalado. Usar AWS CLI v2 apenas para operações automatizadas no servidor (backup S3) onde estará instalado no EC2.

## Standard Stack

### Core (lado local — máquina do desenvolvedor)

| Ferramenta | Versão | Propósito | Por Que Padrão |
|------------|--------|-----------|----------------|
| AWS CLI v2 | 2.34.22 (brew) | Provisionamento via terminal (opcional) | Automação; Console é suficiente para fase manual |
| SSH client | nativo macOS | Acesso à instância | Já disponível |
| SCP | nativo macOS | Cópia de `.env` para EC2 | Zero dependências extras |

### Core (lado servidor — EC2 Ubuntu 24.04)

| Ferramenta | Versão | Propósito | Por Que Padrão |
|------------|--------|-----------|----------------|
| Ubuntu 24.04 LTS | Noble Numbat | SO da instância | LTS com suporte até 2029; AMI oficial Canonical |
| PostgreSQL 16 | 16.x (PGDG apt) | Banco de dados | Versão fixada no projeto; apt do repositório oficial PGDG garante v16 |
| AWS CLI v2 | instalado no EC2 | Upload backup S3 | `aws s3 cp` no cron job de backup |
| boto3 | 1.42.x | Alternativa Python para S3 | Apenas se necessário; AWS CLI é suficiente para backup simples |

### Alternativas Consideradas

| Em vez de | Poderia Usar | Tradeoff |
|-----------|-------------|----------|
| Console para criar instância | AWS CLI v2 local | CLI mais rápido mas requer instalação + configuração local; Console tem UI guiada |
| IAM Instance Profile para S3 | AWS_ACCESS_KEY_ID no .env | Instance profile é mais seguro — sem chaves estáticas no servidor |
| pg_dump + aws s3 cp | pg_dump + boto3 | AWS CLI no EC2 é mais simples; boto3 só se quiser lógica Python |
| Ubuntu 24.04 LTS | Ubuntu 22.04 LTS | 22.04 tem suporte até 2027; 24.04 preferível por suporte mais longo |

### Instalação no desenvolvedor (opcional)

```bash
brew install awscli
aws configure  # AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, us-east-1, json
```

### Instalação no EC2 (obrigatório)

```bash
# PostgreSQL 16 — repositório oficial PGDG
sudo apt install -y curl ca-certificates
sudo install -d /usr/share/postgresql-common/pgdg
sudo curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc
sudo sh -c 'echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
sudo apt update
sudo apt install -y postgresql-16

# AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install
```

## Architecture Patterns

### Estrutura de arquivos no servidor

```
/home/helpertips/           # usuário dedicado (não root)
├── helpertips/             # git clone do repositório
│   ├── helpertips/
│   ├── pyproject.toml
│   └── ...
├── .env                    # chmod 600, dono: helpertips
└── helpertips_listener.session  # gerado pelo listener na 1a execução

/etc/systemd/system/
├── helpertips-listener.service
└── helpertips-dashboard.service   # Phase 8

/usr/local/bin/
└── backup-helpertips.sh    # cron script de backup

/etc/cron.d/
└── helpertips-backup
```

### Padrão 1: Security Group — Regras mínimas

**O que é:** Firewall stateful na camada da instância EC2.

**Regras recomendadas:**

| Tipo | Protocolo | Porta | Origem | Razão |
|------|-----------|-------|--------|-------|
| SSH | TCP | 22 | IP do desenvolvedor /32 | Restrito ao IP pessoal — bots escaneiam SSH 24/7 |
| HTTP | TCP | 8050 | 0.0.0.0/0, ::/0 | Dashboard Dash (Phase 8 adiciona nginx na 80) |
| (futuro) HTTP | TCP | 80 | 0.0.0.0/0, ::/0 | Nginx reverse proxy (Phase 8) |

**Importante:** SSH deve usar `/32` (IP exato), não `/0`. IP pessoal pode ser dinâmico — documentar onde atualizar se mudar.

### Padrão 2: IAM Instance Profile para S3

**O que é:** Role IAM anexada à instância — credentials automáticas sem access keys estáticos.

**Quando usar:** Qualquer operação `aws s3 cp` ou boto3 rodando no EC2.

**Política mínima (princípio de menor privilégio):**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::helpertips-backups-ACCOUNT_ID",
        "arn:aws:s3:::helpertips-backups-ACCOUNT_ID/*"
      ]
    }
  ]
}
```

**Como funciona:** `aws s3 cp` no EC2 usa automaticamente as credenciais temporárias do instance metadata (169.254.169.254). Nenhuma variável de ambiente adicional é necessária no `.env`.

### Padrão 3: pg_dump + S3 via cron

**O que é:** Cron job diário que faz dump do banco e copia para S3 junto com o .session.

```bash
#!/bin/bash
# /usr/local/bin/backup-helpertips.sh
set -e

BUCKET="helpertips-backups-$(aws sts get-caller-identity --query Account --output text)"
DATE=$(date +%Y-%m-%d)
BACKUP_DIR="/tmp/helpertips-backup-$$"

mkdir -p "$BACKUP_DIR"

# Dump PostgreSQL
PGPASSWORD="$DB_PASSWORD" pg_dump \
  -h localhost -U helpertips_user -d helpertips \
  -Fc -f "$BACKUP_DIR/helpertips-$DATE.dump"

# Cópia do .session
cp /home/helpertips/helpertips_listener.session "$BACKUP_DIR/helpertips_listener-$DATE.session" 2>/dev/null || true

# Upload para S3
aws s3 cp "$BACKUP_DIR/" "s3://$BUCKET/backups/$DATE/" --recursive

# Limpeza
rm -rf "$BACKUP_DIR"
```

**Crontab entry (`/etc/cron.d/helpertips-backup`):**

```
0 3 * * * helpertips /usr/local/bin/backup-helpertips.sh >> /var/log/helpertips-backup.log 2>&1
```

### Padrão 4: Systemd service para listener Python asyncio

**O que é:** Unit file para manter o listener Telethon rodando como daemon.

```ini
# /etc/systemd/system/helpertips-listener.service
[Unit]
Description=HelperTips Telegram Listener
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=helpertips
WorkingDirectory=/home/helpertips/helpertips
EnvironmentFile=/home/helpertips/.env
ExecStart=/home/helpertips/.venv/bin/python -m helpertips.listener
Restart=on-failure
RestartSec=60
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

**Nota crítica:** `EnvironmentFile` carrega o `.env` — variáveis ficam disponíveis para o processo sem precisar do python-dotenv (mas python-dotenv com `load_dotenv()` também funciona pois lê o arquivo diretamente).

### Padrão 5: Swap de 1GB no t3.micro

**O que é:** Arquivo de swap para evitar OOM killer em picos de uso.

```bash
# Criar swap de 1GB (EBS é suficientemente rápido para swap ocasional)
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
# Persistir no fstab
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Anti-Patterns a Evitar

- **Security Group SSH aberto para 0.0.0.0/0:** Bots escaneiam e tentam brute force imediatamente. Usar `/32` do IP pessoal.
- **AWS access keys no .env do servidor:** Vazar o .env compromete conta AWS inteira. Usar IAM instance profile.
- **Elastic IP não associado:** Cobra $0.005/hora mesmo sem usar. Associar imediatamente após alocar.
- **PostgreSQL com listen_addresses='*' sem senha:** Por padrão pg_hba.conf usa peer auth localmente — só mudar o necessário, não abrir para toda a rede.
- **Root para rodar aplicações:** Criar usuário `helpertips` dedicado; instância com root comprometido = jogo acabou.

## Don't Hand-Roll

| Problema | Não Construir | Usar Ao Invés | Por Que |
|----------|--------------|---------------|---------|
| Schema migration | Script SQL custom com controle de versão | `ensure_schema()` já no `db.py` | Já idempotente com `CREATE TABLE IF NOT EXISTS`; funciona sem migração tool |
| Credential rotation | Lógica de rotação custom | IAM Instance Profile + temp credentials | AWS rotaciona automaticamente a cada hora |
| Monitoramento de custo | Script de billing custom | AWS Budgets (built-in) | Interface nativa, sem infraestrutura adicional |
| Descoberta de AMI | Hardcode de AMI ID | SSM Parameter `/aws/service/canonical/ubuntu/server/24.04/.../ami-id` | AMI IDs mudam por região/atualização; SSM sempre retorna o mais recente |

**Insight:** Para uma instância single-tenant pessoal, complexidade zero é a meta. Cron + aws s3 cp é mais confiável do que qualquer solução de backup elaborada.

## Common Pitfalls

### Pitfall 1: Elastic IP cobra mesmo com instância running (pós-free-tier)

**O que dá errado:** Desenvolvedor assume que EIP em instância running é sempre gratuito.
**Por que acontece:** Desde fev/2024, AWS cobra $0.005/hora por **qualquer** IPv4 público — inclusive EIP associado a instância em execução. Free tier inclui 750h/mês de IPv4 público, então durante o free tier está coberto. Pós-free-tier: ~$3.60/mês apenas pelo EIP.
**Como evitar:** Incluir no orçamento (~$3.60/mês). O budget alert de $15 cobre isso com margem.
**Sinais de alerta:** Custo mensal acima do esperado no primeiro mês pós-free-tier.

### Pitfall 2: SSH bloqueado por IP dinâmico do desenvolvedor

**O que dá errado:** Security Group restringe SSH ao IP `/32` do desenvolvedor, mas ISP muda o IP.
**Por que acontece:** `/32` é correto para segurança mas IPs residenciais são dinâmicos.
**Como evitar:** Documentar o procedimento de atualização do SG (Console > Security Groups > Inbound Rules > Edit). Opcional: criar regra adicional para IP de fallback (celular 4G). **Não** abrir para 0.0.0.0/0.
**Sinais de alerta:** `Connection refused` ou timeout ao tentar SSH após troca de rede.

### Pitfall 3: .session não gerado pelo systemd service

**O que dá errado:** Listener iniciado como systemd service falha na primeira vez porque `.session` não existe e precisa de TTY interativo para código SMS.
**Por que acontece:** Telethon's `TelegramClient.start()` pede input() quando não há sessão — systemd não tem TTY.
**Como evitar:** Primeira execução do listener DEVE ser feita manualmente via SSH interativo (`python -m helpertips.listener`) com o terminal conectado. Só depois de autenticado iniciar o systemd service. Esta etapa é DEP-05 (Phase 7), não Phase 6.
**Sinais de alerta:** Service fica em estado `failed` com `EOFError` ou `RuntimeError: There is no current event loop` no journal.

### Pitfall 4: pg_hba.conf com método `peer` quebra conexão do Python

**O que dá errado:** psycopg2 com `DB_USER=helpertips_user` falha com `FATAL: Peer authentication failed`.
**Por que acontece:** Default do Ubuntu é `peer` para conexões locais, que verifica se o usuário Unix bate com o role PostgreSQL. Se o processo roda como `helpertips` (Unix) mas conecta como `helpertips_user` (PostgreSQL), peer auth falha.
**Como evitar:** Alterar `/etc/postgresql/16/main/pg_hba.conf` para `scram-sha-256` (md5) para o user da aplicação, ou criar role PostgreSQL com mesmo nome do usuário Unix. O padrão recomendado é usar `scram-sha-256` com senha.
**Sinais de alerta:** `psycopg2.OperationalError: FATAL: Peer authentication failed for user "helpertips_user"`.

### Pitfall 5: RAM insuficiente no t3.micro mata processos

**O que dá errado:** OOM killer do Linux mata o processo do listener ou dashboard.
**Por que acontece:** t3.micro tem 1 GB de RAM. PostgreSQL shared_buffers (128MB padrão) + Dash (~200MB) + Telethon (~80MB) + OS (~200MB) = ~600MB, deixando ~400MB. Picos de query no dashboard podem causar swap thrashing.
**Como evitar:** Configurar 1GB de swap (arquivo no EBS). Reduzir `shared_buffers` do PostgreSQL para 64MB para base de dados pequena. Monitorar com `free -h` e `top` no primeiro dia.
**Sinais de alerta:** `dmesg | grep -i "out of memory"` ou serviços caindo sem log de erro explícito.

### Pitfall 6: Budget alert em região errada (us-east-1 obrigatório)

**O que dá errado:** Budget alert criado em região diferente não recebe dados de billing.
**Por que acontece:** AWS Billing é um serviço global mas sua API está apenas em `us-east-1`. Budget alerts no Console devem ser criados estando na região us-east-1 (ou via CloudWatch Billing que é sempre global).
**Como evitar:** Para criar via AWS Console: verificar que o seletor de região mostra "N. Virginia" (us-east-1) antes de criar o Budget. Via CLI: sempre usar `--region us-east-1`.
**Sinais de alerta:** Budget criado mas sem dados de utilização exibidos.

## Code Examples

Padrões verificados por pesquisa e código existente do projeto:

### AMI Ubuntu 24.04 — método robusto (sem hardcode)

```bash
# Busca o AMI ID atual via SSM (sempre mais recente, funciona em qualquer região)
aws ssm get-parameter \
  --name /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id \
  --query "Parameter.Value" \
  --output text \
  --region us-east-1
```

### Schema migration via SSH

```bash
# Na máquina local — copia o repositório (ou usa git clone no EC2)
# No EC2, ativar o venv e rodar ensure_schema()
ssh -i ~/.ssh/helpertips.pem ubuntu@ELASTIC_IP
cd /home/helpertips/helpertips
source .venv/bin/activate
python3 -c "
from helpertips.db import get_connection, ensure_schema
conn = get_connection()
ensure_schema(conn)
conn.close()
print('Schema migrado com sucesso')
"
```

### PostgreSQL — configurar role da aplicação

```sql
-- Rodar como postgres (sudo -u postgres psql)
CREATE USER helpertips_user WITH PASSWORD 'senha_segura_aqui';
CREATE DATABASE helpertips OWNER helpertips_user;
GRANT ALL PRIVILEGES ON DATABASE helpertips TO helpertips_user;
```

### pg_hba.conf — trocar peer por scram-sha-256

```
# /etc/postgresql/16/main/pg_hba.conf
# Adicionar ANTES das linhas locais existentes:
local   helpertips      helpertips_user                 scram-sha-256
```

```bash
sudo systemctl restart postgresql
```

### Budget Alert via AWS CLI

```bash
# Requer aws configure com credenciais e região us-east-1
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws budgets create-budget \
  --account-id $ACCOUNT_ID \
  --budget '{
    "BudgetName": "HelperTips-Monthly",
    "BudgetLimit": {"Amount": "15", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }' \
  --notifications-with-subscribers '[{
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80,
      "ThresholdType": "PERCENTAGE"
    },
    "Subscribers": [{
      "SubscriptionType": "EMAIL",
      "Address": "seu-email@example.com"
    }]
  }]'
```

### Systemd — habilitar e verificar serviço

```bash
sudo systemctl daemon-reload
sudo systemctl enable helpertips-listener
sudo systemctl start helpertips-listener
sudo systemctl status helpertips-listener
sudo journalctl -u helpertips-listener -f  # logs em tempo real
```

### .env — cópia segura para EC2

```bash
# Na máquina local
scp -i ~/.ssh/helpertips.pem .env helpertips@ELASTIC_IP:/home/helpertips/.env
# No EC2
chmod 600 /home/helpertips/.env
chown helpertips:helpertips /home/helpertips/.env
```

## State of the Art

| Abordagem Antiga | Abordagem Atual | Quando Mudou | Impacto |
|-----------------|-----------------|--------------|---------|
| Elastic IP gratuito para instância running | $0.005/hr por qualquer IPv4 público | Fev/2024 | +~$3.60/mês pós-free-tier |
| pg_hba.conf md5 padrão | scram-sha-256 padrão (PG 16) | PostgreSQL 14+ | Alterar método de auth no pg_hba.conf para scram-sha-256 |
| t2.micro free tier | t3.micro free tier em muitas regiões | 2019+ | t3.micro tem performance credit model mais eficiente |

**Deprecated/Obsoleto:**
- `md5` no pg_hba.conf: PostgreSQL 16 suporta `scram-sha-256` — mais seguro, usar ao invés de md5.
- AWS CLI v1 (via pip): Usar AWS CLI v2 (binary oficial ou brew).

## Open Questions

1. **IP pessoal dinâmico para Security Group**
   - O que sabemos: SSH deve ser restrito ao IP do desenvolvedor via /32
   - O que não está claro: Se o IP residencial do usuário é dinâmico (muda frequentemente)
   - Recomendação: Documentar comando de atualização do SG no SUMMARY da fase; considerar permitir também IP de um segundo dispositivo como fallback

2. **Key pair já existente vs. criar novo**
   - O que sabemos: Há `.pem` files em `~/.ssh/` (asaas-rsistema.pem, aws-asaas.pem) — outros projetos AWS
   - O que não está claro: Se o usuário quer criar um key pair dedicado para helpertips ou reusar existente
   - Recomendação: Criar key pair novo `helpertips-key` específico para o projeto — princípio de isolamento

3. **Conta AWS já configurada?**
   - O que sabemos: Não há `~/.aws/` directory na máquina local; AWS CLI não está instalado
   - O que não está claro: Se a conta AWS do usuário já existe ou precisa ser criada
   - Recomendação: Plano 06-01 deve incluir verificação de pré-requisitos (conta AWS ativa, billing habilitado, IAM user com permissões)

## Environment Availability

| Dependência | Requerida Por | Disponível | Versão | Fallback |
|-------------|--------------|-----------|--------|---------|
| AWS CLI v2 (local) | Provisionamento via terminal | Nao | — | Usar AWS Console (GUI) para toda a fase |
| boto3 (local) | Scripts locais S3 | Nao | — | Não necessário — backup roda no EC2 |
| psql client (local) | Verificação remota do banco | Nao | — | SSH para EC2 e rodar psql lá |
| SSH client (local) | Acesso EC2 | Sim | nativo macOS | — |
| SCP (local) | Cópia do .env | Sim | nativo macOS | — |
| Homebrew (local) | Instalar AWS CLI | Sim | 5.1.3 | Pkg oficial da AWS em docs.aws.amazon.com |
| Conta AWS | Toda a fase | Desconhecido | — | Criar conta gratuita aws.amazon.com |

**Dependências ausentes sem fallback:**
- Nenhuma — AWS Console cobre tudo o que AWS CLI faria nesta fase

**Dependências ausentes com fallback:**
- AWS CLI v2 local: AWS Console é suficiente para provisionamento manual (1x). Instalar via `brew install awscli` se preferir CLI.
- psql local: SSH para EC2 e executar `psql` diretamente no servidor.

## Validation Architecture

### Test Framework

| Propriedade | Valor |
|-------------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Comando rápido | `pytest tests/ -x -q` |
| Suite completa | `pytest tests/ -v` |

### Phase Requirements -> Test Map

| Req ID | Comportamento | Tipo de Teste | Comando Automatizado | Arquivo Existe? |
|--------|--------------|---------------|---------------------|----------------|
| AWS-01 | EC2 acessível via SSH com Elastic IP | smoke manual | SSH interativo | N/A (infra) |
| AWS-01 | Security Group bloqueia portas não autorizadas | manual (nmap) | `nmap -p 22,80,443,8050 ELASTIC_IP` | N/A (infra) |
| AWS-02 | PostgreSQL responde em localhost | smoke manual | `psql -U helpertips_user -d helpertips -c "SELECT 1"` | N/A (infra) |
| AWS-02 | Schema migrado — tabela sinais existe | smoke manual | `psql -c "SELECT COUNT(*) FROM signals"` | N/A (infra) |
| AWS-02 | ensure_schema() idempotente | unit (existente) | `pytest tests/test_db.py -x` | Sim (`tests/test_db.py`) |
| AWS-03 | Budget alert ativo no Console | manual verificação | Verificar AWS Budgets Console | N/A (config AWS) |
| AWS-04 | .env com chmod 600 no servidor | smoke manual | `ssh EC2 "stat -c '%a' ~/.env"` | N/A (config servidor) |
| AWS-04 | Variáveis carregam corretamente | unit (existente) | `pytest tests/test_config.py -x` | Sim (`tests/test_config.py`) |
| AWS-05 | .session persiste após reboot | smoke manual | Reiniciar instância, verificar arquivo | N/A (infra) |
| AWS-05 | Cron de backup gera arquivo no S3 | smoke manual | Executar backup script manualmente, checar S3 | N/A (infra) |

### Sampling Rate

- **Por commit de tarefa:** `pytest tests/ -x -q` (testes unitários existentes)
- **Por merge de wave:** `pytest tests/ -v`
- **Gate da fase:** Testes de smoke manuais listados acima + `pytest tests/ -v` verde

### Wave 0 Gaps

Nenhum — infraestrutura de testes existente cobre os requisitos de código (AWS-02, AWS-04). Testes de infra (AWS-01, AWS-03, AWS-05) são verificações manuais por natureza — não requerem novos arquivos de teste.

## Project Constraints (from CLAUDE.md)

| Diretiva | Impacto na Fase |
|----------|----------------|
| Stack: Python 3.12+, Telethon 1.42, PostgreSQL 16, psycopg2-binary | EC2 deve ter Python 3.12+ (Ubuntu 24.04 vem com Python 3.12.x); PostgreSQL 16 via PGDG apt |
| .session deve ficar no .gitignore | Já configurado; no EC2, .session fica em /home/helpertips/ fora do repo |
| Dash + Telethon processos separados | 2 systemd units distintas (helpertips-listener.service + helpertips-dashboard.service) |
| Não incluir .env em snapshots/AMIs | Ao criar AMI de backup, excluir /home/helpertips/.env |
| Comunicação em pt-BR | Todos os artefatos, comentários e scripts em pt-BR |
| GSD workflow — não editar fora de /gsd:execute-phase | Aplicável na execução |

## Sources

### Primárias (confiança HIGH)

- [AWS EC2 Security Group Rules Reference](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-rules-reference.html) — CIDR /32 para SSH, 0.0.0.0/0 para HTTP
- [AWS Elastic IP Addresses](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html) — pricing, allocation, association
- [Ubuntu AMI Finder (Canonical)](https://cloud-images.ubuntu.com/locator/ec2/) — AMI IDs oficiais Ubuntu
- [Ubuntu AWS SSM Parameter](https://documentation.ubuntu.com/aws/aws-how-to/instances/launch-ubuntu-ec2-instance/) — `/aws/service/canonical/ubuntu/server/24.04/.../ami-id`
- [AWS Budgets — Creating a cost budget](https://docs.aws.amazon.com/cost-management/latest/userguide/create-cost-budget.html) — Budget alert configuration
- [IAM Roles for EC2](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2.html) — Instance profile para S3 sem access keys
- `helpertips/db.py` — ensure_schema() idempotente confirmado via leitura do código
- `helpertips/listener.py` linha 94 — nome da sessão: `helpertips_listener`

### Secundárias (confiança MEDIUM)

- [PostgreSQL on AWS EC2 Ubuntu 22.04](https://medium.com/@akhilsharma_10270/the-right-way-to-install-postgresql-on-aws-ec2-ubuntu-22-04-c77e72bfb8ef) — instalação via PGDG
- [AWS Public IPv4 Charge announcement](https://aws.amazon.com/blogs/aws/new-aws-public-ipv4-address-charge-public-ip-insights/) — $0.005/hr desde fev/2024
- [systemd Python service pattern](https://lucacorbucci.medium.com/how-to-run-a-python-code-as-a-service-using-systemctl-4f6ad1835bf2) — EnvironmentFile, Restart=on-failure
- [pg_dump to S3 cron pattern](https://dev.to/finny_collins/postgresql-backup-to-s3-how-to-store-your-database-backups-in-the-cloud-b8f) — backup script pattern

## Metadata

**Breakdown de confiança:**
- Provisioning EC2/SG/EIP: HIGH — documentação oficial AWS verificada
- PostgreSQL 16 install: HIGH — PGDG é a fonte oficial; padrão bem estabelecido
- IAM Instance Profile: HIGH — documentação oficial AWS; padrão best practice
- systemd units: MEDIUM — padrão estabelecido mas não testado com este stack específico
- RAM baseline t3.micro: MEDIUM — estimativa baseada em componentes individuais; medir no primeiro dia
- Budget alert: HIGH — AWS Budgets é serviço estável com documentação clara

**Data da pesquisa:** 2026-04-03
**Válido até:** 2026-05-03 (30 dias; AWS pricing estável, Ubuntu LTS estável)
