"""Тесты для Moodle Get Course интеграции."""
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
            "token": "test_token_12345"
        }
    })
    return resolver


@pytest.fixture
def credentials_resolver_without_payload():
    """Создает mock credentials resolver без payload (для обратной совместимости)."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "url": "https://moodle.example.com",
        "wstoken": "test_token_12345"
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


@pytest.fixture
def mock_course_data():
    """Возвращает тестовые данные курса."""
    return {
        "id": 1,
        "shortname": "MATH101",
        "fullname": "Mathematics 101",
        "displayname": "Mathematics 101",
        "summary": "Introduction to Mathematics",
        "summaryformat": 1,
        "categoryid": 2,
        "categoryname": "Mathematics",
        "format": "topics",
        "startdate": 1609459200,
        "enddate": 1640995200,
        "visible": 1,
        "idnumber": "MATH101",
        "timecreated": 1609459200,
        "timemodified": 1609459200
    }


def test_moodle_metadata(integration):
    """Тест метаданных Moodle интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "moodle_get_course"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Moodle Get Course"
    assert metadata.category == "education"
    assert metadata.credentials_provider == "moodle"
    assert metadata.credentials_strategy == "api_key"
    assert metadata.library_name == "httpx"
    assert metadata.icon_s3_key == "icons/integrations/moodle.svg"
    assert metadata.color == "#f98012"
    assert len(metadata.examples) == 2


