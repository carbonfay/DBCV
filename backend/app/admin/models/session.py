from typing import Any
from uuid import UUID

from fastadmin import SqlAlchemyModelAdmin, register, WidgetType
from app.crud.user import authenticate
from app.database import get_db_session, sessionmanager
from app.models.session import SessionModel, SessionVariables
from app.database import sessionmanager


@register(SessionModel, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class SessionAdmin(SqlAlchemyModelAdmin):
    list_display = ("id", "user", "bot", "channel", "step", )
    list_display_links = ("id", "user", "bot", "channel", "step", )
    list_filter = ("id", "user_id", "bot_id", "channel_id", "step_id", )
    search_fields = ("name",)

    fieldsets = (
        (None, {
            "fields": (
                "user",
                "bot",
                "channel",
                "step",
            )
        }),
    )


@register(SessionVariables, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class SessionVariablesAdmin(SqlAlchemyModelAdmin):
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
            from app.models.session import SessionVariables
            await _invalidate_variables_cache(str(obj.id), SessionVariables)
        except Exception as e:
            import logging
            logging.warning(f"Failed to invalidate session variables cache: {e}")