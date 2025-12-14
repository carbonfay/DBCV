"""VK Get User интеграция используя httpx для прямых API вызовов."""
from typing import Dict, Any
from uuid import UUID
import httpx
import json

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# httpx уже в requirements.txt, поэтому проверяем доступность
HTTPX_AVAILABLE = True


class VKGetUserIntegration(BaseIntegration):
    """Интеграция для получения информации о пользователе VK."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="vk_get_user",
            version="1.0.0",
            name="VK Get User",
            description="Получение информации о пользователе VK через API",
            category="messaging",
            icon_s3_key="icons/integrations/vk.svg",
            color="#4A76A8",
            config_schema={
                "type": "object",
                "required": ["user_ids"],
                "properties": {
                    "user_ids": {
                        "type": "array",
                        "title": "User IDs",
                        "description": "Массив ID пользователей для получения информации",
                        "items": {
                            "type": "string"
                        }
                    },
                    "fields": {
                        "type": "array",
                        "title": "Fields",
                        "description": "Поля для получения информации о пользователе",
                        "items": {
                            "type": "string",
                            "enum": [
                                "about", "activities", "bdate", "blacklisted", "blacklisted_by_me",
                                "books", "can_post", "can_see_all_posts", "can_see_audio", "can_send_friend_request",
                                "can_write_private_message", "career", "common_count", "connections", "crop_photo",
                                "domain", "education", "exports", "first_name", "followers_count", "friend_status",
                                "games", "has_mobile", "has_photo", "home_town", "interests", "is_favorite",
                                "is_friend", "last_name", "last_seen", "lists", "maiden_name", "military",
                                "movies", "music", "nickname", "occupation", "online", "personal", "photo_100",
                                "photo_200", "photo_200_orig", "photo_400_orig", "photo_max", "photo_max_orig",
                                "quotes", "relation", "relatives", "schools", "sex", "site", "status", "timezone",
                                "tv", "universities", "verified", "wall_comments"
                            ]
                        },
                        "default": ["first_name", "last_name", "photo_100", "online"]
                    },
                    "name_case": {
                        "type": "string",
                        "title": "Name Case",
                        "description": "Падеж для склонения имени и фамилии",
                        "enum": ["nom", "gen", "dat", "acc", "ins", "abl"],
                        "default": "nom"
                    }
                }
            },
            credentials_provider="vk",
            credentials_strategy="api_key",
            library_name="httpx" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить базовую информацию о пользователе",
                    "config": {
                        "user_ids": ["{$user.vk_id$}"],
                        "fields": ["first_name", "last_name", "photo_100", "online"]
                    }
                },
                {
                    "title": "Получить расширенную информацию о пользователе",
                    "config": {
                        "user_ids": ["123456789"],
                        "fields": [
                            "first_name", "last_name", "bdate", "city", "country", 
                            "photo_200", "status", "verified"
                        ]
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
        Выполняет интеграцию используя httpx для прямых вызовов VK API.

        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер

        Returns:
            Результат выполнения в формате системы
        """
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "httpx library is not available"
                }
            }

        # Получаем access_token из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="vk",
            strategy="api_key"
        )

        if not creds:
            await logger.error("VK credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "VK access_token not found in credentials"
                }
            }

        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds

        access_token = payload.get("access_token") or payload.get("token")
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
        user_ids = config.get("user_ids")
        fields = config.get("fields", ["first_name", "last_name", "photo_100", "online"])
        name_case = config.get("name_case", "nom")

        if not user_ids or not isinstance(user_ids, list) or len(user_ids) == 0:
            await logger.error("user_ids is required and must be a non-empty list")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "user_ids is required and must be a non-empty list"
                }
            }

        # ИСПОЛЬЗУЕМ httpx НАПРЯМУЮ
        try:
            # Формируем параметры для запроса к VK API
            params = {
                "user_ids": ",".join(map(str, user_ids)),  # Преобразуем массив в строку через запятую
                "fields": ",".join(fields),
                "name_case": name_case,
                "access_token": access_token,
                "v": "5.131"  # Используем актуальную версию API
            }

            # Выполняем GET-запрос к VK API
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.vk.com/method/users.get", params=params)

            # Проверяем статус ответа
            if response.status_code != 200:
                await logger.error(f"VK API returned status {response.status_code}: {response.text}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": response.status_code,
                        "description": f"VK API returned status {response.status_code}: {response.text}"
                    }
                }

            # Парсим JSON-ответ
            data = response.json()

            # Проверяем, есть ли ошибки в ответе от VK
            if "error" in data:
                error = data["error"]
                error_msg = error.get("error_msg", "Unknown error")
                error_code = error.get("error_code", 500)
                
                await logger.error(f"VK API error: {error_msg} (code: {error_code})")
                return {
                    "response": {
                        "ok": False,
                        "error_code": error_code,
                        "description": f"VK API error: {error_msg}"
                    }
                }

            # Извлекаем результат
            response_data = data.get("response", [])

            # Подготавливаем результат в формате системы
            users_info = []
            for user in response_data:
                user_info = {
                    "id": user.get("id"),
                    "first_name": user.get("first_name"),
                    "last_name": user.get("last_name"),
                    "is_closed": user.get("is_closed"),
                    "can_access_closed": user.get("can_access_closed"),
                    "photo_50": user.get("photo_50"),
                    "photo_100": user.get("photo_100"),
                    "photo_200": user.get("photo_200"),
                    "online": user.get("online", 0),
                    "online_mobile": user.get("online_mobile"),
                    "last_seen": user.get("last_seen", {}).get("time") if "last_seen" in user else None,
                    "status": user.get("status"),
                    "verified": user.get("verified"),
                    "sex": user.get("sex"),
                    "bdate": user.get("bdate"),
                    "city": user.get("city", {}).get("title") if "city" in user else None,
                    "country": user.get("country", {}).get("title") if "country" in user else None,
                    "home_town": user.get("home_town"),
                    "occupation": user.get("occupation", {}).get("name") if "occupation" in user else None,
                    "universities": user.get("universities", []),
                    "schools": user.get("schools", []),
                    "interests": user.get("interests"),
                    "music": user.get("music"),
                    "activities": user.get("activities"),
                    "movies": user.get("movies"),
                    "tv": user.get("tv"),
                    "books": user.get("books"),
                    "games": user.get("games"),
                    "about": user.get("about"),
                    "quotes": user.get("quotes"),
                    "site": user.get("site"),
                    "skype": user.get("skype"),
                    "facebook": user.get("facebook"),
                    "twitter": user.get("twitter"),
                    "livejournal": user.get("livejournal"),
                    "instagram": user.get("instagram")
                }
                users_info.append(user_info)

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "users": users_info,
                        "count": len(users_info)
                    }
                }
            }
        except httpx.RequestError as e:
            await logger.error(f"HTTP request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"HTTP request error: {e}"
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

