from typing import Any
from uuid import UUID, uuid4

import bcrypt
from fastadmin import SqlAlchemyModelAdmin, register, WidgetType

from app.admin.models.inlines import InlineBotAdmin, InlineUserChannelModel
from app.crud.user import authenticate
from app.database import get_db_session, sessionmanager
from app.models.user import UserModel, UserVariables
from app.models.anonymous_user import AnonymousUserModel
from app.admin.models.subscriber import SubscriberAdmin
from app.utils.auth import get_password_hash
from app.models.role import RoleType

@register(AnonymousUserModel, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class AnonymousUserAdmin(SqlAlchemyModelAdmin):
    list_display_links = ("id", )


@register(UserModel, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class UserAdmin(SqlAlchemyModelAdmin):
    list_display = ("id", "username", "email", "role", "is_active", "created_at", "updated_at")
    list_display_links = ("id", "username")
    list_filter = ("id", "username", "role", "is_active")
    search_fields = ("username",)
    fieldsets = (
        (None, {
            "fields": (
                "username",
                "email",
                "first_name",
                "last_name",
                "channels",
                "bots",
                "access_bots"
            )
        }),
        ("Permissions", {"fields": ("is_active", "role")}),
    )
    formfield_overrides = {  # noqa: RUF012
        "password": (WidgetType.PasswordInput, {"passwordModalForm": True}),
    }

    inlines = (InlineUserChannelModel, )

    async def authenticate(self, username: str, password: str) -> UUID | int | None:
        async with sessionmanager.session() as session:
            user = await authenticate(session, username, password)
            if not user:
                return None
            if not user.role == RoleType.ADMIN:
                return None
            return user.id

    async def change_password(self, id: UUID | int, password: str) -> None:
        user = await self.model_cls.filter(id=id).first()
        if not user:
            return
        user.hash_password = get_password_hash(password)
        await user.save(update_fields=("hashed_password",))


@register(UserVariables, sqlalchemy_sessionmaker=sessionmanager._sessionmaker)
class UserVariablesAdmin(SqlAlchemyModelAdmin):
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
            from app.models.user import UserVariables
            await _invalidate_variables_cache(str(obj.id), UserVariables)
        except Exception as e:
            import logging
            logging.warning(f"Failed to invalidate user variables cache: {e}")