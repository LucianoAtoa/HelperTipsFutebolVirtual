# Phase 7: Listener Deployment - Research

**Researched:** 2026-04-04
**Domain:** systemd service deployment, Telethon session management, Python daemon logging
**Confidence:** HIGH

## Summary

Esta fase converte o listener Telethon (já funcional localmente) em um serviço systemd 24/7 na EC2. O código em `listener.py` não precisa de mudanças estruturais: `client.start()` já lida com autenticação interativa via stdin, que funciona perfeitamente em sessões SSH. O único ajuste de código necessário é a lógica de logging para detectar TTY e usar RotatingFileHandler em produção em vez do RichHandler.

O fluxo de deploy tem dois momentos distintos: (1) primeira execução interativa via SSH para gerar o arquivo `.session`, configurar TELEGRAM_GROUP_ID no `.env`, e verificar que o listener processa mensagens reais; (2) configuração do systemd service que usará a sessão já autenticada para restarts automáticos. Após `client.start()` encontrar um arquivo `.session` válido, nenhuma interação adicional é necessária em restarts.

O systemd exige atenção em dois pontos críticos: `StartLimitBurst`/`StartLimitIntervalSec` devem ficar na seção `[Unit]` (não `[Service]`) — erro comum que faz os parâmetros serem ignorados silenciosamente; e `EnvironmentFile` com permissões 600 é a abordagem correta para passar o `.env` sem expor secrets no log de journald.

**Recomendação principal:** Script de deploy único `deploy/05-setup-listener.sh` que cria o unit file, configura logrotate, cria o script de notificação de falha e habilita o serviço — deixando a autenticação interativa como passo manual documentado separado.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01 — Fluxo de Autenticação:**
SSH interativo + `client.start()` padrão. Rodar listener uma vez via SSH, digitar phone + SMS code, selecionar grupo via `selecionar_grupo`. Zero mudança de código. Depois configurar TELEGRAM_GROUP_ID no .env com o ID selecionado para evitar prompt interativo em restarts automáticos.

**D-02 — Gestão de Logs:**
RotatingFileHandler em `/var/log/helpertips/listener.log`. Logs em arquivo independente do systemd. Detectar `sys.stdout.isatty()` para manter RichHandler no desenvolvimento local e usar logging padrão em produção. Configurar logrotate para rotação automática.

**D-03 — Comportamento em Falha:**
`Restart=on-failure` com `RestartSec=60`, `StartLimitBurst=5`, `StartLimitIntervalSec=300` (5 falhas em 5 min). `OnFailure=` dispara script que envia alerta via Telegram Bot API (curl simples). Se cair repetidamente, para e notifica — perder sinais sem saber contradiz o objetivo do sistema.

**D-04 — Localização do .session:**
Arquivo `.session` em `/home/helpertips/` (home do user dedicado). Servidor single-purpose, permissões já corretas para user helpertips. Backup S3 diário já cobre esse path (script `backup-helpertips.sh` referencia `/home/helpertips/helpertips_listener.session`). WorkingDirectory do systemd aponta para `/home/helpertips/`.

### Claude's Discretion
- Configuração exata do unit file systemd (ExecStart, Environment, etc.)
- Script de notificação de falha (formato da mensagem Telegram)
- Configuração do logrotate (tamanho, retenção)
- Ajuste do listener.py para detectar TTY e trocar handler de logging
- Ordem exata dos passos no script de deploy

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEP-05 | Primeira autenticação Telethon feita interativamente via SSH no EC2 | Telethon `client.start()` lê stdin; funciona em SSH sem mudança de código. Verificado via código existente em `listener.py:95`. |
| DEP-01 | Listener rodando como systemd service com `Restart=on-failure` e `RestartSec=60` | Padrão systemd documentado. `StartLimitBurst`/`StartLimitIntervalSec` devem ficar na seção `[Unit]`. Verificado via docs oficiais systemd. |
</phase_requirements>

---

## Standard Stack

