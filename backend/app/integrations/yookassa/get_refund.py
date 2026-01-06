"""YooKassa Get Refund интеграция (получение данных возврата по refund_id)."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    from yookassa import Refund
    from yookassa.configuration import Configuration
    YOOKASSA_AVAILABLE = True
except ImportError:
    YOOKASSA_AVAILABLE = False
    Refund = None
    Configuration = None


class YooKassaGetRefundIntegration(BaseIntegration):
    """Интеграция для получения информации о возврате (refund) в YooKassa."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yookassa_get_refund",
            version="1.0.0",
            name="YooKassa Get Refund",
            description="Получить информацию о возврате (refund) по refund_id через API YooKassa",
            category="payments",
            icon_s3_key="icons/integrations/yookassa.svg",
            color="#6cc24a",
            config_schema={
                "type": "object",
                "required": ["refund_id"],
                "properties": {
                    "refund_id": {
                        "type": "string",
                        "title": "Refund ID",
                        "description": "ID возврата в YooKassa"
                    }
                }
            },
            # Рекомендация преподавателя: для api-key сервисов можно использовать provider other + api_key
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="yookassa>=2.3.0" if YOOKASSA_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить возврат по ID",
                    "config": {"refund_id": "216749b1-000f-50be-b000-0f8b4d2c0000"}
                }
            ],
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        if not YOOKASSA_AVAILABLE:
            await logger.error("yookassa library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "yookassa library is not installed",
                }
            }

        refund_id = config.get("refund_id")
        if not refund_id:
            await logger.error("refund_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "refund_id is required",
                }
            }

        # Получаем креды (provider=other, strategy=api_key)
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy="api_key",
        )
        if not creds:
            await logger.error("Credentials not found for provider=other strategy=api_key")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Credentials not found (provider=other, strategy=api_key)",
                }
            }

        payload = creds.get("payload", {}) or creds
        shop_id = payload.get("shop_id")
        secret_key = payload.get("secret_key")

        if not shop_id or not secret_key:
            await logger.error(f"shop_id/secret_key not found in credentials. Keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "shop_id and secret_key must be provided in credentials payload",
                }
            }

        try:
            Configuration.account_id = str(shop_id)
            Configuration.secret_key = str(secret_key)

            refund = Refund.find_one(str(refund_id))

            # SDK объект -> в dict
            if hasattr(refund, "__dict__"):
                result = refund.__dict__
            else:
                result = refund

            return {"response": {"ok": True, "result": result}}
        except Exception as e:
            await logger.error(f"YooKassa error: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
