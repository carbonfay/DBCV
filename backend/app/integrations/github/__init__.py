"""GitHub интеграции."""
from .create_issue import GitHubCreateIssueIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(GitHubCreateIssueIntegration())
