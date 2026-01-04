import json
from pathlib import Path
from datetime import datetime
import pytest
from uuid import UUID
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import httpx

from app.integrations.medicine.get_pharmacy_info_cms_provider_data import (
    MedicineGetPharmacyInfoIntegration,
)
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class _MockResponse:
    """Minimal mock for httpx.Response used in tests."""

    def __init__(self, status_code: int = 200, json_data: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text

    def json(self):  # pylint: disable=invalid-name
        return self._json_data


class _MockAsyncClient:
    """Context-manager stub replacing httpx.AsyncClient inside tests."""

    def __init__(self, response: _MockResponse | None = None, *_, **__):
        self.post = AsyncMock(
            return_value=response
            or _MockResponse(json_data={"results": [{"npi": "1234567890", "provider_name": "Test Pharmacy"}]})
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):  # noqa: D401, pylint: disable=unused-argument
        return False


@pytest.mark.asyncio
@pytest.mark.skipif(
    "MEDICINE_APP_TOKEN" not in __import__("os").environ,
    reason="Requires MEDICINE_APP_TOKEN for CMS Socrata API",
)
async def test_execute_real_cms():
    """Real call to CMS POS dataset via Socrata, requires app token."""

    import os

    integration = MedicineGetPharmacyInfoIntegration()
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(
        return_value={"payload": {"app_token": os.environ["MEDICINE_APP_TOKEN"]}}
    )
    bot_id = UUID("00000000-0000-0000-0000-000000000000")
    logger = MagicMock(spec=BotLogger)

    # Known valid pharmacy NPI example (may need update if dataset changes)
    npi = "1801997747"
    result = await integration.execute(
        config={"npi": npi},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    logs_dir = Path(__file__).resolve().parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"{Path(__file__).stem}_{ts}_test_execute_real_cms.json"
    with log_file.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    assert result["response"]["ok"] is True
    assert result["response"]["result"].get("npi") == npi


@pytest.mark.asyncio
async def test_execute_success(monkeypatch):
    """Integration returns expected structure on success."""

    # Patch httpx.AsyncClient with our stub
    monkeypatch.setattr(httpx, "AsyncClient", _MockAsyncClient)

    integration = MedicineGetPharmacyInfoIntegration()

    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(
        return_value={
            "payload": {"app_token": "token"}
        }
    )

    bot_id = UUID("00000000-0000-0000-0000-000000000000")
    logger = MagicMock(spec=BotLogger)

    result = await integration.execute(
        config={"npi": "1234567890", "state": "TX"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["npi"] == "1234567890"
    assert result["response"]["result"]["provider_name"] == "Test Pharmacy"
    # Ensure the underlying HTTP call was formed correctly
    credentials_resolver.get_default_for.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_no_credentials(monkeypatch):
    """Integration fails gracefully when credentials are missing."""

    # Replace httpx.AsyncClient to avoid real network even if accidentally called
    monkeypatch.setattr(httpx, "AsyncClient", _MockAsyncClient)

    integration = MedicineGetPharmacyInfoIntegration()
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    bot_id = UUID("00000000-0000-0000-0000-000000000000")
    logger = MagicMock(spec=BotLogger)

    result = await integration.execute(
        config={"npi": "1234567890"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_execute_missing_npi(monkeypatch):
    """Integration validates required npi."""

    monkeypatch.setattr(httpx, "AsyncClient", _MockAsyncClient)

    integration = MedicineGetPharmacyInfoIntegration()
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
