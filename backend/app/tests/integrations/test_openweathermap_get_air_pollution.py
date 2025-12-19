"""Тесты для OpenWeatherMap Get Air Pollution интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.openweathermap.get_air_pollution import OpenweathermapGetAirPollutionIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


# Фикстуры
@pytest.fixture
def air_pollution_integration():
    """Создает экземпляр Air Pollution интеграции."""
    return OpenweathermapGetAirPollutionIntegration()


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


# Тесты для get_air_pollution
def test_air_pollution_metadata(air_pollution_integration):
    """Тест метаданных Air Pollution интеграции."""
    metadata = air_pollution_integration.metadata
    
    assert metadata.id == "openweathermap_get_air_pollution"
    assert metadata.version == "1.0.0"
    assert metadata.name == "OpenWeatherMap Get Air Pollution"
    assert metadata.category == "weather"
    assert metadata.credentials_provider == "openweathermap"
    assert metadata.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_air_pollution_execute_success(air_pollution_integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения Air Pollution интеграции."""
    mock_response_data = {
        "coord": {"lon": 37.6173, "lat": 55.7558},
        "list": [
            {
                "dt": 1609459200,
                "main": {"aqi": 2},
                "components": {
                    "co": 203.609,
                    "no": 0.0,
                    "no2": 0.396,
                    "o3": 75.102,
                    "so2": 0.648,
                    "pm2_5": 23.253,
                    "pm10": 92.214,
                    "nh3": 0.117
                }
            }
        ]
    }
    
    with patch('app.integrations.openweathermap.get_air_pollution.httpx') as mock_httpx:
        # Мокаем geocoding для названия города
        mock_client = AsyncMock()
        mock_geocode_response = MagicMock()
        mock_geocode_response.status_code = 200
        mock_geocode_response.json.return_value = [
            {"lat": 55.7558, "lon": 37.6173, "name": "Moscow", "country": "RU"}
        ]
        
        mock_air_response = MagicMock()
        mock_air_response.status_code = 200
        mock_air_response.json.return_value = mock_response_data
        mock_air_response.headers.get.return_value = "application/json"
        
        # Первый вызов - geocoding, второй - air pollution
        mock_client.get = AsyncMock(side_effect=[mock_geocode_response, mock_air_response])
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await air_pollution_integration.execute(
            config={
                "location": "Moscow,ru"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["coord"]["lat"] == 55.7558
        assert len(result["response"]["result"]["list"]) == 1
        assert result["response"]["result"]["list"][0]["main"]["aqi"] == 2
        # Проверяем, что было 2 вызова: geocoding и air pollution
        assert mock_client.get.call_count == 2


@pytest.mark.asyncio
async def test_air_pollution_execute_with_coordinates(air_pollution_integration, credentials_resolver, logger, bot_id):
    """Тест выполнения Air Pollution с координатами."""
    mock_response_data = {
        "coord": {"lon": 37.6173, "lat": 55.7558},
        "list": [{"dt": 1609459200, "main": {"aqi": 2}, "components": {}}]
    }
    
    with patch('app.integrations.openweathermap.get_air_pollution.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.headers.get.return_value = "application/json"
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await air_pollution_integration.execute(
            config={
                "location": "55.7558,37.6173"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        # С координатами должен быть только один вызов (без geocoding)
        assert mock_client.get.call_count == 1
        call_args = mock_client.get.call_args
        assert "air_pollution" in call_args[0][0]


@pytest.mark.asyncio
async def test_air_pollution_execute_no_credentials(air_pollution_integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await air_pollution_integration.execute(
        config={"location": "55.7558,37.6173"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_air_pollution_execute_api_error(air_pollution_integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибки API."""
    with patch('app.integrations.openweathermap.get_air_pollution.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Invalid API key"}
        mock_response.headers.get.return_value = "application/json"
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await air_pollution_integration.execute(
            config={
                "location": "55.7558,37.6173"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 401
        assert "Invalid API key" in result["response"]["description"]

