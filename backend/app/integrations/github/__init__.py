"""GitHub интеграции."""
from .create_pull_request import GitHubCreatePullRequestIntegration
from app.integrations.registry import registry

# Регистрация интеграции
registry.register(GitHubCreatePullRequestIntegration())