from typing import Any
from uuid import UUID

from fastadmin import SqlAlchemyModelAdmin, register, WidgetType
from app.crud.user import authenticate
from app.database import get_db_session, sessionmanager
from app.models.step import StepModel
from app.database import sessionmanager


@register(StepModel, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class StepAdmin(SqlAlchemyModelAdmin):
    list_display = ("id", "name", "is_proxy", "bot", "message", "connections", "created_at", "updated_at")
    list_display_links = ("id", "name", "is_proxy", "bot",  "message",)
    list_filter = ("id", "name", "is_proxy")
    search_fields = ("name",)
    fieldsets = (
        (None, {
            "fields": (
                "name",
                "is_proxy",
                "bot",
                "pos_x",
                "pos_y",
            )
        }),
    )
