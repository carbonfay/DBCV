"""NewsAPI Get Top Headlines integration using newsapi-python library."""
from typing import Dict, Any, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ
try:
    from newsapi import NewsApiClient
    try:
        # new versions may expose a specific exception class
        from newsapi.newsapi_exception import NewsAPIException  # type: ignore
    except Exception:
        NewsAPIException = Exception
    NEWSAPI_AVAILABLE = True
except Exception:
    NewsApiClient = None  # type: ignore
    NewsAPIException = Exception
    NEWSAPI_AVAILABLE = False


class NewsAPIGetTopHeadlines(BaseIntegration):
    """Интеграция для получения топовых заголовков через NewsAPI (newsapi-python)."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="newsapi_get_top_headlines",
            version="1.0.0",
            name="NewsAPI Get Top Headlines",
            description="Получение топовых заголовков новостей через NewsAPI",
            category="news",
            icon_s3_key="icons/integrations/newsapi.svg",
            color="#ff6600",
            config_schema={
                "type": "object",
                "properties": {
                    "q": {
                        "type": "string",
                        "title": "Query",
                        "description": "Keywords or a phrase to search for."
                    },
                    "country": {
                        "type": "string",
                        "title": "Country",
                        "description": "2-letter ISO 3166-1. Cannot be combined with 'sources'."
                    },
                    "category": {
                        "type": "string",
                        "title": "Category",
                        "enum": [
                            "business",
                            "entertainment",
                            "general",
                            "health",
                            "science",
                            "sports",
                            "technology"
                        ]
                    },
                    "sources": {
                        "type": "string",
                        "title": "Sources",
                        "description": "Comma-separated source identifiers"
                    },
                    "pageSize": {
                        "type": "integer",
                        "title": "Page Size",
                        "description": "Number of results per page (default 20)",
                        "default": 20,
                        "maximum": 100
                    },
                    "page": {
                        "type": "integer",
                        "title": "Page",
                        "description": "Page number to retrieve (default 1)",
                        "default": 1,
                        "maximum": 100
                    }
                }
            },
            credentials_provider="newsapi",
            credentials_strategy="api_key",
            library_name=("newsapi-python" if NEWSAPI_AVAILABLE else None),
            examples=[
                {
                    "title": "Top headlines in the US",
                    "config": {"country": "us", "page_size": 10}
                }
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        """
        Выполняет вызов NewsAPI.get_top_headlines используя клиент newsapi-python.

        Возвращает формат: {"response": {"ok": True, "result": {...}}}
        """
        if not NEWSAPI_AVAILABLE:
            await logger.error("newsapi-python library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "newsapi-python library is not installed",
                }
            }

        # Получаем credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id, provider="newsapi", strategy="api_key"
        )

        if not creds:
            await logger.error("NewsAPI credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "NewsAPI api_key not found in credentials",
                }
            }

        payload = creds.get("payload", {}) if isinstance(creds, dict) else creds
        if not payload:
            payload = creds

        api_key = None
        if isinstance(payload, dict):
            api_key = payload.get("api_key") or payload.get("key") or payload.get("token") or payload.get("newsapi_api_key")

        if not api_key:
            await logger.error(f"NewsAPI api_key not found in credentials. Available keys: {list(payload.keys()) if isinstance(payload, dict) else 'unknown'}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "NewsAPI api_key not found in credentials",
                }
            }

        # Подготавливаем параметры
        q = config.get("q")
        country = config.get("country")
        category = config.get("category")
        sources = config.get("sources")
        page_size = config.get("pageSize")
        page = config.get("page")

        # Приведение типов
        try:
            if page_size is not None:
                page_size = int(page_size)
                page_size = min(page_size, 100)
        except Exception:
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "Invalid page_size parameter",
                }
            }
        try:
            if page is not None:
                page = int(page)
                page = max(page, 1)
        except Exception:
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "Invalid page parameter",
                }
            }
        try:
            client = NewsApiClient(api_key=api_key)
            # Вызываем библиотеку напрямую
            result = client.get_top_headlines(
                q=q,
                country=country,
                category=category,
                sources=sources,
                page_size=page_size,
                page=page,
            )

            # Ожидаемый результат — dict
            return {"response": {"ok": True, "result": result}}

        except NewsAPIException as e:
            await logger.error(f"NewsAPI error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": getattr(e, 'status_code', 500),
                    "description": str(e),
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error in NewsAPI integration: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e),
                }
            }
