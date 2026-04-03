"""
Unit tests for parser.py — Signal Message Parser.

Covers requirements PARS-01 through PARS-07 and LIST-04.

TDD approach: these tests are written before the implementation exists.
All tests must FAIL before parser.py is created (RED phase).
All tests must PASS after parser.py is created (GREEN phase).
"""

import pytest
from parser import parse_message


# ---------------------------------------------------------------------------
# PARS-01: liga extraction
# ---------------------------------------------------------------------------

def test_parse_liga(signal_new):
    """PARS-01: liga field is extracted correctly from a new signal."""
    result = parse_message(signal_new, 1)
    assert result is not None
    assert result["liga"] == "Euro League"


# ---------------------------------------------------------------------------
# PARS-02: entrada extraction
# ---------------------------------------------------------------------------

def test_parse_entrada(signal_new):
    """PARS-02: entrada field is extracted correctly from a new signal."""
    result = parse_message(signal_new, 1)
    assert result is not None
    assert result["entrada"] == "Over 1.5 Gols"


# ---------------------------------------------------------------------------
# PARS-03: horario extraction
# ---------------------------------------------------------------------------

def test_parse_horario(signal_new):
    """PARS-03: horario field is extracted as HH:MM string."""
    result = parse_message(signal_new, 1)
    assert result is not None
    assert result["horario"] == "14:30"


# ---------------------------------------------------------------------------
# PARS-04: resultado extraction
# ---------------------------------------------------------------------------

def test_parse_resultado_green(signal_green_with_placar):
    """PARS-04: 'GREEN' is extracted from edited message with checkmark emoji."""
    result = parse_message(signal_green_with_placar, 2)
    assert result is not None
    assert result["resultado"] == "GREEN"


def test_parse_resultado_red(signal_red_with_placar):
    """PARS-04: 'RED' is extracted from edited message with X emoji."""
    result = parse_message(signal_red_with_placar, 3)
    assert result is not None
    assert result["resultado"] == "RED"


def test_parse_resultado_none_for_new(signal_new):
    """PARS-04: resultado is None when no result emoji is present (new signal)."""
    result = parse_message(signal_new, 1)
    assert result is not None
    assert result["resultado"] is None


# ---------------------------------------------------------------------------
# PARS-05: placar extraction
# ---------------------------------------------------------------------------

def test_parse_placar(signal_green_with_placar):
    """PARS-05: placar 'X-Y' is extracted when present in message."""
    result = parse_message(signal_green_with_placar, 2)
    assert result is not None
    assert result["placar"] == "2-1"


def test_parse_placar_none_when_absent(signal_new):
    """PARS-05: placar is None when not in message."""
    result = parse_message(signal_new, 1)
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
    """GREEN result without placar: resultado='GREEN', placar=None."""
    result = parse_message(signal_green_no_placar, 10)
    assert result is not None
    assert result["resultado"] == "GREEN"
    assert result["placar"] is None


# ---------------------------------------------------------------------------
# RED with placar end-to-end
# ---------------------------------------------------------------------------

def test_red_with_placar_full(signal_red_with_placar):
    """End-to-end: RED signal with all fields including placar."""
    result = parse_message(signal_red_with_placar, 3)
    assert result is not None
    assert result["liga"] == "Premier League"
    assert result["entrada"] == "Under 2.5 Gols"
    assert result["horario"] == "16:00"
    assert result["resultado"] == "RED"
    assert result["placar"] == "0-1"
    assert result["raw_text"] == signal_red_with_placar
    assert result["message_id"] == 3
