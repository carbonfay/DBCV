from typing import Any
from uuid import UUID

from fastadmin import SqlAlchemyModelAdmin, register, WidgetType
from app.crud.user import authenticate
from app.database import get_db_session, sessionmanager
from app.models.note import NoteModel
from app.database import sessionmanager


@register(NoteModel, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class NoteAdmin(SqlAlchemyModelAdmin):
    list_display = ("id", "text")
    list_display_links = ("id", "text", )
    list_filter = ("id", "text")
    fieldsets = (
        (None, {
            "fields": (
                "text",
                "step",
                "bot",
                "pos_x",
                "pos_y",
            )
        }),
    )
