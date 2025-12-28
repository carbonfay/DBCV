from app.integrations.github.create_issue import GitHubCreateIssueIntegration
from app.integrations.registry import registry

registry.register(GitHubCreateIssueIntegration())

__all__ = [
    "GitHubCreateIssueIntegration",
]
