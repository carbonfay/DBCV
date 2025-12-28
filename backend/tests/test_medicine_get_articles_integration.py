import types

import pytest

from app.integrations.medicine import get_articles as medicine_module
from app.integrations.medicine.get_articles import MedicineGetArticlesIntegration


class DummyResolver:
    def __init__(self, creds):
        self._creds = creds

    async def get_default_for(self, *, bot_id, provider, strategy):
        return self._creds


class DummyLogger:
    def __init__(self):
        self.messages = []

    async def error(self, message, *args, **kwargs):
        self.messages.append(message)


@pytest.mark.asyncio
async def test_execute_success_with_api_key(monkeypatch):
    captured = {}

    async def fake_fetch(endpoint, headers, params, logger):
        captured["endpoint"] = endpoint
        captured["headers"] = headers
        captured["params"] = params
        return {"items": [1, 2]}, None

    monkeypatch.setattr(medicine_module, "_fetch_articles", fake_fetch)

    integration = MedicineGetArticlesIntegration()
    resolver = DummyResolver(
        {"payload": {"api_key": "test-key", "api_key_header": "X-Test-Key"}}
    )
    logger = DummyLogger()

    result = await integration.execute(
        config={"base_url": "http://localhost:8003", "query": "diabetes", "page": 1, "page_size": 5},
        credentials_resolver=resolver,
        bot_id=types.SimpleNamespace(),
        logger=logger,
    )

    assert result["response"]["ok"] is True
    assert result["response"]["result"] == {"items": [1, 2]}
    assert captured["headers"] == {"X-Test-Key": "test-key"}
    assert captured["params"]["query"] == "diabetes"
    assert captured["params"]["page"] == 1
    assert captured["params"]["page_size"] == 5


@pytest.mark.asyncio
async def test_execute_success_without_api_key(monkeypatch):
    captured = {}

    async def fake_fetch(endpoint, headers, params, logger):
        captured["headers"] = headers
        return {"items": []}, None

    monkeypatch.setattr(medicine_module, "_fetch_articles", fake_fetch)

    integration = MedicineGetArticlesIntegration()
    resolver = DummyResolver(None)
    logger = DummyLogger()

    result = await integration.execute(
        config={"base_url": "http://localhost:8003"},
        credentials_resolver=resolver,
        bot_id=types.SimpleNamespace(),
        logger=logger,
    )

    assert result["response"]["ok"] is True
    assert result["response"]["result"] == {"items": []}
    assert captured["headers"] == {}


@pytest.mark.asyncio
async def test_execute_missing_base_url():
    integration = MedicineGetArticlesIntegration()
    resolver = DummyResolver(None)
    logger = DummyLogger()

    result = await integration.execute(
        config={},
        credentials_resolver=resolver,
        bot_id=types.SimpleNamespace(),
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
