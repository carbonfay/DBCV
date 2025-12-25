"""GitHub интеграции и автоматическая регистрация."""
from .get_commits import GitHubGetCommitsIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(GitHubGetCommitsIntegration())

__all__ = ["GitHubGetCommitsIntegration"]
