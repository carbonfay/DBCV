"""Tests for PayPal Create Subscription integration."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.paypal.create_subscription import PaypalCreateSubscriptionIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger
import app.integrations.paypal.create_subscription as paypal_module


class DummyResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self):
        return self._json_data


def _make_async_client(post_side_effect):
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=post_side_effect)
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_client
    mock_cm.__aexit__.return_value = AsyncMock(return_value=None)
    return mock_cm, mock_client


@pytest.fixture
def integration():
    return PaypalCreateSubscriptionIntegration()


@pytest.fixture
def credentials_resolver():
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "client_id": "client-id",
            "client_secret": "client-secret",
            "mode": "sandbox"
        }
    })
    return resolver


@pytest.fixture
def logger():
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")


@pytest.mark.asyncio
async def test_paypal_create_subscription_success(
    integration,
    credentials_resolver,
    logger,
    bot_id
):
    token_response = DummyResponse(200, {"access_token": "token"})
    subscription_response = DummyResponse(201, {"id": "I-123", "status": "ACTIVE"})
    mock_cm, mock_client = _make_async_client([token_response, subscription_response])

    with patch.object(paypal_module, "HTTPX_AVAILABLE", True), \
         patch.object(paypal_module.httpx, "AsyncClient", return_value=mock_cm):
        result = await integration.execute(
            config={
                "plan_id": "P-123",
                "subscriber": {"email_address": "customer@example.com"},
                "application_context": {
                    "return_url": "https://example.com/success",
                    "cancel_url": "https://example.com/cancel"
                }
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["id"] == "I-123"

    token_call = mock_client.post.call_args_list[0]
    assert token_call.args[0] == f"{paypal_module.PAYPAL_SANDBOX_API_BASE}/v1/oauth2/token"
    subscription_call = mock_client.post.call_args_list[1]
    assert subscription_call.args[0] == f"{paypal_module.PAYPAL_SANDBOX_API_BASE}/v1/billing/subscriptions"


@pytest.mark.asyncio
async def test_paypal_create_subscription_no_credentials(
    integration,
    logger,
    bot_id
):
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=None)

    with patch.object(paypal_module, "HTTPX_AVAILABLE", True):
        result = await integration.execute(
            config={"plan_id": "P-456"},
            credentials_resolver=resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error"]["type"] == "credentials_missing"


@pytest.mark.asyncio
async def test_paypal_create_subscription_incomplete_credentials(
    integration,
    logger,
    bot_id
):
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "client_id": "client-id"
        }
    })

    with patch.object(paypal_module, "HTTPX_AVAILABLE", True):
        result = await integration.execute(
            config={"plan_id": "P-457"},
            credentials_resolver=resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error"]["type"] == "credentials_missing"


@pytest.mark.asyncio
async def test_paypal_create_subscription_token_auth_error(
    integration,
    credentials_resolver,
    logger,
    bot_id
):
    token_response = DummyResponse(401, {"error": "invalid_client"})
    mock_cm, _ = _make_async_client([token_response])

    with patch.object(paypal_module, "HTTPX_AVAILABLE", True), \
         patch.object(paypal_module.httpx, "AsyncClient", return_value=mock_cm):
        result = await integration.execute(
            config={"plan_id": "P-789"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error"]["type"] == "auth_error"
    assert result["response"]["error"]["status_code"] == 401


@pytest.mark.asyncio
async def test_paypal_create_subscription_api_error(
    integration,
    credentials_resolver,
    logger,
    bot_id
):
    token_response = DummyResponse(200, {"access_token": "token"})
    subscription_response = DummyResponse(422, {"name": "INVALID_REQUEST"})
    mock_cm, _ = _make_async_client([token_response, subscription_response])

    with patch.object(paypal_module, "HTTPX_AVAILABLE", True), \
         patch.object(paypal_module.httpx, "AsyncClient", return_value=mock_cm):
        result = await integration.execute(
            config={"plan_id": "P-900"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error"]["type"] == "api_error"
    assert result["response"]["error"]["status_code"] == 422


@pytest.mark.asyncio
async def test_paypal_create_subscription_network_error(
    integration,
    credentials_resolver,
    logger,
    bot_id
):
    class FakeRequestError(Exception):
        pass

    mock_cm, mock_client = _make_async_client([])
    mock_client.post.side_effect = FakeRequestError("timeout")

    with patch.object(paypal_module, "HTTPX_AVAILABLE", True), \
         patch.object(paypal_module.httpx, "RequestError", FakeRequestError), \
         patch.object(paypal_module.httpx, "AsyncClient", return_value=mock_cm):
        result = await integration.execute(
            config={"plan_id": "P-901"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error"]["type"] == "network_error"
