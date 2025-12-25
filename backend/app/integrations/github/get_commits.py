"""GitHub Get Commits интеграция используя PyGithub библиотеку."""
from typing import Dict, Any, List
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


class GitHubGetCommitsIntegration(BaseIntegration):
    """Интеграция для получения списка коммитов из репозитория GitHub через PyGithub."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_get_commits",
            version="1.0.0",
            name="GitHub Get Commits",
            description="Получить список коммитов из репозитория GitHub с фильтрацией по ветке и количеству",
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
                    },
                    "branch": {
                        "type": "string",
                        "title": "Branch Name",
                        "description": "Имя ветки (опционально, если не указано - используется default ветка репозитория)"
                    },
                    "limit": {
                        "type": "integer",
                        "title": "Limit",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                        "description": "Максимальное количество коммитов для получения (1-100, по умолчанию 10)"
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="PyGithub>=1.55" if PYGITHUB_AVAILABLE else None,
            examples=[
                {
                    "title": "Get recent commits from main branch",
                    "config": {
                        "full_name": "octocat/Hello-World",
                        "limit": 5
                    }
                },
                {
                    "title": "Get commits from specific branch",
                    "config": {
                        "full_name": "octocat/Hello-World",
                        "branch": "develop",
                        "limit": 10
                    }
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
        Выполняет запрос к GitHub и возвращает список коммитов из репозитория.

        Args:
            config: Параметры интеграции
                - full_name: Полное имя репозитория (обязательно)
                - branch: Имя ветки (опционально)
                - limit: Количество коммитов для получения (опционально, по умолчанию 10)
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
        branch = config.get("branch")
        limit = config.get("limit", 10)

        if not full_name:
            await logger.error("full_name is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "full_name (owner/repo) is required"
                }
            }

        # Валидация limit
        try:
            limit = int(limit)
            if limit < 1 or limit > 100:
                limit = 10
        except (ValueError, TypeError):
            limit = 10

        # Получаем credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
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
            # Добавляем api_key в начало, так как это основное поле для этой стратегии
            token = (
                payload.get("api_key") or 
                payload.get("access_token") or 
                payload.get("token") or 
                payload.get("pat")
            )
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

            # Получаем коммиты с указанной ветки или default
            if branch:
                commits = repo.get_commits(sha=branch)
            else:
                commits = repo.get_commits()

            # Собираем информацию о коммитах
            commits_data: List[Dict[str, Any]] = []
            for i, commit in enumerate(commits):
                if i >= limit:
                    break

                commit_info = {
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": {
                        "name": commit.commit.author.name,
                        "email": commit.commit.author.email,
                        "date": commit.commit.author.date.isoformat() if commit.commit.author.date else None
                    },
                    "committer": {
                        "name": commit.commit.committer.name,
                        "email": commit.commit.committer.email,
                        "date": commit.commit.committer.date.isoformat() if commit.commit.committer.date else None
                    },
                    "url": commit.html_url,
                    "parents_count": len(commit.parents)
                }
                commits_data.append(commit_info)

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "commits": commits_data,
                        "count": len(commits_data),
                        "repository": {
                            "full_name": repo.full_name,
                            "branch_used": branch or repo.default_branch
                        }
                    }
                }
            }

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
            await logger.error(f"Unexpected error in GitHub get_commits integration: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
