"""
Unit tests for parser.py — Signal Message Parser.

Covers requirements PARS-01 through PARS-07 and LIST-04.
All fixtures are based on the REAL message format from {VIP} ExtremeTips.

Format observed:
  - New signal: header + Liga + Entrada recomendada + 4 tentativas with times
  - GREEN: same as new but one tentativa has "✅ (X-Y)" inline + GREEN block at bottom
  - RED: same as new but ends with "✖ Red" (no ✅ on any tentativa)
"""

import pytest
from helpertips.parser import parse_message


# ---------------------------------------------------------------------------
# PARS-01: liga extraction
# ---------------------------------------------------------------------------

def test_parse_liga(signal_new):
    """PARS-01: liga field is extracted from the 🏆 Liga: line."""
    result = parse_message(signal_new, 1)
    assert result is not None
    assert result["liga"] == "Superliga"


# ---------------------------------------------------------------------------
# PARS-02: entrada extraction
# ---------------------------------------------------------------------------

def test_parse_entrada(signal_new):
    """PARS-02: entrada (mercado) extracted from 📈 Entrada recomendada: line."""
    result = parse_message(signal_new, 1)
    assert result is not None
    assert result["entrada"] == "Over 2.5"


def test_parse_entrada_strips_fire_emoji(signal_new):
    """PARS-02: 🔥 emojis around the mercado are stripped from entrada."""
    result = parse_message(signal_new, 1)
    assert result is not None
    # Must not contain the fire emoji
    assert "🔥" not in result["entrada"]


# ---------------------------------------------------------------------------
# PARS-03: horario extraction (first tentativa time)
# ---------------------------------------------------------------------------

def test_parse_horario(signal_new):
    """PARS-03: horario is the FIRST tentativa time (HH:MM)."""
    result = parse_message(signal_new, 1)
    assert result is not None
    assert result["horario"] == "06:18"


def test_parse_horario_from_green(signal_green_with_placar):
    """PARS-03: horario is still the first tentativa time even in a GREEN message."""
    result = parse_message(signal_green_with_placar, 2)
    assert result is not None
    assert result["horario"] == "06:18"


# ---------------------------------------------------------------------------
# PARS-04: resultado extraction
# ---------------------------------------------------------------------------

def test_parse_resultado_green(signal_green_with_placar):
    """PARS-04: 'GREEN' is extracted when GREEN block is present."""
    result = parse_message(signal_green_with_placar, 2)
    assert result is not None
    assert result["resultado"] == "GREEN"


def test_parse_resultado_red(signal_red_with_placar):
    """PARS-04: 'RED' is extracted when ✖ Red appears at bottom."""
    result = parse_message(signal_red_with_placar, 3)
    assert result is not None
    assert result["resultado"] == "RED"


def test_parse_resultado_none_for_new(signal_new):
    """PARS-04: resultado is None for a new signal without result."""
    result = parse_message(signal_new, 1)
    assert result is not None
    assert result["resultado"] is None


# ---------------------------------------------------------------------------
# PARS-05: placar extraction
# ---------------------------------------------------------------------------

def test_parse_placar(signal_green_with_placar):
    """PARS-05: placar 'X-Y' extracted from the ✅ (X-Y) tentativa line."""
    result = parse_message(signal_green_with_placar, 2)
    assert result is not None
    assert result["placar"] == "2-1"


def test_parse_placar_none_when_absent(signal_new):
    """PARS-05: placar is None on a new signal (no ✅ yet)."""
    result = parse_message(signal_new, 1)
    assert result is not None
    assert result["placar"] is None


def test_parse_placar_none_for_red(signal_red_with_placar):
    """PARS-05: placar is None for RED signals (no ✅ line, no score)."""
    result = parse_message(signal_red_with_placar, 3)
    assert result is not None
    assert result["placar"] is None


# ---------------------------------------------------------------------------
# PARS-06: raw_text always stored
# ---------------------------------------------------------------------------

def test_raw_text_always_stored(signal_new):
    """PARS-06: raw_text equals the original input text exactly."""
    result = parse_message(signal_new, 1)
    assert result is not None
    assert result["raw_text"] == signal_new


def test_raw_text_stored_for_green(signal_green_with_placar):
    """PARS-06: raw_text equals original for edited GREEN message."""
    result = parse_message(signal_green_with_placar, 2)
    assert result is not None
    assert result["raw_text"] == signal_green_with_placar


# ---------------------------------------------------------------------------
# PARS-07: returns None for unrecognizable messages
# ---------------------------------------------------------------------------

