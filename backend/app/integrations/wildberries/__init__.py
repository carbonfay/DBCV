"""Интеграции с Wildberries."""
from .get_order import WildberriesGetOrderIntegration
from .get_orders import WildberriesGetOrdersIntegration
from .update_stock import WildberriesUpdateStockIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(WildberriesGetOrderIntegration())
registry.register(WildberriesGetOrdersIntegration())
registry.register(WildberriesUpdateStockIntegration())

__all__ = ["WildberriesGetOrderIntegration", "WildberriesGetOrdersIntegration", "WildberriesUpdateStockIntegration"]
