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
                dia_semana, resultado, placar, raw_text, received_at, updated_at
            ) VALUES (
                %(message_id)s, %(liga)s, %(entrada)s, %(horario)s, %(periodo)s,
                %(dia_semana)s, %(resultado)s, %(placar)s, %(raw_text)s,
                NOW(), NOW()
            )
            ON CONFLICT (message_id) DO UPDATE SET
                resultado  = EXCLUDED.resultado,
                placar     = EXCLUDED.placar,
                liga       = EXCLUDED.liga,
                entrada    = EXCLUDED.entrada,
                updated_at = NOW()
            WHERE
                signals.resultado IS DISTINCT FROM EXCLUDED.resultado
                OR signals.resultado IS NULL
            """,
            data,
        )
    conn.commit()


def get_stats(conn) -> tuple:
    """
    Return summary counts from the signals table.

    Returns
    -------
    tuple : (total, greens, reds, pending)
        total   — total number of signals
        greens  — signals with resultado = 'GREEN'
        reds    — signals with resultado = 'RED'
        pending — signals with resultado IS NULL (not yet resolved)
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
        return cur.fetchone()
