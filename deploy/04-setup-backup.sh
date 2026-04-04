#!/bin/bash
# Configurar backup automatico diario para HelperTips
# Executar como root no EC2 apos PostgreSQL estar funcionando
set -euo pipefail

echo "=== HelperTips Backup Setup ==="

# 1. Instalar AWS CLI v2 (se nao presente)
if ! command -v aws &>/dev/null; then
    echo ">>> Instalando AWS CLI v2..."
    cd /tmp
    curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip -qo awscliv2.zip
    ./aws/install
    rm -rf awscliv2.zip aws/
    echo "AWS CLI v2 instalado: $(aws --version)"
else
    echo "AWS CLI ja instalado: $(aws --version)"
fi

# 2. Copiar script de backup para /usr/local/bin
echo ">>> Instalando script de backup..."
cp /home/helpertips/helpertips/deploy/backup-helpertips.sh /usr/local/bin/backup-helpertips.sh
chmod 755 /usr/local/bin/backup-helpertips.sh
chown root:root /usr/local/bin/backup-helpertips.sh

# 3. Criar cron entry
echo ">>> Configurando cron diario (03:00 UTC)..."
cat > /etc/cron.d/helpertips-backup <<'CRON'
# Backup diario HelperTips: pg_dump + .session para S3
# Executa as 03:00 UTC como usuario helpertips
0 3 * * * helpertips /usr/local/bin/backup-helpertips.sh >> /var/log/helpertips/backup.log 2>&1
CRON
chmod 644 /etc/cron.d/helpertips-backup

echo ""
echo "=== Backup setup concluido ==="
echo ""
echo "IMPORTANTE: Antes do backup funcionar, voce precisa:"
echo ""
echo "1. Criar S3 bucket no Console AWS:"
echo "   - Nome: helpertips-backups-ACCOUNT_ID (substituir ACCOUNT_ID)"
echo "   - Regiao: us-east-1"
echo "   - Block all public access: SIM"
echo "   - Versioning: desabilitado (cron ja organiza por data)"
echo ""
echo "2. Criar IAM Role para EC2 no Console AWS:"
echo "   - IAM > Roles > Create Role > AWS Service > EC2"
echo "   - Nome: helpertips-ec2-role"
echo "   - Criar policy inline com permissoes:"
echo '   {'
echo '     "Version": "2012-10-17",'
echo '     "Statement": [{'
echo '       "Effect": "Allow",'
echo '       "Action": ["s3:PutObject", "s3:GetObject", "s3:ListBucket", "s3:DeleteObject"],'
echo '       "Resource": ['
echo '         "arn:aws:s3:::helpertips-backups-ACCOUNT_ID",'
echo '         "arn:aws:s3:::helpertips-backups-ACCOUNT_ID/*"'
echo '       ]'
echo '     }]'
echo '   }'
echo ""
echo "3. Associar IAM Role a instancia EC2:"
echo "   - EC2 Console > selecionar instancia > Actions > Security > Modify IAM Role"
echo "   - Selecionar helpertips-ec2-role"
echo ""
echo "4. Testar manualmente:"
echo "   sudo -u helpertips /usr/local/bin/backup-helpertips.sh"
echo "   aws s3 ls s3://helpertips-backups-ACCOUNT_ID/backups/"
