"""
test_queries.py — Unit and integration tests for the queries data layer.

Tests for helpertips/queries.py:
  - get_filtered_stats: filtered SQL counts by liga, entrada, date range
  - get_signal_history: ordered history with filters and limit
  - get_distinct_values: dropdown options for liga and entrada
  - calculate_roi: pure Python ROI calculation for Stake Fixa and Gale modes

DB-dependent tests require a live PostgreSQL connection configured via .env.
If the database is not available, those tests are skipped automatically.

Pure-Python tests (calculate_roi) always run — no DB required.
"""
import os
import pytest

# ---------------------------------------------------------------------------
# Import guards — skip DB tests if imports fail
# ---------------------------------------------------------------------------

try:
    from helpertips.db import get_connection, ensure_schema
    from helpertips.queries import (
        get_filtered_stats,
        get_signal_history,
        get_distinct_values,
        calculate_roi,
        _parse_placar,
        validar_complementar,
    )
    _IMPORTS_OK = True
except ImportError as e:
    _IMPORTS_OK = False
    _IMPORT_ERROR = str(e)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_signal_dict(message_id: int, liga="Superliga", entrada="Over 2.5",
                      resultado=None, placar=None, tentativa=1) -> dict:
    """Build a minimal valid signal dict for DB insertion."""
    return {
        "message_id": message_id,
        "liga": liga,
        "entrada": entrada,
        "horario": "10:00",
        "periodo": None,
        "dia_semana": 0,
        "resultado": resultado,
        "placar": placar,
        "tentativa": tentativa,
        "raw_text": f"Liga: {liga}\nEntrada: {entrada}",
    }


