"""Telegram Get User integration."""
from typing import Dict, Any
from uuid import UUID

from telegram import Bot
from telegram.error import BadRequest, Unauthorized, NetworkError

from app.auth.credentials_resolver import CredentialsResolver
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.loggers.bot import BotLogger


class TelegramGetUserIntegration(BaseIntegration):
    """Integration to get user information from Telegram."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_get_user",
            version="1.0.0",
            name="Telegram Get User",
            description="Get user information from a Telegram chat",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "Chat ID where the user is a member"
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "User ID to get information about"
                    }
                },
                "required": ["chat_id", "user_id"]
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot",
            examples=[
                {
                    "config": {
                        "chat_id": "@example_chat",
                        "user_id": 123456789
                    },
                    "description": "Get user info from a public chat"
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
        """Execute the integration to get user information."""
        try:
            # Get credentials
            creds = await credentials_resolver.get_default_for(
                bot_id=bot_id,
                provider="telegram",
                strategy="api_key"
            )

            if not creds or "token" not in creds:
                return {
                    "response": {
                        "ok": False,
                        "error_code": 401,
                        "description": "Telegram API token not found"
                    }
                }

            # Initialize bot
            bot = Bot(token=creds["token"])

            # Get chat member information
            chat_member = await bot.get_chat_member(
                chat_id=config["chat_id"],
                user_id=config["user_id"]
            )

            # Convert to dict and return
            result = {
                "user": chat_member.user.to_dict() if chat_member.user else None,
                "status": chat_member.status,
                "until_date": chat_member.until_date,
                "can_be_edited": chat_member.can_be_edited,
                "can_change_info": chat_member.can_change_info,
                "can_delete_messages": chat_member.can_delete_messages,
                "can_invite_users": chat_member.can_invite_users,
                "can_restrict_members": chat_member.can_restrict_members,
                "can_pin_messages": chat_member.can_pin_messages,
                "can_promote_members": chat_member.can_promote_members,
                "is_member": chat_member.is_member,
                "can_send_messages": chat_member.can_send_messages,
                "can_send_media_messages": chat_member.can_send_media_messages,
                "can_send_polls": chat_member.can_send_polls,
                "can_send_other_messages": chat_member.can_send_other_messages,
                "can_add_web_page_previews": chat_member.can_add_web_page_previews,
                "can_manage_chat": chat_member.can_manage_chat,
                "can_manage_video_chats": chat_member.can_manage_video_chats,
                "custom_title": chat_member.custom_title
            }

            return {
                "response": {
                    "ok": True,
                    "result": result
                }
            }

        except BadRequest as e:
            logger.error(f"Telegram BadRequest: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": f"Bad request: {str(e)}"
                }
            }
        except Unauthorized as e:
            logger.error(f"Telegram Unauthorized: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": f"Unauthorized: {str(e)}"
                }
            }
        except NetworkError as e:
            logger.error(f"Telegram NetworkError: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Network error: {str(e)}"
                }
            }
        except Exception as e:
            logger.error(f"Unexpected error in Telegram get_user: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Unexpected error: {str(e)}"
                }
            }