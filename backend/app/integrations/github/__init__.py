"""GitHub интеграции."""
from app.integrations.registry import registry

from .update_issue import GitHubUpdateIssueIntegration

registry.register(GitHubUpdateIssueIntegration())

__all__ = ["GitHubUpdateIssueIntegration"]