def test_parse_returns_none_for_garbage(garbage_message):
    """PARS-07: None returned for non-signal text (coverage tracking)."""
    result = parse_message(garbage_message, 456)
    assert result is None


# ---------------------------------------------------------------------------
# LIST-04: empty text returns None
# ---------------------------------------------------------------------------

def test_empty_text_returns_none():
    """LIST-04: None returned for empty string input."""
    result = parse_message("", 789)
    assert result is None


# ---------------------------------------------------------------------------
# message_id passthrough
# ---------------------------------------------------------------------------

def test_message_id_preserved(signal_new):
    """message_id passed as argument is preserved in returned dict."""
    result = parse_message(signal_new, 42)
    assert result is not None
    assert result["message_id"] == 42


# ---------------------------------------------------------------------------
# GREEN without placar edge case
# ---------------------------------------------------------------------------

def test_green_without_placar(signal_green_no_placar):
    """GREEN result without placar score: resultado='GREEN', placar=None."""
    result = parse_message(signal_green_no_placar, 10)
    assert result is not None
    assert result["resultado"] == "GREEN"
    assert result["placar"] is None


# ---------------------------------------------------------------------------
# tentativa field (new in real format)
# ---------------------------------------------------------------------------

def test_tentativa_hit_on_green(signal_green_with_placar):
    """Tentativa 2 hit the GREEN — tentativa field is 2."""
    result = parse_message(signal_green_with_placar, 2)
    assert result is not None
    assert result["tentativa"] == 2


def test_tentativa_hit_on_green_first(signal_green_no_placar):
    """Tentativa 3 has ✅ inline (no score) — tentativa field is 3."""
    result = parse_message(signal_green_no_placar, 10)
    assert result is not None
    assert result["tentativa"] == 3


def test_tentativa_none_for_new(signal_new):
    """No tentativa has hit yet on new signal — tentativa is None."""
    result = parse_message(signal_new, 1)
    assert result is not None
    assert result["tentativa"] is None


def test_tentativa_none_for_red(signal_red_with_placar):
    """RED signal: no tentativa hit — tentativa is None."""
    result = parse_message(signal_red_with_placar, 3)
    assert result is not None
    assert result["tentativa"] is None


# ---------------------------------------------------------------------------
# Full end-to-end: RED signal
# ---------------------------------------------------------------------------

def test_red_full_end_to_end(signal_red_with_placar):
    """End-to-end: RED signal with all fields checked."""
    result = parse_message(signal_red_with_placar, 3)
    assert result is not None
    assert result["liga"] == "Euro League"
    assert result["entrada"] == "Ambas Marcam"
    assert result["horario"] == "10:05"
    assert result["resultado"] == "RED"
    assert result["placar"] is None
    assert result["tentativa"] is None
    assert result["raw_text"] == signal_red_with_placar
    assert result["message_id"] == 3


# ---------------------------------------------------------------------------
# Full end-to-end: GREEN signal with tentativa 2
# ---------------------------------------------------------------------------

def test_green_full_end_to_end(signal_green_with_placar):
    """End-to-end: GREEN signal with tentativa 2 and score 2-1."""
    result = parse_message(signal_green_with_placar, 99)
    assert result is not None
    assert result["liga"] == "Superliga"
    assert result["entrada"] == "Over 2.5"
    assert result["horario"] == "06:18"
    assert result["resultado"] == "GREEN"
    assert result["placar"] == "2-1"
    assert result["tentativa"] == 2
    assert result["message_id"] == 99


# ---------------------------------------------------------------------------
# Return dict contract (all expected keys present)
# ---------------------------------------------------------------------------

def test_return_dict_keys(signal_new):
    """Return dict must contain all expected keys for store.py compatibility."""
    result = parse_message(signal_new, 1)
    assert result is not None
    expected_keys = {
        "message_id", "liga", "entrada", "horario", "periodo",
        "dia_semana", "resultado", "placar", "tentativa", "raw_text",
    }
    assert set(result.keys()) == expected_keys


def test_periodo_always_none(signal_new):
    """periodo is always None — reserved for future use."""
    result = parse_message(signal_new, 1)
    assert result is not None
    assert result["periodo"] is None


def test_dia_semana_is_string(signal_new):
    """dia_semana is a 3-char lowercase string from the weekday labels."""
    result = parse_message(signal_new, 1)
    assert result is not None
    assert result["dia_semana"] in {"seg", "ter", "qua", "qui", "sex", "sab", "dom"}
