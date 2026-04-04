#!/bin/bash
# Configura o dashboard HelperTips como servico systemd na EC2 via gunicorn
# Executar como root apos deploy/05-setup-listener.sh ja executado
# Prerequisito: user helpertips + venv + pacote helpertips instalado no venv
set -euo pipefail

echo "=== HelperTips Dashboard Setup ==="

# ---------------------------------------------------------------------------
# 1. Unit file do dashboard
# ---------------------------------------------------------------------------
echo ">>> Criando /etc/systemd/system/helpertips-dashboard.service..."

cat > /etc/systemd/system/helpertips-dashboard.service <<'UNIT'
[Unit]
Description=HelperTips Dashboard
After=network.target postgresql.service
StartLimitBurst=5
StartLimitIntervalSec=300

[Service]
Type=simple
User=helpertips
Group=helpertips
WorkingDirectory=/home/helpertips
EnvironmentFile=/home/helpertips/.env
ExecStart=/home/helpertips/.venv/bin/gunicorn \
    --workers 2 \
    --bind 127.0.0.1:8050 \
    --timeout 120 \
    --access-logfile /var/log/helpertips/dashboard-access.log \
    --error-logfile /var/log/helpertips/dashboard-error.log \
    helpertips.dashboard:server
Restart=on-failure
RestartSec=60
StandardOutput=null
StandardError=null
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
UNIT

chmod 644 /etc/systemd/system/helpertips-dashboard.service
echo "helpertips-dashboard.service criado"

# ---------------------------------------------------------------------------
# 2. Logrotate — inclui listener + dashboard (substitui configuracao anterior)
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

/var/log/helpertips/dashboard-access.log
/var/log/helpertips/dashboard-error.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    missingok
    create 0640 helpertips helpertips
    postrotate
        systemctl kill -s USR1 helpertips-dashboard.service 2>/dev/null || true
    endscript
}
LOGROTATE

chmod 644 /etc/logrotate.d/helpertips
echo "logrotate configurado"

# ---------------------------------------------------------------------------
# 3. Instalar gunicorn no venv
# ---------------------------------------------------------------------------
echo ">>> Instalando gunicorn no venv..."
sudo -u helpertips /home/helpertips/.venv/bin/pip install -q "gunicorn>=25.0"
echo "gunicorn instalado"

# ---------------------------------------------------------------------------
# 4. Criar diretorio de log (idempotente)
# ---------------------------------------------------------------------------
echo ">>> Criando /var/log/helpertips/ (idempotente)..."
mkdir -p /var/log/helpertips
chown helpertips:helpertips /var/log/helpertips
echo "diretorio de log pronto"

# ---------------------------------------------------------------------------
# 5. Recarregar systemd
# ---------------------------------------------------------------------------
echo ">>> Recarregando systemd daemon..."
systemctl daemon-reload
echo "systemd recarregado"

# ---------------------------------------------------------------------------
# 6. Habilitar e iniciar servico (idempotente)
# ---------------------------------------------------------------------------
echo ">>> Habilitando e iniciando helpertips-dashboard..."
systemctl enable helpertips-dashboard
systemctl restart helpertips-dashboard
echo "helpertips-dashboard habilitado e iniciado"

# ---------------------------------------------------------------------------
# 7. Instrucoes finais com verificacao
# ---------------------------------------------------------------------------
echo ""
echo "=== Dashboard setup concluido ==="
echo "Verificar: sudo systemctl status helpertips-dashboard"
echo "Testar: curl -s http://127.0.0.1:8050 | head -5"
