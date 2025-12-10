"""YooKassa Get Receipt integration."""
from typing import Dict, Any, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger
from app.integrations.registry import registry

# Import library
try:
    import yookassa
    from yookassa import Configuration, Receipt
    YOOKASSA_AVAILABLE = True
except ImportError:
    YOOKASSA_AVAILABLE = False
    Configuration = None
    Receipt = None


class YooKassaGetReceiptIntegration(BaseIntegration):
    """Интеграция для получения информации о чеке в YooKassa."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yookassa_get_receipt",
            version="1.0.0",
            name="YooKassa Get Receipt",
            description="Получить информацию о чеке по его ID",
            category="payments",
            icon_s3_key="icons/integrations/yookassa.svg",
            color="#0070F0",
            config_schema={
                "type": "object",
                "required": ["receipt_id"],
                "properties": {
                    "receipt_id": {
                        "type": "string",
                        "title": "Receipt ID",
                        "description": "ID чека в YooKassa"
                    }
                }
            },
            credentials_provider="yookassa",
            credentials_strategy="api_key",
            library_name="yookassa>=2.3.0" if YOOKASSA_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить информацию о чеке",
                    "config": {
                        "receipt_id": "rt_1da5c87d-000f-5000-8000-18d169040000"
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
        Получает информацию о чеке используя библиотеку yookassa.
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
            
            receipt_id = config.get("receipt_id")
            
            if not receipt_id:
                return {"response": {"ok": False, "error_code": 400, "description": "receipt_id is required"}}
            
            # Выполняем запрос на получение чека
            # Используем find(receipt_id)
            receipt = Receipt.find(receipt_id)
            
            # Сериализуем результат
            result_dict = {}
            if hasattr(receipt, "json"):
                import json
                result_dict = json.loads(receipt.json())
            elif hasattr(receipt, "__dict__"):
                result_dict = receipt.__dict__
            else:
                 result_dict = str(receipt)

            return {
                "response": {
                    "ok": True,
                    "result": result_dict
                }
            }
            
        except Exception as e:
            await logger.error(f"YooKassa get receipt error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }

# Регистрируем интеграцию
registry.register(YooKassaGetReceiptIntegration())
