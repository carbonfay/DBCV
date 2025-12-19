"""Тесты для OpenWeatherMap Get Forecast интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.openweathermap.get_forecast import OpenweathermapGetForecastIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


# Фикстуры
@pytest.fixture
def forecast_integration():
    """Создает экземпляр Forecast интеграции."""
    return OpenweathermapGetForecastIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "api_key": "test_api_key_12345"
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


# Тесты для get_forecast
def test_forecast_metadata(forecast_integration):
    """Тест метаданных Forecast интеграции."""
    metadata = forecast_integration.metadata
    
    assert metadata.id == "openweathermap_get_forecast"
    assert metadata.version == "1.0.0"
    assert metadata.name == "OpenWeatherMap Get Forecast"
    assert metadata.category == "weather"
    assert metadata.credentials_provider == "openweathermap"
    assert metadata.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_forecast_execute_success(forecast_integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения Forecast интеграции."""
    mock_response_data = {
        "cod": "200",
        "message": 0,
        "cnt": 40,
        "city": {
            "id": 524901,
            "name": "Moscow",
            "country": "RU",
            "coord": {"lat": 55.7558, "lon": 37.6173}
        },
        "list": [
            {
                "dt": 1609459200,
                "main": {"temp": 5.5, "feels_like": 3.2},
                "weather": [{"main": "Clear", "description": "clear sky"}]
            }
        ]
    }
    
    with patch('app.integrations.openweathermap.get_forecast.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.headers.get.return_value = "application/json"
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await forecast_integration.execute(
            config={
                "location": "Moscow,ru",
                "units": "metric",
                "lang": "ru"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["city"]["name"] == "Moscow"
        assert result["response"]["result"]["cnt"] == 40
        mock_client.get.assert_called_once()


@pytest.mark.asyncio
async def test_forecast_execute_no_credentials(forecast_integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await forecast_integration.execute(
        config={"location": "Moscow"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_forecast_execute_missing_location(forecast_integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующим location."""
    result = await forecast_integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400

