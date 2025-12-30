"""GitHub Get Pull Request integration using PyGithub."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    from github import Github
    from github.GithubException import GithubException
    PYGITHUB_AVAILABLE = True
except Exception:
    Github = None
    GithubException = Exception
    PYGITHUB_AVAILABLE = False


class GitHubGetPullRequestIntegration(BaseIntegration):
    """Интеграция для получения информации о Pull Request через PyGithub."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_get_pull_request",
            version="1.0.0",
            name="GitHub Get Pull Request",
            description="Получить информацию о Pull Request по его номеру в репозитории GitHub",
            category="developer_tools",
            icon_s3_key="icons/integrations/github.svg",
            color="#24292e",
            config_schema={
                "type": "object",
                "required": ["owner", "repo", "pull_number"],
                "properties": {
                    "owner": {"type": "string", "title": "Owner", "description": "Владелец репозитория (organization или user)"},
                    "repo": {"type": "string", "title": "Repository", "description": "Имя репозитория"},
                    "pull_number": {"type": "integer", "title": "Pull Request Number", "description": "Номер PR в репозитории"}
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="PyGithub>=1.55" if PYGITHUB_AVAILABLE else None,
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        """Получает Pull Request и возвращает нормализованный результат."""
        if not PYGITHUB_AVAILABLE:
            await logger.error("PyGithub is not installed")
            return {"response": {"ok": False, "error_code": 500, "description": "PyGithub library is not installed"}}

        owner = config.get("owner")
        repo_name = config.get("repo")
        pull_number = config.get("pull_number")

        if not owner or not repo_name or not pull_number:
            await logger.error("Missing required config fields: owner, repo, pull_number")
            return {"response": {"ok": False, "error_code": 400, "description": "owner, repo and pull_number are required"}}

        # Сохраняем логику provider='other' и strategy='api_key'
        creds = await credentials_resolver.get_default_for(bot_id=bot_id, provider="other", strategy="api_key")

        if not creds:
            await logger.error("Credentials missing for GitHub (provider=other)")
            return {"response": {"ok": False, "error_code": 401, "description": "GitHub token not found in credentials"}}

        token = None
        if isinstance(creds, dict):
            payload = creds.get("payload", {})
            if isinstance(payload, dict):
                token = payload.get("api_key") or payload.get("access_token")
        if not token and isinstance(creds, str):
            token = creds

        if not token:
            await logger.error("GitHub token not present in credentials payload")
            return {"response": {"ok": False, "error_code": 401, "description": "GitHub token not found in credentials. Check 'api_key' in Payload."}}

        try:
            gh = Github(token)
            full_name = f"{owner}/{repo_name}"
            repository = gh.get_repo(full_name)
            pr = repository.get_pull(int(pull_number))

            result: Dict[str, Any] = {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "locked": pr.locked,
                "merged": pr.merged,
                "mergeable": getattr(pr, "mergeable", None),
                "mergeable_state": getattr(pr, "mergeable_state", None),
                "merged_at": pr.merged_at.isoformat() if getattr(pr, "merged_at", None) else None,
                "created_at": pr.created_at.isoformat() if getattr(pr, "created_at", None) else None,
                "updated_at": pr.updated_at.isoformat() if getattr(pr, "updated_at", None) else None,
                "user": {
                    "login": pr.user.login if pr.user else None,
                    "id": pr.user.id if pr.user else None,
                    "type": pr.user.type if pr.user else None,
                },
                "html_url": pr.html_url,
                "comments": pr.comments,
                "additions": getattr(pr, "additions", None),
                "deletions": getattr(pr, "deletions", None),
                "changed_files": getattr(pr, "changed_files", None),
                "head": {
                    "ref": pr.head.ref if pr.head else None,
                    "sha": pr.head.sha if pr.head else None,
                    "repo_full_name": pr.head.repo.full_name if getattr(pr, "head", None) and getattr(pr.head, "repo", None) else None,
                },
                "base": {
                    "ref": pr.base.ref if pr.base else None,
                    "sha": pr.base.sha if pr.base else None,
                    "repo_full_name": pr.base.repo.full_name if getattr(pr, "base", None) and getattr(pr.base, "repo", None) else None,
                },
                "assignees": [a.login for a in pr.assignees] if getattr(pr, "assignees", None) else None,
                "labels": [l.name for l in pr.labels] if getattr(pr, "labels", None) else None,
            }

            return {"response": {"ok": True, "result": result}}

        except GithubException as e:
            await logger.error(f"GitHub API error while fetching PR: {e}")
            status = getattr(e, "status", None)
            return {"response": {"ok": False, "error_code": status or 500, "description": str(e)}}
        except Exception as e:
            await logger.error(f"Unexpected error in GitHub get_pull_request: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