def _insert_signal(conn, data: dict) -> None:
    """Direct INSERT for test setup — bypasses store to avoid coupling."""
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
            """,
            data,
        )
    conn.commit()


# ---------------------------------------------------------------------------
# DB fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def db_conn():
    """
    Provide a live psycopg2 connection for DB-dependent tests.
    Ensures schema and cleans up test data after each test.
    """
    if not _IMPORTS_OK:
        pytest.skip(f"helpertips.queries or helpertips.db import failed: {_IMPORT_ERROR}")

    try:
        conn = get_connection()
    except Exception as exc:
        pytest.skip(f"PostgreSQL not available: {exc}")

    ensure_schema(conn)

    # Setup: clear any pre-existing data so tests start from a clean state
    with conn.cursor() as cur:
        cur.execute("DELETE FROM signals")
    conn.commit()

    yield conn

    # Teardown: remove all test data
    with conn.cursor() as cur:
        cur.execute("DELETE FROM signals")
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# get_filtered_stats tests
# ---------------------------------------------------------------------------


def test_get_filtered_stats_no_filter(db_conn):
    """No filters: returns all signals with correct total/greens/reds/pending."""
    _insert_signal(db_conn, _make_signal_dict(9001, resultado="GREEN"))
    _insert_signal(db_conn, _make_signal_dict(9002, resultado="RED"))
    _insert_signal(db_conn, _make_signal_dict(9003, resultado=None))

    result = get_filtered_stats(db_conn)

    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert result["total"] == 3
    assert result["greens"] == 1
    assert result["reds"] == 1
    assert result["pending"] == 1


def test_get_filtered_stats_by_liga(db_conn):
    """Filtering by liga='Superliga' excludes signals from other ligas."""
    _insert_signal(db_conn, _make_signal_dict(9010, liga="Superliga", resultado="GREEN"))
    _insert_signal(db_conn, _make_signal_dict(9011, liga="Euro League", resultado="GREEN"))
    _insert_signal(db_conn, _make_signal_dict(9012, liga="Superliga", resultado="RED"))

    result = get_filtered_stats(db_conn, liga="Superliga")

    assert result["total"] == 2
    assert result["greens"] == 1
    assert result["reds"] == 1


def test_get_filtered_stats_by_entrada(db_conn):
    """Filtering by entrada='Over 2.5' returns only Over 2.5 signals."""
    _insert_signal(db_conn, _make_signal_dict(9020, entrada="Over 2.5", resultado="GREEN"))
    _insert_signal(db_conn, _make_signal_dict(9021, entrada="Ambas Marcam", resultado="GREEN"))
    _insert_signal(db_conn, _make_signal_dict(9022, entrada="Over 2.5", resultado=None))

    result = get_filtered_stats(db_conn, entrada="Over 2.5")

    assert result["total"] == 2
    assert result["greens"] == 1
    assert result["pending"] == 1


def test_get_filtered_stats_combined(db_conn):
    """liga + entrada filter returns only signals matching BOTH conditions."""
    _insert_signal(db_conn, _make_signal_dict(9030, liga="Superliga", entrada="Over 2.5", resultado="GREEN"))
    _insert_signal(db_conn, _make_signal_dict(9031, liga="Euro League", entrada="Over 2.5", resultado="GREEN"))
    _insert_signal(db_conn, _make_signal_dict(9032, liga="Superliga", entrada="Ambas Marcam", resultado="GREEN"))

    result = get_filtered_stats(db_conn, liga="Superliga", entrada="Over 2.5")

    assert result["total"] == 1
    assert result["greens"] == 1


def test_get_filtered_stats_by_date(db_conn):
    """date_start and date_end filters restrict returned signals correctly."""
    # Insert a signal — it will have received_at = NOW() which is today
    _insert_signal(db_conn, _make_signal_dict(9040, resultado="GREEN"))

    import datetime
    today = datetime.date.today().isoformat()
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

    # Should find the signal when filtering today..tomorrow
    result_in = get_filtered_stats(db_conn, date_start=today, date_end=tomorrow)
    assert result_in["total"] == 1

    # Should find nothing when filtering before today
    result_out = get_filtered_stats(db_conn, date_start=yesterday, date_end=yesterday)
    assert result_out["total"] == 0


# ---------------------------------------------------------------------------
# get_signal_history tests
# ---------------------------------------------------------------------------


def test_get_signal_history_order(db_conn):
    """Rows are returned sorted by received_at DESC (most recent first)."""
    _insert_signal(db_conn, _make_signal_dict(9100, resultado="GREEN"))
    _insert_signal(db_conn, _make_signal_dict(9101, resultado="RED"))
    _insert_signal(db_conn, _make_signal_dict(9102, resultado=None))

    rows = get_signal_history(db_conn)

    assert isinstance(rows, list), f"Expected list, got {type(rows)}"
    assert len(rows) >= 3
    # Rows should be dicts
    assert isinstance(rows[0], dict), f"Expected dict rows, got {type(rows[0])}"
    # Check that received_at is descending
    timestamps = [r["received_at"] for r in rows if r["received_at"] is not None]
    assert timestamps == sorted(timestamps, reverse=True), "Rows not in DESC order"


def test_get_signal_history_limit(db_conn):
    """limit parameter caps the number of returned rows."""
    for i in range(10):
        _insert_signal(db_conn, _make_signal_dict(9200 + i, resultado="GREEN"))

    rows = get_signal_history(db_conn, limit=3)

    assert len(rows) == 3


def test_get_signal_history_filters(db_conn):
    """liga/entrada filters apply correctly to history query."""
    _insert_signal(db_conn, _make_signal_dict(9300, liga="Superliga", entrada="Over 2.5", resultado="GREEN"))
    _insert_signal(db_conn, _make_signal_dict(9301, liga="Euro League", entrada="Over 2.5", resultado="RED"))

    rows = get_signal_history(db_conn, liga="Superliga")

    assert len(rows) == 1
    assert rows[0]["liga"] == "Superliga"


def test_get_signal_history_columns(db_conn):
    """Returned dicts contain the 7 expected columns."""
    _insert_signal(db_conn, _make_signal_dict(9400, resultado="GREEN", placar="2-1", tentativa=2))

    rows = get_signal_history(db_conn)

    assert len(rows) >= 1
    row = rows[0]
    expected_keys = {"liga", "entrada", "horario", "resultado", "placar", "tentativa", "received_at"}
    assert expected_keys.issubset(set(row.keys())), f"Missing keys: {expected_keys - set(row.keys())}"


# ---------------------------------------------------------------------------
# get_distinct_values tests
# ---------------------------------------------------------------------------


def test_get_distinct_values_liga(db_conn):
    """Returns sorted list of unique liga values, no NULLs."""
    _insert_signal(db_conn, _make_signal_dict(9500, liga="Superliga"))
    _insert_signal(db_conn, _make_signal_dict(9501, liga="Euro League"))
    _insert_signal(db_conn, _make_signal_dict(9502, liga="Superliga"))  # duplicate

    values = get_distinct_values(db_conn, "liga")

    assert isinstance(values, list)
    assert "Superliga" in values
    assert "Euro League" in values
    assert len(set(values)) == len(values), "Should not contain duplicates"
    assert values == sorted(values), "Values should be sorted"
    assert all(v is not None for v in values), "Should not contain NULLs"


def test_get_distinct_values_entrada(db_conn):
    """Returns sorted list of unique entrada values, no NULLs."""
    _insert_signal(db_conn, _make_signal_dict(9600, entrada="Over 2.5"))
    _insert_signal(db_conn, _make_signal_dict(9601, entrada="Ambas Marcam"))

    values = get_distinct_values(db_conn, "entrada")

    assert isinstance(values, list)
    assert "Over 2.5" in values
    assert "Ambas Marcam" in values
    assert values == sorted(values)


def test_get_distinct_values_invalid_field(db_conn):
    """Invalid field raises ValueError (SQL injection prevention)."""
    with pytest.raises(ValueError):
        get_distinct_values(db_conn, "raw_text")

    with pytest.raises(ValueError):
        get_distinct_values(db_conn, "'; DROP TABLE signals; --")


# ---------------------------------------------------------------------------
# calculate_roi tests — pure Python, no DB
# ---------------------------------------------------------------------------


def test_calculate_roi_empty():
    """Empty list returns zero profit, roi_pct, total_invested."""
    result = calculate_roi([], stake=10.0, odd=1.90, gale_on=False)

    assert result == {"profit": 0.0, "roi_pct": 0.0, "total_invested": 0.0}


def test_calculate_roi_stake_fixa():
    """3 GREEN signals at R$10 stake, odd 1.90 => profit = 3 * 10 * 0.90 = 27.0, invested = 30.0."""
    signals = [
        {"resultado": "GREEN", "tentativa": 1},
        {"resultado": "GREEN", "tentativa": 1},
        {"resultado": "GREEN", "tentativa": 1},
    ]

    result = calculate_roi(signals, stake=10.0, odd=1.90, gale_on=False)

    assert result["total_invested"] == pytest.approx(30.0)
    assert result["profit"] == pytest.approx(27.0)
    assert result["roi_pct"] == pytest.approx(90.0)


def test_calculate_roi_stake_fixa_mixed():
    """2 GREEN + 1 RED at R$10 stake, odd 1.90 => profit = 2*9 - 10 = 8.0, invested = 30.0."""
    signals = [
        {"resultado": "GREEN", "tentativa": 1},
        {"resultado": "GREEN", "tentativa": 1},
        {"resultado": "RED", "tentativa": 4},
    ]

    result = calculate_roi(signals, stake=10.0, odd=1.90, gale_on=False)

    assert result["total_invested"] == pytest.approx(30.0)
    assert result["profit"] == pytest.approx(8.0)
    assert result["roi_pct"] == pytest.approx(8.0 / 30.0 * 100)


def test_calculate_roi_gale_on():
    """
    Gale GREEN at tentativa=3:
    - Stakes: 10 (1st), 20 (2nd), 40 (3rd) = total invested 70
    - Lost: 10 + 20 = 30
    - Win: 40 * (1.90 - 1) = 40 * 0.90 = 36
    - Net: 36 - 30 = 6
    """
    signals = [
        {"resultado": "GREEN", "tentativa": 3},
    ]

    result = calculate_roi(signals, stake=10.0, odd=1.90, gale_on=True)

    assert result["total_invested"] == pytest.approx(70.0)  # 10 + 20 + 40
    assert result["profit"] == pytest.approx(6.0)           # 36 - 30


def test_calculate_roi_gale_red():
    """
    Gale RED (all 4 tentativas failed):
    - Stakes: 10 + 20 + 40 + 80 = 150 invested
    - Net: -150
    """
    signals = [
        {"resultado": "RED", "tentativa": 4},
    ]

    result = calculate_roi(signals, stake=10.0, odd=1.90, gale_on=True)

    assert result["total_invested"] == pytest.approx(150.0)  # 10*(2^4 - 1)
    assert result["profit"] == pytest.approx(-150.0)


def test_calculate_roi_pending_skipped():
    """Signals with resultado=None (pending) are excluded from ROI."""
    signals = [
        {"resultado": "GREEN", "tentativa": 1},
        {"resultado": None, "tentativa": None},
        {"resultado": None, "tentativa": 2},
    ]

    result = calculate_roi(signals, stake=10.0, odd=1.90, gale_on=False)

    # Only the 1 GREEN counts
    assert result["total_invested"] == pytest.approx(10.0)
    assert result["profit"] == pytest.approx(9.0)


def test_calculate_roi_gale_accumulates_across_tentativas():
    """Gale GREEN at tentativa=1 costs less than at tentativa=3 — verifies exponential cost."""
    signals_t1 = [{"resultado": "GREEN", "tentativa": 1}]
    signals_t3 = [{"resultado": "GREEN", "tentativa": 3}]

    result_t1 = calculate_roi(signals_t1, stake=10.0, odd=1.90, gale_on=True)
    result_t3 = calculate_roi(signals_t3, stake=10.0, odd=1.90, gale_on=True)

    assert result_t3["total_invested"] > result_t1["total_invested"], (
        "Gale at tentativa=3 should cost more than tentativa=1"
    )


# ---------------------------------------------------------------------------
# _parse_placar tests — pure Python, no DB
# ---------------------------------------------------------------------------


def test_parse_placar_valid():
    """_parse_placar converte 'X-Y' em tupla (int, int)."""
    assert _parse_placar("3-2") == (3, 2)
    assert _parse_placar("0-0") == (0, 0)
    assert _parse_placar("10-5") == (10, 5)


def test_parse_placar_none_input():
    """_parse_placar retorna None quando a entrada e None."""
    assert _parse_placar(None) is None


def test_parse_placar_empty_string():
    """_parse_placar retorna None para string vazia."""
    assert _parse_placar("") is None


def test_parse_placar_invalid_format():
    """_parse_placar retorna None para strings que nao sao 'X-Y'."""
    assert _parse_placar("abc") is None
    assert _parse_placar("3-2-1") is None


# ---------------------------------------------------------------------------
# validar_complementar tests — pure Python, no DB
# ---------------------------------------------------------------------------


def test_validar_complementar_over_3_5_green():
    """over_3_5 retorna GREEN quando total de gols > 3.5."""
    assert validar_complementar("over_3_5", "3-2", "GREEN") == "GREEN"  # total=5


def test_validar_complementar_over_3_5_red():
    """over_3_5 retorna RED quando total de gols nao excede 3.5."""
    assert validar_complementar("over_3_5", "2-0", "GREEN") == "RED"  # total=2


def test_validar_complementar_over_5_plus_green():
    """over_5_plus retorna GREEN quando total >= 6."""
    assert validar_complementar("over_5_plus", "4-3", "GREEN") == "GREEN"  # total=7


def test_validar_complementar_over_5_plus_red():
    """over_5_plus retorna RED quando total < 6."""
    assert validar_complementar("over_5_plus", "3-2", "GREEN") == "RED"  # total=5


def test_validar_complementar_empate_3_3_4_4_green():
    """empate_3_3_4_4 retorna GREEN para placar 3-3 e 4-4."""
    assert validar_complementar("empate_3_3_4_4", "3-3", "GREEN") == "GREEN"
    assert validar_complementar("empate_3_3_4_4", "4-4", "GREEN") == "GREEN"


def test_validar_complementar_empate_3_3_4_4_falso_positivo():
    """empate_3_3_4_4 NAO aceita placar 2-4 ou 4-2 como GREEN (falso-positivo trap)."""
    assert validar_complementar("empate_3_3_4_4", "2-4", "GREEN") == "RED"
    assert validar_complementar("empate_3_3_4_4", "5-1", "GREEN") == "RED"


def test_validar_complementar_gols_casa_4_green():
    """gols_casa_4 retorna GREEN quando casa == 4."""
    assert validar_complementar("gols_casa_4", "4-1", "GREEN") == "GREEN"


def test_validar_complementar_gols_casa_4_red():
    """gols_casa_4 retorna RED quando casa != 4."""
    assert validar_complementar("gols_casa_4", "3-1", "GREEN") == "RED"


def test_validar_complementar_gols_fora_4_green():
    """gols_fora_4 retorna GREEN quando fora == 4."""
    assert validar_complementar("gols_fora_4", "1-4", "GREEN") == "GREEN"


def test_validar_complementar_gols_fora_4_red():
    """gols_fora_4 retorna RED quando fora != 4."""
    assert validar_complementar("gols_fora_4", "1-3", "GREEN") == "RED"


def test_validar_complementar_gols_casa_5_plus_green():
    """gols_casa_5_plus retorna GREEN quando casa >= 5."""
    assert validar_complementar("gols_casa_5_plus", "5-0", "GREEN") == "GREEN"


def test_validar_complementar_gols_casa_5_plus_red():
    """gols_casa_5_plus retorna RED quando casa < 5."""
    assert validar_complementar("gols_casa_5_plus", "4-0", "GREEN") == "RED"


def test_validar_complementar_gols_fora_5_plus_green():
    """gols_fora_5_plus retorna GREEN quando fora >= 5."""
    assert validar_complementar("gols_fora_5_plus", "0-6", "GREEN") == "GREEN"


def test_validar_complementar_gols_fora_5_plus_red():
    """gols_fora_5_plus retorna RED quando fora < 5."""
    assert validar_complementar("gols_fora_5_plus", "0-4", "GREEN") == "RED"


def test_validar_complementar_principal_pendente():
    """resultado_principal=None retorna None (sinal pendente — D-09)."""
    assert validar_complementar("over_3_5", "3-2", None) is None


def test_validar_complementar_principal_red_sem_placar():
    """resultado_principal='RED' com placar=None retorna RED (D-08)."""
    assert validar_complementar("over_3_5", None, "RED") == "RED"


def test_validar_complementar_principal_red_com_placar():
    """resultado_principal='RED' sempre retorna RED, independente do placar (D-08)."""
    assert validar_complementar("over_3_5", "3-2", "RED") == "RED"


def test_validar_complementar_placar_ausente_principal_green():
    """resultado_principal='GREEN' com placar=None retorna RED (conservador)."""
    assert validar_complementar("over_3_5", None, "GREEN") == "RED"


def test_validar_complementar_regra_invalida():
    """Regra desconhecida retorna RED (comportamento conservador)."""
    assert validar_complementar("regra_invalida", "3-2", "GREEN") == "RED"
