"""Тесты для YouKassa Get Payment (by id) интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.yookassa.get_payment import YoukassaGetPaymentIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return YoukassaGetPaymentIntegration()


@pytest.fixture
def logger():
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def creds_with_keys():
    return {"payload": {"account_id": "acct_123", "secret_key": "sk_test_456"}}


@pytest.fixture
def creds_with_oauth():
    return {"payload": {"oauth_token": "oauth_abc"}}


@pytest.mark.asyncio
async def test_metadata(integration):
    meta = integration.metadata
    assert meta.id == "youkassa_get_payment"
    assert meta.version == "1.0.0"
    assert meta.category == "payments"
    assert meta.credentials_provider == "youkassa"
    assert meta.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_execute_no_credentials(integration, logger, bot_id):
    creds_resolver = MagicMock(spec=CredentialsResolver)
    creds_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute({"payment_id": "id123"}, creds_resolver, bot_id, logger)

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_execute_missing_payment_id(integration, logger, bot_id):
    creds_resolver = MagicMock(spec=CredentialsResolver)
    creds_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute({}, creds_resolver, bot_id, logger)

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_execute_configures_with_keys_and_returns_payment(integration, logger, bot_id, creds_with_keys):
    creds_resolver = MagicMock(spec=CredentialsResolver)
    creds_resolver.get_default_for = AsyncMock(return_value=creds_with_keys)

    class FakePayment:
        def to_dict(self):
            return {"id": "pay_1", "status": "succeeded"}

    with patch("app.integrations.yookassa.get_payment.Configuration") as mock_conf:
        with patch("app.integrations.yookassa.get_payment.Payment") as mock_payment:
            mock_payment.find_one.return_value = FakePayment()

            result = await integration.execute({"payment_id": "pay_1"}, creds_resolver, bot_id, logger)

            mock_conf.configure.assert_called_once_with("acct_123", "sk_test_456")
            assert result["response"]["ok"] is True
            assert result["response"]["result"]["id"] == "pay_1"


@pytest.mark.asyncio
async def test_execute_with_fixture_detail(integration, logger, bot_id, creds_with_keys):
    """Использование фикстуры JSON для проверки получения платежа по ID"""
    creds_resolver = MagicMock(spec=CredentialsResolver)
    creds_resolver.get_default_for = AsyncMock(return_value=creds_with_keys)

    import json
    from pathlib import Path

    fixture_path = Path(__file__).parent.parent / "fixtures" / "youkassa" / "payment_detail.json"
    data = json.loads(fixture_path.read_text())

    class FakePaymentFromJson:
        def __init__(self, payload):
            self._payload = payload

        def to_dict(self):
            return self._payload

    with patch("app.integrations.yookassa.get_payment.Configuration") as mock_conf:
        with patch("app.integrations.yookassa.get_payment.Payment") as mock_payment:
            mock_payment.find_one.return_value = FakePaymentFromJson(data)

            result = await integration.execute({"payment_id": "pay_1"}, creds_resolver, bot_id, logger)

            assert result["response"]["ok"] is True
            assert result["response"]["result"]["status"] == "succeeded"


@pytest.mark.asyncio
async def test_execute_configures_with_oauth_token(integration, logger, bot_id, creds_with_oauth):
    creds_resolver = MagicMock(spec=CredentialsResolver)
    creds_resolver.get_default_for = AsyncMock(return_value=creds_with_oauth)

    with patch("app.integrations.yookassa.get_payment.Configuration") as mock_conf:
        with patch("app.integrations.yookassa.get_payment.Payment") as mock_payment:
            class FakePayment:
                def to_dict(self):
                    return {}

            mock_payment.find_one.return_value = FakePayment()

            result = await integration.execute({"payment_id": "pay_1"}, creds_resolver, bot_id, logger)

            mock_conf.configure_auth_token.assert_called_once_with("oauth_abc")
            assert result["response"]["ok"] is True


@pytest.mark.asyncio
async def test_execute_handles_sdk_api_error(integration, logger, bot_id, creds_with_keys):
    creds_resolver = MagicMock(spec=CredentialsResolver)
    creds_resolver.get_default_for = AsyncMock(return_value=creds_with_keys)

    class FakeApiError(Exception):
        http_code = 404

    with patch("app.integrations.yookassa.get_payment.Configuration") as mock_conf:
        with patch("app.integrations.yookassa.get_payment.Payment") as mock_payment:
            mock_payment.find_one.side_effect = FakeApiError("not found")

            result = await integration.execute({"payment_id": "pay_1"}, creds_resolver, bot_id, logger)

            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 404


@pytest.mark.asyncio
async def test_execute_library_not_available(integration, logger, bot_id, monkeypatch):
    monkeypatch.setattr("app.integrations.yookassa.get_payment.YOOKASSA_AVAILABLE", False)

    creds_resolver = MagicMock(spec=CredentialsResolver)
    creds_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute({"payment_id": "pay_1"}, creds_resolver, bot_id, logger)

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500
