"""
Tests for validate_config() in db.py.

Behaviors tested:
- test_missing_var_raises: Any missing required var causes SystemExit
- test_all_vars_present_passes: All vars set → no exception
- test_empty_var_raises: Empty string value triggers SystemExit
"""
import pytest
import os

# All required environment variable names
REQUIRED_VARS = [
    'TELEGRAM_API_ID',
    'TELEGRAM_API_HASH',
    'TELEGRAM_GROUP_ID',
    'DB_HOST',
    'DB_PORT',
    'DB_NAME',
    'DB_USER',
    'DB_PASSWORD',
]

SAMPLE_VALUES = {
    'TELEGRAM_API_ID': '12345678',
    'TELEGRAM_API_HASH': 'abc123def456',
    'TELEGRAM_GROUP_ID': '-1001234567890',
    'DB_HOST': 'localhost',
    'DB_PORT': '5432',
    'DB_NAME': 'helpertips',
    'DB_USER': 'helpertips_user',
    'DB_PASSWORD': 'secret',
}


def set_all_vars(monkeypatch):
    """Helper: set all required vars to sample values."""
    for k, v in SAMPLE_VALUES.items():
        monkeypatch.setenv(k, v)


def test_all_vars_present_passes(monkeypatch):
    """When all required vars are set, validate_config() returns without error."""
    set_all_vars(monkeypatch)
    from db import validate_config
    validate_config()  # must not raise


def test_missing_var_raises(monkeypatch):
    """When any required var is missing, validate_config() raises SystemExit."""
    set_all_vars(monkeypatch)
    for var in REQUIRED_VARS:
        monkeypatch.delenv(var, raising=False)
        with pytest.raises(SystemExit):
            from db import validate_config
            validate_config()
        # Restore for next iteration
        monkeypatch.setenv(var, SAMPLE_VALUES[var])


def test_empty_var_raises(monkeypatch):
    """When a required var is set to empty string, validate_config() raises SystemExit."""
    set_all_vars(monkeypatch)
    for var in REQUIRED_VARS:
        monkeypatch.setenv(var, '')
        with pytest.raises(SystemExit):
            from db import validate_config
            validate_config()
        # Restore for next iteration
        monkeypatch.setenv(var, SAMPLE_VALUES[var])
