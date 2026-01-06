from typing import Any
from uuid import UUID

from fastadmin import SqlAlchemyModelAdmin, register, WidgetType
from app.database import get_db_session, sessionmanager
from app.models.connection import ConnectionModel, ConnectionGroupModel
from app.database import sessionmanager
from app.crud.connection import get_connection
from app.admin.models.inlines import InlineConnectionAdmin


@register(ConnectionGroupModel, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class ConnectionGroupAdmin(SqlAlchemyModelAdmin):
    list_display = ("id", "search_type", "step", "created_at", "updated_at")
    list_display_links = ("id", "search_type",)
    list_filter = ("search_type",)
    search_fields = ("search_type",)
    sortable_by = "search_type"
    fieldsets = (
        (None, {
            "fields": (
                "id",
                "search_type",
                "code",
                "variables",
                "request",
                "step",
                "bot"
            )
        }),
    )

    formfield_overrides = {  # noqa: RUF012
        "code": (WidgetType.TextArea, {"required": False}),
    }

    inlines = (InlineConnectionAdmin, )


@register(ConnectionModel, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class ConnectionAdmin(SqlAlchemyModelAdmin):
    list_display = ("id", "group",  "next_step", "created_at", "updated_at")
    list_display_links = ("id",)
    list_filter = ("id",)
    search_fields = ("id",)
    sortable_by = "id"
    fieldsets = (
        (None, {
            "fields": (
                "id",
                "next_step",
                "rules",
                "plugins",
                "filters",
                "group",
            )
        }),
    )


