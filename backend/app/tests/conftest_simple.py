"""Simplified conftest for integration unit tests (no DB required)."""
import pytest


@pytest.fixture
def bot_id():
    """Return a test bot ID."""
    from uuid import UUID
    return UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def logger():
    """Return a mock logger."""
    from unittest.mock import MagicMock
    from app.loggers.bot import BotLogger
    return MagicMock(spec=BotLogger)
