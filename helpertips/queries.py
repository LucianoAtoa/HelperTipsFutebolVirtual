"""
queries.py — Data layer for the HelperTips dashboard.

Provides filtered SQL queries and pure-Python ROI calculation:
  - get_filtered_stats: aggregate counts with optional liga/entrada/date filters
  - get_signal_history: paginated signal rows with same filter support
  - get_distinct_values: dropdown option lists for liga and entrada fields
  - calculate_roi: Stake Fixa and Gale ROI simulation — no DB access
  - _parse_placar: convert 'X-Y' string to (int, int) tuple
  - _REGRA_VALIDATORS: dispatch dict for complementary market validation rules
  - validar_complementar: determine GREEN/RED/None for a complementary market

Design notes:
  - All SQL uses %s parameterized queries — no f-strings for values
  - get_distinct_values validates the field name against an allowlist to prevent
    SQL injection (field name cannot be parameterized in PostgreSQL)
  - calculate_roi is pure Python and has zero dependencies on DB or Dash
  - validar_complementar is pure Python with no DB dependency
  - This module is SYNC ONLY — caller wraps in asyncio.to_thread() if needed
"""

from typing import Callable

from helpertips.db import get_connection  # noqa: F401 (re-export for callers)

_ALLOWED_DISTINCT_FIELDS = frozenset({"liga", "entrada"})


def _build_where(liga=None, entrada=None, date_start=None, date_end=None):
    """
    Build a parameterized WHERE clause from optional filter args.

    Returns (where_sql: str, params: list) where where_sql starts with '1=1'
    and params contains values in the same order as %s placeholders.
    """
    conditions = ["1=1"]
    params = []

    if liga is not None:
        conditions.append("liga = %s")
        params.append(liga)

    if entrada is not None:
        conditions.append("entrada = %s")
        params.append(entrada)

    if date_start is not None:
        conditions.append("received_at::date >= %s::date")
        params.append(date_start)

    if date_end is not None:
        conditions.append("received_at::date <= %s::date")
        params.append(date_end)

    return " AND ".join(conditions), params


def get_filtered_stats(conn, liga=None, entrada=None, date_start=None, date_end=None) -> dict:
    """
    Return aggregate signal counts with optional filters.

    Parameters
    ----------
    conn : psycopg2 connection
        An open psycopg2 connection. Caller manages its lifecycle.
    liga : str | None
        Filter to a specific liga name.
    entrada : str | None
        Filter to a specific entrada (betting market).
    date_start : str | None
        ISO date string (YYYY-MM-DD). Signals on or after this date are included.
    date_end : str | None
        ISO date string (YYYY-MM-DD). Signals on or before this date are included.

    Returns
    -------
    dict with keys:
        total   — total signals matching filters
        greens  — signals with resultado = 'GREEN'
        reds    — signals with resultado = 'RED'
        pending — signals with resultado IS NULL
    """
    where, params = _build_where(liga=liga, entrada=entrada,
                                 date_start=date_start, date_end=date_end)

    sql = f"""
        SELECT
            COUNT(*)                                     AS total,
            COUNT(*) FILTER (WHERE resultado = 'GREEN') AS greens,
            COUNT(*) FILTER (WHERE resultado = 'RED')   AS reds,
            COUNT(*) FILTER (WHERE resultado IS NULL)   AS pending
        FROM signals
        WHERE {where}
    """

    with conn.cursor() as cur:
        cur.execute(sql, params)
        total, greens, reds, pending = cur.fetchone()

    return {
        "total": int(total),
        "greens": int(greens),
        "reds": int(reds),
        "pending": int(pending),
    }


def get_signal_history(conn, liga=None, entrada=None, date_start=None,
                       date_end=None, limit=500) -> list:
    """
    Return paginated signal rows ordered by received_at DESC.

    Parameters
    ----------
    conn : psycopg2 connection
        An open psycopg2 connection. Caller manages its lifecycle.
    liga : str | None
        Optional liga filter.
    entrada : str | None
        Optional entrada filter.
    date_start : str | None
        ISO date string for start of range (inclusive).
    date_end : str | None
        ISO date string for end of range (inclusive).
    limit : int
        Maximum number of rows to return (default 500).

    Returns
    -------
    list[dict]
        Each dict has keys: liga, entrada, horario, resultado, placar,
        tentativa, received_at. Ordered received_at DESC.
    """
    where, params = _build_where(liga=liga, entrada=entrada,
                                 date_start=date_start, date_end=date_end)
    params.append(limit)

    sql = f"""
        SELECT liga, entrada, horario, resultado, placar, tentativa, received_at
        FROM signals
        WHERE {where}
        ORDER BY received_at DESC
        LIMIT %s
    """

    with conn.cursor() as cur:
        cur.execute(sql, params)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

    return [dict(zip(columns, row)) for row in rows]


def get_distinct_values(conn, field: str) -> list:
    """
    Return sorted unique non-NULL values for a given field.

    Parameters
    ----------
    conn : psycopg2 connection
        An open psycopg2 connection. Caller manages its lifecycle.
    field : str
        Column name — must be 'liga' or 'entrada'. Any other value raises
        ValueError to prevent SQL injection via field name interpolation.

    Returns
    -------
    list[str]
        Sorted list of unique non-NULL values.

    Raises
    ------
    ValueError
        If field is not in the allowlist {"liga", "entrada"}.
    """
    if field not in _ALLOWED_DISTINCT_FIELDS:
        raise ValueError(
            f"Invalid field '{field}'. Must be one of: {sorted(_ALLOWED_DISTINCT_FIELDS)}"
        )

    sql = f"SELECT DISTINCT {field} FROM signals WHERE {field} IS NOT NULL ORDER BY {field}"

    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()

    return [row[0] for row in rows]


