"""Конфигурация pytest для тестов интеграций."""
# Переопределяем conftest из родительской директории, чтобы не требовать базу данных
# Тесты интеграций не требуют базы данных, только моки
import pytest
import sys
import os

# Добавляем путь к проекту в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


# Переопределяем фикстуру engine, чтобы не требовать базу данных для тестов интеграций
@pytest.fixture(scope="session", autouse=True)
def engine():
    """Пустая фикстура engine для тестов интеграций."""
    yield None


# Добавляем фикстуру для settings, которую ожидает родительский conftest.py
@pytest.fixture(scope="session")
def settings():
    """Мок фикстуры settings."""
    from unittest.mock import Mock
    mock_settings = Mock()
    # Добавьте здесь необходимые атрибуты, если они нужны для тестов
    return mock_settings


# Фикстура для event_loop (нужна для асинхронных тестов)
@pytest.fixture(scope="session")
def event_loop():
    """Создаёт event loop для асинхронных тестов."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Добавляем фикстуру для anyio_backend
@pytest.fixture(scope="session")
def anyio_backend():
    """Определяет бэкенд для anyio."""
    return "asyncio"