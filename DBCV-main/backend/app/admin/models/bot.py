from fastadmin import SqlAlchemyModelAdmin, register, WidgetType, DashboardWidgetType

from app.database import sessionmanager
from app.models.bot import BotModel, BotVariables


@register(BotModel, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class BotAdmin(SqlAlchemyModelAdmin):
    list_display = ("id", "name", "owner")
    list_display_links = ("id")
    list_filter = ("id", "name")
    search_fields = ("name",)

    fieldsets = (
        (None, {
            "fields": (
                "name",
                "owner",
                "first_step",
                "logs",
                "config",
                "cache_structure"
            )
        }),
    )
    formfield_overrides = {
        "logs": (WidgetType.TextArea, {}),
        "config": (WidgetType.JsonTextArea, {})
    }


@register(BotVariables, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class BotVariablesAdmin(SqlAlchemyModelAdmin):
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
            from app.models.bot import BotVariables
            await _invalidate_variables_cache(str(obj.id), BotVariables)
        except Exception as e:
            import logging
            logging.warning(f"Failed to invalidate bot variables cache: {e}")