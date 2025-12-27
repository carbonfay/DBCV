"""Мок-тесты для Moodle Get Course интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.integrations.moodle.get_course import MoodleGetCourseIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр Moodle интеграции."""
    return MoodleGetCourseIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver с валидными credentials."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "url": "https://moodle.example.com",
            "token": "test-wstoken-12345"
        }
    })
    return resolver


@pytest.fixture
def credentials_resolver_no_payload():
    """Создает mock credentials resolver без payload (обратная совместимость)."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "url": "https://moodle.example.com",
        "wstoken": "test-wstoken-12345"
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
    """Тест метаданных Moodle интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "moodle_get_course"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Moodle Get Course"
    assert metadata.category == "education"
    assert metadata.credentials_provider == "other"
    assert metadata.credentials_strategy == "api_key"
    assert metadata.library_name == "httpx"
    assert len(metadata.examples) == 3


@pytest.mark.asyncio
async def test_moodle_execute_success_by_id(integration, credentials_resolver, logger, bot_id):
    """Тест успешного получения курса по ID."""
    mock_course_data = {
        "courses": [
            {
                "id": 5,
                "shortname": "MATH101",
                "fullname": "Mathematics 101",
                "idnumber": "COURSE-2024-001",
                "summary": "Introduction to Mathematics",
                "categoryid": 1
            }
        ]
    }
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_course_data
        mock_response.raise_for_status = MagicMock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "field": "id",
                "value": "5"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert "courses" in result["response"]["result"]
        assert result["response"]["result"]["courses"][0]["id"] == 5
        assert result["response"]["result"]["courses"][0]["shortname"] == "MATH101"
        
        # Проверяем, что HTTP запрос был выполнен
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "webservice/rest/server.php" in call_args[0][0]
        assert call_args[1]["params"]["wsfunction"] == "core_course_get_courses_by_field"
        assert call_args[1]["params"]["field"] == "id"
        assert call_args[1]["params"]["value"] == "5"
        assert call_args[1]["params"]["wstoken"] == "test-wstoken-12345"


@pytest.mark.asyncio
async def test_moodle_execute_success_by_shortname(integration, credentials_resolver, logger, bot_id):
    """Тест успешного получения курса по короткому имени."""
    mock_course_data = {
        "courses": [
            {
                "id": 5,
                "shortname": "MATH101",
                "fullname": "Mathematics 101"
            }
        ]
    }
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_course_data
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        result = await integration.execute(
            config={
                "field": "shortname",
                "value": "MATH101"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["field"] == "shortname"
        assert call_args[1]["params"]["value"] == "MATH101"


@pytest.mark.asyncio
async def test_moodle_execute_success_no_payload(integration, credentials_resolver_no_payload, logger, bot_id):
    """Тест успешного выполнения с credentials без payload (обратная совместимость)."""
    mock_course_data = {"courses": [{"id": 5, "shortname": "MATH101"}]}
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_course_data
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        result = await integration.execute(
            config={"field": "id", "value": "5"},
            credentials_resolver=credentials_resolver_no_payload,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True


@pytest.mark.asyncio
async def test_moodle_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={"field": "id", "value": "5"},
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
            "token": "test-token"
            # URL отсутствует
        }
    })
    
    result = await integration.execute(
        config={"field": "id", "value": "5"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "url not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_moodle_execute_missing_token(integration, logger, bot_id):
    """Тест выполнения с отсутствующим токеном в credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "url": "https://moodle.example.com"
            # token отсутствует
        }
    })
    
    result = await integration.execute(
        config={"field": "id", "value": "5"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "token" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_moodle_execute_missing_value(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующим значением value."""
    result = await integration.execute(
        config={
            "field": "id"
            # value отсутствует
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "required" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_moodle_execute_invalid_field(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с невалидным полем field."""
    result = await integration.execute(
        config={
            "field": "invalid_field",
            "value": "5"
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "invalid field" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_moodle_execute_moodle_api_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибки от Moodle API."""
    mock_error_response = {
        "exception": "moodle_exception",
        "errorcode": "invalidtoken",
        "message": "Invalid token"
    }
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_error_response
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        result = await integration.execute(
            config={"field": "id", "value": "5"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "moodle api error" in result["response"]["description"].lower()
        assert "invalidtoken" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_moodle_execute_http_status_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки HTTP статус ошибки."""
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        http_error = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=mock_response
        )
        mock_client.get = AsyncMock(side_effect=http_error)
        mock_client_class.return_value = mock_client
        
        result = await integration.execute(
            config={"field": "id", "value": "5"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 404
        assert "http error" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_moodle_execute_request_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибки запроса (сетевая ошибка)."""
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        request_error = httpx.RequestError("Connection failed", request=MagicMock())
        mock_client.get = AsyncMock(side_effect=request_error)
        mock_client_class.return_value = mock_client
        
        result = await integration.execute(
            config={"field": "id", "value": "5"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "request error" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_moodle_execute_unexpected_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки неожиданной ошибки."""
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        unexpected_error = ValueError("Unexpected error")
        mock_client.get = AsyncMock(side_effect=unexpected_error)
        mock_client_class.return_value = mock_client
        
        result = await integration.execute(
            config={"field": "id", "value": "5"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "unexpected error" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_moodle_execute_url_with_trailing_slash(integration, credentials_resolver, logger, bot_id):
    """Тест обработки URL с trailing slash."""
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "url": "https://moodle.example.com/",  # С trailing slash
            "token": "test-wstoken-12345"
        }
    })
    
    mock_course_data = {"courses": [{"id": 5}]}
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_course_data
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        result = await integration.execute(
            config={"field": "id", "value": "5"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        # Проверяем, что trailing slash был удален
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "https://moodle.example.com/webservice/rest/server.php"


@pytest.mark.asyncio
async def test_moodle_execute_alternative_credential_keys(integration, logger, bot_id):
    """Тест с альтернативными ключами в credentials (moodle_url, server_url, wstoken, api_key)."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "moodle_url": "https://moodle.example.com",
            "wstoken": "test-wstoken-12345"
        }
    })
    
    mock_course_data = {"courses": [{"id": 5}]}
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_course_data
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        result = await integration.execute(
            config={"field": "id", "value": "5"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["wstoken"] == "test-wstoken-12345"

