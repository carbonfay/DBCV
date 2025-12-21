"""Tests for Medicine Get Drug Info integration."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.integrations.medicine.get_drug_info import MedicineGetDrugInfoIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return MedicineGetDrugInfoIntegration()


@pytest.fixture
def credentials_resolver():
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={"api_key": "secret-key"})
    return resolver


@pytest.fixture
def no_credentials_resolver():
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=None)
    return resolver


@pytest.fixture
def logger():
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")


def test_medicine_metadata(integration):
    meta = integration.metadata
    assert meta.id == "medicine_get_drug_info"
    assert meta.version == "1.0.0"
    assert meta.name == "Medicine Get Drug Info"
    assert meta.category == "medicine"
    assert meta.credentials_provider == "medicine"
    assert meta.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_execute_success(integration, credentials_resolver, logger, bot_id):
    drug_id = "123"
    base_url = "https://api.example-med.com"
    expected_url = f"{base_url}/api/v1/drugs/{drug_id}"
    expected_data = {"id": drug_id, "name": "Aspirin"}

    # Mock httpx.AsyncClient context and get
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value=expected_data)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    mock_async_client_cls = AsyncMock()
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client

    with patch("app.integrations.medicine.get_drug_info.httpx.AsyncClient", mock_async_client_cls):
        result = await integration.execute(
            config={"drug_id": drug_id, "base_url": base_url},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"] == expected_data

    mock_client.get.assert_awaited_once()
    called_url = mock_client.get.call_args.kwargs.get("url") or mock_client.get.call_args.args[0]
    assert called_url == expected_url


@pytest.mark.asyncio
async def test_execute_missing_drug_id(integration, credentials_resolver, logger, bot_id):
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_execute_http_status_error(integration, credentials_resolver, logger, bot_id):
    drug_id = "notfound"
    base_url = "https://api.example-med.com"

    # Simulate HTTPStatusError
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"

    exc = httpx.HTTPStatusError("error", request=None, response=mock_response)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=exc)

    mock_async_client_cls = AsyncMock()
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client

    with patch("app.integrations.medicine.get_drug_info.httpx.AsyncClient", mock_async_client_cls):
        result = await integration.execute(
            config={"drug_id": drug_id, "base_url": base_url},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 404


@pytest.mark.asyncio
async def test_execute_request_error(integration, credentials_resolver, logger, bot_id):
    drug_id = "123"
    base_url = "https://api.example-med.com"

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.RequestError("connection error"))

    mock_async_client_cls = AsyncMock()
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client

    with patch("app.integrations.medicine.get_drug_info.httpx.AsyncClient", mock_async_client_cls):
        result = await integration.execute(
            config={"drug_id": drug_id, "base_url": base_url},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 502


@pytest.mark.asyncio
async def test_execute_without_credentials(integration, no_credentials_resolver, logger, bot_id):
    # Integration should still call the API without credentials (headers empty)
    drug_id = "123"
    base_url = "https://api.example-med.com"
    expected_data = {"id": drug_id}

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value=expected_data)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    mock_async_client_cls = AsyncMock()
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client

    with patch("app.integrations.medicine.get_drug_info.httpx.AsyncClient", mock_async_client_cls):
        result = await integration.execute(
            config={"drug_id": drug_id, "base_url": base_url},
            credentials_resolver=no_credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"] == expected_data
