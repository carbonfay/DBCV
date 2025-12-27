"""Тесты для Yandex Maps Route интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import sys
import os

# Добавляем путь к корню приложения для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Импортируем напрямую, чтобы избежать проблем с conftest
from app.integrations.yandex.maps_route import YandexMapsRouteIntegration


@pytest.fixture
def integration():
    """Создает экземпляр Yandex Maps Route интеграции."""
    return YandexMapsRouteIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock()
    resolver.get_default_for = AsyncMock(return_value={
        "api_key": "test-yandex-api-key-123"
    })
    return resolver


@pytest.fixture
def no_credentials_resolver():
    """Создает mock credentials resolver без учетных данных."""
    resolver = MagicMock()
    resolver.get_default_for = AsyncMock(return_value=None)
    return resolver


@pytest.fixture
def logger():
    """Создает mock logger."""
    logger_mock = MagicMock()
    # Добавляем async методы
    logger_mock.error = AsyncMock()
    logger_mock.info = AsyncMock()
    logger_mock.debug = AsyncMock()
    return logger_mock


if __name__ == "__main__":
    import pytest
    # Run tests with detailed output
    pytest.main([__file__, "-v", "--tb=short"])


@pytest.fixture
def bot_id():
    """Создает test bot ID."""
    return UUID("12345678-1234-5678-1234-567812345678")


def test_yandex_maps_route_metadata(integration):
    """Тест метаданных Yandex Maps Route интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "yandex_maps_route"
    assert metadata.version == "1.0.1"
    assert metadata.name == "Yandex Maps Route"
    assert metadata.category == "maps"
    assert metadata.credentials_provider == "yandex"
    assert metadata.credentials_strategy == "api_key"
    assert "origin_lat" in metadata.config_schema["required"]
    assert "origin_lon" in metadata.config_schema["required"]
    assert "destination_lat" in metadata.config_schema["required"]
    assert "destination_lon" in metadata.config_schema["required"]


@pytest.mark.asyncio
async def test_yandex_maps_route_execute_success(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения Yandex Maps Route интеграции."""
    with patch('httpx.AsyncClient') as mock_client_class:
        # Настраиваем mock для httpx
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "OK",
            "routes": [
                {
                    "legs": [
                        {
                            "steps": [
                                {
                                    "length": 1000,
                                    "duration": 120
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "origin_lat": 55.7539,
                "origin_lon": 37.6208,
                "destination_lat": 55.7520,
                "destination_lon": 37.6175,
                "mode": "driving"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["status_code"] == 200
        assert "summary" in result["response"]["result"]
        assert "data" in result["response"]["result"]
        
        # Проверяем, что API был вызван
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "api.routing.yandex.net" in str(call_args)


@pytest.mark.asyncio
async def test_yandex_maps_route_execute_no_credentials(integration, no_credentials_resolver, logger, bot_id):
    """Тест выполнения без credentials."""
    result = await integration.execute(
        config={
            "origin_lat": 55.7539,
            "origin_lon": 37.6208,
            "destination_lat": 55.7520,
            "destination_lon": 37.6175
        },
        credentials_resolver=no_credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_yandex_maps_route_execute_missing_config(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующими параметрами."""
    # Тест с отсутствующими координатами
    result = await integration.execute(
        config={},  # Отсутствуют все обязательные поля
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "required" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_yandex_maps_route_execute_invalid_coordinates(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с невалидными координатами."""
    result = await integration.execute(
        config={
            "origin_lat": "invalid",
            "origin_lon": 37.6208,
            "destination_lat": 55.7520,
            "destination_lon": 37.6175
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "coordinates" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_yandex_maps_route_execute_with_via_points(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с промежуточными точками."""
    with patch('httpx.AsyncClient') as mock_client_class:
        # Настраиваем mock для httpx
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "OK",
            "routes": [
                {
                    "legs": [
                        {
                            "steps": [
                                {
                                    "length": 500,
                                    "duration": 60
                                },
                                {
                                    "length": 300,
                                    "duration": 40
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Выполняем интеграцию с промежуточными точками
        result = await integration.execute(
            config={
                "origin_lat": 55.7539,
                "origin_lon": 37.6208,
                "destination_lat": 55.7520,
                "destination_lon": 37.6175,
                "via_points": [
                    {"lat": 55.7530, "lon": 37.6190},
                    {"lat": 55.7525, "lon": 37.6180}
                ],
                "mode": "driving"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["status_code"] == 200


@pytest.mark.asyncio
async def test_yandex_maps_route_execute_different_modes(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с разными режимами передвижения."""
    modes = ["driving", "walking", "bicycle", "transit", "truck", "scooter"]
    
    for mode in modes:
        with patch('httpx.AsyncClient') as mock_client_class:
            # Настраиваем mock для httpx
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "OK",
                "routes": [
                    {
                        "legs": [
                            {
                                "steps": [
                                    {
                                        "length": 1000,
                                        "duration": 120
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Выполняем интеграцию
            result = await integration.execute(
                config={
                    "origin_lat": 55.7539,
                    "origin_lon": 37.6208,
                    "destination_lat": 55.7520,
                    "destination_lon": 37.6175,
                    "mode": mode
                },
                credentials_resolver=credentials_resolver,
                bot_id=bot_id,
                logger=logger
            )
            
            # Проверяем результат
            assert result["response"]["ok"] is True
            assert result["response"]["result"]["summary"]["mode"] == mode


@pytest.mark.asyncio
async def test_yandex_maps_route_execute_api_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибок API."""
    with patch('httpx.AsyncClient') as mock_client_class:
        # Настраиваем mock для ошибки API
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "error": "Invalid API key"
        }
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "origin_lat": 55.7539,
                "origin_lon": 37.6208,
                "destination_lat": 55.7520,
                "destination_lon": 37.6175
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 403


@pytest.mark.asyncio
async def test_yandex_maps_route_execute_network_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки сетевых ошибок."""
    with patch('httpx.AsyncClient') as mock_client_class:
        # Настраиваем mock для сетевой ошибки
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.RequestError("Network error")
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "origin_lat": 55.7539,
                "origin_lon": 37.6208,
                "destination_lat": 55.7520,
                "destination_lon": 37.6175
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
