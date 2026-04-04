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
  - get_complementares_config: query complementary market config for a given mercado slug
  - get_mercado_config: query market config (id, slug, odd_ref, ativo) by slug
  - get_signals_com_placar: resolved signals with mercado_slug for P&L calculation (FIN-01)
  - calculate_roi_complementares: pure Python ROI for complementary markets with Gale support
  - get_heatmap_data: win rate by hour x day-of-week matrix (24x7) for go.Heatmap
  - get_winrate_by_dow: win rate per day-of-week list for bar chart
  - calculate_equity_curve: bankroll curve for Stake Fixa and Gale (pure Python, no DB)
  - calculate_streaks: current and historical max streaks (pure Python, no DB)
  - get_gale_analysis: recovery rate by gale level (tentativa), excluding NULL
  - get_volume_by_day: signal count grouped by day for bar chart
  - get_cross_dimensional: win rate breakdown by (liga, entrada), ordered by win_rate DESC
  - get_parse_failures_detail: last N parse failures for modal display (OPER-01)
  - get_winrate_by_periodo: win rate grouped by periodo (1T/2T/FT), excluding NULL (ANAL-03)

Design notes:
  - All SQL uses %s parameterized queries — no f-strings for values
  - get_distinct_values validates the field name against an allowlist to prevent
    SQL injection (field name cannot be parameterized in PostgreSQL)
  - calculate_roi and calculate_roi_complementares are pure Python with zero DB or Dash deps
  - validar_complementar is pure Python with no DB dependency
  - This module is SYNC ONLY — caller wraps in asyncio.to_thread() if needed
"""

from typing import Callable

from helpertips.db import get_connection  # noqa: F401 (re-export for callers)

_ALLOWED_DISTINCT_FIELDS = frozenset({"liga", "entrada"})


def _build_where(liga=None, entrada=None, date_start=None, date_end=None, mercado_id=None):
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

    if mercado_id is not None:
        conditions.append("mercado_id = %s")
        params.append(mercado_id)

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
        Each dict has keys: id, liga, entrada, horario, resultado, placar,
        tentativa, received_at. Ordered received_at DESC.
    """
    where, params = _build_where(liga=liga, entrada=entrada,
                                 date_start=date_start, date_end=date_end)
    params.append(limit)

    sql = f"""
        SELECT id, liga, entrada, horario, resultado, placar, tentativa, received_at
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

        if resultado == "RED":
            # RED: all 4 attempts were made and lost
            if not gale_on:
                invested = stake * 4
            else:
                invested = stake * (2 ** 4 - 1)  # 10+20+40+80 = 150
            net = -invested
        elif not gale_on:
            # GREEN Stake Fixa: same stake every time
            invested = stake
            net = stake * (odd - 1)
        else:
            # GREEN Gale: stake doubles on each attempt
            accumulated_stake = stake * (2 ** tentativa - 1)
            winning_stake = stake * (2 ** (tentativa - 1))
            invested = accumulated_stake
            win_profit = winning_stake * (odd - 1)
            prior_losses = accumulated_stake - winning_stake
            net = win_profit - prior_losses

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
    "over_5_plus": lambda casa, fora: (casa + fora) >= 5,
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


# ---------------------------------------------------------------------------
# Complementary market config query
# ---------------------------------------------------------------------------


def get_complementares_config(conn, mercado_slug: str) -> list[dict]:
    """
    Retorna a lista de mercados complementares para um slug de mercado principal.

    Executa um JOIN entre complementares e mercados, filtrando pelo slug do mercado
    principal e garantindo que o mercado esteja ativo.

    Parametros
    ----------
    conn : psycopg2 connection
        Conexao aberta. O chamador gerencia o ciclo de vida.
    mercado_slug : str
        Slug do mercado principal (ex: 'over_2_5', 'ambas_marcam').

    Retorna
    -------
    list[dict]
        Lista de dicts com chaves: id, slug, nome_display, percentual, odd_ref, regra_validacao.
        Ordenada por percentual DESC, slug ASC.
        Lista vazia se o mercado nao existir ou nao estiver ativo.
    """
    sql = """
        SELECT c.id, c.slug, c.nome_display, c.percentual, c.odd_ref, c.regra_validacao
        FROM complementares c
        JOIN mercados m ON c.mercado_id = m.id
        WHERE m.slug = %s AND m.ativo = TRUE
        ORDER BY c.percentual DESC, c.slug
    """

    with conn.cursor() as cur:
        cur.execute(sql, (mercado_slug,))
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

    return [dict(zip(columns, row)) for row in rows]


# ---------------------------------------------------------------------------
# Market config query
# ---------------------------------------------------------------------------


def get_mercado_config(conn, mercado_slug: str) -> dict | None:
    """
    Retorna config de um mercado por slug. None se nao existir ou inativo.

    Parametros
    ----------
    conn : psycopg2 connection
        Conexao aberta. O chamador gerencia o ciclo de vida.
    mercado_slug : str
        Slug do mercado (ex: 'over_2_5', 'ambas_marcam').

    Retorna
    -------
    dict | None
        Dict com chaves: id, slug, nome_display, odd_ref, ativo.
        None se o mercado nao existir ou estiver inativo.
    """
    sql = """
        SELECT id, slug, nome_display, odd_ref, ativo
        FROM mercados
        WHERE slug = %s AND ativo = TRUE
    """
    with conn.cursor() as cur:
        cur.execute(sql, (mercado_slug,))
        row = cur.fetchone()
    if row is None:
        return None
    columns = ["id", "slug", "nome_display", "odd_ref", "ativo"]
    return dict(zip(columns, row))


# ---------------------------------------------------------------------------
# Signals com placar e mercado_slug — para calculo P&L (FIN-01)
# ---------------------------------------------------------------------------


def get_signals_com_placar(
    conn,
    liga=None, entrada=None, date_start=None, date_end=None, mercado_id=None,
) -> list[dict]:
    """
    Retorna sinais resolvidos (GREEN/RED) com mercado_id e mercado_slug.

    Ordenado por received_at ASC para calculo cronologico de P&L.
    Inclui sinais com placar=NULL (REDs sem placar registrado).

    Parametros
    ----------
    conn : psycopg2 connection
        Conexao aberta. O chamador gerencia o ciclo de vida.
    liga : str | None
        Filtro opcional por liga.
    entrada : str | None
        Filtro opcional por entrada.
    date_start : str | None
        Data inicio ISO (YYYY-MM-DD), inclusiva.
    date_end : str | None
        Data fim ISO (YYYY-MM-DD), inclusiva.
    mercado_id : int | None
        Filtro opcional por mercado. None retorna todos os mercados (backward compat).

    Retorna
    -------
    list[dict]
        Cada dict tem chaves: id, resultado, placar, tentativa, mercado_id,
        mercado_slug, entrada, liga, received_at. Ordenado por received_at ASC.
    """
    where, params = _build_where(
        liga=liga, entrada=entrada,
        date_start=date_start, date_end=date_end,
        mercado_id=mercado_id,
    )
    sql = f"""
        SELECT s.id, s.resultado, s.placar, s.tentativa,
               s.mercado_id, m.slug AS mercado_slug, s.entrada, s.liga, s.received_at
        FROM signals s
        LEFT JOIN mercados m ON s.mercado_id = m.id
        WHERE s.resultado IN ('GREEN', 'RED') AND {where}
        ORDER BY s.received_at ASC
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
    return [dict(zip(columns, row)) for row in rows]


