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

    async def get_default_for(self, *, bot_id: UUID, provider: str, strategy: str | None) -> Optional[Mapping[str, Any]]:
        data = await self.dm.resolve_default_credential(str(bot_id), provider, strategy)
        return data or None

    async def get_single_for(self, *, bot_id: UUID, provider: str, strategy: str | None) -> Optional[Mapping[str, Any]]:
        data = await self.dm.resolve_default_credential(str(bot_id), provider, strategy)
        if data:
            return data
        data = await self.dm.resolve_singleton_credential(str(bot_id), provider, strategy)
        return data or None
