"""Wildberries интеграции."""
from .get_orders import WildberriesGetOrdersIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(WildberriesGetOrdersIntegration())