# ---------------------------------------------------------------------------
# ROI de mercados complementares — puro Python, sem DB
# ---------------------------------------------------------------------------


def calculate_roi_complementares(
    signals: list,
    complementares_config: list[dict],
    stake: float,
    gale_on: bool,
) -> dict:
    """
    Calcula o ROI para mercados complementares.

    Puro Python — sem acesso ao banco. Sinais pendentes (resultado=None) sao ignorados.

    A logica de Gale para complementares segue o mesmo padrao de calculate_roi(),
    mas o stake base de cada complementar e `stake * percentual` em vez de `stake`.

    Parametros
    ----------
    signals : list[dict]
        Lista de dicts de sinais. Cada um deve ter 'resultado' (str|None),
        'placar' (str|None) e 'tentativa' (int|None).
    complementares_config : list[dict]
        Config dos complementares — formato retornado por get_complementares_config().
        Cada dict: id, slug, nome_display, percentual, odd_ref, regra_validacao.
        percentual e odd_ref podem ser Decimal (do PostgreSQL) — convertidos para float
        internamente.
    stake : float
        Stake base do sinal principal (ex: 100.0 para R$100).
    gale_on : bool
        False: Stake Fixa — stake_comp = stake * percentual em todos os sinais.
        True: Gale — stake dobra em cada tentativa.
              stake_comp_winning = stake * 2^(N-1) * percentual
              stake_comp_acumulado = stake * (2^N - 1) * percentual

    Retorna
    -------
    dict com chaves:
        profit         — lucro total liquido
        roi_pct        — profit / total_invested * 100 (0.0 se sem investimento)
        total_invested — total apostado em todos os complementares resolvidos
        por_mercado    — lista de dicts com: slug, nome_display, greens, reds, lucro, investido
    """
    # Filtra apenas sinais resolvidos (ignora pendentes)
    resolved = [s for s in signals if s.get("resultado") is not None]

    if not resolved or not complementares_config:
        return {"profit": 0.0, "roi_pct": 0.0, "total_invested": 0.0, "por_mercado": []}

    # Acumuladores por slug de complementar
    per_comp: dict[str, dict] = {}
    for comp in complementares_config:
        per_comp[comp["slug"]] = {
            "slug": comp["slug"],
            "nome_display": comp["nome_display"],
            "greens": 0,
            "reds": 0,
            "lucro": 0.0,
            "investido": 0.0,
        }

    total_invested = 0.0
    profit = 0.0

    for signal in resolved:
        tentativa = signal.get("tentativa") or 1

        for comp in complementares_config:
            # Converte Decimal do PostgreSQL para float antes de calcular
            percentual = float(comp["percentual"])
            odd_ref = float(comp["odd_ref"])
            slug = comp["slug"]

            resultado_comp = validar_complementar(
                comp["regra_validacao"],
                signal.get("placar"),
                signal.get("resultado"),
            )

            stake_comp = stake * percentual

            if resultado_comp != "GREEN":
                # RED: all 4 attempts lost
                if not gale_on:
                    invested = stake_comp * 4
                else:
                    invested = stake * (2 ** 4 - 1) * percentual
                net = -invested
                per_comp[slug]["reds"] += 1
            elif not gale_on:
                # GREEN Stake Fixa
                invested = stake_comp
                net = stake_comp * (odd_ref - 1)
                per_comp[slug]["greens"] += 1
            else:
                # GREEN Gale
                accumulated_stake = stake * (2 ** tentativa - 1) * percentual
                winning_stake = stake * (2 ** (tentativa - 1)) * percentual
                invested = accumulated_stake
                prior_losses = accumulated_stake - winning_stake
                net = winning_stake * (odd_ref - 1) - prior_losses
                per_comp[slug]["greens"] += 1

            per_comp[slug]["lucro"] += net
            per_comp[slug]["investido"] += invested
            total_invested += invested
            profit += net

    roi_pct = (profit / total_invested * 100) if total_invested > 0 else 0.0

    return {
        "profit": round(profit, 10),
        "roi_pct": round(roi_pct, 10),
        "total_invested": round(total_invested, 10),
        "por_mercado": list(per_comp.values()),
    }


