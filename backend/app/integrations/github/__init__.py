"""GitHub интеграции."""
from .get_issue import GitHubGetIssueIntegration
from app.integrations.registry import registry

registry.register(GitHubGetIssueIntegration())

__all__ = ["GitHubGetIssueIntegration"]