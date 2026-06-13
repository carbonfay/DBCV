"""
Интеграция для создания компании в Битрикс24 через REST API.
Использует прямые HTTP-запросы с помощью библиотеки httpx.
"""

from typing import Any, Dict, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


class Bitrix24CreateCompanyIntegration(BaseIntegration):
    """
    Создание компании в Битрикс24.
    """

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="bitrix24_create_company",
            version="1.0.0",
            name="Битрикс24 Create Company",
            description="Создание компании в CRM Битрикс24",
            category="crm",
            icon_s3_key="icons/integrations/bitrix24.svg",
            color="#2c9ab7",
            config_schema={
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title": {
                        "type": "string",
                        "title": "Название компании",
                        "description": "Название компании (обязательное поле)"
                    },
                    "address": {
                        "type": "string",
                        "title": "Адрес",
                        "description": "Юридический или фактический адрес"
                    },
                    "phone": {
                        "type": "array",
                        "title": "Телефоны",
                        "description": "Список телефонов компании",
                        "items": {
                            "type": "object",
                            "properties": {
                                "VALUE": {"type": "string"},
                                "VALUE_TYPE": {"type": "string", "enum": ["WORK", "MOBILE", "HOME"]}
                            }
                        }
                    },
                    "email": {
                        "type": "array",
                        "title": "Email",
                        "description": "Список email-адресов",
                        "items": {
                            "type": "object",
                            "properties": {
                                "VALUE": {"type": "string"},
                                "VALUE_TYPE": {"type": "string", "enum": ["WORK", "HOME"]}
                            }
                        }
                    },
                    "web": {
                        "type": "array",
                        "title": "Сайты",
                        "description": "Список сайтов компании",
                        "items": {
                            "type": "object",
                            "properties": {
                                "VALUE": {"type": "string"},
                                "VALUE_TYPE": {"type": "string", "enum": ["WORK", "HOME"]}
                            }
                        }
                    },
                    "industry": {
                        "type": "string",
                        "title": "Сфера деятельности",
                        "description": "Код отрасли (например, 'IT', 'MANUFACTURING')"
                    },
                    "company_type": {
                        "type": "string",
                        "title": "Тип компании",
                        "description": "Тип: CUSTOMER, PARTNER, COMPETITOR, etc."
                    },
                    "comments": {
                        "type": "string",
                        "title": "Комментарий",
                        "description": "Дополнительная информация"
                    },
                    "open": {
                        "type": "boolean",
                        "title": "Доступность",
                        "description": "Доступна ли компания для всех сотрудников",
                        "default": True
                    },
                    "assigned_by_id": {
                        "type": "integer",
                        "title": "Ответственный",
                        "description": "ID ответственного сотрудника"
                    },
                    "uf_crm_fields": {
                        "type": "object",
                        "title": "Пользовательские поля",
                        "description": "Значения пользовательских полей (префикс UF_*)"
                    }
                }
            },
            credentials_provider="bitrix24",
            credentials_strategy="api_key",
            library_name="httpx" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Создать компанию с названием",
                    "config": {
                        "title": "ООО Ромашка"
                    }
                },
                {
                    "title": "Создать компанию с контактами",
                    "config": {
                        "title": "ТехноСервис",
                        "phone": [{"VALUE": "+7-123-456-78-90", "VALUE_TYPE": "WORK"}],
                        "email": [{"VALUE": "info@technoservice.ru", "VALUE_TYPE": "WORK"}],
                        "web": [{"VALUE": "https://technoservice.ru", "VALUE_TYPE": "WORK"}],
                        "assigned_by_id": 1
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
        Выполняет создание компании в Битрикс24.

        :param config: Конфигурация интеграции (поля компании).
        :param credentials_resolver: Резолвер для получения учетных данных.
        :param bot_id: ID бота (для области видимости credentials).
        :param logger: Логгер бота.
        :return: Результат выполнения в стандартном формате.
        """
        if not HTTPX_AVAILABLE:
            await logger.error("Библиотека httpx не установлена")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "Библиотека httpx не установлена"
                }
            }

        # Получение вебхука из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="bitrix24",
            strategy="api_key"
        )
        if not creds:
            await logger.error("Учетные данные Битрикс24 не найдены")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Учетные данные Битрикс24 не найдены"
                }
            }

        payload = creds.get("payload", creds)
        webhook_url = payload.get("webhook_url") or payload.get("api_key")
        if not webhook_url:
            await logger.error("Не указан webhook_url или api_key в учетных данных")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Не указан webhook_url в учетных данных"
                }
            }

        # Формирование URL для REST-метода crm.company.add
        base_url = webhook_url.rstrip('/')
        method_url = f"{base_url}/crm.company.add.json"

        # Подготовка полей компании из конфигурации
        fields = {}
        # Обязательное поле
        if not config.get("title"):
            await logger.error("Отсутствует обязательное поле 'title'")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "Поле 'title' обязательно для создания компании"
                }
            }
        fields["TITLE"] = config["title"]

        # Опциональные поля
        optional_mapping = {
            "address": "ADDRESS",
            "industry": "INDUSTRY",
            "company_type": "COMPANY_TYPE",
            "comments": "COMMENTS",
            "open": "OPENED",
            "assigned_by_id": "ASSIGNED_BY_ID",
        }
        for config_key, bx_key in optional_mapping.items():
            if config_key in config and config[config_key] is not None:
                fields[bx_key] = config[config_key]

        # Множественные поля
        if "phone" in config and config["phone"]:
            fields["PHONE"] = config["phone"]
        if "email" in config and config["email"]:
            fields["EMAIL"] = config["email"]
        if "web" in config and config["web"]:
            fields["WEB"] = config["web"]

        # Пользовательские поля UF_*
        if "uf_crm_fields" in config and config["uf_crm_fields"]:
            for uf_name, uf_value in config["uf_crm_fields"].items():
                if uf_name.startswith("UF_"):
                    fields[uf_name] = uf_value

        # Формирование параметров запроса
        params = {"fields": fields}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(method_url, json=params)
                response.raise_for_status()
                data = response.json()

            # Проверка на ошибки Битрикс24
            if "error" in data:
                error_msg = data.get("error_description", data.get("error", "Неизвестная ошибка"))
                await logger.error(f"Ошибка Битрикс24 API: {error_msg}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": f"Ошибка Битрикс24: {error_msg}"
                    }
                }

            company_id = data.get("result")
            if not company_id:
                await logger.error("Ответ API не содержит ID созданной компании")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 500,
                        "description": "Не удалось получить ID компании"
                    }
                }

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "company_id": company_id,
                        "message": f"Компания успешно создана. ID: {company_id}"
                    }
                }
            }

        except httpx.HTTPStatusError as e:
            await logger.error(f"HTTP ошибка: {e.response.status_code} - {e.response.text}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.response.status_code,
                    "description": f"HTTP ошибка: {e.response.status_code}"
                }
            }
        except httpx.RequestError as e:
            await logger.error(f"Ошибка сети: {str(e)}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 503,
                    "description": f"Ошибка сети: {str(e)}"
                }
            }
        except Exception as e:
            await logger.error(f"Неожиданная ошибка: {str(e)}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Внутренняя ошибка: {str(e)}"
                }
            }