# ---------------------------------------------------------------------------
# P&L por entrada — puro Python, sem DB (FIN-02)
# ---------------------------------------------------------------------------


def calculate_pl_por_entrada(
    signals: list[dict],
    complementares_por_mercado: dict[str, list[dict]],
    stake: float,
    odd_por_mercado: dict[str, float],
    gale_on: bool,
) -> list[dict]:
    """
    Calcula P&L detalhado por sinal individual.

    Parametros
    ----------
    signals : list[dict]
        Sinais de get_signals_com_placar(). Cada dict: resultado, placar, tentativa, mercado_slug.
    complementares_por_mercado : dict[str, list[dict]]
        Mapa mercado_slug -> list[dict config complementar] (de get_complementares_config).
    stake : float
        Stake base do principal.
    odd_por_mercado : dict[str, float]
        Mapa mercado_slug -> odd de referencia do principal (ex: {"over_2_5": 2.30}).
    gale_on : bool
        Se True, aplica Gale progressivo (1x, 2x, 4x, 8x).

    Retorna
    -------
    list[dict] com uma linha por sinal resolvido:
        mercado_slug, resultado, tentativa, placar, liga, entrada,
        investido_principal, retorno_principal, lucro_principal,
        investido_comp, retorno_comp, lucro_comp,
        investido_total, lucro_total
    """
    resultado_lista = []

    for signal in signals:
        resultado = signal.get("resultado")

        # Ignorar sinais pendentes
        if resultado is None:
            continue

        tentativa = signal.get("tentativa") or 1
        mercado_slug = signal.get("mercado_slug") or "over_2_5"
        odd = odd_por_mercado.get(mercado_slug, 2.30)

        # Calculo principal (replicando formula exata de calculate_roi)
        if resultado == "RED":
            # RED: all 4 attempts lost
            if gale_on:
                investido_principal = stake * (2 ** 4 - 1)
            else:
                investido_principal = stake * 4
            retorno_principal = 0.0
            lucro_principal = -investido_principal
        elif gale_on:
            accumulated_stake = stake * (2 ** tentativa - 1)
            winning_stake = stake * (2 ** (tentativa - 1))
            investido_principal = accumulated_stake
            retorno_principal = winning_stake * odd
            lucro_principal = winning_stake * (odd - 1) - (accumulated_stake - winning_stake)
        else:
            investido_principal = stake
            retorno_principal = stake * odd
            lucro_principal = stake * (odd - 1)

        # Calculo complementares (replicando logica de calculate_roi_complementares)
        comps = complementares_por_mercado.get(mercado_slug, [])
        investido_comp = 0.0
        retorno_comp = 0.0
        lucro_comp = 0.0

        for comp in comps:
            percentual = float(comp["percentual"])
            odd_ref = float(comp["odd_ref"])

            resultado_comp = validar_complementar(
                comp["regra_validacao"],
                signal.get("placar"),
                signal.get("resultado"),
            )

            stake_comp = stake * percentual

            if resultado_comp != "GREEN":
                # RED: all 4 attempts lost
                if gale_on:
                    invested_comp = stake * (2 ** 4 - 1) * percentual
                else:
                    invested_comp = stake_comp * 4
                ret_comp = 0.0
                net_comp = -invested_comp
            elif gale_on:
                acc_comp = stake * (2 ** tentativa - 1) * percentual
                win_comp = stake * (2 ** (tentativa - 1)) * percentual
                invested_comp = acc_comp
                ret_comp = win_comp * odd_ref
                net_comp = win_comp * (odd_ref - 1) - (acc_comp - win_comp)
            else:
                invested_comp = stake_comp
                ret_comp = stake_comp * odd_ref
                net_comp = stake_comp * (odd_ref - 1)

            investido_comp += invested_comp
            retorno_comp += ret_comp
            lucro_comp += net_comp

        resultado_lista.append({
            "mercado_slug": mercado_slug,
            "resultado": resultado,
            "tentativa": tentativa,
            "placar": signal.get("placar"),
            "liga": signal.get("liga"),
            "entrada": signal.get("entrada"),
            "investido_principal": round(investido_principal, 2),
            "retorno_principal": round(retorno_principal, 2),
            "lucro_principal": round(lucro_principal, 2),
            "investido_comp": round(investido_comp, 2),
            "retorno_comp": round(retorno_comp, 2),
            "lucro_comp": round(lucro_comp, 2),
            "investido_total": round(investido_principal + investido_comp, 2),
            "lucro_total": round(lucro_principal + lucro_comp, 2),
        })

    return resultado_lista


# ---------------------------------------------------------------------------
# Fase 4: Pagina de Detalhe do Sinal — funcoes de dados individuais (SIG-02..06)
# ---------------------------------------------------------------------------


