# backend/app/integrations/wildberries/__init__.py
"""Wildberries интеграции."""
from .update_stock import WildberriesUpdateStockIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(WildberriesUpdateStockIntegration())
