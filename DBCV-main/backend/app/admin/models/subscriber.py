from uuid import UUID

from fastadmin import SqlAlchemyModelAdmin, register
from app.crud.user import authenticate
from app.database import get_db_session, sessionmanager
from app.models.subscriber import SubscriberModel
from app.admin.models.inlines import InlineMessageSenderModel, InlineMessageRecipientModel


@register(SubscriberModel, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class SubscriberAdmin(SqlAlchemyModelAdmin):
    list_display = ("id", "type")
    list_display_links = ("id", "type")
    list_filter = ("id", "type")
    search_fields = ("type",)

    fieldsets = (
        (None, {
            "fields": (
                "type",
                "channels",
                "my_channels",
                "sender_messages",
            )
        }),
    )

    inlines = (InlineMessageSenderModel, )
