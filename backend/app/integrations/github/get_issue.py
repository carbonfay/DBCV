"""GitHub Get Issue интеграция используя PyGithub библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    from github import Github
    from github.GithubException import GithubException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    Github = None
    GithubException = Exception


class GitHubGetIssueIntegration(BaseIntegration):
    """Интеграция для получения информации об Issue на GitHub."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_get_issue",
            version="1.0.0",
            name="GitHub Get Issue",
            description="Получение информации об Issue на GitHub: статус, описание, комментарии, автор и т.д.",
            category="integration",
            icon_s3_key="icons/integrations/github.svg",
            color="#ffffff",
            config_schema={
                "type": "object",
                "required": ["owner", "repo", "issue_number"],
                "properties": {
                    "owner": {
                        "type": "string",
                        "title": "Repository Owner",
                        "description": "Владелец репозитория (username или организация)"
                    },
                    "repo": {
                        "type": "string",
                        "title": "Repository Name",
                        "description": "Название репозитория"
                    },
                    "issue_number": {
                        "type": "integer",
                        "title": "Issue Number",
                        "description": "Номер Issue"
                    }
                }
            },
            credentials_provider="github",
            credentials_strategy="api_key",
            library_name="PyGithub>=2.0.0" if GITHUB_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить Issue из репозитория",
                    "config": {
                        "owner": "carbonfay",
                        "repo": "DBCV",
                        "issue_number": 1
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
        Выполняет интеграцию используя библиотеку PyGithub.
        
        Args:
            config: Параметры интеграции (owner, repo, issue_number)
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
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
        
        # Получаем token из credentials
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
        
        # Credentials возвращаются с ключом "payload"
        payload = creds.get("payload", {})
        if not payload:
            payload = creds
        
        token = payload.get("token") or payload.get("access_token")
        if not token:
            await logger.error(f"token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "token not found in credentials"
                }
            }
        
        # Получаем параметры из config
        owner = config.get("owner", "").strip()
        repo = config.get("repo", "").strip()
        issue_number = config.get("issue_number")
        
        # Валидация параметров
        if not owner or not repo or not issue_number:
            await logger.error("owner, repo and issue_number are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "owner, repo and issue_number are required"
                }
            }
        
        if not isinstance(issue_number, int) or issue_number <= 0:
            await logger.error("issue_number must be a positive integer")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "issue_number must be a positive integer"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем Github клиент с access token
            g = Github(token)
            
            # Получаем репозиторий
            repo_obj = g.get_user(owner).get_repo(repo)
            
            # Получаем Issue по номеру
            issue = repo_obj.get_issue(issue_number)
            
            # Формируем результат с основной информацией об Issue
            result = {
                "id": issue.id,
                "number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "state": issue.state,
                "state_reason": issue.state_reason,
                "user": {
                    "login": issue.user.login,
                    "id": issue.user.id,
                    "avatar_url": issue.user.avatar_url,
                    "url": issue.user.html_url
                },
                "created_at": issue.created_at.isoformat() if issue.created_at else None,
                "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                "comments": issue.comments,
                "labels": [label.name for label in issue.labels],
                "assignees": [assignee.login for assignee in issue.assignees],
                "url": issue.html_url,
                "api_url": issue.url
            }
            
            await logger.debug(f"Successfully fetched issue #{issue_number} from {owner}/{repo}")
            
            return {
                "response": {
                    "ok": True,
                    "result": result
                }
            }
        
        except GithubException as e:
            # Обработка ошибок GitHub API
            error_msg = str(e)
            error_code = e.status if hasattr(e, 'status') else 500
            
            await logger.error(f"GitHub API error: {error_msg}")
            
            # Определяем более специфичный код ошибки
            if error_code == 404:
                description = f"Issue #{issue_number} not found in {owner}/{repo}"
            elif error_code == 403:
                description = "Access denied to repository (check token permissions)"
            elif error_code == 401:
                description = "Invalid GitHub token"
            else:
                description = error_msg
            
            return {
                "response": {
                    "ok": False,
                    "error_code": error_code,
                    "description": description
                }
            }
        
        except Exception as e:
            # Обработка неожиданных ошибок
            error_msg = str(e)
            await logger.error(f"Unexpected error: {error_msg}")
            
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Unexpected error: {error_msg}"
                }
            }
