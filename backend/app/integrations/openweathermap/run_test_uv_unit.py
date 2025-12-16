"""Run small standalone checks for OpenWeatherMapGetUVIndexIntegration using respx.

This avoids importing project-wide pytest conftest and heavy deps.
"""
import asyncio
from uuid import uuid4

import respx
from httpx import Response

# Load integration module directly to avoid importing whole `app` package
import importlib.util
from pathlib import Path

module_path = Path(__file__).with_name("get_uv_index.py")
spec = importlib.util.spec_from_file_location("openweathermap.get_uv_index", str(module_path))
mod = importlib.util.module_from_spec(spec)
# ensure submodule name so relative imports inside module resolve to names
import sys
sys.modules["openweathermap.get_uv_index"] = mod
# Prepare minimal stubs for app.integrations.base, app.loggers.bot and app.auth.credentials_resolver
import types
import sys

base_mod = types.ModuleType("app.integrations.base")

class BaseIntegration:
    pass

class IntegrationMetadata:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

base_mod.BaseIntegration = BaseIntegration
base_mod.IntegrationMetadata = IntegrationMetadata
sys.modules["app.integrations.base"] = base_mod

log_mod = types.ModuleType("app.loggers.bot")
class NoopBotLogger:
    def __init__(self, *args, **kwargs):
        pass
    async def error(self, *a, **k):
        return
    async def info(self, *a, **k):
        return
log_mod.BotLogger = NoopBotLogger
log_mod.NoopBotLogger = NoopBotLogger
sys.modules["app.loggers.bot"] = log_mod

auth_mod = types.ModuleType("app.auth.credentials_resolver")
class CredentialsResolver:
    pass
auth_mod.CredentialsResolver = CredentialsResolver
sys.modules["app.auth.credentials_resolver"] = auth_mod

spec.loader.exec_module(mod)  # type: ignore
OpenWeatherMapGetUVIndexIntegration = getattr(mod, "OpenWeatherMapGetUVIndexIntegration")


class DummyResolver:
    def __init__(self, api_key):
        self._key = api_key

    async def get_default_for(self, *, bot_id, provider, strategy):
        if not self._key:
            return None
        return {"payload": {"api_key": self._key}}


async def run():
    integration = OpenWeatherMapGetUVIndexIntegration()
    bot_id = uuid4()

    # Test success
    api_key = "test_key"
    resolver = DummyResolver(api_key)
    url = "https://api.openweathermap.org/data/2.5/uvi"
    expected_json = {"lat": 1.0, "lon": 2.0, "value": 5.5}

    class AsyncLogger:
        async def error(self, *a, **k):
            return
        async def info(self, *a, **k):
            return

    with respx.mock as rsps:
        rsps.get(url, params={"lat": "1.0", "lon": "2.0", "appid": api_key}).mock(return_value=Response(200, json=expected_json))

        result = await integration.execute(config={"lat": 1.0, "lon": 2.0}, credentials_resolver=resolver, bot_id=bot_id, logger=AsyncLogger())
        assert result["response"]["ok"] is True, f"expected ok True, got {result}"
        print("Success test passed")

    # Test missing credentials
    resolver2 = DummyResolver(None)
    result2 = await integration.execute(config={"lat": 1.0, "lon": 2.0}, credentials_resolver=resolver2, bot_id=bot_id, logger=AsyncLogger())
    assert result2["response"]["ok"] is False and result2["response"]["error_code"] == 401, f"expected 401, got {result2}"
    print("Missing credentials test passed")


if __name__ == "__main__":
    asyncio.run(run())
