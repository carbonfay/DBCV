"""GitVerse интеграции."""
from .create_issue import GitVerseCreateIssueIntegration
from app.integrations.registry import registry

# Регистрация интеграций
registry.register(GitVerseCreateIssueIntegration())
