import logging
from app.broker import broker
from app.logging_config import LOGGING_CONFIG
from app.config import settings


class BotLogger:
    def __init__(self, bot_id: str):
        self.bot_id = bot_id
        self.step_id = None
        self.logger = logging.getLogger(__name__)
        self.formatter = logging.Formatter(LOGGING_CONFIG["formatters"]["default"]["format"])

    def set_step(self, step_id: str):
        self.step_id = step_id

    async def info(self, message: str):
        await self.log(message, logging.INFO)

    async def warning(self, message: str):
        await self.log(message, logging.WARNING)

    async def error(self, message: str):
        await self.log(message, logging.ERROR)

    async def log(self, message: str, level: int = logging.INFO):
        # Форматирование сообщения
        record = self.logger.makeRecord(
            self.logger.name, level, None, None, message, None, None
        )
        formatted_message = self.formatter.format(record)

        # Логирование в обычный логгер
        self.logger.log(level, formatted_message)

        # Отправка лога в брокер
        await broker.publish({"bot_id": self.bot_id, "message": {"type": "logs", "level": logging.getLevelName(level), "step_id": self.step_id, "message": formatted_message}}, "bot_message_queue")

    async def print(self, *args, sep=' ', end='\n'):
        message = sep.join(str(arg) for arg in args) + end
        await self.info(message.rstrip('\n'))

    async def send_variables(self, variables: dict):
        await broker.publish({"bot_id": self.bot_id, "message": {"type": "variables", "variables": variables}}, "bot_message_queue")


class NoopBotLogger(BotLogger):
    def __init__(self):
        super().__init__(bot_id="noop",)

    async def info(self, message: str):    return

    async def warning(self, message: str): return

    async def error(self, message: str):   return

    async def debug(self, message: str):   return

    async def print(self, *args, **kwargs): return

    async def send_variables(self, variables: dict): return