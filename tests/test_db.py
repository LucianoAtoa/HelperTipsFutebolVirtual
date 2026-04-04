"""
test_db.py — Testes de integração para ensure_schema() com tabelas mercados e complementares.

Verifica:
  - Criação das tabelas mercados e complementares
  - Seed data de 2 mercados principais (Over 2.5 e Ambas Marcam)
  - Seed data de 14 complementares (7 por mercado)
  - Idempotência: chamadas repetidas não duplicam dados
  - Percentuais armazenados como fração decimal (0.20, não 20)

Requer conexão PostgreSQL configurada via .env.
"""
from decimal import Decimal

import pytest

try:
    from helpertips.db import ensure_schema, get_connection
    _IMPORTS_OK = True
except ImportError as e:
    _IMPORTS_OK = False
    _IMPORT_ERROR = str(e)


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def db_conn():
    """
    Provide a live psycopg2 connection for DB-dependent tests.
    Ensures schema and cleans up mercados/complementares after each test.
    """
    if not _IMPORTS_OK:
        pytest.skip(f"helpertips.db import failed: {_IMPORT_ERROR}")

    try:
        conn = get_connection()
    except Exception as exc:
        pytest.skip(f"PostgreSQL not available: {exc}")

    ensure_schema(conn)

    yield conn

    # Teardown: FK order — complementares antes de mercados
    with conn.cursor() as cur:
        cur.execute("DELETE FROM complementares")
        cur.execute("DELETE FROM mercados")
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Testes de estrutura das tabelas
# ---------------------------------------------------------------------------

def test_ensure_schema_mercados(db_conn):
    """Após ensure_schema(), tabela mercados existe com colunas esperadas."""
    with db_conn.cursor() as cur:
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'mercados'
            ORDER BY column_name
        """)
        columns = {row[0] for row in cur.fetchall()}

    expected = {'id', 'slug', 'nome_display', 'odd_ref', 'ativo'}
    assert expected.issubset(columns), (
        f"Colunas ausentes em mercados: {expected - columns}"
    )


def test_ensure_schema_complementares(db_conn):
    """Após ensure_schema(), tabela complementares existe com colunas esperadas."""
    with db_conn.cursor() as cur:
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'complementares'
            ORDER BY column_name
        """)
        columns = {row[0] for row in cur.fetchall()}

    expected = {'id', 'mercado_id', 'slug', 'nome_display', 'percentual', 'odd_ref', 'regra_validacao'}
    assert expected.issubset(columns), (
        f"Colunas ausentes em complementares: {expected - columns}"
    )


# ---------------------------------------------------------------------------
# Testes de seed data — mercados
# ---------------------------------------------------------------------------

def test_seed_mercados_over_2_5(db_conn):
    """Após ensure_schema(), mercados contém slug='over_2_5' com nome e odd corretos."""
    with db_conn.cursor() as cur:
        cur.execute("""
            SELECT slug, nome_display, odd_ref
            FROM mercados
            WHERE slug = 'over_2_5'
        """)
        row = cur.fetchone()

    assert row is not None, "Mercado 'over_2_5' não encontrado em mercados"
    slug, nome_display, odd_ref = row
    assert slug == 'over_2_5'
    assert nome_display == 'Over 2.5'
    assert odd_ref == Decimal('2.30'), f"odd_ref esperado 2.30, got {odd_ref}"


def test_seed_mercados_ambas_marcam(db_conn):
    """Após ensure_schema(), mercados contém slug='ambas_marcam' com nome e odd corretos."""
    with db_conn.cursor() as cur:
        cur.execute("""
            SELECT slug, nome_display, odd_ref
            FROM mercados
            WHERE slug = 'ambas_marcam'
        """)
        row = cur.fetchone()

    assert row is not None, "Mercado 'ambas_marcam' não encontrado em mercados"
    slug, nome_display, odd_ref = row
    assert slug == 'ambas_marcam'
    assert nome_display == 'Ambas Marcam'
    assert odd_ref == Decimal('2.10'), f"odd_ref esperado 2.10, got {odd_ref}"


