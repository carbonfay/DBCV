"""GitHub Get Repository интеграция используя PyGithub библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку напрямую
try:
    from github import Github
    from github.GithubException import GithubException
    PYGITHUB_AVAILABLE = True
except Exception:
    Github = None
    GithubException = Exception
    PYGITHUB_AVAILABLE = False


class GitHubGetRepositoryIntegration(BaseIntegration):
    """Интеграция для получения информации о репозитории GitHub через PyGithub."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_get_repository",
            version="1.0.0",
            name="GitHub Get Repository",
            description="Получить информацию о репозитории GitHub по его full_name (owner/repo)",
            category="developer_tools",
            icon_s3_key="icons/integrations/github.svg",
            color="#24292e",
            config_schema={
                "type": "object",
                "required": ["full_name"],
                "properties": {
                    "full_name": {
                        "type": "string",
                        "title": "Repository Full Name",
                        "description": "Полное имя репозитория в формате owner/repo, например: octocat/Hello-World"
                    }
                }
            },
            credentials_provider="github",
            credentials_strategy="api_key",
            library_name="PyGithub>=1.55" if PYGITHUB_AVAILABLE else None,
            examples=[
                {
                    "title": "Get repository info",
                    "config": {"full_name": "octocat/Hello-World"}
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
        """
        Выполняет запрос к GitHub через PyGithub и возвращает информацию о репозитории.

        Args:
            config: Ожидает ключ `full_name` (owner/repo)
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота
            logger: Логгер

        Returns:
            Результат в формате системы
        """
        if not PYGITHUB_AVAILABLE:
            await logger.error("PyGithub library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "PyGithub library is not installed"
                }
            }

        full_name = config.get("full_name")
        if not full_name:
            await logger.error("full_name is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "full_name (owner/repo) is required"
                }
            }

        # Получаем credentials (ожидаем api_key / token)
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="github",
            strategy="api_key"
        )

        if not creds:
            await logger.error("GitHub credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "GitHub token not found in credentials"
                }
            }

        payload = creds.get("payload", {}) if isinstance(creds, dict) else {}
        if not payload:
            payload = creds

        token = None
        if isinstance(payload, dict):
            # Common keys: access_token, token
            token = payload.get("access_token") or payload.get("token") or payload.get("pat")
        # fallback: if creds is string
        if not token and isinstance(creds, str):
            token = creds

        if not token:
            await logger.error("GitHub token not found in credentials payload")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "GitHub token not found in credentials"
                }
            }

        try:
            gh = Github(token)
            repo = gh.get_repo(full_name)

            result = {
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "private": repo.private,
                "html_url": repo.html_url,
                "clone_url": repo.clone_url,
                "ssh_url": getattr(repo, "ssh_url", None),
                "language": repo.language,
                "license": repo.license.name if repo.license else None,
                "owner": {
                    "login": repo.owner.login,
                    "id": repo.owner.id,
                    "type": repo.owner.type
                },
                "stargazers_count": repo.stargazers_count,
                "forks_count": repo.forks_count,
                "open_issues_count": repo.open_issues_count,
                "watchers_count": getattr(repo, "watchers_count", None),
                "created_at": repo.created_at.isoformat() if getattr(repo, "created_at", None) else None,
                "updated_at": repo.updated_at.isoformat() if getattr(repo, "updated_at", None) else None,
            }

            return {"response": {"ok": True, "result": result}}

        except GithubException as e:
            await logger.error(f"GitHub API error: {e}")
            status = getattr(e, 'status', None)
            return {
                "response": {
                    "ok": False,
                    "error_code": status or 500,
                    "description": str(e)
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error in GitHub integration: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
