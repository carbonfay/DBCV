# backend/app/integrations/yandex/__init__.py
from .weather_forecast import YandexGetForecastIntegration
from app.integrations.registry import registry

registry.register(YandexGetForecastIntegration())