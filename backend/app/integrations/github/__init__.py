"""GitHub интеграции."""
try:
    from .get_issue import GitHubGetIssueIntegration
    from .update_issue import GitHubUpdateIssueIntegration
    from app.integrations.registry import registry

    registry.register(GitHubGetIssueIntegration())
    registry.register(GitHubUpdateIssueIntegration())
    all = ["GitHubGetIssueIntegration", "GitHubUpdateIssueIntegration"]
except ImportError as e:
    # Если PyGithub не установлена, просто пропускаем
    import warnings
    warnings.warn(f"GitHub integration not available: {e}")
    all = []