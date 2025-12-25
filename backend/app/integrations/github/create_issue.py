"""GitHub Create Issue интеграция используя PyGithub библиотеку."""
from typing import Dict, Any, List, Optional
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


class GitHubCreateIssueIntegration(BaseIntegration):
    """Создать Issue в репозитории GitHub через PyGithub."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_create_issue",
            version="1.0.0",
            name="GitHub Create Issue",
            description="Создать issue в репозитории GitHub (POST /repos/{owner}/{repo}/issues)",
            category="developer_tools",
            icon_s3_key="icons/integrations/github.svg",
            color="#24292e",
            config_schema={
                "type": "object",
                "required": ["owner", "repo", "title"],
                "properties": {
                    "owner": {"type": "string", "title": "Owner", "description": "Владелец репозитория"},
                    "repo": {"type": "string", "title": "Repository", "description": "Имя репозитория"},
                    "title": {"type": "string", "title": "Title", "description": "Заголовок issue"},
                    "body": {"type": "string", "title": "Body", "description": "Текст описания issue"},
                    "assignees": {"type": "array", "items": {"type": "string"}, "title": "Assignees", "description": "Список логинов для назначения"},
                    "labels": {"type": "array", "items": {"type": "string"}, "title": "Labels", "description": "Список меток"}
                }
            },
            credentials_provider="other", # ИЗМЕНЕНО: под твой Credentials
            credentials_strategy="api_key",
            library_name="PyGithub>=1.55" if PYGITHUB_AVAILABLE else None,
            examples=[
                {
                    "title": "Create simple issue",
                    "config": {"owner": "octocat", "repo": "Hello-World", "title": "Bug report", "body": "Details..."}
                }
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        if not PYGITHUB_AVAILABLE:
            await logger.error("PyGithub library is not available")
            return {"response": {"ok": False, "error_code": 500, "description": "PyGithub library is not installed"}}

        owner = config.get("owner")
        repo_name = config.get("repo")
        title = config.get("title")
        body = config.get("body")
        assignees: Optional[List[str]] = config.get("assignees")
        labels: Optional[List[str]] = config.get("labels")

        if not owner or not repo_name or not title:
            await logger.error("owner, repo and title are required")
            return {"response": {"ok": False, "error_code": 400, "description": "owner, repo and title are required"}}

        # Получаем credentials (провайдер other)
        creds = await credentials_resolver.get_default_for(bot_id=bot_id, provider="other", strategy="api_key")
        
        if not creds:
            await logger.error("GitHub credentials not found")
            return {"response": {"ok": False, "error_code": 401, "description": "Credentials not found in system"}}

        # Универсальный поиск токена
        token = None
        if isinstance(creds, dict):
            payload = creds.get("payload", {})
            if isinstance(payload, dict):
                # Добавляем api_key первым в список поиска
                token = (payload.get("api_key") or 
                         payload.get("token") or 
                         payload.get("access_token"))
        
        if not token and isinstance(creds, str):
            token = creds

        if not token:
            await logger.error("GitHub token (api_key) not found in credentials payload")
            return {"response": {"ok": False, "error_code": 401, "description": "GitHub token not found in credentials"}}

        try:
            gh = Github(token)
            repo = gh.get_repo(f"{owner}/{repo_name}")
            
            # POST запрос через PyGithub
            issue = repo.create_issue(
                title=str(title), 
                body=str(body) if body is not None else None, 
                assignees=assignees or None, 
                labels=labels or None
            )

            result = {
                "number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "state": issue.state,
                "html_url": issue.html_url,
                "created_at": issue.created_at.isoformat() if getattr(issue, "created_at", None) else None,
                "user": {"login": issue.user.login if issue.user else None, "id": issue.user.id if issue.user else None}
            }

            return {"response": {"ok": True, "result": result}}

        except GithubException as e:
            await logger.error(f"GitHub API error: {e}")
            return {"response": {"ok": False, "error_code": e.status, "description": str(e)}}
        except Exception as e:
            await logger.error(f"Unexpected error in GitHub create_issue integration: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}