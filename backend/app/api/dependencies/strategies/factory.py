from .base import BaseAuthStrategy
from .channel import ChannelAuthStrategy
from .bot import BotAuthStrategy


class AuthStrategyFactory:
    @staticmethod
    def get_strategy(entity_type: str) -> BaseAuthStrategy:
        if entity_type == "channel":
            return ChannelAuthStrategy()
        elif entity_type == "bot":
            return BotAuthStrategy()
        else:
            raise ValueError("Неизвестный тип сущности")