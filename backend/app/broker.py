from faststream.redis import RedisBroker
from app.config import settings


broker = RedisBroker(settings.REDIS_URL)