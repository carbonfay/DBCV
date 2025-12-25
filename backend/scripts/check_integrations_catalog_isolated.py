"""Изолированная проверка каталога интеграций (имитация /api/integrations/catalog).

Скрипт загружает минимально необходимые модули, регистрирует Telegram интеграции
и выводит их метаданные в формате, похожем на API-ответ.
"""
from pathlib import Path
import sys
import importlib.util
from types import ModuleType

BASE_DIR = Path(__file__).resolve().parents[1]  # backend/
sys.path.insert(0, str(BASE_DIR))

# Вставляем заглушечный app.loggers.bot
stub_bot_mod = ModuleType("app.loggers.bot")
class StubBotLogger:
    def __init__(self, bot_id: str = "stub"): self.bot_id = bot_id
    async def info(self, msg: str): return
    async def warning(self, msg: str): return
    async def error(self, msg: str): return
stub_bot_mod.BotLogger = StubBotLogger
sys.modules["app.loggers.bot"] = stub_bot_mod

def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

# Load base and registry
load_mod("app.integrations.base", BASE_DIR / "app" / "integrations" / "base.py")
load_mod("app.integrations.registry", BASE_DIR / "app" / "integrations" / "registry.py")

# Load registry global
from app.integrations.registry import registry

# Load telegram modules (send_message may or may not exist; handle gracefully)
msg_path = BASE_DIR / "app" / "integrations" / "telegram" / "send_message.py"
video_path = BASE_DIR / "app" / "integrations" / "telegram" / "send_video.py"

registered = []
try:
    mod_msg = load_mod("app.integrations.telegram.send_message", msg_path)
    cls_msg = getattr(mod_msg, "TelegramSendMessageIntegration", None)
    if cls_msg:
        registry.register(cls_msg())
        registered.append(cls_msg().metadata)
except FileNotFoundError:
    pass

try:
    mod_vid = load_mod("app.integrations.telegram.send_video", video_path)
    cls_vid = getattr(mod_vid, "TelegramSendVideoIntegration", None)
    if cls_vid:
        registry.register(cls_vid())
        registered.append(cls_vid().metadata)
except FileNotFoundError:
    pass

# Simulate icon_service.get_icon_url by returning placeholder

def icon_url_for(key):
    return f"/static/{key}" if key else ""

# Print catalog items for category 'messaging'
items = []
for meta in registry.list_by_category("messaging", latest_only=True):
    items.append({
        "id": meta.id,
        "version": meta.version,
        "name": meta.name,
        "description": meta.description,
        "category": meta.category,
        "icon_url": icon_url_for(meta.icon_s3_key),
        "color": meta.color,
        "config_schema": meta.config_schema,
        "credentials_provider": meta.credentials_provider,
        "credentials_strategy": meta.credentials_strategy,
        "library_name": meta.library_name,
        "examples": meta.examples or [],
    })

import json
print(json.dumps({"items": items}, ensure_ascii=False, indent=2))
