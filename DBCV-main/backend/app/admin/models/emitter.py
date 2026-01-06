from typing import Any
from uuid import UUID

from fastadmin import SqlAlchemyModelAdmin, register, WidgetType
from app.models.emitter import EmitterModel
from app.database import sessionmanager


@register(EmitterModel, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class EmitterAdmin(SqlAlchemyModelAdmin):
    list_display = ("id", "name", "job_id", "step")
    list_display_links = ("id")
    list_filter = ("id", "name")
    search_fields = ("name",)
    fieldsets = (
        (None, {
            "fields": (
                "name",
                "needs_message_processing",
                "job_id",
                "message",
                "bot",
                "cron",
            )
        }),
    )
