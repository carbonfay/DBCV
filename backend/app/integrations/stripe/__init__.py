"""Stripe интеграции."""
try:
    from .cancel_subscription import StripeCancelSubscriptionIntegration
    from app.integrations.registry import registry
    
    # Автоматическая регистрация интеграций
    registry.register(StripeCancelSubscriptionIntegration())
except ImportError:
    # Библиотека не установлена, пропускаем
    pass