def get_sinal_detalhado(conn, signal_id: int) -> dict | None:
    """
    Busca sinal completo por ID com JOIN em mercados.

    Parametros
    ----------
    conn : psycopg2 connection
        Conexao aberta. O chamador gerencia o ciclo de vida.
    signal_id : int
        ID do sinal a buscar.

    Retorna
    -------
    dict com keys [id, liga, entrada, resultado, placar, tentativa, received_at,
    mercado_id, mercado_slug] ou None se nao encontrado.
    """
    sql = """
        SELECT s.id, s.liga, s.entrada, s.resultado, s.placar,
               s.tentativa, s.received_at, s.mercado_id,
               m.slug AS mercado_slug
        FROM signals s
        LEFT JOIN mercados m ON s.mercado_id = m.id
        WHERE s.id = %s
    """
    with conn.cursor() as cur:
        cur.execute(sql, (signal_id,))
        row = cur.fetchone()
    if row is None:
        return None
    columns = [
        "id", "liga", "entrada", "resultado", "placar",
        "tentativa", "received_at", "mercado_id", "mercado_slug",
    ]
    return dict(zip(columns, row))


def calculate_pl_detalhado_por_sinal(
    sinal: dict,
    complementares_config: list[dict],
    stake: float,
    odd_principal: float,
    gale_on: bool,
) -> dict:
    """
    Calcula P&L com breakdown individual por complementar para um unico sinal.

    Parametros
    ----------
    sinal : dict
        Sinal com keys: resultado, placar, tentativa, mercado_slug.
    complementares_config : list[dict]
        Lista de configs de complementares (nome_display, percentual, odd_ref, regra_validacao).
    stake : float
        Stake base do principal.
    odd_principal : float
        Odd de referencia do mercado principal.
    gale_on : bool
        Se True, aplica Gale progressivo (1x, 2x, 4x, 8x).

    Retorna
    -------
    dict com:
        principal  : dict com keys [investido, retorno, lucro, resultado, stake_efetiva]
        complementares : list[dict] cada um com keys [nome, odd, stake, resultado, lucro, investido, retorno]
        totais     : dict com keys [investido, retorno, lucro]
    """
    resultado = sinal.get("resultado")
    tentativa = sinal.get("tentativa") or 1
    placar = sinal.get("placar")

    # --- Principal ---
    if resultado == "RED":
        # RED: all 4 attempts lost
        if gale_on:
            investido_principal = stake * (2 ** 4 - 1)
            stake_efetiva = stake * (2 ** 3)
        else:
            investido_principal = stake * 4
            stake_efetiva = stake
        retorno_principal = 0.0
        lucro_principal = -investido_principal
    elif gale_on:
        accumulated_stake = stake * (2 ** tentativa - 1)
        winning_stake = stake * (2 ** (tentativa - 1))
        investido_principal = accumulated_stake
        stake_efetiva = winning_stake
        retorno_principal = winning_stake * odd_principal
        lucro_principal = winning_stake * (odd_principal - 1) - (accumulated_stake - winning_stake)
    else:
        investido_principal = stake
        stake_efetiva = stake
        retorno_principal = stake * odd_principal
        lucro_principal = stake * (odd_principal - 1)

    principal = {
        "odd": round(odd_principal, 2),
        "investido": round(investido_principal, 2),
        "retorno": round(retorno_principal, 2),
        "lucro": round(lucro_principal, 2),
        "resultado": resultado,
        "stake_efetiva": round(stake_efetiva, 2),
    }

    # --- Complementares ---
    complementares = []
    placar_disponivel = placar is not None

    for comp in complementares_config:
        percentual = float(comp["percentual"])
        odd_ref = float(comp["odd_ref"])
        nome = comp["nome_display"]

        if not placar_disponivel:
            # Placar ausente — complementar nao pode ser validado
            complementares.append({
                "nome": nome,
                "odd": odd_ref,
                "stake": round(stake * percentual, 2),
                "resultado": "N/A",
                "lucro": 0.0,
                "investido": 0.0,
                "retorno": 0.0,
            })
            continue

        resultado_comp = validar_complementar(
            comp["regra_validacao"],
            placar,
            resultado,
        )

        if resultado_comp is None:
            # Principal pendente — complementar pendente
            complementares.append({
                "nome": nome,
                "odd": odd_ref,
                "stake": round(stake * percentual, 2),
                "resultado": "N/A",
                "lucro": 0.0,
                "investido": 0.0,
                "retorno": 0.0,
            })
            continue

        stake_comp = stake * percentual

        if resultado_comp != "GREEN":
            # RED: all 4 attempts lost
            if gale_on:
                invested_comp = stake * (2 ** 4 - 1) * percentual
            else:
                invested_comp = stake_comp * 4
            ret_comp = 0.0
            net_comp = -invested_comp
        elif gale_on:
            acc_comp = stake * (2 ** tentativa - 1) * percentual
            win_comp = stake * (2 ** (tentativa - 1)) * percentual
            invested_comp = acc_comp
            ret_comp = win_comp * odd_ref
            net_comp = win_comp * (odd_ref - 1) - (acc_comp - win_comp)
        else:
            invested_comp = stake_comp
            ret_comp = stake_comp * odd_ref
            net_comp = stake_comp * (odd_ref - 1)

        complementares.append({
            "nome": nome,
            "odd": odd_ref,
            "stake": round(stake * percentual, 2),
            "resultado": resultado_comp,
            "lucro": round(net_comp, 2),
            "investido": round(invested_comp, 2),
            "retorno": round(ret_comp, 2),
        })

    # --- Totais ---
    total_investido = round(
        principal["investido"] + sum(c["investido"] for c in complementares), 2
    )
    total_retorno = round(
        principal["retorno"] + sum(c["retorno"] for c in complementares), 2
    )
    total_lucro = round(
        principal["lucro"] + sum(c["lucro"] for c in complementares), 2
    )

    return {
        "principal": principal,
        "complementares": complementares,
        "totais": {
            "investido": total_investido,
            "retorno": total_retorno,
            "lucro": total_lucro,
        },
    }


