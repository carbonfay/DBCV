"""PayPal Create Payout интеграция используя paypal-payouts-sdk библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    from paypalpayoutssdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment
    from paypalpayoutssdk.payouts import PayoutsPostRequest
    from paypalhttp import HttpError
    PAYPAL_SDK_AVAILABLE = True
except ImportError:
    PAYPAL_SDK_AVAILABLE = False
    PayPalHttpClient = None
    SandboxEnvironment = None
    LiveEnvironment = None
    PayoutsPostRequest = None
    HttpError = Exception


class PayPalCreatePayoutIntegration(BaseIntegration):
    """Интеграция для создания выплаты (Payout) через PayPal Payouts API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="paypal_create_payout",
            version="1.0.0",
            name="PayPal Create Payout",
            description="Создание выплаты (Payout) через PayPal Payouts API",
            category="payments",
            icon_s3_key="icons/integrations/paypal.svg",
            color="#0070ba",
            config_schema={
                "type": "object",
                "required": ["sender_batch_id", "email_subject", "currency", "items"],
                "properties": {
                    "sender_batch_id": {
                        "type": "string",
                        "title": "Sender Batch ID",
                        "description": "Уникальный идентификатор выплаты (максимум 127 символов)"
                    },
                    "email_subject": {
                        "type": "string",
                        "title": "Email Subject",
                        "description": "Тема письма получателю"
                    },
                    "currency": {
                        "type": "string",
                        "title": "Currency",
                        "description": "Валюта выплаты (например, USD, EUR, RUB)",
                        "pattern": "^[A-Z]{3}$"
                    },
                    "items": {
                        "type": "array",
                        "title": "Payout Items",
                        "description": "Список выплат",
                        "items": {
                            "type": "object",
                            "required": ["receiver", "amount", "recipient_type"],
                            "properties": {
                                "receiver": {
                                    "type": "string",
                                    "title": "Receiver",
                                    "description": "Email или PayPal ID получателя"
                                },
                                "amount": {
                                    "type": "number",
                                    "title": "Amount",
                                    "description": "Сумма выплаты (должна быть положительным числом)",
                                    "minimum": 0.01
                                },
                                "note": {
                                    "type": "string",
                                    "title": "Note",
                                    "description": "Комментарий получателю (опционально)"
                                },
                                "recipient_type": {
                                    "type": "string",
                                    "title": "Recipient Type",
                                    "description": "Тип получателя",
                                    "enum": ["EMAIL", "PAYPAL_ID"],
                                    "default": "EMAIL"
                                },
                                "sender_item_id": {
                                    "type": "string",
                                    "title": "Sender Item ID",
                                    "description": "Уникальный идентификатор элемента выплаты (опционально)"
                                }
                            }
                        },
                        "minItems": 1,
                        "maxItems": 5000
                    },
                    "environment": {
                        "type": "string",
                        "title": "Environment",
                        "description": "Окружение PayPal (sandbox или live)",
                        "enum": ["sandbox", "live"],
                        "default": "sandbox"
                    }
                }
            },
            credentials_provider="paypal",
            credentials_strategy="oauth",
            library_name="paypal-payouts-sdk>=1.0.0" if PAYPAL_SDK_AVAILABLE else None,
            examples=[
                {
                    "title": "Одиночная выплата по email",
                    "config": {
                        "sender_batch_id": "batch_001",
                        "email_subject": "Вам поступил платеж!",
                        "currency": "USD",
                        "items": [
                            {
                                "receiver": "[email protected]",
                                "amount": 10.00,
                                "note": "Спасибо за вашу работу!",
                                "recipient_type": "EMAIL"
                            }
                        ]
                    }
                },
                {
                    "title": "Множественные выплаты",
                    "config": {
                        "sender_batch_id": "batch_002",
                        "email_subject": "Выплата за услуги",
                        "currency": "USD",
                        "items": [
                            {
                                "receiver": "[email protected]",
                                "amount": 50.00,
                                "note": "Оплата за услуги",
                                "recipient_type": "EMAIL"
                            },
                            {
                                "receiver": "[email protected]",
                                "amount": 75.50,
                                "note": "Оплата за услуги",
                                "recipient_type": "EMAIL"
                            }
                        ]
                    }
                },
                {
                    "title": "Выплата по PayPal ID",
                    "config": {
                        "sender_batch_id": "batch_003",
                        "email_subject": "Выплата",
                        "currency": "EUR",
                        "items": [
                            {
                                "receiver": "V7H7Q2Z5QXQHA",
                                "amount": 25.00,
                                "note": "Выплата",
                                "recipient_type": "PAYPAL_ID"
                            }
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
        """
        Выполняет интеграцию используя библиотеку paypal-payouts-sdk.
        
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
        """
        if not PAYPAL_SDK_AVAILABLE:
            await logger.error("paypal-payouts-sdk library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "paypal-payouts-sdk library is not installed"
                }
            }
        
        # Получаем credentials из credentials_resolver
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="paypal",
            strategy="oauth"
        )
        
        if not creds:
            await logger.error("PayPal credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "PayPal credentials not found"
                }
            }
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        client_id = payload.get("client_id") or payload.get("clientId")
        client_secret = payload.get("client_secret") or payload.get("clientSecret")
        
        if not client_id or not client_secret:
            await logger.error(f"client_id or client_secret not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "client_id and client_secret are required in PayPal credentials"
                }
            }
        
        # Получаем параметры из config
        sender_batch_id = config.get("sender_batch_id")
        email_subject = config.get("email_subject")
        currency = config.get("currency")
        items = config.get("items")
        environment_type = config.get("environment", "sandbox")
        
        # Валидация параметров
        if not sender_batch_id:
            await logger.error("sender_batch_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "sender_batch_id is required"
                }
            }
        
        if not email_subject:
            await logger.error("email_subject is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "email_subject is required"
                }
            }
        
        if not currency:
            await logger.error("currency is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "currency is required"
                }
            }
        
        if not items or not isinstance(items, list) or len(items) == 0:
            await logger.error("items must be a non-empty array")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "items must be a non-empty array"
                }
            }
        
        if len(items) > 5000:
            await logger.error("items array cannot contain more than 5000 items")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "items array cannot contain more than 5000 items"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем окружение PayPal (sandbox или live)
            if environment_type == "live":
                environment = LiveEnvironment(client_id=client_id, client_secret=client_secret)
            else:
                environment = SandboxEnvironment(client_id=client_id, client_secret=client_secret)
            
            # Создаем клиент PayPal
            client = PayPalHttpClient(environment)
            
            # Формируем список payout items
            payout_items = []
            for idx, item in enumerate(items):
                receiver = item.get("receiver")
                amount = item.get("amount")
                recipient_type = item.get("recipient_type", "EMAIL")
                note = item.get("note", "")
                sender_item_id = item.get("sender_item_id") or f"{sender_batch_id}_{idx}"
                
                if not receiver:
                    await logger.error(f"receiver is required for item at index {idx}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": f"receiver is required for item at index {idx}"
                        }
                    }
                
                if amount is None or amount <= 0:
                    await logger.error(f"amount must be a positive number for item at index {idx}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": f"amount must be a positive number for item at index {idx}"
                        }
                    }
                
                # Создаем словарь для payout item
                payout_item = {
                    "recipient_type": recipient_type,
                    "receiver": receiver,
                    "amount": {
                        "value": str(amount),
                        "currency": currency
                    },
                    "note": note,
                    "sender_item_id": sender_item_id
                }
                
                payout_items.append(payout_item)
            
            # Создаем запрос на выплату
            payout_request = PayoutsPostRequest()
            payout_request.request_body({
                "sender_batch_header": {
                    "sender_batch_id": sender_batch_id,
                    "email_subject": email_subject
                },
                "items": payout_items
            })
            
            # Выполняем запрос
            response = client.execute(payout_request)
            
            # Преобразуем результат в словарь
            def to_dict(obj):
                """Рекурсивно конвертирует объект в словарь."""
                if isinstance(obj, dict):
                    return {k: to_dict(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [to_dict(item) for item in obj]
                elif hasattr(obj, '__dict__'):
                    return {k: to_dict(v) for k, v in obj.__dict__.items()}
                elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
                    return [to_dict(item) for item in obj]
                else:
                    return obj
            
            # Получаем результат из response
            if hasattr(response, 'result'):
                result_dict = to_dict(response.result)
            elif hasattr(response, '__dict__'):
                result_dict = to_dict(response.__dict__)
            else:
                result_dict = to_dict(response)
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": result_dict
                }
            }
            
        except HttpError as e:
            await logger.error(f"PayPal HTTP error: {e}")
            error_message = str(e)
            error_code = getattr(e, 'status_code', 500)
            
            # Попытка извлечь детали ошибки из ответа
            if hasattr(e, 'message'):
                error_message = str(e.message)
            elif hasattr(e, 'response'):
                error_message = f"PayPal API error: {error_message}"
            
            return {
                "response": {
                    "ok": False,
                    "error_code": error_code,
                    "description": error_message
                }
            }
        except ValueError as e:
            await logger.error(f"Invalid parameter: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": f"Invalid parameter: {str(e)}"
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Unexpected error: {str(e)}"
                }
            }

