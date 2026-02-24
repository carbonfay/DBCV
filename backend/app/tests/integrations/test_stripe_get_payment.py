import json
from pathlib import Path
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.integrations.stripe.get_payment import StripeGetPaymentIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return StripeGetPaymentIntegration()


@pytest.fixture
def credentials_resolver():
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {"api_key": "sk_test_123"}
    })
    return resolver


@pytest.fixture
def logger():
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")


def _load_fixture():
    p = Path(__file__).resolve().parents[2] / "fixtures" / "stripe" / "get_payment.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def test_stripe_metadata(integration):
    meta = integration.metadata
    assert meta.id == "stripe_get_payment"
    assert meta.version == "1.0.0"
    assert meta.category == "payments"
    assert meta.credentials_provider == "stripe"
    assert meta.credentials_strategy == "api_key"
    assert meta.library_name == "stripe"


@pytest.mark.asyncio
async def test_stripe_execute_success(integration, credentials_resolver, logger, bot_id):
    fx = _load_fixture()
    charge = fx["charge"]
    with patch('app.integrations.stripe.get_payment.stripe') as mock_stripe:
        mock_stripe.Charge.retrieve.return_value = charge
        result = await integration.execute(
            config=fx["config"],
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == charge["id"]
        assert result["response"]["result"]["amount"] == charge["amount"]
        assert result["response"]["result"]["currency"] == charge["currency"]
        assert result["response"]["result"]["paid"] == charge["paid"]
        mock_stripe.Charge.retrieve.assert_called_once_with(
            fx["config"]["charge_id"],
            expand=fx["config"]["expand"]
        )


@pytest.mark.asyncio
async def test_stripe_execute_no_credentials(integration, logger, bot_id):
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=None)
    result = await integration.execute(
        config={"charge_id": "ch_123"},
        credentials_resolver=resolver,
        bot_id=bot_id,
        logger=logger
    )
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_stripe_execute_missing_config(integration, credentials_resolver, logger, bot_id):
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
