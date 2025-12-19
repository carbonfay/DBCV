"""Gitverse Get Merge Request интеграция используя PyGithub библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger
from app.integrations.registry import registry

# Попытка импортировать PyGithub напрямую
try:
    from github import Github
    from github.GithubException import GithubException
    GITHUB_AVAILABLE = True
except Exception:
    GITHUB_AVAILABLE = False
    Github = None
    GithubException = Exception


class GitverseGetMergeRequestIntegration(BaseIntegration):
    """Интеграция для получения информации о pull/merge request через PyGithub."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="gitverse_get_merge_request",
            version="1.0.0",
            name="Gitverse Get Merge Request",
            description="Получение информации о pull/merge request из GitHub через PyGithub",
            category="automation",
            icon_s3_key="icons/integrations/gitverse.svg",
            color="#333333",
            config_schema={
                "type": "object",
                "required": ["repo_name", "pull_number"],
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "title": "Repository Name",
                        "description": "Полное имя репозитория в формате owner/repo"
                    },
                    "pull_number": {
                        "type": "integer",
                        "title": "Pull Request Number",
                        "description": "Номер pull/merge request"
                    }
                }
            },
            credentials_provider="gitverse",
            credentials_strategy="api_key",
            library_name="PyGithub==1.77" if GITHUB_AVAILABLE else None,
            examples=[
                {
                    "title": "Get pull request",
                    "config": {"repo_name": "owner/repo", "pull_number": 123}
                }
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        """Выполняет интеграцию используя PyGithub.

        Ожидает в `config`: `repo_name` (owner/repo) и `pull_number` (int)
        Получает credentials через credentials_resolver.get_default_for(...)
        """
        if not GITHUB_AVAILABLE:
            await logger.error("PyGithub library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "PyGithub library is not installed"
                }
            }

        # Получаем credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="gitverse",
            strategy="api_key"
        )

        if not creds:
            await logger.error("Gitverse credentials not found")
            return {
                "response": {"ok": False, "error_code": 401, "description": "Gitverse API key not found in credentials"}
            }

        payload = creds.get("payload", {}) or creds
        token = payload.get("token") or payload.get("access_token") or payload.get("api_key") or payload.get("apiKey")
        if not token:
            await logger.error(f"API token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {"ok": False, "error_code": 401, "description": "API token not found in credentials"}
            }

        # Проверяем входные параметры
        repo_name = config.get("repo_name")
        pull_number = config.get("pull_number")

        if not repo_name or not pull_number:
            await logger.error("repo_name and pull_number are required")
            return {
                "response": {"ok": False, "error_code": 400, "description": "repo_name and pull_number are required"}
            }

        # Используем PyGithub напрямую
        try:
            gh = Github(login_or_token=str(token))
            repo = gh.get_repo(str(repo_name))
            pr = repo.get_pull(int(pull_number))

            # Попытаемся собрать полезную информацию
            try:
                merged = pr.merged if hasattr(pr, "merged") else (pr.is_merged() if hasattr(pr, "is_merged") else None)
            except Exception:
                # is_merged() делает отдельный запрос и может упасть
                merged = None

            result = {
                "id": getattr(pr, "id", None),
                "number": getattr(pr, "number", None),
                "title": getattr(pr, "title", None),
                "body": getattr(pr, "body", None),
                "state": getattr(pr, "state", None),
                "merged": merged,
                "merged_at": getattr(pr, "merged_at", None),
                "user": {"login": pr.user.login} if getattr(pr, "user", None) else None,
                "created_at": getattr(pr, "created_at", None),
                "updated_at": getattr(pr, "updated_at", None),
                "labels": [label.name for label in getattr(pr, "labels", [])]
            }

            return {"response": {"ok": True, "result": result}}

        except GithubException as e:
            await logger.error(f"GitHub API error: {e}")
            return {
                "response": {"ok": False, "error_code": 502, "description": str(e)}
            }
        except Exception as e:
            await logger.error(f"Unexpected error while fetching PR: {e}")
            return {
                "response": {"ok": False, "error_code": 500, "description": str(e)}
            }


# Регистрируем интеграцию
registry.register(GitverseGetMergeRequestIntegration())
