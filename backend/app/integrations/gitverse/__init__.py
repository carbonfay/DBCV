"""GitVerse интеграции."""
from app.integrations.registry import registry
from .get_merge_requests import GitVerseGetMergeRequestsIntegration

# Регистрация интеграций
registry.register(GitVerseGetMergeRequestsIntegration())
