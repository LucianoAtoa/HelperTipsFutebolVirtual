"""
store.py — Repository layer for HelperTips signal persistence.

Provides:
- upsert_signal(conn, data): Insert or update a signal row via ON CONFLICT
- get_stats(conn): Return (total, greens, reds, pending) counts from signals table

Design notes:
- This module is SYNC ONLY — no asyncio, no telethon imports
- The caller (listener.py) wraps calls in asyncio.to_thread() per DB-04
- Each upsert is its own committed transaction (conn.commit inside upsert_signal)
- The ON CONFLICT WHERE clause prevents overwriting a known resultado with NULL
"""


def upsert_signal(conn, data: dict) -> None:
    """
    Insert a new signal or update an existing one by message_id.

    Uses a single INSERT ... ON CONFLICT (message_id) DO UPDATE statement
    so both NewMessage and MessageEdited events flow through the same code path.

    The WHERE clause on the DO UPDATE ensures that a known resultado (GREEN/RED)
    is never overwritten with NULL when the original message is re-processed.

    Parameters
    ----------
    conn : psycopg2 connection
        An open psycopg2 connection. Caller manages its lifecycle.
    data : dict
        Signal dict as produced by parser.parse_message(). Required keys:
        message_id, liga, entrada, horario, periodo, dia_semana,
        resultado, placar, raw_text.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO signals (
                message_id, liga, entrada, horario, periodo,
                dia_semana, resultado, placar, tentativa, raw_text, received_at, updated_at
            ) VALUES (
                %(message_id)s, %(liga)s, %(entrada)s, %(horario)s, %(periodo)s,
                %(dia_semana)s, %(resultado)s, %(placar)s, %(tentativa)s, %(raw_text)s,
                NOW(), NOW()
            )
            ON CONFLICT (message_id) DO UPDATE SET
                resultado  = COALESCE(EXCLUDED.resultado, signals.resultado),
                placar     = COALESCE(EXCLUDED.placar, signals.placar),
                tentativa  = COALESCE(EXCLUDED.tentativa, signals.tentativa),
                liga       = EXCLUDED.liga,
                entrada    = EXCLUDED.entrada,
                updated_at = NOW()
            WHERE
                EXCLUDED.resultado IS NOT NULL
                OR signals.resultado IS NULL
                OR signals.resultado IS NULL
            """,
            data,
        )
    conn.commit()


def get_stats(conn) -> dict:
    """
    Return summary counts from the signals table and parse_failures table.

    Returns
    -------
    dict with keys:
        total          — total number of signals
        greens         — signals with resultado = 'GREEN'
        reds           — signals with resultado = 'RED'
        pending        — signals with resultado IS NULL (not yet resolved)
        parse_failures — total rows in parse_failures table
        coverage       — parseados / (parseados + falhas) * 100 (D-13)
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                COUNT(*)                                     AS total,
                COUNT(*) FILTER (WHERE resultado = 'GREEN') AS greens,
                COUNT(*) FILTER (WHERE resultado = 'RED')   AS reds,
                COUNT(*) FILTER (WHERE resultado IS NULL)   AS pending
            FROM signals
            """
        )
        total, greens, reds, pending = cur.fetchone()

        cur.execute("SELECT COUNT(*) FROM parse_failures")
        total_failures = cur.fetchone()[0]

    return {
        'total': total,
        'greens': greens,
        'reds': reds,
        'pending': pending,
        'parse_failures': total_failures,
        'coverage': (total / (total + total_failures) * 100) if (total + total_failures) > 0 else 100.0,
    }


def log_parse_failure(conn, raw_text: str, reason: str) -> None:
    """
    Save a message that the parser could not interpret (D-10, D-11).

    Parameters
    ----------
    conn : psycopg2 connection
        An open psycopg2 connection. Caller manages its lifecycle.
    raw_text : str
        The original message text that failed to parse.
    reason : str
        A short identifier for the failure reason (e.g. 'no_liga_match', 'empty_text').
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO parse_failures (raw_text, failure_reason)
            VALUES (%s, %s)
            """,
            (raw_text, reason),
        )
    conn.commit()
