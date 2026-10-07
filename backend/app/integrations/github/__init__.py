"""GitHub интеграции."""
from .create_issue import GithubCreateIssueIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(GithubCreateIssueIntegration())

__all__ = [
    "GithubCreateIssueIntegration"
]
