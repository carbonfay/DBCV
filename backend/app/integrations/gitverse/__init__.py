"""GitVerse интеграции."""
from app.integrations.registry import registry
from .get_merge_requests import GitVerseGetMergeRequestsIntegration
from .get_merge_request import GitVerseCreateMergeRequestIntegration

# Регистрация интеграций
registry.register(GitVerseGetMergeRequestsIntegration())
registry.register(GitVerseCreateMergeRequestIntegration())