def calculate_roi(signals: list, stake: float, odd: float, gale_on: bool) -> dict:
    """
    Compute ROI for a list of resolved signals.

    Pure Python — no database access. Pending signals (resultado=None) are skipped.

    Parameters
    ----------
    signals : list[dict]
        List of signal dicts. Each must have 'resultado' (str|None) and
        'tentativa' (int|None). Additional keys are ignored.
    stake : float
        Base stake amount (e.g. 10.0 for R$10).
    odd : float
        Decimal odd (e.g. 1.90).
    gale_on : bool
        If False: Stake Fixa — same stake on every signal regardless of tentativa.
        If True: Gale — stake doubles on each failed tentativa.
                  GREEN at tentativa N: total invested = stake * (2^N - 1).
                  Profit = stake * 2^(N-1) * (odd - 1) - stake * (2^(N-1) - 1).
                  RED (all tentativas failed): invested = stake * (2^tentativa - 1),
                  net = -invested.

    Returns
    -------
    dict with keys:
        profit         — total net profit (positive = gain, negative = loss)
        roi_pct        — profit / total_invested * 100 (0.0 if no investment)
        total_invested — total amount staked across all resolved signals
    """
    total_invested = 0.0
    profit = 0.0

    for signal in signals:
        resultado = signal.get("resultado")

        # Skip pending signals
        if resultado is None:
            continue

        tentativa = signal.get("tentativa") or 1

        if not gale_on:
            # Stake Fixa: same stake every time
            invested = stake
            if resultado == "GREEN":
                net = stake * (odd - 1)
            else:
                net = -stake
        else:
            # Gale: stake doubles on each attempt
            # Total invested across all N attempts: stake * (2^N - 1)
            # The Nth attempt uses stake * 2^(N-1)
            accumulated_stake = stake * (2 ** tentativa - 1)
            winning_stake = stake * (2 ** (tentativa - 1))
            invested = accumulated_stake

            if resultado == "GREEN":
                # Win on last attempt: profit minus all prior losses
                win_profit = winning_stake * (odd - 1)
                prior_losses = accumulated_stake - winning_stake
                net = win_profit - prior_losses
            else:
                # RED: lost all attempts
                net = -accumulated_stake

        total_invested += invested
        profit += net

    roi_pct = (profit / total_invested * 100) if total_invested > 0 else 0.0

    return {
        "profit": round(profit, 10),
        "roi_pct": round(roi_pct, 10),
        "total_invested": round(total_invested, 10),
    }


# ---------------------------------------------------------------------------
# Complementary market validation — pure Python, no DB
# ---------------------------------------------------------------------------


def _parse_placar(placar: str | None) -> tuple[int, int] | None:
    """
    Parse a score string 'X-Y' into a (home, away) integer tuple.

    Returns None for any invalid input (None, empty string, non-numeric,
    wrong segment count, etc.). Never raises.
    """
    if not placar:
        return None
    try:
        parts = placar.split("-")
        if len(parts) != 2:
            return None
        return (int(parts[0]), int(parts[1]))
    except (ValueError, AttributeError):
        return None


# Dispatch dict: maps regra name -> validator(casa, fora) -> bool
_REGRA_VALIDATORS: dict[str, Callable[[int, int], bool]] = {
    "over_3_5": lambda casa, fora: (casa + fora) > 3.5,
    "over_5_plus": lambda casa, fora: (casa + fora) >= 6,
    # empate_3_3_4_4: must be a draw AND total goals in (6, 8) — excludes 2-4, 4-2, 1-5, etc.
    "empate_3_3_4_4": lambda casa, fora: casa == fora and (casa + fora) in (6, 8),
    "gols_casa_4": lambda casa, fora: casa == 4,
    "gols_fora_4": lambda casa, fora: fora == 4,
    "gols_casa_5_plus": lambda casa, fora: casa >= 5,
    "gols_fora_5_plus": lambda casa, fora: fora >= 5,
}


def validar_complementar(
    regra: str,
    placar: str | None,
    resultado_principal: str | None,
) -> str | None:
    """
    Determine GREEN/RED/None for a complementary market entry.

    Rules (applied in order):
    - If resultado_principal is None  -> return None  (principal still pending, D-09)
    - If resultado_principal == 'RED' -> return 'RED' (principal lost, D-08)
    - If placar is None               -> return 'RED' (no score available, conservative)
    - If placar fails to parse        -> return 'RED' (conservative)
    - If regra is unknown             -> return 'RED' (conservative)
    - Otherwise: return 'GREEN' if validator(casa, fora) else 'RED'

    Parameters
    ----------
    regra : str
        Key in _REGRA_VALIDATORS (e.g. 'over_3_5').
    placar : str | None
        Score string in 'X-Y' format, or None if not yet available.
    resultado_principal : str | None
        'GREEN', 'RED', or None for the principal signal outcome.

    Returns
    -------
    'GREEN', 'RED', or None
    """
    # D-09: principal still pending
    if resultado_principal is None:
        return None

    # D-08: principal lost — complementar always loses
    if resultado_principal == "RED":
        return "RED"

    # No score yet — conservative fallback
    if placar is None:
        return "RED"

    parsed = _parse_placar(placar)
    if parsed is None:
        return "RED"

    validator = _REGRA_VALIDATORS.get(regra)
    if validator is None:
        return "RED"

    casa, fora = parsed
    return "GREEN" if validator(casa, fora) else "RED"
