# backend/app/integrations/yandex/__init__.py
from .weather_informers import YandexGetInformersIntegration  
from app.integrations.registry import registry

registry.register(YandexGetInformersIntegration())  