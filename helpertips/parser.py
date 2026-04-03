"""
parser.py — Signal Message Parser

Pure function that extracts structured fields from Telegram signal messages.
Zero external dependencies — only stdlib (re, datetime).

The parser is the bridge between raw Telegram text and structured database
records. If parsing fails, no data is captured.

Architecture note: This module intentionally has NO imports from db, store,
or telethon. It is a pure function: same input always produces same output.
"""

import re
from datetime import datetime

# ---------------------------------------------------------------------------
# Regex patterns for field extraction
# ---------------------------------------------------------------------------

# LIGA: optional soccer emoji, then "LIGA:" label
LIGA_PATTERN = re.compile(
    r'(?:⚽\s*)?LIGA\s*:\s*(.+?)(?:\n|$)',
    re.IGNORECASE,
)

# ENTRADA: optional target emoji, then "Entrada:" label
ENTRADA_PATTERN = re.compile(
    r'(?:🎯\s*)?Entrada\s*:\s*(.+?)(?:\n|$)',
    re.IGNORECASE,
)

# HORARIO: optional clock emoji, then "Horario:"/"Horário:" label, HH:MM
HORARIO_PATTERN = re.compile(
    r'(?:⏰\s*)?Hor[aá]rio\s*:\s*(\d{1,2}:\d{2})(?:\n|$)',
    re.IGNORECASE,
)

# RESULTADO: checkmark (✅) or X (❌) emoji followed by GREEN or RED
RESULTADO_PATTERN = re.compile(
    r'(?:✅|❌)\s*(GREEN|RED)',
    re.IGNORECASE,
)

# PLACAR: "Placar: X-Y" format
PLACAR_PATTERN = re.compile(
    r'Placar\s*:\s*(\d+-\d+)',
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Day-of-week mapping (0=Mon .. 6=Sun) -> short label
# ---------------------------------------------------------------------------

_WEEKDAY_LABELS = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]


def parse_message(text: str, message_id: int) -> dict | None:
    """
    Parse a Telegram signal message and return a structured dict.

    Parameters
    ----------
    text : str
        Raw message text as received from Telegram.
    message_id : int
        Telegram message ID, preserved in the returned dict.

    Returns
    -------
    dict | None
        Structured signal data if the message looks like a valid signal,
        None otherwise (empty text, no LIGA field, or unrecognizable format).

    Return dict keys
    ----------------
    - message_id  : int   — same as the input message_id
    - liga        : str   — league name (e.g. "Euro League")
    - entrada     : str | None — bet type (e.g. "Over 1.5 Gols")
    - horario     : str | None — time as "HH:MM"
    - periodo     : None  — not parsed from message; reserved for future use
    - dia_semana  : str   — short weekday label derived from current date
    - resultado   : str | None — "GREEN" or "RED", None if not yet available
    - placar      : str | None — score "X-Y", None if not present
    - raw_text    : str   — original input text, always stored verbatim
    """
    # Guard: empty or None text
    if not text:
        return None

    # Gate: LIGA must be present — this is what distinguishes a signal
    # from regular chat messages. If no LIGA, return None immediately.
    liga_match = LIGA_PATTERN.search(text)
    if not liga_match:
        return None

    liga = liga_match.group(1).strip()

    # Extract remaining fields — each may be absent (None)
    entrada_match = ENTRADA_PATTERN.search(text)
    entrada = entrada_match.group(1).strip() if entrada_match else None

    horario_match = HORARIO_PATTERN.search(text)
    horario = horario_match.group(1).strip() if horario_match else None

    resultado_match = RESULTADO_PATTERN.search(text)
    resultado = resultado_match.group(1).upper() if resultado_match else None

    placar_match = PLACAR_PATTERN.search(text)
    placar = placar_match.group(1).strip() if placar_match else None

    # Derive dia_semana from current date at parse time
    dia_semana = _WEEKDAY_LABELS[datetime.now().weekday()]

    return {
        "message_id": message_id,
        "liga": liga,
        "entrada": entrada,
        "horario": horario,
        "periodo": None,
        "dia_semana": dia_semana,
        "resultado": resultado,
        "placar": placar,
        "raw_text": text,
    }
