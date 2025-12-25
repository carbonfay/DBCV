"""Tests for YouKassa Create Receipt integration."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.yookassa.create_receipt import YoukassaCreateReceiptIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return YoukassaCreateReceiptIntegration()


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
    assert meta.id == "youkassa_create_receipt"
    assert meta.version == "1.0.0"
    assert meta.category == "payments"


@pytest.mark.asyncio
async def test_execute_missing_credentials(integration, logger, bot_id):
    creds_resolver = MagicMock(spec=CredentialsResolver)
    creds_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute({"payment_id": "p1", "items": []}, creds_resolver, bot_id, logger)
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_execute_missing_fields(integration, logger, bot_id):
    creds_resolver = MagicMock(spec=CredentialsResolver)
    creds_resolver.get_default_for = AsyncMock(return_value={})

    result = await integration.execute({}, creds_resolver, bot_id, logger)
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_execute_creates_receipt_and_returns_result(integration, logger, bot_id, creds_with_keys):
    creds_resolver = MagicMock(spec=CredentialsResolver)
    creds_resolver.get_default_for = AsyncMock(return_value=creds_with_keys)

    class FakeReceipt:
        def to_dict(self):
            return {"id": "rt-1", "status": "created"}

    with patch("app.integrations.yookassa.create_receipt.Configuration") as mock_conf:
        with patch("app.integrations.yookassa.create_receipt.Receipt") as mock_receipt:
            mock_receipt.create.return_value = FakeReceipt()

            cfg = {"payment_id": "p1", "items": [{"description": "x", "amount": {"value": "100.00", "currency": "RUB"}}]}
            result = await integration.execute(cfg, creds_resolver, bot_id, logger)

            mock_conf.configure.assert_called_once_with("acct_123", "sk_test_456")
            assert result["response"]["ok"] is True
            assert result["response"]["result"]["id"] == "rt-1"


@pytest.mark.asyncio
async def test_execute_with_fixture_receipt(integration, logger, bot_id, creds_with_keys):
    """Использование фикстуры JSON для проверки создания чека"""
    creds_resolver = MagicMock(spec=CredentialsResolver)
    creds_resolver.get_default_for = AsyncMock(return_value=creds_with_keys)

    import json
    from pathlib import Path

    fixture_path = Path(__file__).parent.parent / "fixtures" / "youkassa" / "receipt_create.json"
    data = json.loads(fixture_path.read_text())

    class FakeReceiptFromJson:
        def __init__(self, payload):
            self._payload = payload

        def to_dict(self):
            return self._payload

    with patch("app.integrations.yookassa.create_receipt.Configuration") as mock_conf:
        with patch("app.integrations.yookassa.create_receipt.Receipt") as mock_receipt:
            mock_receipt.create.return_value = FakeReceiptFromJson(data)

            cfg = {"payment_id": "p1", "items": [{"description": "x"}]}
            result = await integration.execute(cfg, creds_resolver, bot_id, logger)

            assert result["response"]["ok"] is True
            assert result["response"]["result"]["id"] == "rt-1"


@pytest.mark.asyncio
async def test_execute_configures_with_oauth(integration, logger, bot_id, creds_with_oauth):
    creds_resolver = MagicMock(spec=CredentialsResolver)
    creds_resolver.get_default_for = AsyncMock(return_value=creds_with_oauth)

    with patch("app.integrations.yookassa.create_receipt.Configuration") as mock_conf:
        with patch("app.integrations.yookassa.create_receipt.Receipt") as mock_receipt:
            mock_receipt.create.return_value = MagicMock()

            cfg = {"payment_id": "p1", "items": [{"description": "x"}]}
            result = await integration.execute(cfg, creds_resolver, bot_id, logger)

            mock_conf.configure_auth_token.assert_called_once_with("oauth_abc")
            assert result["response"]["ok"] is True


@pytest.mark.asyncio
async def test_execute_handles_api_error(integration, logger, bot_id, creds_with_keys):
    creds_resolver = MagicMock(spec=CredentialsResolver)
    creds_resolver.get_default_for = AsyncMock(return_value=creds_with_keys)

    class FakeApiError(Exception):
        http_code = 400

    with patch("app.integrations.yookassa.create_receipt.Configuration") as mock_conf:
        with patch("app.integrations.yookassa.create_receipt.Receipt") as mock_receipt:
            mock_receipt.create.side_effect = FakeApiError("bad")

            cfg = {"payment_id": "p1", "items": [{"description": "x"}]}
            result = await integration.execute(cfg, creds_resolver, bot_id, logger)

            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_execute_library_not_available(integration, logger, bot_id, monkeypatch):
    monkeypatch.setattr("app.integrations.yookassa.create_receipt.YOOKASSA_AVAILABLE", False)

    creds_resolver = MagicMock(spec=CredentialsResolver)
    creds_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute({"payment_id": "p1", "items": []}, creds_resolver, bot_id, logger)
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500
