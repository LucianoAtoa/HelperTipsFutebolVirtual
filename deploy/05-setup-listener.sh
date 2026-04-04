#!/bin/bash
# Configura o listener HelperTips como servico systemd na EC2
# Executar como root apos autenticacao interativa Telethon completada
# Prerequisito: deploy/01-provision-ec2.sh ja executado (user helpertips + /var/log/helpertips/)
set -euo pipefail

echo "=== HelperTips Listener Setup ==="

# ---------------------------------------------------------------------------
# 1. Unit file principal do listener
# ---------------------------------------------------------------------------
echo ">>> Criando /etc/systemd/system/helpertips-listener.service..."

cat > /etc/systemd/system/helpertips-listener.service <<'UNIT'
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
StandardOutput=null
StandardError=journal
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
UNIT

chmod 644 /etc/systemd/system/helpertips-listener.service
echo "helpertips-listener.service criado"

# ---------------------------------------------------------------------------
# 2. Unit file de notificacao de falha (template)
# ---------------------------------------------------------------------------
echo ">>> Criando /etc/systemd/system/helpertips-notify-failure@.service..."

cat > /etc/systemd/system/helpertips-notify-failure@.service <<'UNIT'
[Unit]
Description=HelperTips failure notifier for %i

[Service]
Type=oneshot
User=helpertips
EnvironmentFile=/home/helpertips/.env
ExecStart=/usr/local/bin/helpertips-notify-failure.sh %i
UNIT

chmod 644 /etc/systemd/system/helpertips-notify-failure@.service
echo "helpertips-notify-failure@.service criado"

# ---------------------------------------------------------------------------
# 3. Script de notificacao via Telegram Bot API
# ---------------------------------------------------------------------------
echo ">>> Criando /usr/local/bin/helpertips-notify-failure.sh..."

cat > /usr/local/bin/helpertips-notify-failure.sh <<'SCRIPT'
#!/bin/bash
# Envia alerta via Telegram Bot API quando o listener falha
# Invocado pelo systemd OnFailure= com o nome do servico como argumento
SERVICE_NAME="${1:-helpertips-listener}"
BOT_TOKEN="${TELEGRAM_NOTIFY_TOKEN:-}"
CHAT_ID="${TELEGRAM_NOTIFY_CHAT_ID:-}"

if [[ -z "$BOT_TOKEN" || -z "$CHAT_ID" ]]; then
    echo "TELEGRAM_NOTIFY_TOKEN ou TELEGRAM_NOTIFY_CHAT_ID nao configurado — notificacao ignorada" >&2
    exit 0
fi

HOSTNAME=$(hostname)
MESSAGE="HelperTips ALERTA: servico ${SERVICE_NAME} falhou em ${HOSTNAME}. Verificar: sudo systemctl status ${SERVICE_NAME}"

curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d "chat_id=${CHAT_ID}" \
    -d "text=${MESSAGE}" \
    > /dev/null
SCRIPT

chmod 755 /usr/local/bin/helpertips-notify-failure.sh
chown root:root /usr/local/bin/helpertips-notify-failure.sh
echo "helpertips-notify-failure.sh criado"

# ---------------------------------------------------------------------------
# 4. Configuracao logrotate
# ---------------------------------------------------------------------------
echo ">>> Criando /etc/logrotate.d/helpertips..."

cat > /etc/logrotate.d/helpertips <<'LOGROTATE'
/var/log/helpertips/listener.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    missingok
    create 0640 helpertips helpertips
}
LOGROTATE

chmod 644 /etc/logrotate.d/helpertips
echo "logrotate configurado"

# ---------------------------------------------------------------------------
# 5. Recarregar systemd
# ---------------------------------------------------------------------------
echo ">>> Recarregando systemd daemon..."
systemctl daemon-reload
echo "systemd recarregado"

# ---------------------------------------------------------------------------
# Instrucoes finais
# ---------------------------------------------------------------------------
echo ""
echo "=== Setup concluido. Proximo passo: autenticacao interativa via SSH (ver README-deploy.md) ==="
echo ""
echo "IMPORTANTE: Nao habilitar o servico antes de completar a autenticacao Telethon."
echo ""
echo "Passos para autenticacao interativa:"
echo "  sudo -u helpertips bash"
echo "  cd /home/helpertips && source venv/bin/activate"
echo "  python -m helpertips.listener"
echo "  # Digitar phone number, codigo SMS/Telegram"
echo "  # Selecionar grupo {VIP} ExtremeTips"
echo "  # Aguardar 1 sinal aparecer, Ctrl+C"
echo ""
echo "Apos autenticacao:"
echo "  sudo systemctl enable --now helpertips-listener"
echo "  sudo systemctl status helpertips-listener"
