"""GitHub интеграции."""
from .create_pull_request import GitHubCreatePullRequestIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(GitHubCreatePullRequestIntegration())

