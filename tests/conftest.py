"""
Shared pytest fixtures for HelperTips tests.

Provides sample Telegram signal message strings for parser testing.
"""

import pytest


@pytest.fixture
def signal_new():
    """A new signal without result."""
    return "⚽ LIGA: Euro League\n🎯 Entrada: Over 1.5 Gols\n⏰ Horario: 14:30"


@pytest.fixture
def signal_green_with_placar():
    """A signal with GREEN result and placar score."""
    return (
        "⚽ LIGA: Euro League\n"
        "🎯 Entrada: Over 1.5 Gols\n"
        "⏰ Horario: 14:30\n"
        "✅ GREEN\n"
        "Placar: 2-1"
    )


@pytest.fixture
def signal_red_with_placar():
    """A signal with RED result and placar score."""
    return (
        "⚽ LIGA: Premier League\n"
        "🎯 Entrada: Under 2.5 Gols\n"
        "⏰ Horario: 16:00\n"
        "❌ RED\n"
        "Placar: 0-1"
    )


@pytest.fixture
def signal_green_no_placar():
    """A signal with GREEN result but no placar score."""
    return (
        "⚽ LIGA: Champions League\n"
        "🎯 Entrada: Ambas Marcam\n"
        "⏰ Horario: 20:15\n"
        "✅ GREEN"
    )


@pytest.fixture
def garbage_message():
    """A non-signal text that should not be parsed."""
    return "Bom dia a todos! Vamos às apostas de hoje!"