### Core (sem mudanças)
| Library | Version | Purpose | Por que padrão |
|---------|---------|---------|----------------|
| Telethon | ~=1.42 | MTProto listener | Já instalado, sessão SQLite persiste entre restarts |
| systemd | sistema | Process manager | Já presente no Ubuntu 24.04 LTS; restart, logging, dependency management nativos |
| python-dotenv | >=1.0 | Carrega `.env` | Já usado; `EnvironmentFile` no systemd é alternativa sem código Python |
| Python logging stdlib | 3.12 | RotatingFileHandler | Built-in; sem dependência extra para produção |

### Ferramentas de Sistema (EC2)
| Ferramenta | Versão | Purpose | Quando usar |
|------------|--------|---------|-------------|
| logrotate | sistema | Rotação de logs em arquivo | Presente por padrão no Ubuntu; gerencia `/var/log/helpertips/listener.log` |
| curl | sistema | HTTP requests simples | Script de notificação de falha via Telegram Bot API |
| journalctl | sistema | Acesso aos logs do systemd | Debug de falhas de inicialização do serviço |

### Instalação (sem novas dependências)
```bash
# Nenhuma dependência nova — tudo já está em pyproject.toml
# O único pacote extra é o projeto instalado em modo editável no venv da EC2
pip install -e .
```

---

## Architecture Patterns

### Estrutura de arquivos de deploy
```
deploy/
├── 01-provision-ec2.sh          # Existente — cria user, swap, /var/log/helpertips/
├── 02-setup-postgres.sh         # Existente — PostgreSQL
├── 03-setup-budget-alert.sh     # Existente
├── 04-setup-backup.sh           # Existente — backup S3 + cron
└── 05-setup-listener.sh         # NOVO — systemd unit, logrotate, notify script

/etc/systemd/system/
└── helpertips-listener.service  # NOVO — criado pelo script

/etc/logrotate.d/
└── helpertips                   # NOVO — criado pelo script

/usr/local/bin/
└── helpertips-notify-failure.sh # NOVO — script de alerta Telegram

/home/helpertips/
├── .env                         # Existente — variáveis, incluindo TELEGRAM_GROUP_ID
├── helpertips/                  # Código clonado via git
│   └── ...
└── helpertips_listener.session  # GERADO na primeira execução interativa
```

### Pattern 1: Systemd Unit File com EnvironmentFile
**O que é:** Serviço systemd que carrega `.env` via `EnvironmentFile` e roda o listener como user dedicado.
**Quando usar:** Sempre que um daemon precisar de secrets e reinicialização automática.

**Ponto crítico verificado:** `StartLimitBurst` e `StartLimitIntervalSec` DEVEM estar na seção `[Unit]`, não `[Service]`. Colocados em `[Service]` são silenciosamente ignorados.

```ini
# /etc/systemd/system/helpertips-listener.service
[Unit]
Description=HelperTips Telegram Listener
After=network.target postgresql.service
StartLimitBurst=5
StartLimitIntervalSec=300
OnFailure=helpertips-notify-failure@%n.service

[Service]
Type=simple
User=helpertips
Group=helpertips
WorkingDirectory=/home/helpertips
EnvironmentFile=/home/helpertips/.env
ExecStart=/home/helpertips/venv/bin/python -m helpertips.listener
Restart=on-failure
RestartSec=60

# Segurança básica
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### Pattern 2: Serviço de Notificação OnFailure com Template
**O que é:** Um segundo unit file de template instanciado pelo systemd quando `helpertips-listener` falha.
**Quando usar:** Quando `OnFailure=` precisa passar o nome do serviço falho para o script de notificação.

```ini
# /etc/systemd/system/helpertips-notify-failure@.service
[Unit]
Description=HelperTips failure notifier for %i

