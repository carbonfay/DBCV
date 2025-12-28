#!/usr/bin/env python3
"""Простой запуск мок-тестов для Moodle Get Courses интеграции."""
import sys
import asyncio
from pathlib import Path
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from app.integrations.moodle.get_courses import MoodleGetCoursesIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger
import httpx


def create_integration():
    """Создает экземпляр интеграции."""
    return MoodleGetCoursesIntegration()


def create_credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "url": "https://moodle.example.com",
            "api_key": "test-moodle-token-12345"
        }
    })
    return resolver


def create_logger():
    """Создает mock logger."""
    return MagicMock(spec=BotLogger)


def create_bot_id():
    """Создает test bot ID."""
    return UUID("12345678-1234-5678-1234-567812345678")


async def test_metadata():
    """Тест метаданных."""
    print("1. Testing metadata...")
    integration = create_integration()
    metadata = integration.metadata
    
    assert metadata.id == "moodle_get_courses"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Moodle Get Courses"
    assert metadata.category == "education"
    assert metadata.credentials_provider == "other"
    assert metadata.credentials_strategy == "api_key"
    print("   PASSED")


async def test_execute_success():
    """Тест успешного выполнения."""
    print("2. Testing successful execution...")
    integration = create_integration()
    credentials_resolver = create_credentials_resolver()
    logger = create_logger()
    bot_id = create_bot_id()
    
    mock_courses = [
        {"id": 1, "fullname": "Course 1", "shortname": "C1"},
        {"id": 2, "fullname": "Course 2", "shortname": "C2"}
    ]
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_courses
    mock_response.raise_for_status = MagicMock()
    
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch('app.integrations.moodle.get_courses.httpx.AsyncClient', return_value=mock_client):
        result = await integration.execute(
            config={},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["count"] == 2
        assert len(result["response"]["result"]["courses"]) == 2
    print("   PASSED")


async def test_execute_no_credentials():
    """Тест без credentials."""
    print("3. Testing no credentials...")
    integration = create_integration()
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    logger = create_logger()
    bot_id = create_bot_id()
    
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    print("   PASSED")


async def test_execute_missing_url():
    """Тест с отсутствующим URL."""
    print("4. Testing missing URL...")
    integration = create_integration()
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {"api_key": "test-token"}
    })
    logger = create_logger()
    bot_id = create_bot_id()
    
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    print("   PASSED")


async def test_execute_moodle_api_error():
    """Тест ошибки Moodle API."""
    print("5. Testing Moodle API error...")
    integration = create_integration()
    credentials_resolver = create_credentials_resolver()
    logger = create_logger()
    bot_id = create_bot_id()
    
    mock_error_response = {
        "exception": "invalid_parameter_exception",
        "errorcode": "invalidparameter",
        "message": "Invalid token"
    }
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_error_response
    mock_response.raise_for_status = MagicMock()
    
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch('app.integrations.moodle.get_courses.httpx.AsyncClient', return_value=mock_client):
        result = await integration.execute(
            config={},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == "invalidparameter"
    print("   PASSED")


async def run_all_tests():
    """Запускает все тесты."""
    print("Running mock tests for Moodle Get Courses integration...\n")
    
    passed = 0
    failed = 0
    
    tests = [
        ("Metadata", test_metadata),
        ("Successful execution", test_execute_success),
        ("No credentials", test_execute_no_credentials),
        ("Missing URL", test_execute_missing_url),
        ("Moodle API error", test_execute_moodle_api_error),
    ]
    
    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"   FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\nResults:")
    print(f"   PASSED: {passed}")
    print(f"   FAILED: {failed}")
    print(f"   TOTAL: {passed + failed}")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

