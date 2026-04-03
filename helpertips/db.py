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
    'TELEGRAM_GROUP_ID',
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
                raw_text    TEXT NOT NULL,
                received_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at  TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_signals_liga        ON signals(liga);
            CREATE INDEX IF NOT EXISTS idx_signals_entrada     ON signals(entrada);
            CREATE INDEX IF NOT EXISTS idx_signals_resultado   ON signals(resultado);
            CREATE INDEX IF NOT EXISTS idx_signals_received_at ON signals(received_at);
        """)
    conn.commit()
