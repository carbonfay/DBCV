

# backend/app/integrations/telegram/__init__.py
from get_updates import AmoCRMUpdateLeadIntegration
from app.integrations.registry import registry

# Регистрация интеграции
registry.register(AmoCRMUpdateLeadIntegration())