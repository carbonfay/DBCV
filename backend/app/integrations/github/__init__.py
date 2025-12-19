"""GitHub интеграции."""
from app.integrations.registry import registry

from .get_issue import GitHubGetIssueIntegration

registry.register(GitHubGetIssueIntegration())

__all__ = ["GitHubGetIssueIntegration"]