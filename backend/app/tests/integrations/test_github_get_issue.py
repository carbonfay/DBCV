"""Тесты для GitHub Get Issue интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.github.get_issue import GitHubGetIssueIntegration, HTTPX_AVAILABLE
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture(scope="session", autouse=True)
async def engine():
    """Override heavy DB engine fixture to avoid the missing testing.postgresql dependency."""

    class _DummyBeginContext:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def run_sync(self, func):
            return None

    class _DummyEngine:
        async def begin(self):
            return _DummyBeginContext()

        async def connect(self):
            raise RuntimeError("Database access is not expected in GitHub integration tests")

        async def dispose(self):
            return None

    dummy_engine = _DummyEngine()
    yield dummy_engine
    await dummy_engine.dispose()


@pytest.fixture
def integration():
    return GitHubGetIssueIntegration()


@pytest.fixture
def credentials_resolver():
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={"payload": {"token": "ghp_test_token"}})
    resolver.get_by_id = AsyncMock(return_value=None)
    return resolver


@pytest.fixture
def logger():
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")


def test_github_metadata(integration):
    metadata = integration.metadata

    assert metadata.id == "github_get_issue"
    assert metadata.version == "1.0.0"
    assert metadata.category == "github"
    assert metadata.credentials_provider == "other"
    assert metadata.credentials_strategy == "api_key"


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx is required for this test")
@pytest.mark.asyncio
async def test_execute_success(integration, credentials_resolver, logger, bot_id):
    issue_payload = {
        "id": 1,
        "node_id": "MDU6SXNzdWUx",
        "number": 1347,
        "title": "Found a bug",
        "state": "open",
        "state_reason": None,
        "locked": False,
        "user": {
            "id": 1,
            "login": "octocat",
            "type": "User",
            "html_url": "https://github.com/octocat",
            "avatar_url": "https://avatars.githubusercontent.com/u/1?v=4"
        },
        "labels": [{"id": 208045946, "name": "bug", "color": "f29513", "description": "Something isn't working"}],
        "assignees": [],
        "milestone": None,
        "body": "I'm having a problem with this.",
        "body_text": "I'm having a problem with this.",
        "url": "https://api.github.com/repos/octocat/Hello-World/issues/1347",
        "html_url": "https://github.com/octocat/Hello-World/issues/1347",
        "comments": 1,
        "created_at": "2011-04-22T13:33:48Z",
        "updated_at": "2011-04-22T13:33:48Z",
        "closed_at": None,
        "pull_request": None,
        "reactions": {"+1": 0},
        "timeline_url": "https://api.github.com/repos/octocat/Hello-World/issues/1347/timeline",
        "author_association": "OWNER"
    }

    issue_response = MagicMock()
    issue_response.status_code = 200
    issue_response.json.return_value = issue_payload
    issue_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Reset": "1700000000"
    }

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=issue_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.integrations.github.get_issue.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={
                "owner": "octocat",
                "repo": "Hello-World",
                "issue_number": 1347
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is True
    issue = result["response"]["result"]["issue"]
    assert issue["title"] == "Found a bug"
    assert issue["repository"]["owner"] == "octocat"
    assert issue["comments_total"] == 1
    assert "comments" not in issue  # Комментарии больше не загружаются
    assert result["response"]["result"]["rate_limit"]["limit"] == 5000


@pytest.mark.asyncio
async def test_execute_no_credentials(integration, logger, bot_id):
    resolver = MagicMock(spec=CredentialsResolver)
    # Ищет только для provider="other"
    resolver.get_default_for = AsyncMock(return_value=None)
    resolver.get_by_id = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "issue_number": 1},
        credentials_resolver=resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx is required for this test")
@pytest.mark.asyncio
async def test_execute_issue_not_found(integration, credentials_resolver, logger, bot_id):
    issue_response = MagicMock()
    issue_response.status_code = 404
    issue_response.json.return_value = {"message": "Not Found"}
    issue_response.headers = {}

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=issue_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.integrations.github.get_issue.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={"owner": "octocat", "repo": "Hello-World", "issue_number": 999},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 404


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx is required for this test")
@pytest.mark.asyncio
async def test_execute_with_credentials_id(integration, credentials_resolver, logger, bot_id):
    custom_cred_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    credentials_resolver.get_by_id.return_value = {"payload": {"token": "ghp_custom"}}

    issue_payload = {
        "id": 5,
        "number": 10,
        "title": "Issue with explicit creds",
        "state": "open",
        "user": {"id": 3},
        "labels": [],
        "assignees": [],
        "milestone": None,
        "body": "",
        "body_text": "",
        "url": "https://api.github.com/repos/octocat/Hello-World/issues/10",
        "html_url": "https://github.com/octocat/Hello-World/issues/10",
        "comments": 0,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "closed_at": None,
        "pull_request": None,
        "reactions": {},
        "timeline_url": "",
        "author_association": "NONE"
    }

    issue_response = MagicMock()
    issue_response.status_code = 200
    issue_response.json.return_value = issue_payload
    issue_response.headers = {}

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=issue_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.integrations.github.get_issue.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={
                "owner": "octocat",
                "repo": "Hello-World",
                "issue_number": 10,
                "credentials_id": str(custom_cred_id)
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is True
    credentials_resolver.get_by_id.assert_awaited_once_with(custom_cred_id)
    # get_default_for не должен вызываться, если указан credentials_id
    assert credentials_resolver.get_default_for.await_count == 0


@pytest.mark.asyncio
async def test_execute_invalid_credentials_id(integration, credentials_resolver, logger, bot_id):
    result = await integration.execute(
        config={
            "owner": "octocat",
            "repo": "Hello-World",
            "issue_number": 1,
            "credentials_id": "invalid-uuid"
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert credentials_resolver.get_by_id.await_count == 0
    assert credentials_resolver.get_default_for.await_count == 0


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx is required for this test")
@pytest.mark.asyncio
async def test_execute_other_provider(integration, credentials_resolver, logger, bot_id):
    # Использует только provider="other"
    credentials_resolver.get_default_for = AsyncMock(return_value={"payload": {"token": "ghp_other"}})

    issue_payload = {
        "id": 6,
        "number": 20,
        "title": "Issue with other provider",
        "state": "open",
        "user": {"id": 4},
        "labels": [],
        "assignees": [],
        "milestone": None,
        "body": "",
        "body_text": "",
        "url": "https://api.github.com/repos/octocat/Hello-World/issues/20",
        "html_url": "https://github.com/octocat/Hello-World/issues/20",
        "comments": 0,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "closed_at": None,
        "pull_request": None,
        "reactions": {},
        "timeline_url": "",
        "author_association": "NONE"
    }

    issue_response = MagicMock()
    issue_response.status_code = 200
    issue_response.json.return_value = issue_payload
    issue_response.headers = {}

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=issue_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.integrations.github.get_issue.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={"owner": "octocat", "repo": "Hello-World", "issue_number": 20},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is True
    # Должен вызвать get_default_for один раз для provider="other"
    assert credentials_resolver.get_default_for.await_count == 1
    assert result["response"]["result"]["issue"]["number"] == 20
