from .create_receipt import YooKassaCreateReceiptIntegration
from app.integrations.registry import registry

registry.register(YooKassaCreateReceiptIntegration())
