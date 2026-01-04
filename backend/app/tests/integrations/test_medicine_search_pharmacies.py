import os
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock

import httpx

from app.integrations.medicine.search_pharmacies_cms_provider_data import MedicineSearchPharmaciesIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class _MockResponse:
    """Minimal mock for httpx.Response used in tests."""

    def __init__(self, status_code: int = 200, json_data: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._json_data = json_data or {"results": [{"provider_name": "Test Pharmacy", "state": "TX"}]}
        self.text = text

    def json(self):  # pylint: disable=invalid-name
        return self._json_data


class _MockAsyncClient:
    """Context-manager stub replacing httpx.AsyncClient inside tests."""

    def __init__(self, response: _MockResponse | None = None, *_, **__):
        self.post = AsyncMock(return_value=response or _MockResponse())

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


@pytest.mark.asyncio
async def test_execute_success(monkeypatch):
    """Integration returns expected structure on success."""

    monkeypatch.setattr(httpx, "AsyncClient", _MockAsyncClient)

    integration = MedicineSearchPharmaciesIntegration()
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={"payload": {"app_token": "token"}})
    bot_id = UUID("00000000-0000-0000-0000-000000000000")
    logger = MagicMock(spec=BotLogger)

    result = await integration.execute(
        config={"query": "Test", "state": "TX", "limit": 5},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is True
    assert result["response"]["result"][0]["provider_name"] == "Test Pharmacy"
    credentials_resolver.get_default_for.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_missing_query(monkeypatch):
    """Integration validates required query."""

    monkeypatch.setattr(httpx, "AsyncClient", _MockAsyncClient)

    integration = MedicineSearchPharmaciesIntegration()
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={"payload": {"app_token": "token"}})
    bot_id = UUID("00000000-0000-0000-0000-000000000000")
    logger = MagicMock(spec=BotLogger)

    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
@pytest.mark.skipif("MEDICINE_APP_TOKEN" not in os.environ, reason="Requires MEDICINE_APP_TOKEN for real CMS call")
async def test_execute_real_socrata():
    """Real call to CMS provider-data search (requires MEDICINE_APP_TOKEN)."""

    integration = MedicineSearchPharmaciesIntegration()
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={"payload": {"app_token": os.environ["MEDICINE_APP_TOKEN"]}})
    bot_id = UUID("00000000-0000-0000-0000-000000000000")
    logger = MagicMock(spec=BotLogger)

    result = await integration.execute(
        config={"query": "CVS", "state": "TX", "limit": 1},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is True
