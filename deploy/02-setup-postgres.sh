#!/bin/bash
# Instalar PostgreSQL 16 e configurar banco para HelperTips
# Executar como root (sudo) no EC2 apos 01-provision-ec2.sh
set -euo pipefail

echo "=== HelperTips PostgreSQL Setup ==="

# Verificar se ja esta instalado
if command -v psql &>/dev/null && psql --version | grep -q "16"; then
    echo "PostgreSQL 16 ja instalado, pulando instalacao"
else
    # 1. Repositorio oficial PGDG
    echo ">>> Instalando PostgreSQL 16 via PGDG..."
    install -d /usr/share/postgresql-common/pgdg
    curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc
    sh -c 'echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
    apt update -y
    apt install -y postgresql-16
    echo "PostgreSQL 16 instalado"
fi

# 2. Garantir que esta rodando
systemctl enable postgresql
systemctl start postgresql

# 3. Criar role e banco
# A senha sera lida interativamente para nao ficar em historico de shell
echo ""
echo ">>> Definir senha para o usuario helpertips_user do PostgreSQL"
echo "   (esta mesma senha deve ir no DB_PASSWORD do .env no servidor)"
read -s -p "Senha: " DB_PASS
echo ""

sudo -u postgres psql <<EOSQL
-- Criar role (ignora se ja existe)
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'helpertips_user') THEN
        CREATE ROLE helpertips_user WITH LOGIN PASSWORD '${DB_PASS}';
    ELSE
        ALTER ROLE helpertips_user WITH PASSWORD '${DB_PASS}';
    END IF;
END
\$\$;

-- Criar banco (ignora se ja existe)
SELECT 'CREATE DATABASE helpertips OWNER helpertips_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'helpertips')\gexec

GRANT ALL PRIVILEGES ON DATABASE helpertips TO helpertips_user;
EOSQL

# 4. Configurar pg_hba.conf para scram-sha-256 (per pesquisa - peer auth quebra psycopg2)
PG_HBA="/etc/postgresql/16/main/pg_hba.conf"
if ! grep -q "helpertips_user" "$PG_HBA"; then
    echo ">>> Configurando pg_hba.conf para scram-sha-256..."
    # Inserir antes da primeira linha "local" existente
    sed -i '/^local.*all.*all/i local   helpertips      helpertips_user                 scram-sha-256' "$PG_HBA"
    systemctl restart postgresql
    echo "pg_hba.conf atualizado e PostgreSQL reiniciado"
else
    echo "pg_hba.conf ja configurado para helpertips_user"
fi

# 5. Reduzir shared_buffers para 64MB (t3.micro com 1GB RAM — per pesquisa)
PG_CONF="/etc/postgresql/16/main/postgresql.conf"
if grep -q "^shared_buffers = 128MB" "$PG_CONF"; then
    echo ">>> Reduzindo shared_buffers de 128MB para 64MB (economia de RAM)..."
    sed -i 's/^shared_buffers = 128MB/shared_buffers = 64MB/' "$PG_CONF"
    systemctl restart postgresql
    echo "shared_buffers ajustado para 64MB"
fi

# 6. Verificacao
echo ""
echo "=== Verificacao ==="
sudo -u postgres psql -c "SELECT rolname FROM pg_roles WHERE rolname = 'helpertips_user';"
echo "PostgreSQL setup concluido!"
echo ""
echo "Proximos passos:"
echo "  1. Copiar .env para /home/helpertips/.env com DB_PASSWORD preenchido"
echo "  2. Clonar repositorio em /home/helpertips/helpertips"
echo "  3. Criar venv e instalar dependencias"
echo "  4. Rodar: python3 -c 'from helpertips.db import get_connection, ensure_schema; c=get_connection(); ensure_schema(c); c.close(); print(\"Schema OK\")'"
