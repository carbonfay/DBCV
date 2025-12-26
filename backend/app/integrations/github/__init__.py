"""GitHub интеграции."""
from .get_commits import GitHubGetCommitsIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(GitHubGetCommitsIntegration())