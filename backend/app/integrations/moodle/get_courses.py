"""Moodle Get Courses интеграция с использованием библиотеки moodleapi/moodle."""
import asyncio
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:  # moodlepy (pip package: moodle)
    from moodle import Moodle as MoodleClient  # type: ignore
    from moodle.exceptions import MoodleException  # type: ignore
    MOODLE_LIB = "moodle"
except Exception:  # noqa: BLE001 - либы могут отсутствовать
    try:  # moodleapi
        from moodleapi import Moodle as MoodleClient  # type: ignore
        try:
            from moodleapi.exceptions import MoodleException  # type: ignore
        except Exception:  # noqa: BLE001
            MoodleException = Exception
        MOODLE_LIB = "moodleapi"
    except Exception:  # noqa: BLE001
        MoodleClient = None  # type: ignore
        MoodleException = Exception
        MOODLE_LIB = None

MOODLE_AVAILABLE = MOODLE_LIB is not None and MoodleClient is not None


def _normalize_ids(ids_raw: Any) -> Optional[List[int]]:
    if ids_raw is None:
        return None
    if isinstance(ids_raw, (list, tuple)):
        raw_items = ids_raw
    else:
        raw_items = [ids_raw]

    normalized: List[int] = []
    for item in raw_items:
        if item is None:
            continue
        text_value = str(item).strip()
        if not text_value:
            continue
        try:
            normalized.append(int(text_value))
        except ValueError as err:
            raise ValueError(f"ID курса должен быть числом, получено: {item}") from err
    return normalized or None


def _to_serializable(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
        return obj.to_dict()
    try:
        return obj.__dict__  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        return str(obj)


def _extract_courses(result: Any) -> List[Any]:
    if result is None:
        return []
    if isinstance(result, list):
        return [_to_serializable(item) for item in result]
    return [_to_serializable(result)]


class MoodleGetCoursesIntegration(BaseIntegration):
    """Получение списка курсов Moodle через библиотеку (core_course_get_courses)."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="moodle_get_courses",
            version="1.0.0",
            name="Moodle Get Courses",
            description="Получить список курсов Moodle (core_course_get_courses)",
            category="education",
            icon_s3_key="icons/integrations/moodle.svg",
            color="#1E88E5",
            config_schema={
                "type": "object",
                "properties": {
                    "ids": {
                        "type": "array",
                        "items": {
                            "oneOf": [
                                {"type": "integer", "title": "Course ID"},
                                {
                                    "type": "string",
                                    "pattern": "^\\d+$",
                                    "title": "Course ID (строка цифр)"
                                }
                            ]
                        },
                        "title": "Course IDs",
                        "description": "Список ID курсов для фильтрации (опционально)"
                    }
                }
            },
            credentials_provider="moodle",
            credentials_strategy="api_key",
            library_name="moodleapi>=0.1.0",
            examples=[
                {
                    "title": "Получить все курсы",
                    "config": {}
                },
                {
                    "title": "Получить курсы по ID",
                    "config": {
                        "ids": [1, 2, 3]
                    }
                }
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        """
        Выполняет запрос core_course_get_courses через библиотеку Moodle.
        """
        if not MOODLE_AVAILABLE:
            await logger.error("Библиотека Moodle недоступна: moodleapi/moodle не установлена")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "Библиотека Moodle (moodleapi/moodle) не установлена"
                }
            }

        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="moodle",
            strategy="api_key"
        )

        if not creds:
            await logger.error("Moodle credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Не найдены Moodle credentials"
                }
            }

        payload = creds.get("payload", {}) if isinstance(creds, dict) else {}
        if not payload:
            payload = creds if isinstance(creds, dict) else {}

        base_url = payload.get("base_url") or payload.get("url") or payload.get("host")
        token = payload.get("token") or payload.get("wstoken") or payload.get("api_key")

        if not base_url or not token:
            await logger.error(
                "Moodle credentials are incomplete",
                extra={"available_keys": list(payload.keys())}
            )
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "В credentials отсутствуют base_url или token"
                }
            }

        ids_raw = config.get("ids")
        try:
            ids = _normalize_ids(ids_raw)
        except ValueError as err:
            await logger.error(str(err))
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": str(err)
                }
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            client = None
            try:
                client = MoodleClient(base_url, token)  # type: ignore[misc]
            except TypeError:
                # Некоторые реализации используют именованные аргументы
                client = MoodleClient(host=base_url, token=token)  # type: ignore[misc]

            async def _fetch_courses() -> Any:
                def _call():
                    # Предпочтительный путь: core.course.get_courses
                    core_obj = getattr(client, "core", None)
                    course_obj = getattr(core_obj, "course", None) if core_obj else None
                    get_courses_fn = None
                    if course_obj and hasattr(course_obj, "get_courses"):
                        get_courses_fn = course_obj.get_courses
                    elif hasattr(client, "get_courses"):
                        get_courses_fn = client.get_courses

                    if not get_courses_fn:
                        raise AttributeError("Метод get_courses не найден в клиенте Moodle")

                    if ids:
                        return get_courses_fn(ids=ids)
                    return get_courses_fn()

                return await asyncio.to_thread(_call)

            result = await _fetch_courses()
            courses = _extract_courses(result)

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "courses": courses
                    }
                }
            }
        except MoodleException as err:  # type: ignore[misc]
            await logger.error(f"Moodle error: {err}")
            return {
                "response": {
                    "ok": False,
                    "error_code": getattr(err, "errorcode", 500),
                    "description": str(err)
                }
            }
        except Exception as err:  # noqa: BLE001
            await logger.error(f"Unexpected Moodle error: {err}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(err)
                }
            }
