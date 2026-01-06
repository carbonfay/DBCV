import redis
import time
import logging
from config import settings


MEMORY_THRESHOLD_MB = 20
CHECK_INTERVAL_SEC = 10
QUEUE_LENGTH_LIMIT = 5000


PRIORITIZED_QUEUES = [
    {"name": "emitter.events", "priority": 5},
    {"name": "emitter.batch", "priority": 4},
    {"name": "bot_message_queue", "priority": 3},
    {"name": settings.BOT_STREAM_NAME, "priority": 2},
    {"name": settings.USER_STREAM_NAME, "priority": 1},
]


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def get_memory_usage_mb(client: redis.Redis) -> int:
    mem_bytes = int(client.info("memory")["used_memory"])
    return mem_bytes // (1024 * 1024)


def get_stream_length(client: redis.Redis, queue_name: str) -> int:
    try:
        return client.xlen(queue_name)
    except redis.exceptions.ResponseError:
        return 0


def trim_queue(client: redis.Redis, queue_name: str, keep_last_n: int):
    try:
        client.xtrim(queue_name, maxlen=keep_last_n, approximate=True)
        logging.warning(f"Очередь '{queue_name}' обрезана до {keep_last_n} сообщений.")
    except Exception as e:
        logging.error(f"Ошибка при XTRIM очереди '{queue_name}': {e}")


def main():
    client = redis.Redis.from_url(settings.REDIS_URL)

    while True:
        try:
            mem_mb = get_memory_usage_mb(client)
            logging.info(f"Redis использует {mem_mb} MB")

            if mem_mb < MEMORY_THRESHOLD_MB:
                time.sleep(CHECK_INTERVAL_SEC)
                continue

            logging.warning(f"Порог Redis-памяти превышен: {mem_mb} MB > {MEMORY_THRESHOLD_MB} MB")

            for queue in sorted(PRIORITIZED_QUEUES, key=lambda q: q["priority"], reverse=True):
                name = queue["name"]
                priority = queue["priority"]
                length = get_stream_length(client, name)

                logging.info(f"Очередь '{name}': длина = {length}")

                if length > QUEUE_LENGTH_LIMIT:

                    keep = max(500, QUEUE_LENGTH_LIMIT // (priority + 1))
                    trim_queue(client, name, keep)

            time.sleep(CHECK_INTERVAL_SEC)
        except Exception as e:
            logging.error(f"Ошибка в главном цикле: {e}")
            time.sleep(CHECK_INTERVAL_SEC * 2)


if __name__ == "__main__":
    main()