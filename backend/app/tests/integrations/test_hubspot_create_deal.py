"""Тесты для HubSpot Create Deal интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.integrations.hubspot.create_deal import HubSpotCreateDealIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр HubSpot интеграции."""
    return HubSpotCreateDealIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {"api_key": "test-hubspot-api-key-12345"}
    })
    resolver.get_single_for = AsyncMock(return_value=None)
    return resolver


@pytest.fixture
def logger():
    """Создает mock logger."""
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    """Создает test bot ID."""
    return UUID("12345678-1234-5678-1234-567812345678")


def test_hubspot_metadata(integration):
    """Тест метаданных HubSpot интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "hubspot_create_deal"
    assert metadata.version == "1.0.0"
    assert metadata.name == "HubSpot Create Deal"
    assert metadata.category == "crm"
    assert metadata.credentials_provider == "hubspot"
    assert metadata.credentials_strategy == "api_key"
    assert metadata.library_name == "hubspot-api-client>=7.0.0" or metadata.library_name is None


@pytest.mark.asyncio
async def test_hubspot_execute_success(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения HubSpot интеграции."""
    with patch('app.integrations.hubspot.create_deal.HubSpot') as mock_hubspot_class:
        # Настраиваем mock
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.id = "deal_123"
        mock_result.properties = {
            "dealname": "Test Deal",
            "amount": "10000",
            "dealstage": "appointmentscheduled"
        }
        mock_result.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_result.updated_at = datetime(2024, 1, 1, 12, 0, 0)
        
        mock_basic_api = MagicMock()
        # HubSpot API может быть синхронным, используем MagicMock вместо AsyncMock
        mock_basic_api.create = MagicMock(return_value=mock_result)
        mock_client.crm.deals.basic_api = mock_basic_api
        
        mock_hubspot_class.return_value = mock_client
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "properties": {
                    "dealname": "Test Deal",
                    "amount": "10000",
                    "dealstage": "appointmentscheduled"
                }
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == "deal_123"
        assert result["response"]["result"]["properties"]["dealname"] == "Test Deal"
        
        # Проверяем, что метод библиотеки был вызван
        mock_basic_api.create.assert_called_once()
        mock_hubspot_class.assert_called_once_with(access_token="test-hubspot-api-key-12345")


@pytest.mark.asyncio
async def test_hubspot_execute_with_associations(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения HubSpot интеграции с associations."""
    with patch('app.integrations.hubspot.create_deal.HubSpot') as mock_hubspot_class:
        # Настраиваем mock
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.id = "deal_456"
        mock_result.properties = {"dealname": "Deal with Associations"}
        mock_result.created_at = None
        mock_result.updated_at = None
        
        mock_basic_api = MagicMock()
        # HubSpot API может быть синхронным, используем MagicMock вместо AsyncMock
        mock_basic_api.create = MagicMock(return_value=mock_result)
        mock_client.crm.deals.basic_api = mock_basic_api
        
        mock_hubspot_class.return_value = mock_client
        
        # Выполняем интеграцию с associations
        result = await integration.execute(
            config={
                "properties": {
                    "dealname": "Deal with Associations"
                },
                "associations": [
                    {
                        "to": {"id": "contact_123"},
                        "types": [
                            {
                                "associationCategory": "HUBSPOT_DEFINED",
                                "associationTypeId": 3
                            }
                        ]
                    }
                ]
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == "deal_456"
        
        # Проверяем, что метод библиотеки был вызван
        mock_basic_api.create.assert_called_once()


@pytest.mark.asyncio
async def test_hubspot_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    credentials_resolver.get_single_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={
            "properties": {
                "dealname": "Test Deal"
            }
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_hubspot_execute_missing_api_key(integration, logger, bot_id):
    """Тест выполнения с отсутствующим API ключом в credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {}  # Нет api_key
    })
    credentials_resolver.get_single_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={
            "properties": {
                "dealname": "Test Deal"
            }
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_hubspot_execute_missing_properties(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующими properties."""
    result = await integration.execute(
        config={},  # Отсутствуют properties
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_hubspot_execute_api_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибки API HubSpot."""
    with patch('app.integrations.hubspot.create_deal.HubSpot') as mock_hubspot_class:
        # Настраиваем mock для выброса ошибки
        mock_client = MagicMock()
        mock_basic_api = MagicMock()
        
        # Создаем mock для ApiException
        api_exception = MagicMock()
        api_exception.status = 400
        api_exception.reason = "Bad Request"
        api_exception.body = '{"message": "Invalid properties"}'
        api_exception.__str__ = lambda self: "Bad Request: Invalid properties"
        
        mock_basic_api.create = MagicMock(side_effect=api_exception)
        mock_client.crm.deals.basic_api = mock_basic_api
        
        mock_hubspot_class.return_value = mock_client
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "properties": {
                    "dealname": "Test Deal"
                }
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем, что ошибка обработана
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_hubspot_execute_library_not_available(integration, logger, bot_id):
    """Тест выполнения когда библиотека не установлена."""
    # Временно заменяем HUBSPOT_AVAILABLE на False
    with patch('app.integrations.hubspot.create_deal.HUBSPOT_AVAILABLE', False):
        credentials_resolver = MagicMock(spec=CredentialsResolver)
        
        result = await integration.execute(
            config={
                "properties": {
                    "dealname": "Test Deal"
                }
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "not installed" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_hubspot_execute_backward_compatibility_credentials(integration, logger, bot_id):
    """Тест обратной совместимости с форматом credentials без payload."""
    with patch('app.integrations.hubspot.create_deal.HubSpot') as mock_hubspot_class:
        # Настраиваем mock
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.id = "deal_789"
        mock_result.properties = {"dealname": "Test Deal"}
        mock_result.created_at = None
        mock_result.updated_at = None
        
        mock_basic_api = MagicMock()
        # HubSpot API может быть синхронным, используем MagicMock вместо AsyncMock
        mock_basic_api.create = MagicMock(return_value=mock_result)
        mock_client.crm.deals.basic_api = mock_basic_api
        
        mock_hubspot_class.return_value = mock_client
        
        # Используем credentials без payload (старый формат)
        credentials_resolver = MagicMock(spec=CredentialsResolver)
        credentials_resolver.get_default_for = AsyncMock(return_value={
            "api_key": "old-format-api-key"
        })
        credentials_resolver.get_single_for = AsyncMock(return_value=None)
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "properties": {
                    "dealname": "Test Deal"
                }
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == "deal_789"
        
        # Проверяем, что использован старый формат ключа
        mock_hubspot_class.assert_called_once_with(access_token="old-format-api-key")

