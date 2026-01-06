from abc import abstractmethod, ABC

from sqlalchemy.ext.asyncio import AsyncEngine


class BaseManager(ABC):
    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    @abstractmethod
    def insert(self, data: dict) -> dict:
        raise NotImplementedError("Subclasses must implement this method")
