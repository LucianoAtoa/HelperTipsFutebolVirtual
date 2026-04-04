"""
Database module for HelperTips.

Provides:
- REQUIRED_VARS: list of all required environment variables
- validate_config(): raises SystemExit(1) if any required var is missing or empty
- get_connection(): returns a psycopg2 connection using env vars
- ensure_schema(conn): creates the signals table and indexes if not present
"""
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

REQUIRED_VARS = [
    'TELEGRAM_API_ID',
    'TELEGRAM_API_HASH',
    # TELEGRAM_GROUP_ID é opcional — se vazio, listener oferece seleção interativa
    'DB_HOST',
    'DB_PORT',
    'DB_NAME',
    'DB_USER',
    'DB_PASSWORD',
]


def validate_config():
    """
    Validate that all required environment variables are set and non-empty.
    Raises SystemExit(1) with a descriptive message listing all missing vars.
    """
    missing = [k for k in REQUIRED_VARS if not os.environ.get(k)]
    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        print("Copy .env.example to .env and fill in all values.")
        raise SystemExit(1)


def get_connection():
    """
    Return a new psycopg2 connection using DB_* environment variables.
    Caller is responsible for closing the connection.
    """
    return psycopg2.connect(
        host=os.environ['DB_HOST'],
        port=os.environ['DB_PORT'],
        dbname=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
    )


