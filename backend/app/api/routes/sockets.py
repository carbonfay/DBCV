import asyncio
import logging
from uuid import UUID

from fastapi import (APIRouter, Depends, WebSocket, WebSocketDisconnect)

from app.managers.websocket import ChannelWebSocketManager, BotWebSocketManager
from app.api.dependencies.websocket import AuthWebsocketDataChannelDep, AuthWebsocketDataBotDep
from app.managers.websocket import WebSocketManagerBase

router = APIRouter()

logger = logging.getLogger(__name__)

channel_websocket_manager = ChannelWebSocketManager()
bot_websocket_manager = BotWebSocketManager()


async def notify_channel(channel_id: UUID | str, message) -> None:
    await channel_websocket_manager.notify_channel(channel_id, message)


async def notify_bot(bot_id: UUID | str, message) -> None:
    await bot_websocket_manager.notify_bot(bot_id, message)


async def websocket_handler(websocket: WebSocket, auth_data: dict, websocket_manager: WebSocketManagerBase):
    user = auth_data["user"]
    entity = auth_data["entity"]
    connection_uuid = user["connection_uuid"]
    logger.info(f"Пользователь {user['id']} подключился к сущности {entity['id']}")

    # Принимаем WebSocket-соединение
    await websocket.accept()
    await websocket_manager.add_connection(entity['id'], connection_uuid, websocket)

    try:
        while True:
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        logger.info(f"Соединение с сущностью {entity['id']} закрыто пользователем {user['id']}.")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка в WebSocket-соединении с сущностью {entity['id']}: {e}")
    finally:
        await websocket_manager.remove_connection(entity['id'], connection_uuid)
        logger.info(f"Соединение с сущностью {entity['id']} закрыто.")


# WebSocket эндпоинт для соединений с каналами
@router.websocket("/ws/channel")
async def channel_websocket_endpoint(websocket: WebSocket,
                                     auth_data: AuthWebsocketDataChannelDep):
    await websocket_handler(websocket, auth_data, channel_websocket_manager)


# WebSocket эндпоинт для соединений с ботами
@router.websocket("/ws/bot")
async def bot_websocket_endpoint(websocket: WebSocket,
                                 auth_data: AuthWebsocketDataBotDep):
    await websocket_handler(websocket, auth_data, bot_websocket_manager)
