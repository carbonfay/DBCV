"""Мок-тесты для Moodle Create Course интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.integrations.moodle.create_course import MoodleCreateCourseIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр Moodle Create Course интеграции."""
    return MoodleCreateCourseIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver с валидными credentials."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "api_key": "test_moodle_token_12345",
            "moodle_url": "https://moodle.example.com"
        }
    })
    return resolver


@pytest.fixture
def credentials_resolver_with_alternative_keys():
    """Создает mock credentials resolver с альтернативными ключами."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "wstoken": "test_moodle_token_67890",
            "url": "https://moodle2.example.com"
        }
    })
    return resolver


@pytest.fixture
def credentials_resolver_no_payload():
    """Создает mock credentials resolver без payload (обратная совместимость)."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "token": "test_moodle_token_direct",
        "base_url": "https://moodle3.example.com"
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
def moodle_success_response():
    """Создает успешный ответ от Moodle API."""
    return {
        "id": 42,
        "shortname": "test_course"
    }


@pytest.fixture
def moodle_error_response():
    """Создает ответ с ошибкой от Moodle API."""
    return {
        "exception": "moodle_exception",
        "errorcode": "invalidtoken",
        "message": "Invalid token"
    }


def test_moodle_metadata(integration):
    """Тест метаданных Moodle интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "moodle_create_course"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Moodle Create Course"
    assert metadata.category == "education"
    assert metadata.credentials_provider == "other"
    assert metadata.credentials_strategy == "api_key"
    assert metadata.library_name == "httpx"
    assert len(metadata.examples) == 2


@pytest.mark.asyncio
async def test_moodle_execute_success(
    integration, credentials_resolver, logger, bot_id, moodle_success_response
):
    """Тест успешного создания курса в Moodle."""
    # Создаем mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = moodle_success_response
    mock_response.raise_for_status = MagicMock()
    
    # Создаем mock HTTP client
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(return_value=mock_response)
    
    with patch('app.integrations.moodle.create_course.httpx.AsyncClient', return_value=mock_client):
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "fullname": "Test Course",
                "shortname": "test_course",
                "categoryid": 1,
                "summary": "Test course description",
                "format": "topics",
                "visible": 1
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["course_id"] == 42
        assert result["response"]["result"]["fullname"] == "Test Course"
        assert result["response"]["result"]["shortname"] == "test_course"
        assert result["response"]["result"]["categoryid"] == 1
        
        # Проверяем, что HTTP запрос был выполнен
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        
        # Проверяем URL
        assert "webservice/rest/server.php" in call_args[0][0]
        
        # Проверяем параметры запроса
        data = call_args[1]["data"]
        assert data["wstoken"] == "test_moodle_token_12345"
        assert data["wsfunction"] == "core_course_create_courses"
        assert data["moodlewsrestformat"] == "json"
        assert data["courses[0][fullname]"] == "Test Course"
        assert data["courses[0][shortname]"] == "test_course"
        # httpx может преобразовать int в str при отправке, проверяем оба варианта
        assert data["courses[0][categoryid]"] in (1, "1")


@pytest.mark.asyncio
async def test_moodle_execute_success_with_alternative_keys(
    integration, credentials_resolver_with_alternative_keys, logger, bot_id, moodle_success_response
):
    """Тест успешного создания курса с альтернативными ключами credentials."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = moodle_success_response
    mock_response.raise_for_status = MagicMock()
    
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(return_value=mock_response)
    
    with patch('app.integrations.moodle.create_course.httpx.AsyncClient', return_value=mock_client):
        result = await integration.execute(
            config={
                "fullname": "Test Course 2",
                "shortname": "test_course_2",
                "categoryid": 2
            },
            credentials_resolver=credentials_resolver_with_alternative_keys,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        call_args = mock_client.post.call_args
        assert call_args[1]["data"]["wstoken"] == "test_moodle_token_67890"


@pytest.mark.asyncio
async def test_moodle_execute_success_no_payload(
    integration, credentials_resolver_no_payload, logger, bot_id, moodle_success_response
):
    """Тест успешного создания курса без payload (обратная совместимость)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = moodle_success_response
    mock_response.raise_for_status = MagicMock()
    
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(return_value=mock_response)
    
    with patch('app.integrations.moodle.create_course.httpx.AsyncClient', return_value=mock_client):
        result = await integration.execute(
            config={
                "fullname": "Test Course 3",
                "shortname": "test_course_3",
                "categoryid": 3
            },
            credentials_resolver=credentials_resolver_no_payload,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        call_args = mock_client.post.call_args
        assert call_args[1]["data"]["wstoken"] == "test_moodle_token_direct"


@pytest.mark.asyncio
async def test_moodle_execute_url_normalization(
    integration, credentials_resolver, logger, bot_id, moodle_success_response
):
    """Тест нормализации URL Moodle."""
    # Тестируем разные варианты URL
    test_cases = [
        ("https://moodle.example.com", "https://moodle.example.com/webservice/rest/server.php"),
        ("https://moodle.example.com/", "https://moodle.example.com/webservice/rest/server.php"),
        ("https://moodle.example.com/webservice", "https://moodle.example.com/webservice/rest/server.php"),
        ("https://moodle.example.com/webservice/rest", "https://moodle.example.com/webservice/rest/server.php"),
        ("https://moodle.example.com/webservice/rest/server.php", "https://moodle.example.com/webservice/rest/server.php"),
    ]
    
    for input_url, expected_url in test_cases:
        resolver = MagicMock(spec=CredentialsResolver)
        resolver.get_default_for = AsyncMock(return_value={
            "payload": {
                "api_key": "test_token",
                "moodle_url": input_url
            }
        })
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = moodle_success_response
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch('app.integrations.moodle.create_course.httpx.AsyncClient', return_value=mock_client):
            await integration.execute(
                config={
                    "fullname": "Test",
                    "shortname": "test",
                    "categoryid": 1
                },
                credentials_resolver=resolver,
                bot_id=bot_id,
                logger=logger
            )
            
            call_args = mock_client.post.call_args
            assert call_args[0][0] == expected_url


@pytest.mark.asyncio
async def test_moodle_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={
            "fullname": "Test Course",
            "shortname": "test_course",
            "categoryid": 1
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "credentials not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_moodle_execute_missing_api_key(integration, logger, bot_id):
    """Тест выполнения без API ключа в credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "moodle_url": "https://moodle.example.com"
            # Отсутствует api_key
        }
    })
    
    result = await integration.execute(
        config={
            "fullname": "Test Course",
            "shortname": "test_course",
            "categoryid": 1
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "api key" in result["response"]["description"].lower() or "wstoken" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_moodle_execute_missing_url(integration, logger, bot_id):
    """Тест выполнения без URL в credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "api_key": "test_token"
            # Отсутствует moodle_url
        }
    })
    
    result = await integration.execute(
        config={
            "fullname": "Test Course",
            "shortname": "test_course",
            "categoryid": 1
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "url" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_moodle_execute_missing_config(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующими обязательными параметрами."""
    result = await integration.execute(
        config={},  # Отсутствуют fullname, shortname, categoryid
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "required" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_moodle_execute_moodle_api_error(
    integration, credentials_resolver, logger, bot_id, moodle_error_response
):
    """Тест обработки ошибки от Moodle API."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = moodle_error_response
    mock_response.raise_for_status = MagicMock()
    
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(return_value=mock_response)
    
    with patch('app.integrations.moodle.create_course.httpx.AsyncClient', return_value=mock_client):
        result = await integration.execute(
            config={
                "fullname": "Test Course",
                "shortname": "test_course",
                "categoryid": 1
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "moodle api error" in result["response"]["description"].lower()
        assert result["response"]["moodle_error_code"] == "invalidtoken"


@pytest.mark.asyncio
async def test_moodle_execute_http_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки HTTP ошибки."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server Error",
        request=MagicMock(),
        response=mock_response
    )
    
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(return_value=mock_response)
    
    with patch('app.integrations.moodle.create_course.httpx.AsyncClient', return_value=mock_client):
        result = await integration.execute(
            config={
                "fullname": "Test Course",
                "shortname": "test_course",
                "categoryid": 1
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "http error" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_moodle_execute_request_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибки запроса (сеть, таймаут и т.д.)."""
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(side_effect=httpx.RequestError("Connection failed"))
    
    with patch('app.integrations.moodle.create_course.httpx.AsyncClient', return_value=mock_client):
        result = await integration.execute(
            config={
                "fullname": "Test Course",
                "shortname": "test_course",
                "categoryid": 1
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "request error" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_moodle_execute_unexpected_response(
    integration, credentials_resolver, logger, bot_id
):
    """Тест обработки неожиданного формата ответа от Moodle API."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"unexpected": "format"}
    mock_response.raise_for_status = MagicMock()
    
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(return_value=mock_response)
    
    with patch('app.integrations.moodle.create_course.httpx.AsyncClient', return_value=mock_client):
        result = await integration.execute(
            config={
                "fullname": "Test Course",
                "shortname": "test_course",
                "categoryid": 1
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "unexpected" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_moodle_execute_with_optional_params(
    integration, credentials_resolver, logger, bot_id, moodle_success_response
):
    """Тест создания курса со всеми опциональными параметрами."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = moodle_success_response
    mock_response.raise_for_status = MagicMock()
    
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(return_value=mock_response)
    
    with patch('app.integrations.moodle.create_course.httpx.AsyncClient', return_value=mock_client):
        result = await integration.execute(
            config={
                "fullname": "Advanced Python Course",
                "shortname": "python_advanced",
                "categoryid": 5,
                "summary": "Advanced Python programming course",
                "summaryformat": 1,
                "format": "weeks",
                "startdate": 1704067200,
                "enddate": 1735689600,
                "visible": 1,
                "lang": "ru",
                "numsections": 12
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        
        # Проверяем, что все параметры были переданы
        call_args = mock_client.post.call_args
        data = call_args[1]["data"]
        
        assert data["courses[0][summary]"] == "Advanced Python programming course"
        # httpx может преобразовать int в str при отправке, проверяем оба варианта
        assert data["courses[0][summaryformat]"] in (1, "1")
        assert data["courses[0][format]"] == "weeks"
        assert data["courses[0][startdate]"] in (1704067200, "1704067200")
        assert data["courses[0][enddate]"] in (1735689600, "1735689600")
        assert data["courses[0][visible]"] in (1, "1")
        assert data["courses[0][lang]"] == "ru"
        assert data["courses[0][numsections]"] in (12, "12")


@pytest.mark.asyncio
async def test_moodle_execute_list_response(
    integration, credentials_resolver, logger, bot_id
):
    """Тест обработки ответа в формате списка от Moodle API."""
    # Moodle может вернуть список с одним элементом
    list_response = [{"id": 99, "shortname": "list_course"}]
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = list_response
    mock_response.raise_for_status = MagicMock()
    
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(return_value=mock_response)
    
    with patch('app.integrations.moodle.create_course.httpx.AsyncClient', return_value=mock_client):
        result = await integration.execute(
            config={
                "fullname": "List Course",
                "shortname": "list_course",
                "categoryid": 1
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["course_id"] == 99

