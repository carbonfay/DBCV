from app.integrations.registry import registry
from app.integrations.github.create_repository import GitHubCreateRepositoryIntegration

__all__ = [
    "GitHubCreateRepositoryIntegration",
]

registry.register(GitHubCreateRepositoryIntegration())
