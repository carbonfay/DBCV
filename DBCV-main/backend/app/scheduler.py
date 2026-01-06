import asyncio
import logging
import logging.config
from uuid import UUID, uuid4
from typing import Union

from faststream import FastStream
from faststream.redis import StreamSub

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import LOGGING_CONFIG
from app.config import settings
from app.broker import broker
from app.schemas import rebuild_models
from app.database import sessionmanager
from app.models.emitter import EmitterModel
from app.utils.message import bot_send_message_by_id
import app.crud.emitter as crud_emitter

logging.config.dictConfig(LOGGING_CONFIG)
rebuild_models()
logger = logging.getLogger(__name__)

app = FastStream(broker)


async def send_message(message_id: Union[str, UUID], bot_id: Union[str, UUID], needs_message_processing: bool = True):
    logger.info(f"[SEND] Sending message_id={message_id} bot_id={bot_id} needs_processing={needs_message_processing}")
    async with sessionmanager.session() as session:
        await bot_send_message_by_id(session, message_id, bot_id, needs_message_processing)


async def safe_send_message(message_id: Union[str, UUID], bot_id: Union[str, UUID], needs_message_processing: bool = True):
    try:
        await send_message(message_id, bot_id, needs_message_processing)
    except Exception as e:
        logger.exception(f"Error while processing message_id={message_id}, bot_id={bot_id}: {e}")


@broker.publisher("emitter.events")
async def publish_emitter_event(event: str, data: dict):
    logger.info(f"[EMIT] Publishing event: {event} | data: {data}")
    await broker.publish({"event": event, "data": data}, "emitter.events")


async def publish_emitter_message_batch(message_data):
    logger.info(f"[EMIT] Publishing message batch: {message_data}")
    await broker.publish(message_data, stream="emitter.batch")


@broker.subscriber("emitter.events")
async def on_emitter_event(event_msg: dict):
    event = event_msg["event"]
    data = event_msg["data"]
    logger.info(f"[EVENT] Received: {event} | data: {data}")

    async with sessionmanager.session() as session:
        emitter = await crud_emitter.get_emitter(session, data["id"])
        logger.info(f"[EVENT] Loaded emitter {emitter.name} (id={emitter.id})")

        match event:
            case "emitter.created":
                await scheduler.add_emitter(session, emitter)
            case "emitter.updated":
                await scheduler.update_emitter(session, emitter)
            case "emitter.deleted":
                await scheduler.delete_emitter(session, emitter)


@broker.subscriber(
    stream=StreamSub("emitter.batch", group="batch-group", consumer=f"batch-consumer-{uuid4()}", batch=True, max_records=50)
)
async def process_emitter_batch(messages):
    logger.info(f"[BATCH] received {len(messages)} messages")
    tasks = [safe_send_message(m.get("message_id"), m.get("bot_id"), m.get("needs_message_processing")) for m in messages]
    await asyncio.gather(*tasks)


