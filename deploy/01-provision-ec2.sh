#!/bin/bash
# Bootstrap inicial do EC2 para HelperTips
# Executar como root (ou com sudo) apos primeiro SSH
set -euo pipefail

echo "=== HelperTips EC2 Bootstrap ==="

# 1. Swap de 1GB (per D-01, t3.micro tem apenas 1GB RAM)
if [ ! -f /swapfile ]; then
    echo ">>> Criando swap de 1GB..."
    fallocate -l 1G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "Swap criado com sucesso"
else
    echo "Swap ja existe, pulando"
fi

# 2. Usuario dedicado helpertips (nao root)
if ! id helpertips &>/dev/null; then
    echo ">>> Criando usuario helpertips..."
    useradd -m -s /bin/bash helpertips
    echo "Usuario helpertips criado"
else
    echo "Usuario helpertips ja existe, pulando"
fi

# 3. Pacotes base
echo ">>> Atualizando pacotes e instalando dependencias..."
apt update -y
apt install -y python3.12-venv git curl ca-certificates unzip

# 4. Diretorio de logs
mkdir -p /var/log/helpertips
chown helpertips:helpertips /var/log/helpertips

echo "=== Bootstrap concluido ==="
echo "Proximos passos: executar deploy/02-setup-postgres.sh"
