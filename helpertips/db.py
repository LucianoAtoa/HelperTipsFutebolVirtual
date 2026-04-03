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

            -- Seed: mercados principais (idempotente)
            INSERT INTO mercados (slug, nome_display, odd_ref) VALUES
                ('over_2_5',     'Over 2.5',     2.30),
                ('ambas_marcam', 'Ambas Marcam', 2.10)
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

    conn.commit()
