"""HubSpot Get Contact интеграция используя hubspot-api-client библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import hubspot
    from hubspot import HubSpot
    from hubspot.crm.contacts import BasicApi
    from hubspot.crm.contacts.exceptions import ApiException
    from hubspot.crm.objects.exceptions import NotFoundException
    HUBSPOT_AVAILABLE = True
except ImportError:
    HUBSPOT_AVAILABLE = False
    hubspot = None
    HubSpot = None
    BasicApi = None
    ApiException = Exception
    NotFoundException = Exception


class HubSpotGetContactIntegration(BaseIntegration):
    """Интеграция для получения информации о контакте в HubSpot CRM."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="hubspot_get_contact",
            version="1.0.0",
            name="HubSpot Get Contact",
            description="Получение информации о контакте в HubSpot CRM",
            category="crm",
            icon_s3_key="icons/integrations/hubspot.svg",
            color="#FF7A59",
            config_schema={
                "type": "object",
                "required": ["contact_id"],
                "properties": {
                    "contact_id": {
                        "type": "string",
                        "title": "Contact ID",
                        "description": "ID контакта для получения информации"
                    },
                    "properties": {
                        "type": "array",
                        "title": "Properties",
                        "description": "Свойства для получения (если не указаны, возвращаются все)",
                        "items": {
                            "type": "string",
                            "enum": [
                                "email", "firstname", "lastname", "phone", "address", "city", "state",
                                "zip", "country", "company", "jobtitle", "website", "lifecyclestage",
                                "notes_last_updated", "num_conversion_events", "recent_deal_amount",
                                "recent_deal_name", "createdate", "lastmodifieddate", "hs_language",
                                "hs_avatar_filemanager_key", "hs_sales_email_last_used", "hs_social_last_engagement",
                                "hubspot_owner_id", "notes_next_activity_date", "num_contacted_notes",
                                "num_notes", "days_to_close", "closedate", "hubspot_team_id", "hubspot_owner_assigneddate",
                                "hubspot_num_sales_interaction_events", "notes_last_contacted", "notes_next_activity_date",
                                "num_unique_conversion_events", "vid", "identity_profiles", "merge_audits",
                                "hs_is_unworked", "hs_latest_source_timestamp", "hs_object_id", "hubspotscore",
                                "hs_predictivecontactscore_v2", "hs_predictivecontactscore", "hs_calculated_phone_number",
                                "hs_calculated_phone_number_country_code", "hs_calculated_phone_number_invalid",
                                "hs_calculated_phone_number_region_code", "hs_calculated_phone_number_type", "hs_timezone",
                                "hs_language", "hs_analytics_last_timestamp", "hs_analytics_first_timestamp",
                                "hs_analytics_first_touch_converting_campaign", "hs_analytics_last_touch_converting_campaign",
                                "hs_analytics_source", "hs_analytics_source_data_1", "hs_analytics_source_data_2",
                                "hs_analytics_first_visit_timestamp", "hs_analytics_last_visit_timestamp",
                                "hs_analytics_revenue", "hs_analytics_average_page_views", "hs_analytics_pages_per_session",
                                "hs_analytics_lang", "hs_analytics_device_type", "hs_analytics_num_visits",
                                "hs_analytics_num_page_views", "hs_analytics_avg_time_on_site", "hs_analytics_last_timestamp_restricted",
                                "hs_analytics_last_referrer", "hs_analytics_last_url", "hs_analytics_utk",
                                "hs_analytics_num_event_completions", "hs_analytics_first_referrer", "hs_analytics_first_url",
                                "hs_ip_timezone", "hs_analytics_latest_source_timestamp", "hs_latest_source",
                                "hs_latest_source_data_1", "hs_latest_source_data_2", "hs_latest_source_timestamp",
                                "hs_all_contact_vids", "hs_merged_object_ids", "hs_num_form_submissions",
                                "hs_num_portal_sessions", "hubspot_score", "isclosedwon", "isclosed",
                                "isdeleted", "form_submissions", "page_view_history", "email_domain",
                                "hs_email_optout", "hs_email_optout_25193466", "hs_email_hard_bounce_reason",
                                "hs_email_hard_bounce_reason_25193466", "hs_email_quarantined",
                                "hs_email_quarantined_25193466", "hs_email_recipient_failed_deliverability_reas",
                                "hs_email_recipient_failed_deliverability_reas_25193466", "hs_email_sends_since_last_engagement",
                                "hs_emailconfirmationstatus", "hs_facebook_click_id", "hs_feedback_last_nps_follow_up",
                                "hs_feedback_last_nps_rating", "hs_feedback_last_survey_date", "hs_feedback_show_nps_web_survey",
                                "hs_first_engagement_object_id", "hs_google_click_id", "hs_ip_city",
                                "hs_ip_continent_code", "hs_ip_country", "hs_ip_country_code", "hs_ip_latitude",
                                "hs_ip_longitude", "hs_ip_state", "hs_ip_state_code", "hs_is_contact", "hs_last_sales_activity_timestamp",
                                "hs_lastmodifieddate", "hs_object_id", "hs_sales_email_last_clicked",
                                "hs_sales_email_last_opened", "hs_sequence_enrolled", "hs_sequence_enrolled_count",
                                "hs_sequence_ended", "hs_sequence_ended_count", "hs_sequence_exited",
                                "hs_sequence_exited_count", "hs_sequence_is_enrolled", "hs_sequences_actively_enrolled_count",
                                "hs_sequences_enrolled_count", "hs_sequences_opted_out_count", "hubspot_owner_assigneddate",
                                "ip_city", "ip_country", "ip_country_code", "ip_lat", "ip_long", "ip_state",
                                "ip_state_code", "lastmodifieddate", "sales_email_last_clicked", "sales_email_last_opened",
                                "sales_lastmodifieddate", "createdate", "hs_analytics_first_timestamp",
                                "hs_analytics_last_timestamp", "hs_analytics_num_visits", "hs_analytics_num_page_views",
                                "hs_analytics_revenue", "hs_analytics_source", "hs_created_by_conversations",
                                "hs_email_bad_address", "hs_email_domain", "hs_email_hard_bounce_reason",
                                "hs_email_quarantined", "hs_email_recipient_failed_deliverability_reas",
                                "hs_email_sends_since_last_engagement", "hs_emailconfirmed", "hs_facebook_click_id",
                                "hs_feedback_last_nps_follow_up", "hs_feedback_last_nps_rating", "hs_feedback_last_survey_date",
                                "hs_feedback_show_nps_web_survey", "hs_first_engagement_object_id",
                                "hs_google_click_id", "hs_ip_city", "hs_ip_continent_code", "hs_ip_country",
                                "hs_ip_country_code", "hs_ip_latitude", "hs_ip_longitude", "hs_ip_state",
                                "hs_ip_state_code", "hs_is_contact", "hs_latest_source", "hs_latest_source_data_1",
                                "hs_latest_source_data_2", "hs_latest_source_timestamp", "hs_object_id",
                                "hs_predictivecontactscore", "hs_predictivecontactscore_v2", "hs_sales_email_last_used"
                            ]
                        }
                    }
                }
            },
            credentials_provider="hubspot",
            credentials_strategy="api_key",  # Uses access token for private app
            library_name="hubspot-api-client>=7.0.0" if HUBSPOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить информацию о контакте",
                    "config": {
                        "contact_id": "{$session.contact_id$}",
                        "properties": ["email", "firstname", "lastname", "company", "phone"]
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
        contact_id = config.get("contact_id")
        properties = config.get("properties")

        if not contact_id:
            await logger.error("contact_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "contact_id is required"
                }
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем конфигурацию для API с токеном авторизации
            configuration = hubspot.Configuration(
                access_token=access_token
            )

            # Создаем API клиент
            with hubspot.ApiClient(configuration) as api_client:
                api_instance = BasicApi(api_client)
                
                # Подготовим параметры для запроса
                # Если указаны properties, передаем их
                if properties and isinstance(properties, list) and len(properties) > 0:
                    # Получаем контакт с указанными свойствами
                    contact = api_instance.get_by_id(
                        contact_id=contact_id,
                        properties=properties
                    )
                else:
                    # Получаем контакт со всеми свойствами
                    contact = api_instance.get_by_id(contact_id=contact_id)

            # Подготавливаем результат в формате системы
            contact_properties = contact.properties if hasattr(contact, 'properties') else {}
            
            contact_info = {
                "id": contact.id if hasattr(contact, 'id') else None,
                "properties": contact_properties,
                "created_at": contact.created_at.isoformat() if hasattr(contact, 'created_at') and contact.created_at else None,
                "updated_at": contact.updated_at.isoformat() if hasattr(contact, 'updated_at') and contact.updated_at else None,
                "archived": contact.archived if hasattr(contact, 'archived') else False,
                "archived_at": contact.archived_at.isoformat() if hasattr(contact, 'archived_at') and contact.archived_at else None
            }

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": contact_info
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

