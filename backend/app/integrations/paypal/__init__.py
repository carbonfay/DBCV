from .create_payout import PayPalCreatePayout
from app.integrations.registry import registry

# Регистрация интеграции
registry.register(PayPalCreatePayout())
