"""GitHub интеграции и автоматическая регистрация."""
from .create_issue import GitHubCreateIssueIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(GitHubCreateIssueIntegration())

__all__ = ["GitHubCreateIssueIntegration"]
