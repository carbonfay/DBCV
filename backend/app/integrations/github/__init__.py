"""GitHub интеграции."""
from app.integrations.registry import registry

from .create_pull_request import GitHubCreatePullRequestIntegration

registry.register(GitHubCreatePullRequestIntegration())

__all__ = ["GitHubCreatePullRequestIntegration"]