from typing import Any
from uuid import UUID

from fastadmin import SqlAlchemyModelAdmin, register, WidgetType
from app.crud.user import authenticate
from app.database import get_db_session, sessionmanager
from app.models.message import MessageModel


@register(MessageModel, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class MessageAdmin(SqlAlchemyModelAdmin):
    list_display = ("id", "text", "created_at")
    list_display_links = ("id", "name")
    list_filter = ("id", "name", "is_public")
    search_fields = ("name", "created_at")

    fieldsets = (
        (None, {
            "fields": (
                "text",
                "channel",
                "sender",
                "recipient",
                "widget",
                "params",



            )
        }),
    )


