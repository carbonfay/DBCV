"""GitHub Update Issue интеграция используя PyGithub библиотеку."""
from typing import Dict, Any, TYPE_CHECKING, Optional, List
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata

if TYPE_CHECKING:
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


class GitHubUpdateIssueIntegration(BaseIntegration):
    """Интеграция для обновления Issue на GitHub (PATCH /repos/{owner}/{repo}/issues/{issue_number})."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_update_issue",
            version="1.0.0",
            name="GitHub Update Issue",
            description="Обновление информации об Issue на GitHub: название, описание, статус, labels, assignees",
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
                        "description": "Номер Issue для обновления"
                    },
                    "title": {
                        "type": "string",
                        "title": "Issue Title",
                        "description": "Новое название Issue (опционально)"
                    },
                    "body": {
                        "type": "string",
                        "title": "Issue Body",
                        "description": "Новое описание Issue (опционально)"
                    },
                    "state": {
                        "type": "string",
                        "title": "Issue State",
                        "enum": ["open", "closed"],
                        "description": "Новый статус Issue (open или closed)"
                    },
                    "state_reason": {
                        "type": "string",
                        "title": "State Reason",
                        "enum": ["completed", "not_planned"],
                        "description": "Причина закрытия Issue (если state=closed)"
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "title": "Labels",
                        "description": "Список новых labels для Issue"
                    },
                    "assignees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "title": "Assignees",
                        "description": "Список новых assignees для Issue (username)"
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="none",
            library_name="PyGithub>=2.0.0" if GITHUB_AVAILABLE else None,
            examples=[
                {
                    "title": "Обновить название Issue",
                    "config": {
                        "owner": "carbonfay",
                        "repo": "DBCV",
                        "issue_number": 1,
                        "title": "Новое название"
                    }
                },
                {
                    "title": "Закрыть Issue и добавить labels",
                    "config": {
                        "owner": "carbonfay",
                        "repo": "DBCV",
                        "issue_number": 1,
                        "state": "closed",
                        "state_reason": "completed",
                        "labels": ["bug", "fixed"]
                    }
                },
                {
                    "title": "Добавить assignees к Issue",
                    "config": {
                        "owner": "carbonfay",
                        "repo": "DBCV",
                        "issue_number": 1,
                        "assignees": ["user1", "user2"]
                    }
                }
            ]
        )
    
    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: "CredentialsResolver",
        bot_id: UUID,
        logger: "BotLogger"
    ) -> Dict[str, Any]:
        """
        Выполняет интеграцию обновления Issue используя библиотеку PyGithub.
        
        Args:
            config: Параметры интеграции (owner, repo, issue_number и параметры для обновления)
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
        
        # Валидация обязательных параметров
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
        
        # Получаем параметры для обновления (все опциональны)
        title = config.get("title")
        body = config.get("body")
        state = config.get("state")
        state_reason = config.get("state_reason")
        labels = config.get("labels", [])
        assignees = config.get("assignees", [])
        
        # Проверяем что хотя бы один параметр для обновления предоставлен
        has_update_params = any([
            title is not None,
            body is not None,
            state is not None,
            labels,
            assignees
        ])
        
        if not has_update_params:
            await logger.error("At least one update parameter must be provided (title, body, state, labels, assignees)")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "At least one update parameter must be provided"
                }
            }
        
        # Валидация state
        if state is not None and state not in ["open", "closed"]:
            await logger.error("state must be 'open' or 'closed'")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "state must be 'open' or 'closed'"
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
            
            # Подготавливаем параметры для обновления
            update_params = {}
            
            if title is not None:
                update_params['title'] = title
            
            if body is not None:
                update_params['body'] = body
            
            if state is not None:
                update_params['state'] = state
                # state_reason используется только при закрытии issue
                if state == "closed" and state_reason is not None:
                    if state_reason not in ["completed", "not_planned"]:
                        await logger.error("state_reason must be 'completed' or 'not_planned'")
                        return {
                            "response": {
                                "ok": False,
                                "error_code": 400,
                                "description": "state_reason must be 'completed' or 'not_planned'"
                            }
                        }
                    update_params['state_reason'] = state_reason
            
            if labels:
                if not isinstance(labels, list):
                    await logger.error("labels must be a list")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": "labels must be a list"
                        }
                    }
                update_params['labels'] = labels
            
            if assignees:
                if not isinstance(assignees, list):
                    await logger.error("assignees must be a list")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": "assignees must be a list"
                        }
                    }
                update_params['assignees'] = assignees
            
            # Обновляем Issue
            issue.edit(**update_params)
            
            # Переполучаем обновленный Issue
            updated_issue = repo_obj.get_issue(issue_number)
            
            # Формируем результат с информацией об обновленном Issue
            result = {
                "id": updated_issue.id,
                "number": updated_issue.number,
                "title": updated_issue.title,
                "body": updated_issue.body,
                "state": updated_issue.state,
                "state_reason": updated_issue.state_reason,
                "user": {
                    "login": updated_issue.user.login,
                    "id": updated_issue.user.id,
                    "avatar_url": updated_issue.user.avatar_url,
                    "url": updated_issue.user.html_url
                },
                "created_at": updated_issue.created_at.isoformat() if updated_issue.created_at else None,
                "updated_at": updated_issue.updated_at.isoformat() if updated_issue.updated_at else None,
                "closed_at": updated_issue.closed_at.isoformat() if updated_issue.closed_at else None,
                "comments": updated_issue.comments,
                "labels": [label.name for label in updated_issue.labels],
                "assignees": [assignee.login for assignee in updated_issue.assignees],
                "url": updated_issue.html_url,
                "api_url": updated_issue.url
            }
            
            await logger.debug(f"Successfully updated issue #{issue_number} in {owner}/{repo}")
            
            return {
                "response": {
                    "ok": True,
                    "result": result
                }
            }
        
        except GithubException as e:
            error_msg = e.data.get("message", str(e)) if hasattr(e, 'data') else str(e)
            await logger.error(f"GitHub API error: {e.status if hasattr(e, 'status') else 'Unknown'} - {error_msg}")
            return {
                "response": {
                    "ok": False,
                    "error_code": getattr(e, 'status', 500),
                    "description": f"GitHub API error: {error_msg}"
                }
            }
        
        except Exception as e:
            await logger.error(f"Unexpected error: {str(e)}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Unexpected error: {str(e)}"
                }
            }
