"""Wildberries integrations package: register available integrations."""
from .get_order import WildberriesGetOrderIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций при импорте пакета
registry.register(WildberriesGetOrderIntegration())

__all__ = ["WildberriesGetOrderIntegration"]
