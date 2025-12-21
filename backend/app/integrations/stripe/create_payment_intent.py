"""Stripe Create Payment Intent интеграция используя stripe библиотеку."""
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


class StripeCreatePaymentIntentIntegration(BaseIntegration):
    """Интеграция для создания Payment Intent в Stripe через stripe библиотеку."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="stripe_create_payment_intent",
            version="1.0.0",
            name="Stripe Create Payment Intent",
            description="Создание Payment Intent в Stripe для обработки платежей",
            category="payments",
            icon_s3_key="icons/integrations/stripe.svg",
            color="#635BFF",
            config_schema={
                "type": "object",
                "required": ["amount", "currency"],
                "properties": {
                    "amount": {
                        "type": "integer",
                        "title": "Amount",
                        "description": "Сумма в центах (например, 1000 = $10.00)"
                    },
                    "currency": {
                        "type": "string",
                        "title": "Currency",
                        "description": "Валюта (например, 'usd', 'rub')"
                    },
                    "payment_method": {
                        "type": "string",
                        "title": "Payment Method ID",
                        "description": "ID метода оплаты (опционально)"
                    },
                    "payment_method_types": {
                        "type": "array",
                        "title": "Payment Method Types",
                        "description": "Список типов методов оплаты (например, ['card', 'ideal'])",
                        "items": {
                            "type": "string"
                        }
                    },
                    "customer": {
                        "type": "string",
                        "title": "Customer ID",
                        "description": "ID существующего клиента в Stripe"
                    },
                    "description": {
                        "type": "string",
                        "title": "Description",
                        "description": "Описание платежа"
                    },
                    "metadata": {
                        "type": "object",
                        "title": "Metadata",
                        "description": "Дополнительные данные в формате ключ-значение",
                        "additionalProperties": {
                            "type": "string"
                        }
                    },
                    "receipt_email": {
                        "type": "string",
                        "title": "Receipt Email",
                        "description": "Email для отправки квитанции"
                    },
                    "shipping": {
                        "type": "object",
                        "title": "Shipping",
                        "description": "Информация о доставке",
                        "properties": {
                            "name": {"type": "string", "title": "Name"},
                            "phone": {"type": "string", "title": "Phone"},
                            "address": {
                                "type": "object",
                                "title": "Address",
                                "properties": {
                                    "line1": {"type": "string"},
                                    "line2": {"type": "string"},
                                    "city": {"type": "string"},
                                    "state": {"type": "string"},
                                    "postal_code": {"type": "string"},
                                    "country": {"type": "string"}
                                }
                            }
                        }
                    },
                    "statement_descriptor": {
                        "type": "string",
                        "title": "Statement Descriptor",
                        "description": "Описание в выписке (до 22 символов)"
                    },
                    "statement_descriptor_suffix": {
                        "type": "string",
                        "title": "Statement Descriptor Suffix",
                        "description": "Суффикс описания в выписке"
                    },
                    "capture_method": {
                        "type": "string",
                        "title": "Capture Method",
                        "description": "Метод захвата: 'automatic' или 'manual'",
                        "enum": ["automatic", "manual"]
                    },
                    "confirmation_method": {
                        "type": "string",
                        "title": "Confirmation Method",
                        "description": "Метод подтверждения: 'automatic' или 'manual'",
                        "enum": ["automatic", "manual"]
                    },
                    "confirm": {
                        "type": "boolean",
                        "title": "Confirm",
                        "description": "Подтвердить PaymentIntent сразу после создания"
                    },
                    "return_url": {
                        "type": "string",
                        "title": "Return URL",
                        "description": "URL для перенаправления после оплаты"
                    },
                    "setup_future_usage": {
                        "type": "string",
                        "title": "Setup Future Usage",
                        "description": "Сохранить метод оплаты для будущего использования",
                        "enum": ["on_session", "off_session"]
                    },
                    "application_fee_amount": {
                        "type": "integer",
                        "title": "Application Fee Amount",
                        "description": "Сумма комиссии приложения в центах"
                    },
                    "transfer_data": {
                        "type": "object",
                        "title": "Transfer Data",
                        "description": "Данные для перевода на другой аккаунт (Connect)",
                        "properties": {
                            "amount": {"type": "integer", "title": "Amount"},
                            "destination": {"type": "string", "title": "Destination Account ID"}
                        }
                    },
                    "on_behalf_of": {
                        "type": "string",
                        "title": "On Behalf Of",
                        "description": "ID аккаунта, от имени которого создается платеж (Connect)"
                    },
                    "automatic_payment_methods": {
                        "type": "object",
                        "title": "Automatic Payment Methods",
                        "description": "Настройки автоматических методов оплаты",
                        "properties": {
                            "enabled": {"type": "boolean", "title": "Enabled"},
                            "allow_redirects": {
                                "type": "string",
                                "title": "Allow Redirects",
                                "enum": ["always", "never"]
                            }
                        }
                    },
                    "payment_method_options": {
                        "type": "object",
                        "title": "Payment Method Options",
                        "description": "Опции для методов оплаты",
                        "additionalProperties": True
                    }
                }
            },
            credentials_provider="stripe",
            credentials_strategy="api_key",
            library_name="stripe>=7.0.0" if STRIPE_AVAILABLE else None,
            examples=[
                {
                    "title": "Простой платеж",
                    "config": {
                        "amount": 1000,
                        "currency": "usd"
                    }
                },
                {
                    "title": "Платеж с методом оплаты",
                    "config": {
                        "amount": 5000,
                        "currency": "rub",
                        "payment_method": "pm_1234567890",
                        "description": "Оплата заказа #123"
                    }
                },
                {
                    "title": "Платеж с метаданными и email",
                    "config": {
                        "amount": 2000,
                        "currency": "usd",
                        "description": "Оплата подписки",
                        "metadata": {
                            "order_id": "12345",
                            "user_id": "67890"
                        },
                        "receipt_email": "customer@example.com"
                    }
                },
                {
                    "title": "Платеж с доставкой",
                    "config": {
                        "amount": 3000,
                        "currency": "usd",
                        "shipping": {
                            "name": "John Doe",
                            "phone": "+1234567890",
                            "address": {
                                "line1": "123 Main St",
                                "city": "New York",
                                "state": "NY",
                                "postal_code": "10001",
                                "country": "US"
                            }
                        }
                    }
                },
                {
                    "title": "Платеж с ручным захватом",
                    "config": {
                        "amount": 5000,
                        "currency": "usd",
                        "capture_method": "manual",
                        "description": "Предварительная авторизация"
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
        
        # Получаем обязательные параметры из config
        amount = config.get("amount")
        currency = config.get("currency")
        
        if amount is None or currency is None:
            await logger.error("amount and currency are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "amount and currency are required"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            stripe.api_key = api_key
            
            # Создаем базовые параметры для PaymentIntent
            payment_intent_params = {
                "amount": int(amount),
                "currency": str(currency).lower()
            }
            
            # Добавляем опциональные параметры
            # Payment method
            if config.get("payment_method"):
                payment_intent_params["payment_method"] = str(config["payment_method"])
            elif not config.get("payment_method_types") and not config.get("automatic_payment_methods"):
                # Если payment_method не указан и нет payment_method_types/automatic_payment_methods,
                # включаем автоматические методы оплаты по умолчанию
                payment_intent_params["automatic_payment_methods"] = {"enabled": True}
            
            # Payment method types
            if config.get("payment_method_types"):
                payment_intent_params["payment_method_types"] = config["payment_method_types"]
            
            # Customer
            if config.get("customer"):
                payment_intent_params["customer"] = str(config["customer"])
            
            # Description
            if config.get("description"):
                payment_intent_params["description"] = str(config["description"])
            
            # Metadata
            if config.get("metadata"):
                payment_intent_params["metadata"] = config["metadata"]
            
            # Receipt email
            if config.get("receipt_email"):
                payment_intent_params["receipt_email"] = str(config["receipt_email"])
            
            # Shipping
            if config.get("shipping"):
                payment_intent_params["shipping"] = config["shipping"]
            
            # Statement descriptor
            if config.get("statement_descriptor"):
                payment_intent_params["statement_descriptor"] = str(config["statement_descriptor"])
            
            if config.get("statement_descriptor_suffix"):
                payment_intent_params["statement_descriptor_suffix"] = str(config["statement_descriptor_suffix"])
            
            # Capture method
            if config.get("capture_method"):
                payment_intent_params["capture_method"] = str(config["capture_method"])
            
            # Confirmation method
            if config.get("confirmation_method"):
                payment_intent_params["confirmation_method"] = str(config["confirmation_method"])
            
            # Confirm
            if config.get("confirm") is not None:
                payment_intent_params["confirm"] = bool(config["confirm"])
            
            # Return URL
            if config.get("return_url"):
                payment_intent_params["return_url"] = str(config["return_url"])
            
            # Setup future usage
            if config.get("setup_future_usage"):
                payment_intent_params["setup_future_usage"] = str(config["setup_future_usage"])
            
            # Application fee amount
            if config.get("application_fee_amount") is not None:
                payment_intent_params["application_fee_amount"] = int(config["application_fee_amount"])
            
            # Transfer data
            if config.get("transfer_data"):
                payment_intent_params["transfer_data"] = config["transfer_data"]
            
            # On behalf of
            if config.get("on_behalf_of"):
                payment_intent_params["on_behalf_of"] = str(config["on_behalf_of"])
            
            # Automatic payment methods
            if config.get("automatic_payment_methods"):
                payment_intent_params["automatic_payment_methods"] = config["automatic_payment_methods"]
            
            # Payment method options
            if config.get("payment_method_options"):
                payment_intent_params["payment_method_options"] = config["payment_method_options"]
            
            # Создаем PaymentIntent
            payment_intent = stripe.PaymentIntent.create(**payment_intent_params)
            
            # Формируем результат
            result = {
                "id": payment_intent.id,
                "status": payment_intent.status,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency,
                "client_secret": payment_intent.client_secret
            }
            
            # Добавляем дополнительную информацию в зависимости от статуса
            if hasattr(payment_intent, 'description') and payment_intent.description:
                result["description"] = payment_intent.description
            
            if hasattr(payment_intent, 'metadata') and payment_intent.metadata:
                result["metadata"] = dict(payment_intent.metadata)
            
            if hasattr(payment_intent, 'customer') and payment_intent.customer:
                result["customer"] = payment_intent.customer
            
            if hasattr(payment_intent, 'payment_method') and payment_intent.payment_method:
                result["payment_method"] = payment_intent.payment_method
            
            # Добавляем информацию о следующих шагах для некоторых статусов
            if payment_intent.status == "requires_payment_method":
                result["next_action"] = "Прикрепите метод оплаты и подтвердите платеж"
            elif payment_intent.status == "requires_confirmation":
                result["next_action"] = "Подтвердите платеж"
            elif payment_intent.status == "requires_action":
                result["next_action"] = "Требуется дополнительное действие (например, 3D Secure)"
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": result
                }
            }
        except StripeError as e:
            await logger.error(f"Stripe error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.http_status if hasattr(e, 'http_status') else 500,
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

