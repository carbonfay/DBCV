import json
import logging
import uuid
from copy import deepcopy
from typing import Any, Optional, TypeVar, Callable
import functools
from uuid import uuid4
from datetime import datetime

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

logger = logging.getLogger(__name__)

AnyModel = TypeVar("AnyModel", bound=BaseModel)


def partial_model(model: type[AnyModel]) -> type[AnyModel]:
    """Decorator function used to modify a pydantic model's fields to all be optional.

    Taken from https://stackoverflow.com/a/76560886/19129261
    """

    def make_field_optional(
        field: FieldInfo, default: Any = None
    ) -> tuple[Any, FieldInfo]:
        new = deepcopy(field)
        new.default = default
        new.annotation = Optional[field.annotation]  # type: ignore
        return new.annotation, new

    return create_model(
        f"Partial{model.__name__}",
        __base__=model,
        __module__=model.__module__,
        **{  # type: ignore
            field_name: make_field_optional(field_info)
            for field_name, field_info in model.model_fields.items()
        },
    )


def prepare_insert_data(json_fields: list[str] = None) -> Callable:
    """
    Декоратор для подготовки данных перед вставкой:
    - автогенерация id, created_at, updated_at
    - сериализация JSON-полей
    - перехват и логирование ошибок
    """
    json_fields = json_fields or []

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, data: dict, *args, **kwargs) -> Any:
            try:
                # Генерация ID
                data.setdefault("id", str(uuid.uuid4()))

                # Автоматическое время
                now = datetime.now()
                data.setdefault("created_at", now)
                data.setdefault("updated_at", now)

                # Сериализация JSON-полей
                for field in json_fields:
                    if field in data and isinstance(data[field], (dict, list)):
                        data[field] = json.dumps(data[field], ensure_ascii=False)

                return await func(self, data, *args, **kwargs)

            except Exception as e:
                logger.exception(f"[InsertError] Failed to insert data in {func.__qualname__}: {e}")
                raise

        return wrapper

    return decorator