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
    from yookassa import Payment, Configuration
    from yookassa.domain.exceptions import ApiError
    YOOKASSA_AVAILABLE = True
except ImportError:
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
            credentials_provider="other",
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
            provider="other",
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

        # Извлекаем payload: ожидается словарь в поле 'payload'.
        # Фолбэк: если 'account_id' и 'secret_key' находятся в корне, используем весь словарь как payload.
        payload = None
        if isinstance(creds, dict):
            payload = creds.get("payload", creds)
        if not isinstance(payload, dict):
            await logger.error("YouKassa credentials missing 'payload' dict")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Invalid credentials format: 'payload' dict is required"
                }
            }

        # Извлекаем account_id и secret_key
        # Support both 'shop_id' and 'account_id' as per PR #44
        account_id = str(payload.get("shop_id") or payload.get("account_id") or "").strip()
        # Primary key name is 'secret_key'; allow 'api_key' as fallback for robustness
        secret_key = str(payload.get("secret_key") or payload.get("api_key") or "").strip()

        if not account_id or not secret_key:
            safe_keys = sorted([k for k in payload.keys()])
            await logger.error(f"Missing shop_id/account_id or secret_key in payload; available keys={safe_keys}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": f"YooKassa credentials {payload} missing 'shop_id/account_id' or 'secret_key' in payload"
                }
            }

        # Настройка аутентификации
        try:
            Configuration.configure(str(account_id), str(secret_key))
            await logger.info(f"Configured YooKassa with account_id={account_id}")
        except Exception as e:
            await logger.error(f"Failed to configure YooKassa authentication: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Failed to configure authentication: {str(e)}"
                }
            }

        # Подготавливаем параметры фильтрации
        allowed_keys = {"limit", "payment_method", "status", "created_at.gte", "created_at.lt", "cursor"}
        params: Dict[str, Any] = {}
        for k in allowed_keys:
            if k in config and config.get(k) is not None:
                params[k] = config.get(k)

        try:
            # Вызываем SDK
            res = Payment.list(params)

            items_raw = getattr(res, "items", []) or []
            items: List[Any] = []
            for it in items_raw:
                if hasattr(it, "to_dict"):
                    try:
                        items.append(it.to_dict())
                    except Exception as e:
                        items.append(str(it))
                elif hasattr(it, "__dict__"):
                    try:
                        items.append({k: v for k, v in vars(it).items() if not k.startswith("_")})
                    except Exception:
                        items.append(str(it))
                else:
                    items.append(str(it))

            next_cursor = getattr(res, "next_cursor", None)

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "items": items,
                        "next_cursor": next_cursor
                    }
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
            await logger.error(f"Unexpected error while listing payments: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
