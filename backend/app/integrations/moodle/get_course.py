"""Moodle Get Course интеграция через Moodle Web Services REST API (httpx)."""
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from urllib.parse import urlparse

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


MOODLE_COURSE_FIELDS = {"id", "shortname", "idnumber", "category"}
MOODLE_AUTH_ERROR_CODES = {
    "invalidtoken",
    "invalidlogin",
    "accessdenied",
    "requireloginerror",
    "nopermission",
}


def _validate_credentials(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Проверяет и приводит базовые креды Moodle.

    Returns:
        (base_url, token, error_message)
    """
    base_url = payload.get("base_url") or payload.get("url") or payload.get("host")
    token = payload.get("token") or payload.get("wstoken") or payload.get("api_key")

    if not base_url or not isinstance(base_url, str) or not base_url.strip():
        return None, None, "В credentials отсутствует base_url"
    if not token or not isinstance(token, str) or not token.strip():
        return None, None, "В credentials отсутствует token/wstoken"

    base_url = base_url.strip()
    token = token.strip()

    if not (base_url.startswith("http://") or base_url.startswith("https://")):
        return None, None, "base_url должен начинаться с http:// или https://"

    parsed = urlparse(base_url)
    if not parsed.scheme or not parsed.netloc:
        return None, None, "base_url должен быть полноценным URL (например, https://example.com)"

    return base_url, token, None


def _build_endpoint(base_url: str) -> str:
    trimmed = base_url.rstrip("/")
    if trimmed.endswith("server.php"):
        return trimmed
    return f"{trimmed}/webservice/rest/server.php"


def _normalize_field(field_raw: Any) -> Optional[str]:
    if field_raw is None:
        return None
    field = str(field_raw).strip()
    if not field:
        return None
    if field not in MOODLE_COURSE_FIELDS:
        raise ValueError(
            f"Поле фильтра должно быть одним из: {', '.join(sorted(MOODLE_COURSE_FIELDS))}"
        )
    return field


def _normalize_field_value(field: Optional[str], value_raw: Any) -> Optional[str]:
    if value_raw is None:
        return None
    if isinstance(value_raw, (list, tuple, dict)):
        raise ValueError("Значение для фильтра должно быть строкой или числом")
    value = str(value_raw).strip()
    if not value:
        return None
    if field in {"id", "category"}:
        try:
            int(value)
        except ValueError as err:
            raise ValueError("Значение для фильтра должно быть числом") from err
    return value


def _extract_moodle_error(data: Any) -> Optional[Tuple[int, str]]:
    if not isinstance(data, dict):
        return None
    if not data.get("exception") and not data.get("errorcode"):
        return None
    error_code = 401 if data.get("errorcode") in MOODLE_AUTH_ERROR_CODES else 400
    message = data.get("message") or data.get("exception") or "Ошибка Moodle"
    debug_info = data.get("debuginfo")
    if debug_info:
        message = f"{message} ({debug_info})"
    return error_code, message


async def _fetch_moodle_json(
    endpoint: str,
    params: Dict[str, Any],
    logger: BotLogger,
) -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
    except httpx.HTTPStatusError as err:
        await logger.error(f"Moodle HTTP error: {err}")
        return None, {
            "response": {
                "ok": False,
                "error_code": err.response.status_code,
                "description": str(err),
            }
        }
    except httpx.RequestError as err:
        await logger.error(f"Moodle request error: {err}")
        return None, {
            "response": {
                "ok": False,
                "error_code": 500,
                "description": str(err),
            }
        }

    try:
        data = response.json()
    except ValueError as err:
        await logger.error(f"Moodle response parse error: {err}")
        return None, {
            "response": {
                "ok": False,
                "error_code": 500,
                "description": "Некорректный JSON в ответе Moodle",
            }
        }

    moodle_error = _extract_moodle_error(data)
    if moodle_error:
        error_code, description = moodle_error
        return None, {
            "response": {
                "ok": False,
                "error_code": error_code,
                "description": description,
            }
        }

    return data, None


class MoodleGetCourseIntegration(BaseIntegration):
    """Получение курса Moodle по полю через REST API (core_course_get_courses_by_field)."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="moodle_get_course",
            version="1.0.0",
            name="Moodle Get Course",
            description="Получить курс Moodle по полю (core_course_get_courses_by_field)",
            category="education",
            icon_s3_key="icons/integrations/moodle.svg",
            color="#1E88E5",
            config_schema={
                "type": "object",
                "properties": {
                    "field": {
                        "type": "string",
                        "title": "Course Field",
                        "enum": sorted(MOODLE_COURSE_FIELDS),
                        "description": "Поле для поиска курса (core_course_get_courses_by_field)",
                    },
                    "value": {
                        "type": "string",
                        "title": "Field Value",
                        "description": "Значение поля для поиска курса",
                    },
                    "include_warnings": {
                        "type": "boolean",
                        "title": "Include Warnings",
                        "default": True,
                        "description": "Возвращать предупреждения Moodle (warnings)",
                    },
                },
                "required": ["field", "value"],
            },
            credentials_provider="moodle",
            credentials_strategy="api_key",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Курс по короткому имени",
                    "config": {
                        "field": "shortname",
                        "value": "course_shortname",
                    },
                },
                {
                    "title": "Курс по идентификатору",
                    "config": {
                        "field": "id",
                        "value": "15",
                    },
                },
            ],
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        """Выполняет запрос core_course_get_courses_by_field для получения курса."""
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="moodle",
            strategy="api_key",
        )

        if not creds:
            await logger.error("Moodle credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Не найдены Moodle credentials",
                }
            }

        payload = creds.get("payload", {}) if isinstance(creds, dict) else {}
        if not payload:
            payload = creds if isinstance(creds, dict) else {}

        base_url, token, cred_error = _validate_credentials(payload)
        if cred_error:
            await logger.error(
                "Moodle credentials are incomplete",
                extra={"available_keys": list(payload.keys())},
            )
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": cred_error,
                }
            }

        field_raw = config.get("field")
        value_raw = config.get("value")
        include_warnings = bool(config.get("include_warnings", True))

        try:
            field = _normalize_field(field_raw)
            value = _normalize_field_value(field, value_raw)
        except ValueError as err:
            await logger.error(str(err))
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": str(err),
                }
            }

        if not field or not value:
            await logger.error("Field and value are required for Moodle get course")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "Параметры field и value обязательны",
                }
            }

        endpoint = _build_endpoint(base_url)
        params: Dict[str, Any] = {
            "wstoken": token,
            "wsfunction": "core_course_get_courses_by_field",
            "moodlewsrestformat": "json",
            "field": field,
            "value": value,
        }

        data, error_response = await _fetch_moodle_json(endpoint, params, logger)
        if error_response:
            return error_response

        courses: List[Any] = []
        warnings: Optional[Any] = None
        if isinstance(data, dict):
            courses = data.get("courses") or []
            warnings = data.get("warnings")
        elif data is not None:
            courses = [data]

        result: Dict[str, Any] = {"courses": courses, "course": courses[0] if courses else None}
        if include_warnings and warnings:
            result["warnings"] = warnings

        return {
            "response": {
                "ok": True,
                "result": result,
            }
        }
