"""Обертка-конфиг для совместимости импортов."""

# Основные настройки backend
from app.config import settings  # noqa: F401

# Конфиг MCP-ассистента (используется в mcp/autonomous_assistant.py)
try:
    from mcp.config import config  # type: ignore # noqa: F401
except Exception:  # noqa: BLE001
    config = None  # type: ignore

__all__ = ["settings", "config"]
