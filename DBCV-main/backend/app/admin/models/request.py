from typing import Any
from uuid import UUID

from fastadmin import SqlAlchemyModelAdmin, register
from app.crud.user import authenticate
from app.database import get_db_session, sessionmanager
from app.models.request import RequestModel
from app.database import sessionmanager


@register(RequestModel, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class RequestAdmin(SqlAlchemyModelAdmin):
    list_display = ("id", "name", "params", "request_url", "method", "created_at", "updated_at")
    list_display_links = ("id", "name", )
    search_fields = ("name",)
    fieldsets = (
        (None, {
            "fields": (
                "name",
                "method",
                "request_url",
                "params",
                "data",
                "content",
                "headers",
                "proxies",
                "attachments"
            )
        }),
    )



