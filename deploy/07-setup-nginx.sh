#!/bin/bash
# Configura nginx como reverse proxy com HTTP Basic Auth para o dashboard HelperTips
# Executar como root apos deploy/06-setup-dashboard.sh concluido
# Prerequisito: DASHBOARD_USER e DASHBOARD_PASSWORD definidos em /home/helpertips/.env
set -euo pipefail

echo "=== HelperTips Nginx Setup ==="

# ---------------------------------------------------------------------------
# 1. Instalar nginx e apache2-utils
# ---------------------------------------------------------------------------
echo ">>> Instalando nginx e apache2-utils..."
apt install -y nginx apache2-utils
echo "nginx e apache2-utils instalados"

# ---------------------------------------------------------------------------
# 2. Gerar /etc/nginx/.htpasswd a partir das credenciais do .env
# ---------------------------------------------------------------------------
echo ">>> Gerando /etc/nginx/.htpasswd..."
source /home/helpertips/.env

if [[ -z "${DASHBOARD_USER:-}" || -z "${DASHBOARD_PASSWORD:-}" ]]; then
    echo "ERRO: DASHBOARD_USER e DASHBOARD_PASSWORD devem estar definidos em /home/helpertips/.env"
    exit 1
fi

# -c cria/recria arquivo (idempotente), -b aceita senha no CLI (obrigatorio para scripting),
# -B usa bcrypt (mais seguro que MD5 padrao do htpasswd)
htpasswd -cbB /etc/nginx/.htpasswd "$DASHBOARD_USER" "$DASHBOARD_PASSWORD"
chmod 640 /etc/nginx/.htpasswd
chown root:www-data /etc/nginx/.htpasswd
echo ".htpasswd gerado para usuario: $DASHBOARD_USER"

# ---------------------------------------------------------------------------
# 3. Configurar server block nginx
# ---------------------------------------------------------------------------
echo ">>> Criando /etc/nginx/sites-available/helpertips..."

cat > /etc/nginx/sites-available/helpertips <<'NGINX'
server {
    listen 80;
    server_name _;

    auth_basic "HelperTips";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass         http://127.0.0.1:8050;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }
}
NGINX

chmod 644 /etc/nginx/sites-available/helpertips
echo "server block nginx configurado"

# ---------------------------------------------------------------------------
# 4. Ativar site helpertips e desabilitar site default
# ---------------------------------------------------------------------------
echo ">>> Ativando site helpertips e desabilitando default..."
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/helpertips /etc/nginx/sites-enabled/helpertips
nginx -t && systemctl reload nginx
echo "site helpertips ativado, default desabilitado"

# ---------------------------------------------------------------------------
# 5. Habilitar nginx no boot
# ---------------------------------------------------------------------------
echo ">>> Habilitando nginx no boot..."
systemctl enable nginx
echo "nginx habilitado para iniciar automaticamente apos reboot"

# ---------------------------------------------------------------------------
# Instrucoes finais
# ---------------------------------------------------------------------------
echo ""
echo "=== Nginx setup concluido ==="
echo ""
echo "Verificar:"
echo "  curl -I http://localhost/          # Deve retornar 401 Unauthorized"
echo "  curl -u \$DASHBOARD_USER:\$DASHBOARD_PASSWORD http://localhost/ | head -5  # Deve retornar HTML Dash"
echo ""
echo "IMPORTANTE: Fechar porta 8050 no AWS Security Group (helpertips-sg)!"
echo "A porta 8050 foi aberta temporariamente na Phase 6."
echo "Com nginx ativo na porta 80, acesso direto a 8050 bypassa autenticacao."
echo "AWS Console -> EC2 -> Security Groups -> helpertips-sg -> Editar inbound rules -> Remover regra 8050"
