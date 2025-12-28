"""Тесты для интеграции Moodle Get Courses."""
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.auth.credentials_resolver import CredentialsResolver
from app.integrations.moodle.get_courses import MoodleGetCoursesIntegration
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр интеграции Moodle."""
    return MoodleGetCoursesIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock для credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "base_url": "https://moodle.example",
            "token": "test-token",
        }
    })
    return resolver


@pytest.fixture
def logger():
    """Создает mock логгера."""
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    """Фиксированный bot_id для тестов."""
    return UUID("12345678-1234-5678-1234-567812345678")


def test_moodle_metadata(integration):
    """Проверяет базовые метаданные интеграции."""
    metadata = integration.metadata

    assert metadata.id == "moodle_get_courses"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Moodle Get Courses"
    assert metadata.category == "education"
    assert metadata.credentials_provider == "moodle"
    assert metadata.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_moodle_execute_ids_success(integration, credentials_resolver, logger, bot_id):
    """Проверяет получение курсов по списку ID."""
    with patch(
        "app.integrations.moodle.get_courses._fetch_moodle_json",
        new=AsyncMock(return_value=([{"id": 10}], None)),
    ) as mock_fetch:
        result = await integration.execute(
            config={"ids": [10]},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["courses"] == [{"id": 10}]

    endpoint, params, _logger = mock_fetch.await_args.args
    assert endpoint == "https://moodle.example/webservice/rest/server.php"
    assert params["wsfunction"] == "core_course_get_courses"
    assert params["options[ids][0]"] == 10


@pytest.mark.asyncio
async def test_moodle_execute_field_success(integration, credentials_resolver, logger, bot_id):
    """Проверяет получение курсов по полю и значению."""
    response_data = {"courses": [{"id": 1}], "warnings": [{"warningcode": "test"}]}
    with patch(
        "app.integrations.moodle.get_courses._fetch_moodle_json",
        new=AsyncMock(return_value=(response_data, None)),
    ) as mock_fetch:
        result = await integration.execute(
            config={"field": "shortname", "value": "course-1"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["courses"] == [{"id": 1}]
    assert result["response"]["result"]["warnings"] == [{"warningcode": "test"}]

    endpoint, params, _logger = mock_fetch.await_args.args
    assert endpoint == "https://moodle.example/webservice/rest/server.php"
    assert params["wsfunction"] == "core_course_get_courses_by_field"
    assert params["field"] == "shortname"
    assert params["value"] == "course-1"


@pytest.mark.asyncio
async def test_moodle_execute_include_site_info(integration, credentials_resolver, logger, bot_id):
    """Проверяет добавление site_info в результат."""
    fetch_side_effect = [
        ({"sitename": "Test"}, None),
        ([{"id": 42}], None),
    ]
    with patch(
        "app.integrations.moodle.get_courses._fetch_moodle_json",
        new=AsyncMock(side_effect=fetch_side_effect),
    ) as mock_fetch:
        result = await integration.execute(
            config={"include_site_info": True},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["courses"] == [{"id": 42}]
    assert result["response"]["result"]["site_info"] == {"sitename": "Test"}
    assert mock_fetch.await_count == 2


@pytest.mark.asyncio
async def test_moodle_execute_invalid_config(integration, credentials_resolver, logger, bot_id):
    """Проверяет ошибку при одновременном ids и field/value."""
    result = await integration.execute(
        config={"ids": [1], "field": "shortname", "value": "course"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_moodle_execute_no_credentials(integration, logger, bot_id):
    """Проверяет ошибку при отсутствии credentials."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={},
        credentials_resolver=resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
