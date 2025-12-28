"""
Шаблон для создания новой интеграции DBCV.

ИНСТРУКЦИЯ:
1. Скопируйте этот файл в backend/app/integrations/{service}/{action}.py
2. Замените все {ПЛЕЙСХОЛДЕРЫ} на реальные значения
3. Реализуйте метод execute() используя библиотеку напрямую
4. Зарегистрируйте интеграцию в backend/app/integrations/{service}/__init__.py
5. Добавьте импорт в backend/app/integrations/__init__.py
"""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
# ЗАМЕНИТЕ на реальный импорт вашей библиотеки
try:
    # Пример: from {library} import {Class}
    # Пример: from openai import OpenAI
    # Пример: from telegram import Bot
    LIBRARY_AVAILABLE = True
except ImportError:
    LIBRARY_AVAILABLE = False
    # Установите None для классов, которые не импортировались
    # Пример: OpenAI = None


class {Service}{Action}Integration(BaseIntegration):
    """
    Интеграция для {ОПИСАНИЕ_ДЕЙСТВИЯ} через {НАЗВАНИЕ_БИБЛИОТЕКИ}.
    
    ЗАМЕНИТЕ:
    - {Service} - название сервиса (например: Telegram, OpenAI, Stripe)
    - {Action} - действие (например: SendMessage, GenerateText, CreatePayment)
    - {ОПИСАНИЕ_ДЕЙСТВИЯ} - что делает интеграция
    - {НАЗВАНИЕ_БИБЛИОТЕКИ} - название библиотеки
    """
    
    @property
    def metadata(self) -> IntegrationMetadata:
        """
        Метаданные интеграции для фронтенда.
        
        ЗАМЕНИТЕ все {ПЛЕЙСХОЛДЕРЫ} на реальные значения.
        """
        return IntegrationMetadata(
            id="{service}_{action}",  # Например: "telegram_send_message"
            version="1.0.0",
            name="{Service} {Action}",  # Например: "Telegram Send Message"
            description="{ОПИСАНИЕ_ИНТЕГРАЦИИ}",  # Подробное описание
            category="{category}",  # messaging, ai, storage, weather, maps, payments, crm, ecommerce, education, medicine, news, translation
            icon_s3_key="icons/integrations/{service}.svg",  # Путь к иконке в S3
            color="#{HEX_COLOR}",  # Цвет иконки (например: "#0088cc")
            config_schema={
                "type": "object",
                "required": ["{param1}", "{param2}"],  # Обязательные параметры
                "properties": {
                    "{param1}": {
                        "type": "string",  # или "number", "boolean", "object", "array"
                        "title": "{Название параметра}",
                        "description": "{Описание параметра}"
                    },
                    "{param2}": {
                        "type": "string",
                        "title": "{Название параметра}",
                        "description": "{Описание параметра}"
                    }
                    # Добавьте больше параметров по необходимости
                }
            },
            credentials_provider="{service}",  # Название провайдера credentials (должно совпадать с CredentialEntity)
            credentials_strategy="api_key",  # или "oauth" в зависимости от типа авторизации
            library_name="{library}>={version}" if LIBRARY_AVAILABLE else None,  # Например: "python-telegram-bot>=20.0"
            examples=[
                {
                    "title": "{Название примера}",
                    "config": {
                        "{param1}": "{значение1}",
                        "{param2}": "{значение2}"
                    }
                }
                # Добавьте больше примеров по необходимости
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
        Выполняет интеграцию используя библиотеку напрямую.
        
        Args:
            config: Параметры интеграции (из config_schema)
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер для записи логов
        
        Returns:
            Результат выполнения в формате системы:
            {
                "response": {
                    "ok": True/False,
                    "result": {...} или "error_code": ..., "description": "..."
                }
            }
        """
        # Проверка доступности библиотеки
        if not LIBRARY_AVAILABLE:
            await logger.error("{library} library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "{library} library is not installed"
                }
            }
        
        # Получаем credentials через credentials_resolver
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="{service}",  # Должно совпадать с credentials_provider в metadata
            strategy="api_key"  # или "oauth"
        )
        
        if not creds:
            await logger.error("{Service} credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "{Service} credentials not found"
                }
            }
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        # Извлекаем нужные credentials из payload
        # ЗАМЕНИТЕ на реальные ключи ваших credentials
        # Пример: api_key = payload.get("api_key") or payload.get("token")
        # Пример: bot_token = payload.get("bot_token") or payload.get("token")
        api_key = payload.get("{credential_key}") or payload.get("{alternative_key}")
        
        if not api_key:
            await logger.error(f"{credential_key} not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "{credential_key} not found in credentials"
                }
            }
        
        # Получаем параметры из config
        # ЗАМЕНИТЕ на реальные параметры из вашего config_schema
        param1 = config.get("{param1}")
        param2 = config.get("{param2}")
        
        # Валидация обязательных параметров
        if not param1 or not param2:
            await logger.error("{param1} and {param2} are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "{param1} and {param2} are required"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        # ЗАМЕНИТЕ на реальный код использования библиотеки
        try:
            # Пример для OpenAI:
            # client = OpenAI(api_key=api_key)
            # response = await client.chat.completions.create(...)
            
            # Пример для Telegram:
            # bot = Bot(token=api_key)
            # result = await bot.send_message(...)
            
            # Пример для Stripe:
            # import stripe
            # stripe.api_key = api_key
            # result = stripe.PaymentIntent.create(...)
            
            # ВАШ КОД ЗДЕСЬ:
            # client = {LibraryClass}(api_key=api_key)
            # result = await client.{method}(param1=param1, param2=param2)
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        # Преобразуйте result библиотеки в нужный формат
                        # Пример: "id": result.id, "status": result.status
                    }
                }
            }
        except Exception as e:
            # Обработка ошибок библиотеки
            await logger.error(f"{Service} error: {e}")
            
            # Попытка извлечь код ошибки из исключения библиотеки
            error_code = 500
            if hasattr(e, 'error_code'):
                error_code = e.error_code
            elif hasattr(e, 'status_code'):
                error_code = e.status_code
            elif hasattr(e, 'code'):
                error_code = e.code
            
            return {
                "response": {
                    "ok": False,
                    "error_code": error_code,
                    "description": str(e)
                }
            }
        except Exception as e:
            # Обработка неожиданных ошибок
            await logger.error(f"Unexpected error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }










