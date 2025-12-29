from app.integrations.github.get_pull_request import GitHubGetPullRequestIntegration
from app.integrations.registry import registry

registry.register(GitHubGetPullRequestIntegration())

__all__ = [
    "GitHubGetPullRequestIntegration",
]
