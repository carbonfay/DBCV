"""YooKassa Refund Payment integration."""
from typing import Dict, Any, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger
from app.integrations.registry import registry

# Import library
try:
    import yookassa
    from yookassa import Configuration, Refund
    YOOKASSA_AVAILABLE = True
except ImportError:
    YOOKASSA_AVAILABLE = False
    Configuration = None
    Refund = None


class YooKassaRefundIntegration(BaseIntegration):
    """Интеграция для возврата (refund) платежа в YooKassa."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yookassa_refund",
            version="1.0.0",
            name="YooKassa Refund",
            description="Возврат платежа в YooKassa",
            category="payments",
            icon_s3_key="icons/integrations/yookassa.svg",
            color="#0070F0",
            config_schema={
                "type": "object",
                "required": ["payment_id", "amount_value", "amount_currency"],
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "title": "Payment ID",
                        "description": "ID платежа, по которому нужно сделать возврат"
                    },
                    "amount_value": {
                        "type": "string",
                        "title": "Amount Value",
                        "description": "Сумма возврата (например, '2.00')"
                    },
                    "amount_currency": {
                        "type": "string",
                        "title": "Currency",
                        "description": "Валюта возврата (например, 'RUB')",
                        "default": "RUB",
                        "enum": ["RUB", "USD", "EUR"]
                    },
                    "payment_mode": {
                        "type": "string",
                         "title": "Payment Method",
                         "description": "Способ перечисления возврата",
                         "enum": ["partial", "full"],
                         "default": "full"
                    },
                     "reason": {
                        "type": "string",
                        "title": "Reason",
                        "description": "Причина возврата (опционально, до 250 символов)"
                    }
                }
            },
            credentials_provider="yookassa",
            credentials_strategy="api_key",
            library_name="yookassa>=2.3.0" if YOOKASSA_AVAILABLE else None,
            examples=[
                {
                    "title": "Полный возврат",
                    "config": {
                        "payment_id": "2da5c87d-000f-5000-8000-18d169040000",
                        "amount_value": "100.00",
                        "amount_currency": "RUB",
                         "payment_mode": "full"
                    }
                },
                 {
                    "title": "Частичный возврат",
                    "config": {
                        "payment_id": "2da5c87d-000f-5000-8000-18d169040000",
                        "amount_value": "50.00",
                        "amount_currency": "RUB",
                        "payment_mode": "partial",
                        "reason": "Товар частично поврежден"
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
        """
        Выполняет возврат платежа используя библиотеку yookassa.
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
        creds = await credentials_resolver.get_single_for(
            bot_id=bot_id,
            provider="yookassa",
            strategy="api_key"
        )
        
        if not creds:
            await logger.error("YooKassa credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "YooKassa credentials not found"
                }
            }
        
        payload = creds.get("payload", creds)
        shop_id = payload.get("shop_id") or payload.get("account_id")
        secret_key = payload.get("secret_key")
        
        if not shop_id or not secret_key:
            await logger.error("shop_id or secret_key not found in credentials")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "shop_id or secret_key not found in credentials"
                }
            }
            
        try:
            # Настройка глобальной конфигурации YooKassa
            Configuration.configure(shop_id, secret_key)
            
            payment_id = config.get("payment_id")
            amount_value = config.get("amount_value")
            amount_currency = config.get("amount_currency", "RUB")
            reason = config.get("reason")
            
            if not payment_id:
                return {"response": {"ok": False, "error_code": 400, "description": "payment_id is required"}}
            
            if not amount_value:
                 return {"response": {"ok": False, "error_code": 400, "description": "amount_value is required"}}

            refund_data = {
                "payment_id": payment_id,
                "amount": {
                    "value": amount_value,
                    "currency": amount_currency
                }
            }
            
            if reason:
                refund_data["description"] = reason # В API параметр называется description, но мы назвали reason для понятности

            # Выполняем запрос на возврат
            refund = Refund.create(refund_data)
            
            # Сериализуем результат
            result_dict = {}
            if hasattr(refund, "json"):
                import json
                result_dict = json.loads(refund.json())
            elif hasattr(refund, "__dict__"):
                result_dict = refund.__dict__
            else:
                 result_dict = str(refund)

            return {
                "response": {
                    "ok": True,
                    "result": result_dict
                }
            }
            
        except Exception as e:
            await logger.error(f"YooKassa refund error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }

# Регистрируем интеграцию
registry.register(YooKassaRefundIntegration())
