"""Тесты для Google Maps Get Place Photos интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch, Mock

from app.integrations.google_maps.get_place_photos import GoogleMapsGetPlacePhotosIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр Google Maps Get Place Photos интеграции."""
    return GoogleMapsGetPlacePhotosIntegration()


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


def test_google_maps_place_photos_metadata(integration):
    """Тест метаданных Google Maps Get Place Photos интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "google_maps_get_place_photos"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Google Maps Get Place Photos"
    assert metadata.category == "maps"
    assert metadata.description == "Получение фотографий места по place_id или поисковому запросу"
    assert metadata.icon_s3_key == "icons/integrations/google_maps.svg"
    assert metadata.color == "#4285F4"
    assert metadata.credentials_provider == "google_maps"
    assert metadata.credentials_strategy == "api_key"
    assert metadata.library_name == "googlemaps>=4.10.0" or metadata.library_name is None
    assert metadata.examples is not None
    assert len(metadata.examples) == 3


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_success_with_place_id(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения Google Maps интеграции с place_id."""
    # Мокируем результаты API
    mock_place_details = {
        "result": {
            "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
            "name": "Eiffel Tower",
            "photos": [
                {
                    "photo_reference": "photo_ref_1",
                    "width": 4000,
                    "height": 3000,
                    "html_attributions": ["<a href=\"...\">Attribution</a>"]
                },
                {
                    "photo_reference": "photo_ref_2",
                    "width": 3000,
                    "height": 2000,
                    "html_attributions": ["<a href=\"...\">Attribution 2</a>"]
                }
            ]
        }
    }
    
    with patch('app.integrations.google_maps.get_place_photos.googlemaps') as mock_googlemaps:
        # Настраиваем mock клиента
        mock_client = MagicMock()
        mock_client.place = Mock(return_value=mock_place_details)
        mock_googlemaps.Client.return_value = mock_client
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
                "max_photos": 2
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["place_id"] == "ChIJN1t_tDeuEmsRUsoyG83frY4"
        assert result["response"]["result"]["place_name"] == "Eiffel Tower"
        assert result["response"]["result"]["count"] == 2
        assert len(result["response"]["result"]["photos"]) == 2
        assert result["response"]["result"]["photos"][0]["photo_reference"] == "photo_ref_1"
        assert result["response"]["result"]["photos"][0]["url"] is not None
        assert "photo_reference=photo_ref_1" in result["response"]["result"]["photos"][0]["url"]
        assert "key=test-api-key-12345" in result["response"]["result"]["photos"][0]["url"]
        
        # Проверяем, что метод библиотеки был вызван
        mock_client.place.assert_called_once()
        mock_googlemaps.Client.assert_called_once_with(key="test-api-key-12345")


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_success_with_query(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения Google Maps интеграции с query (поиск места)."""
    # Мокируем результаты API
    mock_find_place_result = {
        "candidates": [
            {
                "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
                "name": "Eiffel Tower"
            }
        ]
    }
    
    mock_place_details = {
        "result": {
            "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
            "name": "Eiffel Tower",
            "photos": [
                {
                    "photo_reference": "photo_ref_1",
                    "width": 4000,
                    "height": 3000,
                    "html_attributions": []
                }
            ]
        }
    }
    
    with patch('app.integrations.google_maps.get_place_photos.googlemaps') as mock_googlemaps:
        # Настраиваем mock клиента
        mock_client = MagicMock()
        mock_client.find_place = Mock(return_value=mock_find_place_result)
        mock_client.place = Mock(return_value=mock_place_details)
        mock_googlemaps.Client.return_value = mock_client
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "query": "Eiffel Tower",
                "max_photos": 1
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["place_id"] == "ChIJN1t_tDeuEmsRUsoyG83frY4"
        assert result["response"]["result"]["count"] == 1
        
        # Проверяем, что методы библиотеки были вызваны
        mock_client.find_place.assert_called_once()
        mock_client.place.assert_called_once()


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_with_size_limits(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с ограничениями размера фотографий."""
    mock_place_details = {
        "result": {
            "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
            "name": "Eiffel Tower",
            "photos": [
                {
                    "photo_reference": "photo_ref_1",
                    "width": 4000,
                    "height": 3000,
                    "html_attributions": []
                }
            ]
        }
    }
    
    with patch('app.integrations.google_maps.get_place_photos.googlemaps') as mock_googlemaps:
        mock_client = MagicMock()
        mock_client.place = Mock(return_value=mock_place_details)
        mock_googlemaps.Client.return_value = mock_client
        
        # Выполняем интеграцию с ограничениями размера
        result = await integration.execute(
            config={
                "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
                "max_photos": 1,
                "max_width": 800,
                "max_height": 600
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["photos"][0]["requested_max_width"] == 800
        assert result["response"]["result"]["photos"][0]["requested_max_height"] == 600
        assert "maxwidth=800" in result["response"]["result"]["photos"][0]["url"]
        assert "maxheight=600" in result["response"]["result"]["photos"][0]["url"]


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_max_photos_limit(integration, credentials_resolver, logger, bot_id):
    """Тест ограничения количества фотографий через max_photos."""
    mock_place_details = {
        "result": {
            "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
            "name": "Eiffel Tower",
            "photos": [
                {"photo_reference": "photo_ref_1", "width": 4000, "height": 3000, "html_attributions": []},
                {"photo_reference": "photo_ref_2", "width": 3000, "height": 2000, "html_attributions": []},
                {"photo_reference": "photo_ref_3", "width": 2000, "height": 1500, "html_attributions": []},
                {"photo_reference": "photo_ref_4", "width": 1000, "height": 800, "html_attributions": []},
                {"photo_reference": "photo_ref_5", "width": 500, "height": 400, "html_attributions": []}
            ]
        }
    }
    
    with patch('app.integrations.google_maps.get_place_photos.googlemaps') as mock_googlemaps:
        mock_client = MagicMock()
        mock_client.place = Mock(return_value=mock_place_details)
        mock_googlemaps.Client.return_value = mock_client
        
        # Запрашиваем только 2 фотографии из 5 доступных
        result = await integration.execute(
            config={
                "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
                "max_photos": 2
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем, что вернулось только 2 фотографии
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["count"] == 2
        assert len(result["response"]["result"]["photos"]) == 2
        assert result["response"]["result"]["requested_max"] == 2


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={
            "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4"
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_no_api_key_in_credentials(integration, logger, bot_id):
    """Тест выполнения без api_key в credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "wrong_key": "value"
        }
    })
    
    result = await integration.execute(
        config={
            "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4"
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "api_key" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_credentials_no_payload(integration, credentials_resolver_no_payload, logger, bot_id):
    """Тест выполнения с credentials без payload (обратная совместимость)."""
    mock_place_details = {
        "result": {
            "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
            "name": "Eiffel Tower",
            "photos": [
                {
                    "photo_reference": "photo_ref_1",
                    "width": 4000,
                    "height": 3000,
                    "html_attributions": []
                }
            ]
        }
    }
    
    with patch('app.integrations.google_maps.get_place_photos.googlemaps') as mock_googlemaps:
        mock_client = MagicMock()
        mock_client.place = Mock(return_value=mock_place_details)
        mock_googlemaps.Client.return_value = mock_client
        
        result = await integration.execute(
            config={
                "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4"
            },
            credentials_resolver=credentials_resolver_no_payload,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        mock_googlemaps.Client.assert_called_once_with(key="test-api-key-12345")


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_missing_place_id_and_query(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения без place_id и query."""
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "place_id" in result["response"]["description"].lower() or "query" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_max_photos_too_small(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с max_photos < 1."""
    result = await integration.execute(
        config={
            "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
            "max_photos": 0
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "max_photos" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_max_width_out_of_range(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с max_width вне допустимого диапазона."""
    result = await integration.execute(
        config={
            "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
            "max_width": 2000  # Больше 1600
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "max_width" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_max_height_out_of_range(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с max_height вне допустимого диапазона."""
    result = await integration.execute(
        config={
            "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
            "max_height": 2000  # Больше 1600
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "max_height" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_place_not_found_by_query(integration, credentials_resolver, logger, bot_id):
    """Тест обработки случая, когда место не найдено по query."""
    mock_find_place_result = {
        "candidates": []
    }
    
    with patch('app.integrations.google_maps.get_place_photos.googlemaps') as mock_googlemaps:
        mock_client = MagicMock()
        mock_client.find_place = Mock(return_value=mock_find_place_result)
        mock_googlemaps.Client.return_value = mock_client
        
        result = await integration.execute(
            config={
                "query": "Nonexistent Place 12345"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 404
        assert "not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_place_details_not_found(integration, credentials_resolver, logger, bot_id):
    """Тест обработки случая, когда детали места не найдены."""
    mock_place_details = {}  # Нет ключа "result"
    
    with patch('app.integrations.google_maps.get_place_photos.googlemaps') as mock_googlemaps:
        mock_client = MagicMock()
        mock_client.place = Mock(return_value=mock_place_details)
        mock_googlemaps.Client.return_value = mock_client
        
        result = await integration.execute(
            config={
                "place_id": "INVALID_PLACE_ID"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 404
        assert "not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_no_photos_available(integration, credentials_resolver, logger, bot_id):
    """Тест обработки случая, когда у места нет фотографий."""
    mock_place_details = {
        "result": {
            "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
            "name": "Eiffel Tower",
            "photos": []  # Нет фотографий
        }
    }
    
    with patch('app.integrations.google_maps.get_place_photos.googlemaps') as mock_googlemaps:
        mock_client = MagicMock()
        mock_client.place = Mock(return_value=mock_place_details)
        mock_googlemaps.Client.return_value = mock_client
        
        result = await integration.execute(
            config={
                "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 404
        assert "no photos" in result["response"]["description"].lower() or "photos" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_no_valid_photo_references(integration, credentials_resolver, logger, bot_id):
    """Тест обработки случая, когда у фотографий нет photo_reference."""
    mock_place_details = {
        "result": {
            "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
            "name": "Eiffel Tower",
            "photos": [
                {
                    "width": 4000,
                    "height": 3000,
                    "html_attributions": []
                    # Нет photo_reference
                }
            ]
        }
    }
    
    with patch('app.integrations.google_maps.get_place_photos.googlemaps') as mock_googlemaps:
        mock_client = MagicMock()
        mock_client.place = Mock(return_value=mock_place_details)
        mock_googlemaps.Client.return_value = mock_client
        
        result = await integration.execute(
            config={
                "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "no valid photos" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_api_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибки API."""
    with patch('app.integrations.google_maps.get_place_photos.googlemaps') as mock_googlemaps:
        mock_client = MagicMock()
        # Создаем mock ошибку с атрибутом status
        mock_error = Exception("API Error: Invalid API key")
        mock_error.status = 403
        mock_client.place = Mock(side_effect=mock_error)
        mock_googlemaps.Client.return_value = mock_client
        
        with patch('app.integrations.google_maps.get_place_photos.ApiError', Exception):
            result = await integration.execute(
                config={
                    "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4"
                },
                credentials_resolver=credentials_resolver,
                bot_id=bot_id,
                logger=logger
            )
            
            assert result["response"]["ok"] is False
            # Код ошибки должен быть из статуса ошибки или 500 по умолчанию
            assert result["response"]["error_code"] in [400, 403, 500]


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_http_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки HTTP ошибки."""
    with patch('app.integrations.google_maps.get_place_photos.googlemaps') as mock_googlemaps:
        mock_client = MagicMock()
        mock_error = Exception("HTTP Error: Connection failed")
        mock_client.place = Mock(side_effect=mock_error)
        mock_googlemaps.Client.return_value = mock_client
        
        with patch('app.integrations.google_maps.get_place_photos.HTTPError', Exception):
            result = await integration.execute(
                config={
                    "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4"
                },
                credentials_resolver=credentials_resolver,
                bot_id=bot_id,
                logger=logger
            )
            
            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 500
            assert "error" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_timeout_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибки таймаута."""
    with patch('app.integrations.google_maps.get_place_photos.googlemaps') as mock_googlemaps:
        mock_client = MagicMock()
        mock_error = Exception("Request timeout")
        mock_client.place = Mock(side_effect=mock_error)
        mock_googlemaps.Client.return_value = mock_client
        
        with patch('app.integrations.google_maps.get_place_photos.Timeout', Exception):
            result = await integration.execute(
                config={
                    "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4"
                },
                credentials_resolver=credentials_resolver,
                bot_id=bot_id,
                logger=logger
            )
            
            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 504
            assert "timeout" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_library_not_available(integration, logger, bot_id):
    """Тест выполнения когда библиотека не установлена."""
    with patch('app.integrations.google_maps.get_place_photos.GOOGLEMAPS_AVAILABLE', False):
        # Пересоздаем интеграцию, чтобы флаг применился
        integration = GoogleMapsGetPlacePhotosIntegration()
        
        credentials_resolver = MagicMock(spec=CredentialsResolver)
        credentials_resolver.get_default_for = AsyncMock(return_value={
            "payload": {"api_key": "test-key"}
        })
        
        result = await integration.execute(
            config={
                "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "not installed" in result["response"]["description"].lower() or "not available" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_value_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ValueError (неверные параметры)."""
    with patch('app.integrations.google_maps.get_place_photos.googlemaps') as mock_googlemaps:
        mock_client = MagicMock()
        mock_client.place = Mock(side_effect=ValueError("Invalid place_id"))
        mock_googlemaps.Client.return_value = mock_client
        
        result = await integration.execute(
            config={
                "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "invalid" in result["response"]["description"].lower() or "parameter" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_google_maps_place_photos_execute_unexpected_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки неожиданной ошибки."""
    with patch('app.integrations.google_maps.get_place_photos.googlemaps') as mock_googlemaps:
        mock_client = MagicMock()
        mock_client.place = Mock(side_effect=RuntimeError("Unexpected error"))
        mock_googlemaps.Client.return_value = mock_client
        
        result = await integration.execute(
            config={
                "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "error" in result["response"]["description"].lower()

