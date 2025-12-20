"""YooKassa Create Receipt integration using yookassa SDK.

This integration creates a receipt (check) via the YooKassa SDK `Receipt.create`.
"""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Try to import the SDK directly
try:
    from yookassa import Receipt, Configuration  # type: ignore
    from yookassa.domain.exceptions import ApiError  # type: ignore
    YOOKASSA_AVAILABLE = True
except Exception:
    Receipt = None
    Configuration = None
    ApiError = Exception
    YOOKASSA_AVAILABLE = False


class YoukassaCreateReceiptIntegration(BaseIntegration):
    """Создание чека (receipt) в YooKassa через `yookassa` SDK."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="youkassa_create_receipt",
            version="1.0.0",
            name="YouKassa Create Receipt",
            description="Создание фискального чека через YooKassa SDK",
            category="payments",
            icon_s3_key="icons/integrations/youkassa.svg",
            color="#ff6a00",
            config_schema={
                "type": "object",
                "required": ["payment_id", "items"],
                "properties": {
                    "payment_id": {"type": "string", "title": "Payment ID", "description": "ID платежа, для которого формируется чек"},
                    "type": {"type": "string", "title": "Type", "description": "Тип чека: payment/refund"},
                    "send": {"type": "boolean", "title": "Send to customer", "description": "Отправить чек клиенту"},
                    "customer": {"type": "object", "title": "Customer", "description": "Данные покупателя"},
                    "items": {"type": "array", "items": {"type": "object"}, "title": "Items", "description": "Список позиций"},
                    "settlements": {"type": "array", "items": {"type": "object"}, "title": "Settlements"}
                }
            },
            credentials_provider="youkassa",
            credentials_strategy="api_key",
            library_name="yookassa>=2.3.0" if YOOKASSA_AVAILABLE else None,
            examples=[
                {
                    "title": "Создать чек для платежа",
                    "config": {
                        "payment_id": "21b23b5b-000f-5061-a000-0674e49a8c10",
                        "type": "payment",
                        "send": True,
                        "items": [
                            {"description": "Product 1", "quantity": 1, "amount": {"value": "100.00", "currency": "RUB"}, "vat_code": "2", "payment_mode": "full_payment", "payment_subject": "commodity"}
                        ]
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
        """Создает чек через yookassa SDK.

        Args:
            config: Параметры запроса (см. config_schema)
        """
        if not YOOKASSA_AVAILABLE:
            await logger.error("yookassa library is not available")
            return {
                "response": {"ok": False, "error_code": 500, "description": "yookassa library is not installed"}
            }

        # Basic validation
        payment_id = config.get("payment_id")
        items = config.get("items")
        if not payment_id or not items:
            await logger.error("payment_id and items are required to create a receipt")
            return {
                "response": {"ok": False, "error_code": 400, "description": "payment_id and items are required"}
            }

        # Получаем credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="youkassa",
            strategy="api_key"
        )

        if not creds:
            await logger.error("YouKassa credentials not found")
            return {"response": {"ok": False, "error_code": 401, "description": "YouKassa credentials not found"}}

        payload = creds.get("payload", {}) if isinstance(creds, dict) else {}
        if not payload:
            payload = creds if isinstance(creds, dict) else {}

        account_id = (
            payload.get("account_id") or payload.get("shop_id") or payload.get("shopId") or payload.get("accountId")
        )
        secret_key = (
            payload.get("secret_key") or payload.get("secret") or payload.get("secretKey") or payload.get("token")
        )
        oauth_token = payload.get("oauth_token") or payload.get("auth_token") or payload.get("authToken")

        if oauth_token and Configuration and hasattr(Configuration, "configure_auth_token"):
            try:
                Configuration.configure_auth_token(str(oauth_token))
            except Exception as e:
                await logger.error(f"Failed to configure yookassa auth token: {e}")
                return {"response": {"ok": False, "error_code": 500, "description": "Failed to configure yookassa auth token"}}
        elif account_id and secret_key and Configuration and hasattr(Configuration, "configure"):
            try:
                Configuration.configure(str(account_id), str(secret_key))
            except Exception as e:
                await logger.error(f"Failed to configure yookassa credentials: {e}")
                return {"response": {"ok": False, "error_code": 500, "description": "Failed to configure yookassa credentials"}}
        else:
            await logger.error("YouKassa credentials are missing required fields (account_id and secret_key or oauth_token)")
            return {"response": {"ok": False, "error_code": 401, "description": "YouKassa credentials are missing required fields (account_id and secret_key or oauth_token)"}}

        try:
            # Вызываем SDK
            res = Receipt.create(config)  # type: ignore

            # Преобразуем результат в словарь
            if hasattr(res, "to_dict"):
                result = res.to_dict()
            elif hasattr(res, "__dict__"):
                result = {k: v for k, v in vars(res).items() if not k.startswith("_")}
            else:
                result = str(res)

            return {"response": {"ok": True, "result": result}}
        except ApiError as e:  # type: ignore
            await logger.error(f"YouKassa API error creating receipt: {e}")
            return {"response": {"ok": False, "error_code": getattr(e, 'http_code', 500), "description": str(e)}}
        except Exception as e:
            await logger.error(f"Unexpected error creating receipt: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
