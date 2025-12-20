"""GitHub интеграции."""
try:
    from .get_issue import GitHubGetIssueIntegration
    from .update_issue import GitHubUpdateIssueIntegration
    from .create_pull_request import GitHubCreatePullRequestIntegration
    from app.integrations.registry import registry

    registry.register(GitHubGetIssueIntegration())
    registry.register(GitHubUpdateIssueIntegration())
    registry.register(GitHubCreatePullRequestIntegration())
    all = ["GitHubGetIssueIntegration", "GitHubUpdateIssueIntegration", "GitHubCreatePullRequestIntegration"]
except ImportError as e:
    # Если PyGithub не установлена, просто пропускаем
    import warnings
    warnings.warn(f"GitHub integration not available: {e}")
    all = []