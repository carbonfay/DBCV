"""HubSpot Create Contact интеграция используя hubspot-api-client библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import hubspot
    from hubspot.crm.contacts import BasicApi
    from hubspot.crm.contacts.models import SimplePublicObjectInput
    from hubspot.crm.contacts.exceptions import ApiException
    HUBSPOT_AVAILABLE = True
except ImportError:
    HUBSPOT_AVAILABLE = False
    hubspot = None
    BasicApi = None
    SimplePublicObjectInput = None
    ApiException = Exception


class HubSpotCreateContactIntegration(BaseIntegration):
    """Интеграция для создания контактов в HubSpot CRM."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="hubspot_create_contact",
            version="1.0.0",
            name="HubSpot Create Contact",
            description="Создание нового контакта в HubSpot CRM",
            category="crm",
            icon_s3_key="icons/integrations/hubspot.svg",
            color="#FF7A59",
            config_schema={
                "type": "object",
                "required": ["email"],
                "properties": {
                    "email": {
                        "type": "string",
                        "title": "Email",
                        "description": "Email адрес контакта (обязательный)"
                    },
                    "firstname": {
                        "type": "string",
                        "title": "First Name",
                        "description": "Имя контакта"
                    },
                    "lastname": {
                        "type": "string",
                        "title": "Last Name",
                        "description": "Фамилия контакта"
                    },
                    "phone": {
                        "type": "string",
                        "title": "Phone",
                        "description": "Телефон контакта"
                    },
                    "company": {
                        "type": "string",
                        "title": "Company",
                        "description": "Компания контакта"
                    },
                    "website": {
                        "type": "string",
                        "title": "Website",
                        "description": "Веб-сайт контакта"
                    },
                    "jobtitle": {
                        "type": "string",
                        "title": "Job Title",
                        "description": "Должность контакта"
                    }
                }
            },
            credentials_provider="hubspot",
            credentials_strategy="api_key",  # Note: HubSpot uses private app access token
            library_name="hubspot-api-client>=7.0.0" if HUBSPOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Создание контакта с email и именем",
                    "config": {
                        "email": "{$user.email$}",
                        "firstname": "{$user.first_name$}",
                        "lastname": "{$user.last_name$}"
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
        Выполняет интеграцию используя библиотеку hubspot-api-client.

        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер

        Returns:
            Результат выполнения в формате системы
        """
        if not HUBSPOT_AVAILABLE:
            await logger.error("hubspot-api-client library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "hubspot-api-client library is not installed"
                }
            }

        # Получаем access token из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="hubspot",
            strategy="api_key"
        )

        if not creds:
            await logger.error("HubSpot credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "HubSpot access token not found in credentials"
                }
            }

        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds

        access_token = payload.get("access_token") or payload.get("api_key") or payload.get("token")
        if not access_token:
            await logger.error(f"Access token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Access token not found in credentials"
                }
            }

        # Получаем параметры из config
        email = config.get("email")
        if not email:
            await logger.error("email is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "email is required"
                }
            }

        # Подготовим свойства контакта
        properties = {
            "email": str(email)
        }

        # Добавляем дополнительные свойства, если они есть
        if config.get("firstname"):
            properties["firstname"] = str(config["firstname"])
        if config.get("lastname"):
            properties["lastname"] = str(config["lastname"])
        if config.get("phone"):
            properties["phone"] = str(config["phone"])
        if config.get("company"):
            properties["company"] = str(config["company"])
        if config.get("website"):
            properties["website"] = str(config["website"])
        if config.get("jobtitle"):
            properties["jobtitle"] = str(config["jobtitle"])

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем конфигурацию API с токеном
            configuration = hubspot.Configuration(
                access_token=access_token
            )

            # Создаем API клиент
            with hubspot.ApiClient(configuration) as api_client:
                api_instance = BasicApi(api_client)
                
                # Подготовим объект для создания
                contact_object = SimplePublicObjectInput(
                    properties=properties
                )
                
                # Создаем контакт
                response = api_instance.create(
                    simple_public_object_input=contact_object
                )

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": response.id,
                        "email": properties.get("email"),
                        "firstname": properties.get("firstname"),
                        "lastname": properties.get("lastname"),
                        "properties": properties,
                        "createdAt": response.created_at.isoformat() if response.created_at else None,
                        "updatedAt": response.updated_at.isoformat() if response.updated_at else None
                    }
                }
            }
        except ApiException as e:
            await logger.error(f"HubSpot API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.status if hasattr(e, 'status') else 500,
                    "description": f"HubSpot API error: {e.reason if hasattr(e, 'reason') else str(e)}"
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