# ---------------------------------------------------------------------------
# Testes de seed data — complementares
# ---------------------------------------------------------------------------

def test_seed_complementares_over_2_5_count(db_conn):
    """Após ensure_schema(), há exatamente 7 complementares para mercado over_2_5."""
    with db_conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*)
            FROM complementares c
            JOIN mercados m ON c.mercado_id = m.id
            WHERE m.slug = 'over_2_5'
        """)
        count = cur.fetchone()[0]

    assert count == 7, f"Esperado 7 complementares para over_2_5, encontrado {count}"


def test_seed_complementares_ambas_marcam_count(db_conn):
    """Após ensure_schema(), há exatamente 7 complementares para mercado ambas_marcam."""
    with db_conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*)
            FROM complementares c
            JOIN mercados m ON c.mercado_id = m.id
            WHERE m.slug = 'ambas_marcam'
        """)
        count = cur.fetchone()[0]

    assert count == 7, f"Esperado 7 complementares para ambas_marcam, encontrado {count}"


# ---------------------------------------------------------------------------
# Testes de idempotência
# ---------------------------------------------------------------------------

def test_seed_idempotent(db_conn):
    """Chamar ensure_schema() duas vezes não duplica registros."""
    # Já foi chamado uma vez no fixture — chamar novamente
    ensure_schema(db_conn)

    with db_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM mercados")
        mercados_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM complementares")
        complementares_count = cur.fetchone()[0]

    assert mercados_count == 2, f"Esperado 2 mercados, encontrado {mercados_count}"
    assert complementares_count == 14, f"Esperado 14 complementares, encontrado {complementares_count}"


# ---------------------------------------------------------------------------
# Testes de integridade dos dados
# ---------------------------------------------------------------------------

def test_seed_percentual_fracao(db_conn):
    """Complementar 'over_3_5' de over_2_5 tem percentual=0.20 (fração, não 20)."""
    with db_conn.cursor() as cur:
        cur.execute("""
            SELECT percentual
            FROM complementares
            WHERE slug = 'over_3_5'
              AND mercado_id = (SELECT id FROM mercados WHERE slug = 'over_2_5')
        """)
        row = cur.fetchone()

    assert row is not None, "Complementar 'over_3_5' do mercado 'over_2_5' não encontrado"
    percentual = row[0]
    assert percentual == Decimal('0.2000'), (
        f"Percentual esperado 0.2000 (fração), got {percentual}. "
        "Não usar 20 — deve ser 0.20"
    )


# ---------------------------------------------------------------------------
# Testes de migration Phase 09: group_id e mercado_id em signals
# ---------------------------------------------------------------------------

def test_migration_adds_group_id_column(db_conn):
    """Após ensure_schema(), tabela signals tem coluna group_id."""
    with db_conn.cursor() as cur:
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'signals' AND column_name = 'group_id'
        """)
        row = cur.fetchone()

    assert row is not None, "Coluna group_id deve existir na tabela signals após migration"


def test_migration_adds_mercado_id_column(db_conn):
    """Após ensure_schema(), tabela signals tem coluna mercado_id."""
    with db_conn.cursor() as cur:
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'signals' AND column_name = 'mercado_id'
        """)
        row = cur.fetchone()

    assert row is not None, "Coluna mercado_id deve existir na tabela signals após migration"


def test_migration_idempotent_with_new_columns(db_conn):
    """ensure_schema() chamado 2x não gera erro e colunas existem."""
    # Fixture já chamou ensure_schema() uma vez — chamar novamente
    ensure_schema(db_conn)

    with db_conn.cursor() as cur:
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'signals'
              AND column_name IN ('group_id', 'mercado_id')
            ORDER BY column_name
        """)
        columns = {row[0] for row in cur.fetchall()}

    assert 'group_id' in columns, "group_id deve existir após 2 chamadas de ensure_schema()"
    assert 'mercado_id' in columns, "mercado_id deve existir após 2 chamadas de ensure_schema()"
