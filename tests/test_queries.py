"""
test_queries.py — Unit and integration tests for the queries data layer.

Tests for helpertips/queries.py:
  - get_filtered_stats: filtered SQL counts by liga, entrada, date range
  - get_signal_history: ordered history with filters and limit
  - get_distinct_values: dropdown options for liga and entrada
  - calculate_roi: pure Python ROI calculation for Stake Fixa and Gale modes
  - get_complementares_config: DB query that returns complementary market config
  - calculate_roi_complementares: pure Python ROI for complementary markets with Gale

DB-dependent tests require a live PostgreSQL connection configured via .env.
If the database is not available, those tests are skipped automatically.

Pure-Python tests (calculate_roi, calculate_roi_complementares) always run — no DB required.
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
        get_complementares_config,
        calculate_roi_complementares,
        get_heatmap_data,
        get_winrate_by_dow,
        calculate_equity_curve,
        calculate_streaks,
        get_gale_analysis,
        get_volume_by_day,
        get_cross_dimensional,
        get_parse_failures_detail,
        get_winrate_by_periodo,
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
        cur.execute("DELETE FROM parse_failures")
    conn.commit()

    yield conn

    # Teardown: remove all test data
    with conn.cursor() as cur:
        cur.execute("DELETE FROM signals")
        cur.execute("DELETE FROM parse_failures")
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


# ---------------------------------------------------------------------------
# get_complementares_config tests — requer DB
# ---------------------------------------------------------------------------


def test_get_complementares_config_over_2_5(db_conn):
    """get_complementares_config('over_2_5') retorna 7 complementares."""
    result = get_complementares_config(db_conn, "over_2_5")

    assert isinstance(result, list), f"Esperado list, recebido {type(result)}"
    assert len(result) == 7, f"Esperado 7 complementares para over_2_5, recebido {len(result)}"


def test_get_complementares_config_ambas_marcam(db_conn):
    """get_complementares_config('ambas_marcam') retorna 7 complementares."""
    result = get_complementares_config(db_conn, "ambas_marcam")

    assert isinstance(result, list)
    assert len(result) == 7, f"Esperado 7 complementares para ambas_marcam, recebido {len(result)}"


def test_get_complementares_config_chaves(db_conn):
    """Cada dict retornado tem as chaves: id, slug, nome_display, percentual, odd_ref, regra_validacao."""
    result = get_complementares_config(db_conn, "over_2_5")

    assert len(result) > 0, "Precisa de pelo menos 1 resultado para verificar chaves"
    expected_keys = {"id", "slug", "nome_display", "percentual", "odd_ref", "regra_validacao"}
    assert expected_keys == set(result[0].keys()), (
        f"Chaves incorretas: esperado {expected_keys}, recebido {set(result[0].keys())}"
    )


def test_get_complementares_config_ordenacao(db_conn):
    """Primeiro resultado e over_3_5 (percentual 0.20, maior percentual)."""
    result = get_complementares_config(db_conn, "over_2_5")

    assert len(result) > 0
    assert result[0]["slug"] == "over_3_5", (
        f"Esperado primeiro slug 'over_3_5', recebido '{result[0]['slug']}'"
    )


def test_get_complementares_config_slug_inexistente(db_conn):
    """Slug inexistente retorna lista vazia."""
    result = get_complementares_config(db_conn, "slug_inexistente")

    assert result == [], f"Esperado lista vazia, recebido {result}"


# ---------------------------------------------------------------------------
# calculate_roi_complementares tests — puro Python, sem DB
# ---------------------------------------------------------------------------


# Config simulada para over_2_5 — espelha seed data do banco
_OVER_2_5_CONFIG = [
    {"id": 1, "slug": "over_3_5",        "nome_display": "Over 3.5",        "percentual": 0.20, "odd_ref": 4.00, "regra_validacao": "over_3_5"},
    {"id": 2, "slug": "empate_3_3_4_4",  "nome_display": "Empate 3-3 / 4-4","percentual": 0.01, "odd_ref": 30.00,"regra_validacao": "empate_3_3_4_4"},
    {"id": 3, "slug": "over_5_plus",     "nome_display": "Over 5+",         "percentual": 0.10, "odd_ref": 8.00, "regra_validacao": "over_5_plus"},
    {"id": 4, "slug": "gols_casa_4",     "nome_display": "Gols Casa = 4",   "percentual": 0.01, "odd_ref": 25.00,"regra_validacao": "gols_casa_4"},
    {"id": 5, "slug": "gols_fora_4",     "nome_display": "Gols Fora = 4",   "percentual": 0.01, "odd_ref": 25.00,"regra_validacao": "gols_fora_4"},
    {"id": 6, "slug": "gols_casa_5_plus","nome_display": "Gols Casa 5+",    "percentual": 0.01, "odd_ref": 50.00,"regra_validacao": "gols_casa_5_plus"},
    {"id": 7, "slug": "gols_fora_5_plus","nome_display": "Gols Fora 5+",    "percentual": 0.01, "odd_ref": 50.00,"regra_validacao": "gols_fora_5_plus"},
]


def test_calculate_roi_complementares_empty():
    """Lista vazia retorna zeros e por_mercado vazio."""
    result = calculate_roi_complementares([], _OVER_2_5_CONFIG, stake=100.0, gale_on=False)

    assert result == {
        "profit": 0.0,
        "roi_pct": 0.0,
        "total_invested": 0.0,
        "por_mercado": [],
    }


def test_calculate_roi_complementares_pending_ignorado():
    """Sinais com resultado=None (pendentes) sao ignorados no calculo."""
    signals = [{"resultado": None, "placar": "3-2", "tentativa": 1}]

    result = calculate_roi_complementares(signals, _OVER_2_5_CONFIG, stake=100.0, gale_on=False)

    assert result["total_invested"] == 0.0
    assert result["profit"] == 0.0
    assert result["por_mercado"] == []


def test_calculate_roi_complementares_green_t1_stake_fixa():
    """
    1 sinal GREEN placar='3-2' tentativa=1, stake=100, gale_on=False, config over_2_5:
    - over_3_5: GREEN (total=5 > 3.5) -> stake_comp=100*0.20=20, lucro=20*(4.00-1)=60, investido=20
    - empate_3_3_4_4: RED -> stake_comp=100*0.01=1, lucro=-1, investido=1
    - over_5_plus: RED (total=5 < 6) -> stake_comp=100*0.10=10, lucro=-10, investido=10
    - gols_casa_4: RED (casa=3) -> stake_comp=1, lucro=-1, investido=1
    - gols_fora_4: RED (fora=2) -> stake_comp=1, lucro=-1, investido=1
    - gols_casa_5_plus: RED (casa=3) -> stake_comp=1, lucro=-1, investido=1
    - gols_fora_5_plus: RED (fora=2) -> stake_comp=1, lucro=-1, investido=1
    - Total investido=35, profit=60-1-10-1-1-1-1=45
    """
    signals = [{"resultado": "GREEN", "placar": "3-2", "tentativa": 1}]

    result = calculate_roi_complementares(signals, _OVER_2_5_CONFIG, stake=100.0, gale_on=False)

    assert result["total_invested"] == pytest.approx(35.0)
    assert result["profit"] == pytest.approx(45.0)
    assert result["roi_pct"] == pytest.approx(45.0 / 35.0 * 100)


def test_calculate_roi_complementares_por_mercado_chaves():
    """por_mercado retorna lista de dicts com: slug, nome_display, greens, reds, lucro, investido."""
    signals = [{"resultado": "GREEN", "placar": "3-2", "tentativa": 1}]

    result = calculate_roi_complementares(signals, _OVER_2_5_CONFIG, stake=100.0, gale_on=False)

    assert len(result["por_mercado"]) == 7
    expected_keys = {"slug", "nome_display", "greens", "reds", "lucro", "investido"}
    for entry in result["por_mercado"]:
        assert expected_keys == set(entry.keys()), (
            f"Chaves incorretas em por_mercado: {set(entry.keys())}"
        )


def test_calculate_roi_complementares_por_mercado_over_3_5():
    """over_3_5 no por_mercado tem greens=1, reds=0, lucro=60, investido=20."""
    signals = [{"resultado": "GREEN", "placar": "3-2", "tentativa": 1}]

    result = calculate_roi_complementares(signals, _OVER_2_5_CONFIG, stake=100.0, gale_on=False)

    over_3_5 = next(m for m in result["por_mercado"] if m["slug"] == "over_3_5")
    assert over_3_5["greens"] == 1
    assert over_3_5["reds"] == 0
    assert over_3_5["lucro"] == pytest.approx(60.0)
    assert over_3_5["investido"] == pytest.approx(20.0)


def test_calculate_roi_complementares_gale_t2():
    """
    1 sinal GREEN placar='3-2' tentativa=2, stake=100, gale_on=True:
    - stake_principal_T2 = 100 * 2^(2-1) = 200
    - over_3_5: GREEN
      - stake_comp_winning = 200 * 0.20 = 40
      - prior_losses (T1) = 100 * 0.20 = 20
      - lucro = 40*(4.00-1) - 20 = 120 - 20 = 100
      - investido = 100*(2^2-1)*0.20 = 100*3*0.20 = 60
    """
    signals = [{"resultado": "GREEN", "placar": "3-2", "tentativa": 2}]

    result = calculate_roi_complementares(signals, _OVER_2_5_CONFIG, stake=100.0, gale_on=True)

    over_3_5 = next(m for m in result["por_mercado"] if m["slug"] == "over_3_5")
    assert over_3_5["investido"] == pytest.approx(60.0)   # 100*(2^2-1)*0.20
    assert over_3_5["lucro"] == pytest.approx(100.0)       # 120 - 20


def test_calculate_roi_complementares_gale_red_t4():
    """
    1 sinal RED tentativa=4, stake=100, gale_on=True:
    - Todas complementares RED (D-08)
    - over_3_5: investido = 100*(2^4-1)*0.20 = 100*15*0.20 = 300
    """
    signals = [{"resultado": "RED", "placar": "1-1", "tentativa": 4}]

    result = calculate_roi_complementares(signals, _OVER_2_5_CONFIG, stake=100.0, gale_on=True)

    over_3_5 = next(m for m in result["por_mercado"] if m["slug"] == "over_3_5")
    assert over_3_5["investido"] == pytest.approx(300.0)   # 100*(2^4-1)*0.20
    assert over_3_5["lucro"] == pytest.approx(-300.0)


def test_calculate_roi_complementares_decimal_percentual():
    """
    Verifica que Decimal do PostgreSQL (simulado como float) e tratado corretamente
    — percentual e odd_ref como float nativo (sem erro de tipo Decimal*float).
    """
    from decimal import Decimal

    config_decimal = [
        {
            "id": 1, "slug": "over_3_5", "nome_display": "Over 3.5",
            "percentual": Decimal("0.20"), "odd_ref": Decimal("4.00"),
            "regra_validacao": "over_3_5",
        }
    ]
    signals = [{"resultado": "GREEN", "placar": "3-2", "tentativa": 1}]

    # Nao deve lancar TypeError mesmo com Decimal
    result = calculate_roi_complementares(signals, config_decimal, stake=100.0, gale_on=False)

    over_3_5 = next(m for m in result["por_mercado"] if m["slug"] == "over_3_5")
    assert over_3_5["lucro"] == pytest.approx(60.0)


# ---------------------------------------------------------------------------
# calculate_equity_curve tests — puro Python, sem DB
# ---------------------------------------------------------------------------


def test_calculate_equity_curve():
    """3 sinais GREEN, GREEN, RED (DESC) -> y_fixa=[9.0, 18.0, 8.0], cores corretas."""
    if not _IMPORTS_OK:
        pytest.skip(f"helpertips.queries import failed: {_IMPORT_ERROR}")
    signals_desc = [
        {"resultado": "RED", "tentativa": 1},    # mais recente (DESC)
        {"resultado": "GREEN", "tentativa": 1},
        {"resultado": "GREEN", "tentativa": 1},   # mais antigo
    ]
    result = calculate_equity_curve(signals_desc, stake=10.0, odd=1.90)
    assert result["x"] == [1, 2, 3]
    assert result["y_fixa"] == [9.0, 18.0, 8.0]
    assert result["colors"] == ["#28a745", "#28a745", "#dc3545"]


def test_calculate_equity_curve_with_gale():
    """Sinais com tentativa variavel: y_gale diverge de y_fixa."""
    if not _IMPORTS_OK:
        pytest.skip(f"helpertips.queries import failed: {_IMPORT_ERROR}")
    signals_desc = [
        {"resultado": "GREEN", "tentativa": 1},
        {"resultado": "GREEN", "tentativa": 2},   # gale 2a tentativa
        {"resultado": "RED", "tentativa": 1},
    ]
    # Reversal: RED(t=1), GREEN(t=2), GREEN(t=1) cronologico
    result = calculate_equity_curve(signals_desc, stake=10.0, odd=1.90)
    # RED t=1: fixa=-10, gale=-10
    # GREEN t=2: fixa=+9->-1, gale=winning=20*(0.9)-10=+8->-2
    # GREEN t=1: fixa=+9->+8, gale=+9->+7
    assert result["y_fixa"][-1] == pytest.approx(8.0)
    assert result["y_gale"][-1] != result["y_fixa"][-1]  # gale diverge


def test_equity_curve_reversal():
    """Confirma que sinais DESC sao revertidos: RED (oldest) vira primeiro ponto."""
    if not _IMPORTS_OK:
        pytest.skip(f"helpertips.queries import failed: {_IMPORT_ERROR}")
    signals_desc = [
        {"resultado": "GREEN", "tentativa": 1, "id": "newest"},
        {"resultado": "RED", "tentativa": 1, "id": "oldest"},
    ]
    result = calculate_equity_curve(signals_desc, stake=10.0, odd=1.90)
    # Primeiro ponto deve ser RED (oldest), nao GREEN
    assert result["colors"][0] == "#dc3545"  # RED primeiro (cronologico)
    assert result["colors"][1] == "#28a745"  # GREEN depois


def test_equity_curve_empty():
    """Sem sinais resolvidos -> estrutura vazia com todas as listas vazias."""
    if not _IMPORTS_OK:
        pytest.skip(f"helpertips.queries import failed: {_IMPORT_ERROR}")
    result = calculate_equity_curve([], stake=10.0, odd=1.90)
    assert result == {"x": [], "y_fixa": [], "y_gale": [], "colors": [], "annotations": []}


def test_equity_curve_annotations():
    """Streak >= 5 consecutivos -> annotations nao vazio."""
    if not _IMPORTS_OK:
        pytest.skip(f"helpertips.queries import failed: {_IMPORT_ERROR}")
    signals_desc = [{"resultado": "GREEN", "tentativa": 1} for _ in range(6)]
    result = calculate_equity_curve(signals_desc, stake=10.0, odd=1.90)
    assert len(result["annotations"]) >= 1
    assert "5" in result["annotations"][0]["text"] or "streak" in result["annotations"][0]["text"].lower()


# ---------------------------------------------------------------------------
# calculate_streaks tests — puro Python, sem DB
# ---------------------------------------------------------------------------


def test_calculate_streaks():
    """[G,G,G,R,G] em DESC -> current=1, current_type=GREEN, max_green=3, max_red=1."""
    if not _IMPORTS_OK:
        pytest.skip(f"helpertips.queries import failed: {_IMPORT_ERROR}")
    signals_desc = [
        {"resultado": "GREEN"},  # mais recente (DESC)
        {"resultado": "RED"},
        {"resultado": "GREEN"},
        {"resultado": "GREEN"},
        {"resultado": "GREEN"},  # mais antigo
    ]
    result = calculate_streaks(signals_desc)
    assert result["current"] == 1
    assert result["current_type"] == "GREEN"
    assert result["max_green"] == 3
    assert result["max_red"] == 1


def test_calculate_streaks_all_green():
    """[G,G,G] em DESC -> current=3, max_green=3, max_red=0."""
    if not _IMPORTS_OK:
        pytest.skip(f"helpertips.queries import failed: {_IMPORT_ERROR}")
    signals_desc = [{"resultado": "GREEN"} for _ in range(3)]
    result = calculate_streaks(signals_desc)
    assert result == {"current": 3, "current_type": "GREEN", "max_green": 3, "max_red": 0}


def test_calculate_streaks_empty():
    """Lista vazia -> todos zeros e current_type=None."""
    if not _IMPORTS_OK:
        pytest.skip(f"helpertips.queries import failed: {_IMPORT_ERROR}")
    result = calculate_streaks([])
    assert result == {"current": 0, "current_type": None, "max_green": 0, "max_red": 0}


# ---------------------------------------------------------------------------
# get_heatmap_data tests — requer DB
# ---------------------------------------------------------------------------


def test_get_heatmap_data(db_conn):
    """3 sinais em horas/dias diferentes -> z com valores corretos nas celulas."""
    import datetime
    # Sinal 1: segunda (DOW=1), hora 10 -> GREEN
    # Sinal 2: segunda (DOW=1), hora 10 -> RED (total=2, greens=1, win_rate=50%)
    # Sinal 3: sexta (DOW=5), hora 20 -> GREEN (total=1, greens=1, win_rate=100%)
    monday_10h = datetime.datetime(2026, 3, 30, 10, 0, 0)   # segunda-feira hora 10
    friday_20h = datetime.datetime(2026, 4, 3, 20, 0, 0)    # sexta-feira hora 20

    with db_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO signals (message_id, liga, entrada, horario, resultado, raw_text, received_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (8001, "Liga A", "Over 2.5", "10:00", "GREEN", "raw", monday_10h, monday_10h),
        )
        cur.execute(
            """
            INSERT INTO signals (message_id, liga, entrada, horario, resultado, raw_text, received_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (8002, "Liga A", "Over 2.5", "10:00", "RED", "raw", monday_10h, monday_10h),
        )
        cur.execute(
            """
            INSERT INTO signals (message_id, liga, entrada, horario, resultado, raw_text, received_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (8003, "Liga A", "Over 2.5", "20:00", "GREEN", "raw", friday_20h, friday_20h),
        )
    db_conn.commit()

    result = get_heatmap_data(db_conn)

    assert result["x"] == ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sab"]
    assert result["y"] == [f"{h:02d}h" for h in range(24)]
    assert len(result["z"]) == 24
    assert len(result["z"][0]) == 7

    # Segunda (DOW=1), hora 10: 1 GREEN de 2 -> 50.0%
    assert result["z"][10][1] == pytest.approx(50.0)
    # Sexta (DOW=5), hora 20: 1 GREEN de 1 -> 100.0%
    assert result["z"][20][5] == pytest.approx(100.0)
    # Celulas sem dados sao None
    assert result["z"][0][0] is None


def test_get_heatmap_data_empty(db_conn):
    """Sem sinais -> z com todas as celulas None."""
    result = get_heatmap_data(db_conn)

    assert result["x"] == ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sab"]
    assert result["y"] == [f"{h:02d}h" for h in range(24)]
    assert result["z"] == [[None] * 7 for _ in range(24)]


# ---------------------------------------------------------------------------
# get_winrate_by_dow tests — requer DB
# ---------------------------------------------------------------------------


def test_get_winrate_by_dow(db_conn):
    """4 sinais em 2 dias diferentes -> lista de dicts com win_rate por dia."""
    import datetime
    monday = datetime.datetime(2026, 3, 30, 10, 0, 0)   # segunda (DOW=1)
    friday = datetime.datetime(2026, 4, 3, 10, 0, 0)    # sexta (DOW=5)

    with db_conn.cursor() as cur:
        # Segunda: 2 GREEN, 1 RED -> win_rate = 66.7%
        for mid, res, ts in [(7001, "GREEN", monday), (7002, "GREEN", monday), (7003, "RED", monday)]:
            cur.execute(
                "INSERT INTO signals (message_id, liga, entrada, horario, resultado, raw_text, received_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (mid, "Liga A", "Over 2.5", "10:00", res, "raw", ts, ts),
            )
        # Sexta: 1 GREEN -> win_rate = 100%
        cur.execute(
            "INSERT INTO signals (message_id, liga, entrada, horario, resultado, raw_text, received_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (7004, "Liga A", "Over 2.5", "10:00", "GREEN", "raw", friday, friday),
        )
    db_conn.commit()

    result = get_winrate_by_dow(db_conn)

    assert isinstance(result, list)
    assert len(result) == 2  # apenas segunda e sexta

    dias = {r["dia"]: r for r in result}
    assert 1 in dias  # segunda
    assert 5 in dias  # sexta
    assert dias[1]["dia_nome"] == "Seg"
    assert dias[5]["dia_nome"] == "Sex"
    assert dias[1]["greens"] == 2
    assert dias[1]["total"] == 3
    assert dias[1]["win_rate"] == pytest.approx(66.7)
    assert dias[5]["win_rate"] == pytest.approx(100.0)


def test_get_winrate_by_dow_empty(db_conn):
    """Sem sinais resolvidos -> lista vazia."""
    result = get_winrate_by_dow(db_conn)
    assert result == []


# ---------------------------------------------------------------------------
# get_gale_analysis tests — requer DB
# ---------------------------------------------------------------------------


def test_get_gale_analysis(db_conn):
    """5 sinais com tentativa variada -> lista com 3 dicts com win_rate correto por tentativa."""
    # tentativa=1: 2 sinais (1 GREEN, 1 RED) -> win_rate=50.0%
    # tentativa=2: 2 sinais (2 GREEN) -> win_rate=100.0%
    # tentativa=3: 1 sinal (1 RED) -> win_rate=0.0%
    with db_conn.cursor() as cur:
        cur.execute("INSERT INTO signals (message_id, liga, entrada, resultado, tentativa, raw_text) VALUES (%s, %s, %s, %s, %s, %s)",
                    (5001, "Liga A", "Over 2.5", "GREEN", 1, "raw"))
        cur.execute("INSERT INTO signals (message_id, liga, entrada, resultado, tentativa, raw_text) VALUES (%s, %s, %s, %s, %s, %s)",
                    (5002, "Liga A", "Over 2.5", "RED", 1, "raw"))
        cur.execute("INSERT INTO signals (message_id, liga, entrada, resultado, tentativa, raw_text) VALUES (%s, %s, %s, %s, %s, %s)",
                    (5003, "Liga A", "Over 2.5", "GREEN", 2, "raw"))
        cur.execute("INSERT INTO signals (message_id, liga, entrada, resultado, tentativa, raw_text) VALUES (%s, %s, %s, %s, %s, %s)",
                    (5004, "Liga A", "Over 2.5", "GREEN", 2, "raw"))
        cur.execute("INSERT INTO signals (message_id, liga, entrada, resultado, tentativa, raw_text) VALUES (%s, %s, %s, %s, %s, %s)",
                    (5005, "Liga A", "Over 2.5", "RED", 3, "raw"))
    db_conn.commit()

    result = get_gale_analysis(db_conn)

    assert len(result) == 3
    assert result[0]["tentativa"] == 1
    assert result[0]["win_rate"] == 50.0
    assert result[1]["tentativa"] == 2
    assert result[1]["win_rate"] == 100.0
    assert result[2]["tentativa"] == 3
    assert result[2]["win_rate"] == 0.0


def test_get_gale_analysis_excludes_null(db_conn):
    """Sinais com tentativa=None sao excluidos da analise de gale."""
    with db_conn.cursor() as cur:
        cur.execute("INSERT INTO signals (message_id, liga, entrada, resultado, tentativa, raw_text) VALUES (%s, %s, %s, %s, %s, %s)",
                    (5010, "Liga A", "Over 2.5", "GREEN", 1, "raw"))
        cur.execute("INSERT INTO signals (message_id, liga, entrada, resultado, tentativa, raw_text) VALUES (%s, %s, %s, %s, %s, %s)",
                    (5011, "Liga A", "Over 2.5", "RED", None, "raw"))
    db_conn.commit()

    result = get_gale_analysis(db_conn)

    assert len(result) == 1
    assert result[0]["tentativa"] == 1


def test_get_gale_analysis_empty(db_conn):
    """Sem sinais com tentativa definida -> lista vazia."""
    result = get_gale_analysis(db_conn)
    assert result == []


# ---------------------------------------------------------------------------
# get_volume_by_day tests — requer DB
# ---------------------------------------------------------------------------


def test_get_volume_by_day(db_conn):
    """5 sinais em 2 dias diferentes -> lista com 2 dicts {data, count}."""
    import datetime
    day1 = datetime.datetime(2026, 3, 30, 10, 0, 0)
    day2 = datetime.datetime(2026, 4, 1, 10, 0, 0)

    with db_conn.cursor() as cur:
        for mid in [6001, 6002, 6003]:
            cur.execute(
                "INSERT INTO signals (message_id, liga, entrada, horario, resultado, raw_text, received_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (mid, "Liga A", "Over 2.5", "10:00", "GREEN", "raw", day1, day1),
            )
        for mid in [6004, 6005]:
            cur.execute(
                "INSERT INTO signals (message_id, liga, entrada, horario, resultado, raw_text, received_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (mid, "Liga A", "Over 2.5", "10:00", "RED", "raw", day2, day2),
            )
    db_conn.commit()

    result = get_volume_by_day(db_conn)

    assert len(result) == 2
    assert result[0]["count"] + result[1]["count"] == 5
    assert all("data" in r and "count" in r for r in result)


def test_get_volume_by_day_empty(db_conn):
    """Sem sinais -> lista vazia."""
    result = get_volume_by_day(db_conn)
    assert result == []


# ---------------------------------------------------------------------------
# get_cross_dimensional tests — requer DB
# ---------------------------------------------------------------------------


def test_get_cross_dimensional(db_conn):
    """Sinais com combinacoes de liga/entrada -> breakdown cross-dimensional ordenado por win_rate DESC."""
    with db_conn.cursor() as cur:
        # (Liga A, Over 2.5): 2 GREEN, 0 RED -> win_rate=100%
        cur.execute("INSERT INTO signals (message_id, liga, entrada, resultado, raw_text) VALUES (%s, %s, %s, %s, %s)",
                    (4001, "Liga A", "Over 2.5", "GREEN", "raw"))
        cur.execute("INSERT INTO signals (message_id, liga, entrada, resultado, raw_text) VALUES (%s, %s, %s, %s, %s)",
                    (4002, "Liga A", "Over 2.5", "GREEN", "raw"))
        # (Liga A, Ambas Marcam): 1 GREEN, 1 RED -> win_rate=50%
        cur.execute("INSERT INTO signals (message_id, liga, entrada, resultado, raw_text) VALUES (%s, %s, %s, %s, %s)",
                    (4003, "Liga A", "Ambas Marcam", "GREEN", "raw"))
        cur.execute("INSERT INTO signals (message_id, liga, entrada, resultado, raw_text) VALUES (%s, %s, %s, %s, %s)",
                    (4004, "Liga A", "Ambas Marcam", "RED", "raw"))
        # (Liga B, Over 2.5): 0 GREEN, 1 RED -> win_rate=0%
        cur.execute("INSERT INTO signals (message_id, liga, entrada, resultado, raw_text) VALUES (%s, %s, %s, %s, %s)",
                    (4005, "Liga B", "Over 2.5", "RED", "raw"))
    db_conn.commit()

    result = get_cross_dimensional(db_conn)

    assert len(result) >= 2
    assert all(k in result[0] for k in ("liga", "entrada", "win_rate", "total"))
    # Ordenado por win_rate DESC
    assert result[0]["win_rate"] >= result[-1]["win_rate"]


def test_get_cross_dimensional_empty(db_conn):
    """Sem sinais -> lista vazia."""
    result = get_cross_dimensional(db_conn)
    assert result == []


# ---------------------------------------------------------------------------
# get_parse_failures_detail tests — requer DB
# ---------------------------------------------------------------------------


def test_get_parse_failures_detail(db_conn):
    """3 parse_failures inseridas -> lista de 3 dicts com raw_text, failure_reason, received_at."""
    with db_conn.cursor() as cur:
        for i in range(3):
            cur.execute("INSERT INTO parse_failures (raw_text, failure_reason) VALUES (%s, %s)",
                        (f"msg {i}", "no_liga_match"))
    db_conn.commit()

    result = get_parse_failures_detail(db_conn)

    assert len(result) == 3
    assert "raw_text" in result[0]
    assert "failure_reason" in result[0]
    assert "received_at" in result[0]


def test_get_parse_failures_detail_limit(db_conn):
    """Inserir 5 falhas, chamar com limit=2 -> retorna apenas 2."""
    with db_conn.cursor() as cur:
        for i in range(5):
            cur.execute("INSERT INTO parse_failures (raw_text, failure_reason) VALUES (%s, %s)",
                        (f"msg {i}", "no_liga_match"))
    db_conn.commit()

    result = get_parse_failures_detail(db_conn, limit=2)

    assert len(result) == 2


def test_get_parse_failures_detail_empty(db_conn):
    """Sem falhas -> lista vazia."""
    result = get_parse_failures_detail(db_conn)
    assert result == []


# ---------------------------------------------------------------------------
# get_winrate_by_periodo tests — requer DB (ANAL-03)
# ---------------------------------------------------------------------------


def test_get_winrate_by_periodo(db_conn):
    """Sinais com periodo definido -> lista com win_rate por periodo (1T/2T), excluindo NULL."""
    with db_conn.cursor() as cur:
        # 2 sinais periodo='1T': 1 GREEN, 1 RED -> win_rate=50%
        cur.execute("INSERT INTO signals (message_id, liga, entrada, resultado, periodo, tentativa, raw_text) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (10001, "Liga A", "Over 2.5", "GREEN", "1T", 1, "raw"))
        cur.execute("INSERT INTO signals (message_id, liga, entrada, resultado, periodo, tentativa, raw_text) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (10002, "Liga A", "Over 2.5", "RED", "1T", 1, "raw"))
        # 2 sinais periodo='2T': 2 GREEN -> win_rate=100%
        cur.execute("INSERT INTO signals (message_id, liga, entrada, resultado, periodo, tentativa, raw_text) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (10003, "Liga B", "Over 2.5", "GREEN", "2T", 1, "raw"))
        cur.execute("INSERT INTO signals (message_id, liga, entrada, resultado, periodo, tentativa, raw_text) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (10004, "Liga B", "Over 2.5", "GREEN", "2T", 1, "raw"))
        # 1 sinal com periodo=None (deve ser excluido)
        cur.execute("INSERT INTO signals (message_id, liga, entrada, resultado, periodo, tentativa, raw_text) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (10005, "Liga A", "Over 2.5", "GREEN", None, 1, "raw"))
    db_conn.commit()

    result = get_winrate_by_periodo(db_conn)

    assert len(result) == 2
    assert all(k in result[0] for k in ("periodo", "greens", "total", "win_rate"))

    periodo_1t = next(r for r in result if r["periodo"] == "1T")
    assert periodo_1t["win_rate"] == 50.0

    periodo_2t = next(r for r in result if r["periodo"] == "2T")
    assert periodo_2t["win_rate"] == 100.0


def test_get_winrate_by_periodo_empty(db_conn):
    """Sem sinais com periodo definido -> lista vazia."""
    # Inserir sinal com periodo=None (deve ser excluido)
    with db_conn.cursor() as cur:
        cur.execute("INSERT INTO signals (message_id, liga, entrada, resultado, periodo, raw_text) VALUES (%s, %s, %s, %s, %s, %s)",
                    (10010, "Liga A", "Over 2.5", "GREEN", None, "raw"))
    db_conn.commit()

    result = get_winrate_by_periodo(db_conn)
    assert result == []
