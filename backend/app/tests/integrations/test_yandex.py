"""Тесты для Yandex Weather Forecast интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.yandex.weather_forecast import YandexWeatherForecastIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр Yandex Weather Forecast интеграции."""
    return YandexWeatherForecastIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "api_key": "test-yandex-api-key"
    })
    return resolver


@pytest.fixture
def logger():
    """Создает mock logger."""
    logger = MagicMock(spec=BotLogger)
    logger.error = AsyncMock()
    logger.info = AsyncMock()
    return logger


@pytest.fixture
def bot_id():
    """Создает test bot ID."""
    return UUID("12345678-1234-5678-1234-567812345678")


def test_yandex_weather_forecast_metadata(integration):
    """Тест метаданных Yandex Weather Forecast интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "yandex_weather_forecast"
    assert metadata.version == "1.0.1"
    assert metadata.name == "Yandex Weather Forecast"
    assert metadata.category == "weather"
    assert metadata.credentials_provider == "other"
    assert metadata.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_execute_success(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения интеграции."""
    config = {
        "lat": 55.7558,
        "lon": 37.6173,
        "lang": "ru_RU",
        "limit": 3,
        "hours": True,
        "extra": True
    }
    
    mock_response_data = {
        "now": 1638360000,
        "now_dt": "2021-12-01T12:00:00.000Z",
        "info": {"lat": 55.7558, "lon": 37.6173},
        "fact": {"temp": -5, "feels_like": -10},
        "forecasts": [{"date": "2021-12-01", "parts": {"day": {"temp_avg": -3}}}]
    }
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await integration.execute(config, credentials_resolver, bot_id, logger)
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"] == mock_response_data
        
        # Проверяем, что get был вызван с правильными параметрами
        mock_client.return_value.__aenter__.return_value.get.assert_called_once()
        call_args = mock_client.return_value.__aenter__.return_value.get.call_args
        assert call_args[1]["params"]["lat"] == 55.7558
        assert call_args[1]["params"]["lon"] == 37.6173
        assert call_args[1]["params"]["lang"] == "ru_RU"
        assert call_args[1]["params"]["limit"] == 3
        assert call_args[1]["params"]["hours"] == "true"
        assert call_args[1]["params"]["extra"] == "true"
        assert call_args[1]["headers"]["X-Yandex-API-Key"] == "test-yandex-api-key"


@pytest.mark.asyncio
async def test_execute_missing_credentials(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения без credentials."""
    config = {"lat": 55.7558, "lon": 37.6173}
    
    credentials_resolver.get_default_for.return_value = None
    
    result = await integration.execute(config, credentials_resolver, bot_id, logger)
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "not found" in result["response"]["description"]


@pytest.mark.asyncio
async def test_execute_invalid_lat_lon(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с некорректными координатами."""
    config = {"lat": 100, "lon": 37.6173}  # lat вне диапазона
    
    result = await integration.execute(config, credentials_resolver, bot_id, logger)
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "lat must be between" in result["response"]["description"]


@pytest.mark.asyncio
async def test_execute_api_error(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с ошибкой API."""
    config = {"lat": 55.7558, "lon": 37.6173}
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Invalid API key"
        
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await integration.execute(config, credentials_resolver, bot_id, logger)
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 403
        assert "Invalid API key" in result["response"]["description"]