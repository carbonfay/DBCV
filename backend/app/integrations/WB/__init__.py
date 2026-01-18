from .update_stock import WBUpdateStockIntegration
from app.integrations.registry import registry

registry.register(WBUpdateStockIntegration())
