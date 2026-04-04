#!/bin/bash
# Backup diario do HelperTips: pg_dump + .session para S3
# Executado via cron como usuario helpertips
# Requer: IAM instance profile com permissao s3:PutObject no bucket
set -euo pipefail

TIMESTAMP=$(date +%Y-%m-%d_%H%M)
BACKUP_DIR="/tmp/helpertips-backup-$$"
LOG_PREFIX="[helpertips-backup]"

# Carregar variaveis do .env para DB_PASSWORD
set -a
source /home/helpertips/.env
set +a

# Descobrir bucket name baseado na conta AWS
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "unknown")
BUCKET="helpertips-backups-${ACCOUNT_ID}"

echo "$LOG_PREFIX Iniciando backup $TIMESTAMP para s3://$BUCKET/"

mkdir -p "$BACKUP_DIR"

# 1. Dump PostgreSQL (formato custom, comprimido)
echo "$LOG_PREFIX Executando pg_dump..."
PGPASSWORD="$DB_PASSWORD" pg_dump \
    -h localhost \
    -U helpertips_user \
    -d helpertips \
    -Fc \
    -f "$BACKUP_DIR/helpertips-${TIMESTAMP}.dump"

# 2. Copia do .session (se existir)
SESSION_FILE="/home/helpertips/helpertips_listener.session"
if [ -f "$SESSION_FILE" ]; then
    cp "$SESSION_FILE" "$BACKUP_DIR/helpertips_listener-${TIMESTAMP}.session"
    echo "$LOG_PREFIX .session copiado"
else
    echo "$LOG_PREFIX .session nao encontrado, pulando"
fi

# 3. Upload para S3
echo "$LOG_PREFIX Enviando para S3..."
aws s3 cp "$BACKUP_DIR/" "s3://${BUCKET}/backups/${TIMESTAMP}/" --recursive --quiet

# 4. Limpeza local
rm -rf "$BACKUP_DIR"

# 5. Limpar backups com mais de 30 dias no S3
echo "$LOG_PREFIX Limpando backups antigos (>30 dias)..."
CUTOFF=$(date -d "-30 days" +%Y-%m-%d 2>/dev/null || date -v-30d +%Y-%m-%d)
aws s3 ls "s3://${BUCKET}/backups/" | while read -r line; do
    BACKUP_DATE=$(echo "$line" | awk '{print $2}' | tr -d '/')
    if [[ "$BACKUP_DATE" < "$CUTOFF" ]] && [[ "$BACKUP_DATE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2} ]]; then
        echo "$LOG_PREFIX Removendo backup antigo: $BACKUP_DATE"
        aws s3 rm "s3://${BUCKET}/backups/${BACKUP_DATE}/" --recursive --quiet
    fi
done

echo "$LOG_PREFIX Backup concluido com sucesso: $TIMESTAMP"