[Service]
Type=oneshot
User=helpertips
EnvironmentFile=/home/helpertips/.env
ExecStart=/usr/local/bin/helpertips-notify-failure.sh %i
```

```bash
#!/bin/bash
# /usr/local/bin/helpertips-notify-failure.sh
SERVICE_NAME="${1:-helpertips-listener}"
BOT_TOKEN="${TELEGRAM_NOTIFY_TOKEN}"
CHAT_ID="${TELEGRAM_NOTIFY_CHAT_ID}"

if [[ -z "$BOT_TOKEN" || -z "$CHAT_ID" ]]; then
    echo "TELEGRAM_NOTIFY_TOKEN ou TELEGRAM_NOTIFY_CHAT_ID nao configurado" >&2
    exit 0  # Falha silenciosa — nao queremos loop de notificacao
fi

MESSAGE="⚠️ HelperTips: servico ${SERVICE_NAME} falhou. Verificar EC2."

curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d "chat_id=${CHAT_ID}" \
    -d "text=${MESSAGE}" \
    > /dev/null
```

### Pattern 3: Detecção de TTY para Logging Condicional
**O que é:** `listener.py` detecta se está rodando em terminal interativo e ajusta o handler de logging.
**Quando usar:** Qualquer script Python que precisa rodar tanto em desenvolvimento (terminal rico) quanto em produção (daemon sem TTY).

```python
# Adicionar ao início de listener.py, substituindo a configuração de logging atual
import sys
import logging
from logging.handlers import RotatingFileHandler

