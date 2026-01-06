from fastadmin import SqlAlchemyModelAdmin, register, WidgetType
from app.database import sessionmanager
from app.models.credentials import CredentialEntity


@register(CredentialEntity, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class CredentialAdmin(SqlAlchemyModelAdmin):
    # список
    list_display = ("id", "provider", "strategy", "name", "is_default", "updated_at")
    list_display_links = ("id")  # как у BotAdmin
    list_filter = ("provider", "strategy", "is_default")
    search_fields = ("name",)

    # форма
    fieldsets = (
        (None, {
            "fields": (
                "name",
                "provider",
                "strategy",
                "scopes",
                "is_default",
            )
        }),
    )
