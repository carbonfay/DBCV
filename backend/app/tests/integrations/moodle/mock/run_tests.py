"""Скрипт для запуска мок-тестов Moodle интеграции."""
import sys
import asyncio
from pathlib import Path

# Добавляем путь к backend
backend_path = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

import pytest

if __name__ == "__main__":
    # Запускаем тесты с игнорированием conftest из родительских директорий
    exit_code = pytest.main([
        str(Path(__file__).parent / "test_get_course.py"),
        "-v",
        "--tb=short",
        "-p", "no:cacheprovider"
    ])
    sys.exit(exit_code)

