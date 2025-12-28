from app.integrations.github.list_commits import GitHubListCommitsIntegration
from app.integrations.registry import registry

registry.register(GitHubListCommitsIntegration())

__all__ = [
    "GitHubListCommitsIntegration",
]
