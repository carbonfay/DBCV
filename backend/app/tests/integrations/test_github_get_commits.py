"""Тесты для интеграции GitHub Get Commits."""
import pytest
from unittest.mock import AsyncMock, patch
from uuid import UUID

from app.integrations.github.get_commits import GitHubGetCommitsIntegration
from app.auth.credentials_resolver import CredentialsResolver


@pytest.fixture
def integration():
    """Фикстура для интеграции GitHub Get Commits."""
    return GitHubGetCommitsIntegration()


@pytest.fixture
def mock_credentials_resolver():
    """Фикстура для мокирования CredentialsResolver."""
    resolver = AsyncMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={"payload": {"api_key": "test_token"}})
    return resolver


@pytest.fixture
def mock_logger():
    """Фикстура для мокирования BotLogger."""
    logger = AsyncMock()
    logger.error = AsyncMock()
    logger.info = AsyncMock()
    return logger


@pytest.mark.asyncio
async def test_github_get_commits_metadata(integration):
    """Тест метаданных интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "github_get_commits"
    assert metadata.version == "1.0.0"
    assert metadata.name == "GitHub Get Commits"
    assert metadata.category == "development"
    assert "owner" in metadata.config_schema["properties"]
    assert "repo" in metadata.config_schema["properties"]


@pytest.mark.asyncio
async def test_github_get_commits_missing_required_params(integration, mock_credentials_resolver, mock_logger):
    """Тест интеграции с отсутствующими обязательными параметрами."""
    config = {}
    bot_id = UUID(int=1)
    
    result = await integration.execute(
        config=config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=bot_id,
        logger=mock_logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "owner and repo are required" in result["response"]["description"]


@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_github_get_commits_success(mock_get, integration, mock_credentials_resolver, mock_logger):
    """Тест успешного выполнения интеграции."""
    # Подготовим mock ответ от API
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "sha": "abc123",
            "url": "https://api.github.com/repos/octocat/Hello-World/commits/abc123",
            "commit": {
                "message": "Initial commit",
                "author": {
                    "name": "Octocat",
                    "email": "octocat@github.com",
                    "date": "2023-01-01T00:00:00Z"
                },
                "committer": {
                    "name": "Octocat",
                    "email": "octocat@github.com",
                    "date": "2023-01-01T00:00:00Z"
                }
            },
            "author": {
                "login": "octocat",
                "id": 123456
            },
            "committer": {
                "login": "octocat",
                "id": 123456
            }
        }
    ]
    mock_get.return_value = mock_response
    
    config = {
        "owner": "octocat",
        "repo": "Hello-World"
    }
    bot_id = UUID(int=1)
    
    result = await integration.execute(
        config=config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=bot_id,
        logger=mock_logger
    )
    
    assert result["response"]["ok"] is True
    assert result["response"]["result"]["repository"]["owner"] == "octocat"
    assert result["response"]["result"]["repository"]["name"] == "Hello-World"
    assert len(result["response"]["result"]["commits"]) == 1


@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_github_get_commits_unauthorized(mock_get, integration, mock_credentials_resolver, mock_logger):
    """Тест обработки ошибки авторизации."""
    # Подготовим mock ответ с ошибкой авторизации
    mock_response = AsyncMock()
    mock_response.status_code = 401
    mock_response.text = "Bad credentials"
    mock_get.return_value = mock_response
    
    config = {
        "owner": "octocat",
        "repo": "Hello-World"
    }
    bot_id = UUID(int=1)
    
    result = await integration.execute(
        config=config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=bot_id,
        logger=mock_logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_github_get_commits_not_found(mock_get, integration, mock_credentials_resolver, mock_logger):
    """Тест обработки ошибки 'не найдено'."""
    # Подготовим mock ответ с ошибкой 'не найдено'
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_get.return_value = mock_response
    
    config = {
        "owner": "nonexistent",
        "repo": "nonexistent-repo"
    }
    bot_id = UUID(int=1)
    
    result = await integration.execute(
        config=config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=bot_id,
        logger=mock_logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 404


@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_github_get_commits_forbidden(mock_get, integration, mock_credentials_resolver, mock_logger):
    """Тест обработки ошибки 'запрещено'."""
    # Подготовим mock ответ с ошибкой 'запрещено'
    mock_response = AsyncMock()
    mock_response.status_code = 403
    mock_response.text = "API rate limit exceeded"
    mock_get.return_value = mock_response
    
    config = {
        "owner": "octocat",
        "repo": "Hello-World"
    }
    bot_id = UUID(int=1)
    
    result = await integration.execute(
        config=config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=bot_id,
        logger=mock_logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 403


@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_github_get_commits_http_error(mock_get, integration, mock_credentials_resolver, mock_logger):
    """Тест обработки HTTP ошибки."""
    # Симулируем исключение при HTTP запросе
    mock_get.side_effect = Exception("Network error")
    
    config = {
        "owner": "octocat",
        "repo": "Hello-World"
    }
    bot_id = UUID(int=1)
    
    result = await integration.execute(
        config=config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=bot_id,
        logger=mock_logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500