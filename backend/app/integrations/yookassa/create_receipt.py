"""YooKassa Create Receipt интеграция используя yookassa библиотеку."""
import asyncio
from typing import Dict, Any, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    from yookassa import Configuration, Receipt
    from yookassa.domain.exceptions import ApiError, UnauthorizedError
    YOOKASSA_AVAILABLE = True
except ImportError:
    YOOKASSA_AVAILABLE = False
    Configuration = None
    Receipt = None
    ApiError = Exception
    UnauthorizedError = Exception


class YooKassaCreateReceiptIntegration(BaseIntegration):
    """Интеграция для создания чека в YooKassa через yookassa SDK."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yookassa_create_receipt",
            version="1.0.0",
            name="YooKassa Create Receipt",
            description="Создание чека для платежа или возврата в YooKassa (54-ФЗ)",
            category="payments",
            icon_s3_key="icons/integrations/yookassa.svg",
            color="#FFCC00",
            config_schema={
                "type": "object",
                "required": ["payment_id", "customer", "items"],
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "title": "Payment ID",
                        "description": "Идентификатор платежа в YooKassa"
                    },
                    "refund_id": {
                        "type": "string",
                        "title": "Refund ID",
                        "description": "Идентификатор возврата в YooKassa (опционально, если указан payment_id)"
                    },
                    "customer": {
                        "type": "object",
                        "title": "Customer",
                        "description": "Данные покупателя",
                        "required": ["email"],
                        "properties": {
                            "email": {
                                "type": "string",
                                "title": "Email",
                                "description": "Email покупателя"
                            },
                            "phone": {
                                "type": "string",
                                "title": "Phone",
                                "description": "Телефон покупателя (опционально)"
                            },
                            "inn": {
                                "type": "string",
                                "title": "INN",
                                "description": "ИНН покупателя (опционально)"
                            }
                        }
                    },
                    "items": {
                        "type": "array",
                        "title": "Items",
                        "description": "Список товаров в чеке",
                        "items": {
                            "type": "object",
                            "required": ["description", "quantity", "amount", "vat_code"],
                            "properties": {
                                "description": {
                                    "type": "string",
                                    "title": "Description",
                                    "description": "Наименование товара"
                                },
                                "quantity": {
                                    "type": "number",
                                    "title": "Quantity",
                                    "description": "Количество товара"
                                },
                                "amount": {
                                    "type": "object",
                                    "title": "Amount",
                                    "required": ["value", "currency"],
                                    "properties": {
                                        "value": {
                                            "type": "string",
                                            "title": "Value",
                                            "description": "Цена товара (например, '100.00')"
                                        },
                                        "currency": {
                                            "type": "string",
                                            "title": "Currency",
                                            "description": "Валюта (например, 'RUB')",
                                            "default": "RUB"
                                        }
                                    }
                                },
                                "vat_code": {
                                    "type": "integer",
                                    "title": "VAT Code",
                                    "description": "Код НДС (1-6)",
                                    "enum": [1, 2, 3, 4, 5, 6]
                                },
                                "payment_mode": {
                                    "type": "string",
                                    "title": "Payment Mode",
                                    "description": "Признак способа расчета (опционально)"
                                },
                                "payment_subject": {
                                    "type": "string",
                                    "title": "Payment Subject",
                                    "description": "Признак предмета расчета (опционально)"
                                }
                            }
                        }
                    },
                    "tax_system_code": {
                        "type": "integer",
                        "title": "Tax System Code",
                        "description": "Код системы налогообложения (1-6, опционально)",
                        "enum": [1, 2, 3, 4, 5, 6]
                    }
                }
            },
            credentials_provider="yookassa",
            credentials_strategy="api_key",
            library_name="yookassa>=2.3.0" if YOOKASSA_AVAILABLE else None,
            examples=[
                {
                    "title": "Создать чек для платежа",
                    "config": {
                        "payment_id": "2c5b8d8e-0001-7000-8000-000000000000",
                        "customer": {
                            "email": "customer@example.com"
                        },
                        "items": [
                            {
                                "description": "Товар 1",
                                "quantity": 1,
                                "amount": {
                                    "value": "100.00",
                                    "currency": "RUB"
                                },
                                "vat_code": 1
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
        Выполняет интеграцию используя библиотеку yookassa.
        
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
        
        # Получаем credentials из credentials_resolver
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
        
        shop_id = payload.get("shop_id") or payload.get("account_id")
        secret_key = payload.get("secret_key") or payload.get("api_key")
        
        if not shop_id or not secret_key:
            await logger.error(f"shop_id or secret_key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "shop_id and secret_key are required in credentials"
                }
            }
        
        # Получаем параметры из config
        payment_id = config.get("payment_id")
        refund_id = config.get("refund_id")
        customer = config.get("customer")
        items = config.get("items")
        tax_system_code = config.get("tax_system_code")
        
        # Валидация обязательных параметров
        if not payment_id and not refund_id:
            await logger.error("payment_id or refund_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "payment_id or refund_id is required"
                }
            }
        
        if not customer:
            await logger.error("customer is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "customer is required"
                }
            }
        
        if not isinstance(customer, dict):
            await logger.error("customer must be an object")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "customer must be an object"
                }
            }
        
        customer_email = customer.get("email")
        if not customer_email:
            await logger.error("customer.email is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "customer.email is required"
                }
            }
        
        if not items:
            await logger.error("items is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "items is required"
                }
            }
        
        if not isinstance(items, list) or len(items) == 0:
            await logger.error("items must be a non-empty array")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "items must be a non-empty array"
                }
            }
        
        # Настраиваем конфигурацию YooKassa
        try:
            Configuration.account_id = str(shop_id)
            Configuration.secret_key = str(secret_key)
        except Exception as e:
            await logger.error(f"Failed to configure YooKassa: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Failed to configure YooKassa: {str(e)}"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        # Обертываем синхронный вызов в executor для избежания блокировки event loop
        try:
            # Подготавливаем данные для создания чека
            receipt_data = {
                "customer": {
                    "email": str(customer_email)
                },
                "items": []
            }
            
            # Добавляем опциональные поля customer
            if customer.get("phone"):
                receipt_data["customer"]["phone"] = str(customer["phone"])
            if customer.get("inn"):
                receipt_data["customer"]["inn"] = str(customer["inn"])
            
            # Добавляем payment_id или refund_id
            if payment_id:
                receipt_data["payment_id"] = str(payment_id)
            if refund_id:
                receipt_data["refund_id"] = str(refund_id)
            
            # Добавляем tax_system_code если указан
            if tax_system_code:
                receipt_data["tax_system_code"] = int(tax_system_code)
            
            # Обрабатываем items
            for item in items:
                item_data = {
                    "description": str(item.get("description", "")),
                    "quantity": float(item.get("quantity", 1)),
                    "amount": {
                        "value": str(item["amount"]["value"]),
                        "currency": str(item["amount"].get("currency", "RUB"))
                    },
                    "vat_code": int(item.get("vat_code", 1))
                }
                
                # Добавляем опциональные поля
                if item.get("payment_mode"):
                    item_data["payment_mode"] = str(item["payment_mode"])
                if item.get("payment_subject"):
                    item_data["payment_subject"] = str(item["payment_subject"])
                
                receipt_data["items"].append(item_data)
            
            # Создаем чек
            receipt = await asyncio.to_thread(Receipt.create, receipt_data)
            
            # Преобразуем результат в словарь для возврата
            receipt_dict = {
                "id": receipt.id if hasattr(receipt, 'id') else None,
                "type": receipt.type if hasattr(receipt, 'type') else None,
                "status": receipt.status if hasattr(receipt, 'status') else None,
                "payment_id": receipt.payment_id if hasattr(receipt, 'payment_id') else None,
                "refund_id": receipt.refund_id if hasattr(receipt, 'refund_id') else None,
                "created_at": receipt.created_at.isoformat() if hasattr(receipt, 'created_at') and receipt.created_at else None,
                "fiscal_document_number": receipt.fiscal_document_number if hasattr(receipt, 'fiscal_document_number') else None,
                "fiscal_storage_number": receipt.fiscal_storage_number if hasattr(receipt, 'fiscal_storage_number') else None,
                "fiscal_attribute": receipt.fiscal_attribute if hasattr(receipt, 'fiscal_attribute') else None,
                "registered_at": receipt.registered_at.isoformat() if hasattr(receipt, 'registered_at') and receipt.registered_at else None,
                "tax_system_code": receipt.tax_system_code if hasattr(receipt, 'tax_system_code') else None
            }
            
            # Добавляем customer если есть
            if hasattr(receipt, 'customer') and receipt.customer:
                receipt_dict["customer"] = {
                    "email": receipt.customer.email if hasattr(receipt.customer, 'email') else None,
                    "phone": receipt.customer.phone if hasattr(receipt.customer, 'phone') else None,
                    "inn": receipt.customer.inn if hasattr(receipt.customer, 'inn') else None
                }
            
            # Добавляем items если есть
            receipt_dict["items"] = []
            if hasattr(receipt, 'items') and receipt.items:
                for item in receipt.items:
                    item_dict = {
                        "description": item.description if hasattr(item, 'description') else None,
                        "quantity": float(item.quantity) if hasattr(item, 'quantity') else None,
                        "amount": {
                            "value": float(item.amount.value) if hasattr(item, 'amount') and hasattr(item.amount, 'value') else None,
                            "currency": item.amount.currency if hasattr(item, 'amount') and hasattr(item.amount, 'currency') else None
                        } if hasattr(item, 'amount') else None,
                        "vat_code": item.vat_code if hasattr(item, 'vat_code') else None,
                        "payment_mode": item.payment_mode if hasattr(item, 'payment_mode') else None,
                        "payment_subject": item.payment_subject if hasattr(item, 'payment_subject') else None
                    }
                    receipt_dict["items"].append(item_dict)
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": receipt_dict
                }
            }
        except UnauthorizedError as e:
            await logger.error(f"YooKassa unauthorized error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": f"Unauthorized: {str(e)}"
                }
            }
        except ApiError as e:
            await logger.error(f"YooKassa API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.code if hasattr(e, 'code') else 400,
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

