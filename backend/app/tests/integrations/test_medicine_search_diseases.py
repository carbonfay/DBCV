import json
from pathlib import Path
from datetime import datetime
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock

import httpx

from app.integrations.medicine.search_diseases_clinicaltables import MedicineSearchDiseasesIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class _MockResponse:
    """Minimal mock for httpx.Response used in tests."""

    def __init__(self, status_code: int = 200, json_data: dict | list | None = None, text: str = ""):
        self.status_code = status_code
        self._json_data = json_data or [0, ["diabetes"], None, []]
        self.text = text

    def json(self):  # pylint: disable=invalid-name
        return self._json_data


class _MockAsyncClient:
    """Context-manager stub replacing httpx.AsyncClient inside tests."""

    def __init__(self, response: _MockResponse | None = None, *_, **__):
        self.get = AsyncMock(return_value=response or _MockResponse())

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


@pytest.mark.asyncio
async def test_execute_success(monkeypatch):
    """Integration returns expected structure on success."""

    monkeypatch.setattr(httpx, "AsyncClient", _MockAsyncClient)

    integration = MedicineSearchDiseasesIntegration()
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    bot_id = UUID("00000000-0000-0000-0000-000000000000")
    logger = MagicMock(spec=BotLogger)

    result = await integration.execute(
        config={"query": "diabetes", "max_results": 5},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is True
    assert result["response"]["result"][1][0] == "diabetes"
    credentials_resolver.get_default_for.assert_not_called()


@pytest.mark.asyncio
async def test_execute_missing_query(monkeypatch):
    """Integration validates required query."""

    monkeypatch.setattr(httpx, "AsyncClient", _MockAsyncClient)

    integration = MedicineSearchDiseasesIntegration()
    credentials_resolver = MagicMock(spec=CredentialsResolver)
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
async def test_execute_real_clinicaltables():
    """Real call to ClinicalTables conditions API without credentials."""

    integration = MedicineSearchDiseasesIntegration()
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    bot_id = UUID("00000000-0000-0000-0000-000000000000")
    logger = MagicMock(spec=BotLogger)

    result = await integration.execute(
        config={"query": "diabetes", "max_results": 5},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    logs_dir = Path(__file__).resolve().parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"{Path(__file__).stem}_{ts}_test_execute_real_clinicaltables.json"
    with log_file.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Сеть/endpoint могут быть недоступны; фиксируем результат и лог
    if result["response"]["ok"]:
        assert isinstance(result["response"]["result"], list)
    else:
        assert result["response"].get("error_code") in {404, 500}
