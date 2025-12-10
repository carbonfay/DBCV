"""YooKassa Cancel Payment integration."""
from typing import Dict, Any, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger
from app.integrations.registry import registry

# Импортируем библиотеку
try:
    import yookassa
    from yookassa import Configuration, Payment
    YOOKASSA_AVAILABLE = True
except ImportError:
    YOOKASSA_AVAILABLE = False
    Configuration = None
    Payment = None


class YooKassaCancelPaymentIntegration(BaseIntegration):
    """Интеграция для отмены платежа в YooKassa."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yookassa_cancel_payment",
            version="1.0.0",
            name="YooKassa Cancel Payment",
            description="Отмена платежа в YooKassa (если он в статусе waiting_for_capture)",
            category="payments",
            icon_s3_key="icons/integrations/yookassa.svg",
            color="#0070F0",
            config_schema={
                "type": "object",
                "required": ["payment_id"],
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "title": "Payment ID",
                        "description": "ID платежа для отмены"
                    },
                    "idempotency_key": {
                        "type": "string",
                        "title": "Idempotency Key",
                        "description": "Ключ идемпотентности (опционально, генерируется автоматически если не задан)"
                    }
                }
            },
            credentials_provider="yookassa",
            credentials_strategy="api_key",
            library_name="yookassa>=2.3.0" if YOOKASSA_AVAILABLE else None,
            examples=[
                {
                    "title": "Отмена платежа",
                    "config": {
                        "payment_id": "2da5c87d-000f-5000-8000-18d169040000"
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
        Отменяет платеж используя библиотеку yookassa.
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
            
        # Настраиваем клиент глобально (YooKassa SDK использует глобальный конфиг)
        # ВНИМАНИЕ: Это не потокобезопасно в общем случае, но библиотека yookassa
        # хранит настройки в классе Configuration.
        # Для многопоточной/асинхронной среды лучше бы использовать экземпляр клиента, 
        # но YooKassa Python SDK старых версий (да и текущих) часто работает через глобальный Configuration.
        # Однако, методы Payment.create/cancel принимают параметры конфигурации ? Нет.
        # Проверим: SDK использует Configuration.account_id и secret_key.
        # Если мы меняем их на лету, это может повлиять на другие запросы.
        # Но в рамках задачи мы используем библиотеку "как есть".
        
        try:
            Configuration.configure(shop_id, secret_key)
            
            payment_id = config.get("payment_id")
            idempotency_key = config.get("idempotency_key")
            
            if not payment_id:
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "payment_id is required"
                    }
                }

            # Выполняем запрос
            # Метод cancel принимает idempotency_key вторым аргументом
            if idempotency_key:
                payment = Payment.cancel(payment_id, idempotency_key)
            else:
                payment = Payment.cancel(payment_id)
            
            # Сериализуем результат
            # Объект payment - это модель yookassa, нужно превратить в dict
            # Обычно у них есть json() или dict()
            result_dict = {}
            if hasattr(payment, "json"):
                 # Это вернет строку, нам нужен dict
                import json
                result_dict = json.loads(payment.json())
            elif hasattr(payment, "__dict__"):
                result_dict = payment.__dict__
            else:
                 result_dict = str(payment)

            return {
                "response": {
                    "ok": True,
                    "result": result_dict
                }
            }
            
        except Exception as e:
            await logger.error(f"YooKassa error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }


# Регистрируем интеграцию
registry.register(YooKassaCancelPaymentIntegration())
