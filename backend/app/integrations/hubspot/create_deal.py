"""HubSpot Create Deal интеграция используя hubspot-api-client библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    from hubspot import HubSpot
    from hubspot.crm.deals import SimplePublicObjectInput, ApiException
    HUBSPOT_AVAILABLE = True
except ImportError:
    HUBSPOT_AVAILABLE = False
    HubSpot = None
    SimplePublicObjectInput = None
    ApiException = Exception


class HubSpotCreateDealIntegration(BaseIntegration):
    """Интеграция для создания сделки в HubSpot через hubspot-api-client."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="hubspot_create_deal",
            version="1.0.0",
            name="HubSpot Create Deal",
            description="Создание сделки в HubSpot CRM через HubSpot API (POST /crm/v3/objects/deals)",
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
                        "description": "Свойства сделки (dealname, amount, dealstage, pipeline и др.)",
                        "properties": {
                            "dealname": {
                                "type": "string",
                                "title": "Deal Name",
                                "description": "Название сделки"
                            },
                            "amount": {
                                "type": "string",
                                "title": "Amount",
                                "description": "Сумма сделки"
                            },
                            "dealstage": {
                                "type": "string",
                                "title": "Deal Stage",
                                "description": "Стадия сделки (ID стадии из pipeline)"
                            },
                            "pipeline": {
                                "type": "string",
                                "title": "Pipeline",
                                "description": "ID воронки продаж"
                            },
                            "closedate": {
                                "type": "string",
                                "title": "Close Date",
                                "description": "Дата закрытия сделки в формате ISO 8601 (например, 2024-12-31T23:59:59Z)",
                                "format": "date-time"
                            },
                            "dealtype": {
                                "type": "string",
                                "title": "Deal Type",
                                "description": "Тип сделки"
                            }
                        }
                    },
                    "associations": {
                        "type": "array",
                        "title": "Associations",
                        "description": "Связи с другими объектами (контакты, компании и т.д.)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "to": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"}
                                    }
                                },
                                "types": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "associationCategory": {"type": "string"},
                                            "associationTypeId": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            credentials_provider="hubspot",
            credentials_strategy="api_key",
            library_name="hubspot-api-client>=7.0.0" if HUBSPOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Создать простую сделку",
                    "config": {
                        "properties": {
                            "dealname": "Новая сделка",
                            "amount": "10000",
                            "dealstage": "appointmentscheduled"
                        }
                    }
                },
                {
                    "title": "Создать сделку с полными данными",
                    "config": {
                        "properties": {
                            "dealname": "Крупная сделка",
                            "amount": "50000",
                            "dealstage": "qualifiedtobuy",
                            "pipeline": "default",
                            "closedate": "2024-12-31T23:59:59Z",
                            "dealtype": "newbusiness"
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
        
        # Получаем API ключ из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="hubspot",
            strategy="api_key"
        )
        
        if not creds:
            # Пробуем получить через get_single_for для обратной совместимости
            creds = await credentials_resolver.get_single_for(
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
                    "description": "HubSpot API key not found in credentials"
                }
            }
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        api_key = payload.get("api_key") or payload.get("access_token") or payload.get("token")
        if not api_key:
            await logger.error(f"API key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "API key not found in credentials"
                }
            }
        
        # Получаем параметры из config
        properties = config.get("properties", {})
        associations = config.get("associations")
        
        if not properties:
            await logger.error("properties are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "properties are required"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            client = HubSpot(access_token=api_key)
            
            # Создаем объект SimplePublicObjectInput
            deal_input = SimplePublicObjectInput(properties=properties)
            
            # Если есть associations, добавляем их
            if associations:
                deal_input.associations = associations
            
            # Создаем сделку
            result = client.crm.deals.basic_api.create(
                simple_public_object_input=deal_input
            )
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": result.id,
                        "properties": result.properties,
                        "created_at": result.created_at.isoformat() if result.created_at else None,
                        "updated_at": result.updated_at.isoformat() if result.updated_at else None
                    }
                }
            }
        except ApiException as e:
            await logger.error(f"HubSpot API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.status if hasattr(e, 'status') else 500,
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

