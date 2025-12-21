"""Get Drug Info интеграция используя прямые HTTP запросы через httpx."""
from typing import Dict, Any, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Используем httpx напрямую для запросов к медицинским справочникам
try:
    import httpx
    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover - окружение может не иметь httpx
    httpx = None
    HTTPX_AVAILABLE = False


class MedicineGetDrugInfoIntegration(BaseIntegration):
    """Интеграция для получения информации о препарате по ID через внешний справочник."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_get_drug_info",
            version="1.0.0",
            name="Medicine Get Drug Info",
            description="Получить информацию о лекарственном препарате по ID через внешний медицинский справочник",
            category="medicine",
            icon_s3_key="icons/integrations/medicine.svg",
            color="#9C27B0",
            config_schema={
                "type": "object",
                "required": ["drug_id"],
                "properties": {
                    "drug_id": {
                        "type": "string",
                        "title": "Drug ID",
                        "description": "Идентификатор препарата в справочнике (например, numeric id или код)"
                    },
                    "base_url": {
                        "type": "string",
                        "title": "Base URL",
                        "description": "Базовый URL внешнего справочника, например https://api.example.com",
                        "default": "https://api.example.com"
                    },
                    "fields": {
                        "type": "array",
                        "title": "Fields",
                        "description": "Список полей, которые нужно вернуть (по возможности)",
                        "items": {"type": "string"}
                    }
                }
            },
            credentials_provider="medicine",
            credentials_strategy="api_key",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Get drug by id",
                    "config": {
                        "drug_id": "12345",
                        "base_url": "https://api.example-med.com"
                    }
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
        """Выполняет запрос к внешнему медицинскому API и возвращает результат.

        Ожидаемые config-параметры:
          - drug_id (required)
          - base_url (optional)
          - fields (optional)
        """
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "httpx library is not installed"
                }
            }

        drug_id = config.get("drug_id")
        base_url = config.get("base_url", "https://api.example.com")
        fields = config.get("fields")

        if not drug_id:
            await logger.error("drug_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "drug_id is required"
                }
            }

        # Получаем credentials через credentials_resolver
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id, provider="medicine", strategy="api_key"
        )

        api_key: Optional[str] = None
        if creds:
            payload = creds.get("payload", {}) or creds
            api_key = payload.get("api_key") or payload.get("key") or payload.get("token")

        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            headers["X-API-Key"] = api_key

        url = f"{base_url.rstrip('/')}/api/v1/drugs/{drug_id}"

        params = {}
        if fields and isinstance(fields, (list, tuple)):
            params["fields"] = ",".join(fields)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()

                try:
                    data = response.json()
                except Exception:
                    data = {"raw": response.text}

                return {
                    "response": {
                        "ok": True,
                        "result": data
                    }
                }

        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else 500
            text = e.response.text if e.response is not None else str(e)
            await logger.error(f"HTTP error from medicine API: {status} - {text}")
            return {
                "response": {
                    "ok": False,
                    "error_code": status,
                    "description": text
                }
            }
        except httpx.RequestError as e:
            await logger.error(f"Request error to medicine API: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 502,
                    "description": str(e)
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error in medicine_get_drug_info: {e}")
            import traceback
            traceback_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            await logger.error(f"Traceback: {traceback_str}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
