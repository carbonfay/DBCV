"""Изолированная проверка Telegram GetUpdates integration.

Не использует pytest и не требует установки внешних зависимостей.
"""
import importlib.util
import sys
from types import ModuleType
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

# Создаём заглушечный модуль app.loggers.bot
stub_bot_mod = ModuleType("app.loggers.bot")
class StubBotLogger:
    def __init__(self, bot_id: str = "stub"):
        self.bot_id = bot_id
    async def info(self, msg: str): return
    async def warning(self, msg: str): return
    async def error(self, msg: str): return

stub_bot_mod.BotLogger = StubBotLogger
sys.modules["app.loggers.bot"] = stub_bot_mod

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

try:
    load_module("app.auth.credentials_resolver", BASE_DIR / "app" / "auth" / "credentials_resolver.py")
    load_module("app.integrations.base", BASE_DIR / "app" / "integrations" / "base.py")

    mod = load_module("app.integrations.telegram.get_updates", BASE_DIR / "app" / "integrations" / "telegram" / "get_updates.py")
    cls = getattr(mod, "TelegramGetUpdatesIntegration", None)
    if not cls:
        print("TelegramGetUpdatesIntegration NOT FOUND")
        raise SystemExit(2)

    inst = cls()
    meta = inst.metadata
    print("metadata.id:", meta.id)
    print("metadata.version:", meta.version)
    print("metadata.name:", meta.name)
    print("credentials_provider:", meta.credentials_provider)
    print("credentials_strategy:", meta.credentials_strategy)
    print("has execute():", callable(getattr(inst, "execute", None)))
    print("OK - get_updates isolated check passed")
except Exception as e:
    import traceback
    traceback.print_exc()
    print("ERROR:", e)
    raise
