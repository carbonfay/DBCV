"""Тесты для OpenWeatherMap интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from app.integrations.openweathermap.get_uv_index import GetUVIndexIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр OpenWeatherMap интеграции."""
    return GetUVIndexIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={"payload": {"api_key": "test_api_key_12345"}})
    return resolver


@pytest.fixture
def logger():
    """Создает mock logger."""
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    """Создает test bot ID."""
    return UUID("12345678-1234-5678-1234-567812345678")


def test_openweathermap_metadata(integration):
    """Тест метаданных OpenWeatherMap интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "openweathermap_get_uv_index"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Get UV Index"
    assert metadata.category == "weather"
    assert metadata.credentials_provider == "openweathermap"
    assert metadata.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_openweathermap_execute_success(integration, credentials_resolver, logger, bot_id):
    """Тест успешного получения UV Index."""
    mock_response_data = {
        "value": 7.5,
        "lat": 55.7558,
        "lon": 37.6173,
        "date": "2025-12-09",
        "date_iso": "2025-12-09T12:00:00Z"
    }
    
    with patch('httpx.AsyncClient') as mock_client_class:
        # Настраиваем mock для HTTP ответа
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=mock_response_data)
        mock_response.text = "{}"

        # Настраиваем mock для client
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "latitude": 55.7558,
                "longitude": 37.6173
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["uv_index"] == 7.5
        assert result["response"]["result"]["latitude"] == 55.7558
        assert result["response"]["result"]["longitude"] == 37.6173


@pytest.mark.asyncio
async def test_openweathermap_execute_missing_params(integration, credentials_resolver, logger, bot_id):
    """Тест ошибки при отсутствии параметров."""
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert "обязательными параметрами" in result["response"]["error"]


@pytest.mark.asyncio
async def test_openweathermap_execute_invalid_latitude(integration, credentials_resolver, logger, bot_id):
    """Тест ошибки при неверной широте."""
    result = await integration.execute(
        config={
            "latitude": 91,  # Неверно: > 90
            "longitude": 37.6173
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert "Latitude" in result["response"]["error"]


@pytest.mark.asyncio
async def test_openweathermap_execute_invalid_longitude(integration, credentials_resolver, logger, bot_id):
    """Тест ошибки при неверной долготе."""
    result = await integration.execute(
        config={
            "latitude": 55.7558,
            "longitude": 181  # Неверно: > 180
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert "Longitude" in result["response"]["error"]


@pytest.mark.asyncio
async def test_openweathermap_execute_no_credentials(integration, logger, bot_id):
    """Тест ошибки при отсутствии credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_credential = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={
            "latitude": 55.7558,
            "longitude": 37.6173
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert "API ключ" in result["response"]["error"]


@pytest.mark.asyncio
async def test_openweathermap_execute_api_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибки API."""
    with patch('httpx.AsyncClient') as mock_client_class:
        # Настраиваем mock для ошибки HTTP
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        # Настраиваем mock для client
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "latitude": 55.7558,
                "longitude": 37.6173
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is False
        assert "ошибку" in result["response"]["error"]
