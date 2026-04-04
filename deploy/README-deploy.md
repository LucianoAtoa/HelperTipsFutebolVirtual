# Guia de Provisionamento AWS — HelperTips

Guia passo a passo para provisionar a infraestrutura AWS e executar o bootstrap inicial do servidor.

**Decisoes de arquitetura:**
- Regiao: us-east-1 (N. Virginia) — free tier elegivel, D-01
- Instancia: t3.micro — 1 vCPU, 1GB RAM, free tier por 12 meses
- SO: Ubuntu 24.04 LTS (Noble Numbat) — suporte ate 2029
- EBS: 20GB gp3 — suficiente para logs, banco e codigo
- Elastic IP: IP publico fixo para SSH e acesso ao dashboard

---

## Pre-requisitos

- Conta AWS ativa com billing habilitado (https://aws.amazon.com)
- Acesso ao AWS Console (https://console.aws.amazon.com)
- Terminal com suporte a SSH e SCP (macOS: nativo)

---

## Passo 1 — Criar Key Pair

1. No AWS Console, acesse **EC2 > Network & Security > Key Pairs**
2. Clique em **Create key pair**
3. Configure:
   - Nome: `helpertips-key`
   - Tipo: RSA
   - Formato: `.pem`
4. Clique em **Create key pair** — o arquivo `helpertips-key.pem` sera baixado automaticamente
5. Mova o arquivo para `~/.ssh/` e proteja:
   ```bash
   mv ~/Downloads/helpertips-key.pem ~/.ssh/helpertips-key.pem
   chmod 400 ~/.ssh/helpertips-key.pem
   ```

---

## Passo 2 — Criar Security Group

1. No AWS Console, acesse **EC2 > Network & Security > Security Groups**
2. Clique em **Create security group**
3. Configure:
   - Nome: `helpertips-sg`
   - Descricao: `HelperTips — SSH restrito + Dashboard`
   - VPC: default

4. **Inbound rules** — adicionar as seguintes regras:

   | Tipo | Protocolo | Porta | Origem | Descricao |
   |------|-----------|-------|--------|-----------|
   | SSH | TCP | 22 | IP pessoal /32 | SSH restrito ao seu IP |
   | TCP customizado | TCP | 8050 | 0.0.0.0/0, ::/0 | Dashboard Dash |
   | HTTP | TCP | 80 | 0.0.0.0/0, ::/0 | Nginx (Phase 8) |

   **Para descobrir seu IP pessoal:**
   ```bash
   curl https://checkip.amazonaws.com
   ```
   Use o IP retornado no formato `X.X.X.X/32` na regra de SSH.

   > **Atencao:** SSH com `/32` e mais seguro que `/0` — bots escaneiam a porta 22 continuamente.
   > Se seu ISP mudar seu IP (comum em redes residenciais), atualize a regra:
   > EC2 > Security Groups > helpertips-sg > Inbound Rules > Edit

5. **Outbound rules:** Manter padrao (All traffic, 0.0.0.0/0)
6. Clique em **Create security group**

---

## Passo 3 — Lancar Instancia EC2

1. No AWS Console, acesse **EC2 > Instances > Launch instances**
2. Configure:
   - Nome: `helpertips`
   - **AMI:** Clique em "Browse more AMIs" > busque `Ubuntu` > selecione **Ubuntu Server 24.04 LTS** (HVM, SSD Volume Type) — versao amd64
   - **Tipo de instancia:** `t3.micro` (elegivel para free tier)
   - **Key pair:** `helpertips-key`
   - **Security group:** `helpertips-sg` (selecione o que acabou de criar)
3. Em **Configure storage:**
   - Volume raiz: `20` GB, tipo `gp3`
4. Clique em **Launch instance**
5. Aguarde o status da instancia mudar para `Running` (~1-2 minutos)

---

## Passo 4 — Alocar e Associar Elastic IP

1. No AWS Console, acesse **EC2 > Network & Security > Elastic IPs**
2. Clique em **Allocate Elastic IP address**
   - Network border group: `us-east-1` (padrao)
   - Clique em **Allocate**
3. Selecione o Elastic IP alocado
4. Clique em **Actions > Associate Elastic IP address**
   - Resource type: Instance
   - Instance: selecione `helpertips`
   - Clique em **Associate**
5. **Anote o Elastic IP** — voce usara em todos os comandos SSH a seguir

> **Nota de custo:** A partir de fevereiro/2024, AWS cobra $0.005/hora por qualquer IPv4 publico,
> inclusive Elastic IP associado a instancia em execucao. No free tier (12 meses), as primeiras
> 750h/mês estao isentas. Pos-free-tier: ~$3.60/mes pelo EIP.

---

## Passo 5 — Primeiro SSH e Bootstrap

1. Conecte-se a instancia via SSH (substitua `ELASTIC_IP` pelo IP anotado):
   ```bash
   ssh -i ~/.ssh/helpertips-key.pem ubuntu@ELASTIC_IP
   ```

2. Se for a primeira conexao, confirme a autenticidade do host digitando `yes`

3. Clone o repositorio na instancia:
   ```bash
   git clone https://github.com/SEU_USUARIO/helpertips.git
   cd helpertips
   ```

4. Execute o script de bootstrap como root:
   ```bash
   sudo bash deploy/01-provision-ec2.sh
   ```

5. O script realiza automaticamente:
   - Cria swap de 1GB (`/swapfile`) — persiste nos reboots via `/etc/fstab`
   - Cria usuario dedicado `helpertips` (sem root)
   - Instala pacotes base: `python3.12-venv`, `git`, `curl`, `ca-certificates`, `unzip`
   - Cria diretorio de logs `/var/log/helpertips`

---

## Passo 6 — Verificacao

Apos o bootstrap, verifique no EC2 via SSH:

```bash
# Verificar swap de 1GB
free -h
# Saida esperada: linha Swap com total de 1.0G

# Verificar usuario helpertips
id helpertips
# Saida esperada: uid=NNNN(helpertips) gid=NNNN(helpertips) groups=NNNN(helpertips)

# Verificar pacotes instalados
python3 --version
# Saida esperada: Python 3.12.x

git --version
# Saida esperada: git version 2.x.x
```

---

## Proximos Passos

Apos concluir este guia, prossiga com:

1. **deploy/02-setup-postgres.sh** — Instalar e configurar PostgreSQL 16, criar role e banco
2. **deploy/03-setup-app.sh** — Configurar virtualenv, instalar dependencias Python, migrar schema
3. **deploy/04-setup-systemd.sh** — Criar e habilitar servicos systemd (listener + dashboard)

---

## Solucao de Problemas

**Problema:** `Permission denied (publickey)` ao tentar SSH
**Solucao:** Verifique se o arquivo `.pem` tem permissao `400`:
```bash
chmod 400 ~/.ssh/helpertips-key.pem
```

**Problema:** `Connection timed out` ao tentar SSH
**Solucao:** Verifique se o Security Group tem a regra SSH para o seu IP atual.
Descubra seu IP com `curl https://checkip.amazonaws.com` e atualize a regra no Console.

**Problema:** Script de bootstrap falha com erro de permissao
**Solucao:** Execute com `sudo`:
```bash
sudo bash deploy/01-provision-ec2.sh
```

**Problema:** Elastic IP cobra mesmo com instancia running
**Solucao:** Comportamento esperado pos-free-tier ($0.005/hora). O budget alert de $15/mes
(configurado no Phase 6 Plan 3) cobrira esse custo com margem.
