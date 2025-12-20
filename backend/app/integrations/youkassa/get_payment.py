"""YooKassa Get Payment (by id) integration using yookassa SDK.

This integration retrieves a single payment by its ID using the official `yookassa` SDK.
"""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Try to import the SDK directly
try:
    from yookassa import Payment, Configuration  # type: ignore
    from yookassa.domain.exceptions import ApiError  # type: ignore
    YOOKASSA_AVAILABLE = True
except Exception:
    Payment = None
    Configuration = None
    ApiError = Exception
    YOOKASSA_AVAILABLE = False


class YoukassaGetPaymentIntegration(BaseIntegration):
    """Получение информации о платеже по ID через `yookassa` SDK."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="youkassa_get_payment",
            version="1.0.0",
            name="YouKassa Get Payment",
            description="Получение информации о платеже по его ID через YooKassa SDK",
            category="payments",
            icon_s3_key="icons/integrations/youkassa.svg",
            color="#ff6a00",
            config_schema={
                "type": "object",
                "required": ["payment_id"],
                "properties": {
                    "payment_id": {"type": "string", "title": "Payment ID", "description": "ID платежа (например, '21b23b5b-...')"}
                }
            },
            credentials_provider="youkassa",
            credentials_strategy="api_key",
            library_name="yookassa>=2.3.0" if YOOKASSA_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить платёж по ID",
                    "config": {"payment_id": "21b23b5b-000f-5061-a000-0674e49a8c10"}
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
        """Выполняет получение платежа по ID через yookassa SDK."""
        if not YOOKASSA_AVAILABLE:
            await logger.error("yookassa library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "yookassa library is not installed"
                }
            }

        payment_id = config.get("payment_id")
        if not payment_id:
            await logger.error("payment_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "payment_id is required"
                }
            }

        # Получаем credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="youkassa",
            strategy="api_key"
        )

        if not creds:
            await logger.error("YouKassa credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "YouKassa credentials not found"
                }
            }

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
                return {
                    "response": {
                        "ok": False,
                        "error_code": 500,
                        "description": "Failed to configure yookassa auth token"
                    }
                }
        elif account_id and secret_key and Configuration and hasattr(Configuration, "configure"):
            try:
                Configuration.configure(str(account_id), str(secret_key))
            except Exception as e:
                await logger.error(f"Failed to configure yookassa credentials: {e}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 500,
                        "description": "Failed to configure yookassa credentials"
                    }
                }
        else:
            await logger.error("YouKassa credentials are missing required fields (account_id and secret_key or oauth_token)")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "YouKassa credentials are missing required fields (account_id and secret_key or oauth_token)"
                }
            }

        try:
            # Используем SDK напрямую
            res = Payment.find_one(str(payment_id))  # type: ignore

            # Попытка привести ответ к словарю
            if hasattr(res, "to_dict"):
                result = res.to_dict()
            elif hasattr(res, "__dict__"):
                result = {k: v for k, v in vars(res).items() if not k.startswith("_")}
            else:
                result = str(res)

            return {
                "response": {
                    "ok": True,
                    "result": result
                }
            }
        except ApiError as e:  # type: ignore
            await logger.error(f"YouKassa API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": getattr(e, 'http_code', 500),
                    "description": str(e)
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error while getting payment: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
