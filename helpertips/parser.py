"""
parser.py — Signal Message Parser

Pure function that extracts structured fields from Telegram signal messages
from the {VIP} ExtremeTips group.

Zero external dependencies — only stdlib (re, datetime).

The parser is the bridge between raw Telegram text and structured database
records. If parsing fails, no data is captured.

Architecture note: This module intentionally has NO imports from db, store,
or telethon. It is a pure function: same input always produces same output.

Real message format (as observed in {VIP} ExtremeTips group):

  New signal (PENDENTE):
    ⚽ {VIP} ExtremeTips - Futebol Virtual Bet365
    🏆 Liga: [Nome da Liga]
    📈 Entrada recomendada: 🔥 [Mercado] 🔥
    1️⃣ roboextremetips.com.br ⏳ HH:MM
    2️⃣ roboextremetips.com.br ⏳ HH:MM
    3️⃣ roboextremetips.com.br ⏳ HH:MM
    4️⃣ roboextremetips.com.br ⏳ HH:MM

  GREEN (edited):
    ... same as new signal ...
    2️⃣ roboextremetips.com.br ⏳ HH:MM ✅ (2-1)
    ...
    GREEN 💰💰💰😎😜😎
    ✅✅✅✅✅✅✅✅✅

  RED (edited):
    ... same as new signal (no ✅ on any tentativa) ...
    ✖ Red
"""

import re
from datetime import datetime

# ---------------------------------------------------------------------------
# Regex patterns for field extraction — tuned to real message format
# ---------------------------------------------------------------------------

# GATE: The message must contain the group header or the Liga label.
# Either "{VIP} ExtremeTips" in the header OR "🏆 Liga:" line.
GATE_PATTERN = re.compile(
    r'ExtremeTips|🏆\s*Liga:',
    re.IGNORECASE,
)

# LIGA: after the trophy emoji and "Liga:" label
LIGA_PATTERN = re.compile(
    r'Liga:\s*(.+?)(?:\n|$)',
    re.IGNORECASE,
)

# ENTRADA (mercado): after "Entrada recomendada:", surrounded by optional 🔥 and ** markdown
# Real format: **Entrada recomendada:** Ambas marcam  OR  Entrada recomendada: 🔥 Over 2.5 🔥
ENTRADA_PATTERN = re.compile(
    r'Entrada recomendada:\*{0,2}\s*🔥?\s*(.+?)\s*🔥?\s*(?:\n|$)',
    re.IGNORECASE,
)

# HORARIOS: all four tentativa lines — captures the time from each
# Format: 1️⃣ roboextremetips.com.br ⏳ HH:MM
TENTATIVA_PATTERN = re.compile(
    r'([1-4])️⃣[^\n]*?(\d{2}:\d{2})',
)

# GREEN result: the word "GREEN" as a standalone line (may have trailing emojis)
RESULTADO_GREEN_PATTERN = re.compile(
    r'\bGREEN\b',
    re.IGNORECASE,
)

# RED result: ✖ or ✗ followed by "Red" (the real format uses ✖)
RESULTADO_RED_PATTERN = re.compile(
    r'[✖✗]\s*Red',
    re.IGNORECASE,
)

# PLACAR: from the tentativa line that has ✅ — format: ✅ (X-Y) or ✅ __(X-Y)__
# Real format uses markdown bold: __(1-1)__ around the score
PLACAR_PATTERN = re.compile(
    r'✅\s*_*\(?(\d+-\d+)\)?_*',
)

# TENTATIVA: which number (1-4) has the ✅ on its line
TENTATIVA_HIT_PATTERN = re.compile(
    r'([1-4])️⃣[^\n]*?✅',
)


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
        None otherwise (empty text, no Liga field, or unrecognizable format).

    Return dict keys
    ----------------
    - message_id  : int        — same as the input message_id
    - liga        : str        — league name (e.g. "Superliga")
    - entrada     : str | None — bet type (e.g. "Over 2.5")
    - horario     : str | None — first tentativa time as "HH:MM"
    - periodo     : None       — not parsed; reserved for future use
    - dia_semana  : str        — short weekday label derived from current date
    - resultado   : str | None — "GREEN" or "RED", None if not yet available
    - placar      : str | None — score "X-Y" from the ✅ tentativa line
    - tentativa   : int | None — which attempt hit (1-4), None if no result
    - raw_text    : str        — original input text, always stored verbatim
    """
    # Guard: empty or None text
    if not text:
        return None

    # Gate: must look like a signal from {VIP} ExtremeTips
    # (either group header present, or Liga: label present)
    if not GATE_PATTERN.search(text):
        return None

    # LIGA must be present — this confirms it is a structured signal
    liga_match = LIGA_PATTERN.search(text)
    if not liga_match:
        return None

    liga = liga_match.group(1).strip().strip('*').strip()

    # ENTRADA (mercado) — optional but always present in real signals
    entrada_match = ENTRADA_PATTERN.search(text)
    entrada = entrada_match.group(1).strip().strip('*').strip() if entrada_match else None

    # HORARIO — use the FIRST tentativa time as the signal reference time
    tentativa_times = TENTATIVA_PATTERN.findall(text)
    if tentativa_times:
        # tentativa_times is a list of (number, time) tuples, sorted by number
        horario = sorted(tentativa_times, key=lambda t: int(t[0]))[0][1]
    else:
        horario = None

    # RESULTADO — check for GREEN first, then RED
    if RESULTADO_GREEN_PATTERN.search(text):
        resultado = "GREEN"
    elif RESULTADO_RED_PATTERN.search(text):
        resultado = "RED"
    else:
        resultado = None

    # PLACAR — from the tentativa line with ✅ (X-Y) annotation
    placar_match = PLACAR_PATTERN.search(text)
    placar = placar_match.group(1).strip() if placar_match else None

    # TENTATIVA — which attempt number (1-4) hit the result
    tentativa_hit_match = TENTATIVA_HIT_PATTERN.search(text)
    tentativa = int(tentativa_hit_match.group(1)) if tentativa_hit_match else None

    # Derive dia_semana from current date at parse time (int 0=Mon..6=Sun, matches SMALLINT column)
    dia_semana = datetime.now().weekday()

    return {
        "message_id": message_id,
        "liga": liga,
        "entrada": entrada,
        "horario": horario,
        "periodo": None,
        "dia_semana": dia_semana,
        "resultado": resultado,
        "placar": placar,
        "tentativa": tentativa,
        "raw_text": text,
    }
