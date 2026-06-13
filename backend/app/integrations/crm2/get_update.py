"""
Интеграция для создания сделки (лида) в AmoCRM.
Использует библиотеку amocrm-api-wrapper для работы с API v4.
"""

from typing import Any, Dict, List, Optional

from app.integrations.base import BaseIntegration
from app.integrations.exceptions import IntegrationException
from app.services.credentials_resolver import CredentialsResolver
from amocrm_api import AmoOAuthClient
from amocrm_api.exceptions import AmoCRMException


class AmoCRMCreateLeadIntegration(BaseIntegration):
    """
    Создание сделки (лида) в AmoCRM.
    Позволяет добавлять новые сделки в указанную воронку с заданными параметрами.
    """

    id = "amocrm_create_lead"
    version = "1.0.0"
    category = "crm"
    icon_s3_key = "icons/integrations/amocrm.svg"

    config_schema = {
        "type": "object",
        "properties": {
            "leads": {
                "type": "array",
                "description": "Список сделок для создания",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Название сделки",
                        },
                        "price": {
                            "type": "number",
                            "description": "Бюджет сделки",
                            "minimum": 0,
                        },
                        "pipeline_id": {
                            "type": "integer",
                            "description": "ID воронки (pipeline)",
                        },
                        "status_id": {
                            "type": "integer",
                            "description": "ID статуса сделки (этап воронки)",
                        },
                        "responsible_user_id": {
                            "type": "integer",
                            "description": "ID ответственного пользователя",
                        },
                        "created_by": {
                            "type": "integer",
                            "description": "ID пользователя, создавшего сделку",
                        },
                        "custom_fields_values": {
                            "type": "array",
                            "description": "Дополнительные поля сделки",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "field_id": {"type": "integer"},
                                    "field_code": {"type": "string"},
                                    "values": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "value": {"type": "string"},
                                            },
                                        },
                                    },
                                },
                            },
                        },
                        "_embedded": {
                            "type": "object",
                            "description": "Связанные сущности (контакты, компании, теги)",
                            "properties": {
                                "tags": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "_unsaved": {"type": "boolean"},
                                        },
                                    },
                                },
                                "contacts": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "is_main": {"type": "boolean"},
                                        },
                                    },
                                },
                                "companies": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "is_main": {"type": "boolean"},
                                        },
                                    },
                                },
                            },
                        },
                    },
                    "required": ["name"],
                },
            },
        },
        "required": ["leads"],
    }

    credentials_provider = "amocrm"
    credentials_strategy = "oauth"
    library_name = "amocrm-api-wrapper"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация интеграции с конфигурацией.

        :param config: Параметры конфигурации интеграции.
        """
        super().__init__(config)

    def execute(self, credentials_resolver: CredentialsResolver) -> Dict[str, Any]:
        """
        Выполняет создание сделок (лидов) в AmoCRM.

        :param credentials_resolver: Резолвер для получения учетных данных.
        :return: Результат выполнения в стандартном формате.
        :raises IntegrationException: Если создание не удалось.
        """
        try:
            # Получение учётных данных
            credentials = credentials_resolver.get_default_for("amocrm")
            required_keys = [
                "access_token",
                "refresh_token",
                "subdomain",
                "client_id",
                "client_secret",
                "redirect_uri",
            ]
            for key in required_keys:
                if key not in credentials or not credentials[key]:
                    raise IntegrationException(
                        f"Отсутствует обязательный параметр учётных данных '{key}' для AmoCRM"
                    )

            # Инициализация OAuth-клиента
            client = AmoOAuthClient(
                access_token=credentials["access_token"],
                refresh_token=credentials["refresh_token"],
                crm_url=f"https://{credentials['subdomain']}.amocrm.ru",
                client_id=credentials["client_id"],
                client_secret=credentials["client_secret"],
                redirect_uri=credentials["redirect_uri"],
            )

            # Получение списка сделок из конфигурации
            leads_to_create = self.config.get("leads", [])

            # Вызов API для создания сделок
            result = client.create_leads(leads_to_create)

            # Обработка пустого ответа от библиотеки
            if result is None:
                raise IntegrationException(
                    "Не удалось создать сделки: получен пустой ответ от API AmoCRM"
                )

            # Проверка наличия ошибок в ответе
            if isinstance(result, dict) and "errors" in result:
                error_details = result.get("errors", [])
                error_messages = ", ".join(
                    [str(e) for e in error_details]
                ) or "Неизвестная ошибка при создании сделок"
                raise IntegrationException(
                    f"Ошибка при создании сделок в AmoCRM: {error_messages}"
                )

            # Успешный ответ
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "message": "Сделки успешно созданы",
                        "data": result,
                    },
                }
            }

        except AmoCRMException as e:
            # Обработка специфичных ошибок библиотеки
            self.logger.error(f"Ошибка библиотеки AmoCRM: {str(e)}")
            raise IntegrationException(
                f"Ошибка при создании сделки в AmoCRM: {str(e)}"
            ) from e

        except Exception as e:
            # Обработка любых других ошибок
            self.logger.error(f"Неизвестная ошибка при создании сделки в AmoCRM: {str(e)}")
            raise IntegrationException(
                f"Не удалось создать сделку в AmoCRM: {str(e)}"
            ) from e

    def get_metadata(self) -> Dict[str, Any]:
        """
        Возвращает метаданные интеграции.

        :return: Словарь с метаданными.
        """
        return {
            "id": self.id,
            "version": self.version,
            "category": self.category,
            "icon_s3_key": self.icon_s3_key,
            "config_schema": self.config_schema,
            "credentials_provider": self.credentials_provider,
            "credentials_strategy": self.credentials_strategy,
            "library_name": self.library_name,
        }