"""Stripe Refund интеграция используя stripe библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import stripe
    from stripe import StripeError
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None
    StripeError = Exception


class StripeRefundIntegration(BaseIntegration):
    """Интеграция для создания возврата платежа в Stripe."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="stripe_refund",
            version="1.0.0",
            name="Stripe Refund",
            description="Создание возврата платежа в Stripe",
            category="payments",
            icon_s3_key="icons/integrations/stripe.svg",
            color="#635bff",
            config_schema={
                "type": "object",
                "required": ["charge_id"],
                "properties": {
                    "charge_id": {
                        "type": "string",
                        "title": "Charge ID",
                        "description": "ID платежа (charge) или payment intent для возврата"
                    },
                    "amount": {
                        "type": "integer",
                        "title": "Amount",
                        "description": "Сумма возврата в центах (если не указана, возвращается полная сумма)"
                    },
                    "reason": {
                        "type": "string",
                        "title": "Reason",
                        "description": "Причина возврата",
                        "enum": ["duplicate", "fraudulent", "requested_by_customer"],
                        "default": None
                    },
                    "metadata": {
                        "type": "object",
                        "title": "Metadata",
                        "description": "Дополнительные метаданные для возврата"
                    }
                }
            },
            credentials_provider="stripe",
            credentials_strategy="api_key",
            library_name="stripe>=7.0.0" if STRIPE_AVAILABLE else None,
            examples=[
                {
                    "title": "Полный возврат платежа",
                    "config": {
                        "charge_id": "ch_1234567890"
                    }
                },
                {
                    "title": "Частичный возврат",
                    "config": {
                        "charge_id": "ch_1234567890",
                        "amount": 1000,
                        "reason": "requested_by_customer"
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
        Выполняет интеграцию используя библиотеку stripe.
        
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
        """
        if not STRIPE_AVAILABLE:
            await logger.error("stripe library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "stripe library is not installed"
                }
            }
        
        # Получаем api_key из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="stripe",
            strategy="api_key"
        )
        
        if not creds:
            await logger.error("Stripe credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Stripe api_key not found in credentials"
                }
            }
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        api_key = payload.get("api_key")
        if not api_key:
            await logger.error(f"api_key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "api_key not found in credentials"
                }
            }
        
        # Устанавливаем API ключ
        stripe.api_key = api_key
        
        # Получаем параметры из config
        charge_id = config.get("charge_id")
        amount = config.get("amount")
        reason = config.get("reason")
        metadata = config.get("metadata")
        
        if not charge_id:
            await logger.error("charge_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "charge_id is required"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем параметры для возврата
            refund_params = {}
            
            # Определяем, это charge или payment_intent
            if charge_id.startswith("ch_"):
                refund_params["charge"] = charge_id
            elif charge_id.startswith("pi_"):
                refund_params["payment_intent"] = charge_id
            else:
                # Пробуем как charge по умолчанию
                refund_params["charge"] = charge_id
            
            if amount is not None:
                refund_params["amount"] = int(amount)
            
            if reason:
                refund_params["reason"] = reason
            
            if metadata:
                refund_params["metadata"] = metadata
            
            # Создаем возврат
            refund = stripe.Refund.create(**refund_params)
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": refund.id,
                        "status": refund.status,
                        "amount": refund.amount,
                        "currency": refund.currency,
                        "charge": refund.charge,
                        "created": refund.created,
                        "reason": refund.reason if hasattr(refund, "reason") else None
                    }
                }
            }
        except StripeError as e:
            await logger.error(f"Stripe error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.http_status if hasattr(e, "http_status") else 500,
                    "description": str(e)
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }

