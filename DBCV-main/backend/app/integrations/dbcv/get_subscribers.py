"""Интеграция для получения списка подписчиков канала."""
from typing import Dict, Any, List
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger
from app.managers.data_manager import DataManager
from app.database import sessionmanager


class GetSubscribersIntegration(BaseIntegration):
    """Интеграция для получения списка подписчиков канала (только пользователей, не ботов)."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="dbcv_get_subscribers",
            version="1.0.0",
            name="Get Subscribers",
            description="Получить список всех подписчиков канала (только пользователей, не ботов) для рассылки",
            category="crm",
            icon_s3_key="icons/integrations/dbcv.svg",
            color="#4CAF50",
            config_schema={
                "type": "object",
                "required": ["channel_id"],
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "title": "Channel ID",
                        "description": "ID канала (можно использовать переменные: {$channel.id$})"
                    },
                    "filter_type": {
                        "type": "string",
                        "title": "Filter Type",
                        "enum": ["users_only", "all"],
                        "default": "users_only",
                        "description": "Тип фильтрации: users_only - только пользователи, all - все подписчики"
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="none",
            library_name=None,
            examples=[
                {
                    "title": "Получить всех пользователей канала",
                    "config": {
                        "channel_id": "{$channel.id$}",
                        "filter_type": "users_only"
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
        Получает список подписчиков канала.
        
        Args:
            config: Параметры интеграции
                - channel_id: ID канала (обязательно)
                - filter_type: Тип фильтрации (users_only или all, по умолчанию users_only)
            credentials_resolver: Не используется
            bot_id: ID бота
            logger: Логгер
        
        Returns:
            Результат выполнения в формате:
            {
                "response": {
                    "ok": True/False,
                    "result": {
                        "subscribers": [
                            {
                                "id": "uuid",
                                "type": "user" | "anonymous_user",
                                "username": "...",
                                "email": "...",
                                "first_name": "...",
                                "last_name": "...",
                                "variables": {...}
                            },
                            ...
                        ],
                        "count": 10
                    } или "error": "..."
                }
            }
        """
        channel_id = config.get("channel_id")
        filter_type = config.get("filter_type", "users_only")
        
        if not channel_id:
            await logger.error("channel_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "channel_id is required"
                }
            }
        
        try:
            # Создаем DataManager для получения данных
            from redis.asyncio import Redis
            from app.config import settings
            redis = Redis.from_url(settings.CACHE_REDIS_URL)
            data_manager = DataManager(redis, sessionmanager.engine)
            
            # Получаем список подписчиков с их типами
            subscribers_ids = await data_manager.get_channel_all_subscribers(
                str(channel_id), 
                filter_type=filter_type
            )
            
            if not subscribers_ids:
                await logger.info(f"No subscribers found for channel {channel_id}")
                return {
                    "response": {
                        "ok": True,
                        "result": {
                            "subscribers": [],
                            "count": 0
                        }
                    }
                }
            
            # Получаем полные данные для каждого подписчика
            subscribers_data = []
            
            async with sessionmanager.session() as session:
                from sqlalchemy import select, text
                from app.models.subscriber import SubscriberModel
                from app.models.user import UserModel
                from app.models.anonymous_user import AnonymousUserModel
                
                # Получаем подписчиков с их типами (уже отфильтрованы в запросе)
                subscriber_ids_list = [sub.get("id") for sub in subscribers_ids]
                
                if not subscriber_ids_list:
                    return {
                        "response": {
                            "ok": True,
                            "result": {
                                "subscribers": [],
                                "count": 0
                            }
                        }
                    }
                
                # Запрос для получения подписчиков с их данными
                # Используем IN для списка ID (более совместимо)
                if subscriber_ids_list:
                    # Создаем плейсхолдеры для IN
                    placeholders = ",".join([f":id_{i}" for i in range(len(subscriber_ids_list))])
                    params = {f"id_{i}": sub_id for i, sub_id in enumerate(subscriber_ids_list)}
                    
                    query = text(f"""
                        SELECT 
                            s.id,
                            s.type,
                            CASE 
                                WHEN s.type = 'user' THEN u.username
                                ELSE NULL
                            END as username,
                            CASE 
                                WHEN s.type = 'user' THEN u.email
                                ELSE NULL
                            END as email,
                            CASE 
                                WHEN s.type = 'user' THEN u.first_name
                                ELSE NULL
                            END as first_name,
                            CASE 
                                WHEN s.type = 'user' THEN u.last_name
                                ELSE NULL
                            END as last_name
                        FROM subscriber s
                        LEFT JOIN "user" u ON s.id = u.id AND s.type = 'user'
                        WHERE s.id IN ({placeholders})
                    """)
                    
                    result = await session.execute(query, params)
                    rows = result.mappings().all()
                else:
                    rows = []
                
                for row in rows:
                    subscriber_type = row.get("type")
                    
                    subscriber_info = {
                        "id": str(row.get("id")),
                        "type": subscriber_type,
                        "username": row.get("username"),
                        "email": row.get("email"),
                        "first_name": row.get("first_name"),
                        "last_name": row.get("last_name"),
                    }
                    
                    # Получаем переменные пользователя если есть
                    try:
                        user_vars = await data_manager.get_user_variables(str(row.get("id")))
                        if user_vars:
                            subscriber_info["variables"] = user_vars.get("data", {})
                        else:
                            subscriber_info["variables"] = {}
                    except Exception as e:
                        await logger.warning(f"Could not get variables for subscriber {row.get('id')}: {e}")
                        subscriber_info["variables"] = {}
                    
                    subscribers_data.append(subscriber_info)
            
            await logger.info(f"Found {len(subscribers_data)} subscribers for channel {channel_id}")
            
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "subscribers": subscribers_data,
                        "count": len(subscribers_data)
                    }
                }
            }
            
        except Exception as e:
            await logger.error(f"Error getting subscribers: {e}")
            import traceback
            traceback_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            await logger.error(f"Traceback: {traceback_str}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }

