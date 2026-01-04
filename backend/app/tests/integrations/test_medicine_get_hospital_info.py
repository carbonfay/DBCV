import json
from pathlib import Path
from datetime import datetime
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock

import httpx

from app.integrations.medicine.get_hospital_info_cms_provider_data import (
    MedicineGetHospitalInfoIntegration,
)
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class _MockResponse:
    """Минимальный мок httpx.Response для тестов."""

    def __init__(self, status_code: int = 200, json_data: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text

    def json(self):  # pylint: disable=invalid-name
        return self._json_data


class _MockAsyncClient:
    """Контекстный менеджер, заменяющий httpx.AsyncClient."""

    def __init__(self, response: _MockResponse | None = None, *_, **__):
        resp = response or _MockResponse(
            json_data={"results": [{"facility_id": "42", "facility_name": "City Hospital"}]}
        )
        self.post = AsyncMock(return_value=resp)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):  # noqa: D401 pylint: disable=unused-argument
        return False


@pytest.mark.asyncio
async def test_execute_real_medicare():
    """Реальный вызов Medicare Hospital General Info API без credentials."""

    integration = MedicineGetHospitalInfoIntegration()
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    bot_id = UUID("00000000-0000-0000-0000-000000000000")
    logger = MagicMock(spec=BotLogger)

    # Провайдер 010001 (пример из CMS)
    result = await integration.execute(
        config={"hospital_id": "010001"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    logs_dir = Path(__file__).resolve().parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"{Path(__file__).stem}_{ts}_test_execute_real_medicare.json"
    with log_file.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    assert result["response"]["ok"] is True or result["response"].get("error_code") in {404, 500}


@pytest.mark.asyncio
async def test_execute_success(monkeypatch):
    """Интеграция возвращает ожидаемую структуру при успехе."""

    monkeypatch.setattr(httpx, "AsyncClient", _MockAsyncClient)

    integration = MedicineGetHospitalInfoIntegration()

    credentials_resolver = MagicMock(spec=CredentialsResolver)
    bot_id = UUID("00000000-0000-0000-0000-000000000000")
    logger = MagicMock(spec=BotLogger)

    result = await integration.execute(
        config={"hospital_id": "42"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is True
    assert result["response"]["result"] == {
        "facility_id": "42",
        "facility_name": "City Hospital",
    }
    credentials_resolver.get_default_for.assert_not_called()


@pytest.mark.asyncio
async def test_execute_no_credentials(monkeypatch):
    """Интеграция не требует credentials и не обращается к resolver."""

    monkeypatch.setattr(httpx, "AsyncClient", _MockAsyncClient)

    integration = MedicineGetHospitalInfoIntegration()
    credentials_resolver = MagicMock(spec=CredentialsResolver)

    bot_id = UUID("00000000-0000-0000-0000-000000000000")
    logger = MagicMock(spec=BotLogger)

    result = await integration.execute(
        config={"hospital_id": "42"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is True
    credentials_resolver.get_default_for.assert_not_called()


@pytest.mark.asyncio
async def test_execute_missing_id(monkeypatch):
    """Интеграция валидирует обязательный hospital_id."""

    monkeypatch.setattr(httpx, "AsyncClient", _MockAsyncClient)

    integration = MedicineGetHospitalInfoIntegration()
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

