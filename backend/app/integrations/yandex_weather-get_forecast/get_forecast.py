"""Яндекс.Погода Get Forecast интеграция используя httpx (v0.27.x) для HTTP запросов."""
from typing import Dict, Any
from uuid import UUID
import json

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем httpx для HTTP запросов
"""Deprecated shim for backward compatibility.

The real implementation lives in `app.integrations.yandex_weather_get_forecast`.
This module intentionally raises ImportError to force imports to the new package name.
"""

raise ImportError(
    "yandex_weather-get_forecast package is deprecated. Use app.integrations.yandex_weather_get_forecast instead"
)
    
