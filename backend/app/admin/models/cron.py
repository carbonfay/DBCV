from typing import Any
from uuid import UUID

from fastadmin import SqlAlchemyModelAdmin, register, WidgetType

from app.models.cron import CronModel
from app.database import sessionmanager


@register(CronModel, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class CronAdmin(SqlAlchemyModelAdmin):
    list_display = ("id", "name")
    list_display_links = ("id", "name")

    fieldsets = (
        (None, {
            "fields": (
                "name",
                "year",
                "month",
                "week",
                "day_of_week",
                "hour",
                "minute",
                "second",
                "start_date",
                "end_date",
                "timezone",
                "jitter",

            )
        }),
    )
