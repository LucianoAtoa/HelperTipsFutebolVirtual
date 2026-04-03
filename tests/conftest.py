"""
Shared pytest fixtures for HelperTips tests.

Provides sample Telegram signal message strings for parser testing,
based on the REAL message format observed in the {VIP} ExtremeTips group.

Real format:
  - Header: "⚽ {VIP} ExtremeTips - Futebol Virtual Bet365"
  - Liga line: "🏆 Liga: [Nome da Liga]"
  - Entrada line: "📈 Entrada recomendada: 🔥 [Mercado] 🔥"
  - Tentativas: "N️⃣ roboextremetips.com.br ⏳ HH:MM"
  - GREEN result: tentativa line with "✅ (X-Y)" + "GREEN 💰..." block
  - RED result: "✖ Red" at the bottom (no ✅ on any tentativa)
"""

import pytest


@pytest.fixture
def signal_new():
    """A new signal without result (PENDENTE). Liga=Superliga, entrada=Over 2.5."""
    return (
        "⚽ {VIP} ExtremeTips - Futebol Virtual Bet365\n"
        "\n"
        "🏆 Liga: Superliga\n"
        "📈 Entrada recomendada: 🔥 Over 2.5 🔥\n"
        "\n"
        "1️⃣ roboextremetips.com.br ⏳ 06:18\n"
        "2️⃣ roboextremetips.com.br ⏳ 06:21\n"
        "3️⃣ roboextremetips.com.br ⏳ 06:24\n"
        "4️⃣ roboextremetips.com.br ⏳ 06:27"
    )


@pytest.fixture
def signal_green_with_placar():
    """
    A GREEN signal — tentativa 2 hit with score (2-1).
    The ✅ is inline on the tentativa line, followed by GREEN block.
    Liga=Superliga, entrada=Over 2.5, horario=06:18 (first tentativa).
    """
    return (
        "⚽ {VIP} ExtremeTips - Futebol Virtual Bet365\n"
        "\n"
        "🏆 Liga: Superliga\n"
        "📈 Entrada recomendada: 🔥 Over 2.5 🔥\n"
        "\n"
        "1️⃣ roboextremetips.com.br ⏳ 06:18\n"
        "2️⃣ roboextremetips.com.br ⏳ 06:21 ✅ (2-1)\n"
        "3️⃣ roboextremetips.com.br ⏳ 06:24\n"
        "4️⃣ roboextremetips.com.br ⏳ 06:27\n"
        "\n"
        "GREEN 💰💰💰😎😜😎\n"
        "✅✅✅✅✅✅✅✅✅"
    )


@pytest.fixture
def signal_red_with_placar():
    """
    A RED signal — all tentativas failed, no ✅ inline, ends with ✖ Red.
    Liga=Euro League, entrada=Ambas Marcam, horario=10:05.
    No placar on RED (the group does not provide score on RED signals).
    """
    return (
        "⚽ {VIP} ExtremeTips - Futebol Virtual Bet365\n"
        "\n"
        "🏆 Liga: Euro League\n"
        "📈 Entrada recomendada: 🔥 Ambas Marcam 🔥\n"
        "\n"
        "1️⃣ roboextremetips.com.br ⏳ 10:05\n"
        "2️⃣ roboextremetips.com.br ⏳ 10:08\n"
        "3️⃣ roboextremetips.com.br ⏳ 10:11\n"
        "4️⃣ roboextremetips.com.br ⏳ 10:14\n"
        "\n"
        "✖ Red"
    )


@pytest.fixture
def signal_green_no_placar():
    """
    A GREEN signal where ✅ appears without score in parentheses.
    Tests graceful handling of GREEN without placar.
    Liga=Premier League, entrada=Over 1.5, horario=14:30.
    """
    return (
        "⚽ {VIP} ExtremeTips - Futebol Virtual Bet365\n"
        "\n"
        "🏆 Liga: Premier League\n"
        "📈 Entrada recomendada: 🔥 Over 1.5 🔥\n"
        "\n"
        "1️⃣ roboextremetips.com.br ⏳ 14:30\n"
        "2️⃣ roboextremetips.com.br ⏳ 14:33\n"
        "3️⃣ roboextremetips.com.br ⏳ 14:36 ✅\n"
        "4️⃣ roboextremetips.com.br ⏳ 14:39\n"
        "\n"
        "GREEN 💰💰💰😎😜😎\n"
        "✅✅✅✅✅✅✅✅✅"
    )


@pytest.fixture
def garbage_message():
    """A non-signal text that should return None from parse_message."""
    return "Bom dia a todos! Vamos às apostas de hoje! 🤑"
