"""YooKassa Get Payments integration using yookassa SDK.

This integration uses the official `yookassa` Python SDK (recommended >=2.3.0)
and returns a filtered list of payments.
"""
from typing import Dict, Any, List
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


class YoukassaGetPaymentsIntegration(BaseIntegration):
    """Получение списка платежей из YooKassa через `yookassa` SDK."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="youkassa_get_payments",
            version="1.0.0",
            name="YouKassa Get Payments",
            description="Получение списка платежей с возможностью фильтрации через YooKassa SDK",
            category="payments",
            icon_s3_key="icons/integrations/youkassa.svg",
            color="#ff6a00",
            config_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "title": "Limit", "description": "Максимальное количество элементов в ответе"},
                    "payment_method": {"type": "string", "title": "Payment Method", "description": "Фильтр по способу оплаты (например, 'yoo_money')"},
                    "status": {"type": "string", "title": "Status", "description": "Фильтр по статусу платежа"},
                    "created_at.gte": {"type": "string", "title": "Created At GTE", "description": "Дата создания (>=) в формате ISO 8601"},
                    "created_at.lt": {"type": "string", "title": "Created At LT", "description": "Дата создания (<) в формате ISO 8601"},
                    "cursor": {"type": "string", "title": "Cursor", "description": "Курсор для пагинации"}
                }
            },
            credentials_provider="youkassa",
            credentials_strategy="api_key",
            library_name="yookassa>=2.3.0" if YOOKASSA_AVAILABLE else None,
            examples=[
                {
                    "title": "Список платежей (limit)",
                    "config": {"limit": 5}
                },
                {
                    "title": "Фильтр по времени и способу оплаты",
                    "config": {"limit": 10, "payment_method": "yoo_money", "created_at.gte": "2023-01-01T00:00:00.000Z"}
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
        """Выполнение запроса списка платежей через yookassa SDK.

        Args:
            config: Параметры интеграции (фильтры)
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота
            logger: Логгер

        Returns:
            dict с результатом в формате системы
        """
        if not YOOKASSA_AVAILABLE:
            await logger.error("yookassa library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "yookassa library is not installed"
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

        # payload может быть в creds['payload'] или в корне
        payload = creds.get("payload", {}) if isinstance(creds, dict) else {}
        if not payload:
            payload = creds if isinstance(creds, dict) else {}

        # Поддерживаем несколько ключей для гибкости
        account_id = (
            payload.get("account_id") or payload.get("shop_id") or payload.get("shopId") or payload.get("accountId")
        )
        secret_key = (
            payload.get("secret_key") or payload.get("secret") or payload.get("secretKey") or payload.get("token")
        )

        # Если есть OAuth token
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

        # Подготавливаем параметры фильтрации
        allowed_keys = {"limit", "payment_method", "status", "created_at.gte", "created_at.lt", "cursor"}
        params: Dict[str, Any] = {}
        for k in allowed_keys:
            if k in config and config.get(k) is not None:
                params[k] = config.get(k)

        try:
            # Вызываем SDK напрямую
            res = Payment.list(params)  # type: ignore

            # Конвертируем ответ в простую структуру
            items_raw = getattr(res, "items", []) or []
            items: List[Any] = []
            for it in items_raw:
                if hasattr(it, "to_dict"):
                    try:
                        items.append(it.to_dict())
                        continue
                    except Exception:
                        pass
                if hasattr(it, "__dict__"):
                    try:
                        items.append({k: v for k, v in vars(it).items() if not k.startswith("_")})
                        continue
                    except Exception:
                        pass
                # Fallback
                items.append(str(it))

            next_cursor = getattr(res, "next_cursor", None) if res is not None else None

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "items": items,
                        "next_cursor": next_cursor
                    }
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
            await logger.error(f"Unexpected error while listing payments: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
