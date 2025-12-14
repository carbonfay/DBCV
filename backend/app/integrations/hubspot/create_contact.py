"""HubSpot Create Contact интеграция используя hubspot-api-client библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import hubspot
    from hubspot.crm.contacts import BasicApi, ApiException
    from hubspot.crm.contacts.models import SimplePublicObjectInput
    HUBSPOT_AVAILABLE = True
except ImportError:
    HUBSPOT_AVAILABLE = False
    hubspot = None
    BasicApi = None
    SimplePublicObjectInput = None
    ApiException = Exception


class HubSpotCreateContactIntegration(BaseIntegration):
    """Интеграция для создания контакта в HubSpot CRM."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="hubspot_create_contact",
            version="1.0.0",
            name="HubSpot Create Contact",
            description="Создание контакта в HubSpot CRM",
            category="crm",
            icon_s3_key="icons/integrations/hubspot.svg",
            color="#FF7A59",
            config_schema={
                "type": "object",
                "required": ["properties"],
                "properties": {
                    "properties": {
                        "type": "object",
                        "title": "Properties",
                        "description": "Свойства контакта",
                        "required": ["email"],
                        "properties": {
                            "email": {
                                "type": "string",
                                "title": "Email",
                                "description": "Email адрес (уникальный идентификатор)"
                            },
                            "firstname": {
                                "type": "string",
                                "title": "First Name",
                                "description": "Имя"
                            },
                            "lastname": {
                                "type": "string",
                                "title": "Last Name",
                                "description": "Фамилия"
                            },
                            "phone": {
                                "type": "string",
                                "title": "Phone",
                                "description": "Телефон"
                            },
                            "website": {
                                "type": "string",
                                "title": "Website",
                                "description": "Веб-сайт"
                            },
                            "company": {
                                "type": "string",
                                "title": "Company",
                                "description": "Компания"
                            },
                            "jobtitle": {
                                "type": "string",
                                "title": "Job Title",
                                "description": "Должность"
                            },
                            "address": {
                                "type": "string",
                                "title": "Address",
                                "description": "Адрес"
                            },
                            "city": {
                                "type": "string",
                                "title": "City",
                                "description": "Город"
                            },
                            "state": {
                                "type": "string",
                                "title": "State",
                                "description": "Штат/область"
                            },
                            "zip": {
                                "type": "string",
                                "title": "ZIP Code",
                                "description": "Почтовый индекс"
                            },
                            "country": {
                                "type": "string",
                                "title": "Country",
                                "description": "Страна"
                            },
                            "lifecyclestage": {
                                "type": "string",
                                "title": "Lifecycle Stage",
                                "description": "Стадия жизненного цикла",
                                "enum": ["lead", "subscriber", "marketingqualifiedlead", "salesqualifiedlead", 
                                       "opportunity", "customer", "evangelist", "other"]
                            },
                            "notes": {
                                "type": "string",
                                "title": "Notes",
                                "description": "Примечания"
                            }
                        }
                    }
                }
            },
            credentials_provider="hubspot",
            credentials_strategy="api_key",  # HubSpot использует private app access token
            library_name="hubspot-api-client>=7.0.0" if HUBSPOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Создать контакт с email и именем",
                    "config": {
                        "properties": {
                            "email": "{$user.email$}",
                            "firstname": "{$user.first_name$}",
                            "lastname": "{$user.last_name$}",
                            "phone": "{$user.phone$}",
                            "company": "{$session.company$}",
                            "lifecyclestage": "lead"
                        }
                    }
                },
                {
                    "title": "Создать контакт с полной информацией",
                    "config": {
                        "properties": {
                            "email": "john.doe@example.com",
                            "firstname": "John",
                            "lastname": "Doe",
                            "phone": "+1234567890",
                            "jobtitle": "Developer",
                            "company": "Acme Inc.",
                            "website": "https://example.com",
                            "address": "123 Main Street",
                            "city": "New York",
                            "state": "NY",
                            "zip": "10001",
                            "country": "USA",
                            "lifecyclestage": "marketingqualifiedlead"
                        }
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

        # Получаем учетные данные из credentials
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

        # Получаем свойства из config
        properties = config.get("properties", {})

        if not properties or "email" not in properties:
            await logger.error("properties with email are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "properties with email are required"
                }
            }

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
                result = api_instance.create(
                    simple_public_object_input=contact_object
                )

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": result.id,
                        "createdAt": result.created_at.isoformat() if hasattr(result, 'created_at') and result.created_at else None,
                        "updatedAt": result.updated_at.isoformat() if hasattr(result, 'updated_at') and result.updated_at else None,
                        "archived": result.archived if hasattr(result, 'archived') else None,
                        "properties": result.properties,
                        "propertiesWithHistory": getattr(result, 'properties_with_history', None)
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

