"""Simple script to manually test OpenWeatherMapGetUVIndexIntegration.

Usage:
  - Set environment variable OPENWEATHERMAP_API_KEY to a valid API key to run a real request.
  - Or edit the `DUMMY_API_KEY` below for quick testing.

This script loads the integration module in isolation using minimal stubs so
it can be executed without importing the whole `app` package and its deps.
"""
import os
import sys
import types
import asyncio
from uuid import UUID, uuid4
from pathlib import Path


# To avoid importing the whole `app` package (and its external deps),
# create minimal stub modules and inject them into sys.modules before
# loading the integration module from file.
def _prepare_stubs():
    # app.integrations.base stub
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

    # app.auth.credentials_resolver stub (type only)
    auth_mod = types.ModuleType("app.auth.credentials_resolver")

    class CredentialsResolver:
        async def get_default_for(self, *args, **kwargs):
            return None

    auth_mod.CredentialsResolver = CredentialsResolver
    sys.modules["app.auth.credentials_resolver"] = auth_mod

    # app.loggers.bot stub with NoopBotLogger
    log_mod = types.ModuleType("app.loggers.bot")

    class NoopBotLogger:
        def __init__(self, *args, **kwargs):
            pass

        async def info(self, *args, **kwargs):
            return

        async def warning(self, *args, **kwargs):
            return

        async def error(self, *args, **kwargs):
            return

        async def print(self, *args, **kwargs):
            return

    log_mod.NoopBotLogger = NoopBotLogger
    log_mod.BotLogger = NoopBotLogger
    sys.modules["app.loggers.bot"] = log_mod


async def main():
    # Allow using a real key via env var for manual testing
    api_key = os.environ.get("OPENWEATHERMAP_API_KEY") or os.environ.get("OPENWEATHERMAP_KEY")

    # Prepare stubs so the integration file can be loaded without full app deps
    _prepare_stubs()

    # Load the integration module directly from file
    module_path = Path(__file__).with_name("get_uv_index.py")
    import importlib.util

    spec = importlib.util.spec_from_file_location("openweathermap.get_uv_index", str(module_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["openweathermap.get_uv_index"] = mod
    spec.loader.exec_module(mod)  # type: ignore

    # Build a simple resolver that returns the key
    class DummyResolver:
        def __init__(self, key):
            self._key = key

        async def get_default_for(self, *, bot_id: UUID, provider: str, strategy: str | None):
            if not self._key:
                return None
            return {"payload": {"api_key": self._key}}

    resolver = DummyResolver(api_key)

    # Instantiate integration class from the loaded module
    IntegrationClass = getattr(mod, "OpenWeatherMapGetUVIndexIntegration")
    integration = IntegrationClass()
    logger = sys.modules["app.loggers.bot"].NoopBotLogger()
    bot_id = uuid4()

    config = {"lat": 55.75, "lon": 37.6167}

    result = await integration.execute(config=config, credentials_resolver=resolver, bot_id=bot_id, logger=logger)
    print("Result:", result)


if __name__ == "__main__":
    asyncio.run(main())
