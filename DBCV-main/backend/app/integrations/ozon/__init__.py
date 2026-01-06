from .get_product_info import OzonGetProductInfoIntegration
from app.integrations.registry import registry

registry.register(OzonGetProductInfoIntegration())