"""Изолированная проверка интеграции Telegram Send Video.

Скрипт загружает необходимые модули напрямую из файлов, подставляет
минимальный заглушечный `app.loggers.bot` и проверяет метаданные и
наличие метода `execute` у `TelegramSendVideoIntegration`.
"""
import importlib.util
import importlib.machinery
import sys
from types import ModuleType
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]  # backend/
sys.path.insert(0, str(BASE_DIR))

# Создаём заглушечный модуль app.loggers.bot с минимальным BotLogger
stub_bot_mod = ModuleType("app.loggers.bot")

class StubBotLogger:
    def __init__(self, bot_id: str = "stub"):
        self.bot_id = bot_id
    async def info(self, msg: str):
        return
    async def warning(self, msg: str):
        return
    async def error(self, msg: str):
        return

stub_bot_mod.BotLogger = StubBotLogger
stub_bot_mod.NoopBotLogger = StubBotLogger

# Вставляем модуль в sys.modules
sys.modules["app.loggers.bot"] = stub_bot_mod

# Функция для загрузки модуля из файла под указанным именем
def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

try:
    # Загружаем базовый модуль интеграций и резолвер кредов
    load_module("app.auth.credentials_resolver", BASE_DIR / "app" / "auth" / "credentials_resolver.py")
    load_module("app.integrations.base", BASE_DIR / "app" / "integrations" / "base.py")

    # Загружаем сам send_video под именем package-like
    sv_mod = load_module("app.integrations.telegram.send_video", BASE_DIR / "app" / "integrations" / "telegram" / "send_video.py")

    # Получаем класс
    cls = getattr(sv_mod, "TelegramSendVideoIntegration", None)
    if not cls:
        print("TelegramSendVideoIntegration class NOT FOUND")
        raise SystemExit(2)

    inst = cls()
    meta = inst.metadata
    print("metadata.id:", meta.id)
    print("metadata.version:", meta.version)
    print("metadata.name:", meta.name)
    print("credentials_provider:", meta.credentials_provider)
    print("credentials_strategy:", meta.credentials_strategy)

    # Проверяем метод execute присутствует
    has_execute = callable(getattr(inst, "execute", None))
    print("has execute():", has_execute)

    print("OK - isolated checks passed")
except Exception as e:
    import traceback
    traceback.print_exc()
    print("ERROR:", e)
    raise
