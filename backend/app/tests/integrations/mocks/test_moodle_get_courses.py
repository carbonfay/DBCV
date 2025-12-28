"""Мок-тесты для Moodle Get Courses интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.integrations.moodle.get_courses import MoodleGetCoursesIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр Moodle Get Courses интеграции."""
    return MoodleGetCoursesIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver с валидными credentials."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "url": "https://moodle.example.com",
            "api_key": "test-moodle-token-12345"
        }
    })
    return resolver


@pytest.fixture
def logger():
    """Создает mock logger."""
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    """Создает test bot ID."""
    return UUID("12345678-1234-5678-1234-567812345678")


def test_moodle_metadata(integration):
    """Тест метаданных Moodle Get Courses интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "moodle_get_courses"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Moodle Get Courses"
    assert metadata.description == "Получить список курсов из Moodle через REST API"
    assert metadata.category == "education"
    assert metadata.credentials_provider == "other"
    assert metadata.credentials_strategy == "api_key"
    assert metadata.library_name == "httpx>=0.27.0"
    assert metadata.icon_s3_key == "icons/integrations/moodle.svg"
    assert metadata.color == "#f98012"


@pytest.mark.asyncio
async def test_moodle_execute_success(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения Moodle Get Courses интеграции."""
    # Мок данные курсов от Moodle API
    mock_courses = [
        {
            "id": 1,
            "fullname": "Course 1",
            "shortname": "C1",
            "summary": "Description of course 1"
        },
        {
            "id": 2,
            "fullname": "Course 2",
            "shortname": "C2",
            "summary": "Description of course 2"
        }
    ]
    
    # Мокаем httpx.AsyncClient
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_courses
    mock_response.raise_for_status = MagicMock()
    
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch('app.integrations.moodle.get_courses.httpx.AsyncClient', return_value=mock_client):
        # Выполняем интеграцию
        result = await integration.execute(
            config={},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["count"] == 2
        assert len(result["response"]["result"]["courses"]) == 2
        assert result["response"]["result"]["courses"][0]["id"] == 1
        assert result["response"]["result"]["courses"][0]["fullname"] == "Course 1"
        
        # Проверяем, что был сделан правильный запрос
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "webservice/rest/server.php" in call_args[0][0]
        assert call_args[1]["params"]["wsfunction"] == "core_course_get_courses"
        assert call_args[1]["params"]["wstoken"] == "test-moodle-token-12345"
        assert call_args[1]["params"]["moodlewsrestformat"] == "json"


@pytest.mark.asyncio
async def test_moodle_execute_success_with_trailing_slash(integration, logger, bot_id):
    """Тест успешного выполнения с URL, заканчивающимся на слэш."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "url": "https://moodle.example.com/",
            "api_key": "test-token"
        }
    })
    
    mock_courses = [{"id": 1, "fullname": "Course 1"}]
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
        # Проверяем, что слэш был удален
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "https://moodle.example.com/webservice/rest/server.php"


@pytest.mark.asyncio
async def test_moodle_execute_success_with_alternative_credential_keys(integration, logger, bot_id):
    """Тест успешного выполнения с альтернативными ключами credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "moodle_url": "https://moodle.example.com",
            "wstoken": "alternative-token"
        }
    })
    
    mock_courses = [{"id": 1, "fullname": "Course 1"}]
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
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["wstoken"] == "alternative-token"


@pytest.mark.asyncio
async def test_moodle_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "credentials not found" in result["response"]["description"].lower()
    logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_moodle_execute_missing_url(integration, logger, bot_id):
    """Тест выполнения с отсутствующим URL в credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "api_key": "test-token"
            # Отсутствует url
        }
    })
    
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "moodle_url" in result["response"]["description"].lower() or "url" in result["response"]["description"].lower()
    logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_moodle_execute_missing_api_key(integration, logger, bot_id):
    """Тест выполнения с отсутствующим api_key в credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "url": "https://moodle.example.com"
            # Отсутствует api_key
        }
    })
    
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "api_key" in result["response"]["description"].lower()
    logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_moodle_execute_moodle_api_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибки Moodle API."""
    # Moodle API возвращает ошибку в формате JSON
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
        assert "Invalid token" in result["response"]["description"]
        logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_moodle_execute_http_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки HTTP ошибки."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    
    http_error = httpx.HTTPStatusError(
        message="404 Not Found",
        request=MagicMock(),
        response=mock_response
    )
    
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=http_error)
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
        assert result["response"]["error_code"] == 404
        assert "404" in result["response"]["description"]
        logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_moodle_execute_request_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибки соединения."""
    request_error = httpx.RequestError("Connection failed", request=MagicMock())
    
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=request_error)
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
        assert result["response"]["error_code"] == 500
        assert "Failed to connect" in result["response"]["description"]
        logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_moodle_execute_unexpected_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки неожиданной ошибки."""
    unexpected_error = ValueError("Unexpected error")
    
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=unexpected_error)
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
        assert result["response"]["error_code"] == 500
        assert "Unexpected error" in result["response"]["description"]
        logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_moodle_execute_with_credentials_in_root(integration, logger, bot_id):
    """Тест выполнения с credentials в корне (без payload)."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "url": "https://moodle.example.com",
        "api_key": "root-token"
        # credentials в корне, без payload
    })
    
    mock_courses = [{"id": 1, "fullname": "Course 1"}]
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
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["wstoken"] == "root-token"


@pytest.mark.asyncio
async def test_moodle_execute_courses_dict_format(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ответа, когда курсы в формате словаря с ключом 'courses'."""
    mock_response_data = {
        "courses": [
            {"id": 1, "fullname": "Course 1"},
            {"id": 2, "fullname": "Course 2"}
        ]
    }
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
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

