import asyncio
from uuid import UUID, uuid4

import pytest
import respx
from httpx import Response

from app.integrations.openweathermap.get_uv_index import OpenWeatherMapGetUVIndexIntegration


class DummyResolver:
    def __init__(self, api_key: str | None):
        self._key = api_key

    async def get_default_for(self, *, bot_id: UUID, provider: str, strategy: str | None):
        if not self._key:
            return None
        return {"payload": {"api_key": self._key}}


@pytest.mark.asyncio
async def test_get_uv_index_success(monkeypatch):
    api_key = "test_key"
    resolver = DummyResolver(api_key)
    integration = OpenWeatherMapGetUVIndexIntegration()
    bot_id = uuid4()

    # Mock the external OpenWeatherMap URL
    url = "https://api.openweathermap.org/data/2.5/uvi"
    expected_json = {"lat": 1.0, "lon": 2.0, "value": 5.5}

    with respx.mock as rsps:
        rsps.get(url, params={"lat": "1.0", "lon": "2.0", "appid": api_key}).mock(
            return_value=Response(200, json=expected_json)
        )

        result = await integration.execute(
            config={"lat": 1.0, "lon": 2.0},
            credentials_resolver=resolver,
            bot_id=bot_id,
            logger=type("L", (), {"error": lambda *a, **k: None})(),
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["value"] == expected_json["value"]


@pytest.mark.asyncio
async def test_get_uv_index_no_credentials():
    resolver = DummyResolver(None)
    integration = OpenWeatherMapGetUVIndexIntegration()
    bot_id = uuid4()

    result = await integration.execute(
        config={"lat": 1.0, "lon": 2.0},
        credentials_resolver=resolver,
        bot_id=bot_id,
        logger=type("L", (), {"error": lambda *a, **k: None})(),
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
*** End Patch