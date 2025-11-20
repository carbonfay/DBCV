from typing import Any
from uuid import UUID

from fastadmin import SqlAlchemyModelAdmin, register
from app.crud.user import authenticate
from app.database import get_db_session, sessionmanager
from app.models.widget import WidgetModel
from app.admin.models.subscriber import SubscriberAdmin

from app.database import sessionmanager


@register(WidgetModel, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class WidgetAdmin(SqlAlchemyModelAdmin):
    list_display = ("id", "name", "description", "get_widget_type_display", "owner_id", "get_parent_widget_link", "created_at")
    list_display_links = ("id", "name")
    list_filter = ("is_render", "owner_id", "created_at", "parent_widget_id")
    search_fields = ("name", "description", "owner_id")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
    list_per_page = 25

    fieldsets = (
        ("Основная информация", {
            "fields": (
                "id",
                "name",
                "description",
                "owner_id",
            )
        }),
        ("Тип виджета", {
            "fields": (
                "is_render",
                "parent_widget_id",
            ),
            "description": "is_render: False = шаблон, True = готовый виджет"
        }),
        ("Содержимое", {
            "fields": (
                "body",
                "css", 
                "js",
            )
        }),
        ("Системная информация", {
            "fields": (
                "created_at",
                "updated_at",
            ),
            "classes": ("collapse",)
        }),
    )