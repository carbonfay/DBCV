from __future__ import annotations
import time
from typing import Optional, Tuple, Dict
from app.auth.types import AccessToken


class TokenCache:
    """
    Простой in-memory кеш access-токенов.
    Ключ строю из (bot_id, provider, profile, strategy, scopes_fingerprint).
    """

    def __init__(self):
        self._store: Dict[Tuple[str, str, str, str, str], AccessToken] = {}

    @staticmethod
    def _fingerprint_scopes(scopes: Optional[list[str]]) -> str:
        if not scopes:
            return ""
        return ",".join(sorted(s.strip() for s in scopes if s and s.strip()))

    @staticmethod
    def _now() -> float:
        return time.time()

    def get(
        self,
        *,
        bot_id: str,
        provider: str,
        profile: str,
        strategy: str,
        scopes: Optional[list[str]] = None,
    ) -> Optional[AccessToken]:
        key = (bot_id, provider, profile, strategy, self._fingerprint_scopes(scopes))
        token = self._store.get(key)
        if not token:
            return None
        if token.expires_at and token.expires_at <= (self._now() + 30):  # 30 сек запас
            # протух — удаляю
            self._store.pop(key, None)
            return None
        return token

    def put(
        self,
        *,
        bot_id: str,
        provider: str,
        profile: str,
        strategy: str,
        scopes: Optional[list[str]],
        token: AccessToken,
    ) -> None:
        key = (bot_id, provider, profile, strategy, self._fingerprint_scopes(scopes))
        self._store[key] = token
