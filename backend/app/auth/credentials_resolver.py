from __future__ import annotations
from typing import Optional, Mapping, Any
from uuid import UUID


class CredentialsResolver:
    """Адаптер для AuthService: смотрит в БД через DataManager и возвращает расшифрованные креды."""

    def __init__(self, dm):
        self.dm = dm

    async def get_by_id(self, cred_id: UUID) -> Optional[Mapping[str, Any]]:
        data = await self.dm.get_credential_internal_by_id(str(cred_id))
        return data or None

    @staticmethod
    def _provider_aliases(provider: str) -> list[str]:
        # Backward compatibility / UX fallback:
        # users could have saved provider-specific creds under "other" before the provider existed in UI.
        if provider == "newsapi":
            return ["other"]
        if provider == "google_maps":
            return ["other", "google"]
        return []

    @staticmethod
    def _payload_has_required_keys(provider: str, payload: Mapping[str, Any]) -> bool:
        # Avoid accidentally using unrelated "other" credentials.
        if provider == "newsapi":
            return bool(payload.get("api_key") or payload.get("key") or payload.get("token"))
        if provider == "google_maps":
            return bool(payload.get("api_key") or payload.get("key"))
        return True

    async def get_default_for(self, *, bot_id: UUID, provider: str, strategy: str | None) -> Optional[Mapping[str, Any]]:
        candidates = [provider, *self._provider_aliases(provider)]
        for candidate_provider in candidates:
            data = await self.dm.resolve_default_credential(str(bot_id), candidate_provider, strategy)
            if not data:
                # UX-фоллбек: если default не выставлен, но credential(ы) существуют,
                # берём "самый подходящий" (в DataManager это is_default DESC, updated_at DESC).
                data = await self.dm.resolve_singleton_credential(str(bot_id), candidate_provider, strategy)

            if not data:
                continue

            payload = data.get("payload") or data
            if self._payload_has_required_keys(provider, payload):
                return data

        return None

    async def get_single_for(self, *, bot_id: UUID, provider: str, strategy: str | None) -> Optional[Mapping[str, Any]]:
        data = await self.dm.resolve_default_credential(str(bot_id), provider, strategy)
        if data:
            return data
        data = await self.dm.resolve_singleton_credential(str(bot_id), provider, strategy)
        return data or None
