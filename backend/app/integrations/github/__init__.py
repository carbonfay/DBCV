"""GitHub интеграции."""
from .get_pull_request import GithubGetPullRequestIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(GithubGetPullRequestIntegration())

__all__ = [
    "GithubGetPullRequestIntegration"
]
