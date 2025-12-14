"""AI интеграции."""
from .chat_completion import OpenAIChatCompletionIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(OpenAIChatCompletionIntegration())
