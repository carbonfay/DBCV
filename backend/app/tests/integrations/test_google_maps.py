"""Тесты для Google Maps Get Elevation интеграции."""
import os
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch, Mock

from app.integrations.google_maps.get_elevation import GoogleMapsGetElevationIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр Google Maps интеграции."""
    return GoogleMapsGetElevationIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "api_key": "test-api-key-12345"
        }
    })
    return resolver


@pytest.fixture
def credentials_resolver_no_payload():
    """Создает mock credentials resolver без payload (обратная совместимость)."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "api_key": "test-api-key-12345"
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


def test_google_maps_metadata(integration):
    """Тест метаданных Google Maps интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "google_maps_get_elevation"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Google Maps Get Elevation"
    assert metadata.category == "maps"
    assert metadata.description == "Получение высоты над уровнем моря для заданных координат или вдоль пути"
    assert metadata.icon_s3_key == "icons/integrations/google_maps.svg"
    assert metadata.color == "#4285F4"
    assert metadata.credentials_provider == "google_maps"
    assert metadata.credentials_strategy == "api_key"
    assert metadata.library_name == "googlemaps>=4.10.0" or metadata.library_name is None
    assert metadata.examples is not None
    assert len(metadata.examples) == 3


@pytest.mark.asyncio
async def test_google_maps_execute_success_locations(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения Google Maps интеграции для locations."""
    # Мокируем результаты API
    mock_results = [
        {
            "location": {"lat": 40.714728, "lng": -73.998672},
            "elevation": 10.5
        },
        {
            "location": {"lat": 40.758896, "lng": -73.985130},
            "elevation": 15.2
        }
    ]
    
    with patch('app.integrations.google_maps.get_elevation.googlemaps') as mock_googlemaps:
        # Настраиваем mock клиента
        mock_client = MagicMock()
        mock_client.elevation = Mock(return_value=mock_results)
        mock_googlemaps.Client.return_value = mock_client
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "locations": [
                    {"lat": 40.714728, "lng": -73.998672},
                    {"lat": 40.758896, "lng": -73.985130}
                ],
                "unit": "meters"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["unit"] == "meters"
        assert result["response"]["result"]["count"] == 2
        assert len(result["response"]["result"]["results"]) == 2
        assert result["response"]["result"]["results"][0]["elevation"] == 10.5
        assert result["response"]["result"]["results"][1]["elevation"] == 15.2
        
        # Проверяем, что метод библиотеки был вызван
        mock_client.elevation.assert_called_once()
        mock_googlemaps.Client.assert_called_once_with(key="test-api-key-12345")


