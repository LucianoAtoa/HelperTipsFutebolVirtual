"""Testes para configure_logging() — logging condicional TTY vs daemon."""
import logging
import os
from logging.handlers import RotatingFileHandler
from unittest.mock import patch

import pytest


def get_configure_logging():
    """Import configure_logging fresh to avoid module-level side effects."""
    import importlib
    import helpertips.listener as listener_mod
    importlib.reload(listener_mod)
    return listener_mod.configure_logging


@pytest.fixture(autouse=True)
def clean_root_logger():
    """Limpa handlers do root logger antes e depois de cada teste."""
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    yield
    root.handlers.clear()
    root.handlers.extend(original_handlers)


def test_daemon_mode_uses_rotating_file_handler(tmp_path):
    """Sem TTY, deve usar RotatingFileHandler apontando para o log file."""
    log_file = tmp_path / "listener.log"
    root = logging.getLogger()
    root.handlers.clear()

    with patch("sys.stdout") as mock_stdout, \
         patch("helpertips.listener.LOG_PATH", str(log_file)):
        mock_stdout.isatty.return_value = False
        from helpertips.listener import configure_logging
        configure_logging()

    handlers = logging.getLogger().handlers
    handler_types = [type(h).__name__ for h in handlers]
    assert "RotatingFileHandler" in handler_types, (
        f"Esperado RotatingFileHandler, encontrado: {handler_types}"
    )


def test_tty_mode_uses_rich_handler():
    """Com TTY, deve usar RichHandler."""
    root = logging.getLogger()
    root.handlers.clear()

    with patch("sys.stdout") as mock_stdout:
        mock_stdout.isatty.return_value = True
        from helpertips.listener import configure_logging
        configure_logging()

    handlers = logging.getLogger().handlers
    handler_types = [type(h).__name__ for h in handlers]
    assert "RichHandler" in handler_types, (
        f"Esperado RichHandler, encontrado: {handler_types}"
    )


def test_rotating_file_handler_config(tmp_path):
    """RotatingFileHandler deve ter maxBytes=10MB e backupCount=7."""
    log_file = tmp_path / "listener.log"
    root = logging.getLogger()
    root.handlers.clear()

    with patch("sys.stdout") as mock_stdout, \
         patch("helpertips.listener.LOG_PATH", str(log_file)):
        mock_stdout.isatty.return_value = False
        from helpertips.listener import configure_logging
        configure_logging()

    handlers = logging.getLogger().handlers
    rfh = next((h for h in handlers if isinstance(h, RotatingFileHandler)), None)
    assert rfh is not None, "RotatingFileHandler nao encontrado"
    assert rfh.maxBytes == 10 * 1024 * 1024, f"maxBytes esperado 10485760, encontrado {rfh.maxBytes}"
    assert rfh.backupCount == 7, f"backupCount esperado 7, encontrado {rfh.backupCount}"


def test_rotating_file_handler_format(tmp_path):
    """RotatingFileHandler deve ter formato com asctime, levelname, name e message."""
    log_file = tmp_path / "listener.log"
    root = logging.getLogger()
    root.handlers.clear()

    with patch("sys.stdout") as mock_stdout, \
         patch("helpertips.listener.LOG_PATH", str(log_file)):
        mock_stdout.isatty.return_value = False
        from helpertips.listener import configure_logging
        configure_logging()

    handlers = logging.getLogger().handlers
    rfh = next((h for h in handlers if isinstance(h, RotatingFileHandler)), None)
    assert rfh is not None, "RotatingFileHandler nao encontrado"
    fmt = rfh.formatter._fmt
    assert "%(asctime)s" in fmt, f"asctime nao encontrado no formato: {fmt}"
    assert "%(levelname)s" in fmt, f"levelname nao encontrado no formato: {fmt}"
    assert "%(name)s" in fmt, f"name nao encontrado no formato: {fmt}"
    assert "%(message)s" in fmt, f"message nao encontrado no formato: {fmt}"
