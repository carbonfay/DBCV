"""Ozon интеграции."""
from .get_product_info import OzonGetProductInfoIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(OzonGetProductInfoIntegration())
