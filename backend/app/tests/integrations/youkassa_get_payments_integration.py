"""Тесты для YouKassa Get Payments интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.yookassa.get_payments import YoukassaGetPaymentsIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return YoukassaGetPaymentsIntegration()


@pytest.fixture
def logger():
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def creds_with_keys():
    return {
        "payload": {
            "account_id": "acct_123",
            "secret_key": "sk_test_456"
        }
    }


@pytest.fixture
def creds_with_oauth():
    return {"payload": {"oauth_token": "oauth_abc"}}


@pytest.mark.asyncio
async def test_metadata(integration):
    meta = integration.metadata
    assert meta.id == "youkassa_get_payments"
    assert meta.version == "1.0.0"
    assert meta.category == "payments"
    assert meta.credentials_provider == "youkassa"
    assert meta.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_execute_no_credentials(integration, logger, bot_id):
    creds_resolver = MagicMock(spec=CredentialsResolver)
    creds_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute({}, creds_resolver, bot_id, logger)

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_execute_missing_fields_in_credentials(integration, logger, bot_id):
    creds_resolver = MagicMock(spec=CredentialsResolver)
    creds_resolver.get_default_for = AsyncMock(return_value={})

    result = await integration.execute({}, creds_resolver, bot_id, logger)

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_execute_configures_with_keys_and_returns_items(integration, logger, bot_id, creds_with_keys):
    creds_resolver = MagicMock(spec=CredentialsResolver)
    creds_resolver.get_default_for = AsyncMock(return_value=creds_with_keys)

    # Создаём fake ответ от SDK
    class FakeItem:
        def to_dict(self):
            return {"id": "pay_1", "amount": {"value": "100.00"}}

    class FakeResp:
        def __init__(self):
            self.items = [FakeItem()]
            self.next_cursor = "next123"

    fake_resp = FakeResp()

    with patch("app.integrations.yookassa.get_payments.Configuration") as mock_conf:
        with patch("app.integrations.yookassa.get_payments.Payment") as mock_payment:
            mock_payment.list.return_value = fake_resp

            result = await integration.execute({"limit": 1}, creds_resolver, bot_id, logger)

            # Проверьте, что конфигурация SDK была применена
            mock_conf.configure.assert_called_once_with("acct_123", "sk_test_456")

            assert result["response"]["ok"] is True
            items = result["response"]["result"]["items"]
            assert isinstance(items, list)
            assert items[0]["id"] == "pay_1"
            assert result["response"]["result"]["next_cursor"] == "next123"


@pytest.mark.asyncio
async def test_execute_configures_with_oauth_token(integration, logger, bot_id, creds_with_oauth):
    creds_resolver = MagicMock(spec=CredentialsResolver)
    creds_resolver.get_default_for = AsyncMock(return_value=creds_with_oauth)

    with patch("app.integrations.yookassa.get_payments.Configuration") as mock_conf:
        with patch("app.integrations.yookassa.get_payments.Payment") as mock_payment:
            class FakeResp:
                items = []
                next_cursor = None

            mock_payment.list.return_value = FakeResp()

            result = await integration.execute({}, creds_resolver, bot_id, logger)

            mock_conf.configure_auth_token.assert_called_once_with("oauth_abc")
            assert result["response"]["ok"] is True


@pytest.mark.asyncio
async def test_execute_handles_sdk_api_error(integration, logger, bot_id, creds_with_keys):
    creds_resolver = MagicMock(spec=CredentialsResolver)
    creds_resolver.get_default_for = AsyncMock(return_value=creds_with_keys)

    # Создаём кастомную ошибку с http_code
    class FakeApiError(Exception):
        http_code = 400

    with patch("app.integrations.yookassa.get_payments.Configuration") as mock_conf:
        with patch("app.integrations.yookassa.get_payments.Payment") as mock_payment:
            mock_payment.list.side_effect = FakeApiError("bad")

            result = await integration.execute({}, creds_resolver, bot_id, logger)

            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_execute_library_not_available(integration, logger, bot_id, monkeypatch):
    # Симулируем отсутствие библиотеки
    monkeypatch.setattr("app.integrations.yookassa.get_payments.YOOKASSA_AVAILABLE", False)

    creds_resolver = MagicMock(spec=CredentialsResolver)
    creds_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute({}, creds_resolver, bot_id, logger)

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500