# ---------------------------------------------------------------------------
# Fase 3: Analytics Depth — novas funcoes de dados temporais e equity/streaks
# ---------------------------------------------------------------------------


def get_heatmap_data(conn, liga=None, entrada=None, date_start=None, date_end=None) -> dict:
    """
    Win rate por hora do dia x dia da semana. Retorna {z, x, y} para go.Heatmap.

    Parametros
    ----------
    conn : psycopg2 connection
        Conexao aberta. O chamador gerencia o ciclo de vida.
    liga : str | None
        Filtro opcional de liga.
    entrada : str | None
        Filtro opcional de entrada.
    date_start : str | None
        Data inicial ISO (YYYY-MM-DD), inclusiva.
    date_end : str | None
        Data final ISO (YYYY-MM-DD), inclusiva.

    Retorna
    -------
    dict com chaves:
        z — matriz 24x7 (hora x dia) com win_rate (0-100) ou None para celulas sem dados
        x — lista de 7 nomes de dias: ["Dom","Seg","Ter","Qua","Qui","Sex","Sab"]
        y — lista de 24 horas: ["00h","01h",...,"23h"]
    """
    where, params = _build_where(liga=liga, entrada=entrada,
                                 date_start=date_start, date_end=date_end)
    sql = f"""
        SELECT
            EXTRACT(HOUR FROM received_at)::INT AS hora,
            EXTRACT(DOW FROM received_at)::INT  AS dia,
            COUNT(*) FILTER (WHERE resultado = 'GREEN') AS greens,
            COUNT(*) FILTER (WHERE resultado IN ('GREEN', 'RED')) AS total
        FROM signals
        WHERE resultado IN ('GREEN', 'RED') AND {where}
        GROUP BY 1, 2
        ORDER BY 1, 2
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    z = [[None] * 7 for _ in range(24)]
    for hora, dia, greens, total in rows:
        z[hora][dia] = round(greens / total * 100, 1) if total > 0 else None

    dias = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sab"]
    horas = [f"{h:02d}h" for h in range(24)]
    return {"z": z, "x": dias, "y": horas}


def get_winrate_by_dow(conn, liga=None, entrada=None, date_start=None, date_end=None) -> list:
    """
    Win rate por dia da semana. Retorna lista de dicts {dia, dia_nome, greens, total, win_rate}.

    Parametros
    ----------
    conn : psycopg2 connection
        Conexao aberta. O chamador gerencia o ciclo de vida.
    liga : str | None
        Filtro opcional de liga.
    entrada : str | None
        Filtro opcional de entrada.
    date_start : str | None
        Data inicial ISO (YYYY-MM-DD), inclusiva.
    date_end : str | None
        Data final ISO (YYYY-MM-DD), inclusiva.

    Retorna
    -------
    list[dict]
        Lista de dicts com chaves: dia (int 0-6), dia_nome (str), greens (int),
        total (int), win_rate (float 0-100). Apenas dias com sinais sao incluidos.
        Ordenada por dia da semana (0=Dom, 6=Sab).
    """
    where, params = _build_where(liga=liga, entrada=entrada,
                                 date_start=date_start, date_end=date_end)
    sql = f"""
        SELECT
            EXTRACT(DOW FROM received_at)::INT AS dia,
            COUNT(*) FILTER (WHERE resultado = 'GREEN') AS greens,
            COUNT(*) FILTER (WHERE resultado IN ('GREEN', 'RED')) AS total
        FROM signals
        WHERE resultado IN ('GREEN', 'RED') AND {where}
        GROUP BY 1
        ORDER BY 1
    """
    dias_nomes = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sab"]
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    return [
        {
            "dia": int(dia),
            "dia_nome": dias_nomes[int(dia)],
            "greens": int(g),
            "total": int(t),
            "win_rate": round(g / t * 100, 1) if t > 0 else 0.0,
        }
        for dia, g, t in rows
    ]


def calculate_equity_curve(signals_desc: list, stake: float, odd: float) -> dict:
    """
    Constroi curva de equity acumulado para Stake Fixa e Gale sobrepostos.

    Funcao pura Python — sem acesso ao banco de dados.

    Parametros
    ----------
    signals_desc : list[dict]
        Lista de sinais em ordem DESC (saida de get_signal_history). Cada dict
        deve ter 'resultado' (str|None) e 'tentativa' (int|None).
        Sinais pendentes (resultado=None) sao ignorados.
    stake : float
        Stake base (ex: 10.0 para R$10).
    odd : float
        Odd decimal (ex: 1.90).

    Retorna
    -------
    dict com chaves:
        x           — lista de indices cronologicos [1, 2, 3, ...] (por sinal)
        y_fixa      — bankroll acumulado com Stake Fixa
        y_gale      — bankroll acumulado com Gale
        colors      — cor por sinal: "#28a745" (GREEN) ou "#dc3545" (RED)
        annotations — lista de dicts {x, y, text} para streaks >= 5 consecutivos
    """
    resolved = [s for s in signals_desc if s.get("resultado") in ("GREEN", "RED")]
    resolved_asc = list(reversed(resolved))  # ordem cronologica (ASC)

    if not resolved_asc:
        return {"x": [], "y_fixa": [], "y_gale": [], "colors": [], "annotations": []}

    xs, y_fixa, y_gale, colors = [], [], [], []
    bk_fixa = bk_gale = 0.0

    for i, sig in enumerate(resolved_asc, 1):
        resultado = sig["resultado"]
        tentativa = sig.get("tentativa") or 1

        # Stake Fixa
        net_fixa = stake * (odd - 1) if resultado == "GREEN" else -stake
        bk_fixa += net_fixa

        # Gale: acumula custo de tentativas anteriores
        accumulated = stake * (2 ** tentativa - 1)
        winning = stake * (2 ** (tentativa - 1))
        if resultado == "GREEN":
            net_gale = winning * (odd - 1) - (accumulated - winning)
        else:
            net_gale = -accumulated
        bk_gale += net_gale

        xs.append(i)
        y_fixa.append(round(bk_fixa, 2))
        y_gale.append(round(bk_gale, 2))
        colors.append("#28a745" if resultado == "GREEN" else "#dc3545")

    # Detectar streaks >= 5 e gerar annotations
    annotations = []
    streak_len = 1
    streak_start = 0  # indice em resolved_asc

    for i in range(1, len(resolved_asc)):
        if resolved_asc[i]["resultado"] == resolved_asc[i - 1]["resultado"]:
            streak_len += 1
        else:
            if streak_len >= 5:
                x_pos = streak_start + 1  # indice 1-based do inicio da streak
                annotations.append({
                    "x": x_pos,
                    "y": y_fixa[streak_start],
                    "text": f"Streak {streak_len}x {resolved_asc[streak_start]['resultado']}",
                })
            streak_start = i
            streak_len = 1

    # Verificar ultimo streak
    if streak_len >= 5:
        x_pos = streak_start + 1
        annotations.append({
            "x": x_pos,
            "y": y_fixa[streak_start],
            "text": f"Streak {streak_len}x {resolved_asc[streak_start]['resultado']}",
        })

    return {"x": xs, "y_fixa": y_fixa, "y_gale": y_gale, "colors": colors, "annotations": annotations}


def calculate_equity_curve_breakdown(
    signals: list[dict],
    complementares_por_mercado: dict[str, list[dict]],
    stake: float,
    odd_por_mercado: dict[str, float],
    gale_on: bool,
) -> dict:
    """
    Equity curve com breakdown principal / complementar / total (per D-02).

    Recebe sinais em ordem ASC (saida de get_signals_com_placar).

    Parametros
    ----------
    signals : list[dict]
        Sinais resolvidos em ordem ASC. Cada dict: resultado, placar, tentativa, mercado_slug.
    complementares_por_mercado : dict[str, list[dict]]
        Mapa mercado_slug -> config complementares.
    stake : float
        Stake base.
    odd_por_mercado : dict[str, float]
        Mapa mercado_slug -> odd referencia principal.
    gale_on : bool
        Aplica Gale progressivo.

    Retorna
    -------
    dict com chaves:
        x              — indices cronologicos [1, 2, ...]
        y_principal    — equity acumulado do principal
        y_complementar — equity acumulado dos complementares
        y_total        — y_principal + y_complementar
        colors         — "#28a745" (GREEN) ou "#dc3545" (RED) por sinal
    """
    resolved = [s for s in signals if s.get("resultado") in ("GREEN", "RED")]

    if not resolved:
        return {"x": [], "y_principal": [], "y_complementar": [], "y_total": [], "colors": []}

    xs, y_principal, y_complementar, y_total, colors = [], [], [], [], []
    bk_principal = bk_comp = 0.0

    for i, signal in enumerate(resolved, 1):
        resultado = signal["resultado"]
        tentativa = signal.get("tentativa") or 1
        mercado_slug = signal.get("mercado_slug") or "over_2_5"
        odd = odd_por_mercado.get(mercado_slug, 2.30)

        # Net principal (formula exata de calculate_roi)
        if gale_on:
            accumulated = stake * (2 ** tentativa - 1)
            winning = stake * (2 ** (tentativa - 1))
            if resultado == "GREEN":
                net_principal = winning * (odd - 1) - (accumulated - winning)
            else:
                net_principal = -accumulated
        else:
            if resultado == "GREEN":
                net_principal = stake * (odd - 1)
            else:
                net_principal = -stake

        # Net complementares (formula de calculate_roi_complementares)
        comps = complementares_por_mercado.get(mercado_slug, [])
        net_comp = 0.0

        for comp in comps:
            percentual = float(comp["percentual"])
            odd_ref = float(comp["odd_ref"])

            resultado_comp = validar_complementar(
                comp["regra_validacao"],
                signal.get("placar"),
                signal.get("resultado"),
            )

            if gale_on:
                acc_comp = stake * (2 ** tentativa - 1) * percentual
                win_comp = stake * (2 ** (tentativa - 1)) * percentual
                if resultado_comp == "GREEN":
                    net_comp += win_comp * (odd_ref - 1) - (acc_comp - win_comp)
                else:
                    net_comp -= acc_comp
            else:
                stake_comp = stake * percentual
                if resultado_comp == "GREEN":
                    net_comp += stake_comp * (odd_ref - 1)
                else:
                    net_comp -= stake_comp

        bk_principal += net_principal
        bk_comp += net_comp

        xs.append(i)
        y_principal.append(round(bk_principal, 2))
        y_complementar.append(round(bk_comp, 2))
        y_total.append(round(bk_principal + bk_comp, 2))
        colors.append("#28a745" if resultado == "GREEN" else "#dc3545")

    return {
        "x": xs,
        "y_principal": y_principal,
        "y_complementar": y_complementar,
        "y_total": y_total,
        "colors": colors,
    }


def calculate_streaks(signals_desc: list) -> dict:
    """
    Calcula streaks a partir de sinais em ordem DESC (saida de get_signal_history).

    Funcao pura Python — sem acesso ao banco de dados. Algoritmo O(n) single-pass.

    Parametros
    ----------
    signals_desc : list[dict]
        Lista de sinais em ordem DESC. Cada dict deve ter 'resultado' (str|None).
        Sinais pendentes sao ignorados.

    Retorna
    -------
    dict com chaves:
        current      — comprimento do streak atual (do sinal mais recente)
        current_type — 'GREEN', 'RED', ou None se lista vazia
        max_green    — maior streak consecutiva de GREEN no historico
        max_red      — maior streak consecutiva de RED no historico
    """
    resolved = [s for s in signals_desc if s.get("resultado") in ("GREEN", "RED")]
    resolved_asc = list(reversed(resolved))  # cronologico

    if not resolved_asc:
        return {"current": 0, "current_type": None, "max_green": 0, "max_red": 0}

    current = 1
    max_green = max_red = 0

    for i in range(1, len(resolved_asc)):
        if resolved_asc[i]["resultado"] == resolved_asc[i - 1]["resultado"]:
            current += 1
        else:
            prev = resolved_asc[i - 1]["resultado"]
            if prev == "GREEN":
                max_green = max(max_green, current)
            else:
                max_red = max(max_red, current)
            current = 1

    # Finalizar ultimo streak
    last = resolved_asc[-1]["resultado"]
    if last == "GREEN":
        max_green = max(max_green, current)
    else:
        max_red = max(max_red, current)

    return {
        "current": current,
        "current_type": last,
        "max_green": max_green,
        "max_red": max_red,
    }


# ---------------------------------------------------------------------------
# Fase 3 Plan 02: Gale analysis, volume por dia, cross-dimensional,
# parse failures detail, win rate por periodo
# ---------------------------------------------------------------------------


def get_gale_analysis(conn, liga=None, entrada=None, date_start=None, date_end=None) -> list:
    """
    Taxa de recuperacao por nivel de tentativa (Gale). Exclui sinais sem tentativa.

    Parametros
    ----------
    conn : psycopg2 connection
    liga, entrada, date_start, date_end : filtros opcionais

    Retorna
    -------
    list[dict]
        Lista ordenada por tentativa (1..4) com chaves:
        tentativa (int), greens (int), total (int), win_rate (float 0-100).
        Apenas tentativas com ao menos 1 sinal resolvido sao incluidas.
    """
    where, params = _build_where(liga=liga, entrada=entrada,
                                 date_start=date_start, date_end=date_end)
    sql = f"""
        SELECT
            tentativa,
            COUNT(*) FILTER (WHERE resultado = 'GREEN') AS greens,
            COUNT(*) FILTER (WHERE resultado IN ('GREEN', 'RED')) AS total
        FROM signals
        WHERE resultado IN ('GREEN', 'RED')
          AND tentativa IS NOT NULL
          AND {where}
        GROUP BY tentativa
        ORDER BY tentativa
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return [
        {
            "tentativa": int(t),
            "greens": int(g),
            "total": int(total),
            "win_rate": round(g / total * 100, 1) if total > 0 else 0.0,
        }
        for t, g, total in rows
    ]


