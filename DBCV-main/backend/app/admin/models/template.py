from fastadmin import SqlAlchemyModelAdmin, register, WidgetType
from app.database import sessionmanager
from app.models.template import TemplateModel
from app.models.template_instance import TemplateInstanceModel
from app.models.template_group import TemplateGroupModel


@register(TemplateModel, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class TemplateAdmin(SqlAlchemyModelAdmin):
    list_display = ("id", "name", "description")
    list_display_links = ("id",)
    list_filter = ("id", "name")
    search_fields = ("name",)

    fieldsets = (
        (None, {
            "fields": (
                "name",
                "description",
                "inputs",
                "outputs",
                "variables",
                "steps",
                "first_step_id",
                "bot_id",
                "group"
            )
        }),
    )

    formfield_overrides = {
        "inputs": (WidgetType.JsonTextArea, {}),
        "outputs": (WidgetType.JsonTextArea, {}),
        "variables": (WidgetType.JsonTextArea, {}),
        "steps": (WidgetType.JsonTextArea, {}),
    }


@register(TemplateInstanceModel, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class TemplateInstanceAdmin(SqlAlchemyModelAdmin):
    list_display = ("id", "name", "description")
    list_display_links = ("id",)
    list_filter = ("id", "name")
    search_fields = ("name",)

    fieldsets = (
        (None, {
            "fields": (
                "name",
                "description",
                "inputs_mapping",
                "outputs_mapping",
                "variables",
                "steps",
                "first_step_id"
            )
        }),
    )

    formfield_overrides = {
        "inputs_mapping": (WidgetType.JsonTextArea, {}),
        "outputs_mapping": (WidgetType.JsonTextArea, {}),
        "variables": (WidgetType.JsonTextArea, {}),
        "steps": (WidgetType.JsonTextArea, {}),
    }


@register(TemplateGroupModel, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class TemplateGroupAdmin(SqlAlchemyModelAdmin):
    list_display = ("id", "name", "owner_id")
    list_display_links = ("id",)
    list_filter = ("id", "name")
    search_fields = ("name",)

    fieldsets = (
        (None, {
            "fields": (
                "name",
                "description",
                "owner",
                "templates"
            )
        }),
    )

    formfield_overrides = {
        "description": (WidgetType.TextArea, {}),
    }