@pytest.mark.asyncio
async def test_moodle_execute_success(
    integration, credentials_resolver, logger, bot_id, mock_course_data
):
    """Тест успешного выполнения Moodle интеграции."""
    # Мокаем httpx.AsyncClient
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [mock_course_data]
    mock_response.raise_for_status = MagicMock()
    mock_response.text = ""
    
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch('app.integrations.moodle.get_course.httpx.AsyncClient', return_value=mock_client):
        result = await integration.execute(
            config={
                "course_id": 1,
                "field": "id"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
    
    # Проверяем результат
    assert result["response"]["ok"] is True
    assert result["response"]["result"]["id"] == 1
    assert result["response"]["result"]["shortname"] == "MATH101"
    assert result["response"]["result"]["fullname"] == "Mathematics 101"
    
    # Проверяем, что запрос был сделан с правильными параметрами
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert "https://moodle.example.com/webservice/rest/server.php" in str(call_args[0][0])
    assert call_args[1]["params"]["wstoken"] == "test_token_12345"
    assert call_args[1]["params"]["wsfunction"] == "core_course_get_courses_by_field"
    assert call_args[1]["params"]["field"] == "id"
    assert call_args[1]["params"]["value"] == "1"


@pytest.mark.asyncio
async def test_moodle_execute_success_without_payload(
    integration, credentials_resolver_without_payload, logger, bot_id, mock_course_data
):
    """Тест успешного выполнения с credentials без payload (обратная совместимость)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [mock_course_data]
    mock_response.raise_for_status = MagicMock()
    mock_response.text = ""
    
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch('app.integrations.moodle.get_course.httpx.AsyncClient', return_value=mock_client):
        result = await integration.execute(
            config={
                "course_id": 1
            },
            credentials_resolver=credentials_resolver_without_payload,
            bot_id=bot_id,
            logger=logger
        )
    
    assert result["response"]["ok"] is True
    assert result["response"]["result"]["id"] == 1


@pytest.mark.asyncio
async def test_moodle_execute_by_shortname(
    integration, credentials_resolver, logger, bot_id, mock_course_data
):
    """Тест поиска курса по shortname."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [mock_course_data]
    mock_response.raise_for_status = MagicMock()
    mock_response.text = ""
    
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch('app.integrations.moodle.get_course.httpx.AsyncClient', return_value=mock_client):
        result = await integration.execute(
            config={
                "course_id": "MATH101",
                "field": "shortname"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
    
    assert result["response"]["ok"] is True
    # Проверяем, что запрос был с правильным полем
    call_args = mock_client.get.call_args
    assert call_args[1]["params"]["field"] == "shortname"
    assert call_args[1]["params"]["value"] == "MATH101"


@pytest.mark.asyncio
async def test_moodle_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={"course_id": 1},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "credentials not found" in result["response"]["description"].lower()
    logger.error.assert_called()


@pytest.mark.asyncio
async def test_moodle_execute_no_url(integration, logger, bot_id):
    """Тест выполнения без URL в credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "token": "test_token"
        }
    })
    
    result = await integration.execute(
        config={"course_id": 1},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "url not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_moodle_execute_no_token(integration, logger, bot_id):
    """Тест выполнения без token в credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "url": "https://moodle.example.com"
        }
    })
    
    result = await integration.execute(
        config={"course_id": 1},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "token not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_moodle_execute_missing_course_id(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующим course_id."""
    result = await integration.execute(
        config={},  # Отсутствует course_id
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "course_id is required" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_moodle_execute_course_not_found(
    integration, credentials_resolver, logger, bot_id
):
    """Тест когда курс не найден (пустой список)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []  # Пустой список
    mock_response.raise_for_status = MagicMock()
    mock_response.text = ""
    
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch('app.integrations.moodle.get_course.httpx.AsyncClient', return_value=mock_client):
        result = await integration.execute(
            config={
                "course_id": 999,
                "field": "id"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 404
    assert "course not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_moodle_execute_api_exception(
    integration, credentials_resolver, logger, bot_id
):
    """Тест когда Moodle API возвращает исключение."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "exception": "invalid_parameter_exception",
        "errorcode": "invalidparameter",
        "message": "Invalid course id"
    }
    mock_response.raise_for_status = MagicMock()
    mock_response.text = ""
    
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch('app.integrations.moodle.get_course.httpx.AsyncClient', return_value=mock_client):
        result = await integration.execute(
            config={
                "course_id": 1
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "Moodle API error" in result["response"]["description"]
    assert result["response"]["errorcode"] == "invalidparameter"


@pytest.mark.asyncio
async def test_moodle_execute_http_error(
    integration, credentials_resolver, logger, bot_id
):
    """Тест HTTP ошибки."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    
    mock_client = MagicMock()
    http_error = httpx.HTTPStatusError(
        "Server Error",
        request=MagicMock(),
        response=mock_response
    )
    mock_client.get = AsyncMock(side_effect=http_error)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch('app.integrations.moodle.get_course.httpx.AsyncClient', return_value=mock_client):
        result = await integration.execute(
            config={
                "course_id": 1
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500
    assert "HTTP error" in result["response"]["description"]


@pytest.mark.asyncio
async def test_moodle_execute_request_error(
    integration, credentials_resolver, logger, bot_id
):
    """Тест ошибки запроса (например, сеть недоступна)."""
    mock_client = MagicMock()
    request_error = httpx.RequestError("Connection failed", request=MagicMock())
    mock_client.get = AsyncMock(side_effect=request_error)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch('app.integrations.moodle.get_course.httpx.AsyncClient', return_value=mock_client):
        result = await integration.execute(
            config={
                "course_id": 1
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500
    assert "Request error" in result["response"]["description"]


@pytest.mark.asyncio
async def test_moodle_execute_url_with_trailing_slash(
    integration, logger, bot_id, mock_course_data
):
    """Тест что URL с завершающим слешем обрабатывается правильно."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "url": "https://moodle.example.com/",  # С завершающим слешем
            "token": "test_token_12345"
        }
    })
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [mock_course_data]
    mock_response.raise_for_status = MagicMock()
    mock_response.text = ""
    
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch('app.integrations.moodle.get_course.httpx.AsyncClient', return_value=mock_client):
        result = await integration.execute(
            config={
                "course_id": 1
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
    
    assert result["response"]["ok"] is True
    # Проверяем, что URL был правильно обработан (без двойного слеша)
    call_args = mock_client.get.call_args
    assert "https://moodle.example.com/webservice/rest/server.php" in str(call_args[0][0])
    assert "//webservice" not in str(call_args[0][0])


@pytest.mark.asyncio
async def test_moodle_execute_course_id_as_string(
    integration, credentials_resolver, logger, bot_id, mock_course_data
):
    """Тест что course_id может быть строкой."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [mock_course_data]
    mock_response.raise_for_status = MagicMock()
    mock_response.text = ""
    
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch('app.integrations.moodle.get_course.httpx.AsyncClient', return_value=mock_client):
        result = await integration.execute(
            config={
                "course_id": "1"  # Строка вместо числа
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
    
    assert result["response"]["ok"] is True
    # Проверяем, что значение было преобразовано в строку
    call_args = mock_client.get.call_args
    assert call_args[1]["params"]["value"] == "1"

