from fastadmin import SqlAlchemyInlineModelAdmin

from app.models.bot import BotModel
from app.models.channel import ChannelModel
from app.models.message import MessageModel
from app.models.connection import ConnectionModel
from app.models.user import UserModel
from app.models.subscriber import subscribers_table


class InlineUserChannelModel(SqlAlchemyInlineModelAdmin):
    model = ChannelModel


class InlineMessageModel(SqlAlchemyInlineModelAdmin):
    model = MessageModel
    list_display = ("id", "text")
    list_display_links = ("id", "text")
    list_filter = ("id", "text")
    search_fields = ("text",)


class InlineMessageRecipientModel(SqlAlchemyInlineModelAdmin):
    verbose_name = "Принятые сообщения"

    model = MessageModel
    fk_name = "recipient_id"
    list_display = ("id", "text")
    list_display_links = ("id", "text")
    list_filter = ("id", "text")
    search_fields = ("text",)


class InlineMessageSenderModel(SqlAlchemyInlineModelAdmin):
    verbose_name = "Отправленные сообщения"

    model = MessageModel
    fk_name = "sender_id"
    list_display = ("id", "text")
    list_display_links = ("id", "text")
    list_filter = ("id", "text")
    search_fields = ("text",)


class InlineBotAdmin(SqlAlchemyInlineModelAdmin):
    model = BotModel
    list_display = ("id", "name")
    list_display_links = ("id", "name")
    list_filter = ("id", "name")
    search_fields = ("name",)


class InlineConnectionAdmin(SqlAlchemyInlineModelAdmin):
    model = ConnectionModel
    fk_name = "group_id"
    list_display = ("id",  "step", "next_step", )
    list_display_links = ("id",)
    list_filter = ("id",)
    search_fields = ("id",)
    sortable_by = "id"
    fieldsets = (
        (None, {
            "fields": (
                "id",
                "step",
                "next_step",
                "rules",
                "plugins",
                "filters",
                "variables",
            )
        }),
    )