def configure_logging():
    """Configura logging: RichHandler em TTY, RotatingFileHandler em daemon."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if sys.stdout.isatty():
        # Desenvolvimento local — manter RichHandler atual
        from rich.logging import RichHandler
        handler = RichHandler(rich_tracebacks=True, show_path=False)
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[handler],
        )
    else:
        # Produção / systemd daemon — arquivo com rotação
        log_path = "/var/log/helpertips/listener.log"
        handler = RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB por arquivo
            backupCount=7,               # 7 arquivos = ~70MB máximo
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        root_logger.addHandler(handler)
```

### Pattern 4: Configuração logrotate
**O que é:** Arquivo em `/etc/logrotate.d/helpertips` que complementa o RotatingFileHandler.
**Nota:** RotatingFileHandler já rotaciona por tamanho. O logrotate adiciona rotação por tempo e compressão.

```
# /etc/logrotate.d/helpertips
/var/log/helpertips/listener.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    missingok
    create 0640 helpertips helpertips
}
```

### Anti-Patterns a Evitar

- **Não usar `Restart=always` sem `StartLimitIntervalSec`:** Pode criar loop infinito de restarts que consome CPU. `Restart=on-failure` é mais conservador.
- **Não colocar `StartLimitBurst` na seção `[Service]`:** É ignorado silenciosamente; deve ficar em `[Unit]`.
- **Não usar caminhos relativos no `ExecStart`:** systemd exige caminho absoluto — usar `/home/helpertips/venv/bin/python`, não `python`.
- **Não rodar como root:** User `helpertips` já criado no bootstrap; sem necessidade de root para o listener.
- **Não iniciar o serviço sem o `.session` existente:** O systemd service não deve ser habilitado antes da primeira autenticação interativa. `client.start()` tentaria autenticação, mas systemd não tem TTY.

---

## Don't Hand-Roll

| Problema | Não construir | Usar | Por quê |
|----------|---------------|------|---------|
| Restart automático em crash | Loop Python com try/except | systemd `Restart=on-failure` | systemd monitoriza PID, sobrevive a falhas do processo Python, reinicia na ordem correta |
| Rotação de logs | Script cron + mv + gzip | RotatingFileHandler + logrotate | RotatingFileHandler garante rotação durante execução; logrotate cuida de compressão e limpeza |
| Notificação de falha | Cronjob verificando `ps aux` | systemd `OnFailure=` | Callback imediato na falha real do serviço, não polling |
| Carregamento de variáveis | Leitura manual de arquivo | systemd `EnvironmentFile=` | Gerenciado pelo sistema; variáveis nunca aparecem em logs de audit |
| Inicialização na ordem correta | Sleep no script | systemd `After=network.target postgresql.service` | Dependência declarativa, determinística |

---

## Pitfalls Comuns

### Pitfall 1: `client.start()` em daemon sem TTY causa timeout
**O que vai errado:** Se `TELEGRAM_GROUP_ID` ainda não estiver no `.env` e o listener for reiniciado pelo systemd, `client.start()` tenta autenticação interativa mas não há TTY — o processo fica travado ou falha imediatamente.
**Por que acontece:** `client.start()` usa `input()` para phone/código quando não há sessão válida.
**Como evitar:** Completar a autenticação interativa (step SSH) ANTES de habilitar o serviço systemd. Verificar que o arquivo `.session` existe e que `TELEGRAM_GROUP_ID` está preenchido no `.env`.
**Sinais de alerta:** `systemctl status helpertips-listener` mostra `Active: failed` imediatamente após enable.

### Pitfall 2: `.session` com permissões erradas
**O que vai errado:** Se o arquivo `.session` for criado como `ubuntu` (via sudo ou clone incorreto) e o serviço rodar como `helpertips`, o processo falha ao ler/escrever a sessão.
**Por que acontece:** Confusão entre o usuário de SSH padrão (`ubuntu`) e o usuário dedicado (`helpertips`).
**Como evitar:** A autenticação interativa deve ser feita como o user `helpertips` (`sudo -u helpertips bash`) ou corrigir as permissões após: `chown helpertips:helpertips /home/helpertips/helpertips_listener.session`.
**Sinais de alerta:** Erro `PermissionError` no log do journald: `journalctl -u helpertips-listener -n 50`.

### Pitfall 3: `StartLimitBurst` ignorado por estar em `[Service]`
**O que vai errado:** O serviço reinicia infinitamente em loop mesmo com `StartLimitBurst=5`.
**Por que acontece:** `StartLimitBurst` e `StartLimitIntervalSec` são parâmetros da seção `[Unit]`, não `[Service]`. systemd ignora silenciosamente quando colocados em `[Service]`.
**Como evitar:** Sempre colocar em `[Unit]`. Verificar com `systemctl cat helpertips-listener` após deploy.
**Sinais de alerta:** `systemctl status` mostra contagem de restarts crescendo sem limite.

### Pitfall 4: `journalctl` vs arquivo de log — conflito de handlers
**O que vai errado:** systemd captura stdout/stderr automaticamente para journald. Se o listener também escrever em arquivo, logs ficam duplicados (journald + arquivo). Rich pode quebrar com sequências de escape no journald.
**Por que acontece:** systemd redireciona stdout para journald por padrão.
**Como evitar:** A detecção `sys.stdout.isatty()` resolve: em daemon (sem TTY), usar RotatingFileHandler e não escrever em stdout/stderr, ou usar `StandardOutput=null` no unit file para evitar captura do journald.
**Sinais de alerta:** `journalctl -u helpertips-listener` mostrando caracteres de escape ANSI (`\x1b[32m`).

### Pitfall 5: `_salvar_group_id` escreve no `.env` do projeto, não do home
**O que vai errado:** `list_groups.py:_salvar_group_id` usa `os.path.dirname(os.path.dirname(__file__))` para localizar o `.env`. Na EC2 com código em `/home/helpertips/helpertips/`, isso aponta para `/home/helpertips/.env` — correto. Mas se o código estiver em outro path, pode apontar para o lugar errado.
**Como evitar:** Verificar que o clone do repo está em `/home/helpertips/helpertips/` e que `/home/helpertips/.env` existe antes da autenticação interativa.

### Pitfall 6: `After=postgresql.service` pode atrasar em reboots
**O que vai errado:** PostgreSQL demora mais que o esperado para ficar pronto após reboot, listener inicia antes e falha na conexão DB.
**Como evitar:** `After=postgresql.service` garante ordem de inicialização, mas não garante que o PostgreSQL está aceitando conexões. O código já tem reconexão via `get_connection()` — mas um `RestartSec=60` dá margem suficiente para o PG subir primeiro.

---

## Code Examples

### Verificar status e logs após deploy
```bash
# Status do serviço
sudo systemctl status helpertips-listener

# Logs em tempo real (arquivo)
sudo tail -f /var/log/helpertips/listener.log

# Logs do systemd (stderr + stdout capturado)
sudo journalctl -u helpertips-listener -f

# Verificar unit file como interpretado pelo systemd
sudo systemctl cat helpertips-listener

# Recarregar após editar unit file
sudo systemctl daemon-reload && sudo systemctl restart helpertips-listener
```

### Autenticação interativa como user helpertips
```bash
# SSH na EC2
ssh -i ~/.ssh/helpertips-key.pem ubuntu@32.194.158.134

# Mudar para user helpertips
sudo -u helpertips bash

# Carregar .env e rodar listener interativamente
cd /home/helpertips
source .env  # para checar variáveis
python -m helpertips.listener  # client.start() vai pedir phone + código
# Após login: escolher grupo, confirmar TELEGRAM_GROUP_ID no .env, Ctrl+C
```

### Curl de notificação Telegram (padrão verificado)
```bash
# Formato oficial da API Telegram — MEDIUM confidence (múltiplas fontes)
curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d "chat_id=${CHAT_ID}" \
    -d "text=Mensagem de teste"
```

### Verificar arquivo .session após autenticação
```bash
# Como helpertips
ls -la /home/helpertips/helpertips_listener.session
# Esperado: -rw------- 1 helpertips helpertips XXXX ...
```

---

## Environment Availability

Auditado no ambiente de desenvolvimento local (macOS). O ambiente relevante é a EC2 Ubuntu 24.04 LTS.

| Dependência | Requerida por | Disponível (local) | Disponível (EC2) | Fallback |
|-------------|--------------|---------------------|------------------|---------|
| Python 3.12+ | listener.py | ✓ 3.13.6 | ✓ (instalado pelo bootstrap) | — |
| Telethon 1.42 | listener.py | ✓ 1.42.0 | A verificar após `pip install -e .` | — |
| systemd | serviço daemon | ✗ (macOS) | ✓ (Ubuntu 24.04 nativo) | — |
| logrotate | rotação de logs | ✗ (macOS) | ✓ (Ubuntu padrão) | RotatingFileHandler sozinho |
| curl | script notificação | ✓ | ✓ (Ubuntu padrão) | — |
| /var/log/helpertips/ | RotatingFileHandler | ✗ (não criado localmente) | ✓ (criado pelo 01-provision-ec2.sh) | — |
| User helpertips | systemd User= | ✗ (não existe localmente) | ✓ (criado pelo bootstrap) | — |
| Telegram Bot Token | script notificação | A configurar | A configurar | Omitir notificação (exit 0) |

**Dependências sem fallback:**
- systemd: requer EC2 Ubuntu — não testável localmente
- User helpertips + /var/log/helpertips/: requer que `01-provision-ec2.sh` tenha rodado (Phase 6)

**Dependências com fallback:**
- Telegram Bot Token: script de notificação verifica se está vazio e faz exit 0 silencioso — serviço não falha por falta do token

---

## Validation Architecture

### Framework de Testes
| Propriedade | Valor |
|-------------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` → `[tool.pytest.ini_options]` |
| Comando rápido | `pytest tests/ -x -q` |
| Suite completa | `pytest tests/ -v` |

### Mapeamento de Requisitos → Testes
| ID | Comportamento | Tipo | Comando Automatizado | Arquivo |
|----|---------------|------|----------------------|---------|
| DEP-05 | `client.start()` aceita stdin interativo via SSH | manual | N/A — requer TTY real | N/A |
| DEP-05 | `.session` gerado em `/home/helpertips/` com permissões corretas | manual-ssh | N/A — requer EC2 | N/A |
| DEP-01 | `systemctl status helpertips-listener` = `active (running)` | manual-ssh | N/A — requer EC2 + systemd | N/A |
| DEP-01 | Serviço sobrevive a reboot da EC2 | manual-ssh | N/A — requer EC2 | N/A |
| D-02 | `configure_logging()` usa RotatingFileHandler quando `not sys.stdout.isatty()` | unit | `pytest tests/test_listener_logging.py -x` | ❌ Wave 0 |
| D-02 | `configure_logging()` usa RichHandler quando `sys.stdout.isatty()` | unit | `pytest tests/test_listener_logging.py -x` | ❌ Wave 0 |
| — | Sinal capturado aparece no banco | smoke-ssh | `psql -U helpertips_user -d helpertips -c "SELECT COUNT(*) FROM signals;"` | N/A |

**Nota:** DEP-05 e DEP-01 são intrinsecamente manuais — dependem de EC2 real com systemd, TTY SSH, e autenticação Telegram. Sem simulação viável em CI.

### Gaps do Wave 0
- [ ] `tests/test_listener_logging.py` — testa `configure_logging()`: mock `sys.stdout.isatty`, verifica tipo do handler retornado

**Sem gaps de infra:** pytest, conftest.py e fixtures já existem.

---

## Ordem de Execução Recomendada

A fase tem uma restrição de sequência rígida: a autenticação interativa DEVE acontecer antes de habilitar o serviço systemd.

**Passo A — Código (pode ser feito antes do SSH):**
1. Modificar `listener.py` para `configure_logging()` com detecção de TTY (D-02)
2. Criar `deploy/05-setup-listener.sh` (unit file + logrotate + script de notificação)

**Passo B — EC2 via SSH (requer sequência):**
1. Clonar/atualizar código na EC2
2. Criar/atualizar `.env` com credenciais Telegram
3. Rodar listener interativamente como user `helpertips` → gerar `.session`, configurar `TELEGRAM_GROUP_ID`
4. Confirmar que sinal aparece no banco
5. Ctrl+C e rodar `05-setup-listener.sh`
6. Testar reboot: `sudo reboot` → verificar `systemctl status` após reconexão

---

## Sources

### Primary (HIGH confidence)
- Código existente `helpertips/listener.py` — verificado diretamente; `client.start()` em linha 95 confirma stdin interativo
- Código existente `deploy/01-provision-ec2.sh` — confirma `/var/log/helpertips/` criado, user `helpertips` criado
- `pyproject.toml` — versões de dependências confirmadas

### Secondary (MEDIUM confidence)
- [systemd service environment variables - IT'S FOSS](https://itsfoss.gitlab.io/blog/systemd-service-environment-variables/) — `EnvironmentFile` placement e permissões
- [systemd StartLimitBurst must be in Unit section - copyprogramming](https://copyprogramming.com/howto/systemd-s-startlimitintervalsec-and-startlimitburst-never-work) — pitfall crítico confirmado por múltiplas fontes
- [Python logging handlers docs - docs.python.org](https://docs.python.org/3/library/logging.handlers.html) — `RotatingFileHandler` API oficial
- [Telethon session concepts](https://docs.telethon.dev/en/stable/concepts/sessions.html) — persistência do arquivo `.session` entre restarts
- [Telegram Bot API sendMessage - shellhacks](https://www.shellhacks.com/telegram-api-send-message-personal-notification-bot/) — formato curl confirmado por múltiplas fontes

### Tertiary (LOW confidence)
- [Log rotation for Python - jugmac00.github.io](https://jugmac00.github.io/blog/log-rotation-for-python-applications/) — recomendação `delaycompress` para serviços que mantêm arquivo aberto

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — código já existe e funciona; apenas configuração de sistema operacional nova
- Architecture: HIGH — padrões systemd são estáveis no Ubuntu 24.04; unit file pattern verificado
- Pitfalls: HIGH — `StartLimitBurst` em `[Service]` é bug documentado amplamente; outros pitfalls verificados pelo código existente

**Research date:** 2026-04-04
**Valid until:** 2026-10-04 (stack estável; systemd unit syntax não muda com frequência)
