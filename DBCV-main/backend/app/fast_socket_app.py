import logging
import logging.config
import asyncio
from uuid import uuid4

from faststream import FastStream
from app.logging_config import LOGGING_CONFIG
from app.schemas import rebuild_models
from app.api.routes.sockets import notify_channel, notify_bot
from app.schemas.message import MessagePublic
from app.broker import broker

logging.config.dictConfig(LOGGING_CONFIG)
rebuild_models()
logger = logging.getLogger(__name__)

fast_socket_app = FastStream(broker)


@broker.subscriber("message_queue")
async def handle_channel_message(msg: dict):
    try:
        channel_id = msg["channel_id"]
        message_data = MessagePublic(**msg["message"])
        await notify_channel(channel_id, message_data)
    except Exception as e:
        logger.error(f"[ERROR][message_queue] {e}")


@broker.subscriber("bot_message_queue")
async def handle_bot_message(msg: dict):
    try:
        bot_id = msg["bot_id"]
        message_data = msg["message"]
        await notify_bot(bot_id, message_data)
    except Exception as e:
        logger.error(f"[ERROR][bot_message_queue] {e}")


async def publish_bot_message(bot_id: str, message: dict):
    await broker.publish({"bot_id": bot_id, "message": message}, "bot_message_queue")


if __name__ == "__main__":
    asyncio.run(fast_socket_app.run(sleep_time=0.01))
