"""GitHub интеграции."""
from .get_issue import GitHubGetIssueIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(GitHubGetIssueIntegration())

