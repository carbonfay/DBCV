"""Тесты для OpenWeatherMap Get Daily Forecast интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.openweathermap.get_daily_forecast import OpenweathermapGetDailyForecastIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


# Фикстуры
@pytest.fixture
def daily_forecast_integration():
    """Создает экземпляр Daily Forecast интеграции."""
    return OpenweathermapGetDailyForecastIntegration()


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


# Тесты для get_daily_forecast
def test_daily_forecast_metadata(daily_forecast_integration):
    """Тест метаданных Daily Forecast интеграции."""
    metadata = daily_forecast_integration.metadata
    
    assert metadata.id == "openweathermap_get_daily_forecast"
    assert metadata.version == "1.0.0"
    assert metadata.name == "OpenWeatherMap Get Daily Forecast"
    assert metadata.category == "weather"
    assert metadata.credentials_provider == "openweathermap"
    assert metadata.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_daily_forecast_execute_success(daily_forecast_integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения Daily Forecast интеграции."""
    mock_response_data = {
        "cod": "200",
        "message": 0,
        "cnt": 7,
        "city": {
            "id": 524901,
            "name": "Moscow",
            "country": "RU",
            "coord": {"lat": 55.7558, "lon": 37.6173},
            "population": 11920000,
            "timezone": 10800
        },
        "list": [
            {
                "dt": 1609459200,
                "temp": {"day": 5.5, "min": 2.1, "max": 8.9},
                "weather": [{"main": "Clear", "description": "clear sky"}]
            }
        ]
    }
    
    with patch('app.integrations.openweathermap.get_daily_forecast.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.headers.get.return_value = "application/json"
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await daily_forecast_integration.execute(
            config={
                "location": "55.7558,37.6173",
                "units": "metric",
                "lang": "ru",
                "cnt": 7
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["city"]["name"] == "Moscow"
        assert result["response"]["result"]["cnt"] == 7
        mock_client.get.assert_called_once()


@pytest.mark.asyncio
async def test_daily_forecast_execute_with_city_name(daily_forecast_integration, credentials_resolver, logger, bot_id):
    """Тест выполнения Daily Forecast с названием города."""
    mock_response_data = {
        "cod": "200",
        "message": 0,
        "cnt": 7,
        "city": {"id": 524901, "name": "Moscow", "country": "RU"},
        "list": []
    }
    
    with patch('app.integrations.openweathermap.get_daily_forecast.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.headers.get.return_value = "application/json"
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await daily_forecast_integration.execute(
            config={
                "location": "Moscow,ru",
                "units": "metric"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        # Проверяем, что был вызван правильный endpoint
        call_args = mock_client.get.call_args
        assert "forecast/daily" in call_args[0][0]

