"""GitHub интеграции."""
from .create_pull_request import GitHubCreatePullRequestIntegration
from .get_commits import GitHubGetCommitsIntegration
from app.integrations.registry import registry

# Регистрация интеграций
registry.register(GitHubCreatePullRequestIntegration())
registry.register(GitHubGetCommitsIntegration())
