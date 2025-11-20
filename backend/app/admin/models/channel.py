from typing import Any
from uuid import UUID

from fastadmin import SqlAlchemyModelAdmin, register, WidgetType

from app.admin.models.inlines import InlineMessageModel
from app.crud.user import authenticate
from app.database import get_db_session, sessionmanager
from app.models.channel import ChannelModel, ChannelVariables
from app.crud.channel import create_channel, get_channel
from app.schemas.channel import ChannelCreate, ChannelUpdate


@register(ChannelModel, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class ChannelAdmin(SqlAlchemyModelAdmin):
    list_display = ("id", "name", "owner", "is_public")
    list_display_links = ("id", "name")
    list_filter = ("id", "name", "is_public")
    search_fields = ("name",)

    fieldsets = (
        (None, {
            "fields": (
                "name",
                "is_public",
                "owner",
                "default_bot",
                "subscribers",
                "messages",
                "variables"
            )
        }),
    )


@register(ChannelVariables, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class ChannelVariablesAdmin(SqlAlchemyModelAdmin):
    list_display = ("id", "data", "created_at", "updated_at")
    list_display_links = ("id",)
    list_filter = ("id", "data", "created_at", "updated_at")
    search_fields = ("id", "data")
    formfield_overrides = {
        "data": (WidgetType.JsonTextArea, {})
    }

    fieldsets = (
        (None, {
            "fields": (
                "data",
            )
        }),
    )

    async def save_model(self, request, obj, form, change):
        await super().save_model(request, obj, form, change)
        try:
            from app.crud.variables import _invalidate_variables_cache
            from app.models.channel import ChannelVariables
            await _invalidate_variables_cache(str(obj.id), ChannelVariables)
        except Exception as e:
            import logging
            logging.warning(f"Failed to invalidate channel variables cache: {e}")