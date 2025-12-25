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
    from yookassa import Payment, Configuration
    from yookassa.domain.exceptions import ApiError
    YOOKASSA_AVAILABLE = True
except ImportError:
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
            credentials_provider="other",  # Исправлено: должно быть "other", как в get_payments
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
            provider="other",  # Исправлено: теперь соответствует get_payments
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

        # Извлекаем payload: может быть в `payload` или в корне
        payload = creds.get("payload", creds) if isinstance(creds, dict) else {}
        if not isinstance(payload, dict):
            await logger.error("YouKassa credentials payload is not a dictionary")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Invalid credential format: payload must be a dictionary"
                }
            }

        account_id = (
            payload.get("account_id") or 
            payload.get("shop_id") or 
            payload.get("shopId") or 
            payload.get("accountId")
        )
        secret_key = (
            payload.get("secret_key") or 
            payload.get("api_key") or 
            payload.get("secretKey") or 
            payload.get("apiKey") or
            payload.get("secret")
        )
        oauth_token = (
            payload.get("oauth_token") or 
            payload.get("auth_token") or 
            payload.get("authToken") or
            payload.get("token")
        )

        # Логгируем наличие полей (без вывода значений)
        await logger.debug(f"Found credentials: account_id={bool(account_id)}, secret_key={bool(secret_key)}, oauth_token={bool(oauth_token)}")

        # Настройка аутентификации
        try:
            if oauth_token:
                Configuration.configure_auth_token(oauth_token)
                await logger.info("Configured YooKassa with OAuth token")
            elif account_id and secret_key:
                Configuration.configure(str(account_id), str(secret_key))
                await logger.info(f"Configured YooKassa with account_id={account_id}")
            else:
                await logger.error(
                    "Missing required credentials: need either 'oauth_token' or 'account_id' and 'secret_key'"
                )
                return {
                    "response": {
                        "ok": False,
                        "error_code": 401,
                        "description": "YouKassa credentials are missing required fields: need either 'oauth_token' or 'account_id' and 'secret_key'"
                    }
                }
        except Exception as e:
            await logger.error(f"Failed to configure YooKassa authentication: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Failed to configure authentication: {str(e)}"
                }
            }

        try:
            # Получаем платеж по ID
            res = Payment.find_one(str(payment_id))

            # Конвертируем ответ
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
        except ApiError as e:
            status_code = getattr(e, "http_code", 500)
            await logger.error(f"YouKassa API error [{status_code}]: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": status_code,
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
