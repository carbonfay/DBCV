"""YooKassa Get Refund интеграция используя yookassa библиотеку."""
import asyncio
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    from yookassa import Configuration, Refund
    from yookassa.domain.exceptions import ApiError, UnauthorizedError, NotFoundError
    YOOKASSA_AVAILABLE = True
except ImportError:
    YOOKASSA_AVAILABLE = False
    Configuration = None
    Refund = None
    ApiError = Exception
    UnauthorizedError = Exception
    NotFoundError = Exception


class YooKassaGetRefundIntegration(BaseIntegration):
    """Интеграция для получения информации о возврате платежа через YooKassa API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yookassa_get_refund",
            version="1.0.0",
            name="YooKassa Get Refund",
            description="Получение информации о возврате платежа через YooKassa API",
            category="payments",
            icon_s3_key="icons/integrations/yookassa.svg",
            color="#52A352",
            config_schema={
                "type": "object",
                "required": ["refund_id"],
                "properties": {
                    "refund_id": {
                        "type": "string",
                        "title": "Refund ID",
                        "description": "Уникальный идентификатор возврата платежа"
                    }
                }
            },
            credentials_provider="yookassa",
            credentials_strategy="api_key",
            library_name="yookassa>=2.3.0" if YOOKASSA_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить информацию о возврате",
                    "config": {
                        "refund_id": "2d5b0e00-000f-5000-8000-1a6612345678"
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
            provider="other",
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
        
        # Извлекаем shop_id и secret_key из credentials
        shop_id = payload.get("shop_id") or payload.get("account_id")
        secret_key = payload.get("secret_key") or payload.get("api_key")
        
        if not shop_id or not secret_key:
            await logger.error(
                f"shop_id or secret_key not found in credentials. "
                f"Available keys: {list(payload.keys())}"
            )
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "shop_id and secret_key are required in credentials"
                }
            }
        
        # Получаем параметры из config
        refund_id = config.get("refund_id")
        
        if not refund_id:
            await logger.error("refund_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "refund_id is required"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Настраиваем Configuration с credentials
            Configuration.account_id = shop_id
            Configuration.secret_key = secret_key
            
            # Получаем информацию о возврате (оборачиваем синхронный вызов в executor)
            refund = await asyncio.to_thread(Refund.find_one, refund_id)
            
            # Преобразуем объект Refund в словарь используя метод to_dict()
            # Это правильный способ сериализации объектов YooKassa SDK
            if hasattr(refund, 'to_dict'):
                refund_dict = refund.to_dict()
            else:
                # Fallback: используем vars() если метода to_dict() нет
                refund_dict = vars(refund) if hasattr(refund, '__dict__') else {}
            
            # Преобразуем результат в формат системы
            # Метод to_dict() уже возвращает правильный формат словаря
            result = {
                "id": refund_dict.get("id"),
                "status": refund_dict.get("status"),
                "amount": refund_dict.get("amount"),  # Уже в формате {"value": "...", "currency": "..."}
                "payment_id": refund_dict.get("payment_id"),
                "created_at": refund_dict.get("created_at"),  # Уже в ISO формате строки
                "description": refund_dict.get("description"),
            }
            
            # Добавляем дополнительные поля, если они есть
            if "receipt_registration" in refund_dict:
                result["receipt_registration"] = refund_dict["receipt_registration"]
            
            if "cancellation_details" in refund_dict:
                result["cancellation_details"] = refund_dict["cancellation_details"]
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": result
                }
            }
        except NotFoundError as e:
            await logger.error(f"YooKassa refund not found: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 404,
                    "description": f"Refund not found: {str(e)}"
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
                    "error_code": e.code if hasattr(e, 'code') else 500,
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