@pytest.mark.asyncio
async def test_google_maps_execute_success_path(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения Google Maps интеграции для path."""
    # Мокируем результаты API
    mock_results = [
        {
            "location": {"lat": 40.714728, "lng": -73.998672},
            "elevation": 10.5
        },
        {
            "location": {"lat": 40.720000, "lng": -73.980000},
            "elevation": 12.3
        },
        {
            "location": {"lat": 40.758896, "lng": -73.985130},
            "elevation": 15.2
        }
    ]
    
    with patch('app.integrations.google_maps.get_elevation.googlemaps') as mock_googlemaps:
        # Настраиваем mock клиента
        mock_client = MagicMock()
        mock_client.elevation_along_path = Mock(return_value=mock_results)
        mock_googlemaps.Client.return_value = mock_client
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "path": [
                    {"lat": 40.714728, "lng": -73.998672},
                    {"lat": 40.758896, "lng": -73.985130}
                ],
                "samples": 3,
                "unit": "meters"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["unit"] == "meters"
        assert result["response"]["result"]["count"] == 3
        
        # Проверяем, что метод библиотеки был вызван
        mock_client.elevation_along_path.assert_called_once()
        mock_googlemaps.Client.assert_called_once_with(key="test-api-key-12345")


@pytest.mark.asyncio
async def test_google_maps_execute_unit_feet(integration, credentials_resolver, logger, bot_id):
    """Тест конвертации единиц измерения в футы."""
    # Мокируем результаты API (в метрах)
    mock_results = [
        {
            "location": {"lat": 40.714728, "lng": -73.998672},
            "elevation": 10.5  # метры
        }
    ]
    
    with patch('app.integrations.google_maps.get_elevation.googlemaps') as mock_googlemaps:
        mock_client = MagicMock()
        mock_client.elevation = Mock(return_value=mock_results)
        mock_googlemaps.Client.return_value = mock_client
        
        # Выполняем интеграцию с unit="feet"
        result = await integration.execute(
            config={
                "locations": [
                    {"lat": 40.714728, "lng": -73.998672}
                ],
                "unit": "feet"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем, что высота конвертирована в футы
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["unit"] == "feet"
        # 10.5 метров * 3.28084 = ~34.45 футов
        expected_feet = 10.5 * 3.28084
        assert abs(result["response"]["result"]["results"][0]["elevation"] - expected_feet) < 0.01


@pytest.mark.asyncio
async def test_google_maps_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={
            "locations": [{"lat": 40.714728, "lng": -73.998672}]
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_execute_no_api_key_in_credentials(integration, logger, bot_id):
    """Тест выполнения без api_key в credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "wrong_key": "value"
        }
    })
    
    result = await integration.execute(
        config={
            "locations": [{"lat": 40.714728, "lng": -73.998672}]
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "api_key" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_execute_credentials_no_payload(integration, credentials_resolver_no_payload, logger, bot_id):
    """Тест выполнения с credentials без payload (обратная совместимость)."""
    mock_results = [
        {
            "location": {"lat": 40.714728, "lng": -73.998672},
            "elevation": 10.5
        }
    ]
    
    with patch('app.integrations.google_maps.get_elevation.googlemaps') as mock_googlemaps:
        mock_client = MagicMock()
        mock_client.elevation = Mock(return_value=mock_results)
        mock_googlemaps.Client.return_value = mock_client
        
        result = await integration.execute(
            config={
                "locations": [{"lat": 40.714728, "lng": -73.998672}]
            },
            credentials_resolver=credentials_resolver_no_payload,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        mock_googlemaps.Client.assert_called_once_with(key="test-api-key-12345")


@pytest.mark.asyncio
async def test_google_maps_execute_missing_locations_and_path(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения без locations и path."""
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "locations" in result["response"]["description"].lower() or "path" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_execute_path_without_samples(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения path без samples."""
    result = await integration.execute(
        config={
            "path": [
                {"lat": 40.714728, "lng": -73.998672},
                {"lat": 40.758896, "lng": -73.985130}
            ]
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "samples" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_execute_path_samples_too_small(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения path с samples < 2."""
    result = await integration.execute(
        config={
            "path": [
                {"lat": 40.714728, "lng": -73.998672},
                {"lat": 40.758896, "lng": -73.985130}
            ],
            "samples": 1
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "samples" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_execute_api_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибки API."""
    with patch('app.integrations.google_maps.get_elevation.googlemaps') as mock_googlemaps:
        mock_client = MagicMock()
        # Создаем mock ошибку с атрибутом status
        mock_error = Exception("API Error: Invalid API key")
        mock_error.status = 403
        mock_client.elevation = Mock(side_effect=mock_error)
        mock_googlemaps.Client.return_value = mock_client
        
        # Импортируем ApiError для мокирования
        with patch('app.integrations.google_maps.get_elevation.ApiError', Exception):
            result = await integration.execute(
                config={
                    "locations": [{"lat": 40.714728, "lng": -73.998672}]
                },
                credentials_resolver=credentials_resolver,
                bot_id=bot_id,
                logger=logger
            )
            
            assert result["response"]["ok"] is False
            # Код ошибки должен быть из статуса ошибки или 500 по умолчанию
            assert result["response"]["error_code"] in [400, 403, 500]


@pytest.mark.asyncio
async def test_google_maps_execute_library_not_available(integration, logger, bot_id):
    """Тест выполнения когда библиотека не установлена."""
    # Временно устанавливаем флаг недоступности библиотеки
    original_available = integration.__class__.__module__
    
    with patch('app.integrations.google_maps.get_elevation.GOOGLEMAPS_AVAILABLE', False):
        # Пересоздаем интеграцию, чтобы флаг применился
        integration = GoogleMapsGetElevationIntegration()
        
        credentials_resolver = MagicMock(spec=CredentialsResolver)
        credentials_resolver.get_default_for = AsyncMock(return_value={
            "payload": {"api_key": "test-key"}
        })
        
        result = await integration.execute(
            config={
                "locations": [{"lat": 40.714728, "lng": -73.998672}]
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "not installed" in result["response"]["description"].lower() or "not available" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_execute_value_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ValueError (неверные параметры)."""
    with patch('app.integrations.google_maps.get_elevation.googlemaps') as mock_googlemaps:
        mock_client = MagicMock()
        mock_client.elevation = Mock(side_effect=ValueError("Invalid coordinates"))
        mock_googlemaps.Client.return_value = mock_client
        
        result = await integration.execute(
            config={
                "locations": [{"lat": 40.714728, "lng": -73.998672}]
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "invalid" in result["response"]["description"].lower() or "parameter" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_execute_unexpected_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки неожиданной ошибки."""
    with patch('app.integrations.google_maps.get_elevation.googlemaps') as mock_googlemaps:
        mock_client = MagicMock()
        mock_client.elevation = Mock(side_effect=RuntimeError("Unexpected error"))
        mock_googlemaps.Client.return_value = mock_client
        
        result = await integration.execute(
            config={
                "locations": [{"lat": 40.714728, "lng": -73.998672}]
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "error" in result["response"]["description"].lower()