def get_volume_by_day(conn, liga=None, entrada=None, date_start=None, date_end=None) -> list:
    """
    Volume de sinais agrupado por dia. Retorna lista de {data, count}.

    Parametros
    ----------
    conn : psycopg2 connection
    liga, entrada, date_start, date_end : filtros opcionais

    Retorna
    -------
    list[dict]
        Lista ordenada por data com chaves: data (str YYYY-MM-DD), count (int).
    """
    where, params = _build_where(liga=liga, entrada=entrada,
                                 date_start=date_start, date_end=date_end)
    sql = f"""
        SELECT
            DATE_TRUNC('day', received_at)::DATE AS data,
            COUNT(*) AS count
        FROM signals
        WHERE {where}
        GROUP BY 1
        ORDER BY 1
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return [{"data": str(d), "count": int(c)} for d, c in rows]


def get_cross_dimensional(conn, liga=None, entrada=None, date_start=None, date_end=None) -> list:
    """
    Breakdown cross-dimensional: win rate e contagem por (liga, entrada).

    Parametros
    ----------
    conn : psycopg2 connection
    liga, entrada, date_start, date_end : filtros opcionais

    Retorna
    -------
    list[dict]
        Lista ordenada por win_rate DESC com chaves:
        liga (str), entrada (str), greens (int), total (int), win_rate (float 0-100).
    """
    where, params = _build_where(liga=liga, entrada=entrada,
                                 date_start=date_start, date_end=date_end)
    sql = f"""
        SELECT
            liga,
            entrada,
            COUNT(*) FILTER (WHERE resultado = 'GREEN') AS greens,
            COUNT(*) FILTER (WHERE resultado IN ('GREEN', 'RED')) AS total
        FROM signals
        WHERE resultado IN ('GREEN', 'RED') AND {where}
        GROUP BY liga, entrada
        HAVING COUNT(*) FILTER (WHERE resultado IN ('GREEN', 'RED')) > 0
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    result = [
        {
            "liga": liga_val,
            "entrada": entrada_val,
            "greens": int(g),
            "total": int(t),
            "win_rate": round(g / t * 100, 1) if t > 0 else 0.0,
        }
        for liga_val, entrada_val, g, t in rows
    ]
    result.sort(key=lambda r: r["win_rate"], reverse=True)
    return result


