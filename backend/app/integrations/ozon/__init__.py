"""Ozon интеграции."""
from .get_product_list import OzonGetProductListIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(OzonGetProductListIntegration())
