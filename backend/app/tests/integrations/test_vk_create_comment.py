import sys
from unittest.mock import MagicMock

# Mock problematic modules before importing
sys.modules['app.broker'] = MagicMock()
sys.modules['app.loggers'] = MagicMock()
sys.modules['app.loggers.bot'] = MagicMock()
sys.modules['app.auth.credentials_resolver'] = MagicMock()
sys.modules['app.integrations.base'] = MagicMock()

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.vk.create_comment import VkCreateCommentIntegration


@pytest.mark.asyncio
async def test_vk_create_comment_success():
    integration = VkCreateCommentIntegration()

    config = {
        "owner_id": -1,
        "post_id": 123,
        "message": "Тестовый комментарий",
        "from_group": True
    }

    bot_id = uuid4()

    credentials_resolver = AsyncMock()
    credentials_resolver.get_default_for.return_value = {
        "payload": {
            "access_token": "fake_token"
        }
    }

    logger = AsyncMock()

    with patch("vk_api.VkApi") as vk_api_mock:
        vk_instance = MagicMock()
        vk_instance.method.return_value = {
            "comment_id": 999
        }

        vk_api_mock.return_value = vk_instance

        result = await integration.execute(
            config=config,
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["comment_id"] == 999

    vk_instance.method.assert_called_once_with(
        "wall.createComment",
        {
            "owner_id": -1,
            "post_id": 123,
            "message": "Тестовый комментарий",
            "from_group": 1
        }
    )


@pytest.mark.asyncio
async def test_vk_create_comment_missing_required_fields():
    integration = VkCreateCommentIntegration()

    config = {
        "owner_id": -1,
        # missing post_id and message
    }

    bot_id = uuid4()
    credentials_resolver = AsyncMock()
    logger = AsyncMock()

    result = await integration.execute(
        config=config,
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "required" in result["response"]["description"]
    logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_vk_create_comment_no_access_token():
    integration = VkCreateCommentIntegration()

    config = {
        "owner_id": -1,
        "post_id": 123,
        "message": "Тестовый комментарий"
    }

    bot_id = uuid4()

    credentials_resolver = AsyncMock()
    credentials_resolver.get_default_for.return_value = None

    logger = AsyncMock()

    result = await integration.execute(
        config=config,
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "access_token not found" in result["response"]["description"]
    logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_vk_create_comment_vk_api_error():
    integration = VkCreateCommentIntegration()

    config = {
        "owner_id": -1,
        "post_id": 123,
        "message": "Тестовый комментарий",
        "access_token": "fake_token"
    }

    bot_id = uuid4()
    credentials_resolver = AsyncMock()
    logger = AsyncMock()

    with patch("vk_api.VkApi") as vk_api_mock:
        vk_instance = MagicMock()
        vk_instance.method.side_effect = Exception("VK API Error")

        vk_api_mock.return_value = vk_instance

        result = await integration.execute(
            config=config,
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500
    assert "VK API Error" in result["response"]["description"]
    logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_vk_create_comment_from_group_false():
    integration = VkCreateCommentIntegration()

    config = {
        "owner_id": 12345,
        "post_id": 123,
        "message": "Тестовый комментарий",
        "from_group": False,
        "access_token": "fake_token"
    }

    bot_id = uuid4()
    credentials_resolver = AsyncMock()
    logger = AsyncMock()

    with patch("vk_api.VkApi") as vk_api_mock:
        vk_instance = MagicMock()
        vk_instance.method.return_value = {
            "comment_id": 1000
        }

        vk_api_mock.return_value = vk_instance

        result = await integration.execute(
            config=config,
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["comment_id"] == 1000

    vk_instance.method.assert_called_once_with(
        "wall.createComment",
        {
            "owner_id": 12345,
            "post_id": 123,
            "message": "Тестовый комментарий"
        }
    )


@pytest.mark.asyncio
async def test_vk_create_comment_vk_api_not_available():
    with patch("app.integrations.vk.create_comment.VK_API_AVAILABLE", False):
        integration = VkCreateCommentIntegration()

        config = {
            "owner_id": -1,
            "post_id": 123,
            "message": "Тестовый комментарий",
            "access_token": "fake_token"
        }

        bot_id = uuid4()
        credentials_resolver = AsyncMock()
        logger = AsyncMock()

        result = await integration.execute(
            config=config,
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "vk-api library is not installed" in result["response"]["description"]
        logger.error.assert_called_once()
