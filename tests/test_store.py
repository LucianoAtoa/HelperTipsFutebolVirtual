"""
test_store.py — Integration tests for the store repository layer.

These tests require a real PostgreSQL database configured via .env.
If the database is not available, tests will be skipped with a clear message.

Run with:
    python3 -m pytest tests/test_store.py -x -v
"""
import os
import pytest

# Skip all tests if DB imports fail or connection not available
try:
    from db import get_connection, ensure_schema
    from store import upsert_signal, get_stats
    _IMPORTS_OK = True
except ImportError as e:
    _IMPORTS_OK = False
    _IMPORT_ERROR = str(e)


def _make_signal(message_id: int, resultado=None, placar=None) -> dict:
    """Helper to build a minimal valid signal dict."""
    return {
        "message_id": message_id,
        "liga": "Euro League",
        "entrada": "Over 1.5 Gols",
        "horario": "14:30",
        "periodo": None,
        "dia_semana": 0,
        "resultado": resultado,
        "placar": placar,
        "raw_text": f"LIGA: Euro League\nEntrada: Over 1.5 Gols\nHorario: 14:30",
    }


@pytest.fixture
def db_conn():
    """
    Fixture that provides a live psycopg2 connection to the helpertips database.
    Ensures the schema exists and cleans up signals between tests.
    """
    if not _IMPORTS_OK:
        pytest.skip(f"store or db import failed: {_IMPORT_ERROR}")

    try:
        conn = get_connection()
    except Exception as exc:
        pytest.skip(f"PostgreSQL not available: {exc}")

    ensure_schema(conn)

    yield conn

    # Teardown: remove test data
    with conn.cursor() as cur:
        cur.execute("DELETE FROM signals")
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# upsert_signal tests
# ---------------------------------------------------------------------------


def test_upsert_inserts_new_signal(db_conn):
    """INSERT path: new signal row is created with correct field values."""
    signal = _make_signal(message_id=1001)
    upsert_signal(db_conn, signal)

    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT liga, entrada, horario, raw_text FROM signals WHERE message_id = %s",
            (1001,),
        )
        row = cur.fetchone()

    assert row is not None, "Row should exist after upsert"
    assert row[0] == "Euro League"
    assert row[1] == "Over 1.5 Gols"
    assert row[2] == "14:30"
    assert "LIGA: Euro League" in row[3]


def test_upsert_updates_resultado(db_conn):
    """UPDATE path: upsert with same message_id updates resultado and placar."""
    signal = _make_signal(message_id=1002, resultado=None, placar=None)
    upsert_signal(db_conn, signal)

    # Now the result comes in via a MessageEdited event
    updated = _make_signal(message_id=1002, resultado="GREEN", placar="2-1")
    upsert_signal(db_conn, updated)

    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT resultado, placar FROM signals WHERE message_id = %s",
            (1002,),
        )
        row = cur.fetchone()

    assert row is not None
    assert row[0] == "GREEN", f"Expected GREEN, got {row[0]}"
    assert row[1] == "2-1", f"Expected 2-1, got {row[1]}"


def test_upsert_no_duplicate_rows(db_conn):
    """Upserting the same message_id twice must not create duplicate rows."""
    signal = _make_signal(message_id=1003)
    upsert_signal(db_conn, signal)
    upsert_signal(db_conn, signal)  # Second call — same ID

    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM signals WHERE message_id = %s",
            (1003,),
        )
        count = cur.fetchone()[0]

    assert count == 1, f"Expected 1 row, got {count}"


def test_upsert_preserves_original_on_null_result_update(db_conn):
    """
    If a signal already has resultado='GREEN', a re-upsert with resultado=None
    must NOT overwrite the known result (the WHERE clause protects this).
    """
    # Insert with a known result
    signal = _make_signal(message_id=1004, resultado="GREEN", placar="3-0")
    upsert_signal(db_conn, signal)

    # Re-upsert with resultado=None (simulates the original message being re-processed)
    original = _make_signal(message_id=1004, resultado=None, placar=None)
    upsert_signal(db_conn, original)

    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT resultado, placar FROM signals WHERE message_id = %s",
            (1004,),
        )
        row = cur.fetchone()

    assert row[0] == "GREEN", f"resultado should remain GREEN, got {row[0]}"
    assert row[1] == "3-0", f"placar should remain 3-0, got {row[1]}"


# ---------------------------------------------------------------------------
# get_stats tests
# ---------------------------------------------------------------------------


def test_get_stats_empty_table(db_conn):
    """get_stats on an empty signals table returns (0, 0, 0, 0)."""
    result = get_stats(db_conn)
    assert result == (0, 0, 0, 0), f"Expected (0,0,0,0), got {result}"


def test_get_stats_with_data(db_conn):
    """get_stats returns correct (total, greens, reds, pending) counts."""
    upsert_signal(db_conn, _make_signal(message_id=2001, resultado="GREEN"))
    upsert_signal(db_conn, _make_signal(message_id=2002, resultado="RED"))
    upsert_signal(db_conn, _make_signal(message_id=2003, resultado=None))

    result = get_stats(db_conn)
    total, greens, reds, pending = result

    assert total == 3, f"Expected total=3, got {total}"
    assert greens == 1, f"Expected greens=1, got {greens}"
    assert reds == 1, f"Expected reds=1, got {reds}"
    assert pending == 1, f"Expected pending=1, got {pending}"