class EmitterScheduler(AsyncIOScheduler):
    async def start_scheduler(self):
        logger.info("[SCHEDULER] Starting scheduler and loading emitters")
        super().start()
        self.schedule_sync_emitters()

        async with sessionmanager.session() as session:
            emitters = await crud_emitter.read_emitters(session)
            emitter_job_ids = {e.job_id for e in emitters if e.job_id}

            all_scheduler_jobs = self.get_jobs()
            for job in all_scheduler_jobs:
                if job.id != "sync_emitters" and job.id not in emitter_job_ids:
                    logger.info(f"[SCHEDULER] Removing stale job: {job.id}")
                    self.remove_job(job.id)

            for emitter in emitters:
                await self.add_emitter(session, emitter)

        logger.info("[SCHEDULER] Initial emitters loaded")

    async def add_emitter(self, session: AsyncSession, emitter: EmitterModel) -> EmitterModel:
        if emitter.message_id is None or emitter.cron_id is None:
            if emitter.is_active:
                emitter.is_active = False
                await session.commit()
                await session.refresh(emitter)
            return emitter

        job = self.add_job(
            publish_emitter_message_batch,
            trigger=emitter.cron.get_cron_trigger(),
            args=[{
                "message_id": emitter.message.id,
                "bot_id": emitter.bot_id,
                "needs_message_processing": emitter.needs_message_processing
            }],
            id=emitter.job_id or None,
            name=emitter.name
        )

        emitter.job_id = job.id
        await session.commit()
        await session.refresh(emitter)
        logger.info(f"[SCHEDULER] Added emitter: {emitter.name} (job_id={emitter.job_id})")

        if emitter.is_active:
            if job.next_run_time is None:
                job.resume()
        else:
            job.pause()

        return emitter

    async def delete_emitter(self, session: AsyncSession, emitter: EmitterModel):
        logger.info(f"[SCHEDULER] Deleting emitter: {emitter.name}")
        if emitter.job_id and self.get_job(emitter.job_id):
            self.remove_job(emitter.job_id)
        await crud_emitter.delete_emitter(session, emitter.id)
        await session.commit()

    async def update_emitter(self, session: AsyncSession, emitter: EmitterModel):
        logger.info(f"[SCHEDULER] Updating emitter: {emitter.name}")
        if emitter.job_id is None:
            return await self.add_emitter(session, emitter)
        if emitter.cron_id is None or emitter.message_id is None:
            if emitter.is_active:
                emitter.is_active = False
                await session.commit()
                await session.refresh(emitter)
            return emitter

        job = self.modify_job(
            emitter.job_id,
            trigger=emitter.cron.get_cron_trigger(),
            args=[{
                "message_id": emitter.message.id,
                "bot_id": emitter.bot_id,
                "needs_message_processing": emitter.needs_message_processing
            }]
        )

        if emitter.is_active:
            if job.next_run_time is None:
                job.resume()
        else:
            job.pause()

        return emitter

    async def _run_sync_emitters(self):
        logger.info("[SYNC] Running emitter synchronization")
        try:
            async with sessionmanager.session() as session:
                emitters = await crud_emitter.read_emitters(session)
                valid_job_ids = set()
                for emitter in emitters:
                    valid_job_ids.add(emitter.job_id)
                    existing_job = self.get_job(emitter.job_id) if emitter.job_id else None

                    if existing_job is None:
                        logger.info(f"[SYNC] Re-adding missing job for emitter {emitter.name}")
                        await self.add_emitter(session, emitter)
                    else:
                        new_trigger = emitter.cron.get_cron_trigger()
                        new_args = [{
                            "message_id": emitter.message.id,
                            "bot_id": emitter.bot_id,
                            "needs_message_processing": emitter.needs_message_processing
                        }]

                        if existing_job.trigger != new_trigger or existing_job.args != new_args:
                            logger.info(f"[SYNC] Updating job for emitter {emitter.name} (job_id={emitter.job_id})")
                            self.modify_job(
                                emitter.job_id,
                                trigger=new_trigger,
                                args=new_args,
                                next_run_time=existing_job.next_run_time
                            )

                for job in self.get_jobs():
                    if job.id != "sync_emitters" and job.id not in valid_job_ids:
                        logger.info(f"[SYNC] Removing stale job: {job.id}")
                        self.remove_job(job.id)

        except Exception as e:
            logger.exception(f"[SYNC] Error during emitter synchronization: {repr(e)}")

    def schedule_sync_emitters(self):
        self.add_job(self._run_sync_emitters, trigger="interval", seconds=180, id="sync_emitters", name="Sync Emitters")
        logger.info("[SCHEDULER] Scheduled emitter sync job every 180 seconds")


scheduler = EmitterScheduler(timezone=settings.TIME_ZONE)


async def run_scheduler():
    logger.info("[START] Scheduler loop starting...")
    try:
        await scheduler.start_scheduler()
        logger.info("[START] Scheduler Worker started")

        while True:
            await asyncio.sleep(0.1)
    except Exception as e:
        logger.exception("Scheduler worker encountered an error")
    finally:
        logger.info("[STOP] Scheduler worker stopping")
        scheduler.shutdown()


async def run_faststream():
    logger.info("[START] FastStream starting...")
    await app.run(sleep_time=0.01)
    logger.info("[STOP] FastStream stopped")


async def main():
    logger.info("[MAIN] Starting application...")
    scheduler_task = asyncio.create_task(run_scheduler())
    faststream_task = asyncio.create_task(run_faststream())
    await asyncio.gather(scheduler_task, faststream_task)
    logger.info("[MAIN] Application exiting")


if __name__ == "__main__":
    asyncio.run(main())
