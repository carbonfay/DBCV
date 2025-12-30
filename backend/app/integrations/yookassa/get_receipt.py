"""YooKassa Get Receipt интеграция используя yookassa библиотеку."""
import asyncio
from typing import Dict, Any
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


class YooKassaGetReceiptIntegration(BaseIntegration):
    """Интеграция для получения информации о чеке в YooKassa через yookassa SDK."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yookassa_get_receipt",
            version="1.0.0",
            name="YooKassa Get Receipt",
            description="Получение информации о чеке в YooKassa по идентификатору",
            category="payments",
            icon_s3_key="icons/integrations/yookassa.svg",
            color="#FFCC00",
            config_schema={
                "type": "object",
                "required": ["receipt_id"],
                "properties": {
                    "receipt_id": {
                        "type": "string",
                        "title": "Receipt ID",
                        "description": "Идентификатор чека в YooKassa"
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
                        "receipt_id": "rt-12345678-1234-1234-1234-123456789012"
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
        receipt_id = config.get("receipt_id")
        
        if not receipt_id:
            await logger.error("receipt_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "receipt_id is required"
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
            receipt = await asyncio.to_thread(Receipt.find_one, str(receipt_id))
            
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
                "tax_system_code": receipt.tax_system_code if hasattr(receipt, 'tax_system_code') else None,
                "items": []
            }
            
            # Добавляем позиции чека, если они есть
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

