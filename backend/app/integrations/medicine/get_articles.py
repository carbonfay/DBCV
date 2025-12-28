"""Medicine Get Articles integration using httpx."""
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from urllib.parse import urlparse

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


def _normalize_base_url(value: Any) -> Tuple[Optional[str], Optional[str]]:
    if not value or not isinstance(value, str) or not value.strip():
        return None, "base_url is required"
    base_url = value.strip()
    if not (base_url.startswith("http://") or base_url.startswith("https://")):
        return None, "base_url must start with http:// or https://"
    parsed = urlparse(base_url)
    if not parsed.scheme or not parsed.netloc:
        return None, "base_url must be a valid URL"
    return base_url, None


def _extract_api_key(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    api_key = payload.get("api_key") or payload.get("token") or payload.get("key")
    if api_key is None:
        return None, None, None
    if not isinstance(api_key, str) or not api_key.strip():
        return None, None, "api_key must be a non-empty string"
    api_key_header = payload.get("api_key_header") or "X-API-Key"
    return api_key.strip(), str(api_key_header), None


def _build_endpoint(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/api/v1/articles"


def _normalize_positive_int(value: Any, name: str, min_value: int = 1, max_value: Optional[int] = None) -> Optional[int]:
    if value is None:
        return None
    try:
        normalized = int(str(value).strip())
    except ValueError as err:
        raise ValueError(f"{name} must be an integer") from err
    if normalized < min_value:
        raise ValueError(f"{name} must be >= {min_value}")
    if max_value is not None and normalized > max_value:
        raise ValueError(f"{name} must be <= {max_value}")
    return normalized


def _normalize_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (list, tuple, dict)):
        raise ValueError("String parameters must be simple values")
    text = str(value).strip()
    return text or None


async def _fetch_articles(
    endpoint: str,
    headers: Dict[str, str],
    params: Dict[str, Any],
    logger: BotLogger,
) -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
    except httpx.HTTPStatusError as err:
        await logger.error(f"Medicine HTTP error: {err}")
        return None, {
            "response": {
                "ok": False,
                "error_code": err.response.status_code,
                "description": str(err),
            }
        }
    except httpx.RequestError as err:
        await logger.error(f"Medicine request error: {err}")
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
        await logger.error(f"Medicine response parse error: {err}")
        return None, {
            "response": {
                "ok": False,
                "error_code": 500,
                "description": "Invalid JSON in Medicine API response",
            }
        }

    return data, None


class MedicineGetArticlesIntegration(BaseIntegration):
    """Fetch medical articles from Medicine API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_get_articles",
            version="1.0.0",
            name="Medicine Get Articles",
            description="Fetch medical articles from Medicine API",
            category="medicine",
            icon_s3_key="icons/integrations/medicine.svg",
            color="#2E7D32",
            config_schema={
                "type": "object",
                "required": ["base_url"],
                "properties": {
                    "base_url": {
                        "type": "string",
                        "title": "Base URL",
                        "description": "Base URL of proxy that exposes /api/v1/articles (e.g. http://localhost:8003)",
                    },
                    "query": {
                        "type": "string",
                        "title": "Query",
                        "description": "Search term for articles (optional)",
                    },
                    "category": {
                        "type": "string",
                        "title": "Category",
                        "description": "Filter by category (optional)",
                    },
                    "tag": {
                        "type": "string",
                        "title": "Tag",
                        "description": "Filter by tag (optional)",
                    },
                    "source": {
                        "type": "string",
                        "title": "Source",
                        "description": "Filter by source (optional)",
                    },
                    "sort": {
                        "type": "string",
                        "title": "Sort",
                        "description": "Sort order (optional)",
                    },
                    "page": {
                        "type": "integer",
                        "title": "Page",
                        "minimum": 1,
                        "description": "Page number (optional)",
                    },
                    "page_size": {
                        "type": "integer",
                        "title": "Page Size",
                        "minimum": 1,
                        "maximum": 100,
                        "description": "Items per page (optional)",
                    },
                    "params": {
                        "type": "object",
                        "title": "Extra Params",
                        "description": "Additional query parameters passed to the API",
                        "additionalProperties": True,
                    },
                },
            },
            credentials_provider="medicine",
            credentials_strategy="api_key",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Get latest medical articles",
                    "config": {
                        "base_url": "https://medicine.example.com",
                    },
                },
                {
                    "title": "Search medical articles by query",
                    "config": {
                        "base_url": "https://medicine.example.com",
                        "query": "cardiology",
                        "page": 1,
                        "page_size": 10,
                    },
                },
                {
                    "title": "Filter medical articles by category",
                    "config": {
                        "base_url": "https://medicine.example.com",
                        "category": "research",
                        "sort": "recent",
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
        """
        Execute request to Medicine API GET /api/v1/articles.
        """
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="medicine",
            strategy="api_key",
        )

        payload = creds.get("payload", {}) if isinstance(creds, dict) else {}
        if not payload:
            payload = creds if isinstance(creds, dict) else {}

        base_url, base_url_error = _normalize_base_url(config.get("base_url"))
        if base_url_error:
            await logger.error(base_url_error)
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": base_url_error,
                }
            }

        api_key, api_key_header, api_key_error = _extract_api_key(payload)
        if api_key_error:
            await logger.error(api_key_error)
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": api_key_error,
                }
            }

        params: Dict[str, Any] = {}
        extra_params = config.get("params")
        if extra_params is not None:
            if not isinstance(extra_params, dict):
                await logger.error("params must be an object")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "params must be an object",
                    }
                }
            params.update(extra_params)

        try:
            query = _normalize_string(config.get("query"))
            category = _normalize_string(config.get("category"))
            tag = _normalize_string(config.get("tag"))
            source = _normalize_string(config.get("source"))
            sort = _normalize_string(config.get("sort"))
            page = _normalize_positive_int(config.get("page"), "page", min_value=1)
            page_size = _normalize_positive_int(config.get("page_size"), "page_size", min_value=1, max_value=100)
        except ValueError as err:
            await logger.error(str(err))
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": str(err),
                }
            }

        if query:
            params["query"] = query
        if category:
            params["category"] = category
        if tag:
            params["tag"] = tag
        if source:
            params["source"] = source
        if sort:
            params["sort"] = sort
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size

        endpoint = _build_endpoint(base_url)
        headers: Dict[str, str] = {}
        if api_key and api_key_header:
            headers[api_key_header] = api_key

        data, error_response = await _fetch_articles(endpoint, headers, params, logger)
        if error_response:
            return error_response

        return {
            "response": {
                "ok": True,
                "result": data,
            }
        }
