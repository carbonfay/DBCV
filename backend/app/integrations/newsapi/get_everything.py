"""NewsAPI Get Everything интеграция через прямой HTTP запрос (httpx)."""

from typing import Any, Dict
from uuid import UUID

from app.auth.credentials_resolver import CredentialsResolver
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.loggers.bot import BotLogger

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:  # pragma: no cover
    # Важно: интеграции импортируются при старте приложения автоматически.
    # Если httpx не установлен, мы не должны падать на импорте модуля — только отдавать
    # понятную ошибку при выполнении execute().
    httpx = None  # type: ignore[assignment]
    HTTPX_AVAILABLE = False


class NewsApiGetEverythingIntegration(BaseIntegration):
    @staticmethod
    def _failure(description: str, error_code: int) -> Dict[str, Any]:
        return {"response": {"ok": False, "error_code": error_code, "description": description}}

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="newsapi_get_everything",
            version="1.0.0",
            name="NewsAPI Get Everything",
            description="Поиск новостей по ключевым словам через NewsAPI /v2/everything",
            category="news",
            icon_s3_key="icons/integrations/newsapi.svg",
            color="#1565C0",
            config_schema={
                "type": "object",
                "required": ["q"],
                "properties": {
                    "q": {"type": "string", "title": "Query", "description": "Поисковый запрос"},
                    "language": {"type": "string", "title": "Language", "description": "Код языка (ru, en, ...)"},
                    "sort_by": {
                        "type": "string",
                        "title": "Sort By",
                        "enum": ["relevancy", "popularity", "publishedAt"],
                        "default": "publishedAt",
                    },
                    "page_size": {
                        "type": "integer",
                        "title": "Page Size",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 20,
                    },
                    "page": {"type": "integer", "title": "Page", "minimum": 1, "default": 1},
                },
            },
            credentials_provider="newsapi",
            credentials_strategy="api_key",
            library_name="httpx>=0.27.0" if HTTPX_AVAILABLE else None,
            examples=[
                {"title": "Поиск новостей", "config": {"q": "python", "language": "ru", "page_size": 5}},
            ],
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return self._failure("httpx library is not installed", 500)

        # Credentials в платформе могут приходить в двух формах:
        # - {"payload": {...}}  (основной формат: расшифрованные данные внутри payload)
        # - {...}              (fallback/обратная совместимость)
        creds = await credentials_resolver.get_default_for(bot_id=bot_id, provider="newsapi", strategy="api_key")
        if not creds:
            await logger.error("NewsAPI credentials not found")
            return self._failure("NewsAPI api_key not found in credentials", 401)

        payload = creds.get("payload") or creds
        # Поддерживаем несколько названий поля на всякий случай (в UI могли сохранять по-разному).
        api_key = payload.get("api_key") or payload.get("key") or payload.get("token")
        if not api_key:
            await logger.error(f"api_key not found in credentials. Keys: {list(payload.keys())}")
            return self._failure("api_key not found in credentials", 401)

        q = config.get("q")
        if not q:
            return self._failure("q is required", 400)

        def _as_int(v: Any, default: int) -> int:
            try:
                return int(v)
            except (TypeError, ValueError):
                return default

        page_size = _as_int(config.get("page_size"), 20)
        # NewsAPI ограничивает pageSize диапазоном 1..100 — зажимаем, чтобы не получать 400 от API.
        page_size = 1 if page_size < 1 else 100 if page_size > 100 else page_size

        params = {
            "q": str(q),
            "language": str(config.get("language")) if config.get("language") else None,
            # В NewsAPI параметр называется sortBy (camelCase), а в нашей схеме — sort_by.
            "sortBy": str(config.get("sort_by") or "publishedAt"),
            "pageSize": page_size,
            "page": _as_int(config.get("page"), 1),
        }
        params = {k: v for k, v in params.items() if v is not None}

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:  # type: ignore[attr-defined]
                r = await client.get(
                    "https://newsapi.org/v2/everything",
                    params=params,
                    headers={"X-Api-Key": str(api_key)},
                )
                data = r.json()
        except httpx.HTTPError as exc:  # type: ignore[attr-defined]
            await logger.error(f"NewsAPI HTTP error: {exc}")
            return self._failure(str(exc), 502)
        except Exception as exc:
            await logger.error(f"Unexpected NewsAPI error: {exc}")
            return self._failure(str(exc), 500)

        if not isinstance(data, dict):
            return self._failure("Unexpected response from NewsAPI", 502)

        if data.get("status") != "ok":
            # NewsAPI возвращает error payload вида:
            # {"status":"error","code":"apiKeyInvalid","message":"..."}
            # Маппим коды на HTTP-коды платформы, чтобы фронту/пользователю было понятнее.
            code = (data.get("code") or "").lower()
            message = data.get("message") or "NewsAPI error"
            mapped = 502
            if "apikey" in code:
                mapped = 401
            elif "rate" in code:
                mapped = 429
            elif "parameter" in code:
                mapped = 400
            return self._failure(str(message), mapped)

        # Успех: отдаём исходный ответ NewsAPI (data) + нормализованный request (params),
        # чтобы было удобно отлаживать, какими параметрами мы реально вызвали API.
        return {"response": {"ok": True, "result": {"request": params, "data": data}}}


