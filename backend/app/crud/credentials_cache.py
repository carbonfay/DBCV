from __future__ import annotations

import logging
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


async def invalidate_credential_cache(
    redis: Redis,
    bot_id: str,
    provider: str,
    strategy: str
) -> None:
    """
    Инвалидирует кэш credentials для указанного bot_id, provider и strategy.
    
    Args:
        redis: Подключение к Redis для работы с кэшем
        bot_id: ID бота
        provider: Провайдер credentials
        strategy: Стратегия credentials
    """
    try:
        cache_keys = [
            f"credential:bot:{bot_id}:provider:{provider}:strategy:{strategy}:default",
            f"credential:bot:{bot_id}:provider:{provider}:strategy:{strategy}:singleton"
        ]
        deleted_count = await redis.delete(*cache_keys)
        if deleted_count > 0:
            logger.debug(
                f"Invalidated credential cache for bot_id={bot_id}, "
                f"provider={provider}, strategy={strategy}. "
                f"Deleted {deleted_count} key(s)"
            )
    except Exception as e:
        logger.error(
            f"Failed to invalidate credential cache for bot_id={bot_id}, "
            f"provider={provider}, strategy={strategy}: {e}",
            exc_info=True
        )
        # Не пробрасываем исключение, чтобы не ломать основную логику

