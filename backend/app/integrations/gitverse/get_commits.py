"""Gitverse Get Commits интеграция используя PyGithub библиотеку.

Получает список коммитов из репозитория GitHub.
"""
from typing import Dict, Any, List
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger
from app.integrations.registry import registry

# Попытка импортировать PyGithub непосредственно
try:
    from github import Github
    from github.GithubException import GithubException
    GITHUB_AVAILABLE = True
except Exception:
    GITHUB_AVAILABLE = False
    Github = None
    GithubException = Exception


class GitverseGetCommitsIntegration(BaseIntegration):
    """Интеграция для получения списка коммитов из GitHub через PyGithub."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="gitverse_get_commits",
            version="1.0.0",
            name="Gitverse Get Commits",
            description="Получение списка коммитов из репозитория GitHub через PyGithub",
            category="automation",
            icon_s3_key="icons/integrations/gitverse.svg",
            color="#333333",
            config_schema={
                "type": "object",
                "properties": {
                    "repo_name": {"type": "string", "title": "Repository Name", "description": "Полное имя репозитория в формате owner/repo"},
                    "sha": {"type": "string", "title": "SHA или ветка", "description": "SHA коммита или имя ветки/ветвления"},
                    "path": {"type": "string", "title": "Path", "description": "Опциональный путь для фильтра коммитов"},
                    "author": {"type": "string", "title": "Author", "description": "Логин автора для фильтра"},
                    "since": {"type": "string", "title": "Since", "description": "Дата (ISO) с которой брать коммиты"},
                    "until": {"type": "string", "title": "Until", "description": "Дата (ISO) до которой брать коммиты"},
                },
                "required": ["repo_name"]
            },
            credentials_provider="gitverse",
            credentials_strategy="api_key",
            library_name="PyGithub==1.77" if GITHUB_AVAILABLE else None,
            examples=[
                {"title": "Get recent commits", "config": {"repo_name": "owner/repo", "sha": "main", "since": "2023-01-01T00:00:00Z"}}
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        """Выполняет интеграцию Get Commits.

        Поддерживаемые параметры config: repo_name (обязательный), sha, path, author, since, until
        """
        if not GITHUB_AVAILABLE:
            await logger.error("PyGithub library is not available")
            return {"response": {"ok": False, "error_code": 500, "description": "PyGithub library is not installed"}}

        # Получаем credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id, provider="gitverse", strategy="api_key"
        )

        if not creds:
            await logger.error("Gitverse credentials not found")
            return {"response": {"ok": False, "error_code": 401, "description": "Gitverse API key not found in credentials"}}

        payload = creds.get("payload", {}) or creds
        token = payload.get("token") or payload.get("access_token") or payload.get("api_key") or payload.get("apiKey")
        if not token:
            await logger.error(f"API token not found in credentials. Available keys: {list(payload.keys())}")
            return {"response": {"ok": False, "error_code": 401, "description": "API token not found in credentials"}}

        repo_name = config.get("repo_name")
        if not repo_name:
            await logger.error("repo_name is required")
            return {"response": {"ok": False, "error_code": 400, "description": "repo_name is required"}}

        # Подготовим фильтры
        filters = {}
        for key in ("sha", "path", "author", "since", "until"):
            if config.get(key) is not None:
                filters[key] = config.get(key)

        try:
            gh = Github(login_or_token=str(token))
            repo = gh.get_repo(str(repo_name))

            commits = repo.get_commits(**filters)  # PyGithub поддерживает параметры sha, path, author, since, until

            result: List[Dict[str, Any]] = []
            for c in commits:
                commit_obj = getattr(c, "commit", None)
                author = None
                if getattr(c, "author", None):
                    try:
                        author = {"login": c.author.login}
                    except Exception:
                        author = None
                elif commit_obj and getattr(commit_obj, "author", None):
                    try:
                        author = {"name": commit_obj.author.name}
                    except Exception:
                        author = None

                result.append({
                    "sha": getattr(c, "sha", None),
                    "message": getattr(commit_obj, "message", None),
                    "author": author,
                    "date": getattr(commit_obj, "author", None) and getattr(commit_obj.author, "date", None),
                    "url": getattr(c, "html_url", None),
                })

            return {"response": {"ok": True, "result": {"count": len(result), "commits": result}}}

        except GithubException as e:
            await logger.error(f"GitHub API error: {e}")
            return {"response": {"ok": False, "error_code": 502, "description": str(e)}}
        except Exception as e:
            await logger.error(f"Unexpected error while fetching commits: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}


# Регистрируем интеграцию
registry.register(GitverseGetCommitsIntegration())
