"""Тесты для PayPal интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch, Mock

from app.integrations.paypal.get_payout import PayPalGetPayoutIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр PayPal интеграции."""
    return PayPalGetPayoutIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret"
        }
    })
    return resolver


@pytest.fixture
def credentials_resolver_without_payload():
    """Создает mock credentials resolver без payload (обратная совместимость)."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "clientId": "test_client_id",
        "clientSecret": "test_client_secret"
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


def test_paypal_metadata(integration):
    """Тест метаданных PayPal интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "paypal_get_payout"
    assert metadata.version == "1.0.0"
    assert metadata.name == "PayPal Get Payout"
    assert metadata.category == "payments"
    assert metadata.credentials_provider == "paypal"
    assert metadata.credentials_strategy == "oauth"
    assert metadata.icon_s3_key == "icons/integrations/paypal.svg"
    assert "payout_batch_id" in metadata.config_schema["required"]
    assert metadata.examples is not None
    assert len(metadata.examples) > 0


@pytest.mark.asyncio
async def test_paypal_execute_success(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения PayPal интеграции."""
    # Мокаем httpx
    mock_token_response = Mock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "test_access_token"}
    mock_token_response.raise_for_status = Mock()
    
    mock_payout_response = Mock()
    mock_payout_response.status_code = 200
    mock_payout_response.json.return_value = {
        "batch_header": {
            "payout_batch_id": "PAYOUT_BATCH_ID",
            "batch_status": "SUCCESS"
        },
        "items": [],
        "links": []
    }
    
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        # Настраиваем mock для httpx.AsyncClient
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        # Первый вызов - получение токена
        # Второй вызов - получение payout
        mock_client.post = AsyncMock(return_value=mock_token_response)
        mock_client.get = AsyncMock(return_value=mock_payout_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "payout_batch_id": "PAYOUT_BATCH_ID",
                "environment": "sandbox"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert "batch_header" in result["response"]["result"]
        assert result["response"]["result"]["batch_header"]["payout_batch_id"] == "PAYOUT_BATCH_ID"
        
        # Проверяем, что методы были вызваны
        assert mock_client.post.call_count == 1  # Получение токена
        assert mock_client.get.call_count == 1  # Получение payout


@pytest.mark.asyncio
async def test_paypal_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={"payout_batch_id": "PAYOUT_BATCH_ID"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "credentials not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_execute_missing_client_credentials(integration, logger, bot_id):
    """Тест выполнения с отсутствующими client_id или client_secret."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {}  # Пустой payload
    })
    
    result = await integration.execute(
        config={"payout_batch_id": "PAYOUT_BATCH_ID"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "client_id and client_secret" in result["response"]["description"]


@pytest.mark.asyncio
async def test_paypal_execute_missing_payout_batch_id(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующим payout_batch_id."""
    result = await integration.execute(
        config={},  # Отсутствует payout_batch_id
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "payout_batch_id is required" in result["response"]["description"]


@pytest.mark.asyncio
async def test_paypal_execute_oauth_token_error(integration, credentials_resolver, logger, bot_id):
    """Тест ошибки получения OAuth токена."""
    mock_token_response = Mock()
    mock_token_response.status_code = 401
    mock_token_response.text = "Invalid credentials"
    mock_token_response.raise_for_status.side_effect = Exception("401 Unauthorized")
    
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(side_effect=Exception("401 Unauthorized"))
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={
                "payout_batch_id": "PAYOUT_BATCH_ID",
                "environment": "sandbox"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 401
        assert "access token" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_execute_payout_not_found(integration, credentials_resolver, logger, bot_id):
    """Тест случая, когда payout не найден (404)."""
    mock_token_response = Mock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "test_access_token"}
    mock_token_response.raise_for_status = Mock()
    
    mock_payout_response = Mock()
    mock_payout_response.status_code = 404
    mock_payout_response.text = "Payout not found"
    
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_token_response)
        mock_client.get = AsyncMock(return_value=mock_payout_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={
                "payout_batch_id": "INVALID_BATCH_ID",
                "environment": "sandbox"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 404
        assert "not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_execute_api_error(integration, credentials_resolver, logger, bot_id):
    """Тест ошибки API PayPal (500)."""
    mock_token_response = Mock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "test_access_token"}
    mock_token_response.raise_for_status = Mock()
    
    mock_payout_response = Mock()
    mock_payout_response.status_code = 500
    mock_payout_response.text = "Internal Server Error"
    mock_payout_response.json.return_value = {"message": "Internal Server Error"}
    
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_token_response)
        mock_client.get = AsyncMock(return_value=mock_payout_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={
                "payout_batch_id": "PAYOUT_BATCH_ID",
                "environment": "sandbox"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500


@pytest.mark.asyncio
async def test_paypal_execute_timeout(integration, credentials_resolver, logger, bot_id):
    """Тест таймаута запроса."""
    mock_token_response = Mock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "test_access_token"}
    mock_token_response.raise_for_status = Mock()
    
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        from httpx import TimeoutException
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_token_response)
        mock_client.get = AsyncMock(side_effect=TimeoutException("Request timeout"))
        
        mock_httpx.AsyncClient.return_value = mock_client
        mock_httpx.TimeoutException = TimeoutException
        
        result = await integration.execute(
            config={
                "payout_batch_id": "PAYOUT_BATCH_ID",
                "environment": "sandbox"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 504
        assert "timeout" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_execute_production_environment(integration, credentials_resolver, logger, bot_id):
    """Тест использования production окружения."""
    mock_token_response = Mock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "test_access_token"}
    mock_token_response.raise_for_status = Mock()
    
    mock_payout_response = Mock()
    mock_payout_response.status_code = 200
    mock_payout_response.json.return_value = {
        "batch_header": {"payout_batch_id": "PAYOUT_BATCH_ID"},
        "items": [],
        "links": []
    }
    
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_token_response)
        mock_client.get = AsyncMock(return_value=mock_payout_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={
                "payout_batch_id": "PAYOUT_BATCH_ID",
                "environment": "production"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        # Проверяем, что использовался production URL
        # post должен быть вызван с production URL
        call_args = mock_client.post.call_args
        assert "api.paypal.com" in str(call_args) or "api.sandbox.paypal.com" not in str(call_args)


@pytest.mark.asyncio
async def test_paypal_execute_credentials_without_payload(integration, credentials_resolver_without_payload, logger, bot_id):
    """Тест с credentials без payload (обратная совместимость)."""
    mock_token_response = Mock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "test_access_token"}
    mock_token_response.raise_for_status = Mock()
    
    mock_payout_response = Mock()
    mock_payout_response.status_code = 200
    mock_payout_response.json.return_value = {
        "batch_header": {"payout_batch_id": "PAYOUT_BATCH_ID"},
        "items": [],
        "links": []
    }
    
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_token_response)
        mock_client.get = AsyncMock(return_value=mock_payout_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={
                "payout_batch_id": "PAYOUT_BATCH_ID",
                "environment": "sandbox"
            },
            credentials_resolver=credentials_resolver_without_payload,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True


@pytest.mark.asyncio
async def test_paypal_execute_httpx_not_available(integration, credentials_resolver, logger, bot_id):
    """Тест случая, когда httpx не установлен."""
    with patch('app.integrations.paypal.get_payout.HTTPX_AVAILABLE', False):
        result = await integration.execute(
            config={"payout_batch_id": "PAYOUT_BATCH_ID"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "httpx" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_get_access_token_success(integration, logger):
    """Тест успешного получения access token."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "test_token_12345"}
    mock_response.raise_for_status = Mock()
    mock_response.text = "OK"
    
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        token = await integration._get_access_token(
            client_id="test_client_id",
            client_secret="test_client_secret",
            environment="sandbox",
            logger=logger
        )
        
        assert token == "test_token_12345"
        mock_client.post.assert_called_once()
        # Проверяем, что использовался sandbox URL
        call_args = mock_client.post.call_args
        assert "api.sandbox.paypal.com" in str(call_args[0][0])


@pytest.mark.asyncio
async def test_paypal_get_access_token_production(integration, logger):
    """Тест получения access token для production окружения."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "prod_token"}
    mock_response.raise_for_status = Mock()
    
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        token = await integration._get_access_token(
            client_id="test_client_id",
            client_secret="test_client_secret",
            environment="production",
            logger=logger
        )
        
        assert token == "prod_token"
        # Проверяем, что использовался production URL
        call_args = mock_client.post.call_args
        assert "api.paypal.com" in str(call_args[0][0])
        assert "api.sandbox.paypal.com" not in str(call_args[0][0])


@pytest.mark.asyncio
async def test_paypal_get_access_token_http_error(integration, logger):
    """Тест ошибки HTTP при получении access token."""
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        from httpx import HTTPStatusError
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        # Создаем HTTPStatusError
        http_error = HTTPStatusError("Unauthorized", request=Mock(), response=mock_response)
        mock_client.post = AsyncMock(side_effect=http_error)
        
        mock_httpx.AsyncClient.return_value = mock_client
        mock_httpx.HTTPStatusError = HTTPStatusError
        
        token = await integration._get_access_token(
            client_id="test_client_id",
            client_secret="test_client_secret",
            environment="sandbox",
            logger=logger
        )
        
        assert token is None
        logger.error.assert_called()


@pytest.mark.asyncio
async def test_paypal_get_access_token_timeout(integration, logger):
    """Тест таймаута при получении access token."""
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        from httpx import TimeoutException
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(side_effect=TimeoutException("Timeout"))
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        token = await integration._get_access_token(
            client_id="test_client_id",
            client_secret="test_client_secret",
            environment="sandbox",
            logger=logger
        )
        
        assert token is None
        logger.error.assert_called()


@pytest.mark.asyncio
async def test_paypal_get_access_token_no_token_in_response(integration, logger):
    """Тест случая, когда в ответе нет access_token."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"error": "invalid_client"}  # Нет access_token
    mock_response.raise_for_status = Mock()
    
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        token = await integration._get_access_token(
            client_id="test_client_id",
            client_secret="test_client_secret",
            environment="sandbox",
            logger=logger
        )
        
        assert token is None


@pytest.mark.asyncio
async def test_paypal_execute_forbidden_error(integration, credentials_resolver, logger, bot_id):
    """Тест ошибки 403 Forbidden от PayPal API."""
    mock_token_response = Mock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "test_token"}
    mock_token_response.raise_for_status = Mock()
    
    mock_payout_response = Mock()
    mock_payout_response.status_code = 403
    mock_payout_response.text = "Forbidden"
    mock_payout_response.json.return_value = {"message": "Access denied"}
    
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_token_response)
        mock_client.get = AsyncMock(return_value=mock_payout_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={
                "payout_batch_id": "PAYOUT_BATCH_ID",
                "environment": "sandbox"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 403
        assert "Access denied" in result["response"]["description"]


@pytest.mark.asyncio
async def test_paypal_execute_rate_limit_error(integration, credentials_resolver, logger, bot_id):
    """Тест ошибки 429 Rate Limit от PayPal API."""
    mock_token_response = Mock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "test_token"}
    mock_token_response.raise_for_status = Mock()
    
    mock_payout_response = Mock()
    mock_payout_response.status_code = 429
    mock_payout_response.text = "Too Many Requests"
    
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_token_response)
        mock_client.get = AsyncMock(return_value=mock_payout_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={
                "payout_batch_id": "PAYOUT_BATCH_ID",
                "environment": "sandbox"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 429


@pytest.mark.asyncio
async def test_paypal_execute_invalid_json_response(integration, credentials_resolver, logger, bot_id):
    """Тест случая, когда PayPal API возвращает некорректный JSON."""
    mock_token_response = Mock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "test_token"}
    mock_token_response.raise_for_status = Mock()
    
    mock_payout_response = Mock()
    mock_payout_response.status_code = 200
    mock_payout_response.text = "Not a JSON"
    mock_payout_response.json.side_effect = ValueError("Invalid JSON")
    
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_token_response)
        mock_client.get = AsyncMock(return_value=mock_payout_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={
                "payout_batch_id": "PAYOUT_BATCH_ID",
                "environment": "sandbox"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Должна быть ошибка, так как JSON некорректный
        assert result["response"]["ok"] is False


@pytest.mark.asyncio
async def test_paypal_execute_empty_payout_response(integration, credentials_resolver, logger, bot_id):
    """Тест случая, когда PayPal API возвращает пустой ответ."""
    mock_token_response = Mock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "test_token"}
    mock_token_response.raise_for_status = Mock()
    
    mock_payout_response = Mock()
    mock_payout_response.status_code = 200
    mock_payout_response.json.return_value = {}  # Пустой ответ
    
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_token_response)
        mock_client.get = AsyncMock(return_value=mock_payout_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={
                "payout_batch_id": "PAYOUT_BATCH_ID",
                "environment": "sandbox"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Должен вернуться успешный ответ с пустыми данными
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["batch_header"] == {}
        assert result["response"]["result"]["items"] == []
        assert result["response"]["result"]["links"] == []


@pytest.mark.asyncio
async def test_paypal_execute_request_error_on_token(integration, credentials_resolver, logger, bot_id):
    """Тест RequestError при получении токена."""
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        from httpx import RequestError
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(side_effect=RequestError("Network error"))
        
        mock_httpx.AsyncClient.return_value = mock_client
        mock_httpx.RequestError = RequestError
        
        result = await integration.execute(
            config={
                "payout_batch_id": "PAYOUT_BATCH_ID",
                "environment": "sandbox"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 401
        assert "access token" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_execute_request_error_on_payout(integration, credentials_resolver, logger, bot_id):
    """Тест RequestError при получении payout."""
    mock_token_response = Mock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "test_token"}
    mock_token_response.raise_for_status = Mock()
    
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        from httpx import RequestError
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_token_response)
        mock_client.get = AsyncMock(side_effect=RequestError("Network error"))
        
        mock_httpx.AsyncClient.return_value = mock_client
        mock_httpx.RequestError = RequestError
        
        result = await integration.execute(
            config={
                "payout_batch_id": "PAYOUT_BATCH_ID",
                "environment": "sandbox"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "request error" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_execute_timeout_on_token(integration, credentials_resolver, logger, bot_id):
    """Тест TimeoutException при получении токена."""
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        from httpx import TimeoutException
        
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(side_effect=TimeoutException("Timeout"))
        
        mock_httpx.AsyncClient.return_value = mock_client
        mock_httpx.TimeoutException = TimeoutException
        
        result = await integration.execute(
            config={
                "payout_batch_id": "PAYOUT_BATCH_ID",
                "environment": "sandbox"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 401
        assert "access token" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_execute_default_environment(integration, credentials_resolver, logger, bot_id):
    """Тест использования окружения по умолчанию (sandbox)."""
    mock_token_response = Mock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "test_token"}
    mock_token_response.raise_for_status = Mock()
    
    mock_payout_response = Mock()
    mock_payout_response.status_code = 200
    mock_payout_response.json.return_value = {
        "batch_header": {"payout_batch_id": "PAYOUT_BATCH_ID"},
        "items": [],
        "links": []
    }
    
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_token_response)
        mock_client.get = AsyncMock(return_value=mock_payout_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        # Не указываем environment, должен использоваться sandbox по умолчанию
        result = await integration.execute(
            config={
                "payout_batch_id": "PAYOUT_BATCH_ID"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        # Проверяем, что использовался sandbox URL
        token_call_args = mock_client.post.call_args
        payout_call_args = mock_client.get.call_args
        assert "api.sandbox.paypal.com" in str(token_call_args[0][0])
        assert "api.sandbox.paypal.com" in str(payout_call_args[0][0])


@pytest.mark.asyncio
async def test_paypal_execute_full_payout_data(integration, credentials_resolver, logger, bot_id):
    """Тест с полными данными payout (batch_header, items, links)."""
    mock_token_response = Mock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "test_token"}
    mock_token_response.raise_for_status = Mock()
    
    mock_payout_response = Mock()
    mock_payout_response.status_code = 200
    mock_payout_response.json.return_value = {
        "batch_header": {
            "payout_batch_id": "PAYOUT_BATCH_ID",
            "batch_status": "SUCCESS",
            "sender_batch_header": {
                "sender_batch_id": "SENDER_BATCH_ID",
                "email_subject": "Payment"
            }
        },
        "items": [
            {
                "payout_item_id": "ITEM_1",
                "transaction_status": "SUCCESS",
                "payout_item_fee": "0.00"
            }
        ],
        "links": [
            {
                "href": "https://api.sandbox.paypal.com/v1/payments/payouts/PAYOUT_BATCH_ID",
                "rel": "self",
                "method": "GET"
            }
        ]
    }
    
    with patch('app.integrations.paypal.get_payout.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_token_response)
        mock_client.get = AsyncMock(return_value=mock_payout_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await integration.execute(
            config={
                "payout_batch_id": "PAYOUT_BATCH_ID",
                "environment": "sandbox"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["batch_header"]["payout_batch_id"] == "PAYOUT_BATCH_ID"
        assert result["response"]["result"]["batch_header"]["batch_status"] == "SUCCESS"
        assert len(result["response"]["result"]["items"]) == 1
        assert len(result["response"]["result"]["links"]) == 1