def get_parse_failures_detail(conn, limit: int = 100) -> list:
    """
    Retorna ultimas parse_failures para exibir no modal de operacoes (OPER-01).

    Parametros
    ----------
    conn : psycopg2 connection
    limit : int
        Numero maximo de registros a retornar (padrao 100).

    Retorna
    -------
    list[dict]
        Lista com chaves: raw_text (str), failure_reason (str), received_at.
        Ordenada por received_at DESC (mais recentes primeiro).
    """
    sql = """
        SELECT raw_text, failure_reason, received_at
        FROM parse_failures
        ORDER BY received_at DESC
        LIMIT %s
    """
    with conn.cursor() as cur:
        cur.execute(sql, (limit,))
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
    return [dict(zip(columns, row)) for row in rows]


def get_winrate_by_periodo(conn, liga=None, entrada=None, date_start=None, date_end=None) -> list:
    """
    Win rate por periodo (1T/2T/FT). Exclui sinais com periodo NULL (ANAL-03).

    Parametros
    ----------
    conn : psycopg2 connection
    liga, entrada, date_start, date_end : filtros opcionais

    Retorna
    -------
    list[dict]
        Lista ordenada por periodo com chaves:
        periodo (str), greens (int), total (int), win_rate (float 0-100).
        Apenas periodos com ao menos 1 sinal resolvido sao incluidos.
    """
    where, params = _build_where(liga=liga, entrada=entrada,
                                 date_start=date_start, date_end=date_end)
    sql = f"""
        SELECT
            periodo,
            COUNT(*) FILTER (WHERE resultado = 'GREEN') AS greens,
            COUNT(*) FILTER (WHERE resultado IN ('GREEN', 'RED')) AS total
        FROM signals
        WHERE resultado IN ('GREEN', 'RED')
          AND periodo IS NOT NULL
          AND {where}
        GROUP BY periodo
        ORDER BY periodo
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return [
        {
            "periodo": str(p),
            "greens": int(g),
            "total": int(t),
            "win_rate": round(g / t * 100, 1) if t > 0 else 0.0,
        }
        for p, g, t in rows
    ]


def aggregate_pl_por_liga(pl_lista: list[dict]) -> list[dict]:
    """Agrega P&L por liga para analise dimensional (DASH-05)."""
    from collections import defaultdict
    grupos: dict[str, dict] = defaultdict(lambda: {
        "lucro_principal": 0.0, "lucro_complementar": 0.0,
        "greens": 0, "reds": 0,
    })
    for row in pl_lista:
        liga = row.get("liga") or "Desconhecida"
        resultado = row.get("resultado")
        if resultado not in ("GREEN", "RED"):
            continue
        grupos[liga]["lucro_principal"] += row.get("lucro_principal", 0.0)
        grupos[liga]["lucro_complementar"] += row.get("lucro_comp", 0.0)
        if resultado == "GREEN":
            grupos[liga]["greens"] += 1
        else:
            grupos[liga]["reds"] += 1

    result = []
    for liga, g in grupos.items():
        total = g["greens"] + g["reds"]
        pl_total = g["lucro_principal"] + g["lucro_complementar"]
        taxa = g["greens"] / total * 100 if total > 0 else 0.0
        result.append({
            "liga": liga,
            "lucro_principal": round(g["lucro_principal"], 2),
            "lucro_complementar": round(g["lucro_complementar"], 2),
            "pl_total": round(pl_total, 2),
            "greens": g["greens"],
            "reds": g["reds"],
            "total": total,
            "taxa_green": round(taxa, 1),
        })
    result.sort(key=lambda r: r["pl_total"], reverse=True)
    return result


def aggregate_pl_por_tentativa(pl_lista: list[dict]) -> list[dict]:
    """Agrega P&L por tentativa para analise de gale (DASH-07, per D-07)."""
    from collections import defaultdict
    grupos: dict[int, dict] = defaultdict(lambda: {
        "greens": 0, "lucro_total_greens": 0.0,
    })
    for row in pl_lista:
        t = row.get("tentativa") or 1
        if row.get("resultado") == "GREEN":
            grupos[t]["greens"] += 1
            grupos[t]["lucro_total_greens"] += row.get("lucro_total", 0.0)

    result = []
    for tentativa in sorted(grupos.keys()):
        g = grupos[tentativa]
        lucro_medio = (
            g["lucro_total_greens"] / g["greens"] if g["greens"] > 0 else 0.0
        )
        result.append({
            "tentativa": tentativa,
            "greens": g["greens"],
            "lucro_medio_green": round(lucro_medio, 2),
        })
    return result
