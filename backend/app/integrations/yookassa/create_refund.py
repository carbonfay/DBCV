"""YooKassa Create Refund интеграция используя официальную библиотеку yookassa."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем yookassa для работы с API
try:
    from yookassa import Configuration, Refund
    YOOKASSA_AVAILABLE = True
except ImportError:
    YOOKASSA_AVAILABLE = False
    Configuration = None
    Refund = None


class YooKassaCreateRefundIntegration(BaseIntegration):
    """Интеграция для создания возврата платежа через YooKassa API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yookassa_create_refund",
            version="1.0.0",
            name="YooKassa Create Refund",
            description="Создание возврата платежа через YooKassa API",
            category="payments",
            icon_s3_key="icons/integrations/yookassa.svg",
            color="#FFDB4D",
            config_schema={
                "type": "object",
                "required": ["payment_id", "amount"],
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "title": "Payment ID",
                        "description": "ID платежа, для которого создается возврат (например: 21740069-000f-50be-b000-0486ffbf45b0)"
                    },
                    "amount": {
                        "type": "object",
                        "title": "Amount",
                        "required": ["value", "currency"],
                        "properties": {
                            "value": {
                                "type": "string",
                                "title": "Value",
                                "description": "Сумма возврата (например: \"2.00\")"
                            },
                            "currency": {
                                "type": "string",
                                "title": "Currency",
                                "enum": ["RUB", "USD", "EUR"],
                                "default": "RUB",
                                "description": "Валюта возврата (RUB, USD, EUR)"
                            }
                        }
                    },
                    "description": {
                        "type": "string",
                        "title": "Description",
                        "description": "Описание возврата (необязательно)"
                    }
                }
            },
            credentials_provider="yookassa",
            credentials_strategy="api_key",
            library_name="yookassa>=2.3.0" if YOOKASSA_AVAILABLE else None,
            examples=[
                {
                    "title": "Создать полный возврат платежа",
                    "config": {
                        "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
                        "amount": {
                            "value": "100.00",
                            "currency": "RUB"
                        },
                        "description": "Возврат по заказу #1234"
                    }
                },
                {
                    "title": "Создать частичный возврат",
                    "config": {
                        "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
                        "amount": {
                            "value": "50.00",
                            "currency": "RUB"
                        }
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
        Выполняет интеграцию используя официальную библиотеку yookassa.
        
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
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
        
        # Получаем credentials из YooKassa
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
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        shop_id = payload.get("shop_id") or payload.get("shopId") or payload.get("account_id") or payload.get("accountId")
        secret_key = payload.get("secret_key") or payload.get("secretKey")
        
        if not shop_id or not secret_key:
            await logger.error(f"shop_id or secret_key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "shop_id and secret_key are required in YooKassa credentials"
                }
            }
        
        # Настраиваем Configuration для yookassa
        Configuration.account_id = shop_id
        Configuration.secret_key = secret_key
        
        # Получаем параметры из config
        payment_id = config.get("payment_id")
        amount_config = config.get("amount", {})
        description = config.get("description")
        
        if not payment_id:
            await logger.error("payment_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "payment_id is required"
                }
            }
        
        if not amount_config:
            await logger.error("amount is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "amount is required"
                }
            }
        
        amount_value = amount_config.get("value")
        amount_currency = amount_config.get("currency", "RUB")
        
        if not amount_value:
            await logger.error("amount.value is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "amount.value is required"
                }
            }
        
        # Формируем данные для создания возврата
        refund_data = {
            "payment_id": payment_id,
            "amount": {
                "value": amount_value,
                "currency": amount_currency
            }
        }
        
        if description:
            refund_data["description"] = description
        
        try:
            # Создаем возврат через YooKassa API
            await logger.info(f"Creating refund for payment {payment_id}, amount: {amount_value} {amount_currency}")
            refund = Refund.create(refund_data)
            
            # Преобразуем результат в словарь для возврата
            refund_dict = {
                "id": refund.id,
                "status": refund.status,
                "amount": {
                    "value": refund.amount.value,
                    "currency": refund.amount.currency
                },
                "created_at": refund.created_at.isoformat() if hasattr(refund.created_at, 'isoformat') else str(refund.created_at),
                "payment_id": refund.payment_id
            }
            
            if hasattr(refund, 'description') and refund.description:
                refund_dict["description"] = refund.description
            
            if hasattr(refund, 'refund_authorization_details') and refund.refund_authorization_details:
                refund_dict["refund_authorization_details"] = {
                    "rrn": refund.refund_authorization_details.rrn if hasattr(refund.refund_authorization_details, 'rrn') else None
                }
            
            if hasattr(refund, 'metadata') and refund.metadata:
                refund_dict["metadata"] = dict(refund.metadata) if hasattr(refund.metadata, '__iter__') else refund.metadata
            
            await logger.info(f"Successfully created refund {refund.id} with status {refund.status}")
            
            return {
                "response": {
                    "ok": True,
                    "result": refund_dict
                }
            }
            
        except Exception as e:
            error_message = str(e)
            await logger.error(f"YooKassa API error: {error_message}")
            
            # Пытаемся определить тип ошибки
            error_code = 500
            if "404" in error_message or "not found" in error_message.lower():
                error_code = 404
            elif "401" in error_message or "unauthorized" in error_message.lower() or "authentication" in error_message.lower():
                error_code = 401
            elif "403" in error_message or "forbidden" in error_message.lower():
                error_code = 403
            elif "400" in error_message or "bad request" in error_message.lower():
                error_code = 400
            elif "429" in error_message or "rate limit" in error_message.lower():
                error_code = 429
            
            import traceback
            traceback_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            await logger.error(f"Traceback: {traceback_str}")
            
            return {
                "response": {
                    "ok": False,
                    "error_code": error_code,
                    "description": error_message
                }
            }
