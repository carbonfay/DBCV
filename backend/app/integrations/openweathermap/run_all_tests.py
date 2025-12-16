"""Run pytest-like tests for OpenWeatherMap UV index integration without full pytest setup.

This script loads the test file and runs all async test functions.
"""
import asyncio
import importlib.util
from pathlib import Path
import sys
import types

# Prepare stubs
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

# Load integration
module_path = Path(__file__).parent / "get_uv_index.py"
spec = importlib.util.spec_from_file_location("openweathermap.get_uv_index", str(module_path))
mod = importlib.util.module_from_spec(spec)
sys.modules["openweathermap.get_uv_index"] = mod
spec.loader.exec_module(mod)

# Load test module
test_path = Path(__file__).parent.parent.parent / "tests" / "integrations" / "test_openweathermap_uv.py"
spec_test = importlib.util.spec_from_file_location("test_openweathermap_uv", str(test_path))
test_mod = importlib.util.module_from_spec(spec_test)
sys.modules["test_openweathermap_uv"] = test_mod
spec_test.loader.exec_module(test_mod)

# Import pytest and respx
import pytest
import respx
from httpx import Response

# Run tests
async def run_tests():
    # Get all test functions
    test_functions = [getattr(test_mod, name) for name in dir(test_mod) if name.startswith("test_") and callable(getattr(test_mod, name))]
    
    for test_func in test_functions:
        print(f"Running {test_func.__name__}...")
        try:
            await test_func()
            print(f"✓ {test_func.__name__} passed")
        except Exception as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(run_tests())