def ensure_schema(conn):
    """
    Create the signals table and required indexes if they do not exist.
    Commits the transaction after schema creation.
    """
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id          SERIAL PRIMARY KEY,
                message_id  BIGINT UNIQUE NOT NULL,
                liga        TEXT,
                entrada     TEXT,
                horario     TEXT,
                periodo     TEXT,
                dia_semana  SMALLINT,
                resultado   TEXT,
                placar      TEXT,
                tentativa   SMALLINT,
                raw_text    TEXT NOT NULL,
                received_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at  TIMESTAMPTZ DEFAULT NOW()
            );

            -- Add tentativa column to existing tables that were created before this migration
            ALTER TABLE signals ADD COLUMN IF NOT EXISTS tentativa SMALLINT;

            CREATE INDEX IF NOT EXISTS idx_signals_liga        ON signals(liga);
            CREATE INDEX IF NOT EXISTS idx_signals_entrada     ON signals(entrada);
            CREATE INDEX IF NOT EXISTS idx_signals_resultado   ON signals(resultado);
            CREATE INDEX IF NOT EXISTS idx_signals_received_at ON signals(received_at);

            CREATE TABLE IF NOT EXISTS parse_failures (
                id             SERIAL PRIMARY KEY,
                raw_text       TEXT NOT NULL,
                received_at    TIMESTAMPTZ DEFAULT NOW(),
                failure_reason TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_parse_failures_received_at ON parse_failures(received_at);

            -- Tabela de mercados principais (Over 2.5, Ambas Marcam)
            CREATE TABLE IF NOT EXISTS mercados (
                id           SERIAL PRIMARY KEY,
                slug         TEXT UNIQUE NOT NULL,
                nome_display TEXT NOT NULL,
                odd_ref      NUMERIC(6,2) NOT NULL,
                ativo        BOOLEAN NOT NULL DEFAULT TRUE
            );

            -- Tabela de entradas complementares por mercado
            CREATE TABLE IF NOT EXISTS complementares (
                id               SERIAL PRIMARY KEY,
                mercado_id       INTEGER NOT NULL REFERENCES mercados(id),
                slug             TEXT NOT NULL,
                nome_display     TEXT NOT NULL,
                percentual       NUMERIC(5,4) NOT NULL,
                odd_ref          NUMERIC(8,2) NOT NULL,
                regra_validacao  TEXT NOT NULL,
                UNIQUE (mercado_id, slug)
            );

            -- Seed: mercados principais com IDs fixos (id=1 Over 2.5, id=2 Ambas Marcam)
            -- OVERRIDING SYSTEM VALUE permite inserir id explícito em coluna SERIAL
            INSERT INTO mercados (id, slug, nome_display, odd_ref) OVERRIDING SYSTEM VALUE VALUES
                (1, 'over_2_5',     'Over 2.5',     2.30),
                (2, 'ambas_marcam', 'Ambas Marcam', 2.10)
            ON CONFLICT (slug) DO NOTHING;
        """)

        # Seed: complementares Over 2.5 (percentuais como fracao decimal)
        cur.execute("""
            INSERT INTO complementares (mercado_id, slug, nome_display, percentual, odd_ref, regra_validacao)
            SELECT m.id, c.slug, c.nome_display, c.percentual, c.odd_ref, c.regra_validacao
            FROM mercados m,
            (VALUES
                ('over_3_5',         'Over 3.5',            0.20, 4.00,  'over_3_5'),
                ('empate_3_3_4_4',   'Empate 3-3 / 4-4',   0.01, 30.00, 'empate_3_3_4_4'),
                ('over_5_plus',      'Over 5+',             0.10, 15.00, 'over_5_plus'),
                ('gols_casa_4',      'Total Gols Casa = 4', 0.01, 25.00, 'gols_casa_4'),
                ('gols_fora_4',      'Total Gols Fora = 4', 0.01, 25.00, 'gols_fora_4'),
                ('gols_casa_5_plus', 'Total Gols Casa 5+',  0.01, 40.00, 'gols_casa_5_plus'),
                ('gols_fora_5_plus', 'Total Gols Fora 5+',  0.01, 40.00, 'gols_fora_5_plus')
            ) AS c(slug, nome_display, percentual, odd_ref, regra_validacao)
            WHERE m.slug = 'over_2_5'
            ON CONFLICT (mercado_id, slug) DO NOTHING;
        """)

        # Seed: complementares Ambas Marcam (percentuais diferentes de Over 2.5)
        cur.execute("""
            INSERT INTO complementares (mercado_id, slug, nome_display, percentual, odd_ref, regra_validacao)
            SELECT m.id, c.slug, c.nome_display, c.percentual, c.odd_ref, c.regra_validacao
            FROM mercados m,
            (VALUES
                ('over_3_5',         'Over 3.5',            0.10, 4.00,  'over_3_5'),
                ('empate_3_3_4_4',   'Empate 3-3 / 4-4',   0.01, 30.00, 'empate_3_3_4_4'),
                ('over_5_plus',      'Over 5+',             0.05, 15.00, 'over_5_plus'),
                ('gols_casa_4',      'Total Gols Casa = 4', 0.01, 25.00, 'gols_casa_4'),
                ('gols_fora_4',      'Total Gols Fora = 4', 0.01, 25.00, 'gols_fora_4'),
                ('gols_casa_5_plus', 'Total Gols Casa 5+',  0.01, 40.00, 'gols_casa_5_plus'),
                ('gols_fora_5_plus', 'Total Gols Fora 5+',  0.01, 40.00, 'gols_fora_5_plus')
            ) AS c(slug, nome_display, percentual, odd_ref, regra_validacao)
            WHERE m.slug = 'ambas_marcam'
            ON CONFLICT (mercado_id, slug) DO NOTHING;
        """)

        # --- Migration Phase 09: multi-grupo ---
        # Passo 1: Adicionar colunas (idempotente via IF NOT EXISTS)
        cur.execute("ALTER TABLE signals ADD COLUMN IF NOT EXISTS group_id BIGINT")
        cur.execute("ALTER TABLE signals ADD COLUMN IF NOT EXISTS mercado_id INTEGER REFERENCES mercados(id)")

        # Passo 2: UPDATE retroativo — dados históricos recebem group_id do grupo original
        # Usa TELEGRAM_GROUP_IDS (Phase 09) ou TELEGRAM_GROUP_ID (legado) como fallback
        original_group_id = os.environ.get(
            'TELEGRAM_GROUP_IDS',
            os.environ.get('TELEGRAM_GROUP_ID', '')
        ).split(',')[0].strip()
        if original_group_id:
            cur.execute(
                "UPDATE signals SET group_id = %s WHERE group_id IS NULL",
                (int(original_group_id),)
            )

        # Passo 3: SET NOT NULL somente se não há NULLs restantes (evita erro em produção)
        cur.execute("SELECT COUNT(*) FROM signals WHERE group_id IS NULL")
        null_count = cur.fetchone()[0]
        if null_count == 0:
            cur.execute("""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='signals' AND column_name='group_id'
                        AND is_nullable='YES'
                    ) THEN
                        ALTER TABLE signals ALTER COLUMN group_id SET NOT NULL;
                    END IF;
                END $$;
            """)

        # Passo 4: Drop constraint única antiga e criar nova constraint composta
        cur.execute("ALTER TABLE signals DROP CONSTRAINT IF EXISTS signals_message_id_key")
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'signals_group_message_unique'
                ) THEN
                    ALTER TABLE signals ADD CONSTRAINT signals_group_message_unique
                        UNIQUE (group_id, message_id);
                END IF;
            END $$;
        """)

        # Passo 5: Índices em group_id e mercado_id para performance de queries
        cur.execute("CREATE INDEX IF NOT EXISTS idx_signals_group_id ON signals(group_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_signals_mercado_id ON signals(mercado_id)")

    conn.commit()
