"""GitHub интеграции."""
from .create_pr import GitHubCreatePullRequestIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(GitHubCreatePullRequestIntegration())
