from typing import Optional, Annotated
from uuid import UUID
from app.api.dependencies.db import SessionDep
from app.api.dependencies.strategies.factory import AuthStrategyFactory
from fastapi import (Depends, Query, WebSocketException, status)
from app.api.dependencies.auth import get_token_data
import logging

logger = logging.getLogger(__name__)


class AuthWebsocketBase:
    @staticmethod
    async def _authorize(session: SessionDep,
                         entity_id: str | UUID = Query(...),
                         token: str = Query(...),
                         entity_type: str = Query(...)
                         ) -> Optional[dict]:
        try:
            token_data = get_token_data(token)
            strategy = AuthStrategyFactory.get_strategy(entity_type)
            return await strategy.authorize(session, entity_id, token_data)
        except WebSocketException as e:
            await session.close()
            logger.warning(f"Ошибка авторизации WebSocket: {e.code} - {e.reason}")
            raise
        except Exception as e:
            await session.close()
            logger.error(f"Непредвиденная ошибка авторизации WebSocket: {e}")
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Ошибка авторизации")
        finally:
            await session.close()
