"""Wildberries API Key Provider."""
from __future__ import annotations

import time
from typing import Any, Mapping, Optional

from app.auth.types import AccessToken


class WildberriesProvider:
    """
    Провайдер для Wildberries API ключей.
    
    Поддерживает простую стратегию с API ключом.
    В payload ожидаю:
      - api_token: "your_api_key_here"
      (опционально) api_key: для обратной совместимости
    """

    async def ensure(
        self,
        *,
        bot_id: str,
        profile: str,
        creds_cfg: Mapping[str, Any],
        profile_state: Optional[Mapping[str, Any]],
        hints: Mapping[str, Any],
        cache,
    ) -> AccessToken:
        """Убедиться что у нас есть валидный API ключ."""
        provider = "wildberries"
        strategy = str(creds_cfg.get("strategy", "api_key"))
        scopes = None

        # Проверить кеш
        cached = cache.get(bot_id=bot_id, provider=provider, profile=profile, strategy=strategy, scopes=scopes)
        if cached:
            return cached

        # Получить API ключ из payload
        payload = creds_cfg.get("payload", {})
        api_token = payload.get("api_token") or payload.get("api_key")
        
        if not api_token:
            raise RuntimeError("wildberries: missing api_token or api_key in payload")

        # Для API ключа просто создаем токен с длительным сроком действия
        # API ключи не имеют срока действия, но добавляем для совместимости
        expires_at = time.time() + (365 * 24 * 3600)  # год в секундах
        
        token = AccessToken(
            token_type="Bearer",
            access_token=api_token,
            expires_at=expires_at
        )
        
        # Кешировать токен
        cache.put(
            bot_id=bot_id,
            provider=provider,
            profile=profile,
            strategy=strategy,
            scopes=scopes,
            token=token
        )
        
        return token

    def apply_headers(self, headers: dict, token: AccessToken, hints: Mapping[str, Any]) -> None:
        """Применить токен в заголовки."""
        headers["Authorization"] = f"{token.token_type} {token.access_token}"
