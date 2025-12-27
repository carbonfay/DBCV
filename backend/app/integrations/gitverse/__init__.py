"""GitVerse интеграции."""
from app.integrations.registry import registry
from .get_commits import GitVerseGetCommitsIntegration
from .create_issue import GitVerseCreateIssueIntegration

# Регистрация интеграций
registry.register(GitVerseGetCommitsIntegration())
registry.register(GitVerseCreateIssueIntegration())
