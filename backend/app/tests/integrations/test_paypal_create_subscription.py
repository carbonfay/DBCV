"""Tests for PayPal Create Subscription integration."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.paypal.create_subscription import PaypalCreateSubscriptionIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger
import app.integrations.paypal.create_subscription as paypal_module


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
    with patch.object(paypal_module, "PAYPAL_SDK_AVAILABLE", True), \
         patch.object(paypal_module, "paypalrestsdk") as mock_sdk, \
         patch.object(paypal_module, "BillingSubscription") as mock_subscription_class:
        mock_api = MagicMock()
        mock_sdk.Api.return_value = mock_api

        mock_subscription = MagicMock()
        mock_subscription.create.return_value = True
        mock_subscription.to_dict.return_value = {
            "id": "I-123",
            "status": "ACTIVE"
        }
        mock_subscription_class.return_value = mock_subscription

        result = await integration.execute(
            config={
                "plan_id": "P-123",
                "subscriber": {
                    "email_address": "customer@example.com"
                },
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

        call_args = mock_subscription_class.call_args
        payload = call_args.args[0]
        assert payload["plan_id"] == "P-123"
        assert payload["subscriber"]["email_address"] == "customer@example.com"
        assert call_args.kwargs["api"] == mock_api

        mock_sdk.Api.assert_called_once()


@pytest.mark.asyncio
async def test_paypal_create_subscription_env_fallback(
    integration,
    logger,
    bot_id,
    monkeypatch
):
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=None)

    monkeypatch.setattr(paypal_module, "PAYPAL_CLIENT_ID", "env-client-id")
    monkeypatch.setattr(paypal_module, "PAYPAL_CLIENT_SECRET", "env-client-secret")
    monkeypatch.setattr(paypal_module, "PAYPAL_MODE", "sandbox")

    with patch.object(paypal_module, "PAYPAL_SDK_AVAILABLE", True), \
         patch.object(paypal_module, "paypalrestsdk") as mock_sdk, \
         patch.object(paypal_module, "BillingSubscription") as mock_subscription_class:
        mock_api = MagicMock()
        mock_sdk.Api.return_value = mock_api

        mock_subscription = MagicMock()
        mock_subscription.create.return_value = True
        mock_subscription.to_dict.return_value = {"id": "I-456"}
        mock_subscription_class.return_value = mock_subscription

        result = await integration.execute(
            config={"plan_id": "P-456"},
            credentials_resolver=resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is True
        api_config = mock_sdk.Api.call_args.args[0]
        assert api_config["client_id"] == "env-client-id"
        assert api_config["client_secret"] == "env-client-secret"


@pytest.mark.asyncio
async def test_paypal_create_subscription_api_error(
    integration,
    credentials_resolver,
    logger,
    bot_id
):
    with patch.object(paypal_module, "PAYPAL_SDK_AVAILABLE", True), \
         patch.object(paypal_module, "paypalrestsdk") as mock_sdk, \
         patch.object(paypal_module, "BillingSubscription") as mock_subscription_class:
        mock_sdk.Api.return_value = MagicMock()

        mock_subscription = MagicMock()
        mock_subscription.create.return_value = False
        mock_subscription.error = {
            "name": "INVALID_REQUEST",
            "message": "Bad request"
        }
        mock_subscription_class.return_value = mock_subscription

        result = await integration.execute(
            config={"plan_id": "P-789"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is False
        assert result["response"]["error"]["type"] == "api_error"
        assert "details" in result["response"]["error"]


@pytest.mark.asyncio
async def test_paypal_create_subscription_connection_error(
    integration,
    credentials_resolver,
    logger,
    bot_id
):
    class FakeConnectionError(Exception):
        pass

    with patch.object(paypal_module, "PAYPAL_SDK_AVAILABLE", True), \
         patch.object(paypal_module, "PayPalConnectionError", FakeConnectionError), \
         patch.object(paypal_module, "paypalrestsdk") as mock_sdk, \
         patch.object(paypal_module, "BillingSubscription") as mock_subscription_class:
        mock_sdk.Api.return_value = MagicMock()

        mock_subscription = MagicMock()
        mock_subscription.create.side_effect = FakeConnectionError("timeout")
        mock_subscription_class.return_value = mock_subscription

        result = await integration.execute(
            config={"plan_id": "P-999"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is False
        assert result["response"]["error"]["type"] == "network_error"
