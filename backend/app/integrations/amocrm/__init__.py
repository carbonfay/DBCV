"""AmoCRM интеграции и регистрация в реестре."""
try:
    from .update_task import AmocrmUpdateTaskIntegration  # noqa: F401
    from app.integrations.registry import registry

    registry.register(AmocrmUpdateTaskIntegration())
except Exception:
    # Если что-то с импортом или регистрацией — пропускаем, интеграция будет недоступна
    pass
