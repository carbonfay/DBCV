"""Тесты для Ozon Get Product List интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from app.integrations.ozon.get_product_list import OzonGetProductListIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр Ozon интеграции."""
    return OzonGetProductListIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "client_id": "test_client_id",
            "api_key": "test_api_key"
        }
    })
    return resolver


@pytest.fixture
def credentials_resolver_without_payload():
    """Создает mock credentials resolver без payload."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "clientId": "test_client_id",
        "apiKey": "test_api_key"
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


def test_ozon_metadata(integration):
    """Тест метаданных Ozon интеграции."""
    metadata = integration.metadata
    assert metadata.id == "ozon_get_product_list"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Ozon Get Product List"
    assert metadata.category == "ecommerce"
    assert metadata.credentials_provider == "ozon"
    assert metadata.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_ozon_execute_success(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения Ozon интеграции."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": {"items": []}, "total": 0}

    with patch('app.integrations.ozon.get_product_list.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_httpx.AsyncClient.return_value = mock_client

        result = await integration.execute(
            config={"limit": 10, "visibility": "ALL"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is True
        assert result["response"]["result"]["total"] == 0
        mock_client.post.assert_called_once()

        call_kwargs = mock_client.post.call_args.kwargs
        assert "/v2/product/list" in call_kwargs["url"]
        assert call_kwargs["headers"]["Client-Id"] == "test_client_id"
        assert call_kwargs["headers"]["Api-Key"] == "test_api_key"
        assert call_kwargs["json"]["limit"] == 10


@pytest.mark.asyncio
async def test_ozon_execute_filter_normalization(integration, credentials_resolver, logger, bot_id):
    """Тест нормализации фильтров offer_id и product_id."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": {"items": []}, "total": 0}

    with patch('app.integrations.ozon.get_product_list.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_httpx.AsyncClient.return_value = mock_client

        result = await integration.execute(
            config={"offer_id": "SKU-1", "product_id": 123},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is True
        call_kwargs = mock_client.post.call_args.kwargs
        assert call_kwargs["json"]["filter"]["offer_id"] == ["SKU-1"]
        assert call_kwargs["json"]["filter"]["product_id"] == [123]


@pytest.mark.asyncio
async def test_ozon_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"limit": 10},
        credentials_resolver=resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_ozon_execute_missing_credentials_fields(integration, logger, bot_id):
    """Тест отсутствия client_id или api_key."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={"payload": {}})

    result = await integration.execute(
        config={"limit": 10},
        credentials_resolver=resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_ozon_execute_credentials_without_payload(
    integration, credentials_resolver_without_payload, logger, bot_id
):
    """Тест credentials без payload (обратная совместимость)."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": {"items": []}, "total": 0}

    with patch('app.integrations.ozon.get_product_list.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_httpx.AsyncClient.return_value = mock_client

        result = await integration.execute(
            config={},
            credentials_resolver=credentials_resolver_without_payload,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is True


@pytest.mark.asyncio
async def test_ozon_execute_invalid_limit(integration, credentials_resolver, logger, bot_id):
    """Тест некорректного лимита."""
    result = await integration.execute(
        config={"limit": 2000},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_ozon_execute_api_error(integration, credentials_resolver, logger, bot_id):
    """Тест ошибки Ozon API."""
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden"
    mock_response.json.return_value = {"message": "Forbidden"}

    with patch('app.integrations.ozon.get_product_list.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_httpx.AsyncClient.return_value = mock_client

        result = await integration.execute(
            config={},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 403


@pytest.mark.asyncio
async def test_ozon_execute_invalid_json(integration, credentials_resolver, logger, bot_id):
    """Тест некорректного JSON ответа."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")

    with patch('app.integrations.ozon.get_product_list.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_httpx.AsyncClient.return_value = mock_client

        result = await integration.execute(
            config={},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500


@pytest.mark.asyncio
async def test_ozon_execute_timeout(integration, credentials_resolver, logger, bot_id):
    """Тест таймаута запроса."""
    from httpx import TimeoutException

    with patch('app.integrations.ozon.get_product_list.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(side_effect=TimeoutException("Timeout"))
        mock_httpx.AsyncClient.return_value = mock_client
        mock_httpx.TimeoutException = TimeoutException

        result = await integration.execute(
            config={},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 504


@pytest.mark.asyncio
async def test_ozon_execute_request_error(integration, credentials_resolver, logger, bot_id):
    """Тест сетевой ошибки запроса."""
    from httpx import RequestError

    with patch('app.integrations.ozon.get_product_list.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(side_effect=RequestError("Network error"))
        mock_httpx.AsyncClient.return_value = mock_client
        mock_httpx.RequestError = RequestError

        result = await integration.execute(
            config={},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500


@pytest.mark.asyncio
async def test_ozon_execute_httpx_not_available(integration, credentials_resolver, logger, bot_id):
    """Тест случая, когда httpx не установлен."""
    with patch('app.integrations.ozon.get_product_list.HTTPX_AVAILABLE', False):
        result = await integration.execute(
            config={},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
