#!/bin/bash
# Criar budget alert AWS para HelperTips ($15/mes)
# Requer: aws configure ja executado com credenciais e regiao us-east-1
set -euo pipefail

echo "=== HelperTips Budget Alert Setup ==="

# Verificar AWS CLI
if ! command -v aws &>/dev/null; then
    echo "ERRO: AWS CLI nao encontrado. Instalar com: brew install awscli (macOS) ou ver deploy/README-deploy.md"
    exit 1
fi

# Email para notificacoes
read -p "Email para alertas de billing: " ALERT_EMAIL

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Conta AWS: $ACCOUNT_ID"

# Verificar se budget ja existe
if aws budgets describe-budgets --account-id "$ACCOUNT_ID" --query "Budgets[?BudgetName=='HelperTips-Monthly']" --output text 2>/dev/null | grep -q "HelperTips-Monthly"; then
    echo "Budget 'HelperTips-Monthly' ja existe, pulando criacao"
    exit 0
fi

echo ">>> Criando budget alert de $15/mes..."

aws budgets create-budget \
  --account-id "$ACCOUNT_ID" \
  --budget '{
    "BudgetName": "HelperTips-Monthly",
    "BudgetLimit": {"Amount": "15", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }' \
  --notifications-with-subscribers "[{
    \"Notification\": {
      \"NotificationType\": \"ACTUAL\",
      \"ComparisonOperator\": \"GREATER_THAN\",
      \"Threshold\": 80,
      \"ThresholdType\": \"PERCENTAGE\"
    },
    \"Subscribers\": [{
      \"SubscriptionType\": \"EMAIL\",
      \"Address\": \"${ALERT_EMAIL}\"
    }]
  }]" \
  --region us-east-1

echo ""
echo "=== Budget alert criado com sucesso ==="
echo "  Nome: HelperTips-Monthly"
echo "  Limite: \$15/mes"
echo "  Alerta: Email quando custo real ultrapassar 80% (\$12)"
echo "  Email: $ALERT_EMAIL"
echo ""
echo "Verificar no Console: https://console.aws.amazon.com/billing/home#/budgets"
