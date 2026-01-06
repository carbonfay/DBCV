import asyncio
import logging
import os
from uuid import uuid4

from faststream import FastStream
from faststream.redis import StreamSub
from app.broker import broker
from app.schemas import rebuild_models
from app.config import settings
from app.engine.bot_processor import check_message
from redis.asyncio import Redis

import logging.config
from app.logging_config import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
rebuild_models()
logger = logging.getLogger(__name__)

role = os.getenv("ROLE", "user").lower()
consumer_id = f"{role}-consumer-{uuid4()}"

app = FastStream(broker)

semaphore = asyncio.Semaphore(settings.DB_POOL_SIZE)


async def handle_message(message_data):
    try:
        message = message_data["message"]
        channel_id = message_data.get("channel_id")
    except (KeyError, TypeError) as e:
        logger.error(f"handle_message: invalid message_data: {message_data} | {e}")
        return

    await check_message(message, channel_id)


async def process_batch(messages, stream_name, group_name, from_claim=False):
    async def process_one_safe(m):
        async with semaphore:
            try:
                if from_claim:
                    msg_id, payload = m
                    await handle_message(payload)
                    return msg_id
                else:
                    if isinstance(m.get("channel_id"), str) and m.get("channel_id") == "init":
                        logger.debug("Skipping init message")
                        return
                    await handle_message(m)
                    return None
            except Exception:
                logger.exception("Failed to process message")
                return None

    results = await asyncio.gather(*[process_one_safe(m) for m in messages])

    if from_claim:
        ack_ids = [msg_id for msg_id in results if msg_id]
        logger.debug(f"ACKing messages: {ack_ids}")
        if ack_ids:
            await broker._connection.xack(stream_name, group_name, *ack_ids)

if role == "user":

    @broker.subscriber(stream=StreamSub(
        settings.USER_STREAM_NAME,
        group=settings.USER_STREAM_GROUP,
        consumer=consumer_id,
        batch=True,
        max_records=100,
        no_ack=False))
    async def handle_user_message(messages):
        logger.info(f"Received {len(messages)} user messages")
        await process_batch(messages, settings.USER_STREAM_NAME, settings.USER_STREAM_GROUP)

elif role == "bot":

    @broker.subscriber(stream=StreamSub(
        settings.BOT_STREAM_NAME,
        group=settings.BOT_STREAM_GROUP,
        consumer=consumer_id,
        batch=True,
        max_records=100,
        no_ack=False))
    async def handle_bot_message(messages):
        logger.info(f"Received {len(messages)} bot messages")
        await process_batch(messages, settings.BOT_STREAM_NAME, settings.BOT_STREAM_GROUP)

else:
    raise ValueError(f"Unknown role: {role}")


@app.after_startup
async def after_startup_tasks():
    stream_name = settings.BOT_STREAM_NAME if role == "bot" else settings.USER_STREAM_NAME
    group_name = settings.BOT_STREAM_GROUP if role == "bot" else settings.USER_STREAM_GROUP

    redis = Redis.from_url(settings.REDIS_URL)
    try:
        await redis.xadd(stream_name, {"message": "init", "channel_id": "init"})
        logger.info(f"[{role.upper()}] Initialized stream: {stream_name}")
    except Exception as e:
        logger.warning(f"[{role.upper()}] Stream initialization skipped or failed: {e}")

    async def reclaim_pending():
        logger.info(f"[{role.upper()}] Reclaim loop started for stream: {stream_name}, group: {group_name}, consumer: {consumer_id}")

        while True:
            try:
                pending = await redis.xpending_range(
                    stream_name,
                    group_name,
                    min="-",
                    max="+",
                    count=10
                )
                logger.debug(f"[{role.upper()}] Pending messages: {len(pending)}")

                to_reclaim = [entry for entry in pending if entry["consumer"] != consumer_id]
                for entry in to_reclaim:
                    msg_id = entry["message_id"]
                    logger.warning(f"[{role.upper()}] Reclaiming {msg_id} from {entry['consumer']}")

                    claimed = await redis.xclaim(
                        stream_name,
                        group_name,
                        consumer_id,
                        min_idle_time=10_000,
                        message_ids=[msg_id],
                    )
                    logger.info(f"[{role.upper()}] Claimed {len(claimed)} message(s)")

                    await process_batch(claimed, stream_name, group_name, from_claim=True)
            except Exception as e:
                logger.exception(f"[{role.upper()}] Error during reclaim_pending: {e}")

            logger.debug(f"[{role.upper()}] Reclaim loop sleeping 30s...")
            await asyncio.sleep(30)

    asyncio.create_task(reclaim_pending())


if __name__ == "__main__":
    app.run()
