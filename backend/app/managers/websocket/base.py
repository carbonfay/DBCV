import asyncio
import json
import logging
from typing import Dict, Union
from uuid import UUID
from fastapi import WebSocket
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class WebSocketManagerBase:
    def __init__(self):
        # Активные WebSocket-подключения: {entity_id: {unique_user_key: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        self.lock = asyncio.Lock()

    @staticmethod
    def _normalize_key(key: Union[UUID, str]) -> str:
        """Преобразовать key в строку."""
        return str(key)

    async def notify(self, entity_id: Union[UUID, str], message: BaseModel | str) -> None:
        """Отправить сообщение пользователю в сущности, если он подключен."""
        entity_id = self._normalize_key(entity_id)
        async with self.lock:
            connections = self.active_connections.get(entity_id)

            if not connections:
                logger.warning(f"[WS] No active connections for {entity_id}")
                return

            disconnected = []

            for user_key, websocket in connections.items():
                try:
                    msg = None
                    if isinstance(message, str):
                        msg = message

                    if isinstance(message, BaseModel):
                        msg = message.model_dump_json()
                    if msg is None:
                        try:
                            msg = json.dumps(message)
                        except json.JSONDecodeError:
                            raise ValueError("Invalid message")
                    await websocket.send_text(msg)
                except Exception as e:
                    logger.error(f"[WS] Send failed to {user_key} in {entity_id}: {repr(e)}")
                    disconnected.append(user_key)

            # Удаляем недоступные соединения
            for user_key in disconnected:
                del connections[user_key]
                logger.info(f"[WS] Removed dead connection {user_key} from {entity_id}")

            if not connections:
                del self.active_connections[entity_id]

    async def add_connection(self, entity_id: Union[UUID, str], connection_uuid: Union[UUID, str], websocket: WebSocket):
        entity_id = self._normalize_key(entity_id)
        async with self.lock:
            if entity_id not in self.active_connections:
                self.active_connections[entity_id] = {}
            self.active_connections[entity_id][connection_uuid] = websocket
            logger.info(f"[WS] Connected: {connection_uuid} to {entity_id}")

    async def remove_connection(self, entity_id: Union[UUID, str], connection_uuid: Union[UUID, str]):
        entity_id = self._normalize_key(entity_id)
        async with self.lock:
            entity_conns = self.active_connections.get(entity_id)
            if entity_conns and connection_uuid in entity_conns:
                del entity_conns[connection_uuid]
                logger.info(f"[WS] Disconnected: {connection_uuid} from {entity_id}")
                if not entity_conns:
                    del self.active_connections[entity_id]