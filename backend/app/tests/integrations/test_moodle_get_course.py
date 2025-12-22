"""Тесты для Moodle интеграции get_course."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

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
            "moodle_url": "https://moodle.example.com",
            "token": "test_token_12345"
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
    """Тест метаданных Moodle интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "moodle_get_course"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Moodle Get Course"
    assert metadata.category == "education"
    assert metadata.credentials_provider == "moodle"
    assert metadata.credentials_strategy == "api_key"
    assert metadata.library_name == "httpx>=0.27.0"


@pytest.mark.asyncio
async def test_moodle_execute_success_by_id(integration, credentials_resolver, logger, bot_id):
    """Тест успешного получения курса по ID."""
    mock_course = {
        "id": 1,
        "fullname": "Test Course",
        "shortname": "TEST101",
        "idnumber": "COURSE-001",
        "categoryid": 1
    }
    
    with patch('app.integrations.moodle.get_course.httpx') as mock_httpx:
        mock_response = MagicMock()
        mock_response.json.return_value = [mock_course]
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={"field": "id", "value": "1"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == 1
        assert result["response"]["result"]["fullname"] == "Test Course"
        
        credentials_resolver.get_default_for.assert_called_once_with(
            bot_id=bot_id,
            provider="moodle",
            strategy="api_key"
        )
        mock_client.get.assert_called_once()
        logger.info.assert_called_once()


@pytest.mark.asyncio
async def test_moodle_execute_success_by_shortname(integration, credentials_resolver, logger, bot_id):
    """Тест успешного получения курса по shortname."""
    mock_course = {
        "id": 2,
        "fullname": "Mathematics 101",
        "shortname": "MATH101",
        "idnumber": "MATH-001"
    }
    
    with patch('app.integrations.moodle.get_course.httpx') as mock_httpx:
        mock_response = MagicMock()
        mock_response.json.return_value = [mock_course]
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={"field": "shortname", "value": "MATH101"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["shortname"] == "MATH101"
        
        call_args = mock_client.get.call_args
        assert call_args.kwargs["params"]["field"] == "shortname"
        assert call_args.kwargs["params"]["value"] == "MATH101"


@pytest.mark.asyncio
async def test_moodle_execute_success_by_idnumber(integration, credentials_resolver, logger, bot_id):
    """Тест успешного получения курса по idnumber."""
    mock_course = {
        "id": 3,
        "fullname": "Physics 202",
        "shortname": "PHYS202",
        "idnumber": "COURSE-2024-001"
    }
    
    with patch('app.integrations.moodle.get_course.httpx') as mock_httpx:
        mock_response = MagicMock()
        mock_response.json.return_value = [mock_course]
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={"field": "idnumber", "value": "COURSE-2024-001"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["idnumber"] == "COURSE-2024-001"


@pytest.mark.asyncio
async def test_moodle_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={"field": "id", "value": "1"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "Moodle credentials not found" in result["response"]["description"]
    logger.error.assert_called()


@pytest.mark.asyncio
async def test_moodle_execute_no_moodle_url(integration, logger, bot_id):
    """Тест выполнения без moodle_url в credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {"token": "test_token"}
    })
    
    result = await integration.execute(
        config={"field": "id", "value": "1"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "moodle_url not found" in result["response"]["description"]


@pytest.mark.asyncio
async def test_moodle_execute_no_token(integration, logger, bot_id):
    """Тест выполнения без token в credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {"moodle_url": "https://moodle.example.com"}
    })
    
    result = await integration.execute(
        config={"field": "id", "value": "1"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "token not found" in result["response"]["description"]


@pytest.mark.asyncio
async def test_moodle_execute_credentials_without_payload(integration, logger, bot_id):
    """Тест выполнения с credentials без ключа payload (обратная совместимость)."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "moodle_url": "https://moodle.example.com",
        "token": "test_token_12345"
    })
    
    mock_course = {"id": 1, "fullname": "Test Course"}
    
    with patch('app.integrations.moodle.get_course.httpx') as mock_httpx:
        mock_response = MagicMock()
        mock_response.json.return_value = [mock_course]
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={"field": "id", "value": "1"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True


@pytest.mark.asyncio
async def test_moodle_execute_missing_value(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующим value в config."""
    result = await integration.execute(
        config={"field": "id"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "value is required" in result["response"]["description"]
    logger.error.assert_called()


@pytest.mark.asyncio
async def test_moodle_execute_invalid_field(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с неверным field в config."""
    result = await integration.execute(
        config={"field": "invalid_field", "value": "123"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "Invalid field" in result["response"]["description"]
    logger.error.assert_called()


@pytest.mark.asyncio
async def test_moodle_execute_course_not_found(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения когда курс не найден (пустой список)."""
    with patch('app.integrations.moodle.get_course.httpx') as mock_httpx:
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={"field": "id", "value": "999"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 404
        assert "Course not found" in result["response"]["description"]
        logger.warning.assert_called()


@pytest.mark.asyncio
async def test_moodle_execute_moodle_api_exception(integration, credentials_resolver, logger, bot_id):
    """Тест обработки исключения от Moodle API."""
    with patch('app.integrations.moodle.get_course.httpx') as mock_httpx:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "exception": "dml_missing_record_exception",
            "errorcode": "invalidrecord",
            "message": "Course not found"
        }
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={"field": "id", "value": "999"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "Moodle API error" in result["response"]["description"]
        logger.error.assert_called()


@pytest.mark.asyncio
async def test_moodle_execute_http_status_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки HTTP ошибки."""
    with patch('app.integrations.moodle.get_course.httpx') as mock_httpx:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        # Создаем HTTPStatusError
        http_error = Exception()
        http_error.response = mock_response
        
        mock_client.get = AsyncMock(side_effect=http_error)
        mock_httpx.AsyncClient.return_value = mock_client
        mock_httpx.HTTPStatusError = type('HTTPStatusError', (Exception,), {})
        
        result = await integration.execute(
            config={"field": "id", "value": "1"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        logger.error.assert_called()


@pytest.mark.asyncio
async def test_moodle_execute_request_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибки запроса (сетевая ошибка)."""
    with patch('app.integrations.moodle.get_course.httpx') as mock_httpx:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        request_error = Exception("Connection timeout")
        mock_client.get = AsyncMock(side_effect=request_error)
        
        mock_httpx.AsyncClient.return_value = mock_client
        mock_httpx.RequestError = Exception
        
        result = await integration.execute(
            config={"field": "id", "value": "1"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        logger.error.assert_called()


@pytest.mark.asyncio
async def test_moodle_execute_unexpected_response_format(integration, credentials_resolver, logger, bot_id):
    """Тест обработки неожиданного формата ответа."""
    with patch('app.integrations.moodle.get_course.httpx') as mock_httpx:
        mock_response = MagicMock()
        mock_response.json.return_value = {"unexpected": "format"}
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={"field": "id", "value": "1"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "Unexpected response format" in result["response"]["description"]
        logger.error.assert_called()


@pytest.mark.asyncio
async def test_moodle_execute_url_normalization(integration, logger, bot_id):
    """Тест нормализации URL (убирание trailing slash)."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "moodle_url": "https://moodle.example.com/",
            "token": "test_token"
        }
    })
    
    mock_course = {"id": 1, "fullname": "Test Course"}
    
    with patch('app.integrations.moodle.get_course.httpx') as mock_httpx:
        mock_response = MagicMock()
        mock_response.json.return_value = [mock_course]
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={"field": "id", "value": "1"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "https://moodle.example.com/webservice/rest/server.php"


@pytest.mark.asyncio
async def test_moodle_execute_token_alternatives(integration, logger, bot_id):
    """Тест использования альтернативных ключей для token (api_key, wstoken)."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "moodle_url": "https://moodle.example.com",
            "api_key": "test_api_key"
        }
    })
    
    mock_course = {"id": 1, "fullname": "Test Course"}
    
    with patch('app.integrations.moodle.get_course.httpx') as mock_httpx:
        mock_response = MagicMock()
        mock_response.json.return_value = [mock_course]
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={"field": "id", "value": "1"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        call_args = mock_client.get.call_args
        assert call_args.kwargs["params"]["wstoken"] == "test_api_key"


@pytest.mark.asyncio
async def test_moodle_execute_url_alternative_key(integration, logger, bot_id):
    """Тест использования альтернативного ключа 'url' вместо 'moodle_url'."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "url": "https://moodle.example.com",  # Используем 'url' вместо 'moodle_url'
            "token": "test_token"
        }
    })
    
    mock_course = {"id": 1, "fullname": "Test Course"}
    
    with patch('app.integrations.moodle.get_course.httpx') as mock_httpx:
        mock_response = MagicMock()
        mock_response.json.return_value = [mock_course]
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={"field": "id", "value": "1"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True


@pytest.mark.asyncio
async def test_moodle_execute_wstoken_alternative(integration, logger, bot_id):
    """Тест использования ключа 'wstoken' вместо 'token'."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "moodle_url": "https://moodle.example.com",
            "wstoken": "test_wstoken"  # Используем 'wstoken' вместо 'token'
        }
    })
    
    mock_course = {"id": 1, "fullname": "Test Course"}
    
    with patch('app.integrations.moodle.get_course.httpx') as mock_httpx:
        mock_response = MagicMock()
        mock_response.json.return_value = [mock_course]
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={"field": "id", "value": "1"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        call_args = mock_client.get.call_args
        assert call_args.kwargs["params"]["wstoken"] == "test_wstoken"


@pytest.mark.asyncio
async def test_moodle_execute_default_field(integration, credentials_resolver, logger, bot_id):
    """Тест использования default field (id) когда field не указан."""
    mock_course = {
        "id": 1,
        "fullname": "Test Course",
        "shortname": "TEST101"
    }
    
    with patch('app.integrations.moodle.get_course.httpx') as mock_httpx:
        mock_response = MagicMock()
        mock_response.json.return_value = [mock_course]
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={"value": "1"},  # field не указан, должен использоваться default "id"
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        call_args = mock_client.get.call_args
        assert call_args.kwargs["params"]["field"] == "id"  # Проверяем, что использован default


@pytest.mark.asyncio
async def test_moodle_execute_multiple_courses_returns_first(integration, credentials_resolver, logger, bot_id):
    """Тест когда API возвращает несколько курсов - должен вернуться первый."""
    mock_courses = [
        {"id": 1, "fullname": "First Course", "shortname": "FIRST"},
        {"id": 2, "fullname": "Second Course", "shortname": "SECOND"}
    ]
    
    with patch('app.integrations.moodle.get_course.httpx') as mock_httpx:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_courses
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={"field": "id", "value": "1"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == 1
        assert result["response"]["result"]["fullname"] == "First Course"


@pytest.mark.asyncio
async def test_moodle_execute_api_params_correct(integration, credentials_resolver, logger, bot_id):
    """Тест правильности параметров API запроса."""
    mock_course = {"id": 1, "fullname": "Test Course"}
    
    with patch('app.integrations.moodle.get_course.httpx') as mock_httpx:
        mock_response = MagicMock()
        mock_response.json.return_value = [mock_course]
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        await integration.execute(
            config={"field": "shortname", "value": "MATH101"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        call_args = mock_client.get.call_args
        url = call_args[0][0]
        params = call_args.kwargs["params"]
        
        assert url == "https://moodle.example.com/webservice/rest/server.php"
        assert params["wstoken"] == "test_token_12345"
        assert params["wsfunction"] == "core_course_get_courses_by_field"
        assert params["moodlewsrestformat"] == "json"
        assert params["field"] == "shortname"
        assert params["value"] == "MATH101"


@pytest.mark.asyncio
async def test_moodle_execute_empty_config(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с пустым config."""
    result = await integration.execute(
        config={},  # Пустой config
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "value is required" in result["response"]["description"]


@pytest.mark.asyncio
async def test_moodle_execute_value_converted_to_string(integration, credentials_resolver, logger, bot_id):
    """Тест что value конвертируется в строку перед отправкой в API."""
    mock_course = {"id": 1, "fullname": "Test Course"}
    
    with patch('app.integrations.moodle.get_course.httpx') as mock_httpx:
        mock_response = MagicMock()
        mock_response.json.return_value = [mock_course]
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        await integration.execute(
            config={"field": "id", "value": 123},  # Число вместо строки
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        call_args = mock_client.get.call_args
        params = call_args.kwargs["params"]
        assert isinstance(params["value"], str)
        assert params["value"] == "123"


