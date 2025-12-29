"""Conftest для unit-тестов интеграций (без БД)."""
import pytest

# Переопределяем fixture engine, чтобы не использовать БД для unit-тестов
@pytest.fixture(scope="session", autouse=True)
def engine():
    """Пустой fixture engine для unit-тестов (не требует БД)."""
    return None

