"""Интеграции с Wildberries."""
from app.integrations.Wildberries.update_stock import WildberriesUpdateStockIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(WildberriesUpdateStockIntegration())

__all__ = ["WildberriesUpdateStockIntegration"]