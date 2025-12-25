"""GitHub интеграции и автоматическая регистрация."""
from .git_get_pull_request import GitHubGetPullRequestIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграции
registry.register(GitHubGetPullRequestIntegration())

__all__ = ["GitHubGetPullRequestIntegration"]
