from typing import Optional
from uuid import UUID
from app.api.dependencies.db import SessionDep

from fastapi import (Depends, Query)
from .base import AuthWebsocketBase


class AuthWebsocketChannel(AuthWebsocketBase):
    @classmethod
    def authorize(cls, entity_type: str = "channel") -> Depends:
        async def dependency(session: SessionDep, channel_id: str | UUID = Query(...),
                             token: str = Query(...)) -> Optional[dict]:
            return await cls._authorize(session, channel_id, token, entity_type)

        return Depends(dependency)
