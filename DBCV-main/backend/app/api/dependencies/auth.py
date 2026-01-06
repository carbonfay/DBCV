from typing import Annotated, Union
from uuid import UUID
import jwt
from fastapi import (Depends, HTTPException,
                     Request, status)
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy import select

from app.api.dependencies.db import SessionDep
from app.config import settings
from app.crud.user import get_user

from app.models import BotModel, StepModel
from app.crud.bot import get_bot
from app.models.user import UserModel
from app.models.role import RoleType
from app.models.access import AccessType
from app.models.user_bot_access import user_bot_access
from app.models.anonymous_user import AnonymousUserModel
from app.schemas.auth import TokenPayload
from app.utils.auth import ACCESS_TOKEN_ALGORITHM
from app.utils.users import get_any_user
from app.models.connection import ConnectionModel, ConnectionGroupModel
from app.models.emitter import EmitterModel
import logging

logger = logging.getLogger(__name__)

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

security = HTTPBearer()


class AnyTokenDependency:
    def __init__(self):
        pass

    async def __call__(self, request: Request) -> str:
        """
        Попытка получить токен сначала из OAuth2, затем из Bearer.
        """
        try:
            oauth2_token = await reusable_oauth2(request)
            return oauth2_token
        except HTTPException as e:
            try:
                credentials = await security(request)
                return credentials.credentials
            except HTTPException:
                raise e


TokenDep = Annotated[str, Depends(reusable_oauth2)]
AnyTokenDep = Annotated[str, Depends(AnyTokenDependency())]


def get_token_data(token):
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[ACCESS_TOKEN_ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise InvalidTokenError
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials.",
        )
    return token_data


async def get_current_user(session: SessionDep, token: TokenDep) -> UserModel:
    token_data = get_token_data(token)
    user = await get_user(session, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user.")
    return user


async def get_current_any_user(session: SessionDep, token: AnyTokenDep) -> UserModel | AnonymousUserModel:
    token_data = get_token_data(token)
    return await get_any_user(session, token_data.sub)


CurrentUser = Annotated[UserModel, Depends(get_current_user)]
CurrentAnyUser = Annotated[UserModel | AnonymousUserModel, Depends(get_current_any_user)]


class RoleChecker:
    @staticmethod
    async def _is_required(current_user: CurrentUser, required_role: RoleType) -> UserModel:
        if current_user.role != required_role:
            raise HTTPException(status_code=403, detail="The user doesn't have enough privileges.")
        return current_user

    @classmethod
    def is_required(cls, required_role: RoleType) -> Depends:
        async def dependency(current_user: CurrentUser) -> UserModel:
            return await cls._is_required(current_user, required_role)
        return Depends(dependency)

    @staticmethod
    async def _this_and_upper(current_user: CurrentUser, required_role: RoleType) -> UserModel:
        if RoleType.priority(current_user.role) > RoleType.priority(required_role):
            raise HTTPException(status_code=403, detail="The user doesn't have enough privileges.")
        return current_user

    @classmethod
    def this_and_upper(cls, required_role: RoleType) -> Depends:
        async def dependency(current_user: CurrentUser) -> UserModel:
            return await cls._this_and_upper(current_user, required_role)
        return Depends(dependency)

    @staticmethod
    async def _this_and_lower(current_user: CurrentUser, required_role: RoleType) -> UserModel:
        if RoleType.priority(current_user.role) < RoleType.priority(required_role):
            raise HTTPException(status_code=403, detail="The user doesn't have enough privileges.")
        return current_user

    @classmethod
    def this_and_lower(cls, required_role: RoleType) -> Depends:
        async def dependency(current_user: CurrentUser) -> UserModel:
            return await cls._this_and_lower(current_user, required_role)
        return Depends(dependency)


class BotAccessChecker:
    @staticmethod
    async def get_bot_access(session: SessionDep, bot_id: Union[UUID, str], user: UserModel) -> AccessType:
        if user.role == RoleType.ADMIN:
            return AccessType.EDITOR
        bot = await get_bot(session, bot_id, eager_relationships={})
        if bot.owner_id == user.id:
            return AccessType.EDITOR
        access = await session.execute(
            select(user_bot_access.c.access_type).where(
                user_bot_access.c.user_id == user.id,
                user_bot_access.c.bot_id == bot_id
            )
        )
        return access.scalar_one_or_none() or AccessType.NO_ACCESS

    @classmethod
    async def _has_access(cls, session: SessionDep, bot_id: Union[UUID, str], current_user: CurrentUser, required_access: AccessType) -> UserModel:
        access = await cls.get_bot_access(session, bot_id, current_user)
        if access != required_access:
            raise HTTPException(
                status_code=403, detail="The user doesn't have enough privileges."
            )
        return current_user

    @classmethod
    def has_access(cls, required_access: AccessType) -> Depends:
        async def dependency(session: SessionDep, bot_id: Union[UUID, str], current_user: CurrentUser) -> UserModel:
            return await cls._has_access(session, bot_id, current_user, required_access)
        return Depends(dependency)

    @classmethod
    async def _has_access_or_higher(cls, session: SessionDep, bot_id: Union[UUID, str], current_user: CurrentUser, required_access: AccessType) -> UserModel:
        access = await cls.get_bot_access(session, bot_id, current_user)
        if AccessType.priority(access) > AccessType.priority(required_access):
            raise HTTPException(
                status_code=403, detail="The user doesn't have enough privileges."
            )
        return current_user

    @classmethod
    def has_access_or_higher(cls, required_access: AccessType) -> Depends:
        async def dependency(session: SessionDep, bot_id: Union[UUID, str], current_user: CurrentUser) -> UserModel:
            return await cls._has_access_or_higher(session, bot_id, current_user, required_access)
        return Depends(dependency)

    @classmethod
    async def _has_access_or_lower(cls, session: SessionDep, bot_id: Union[UUID, str], current_user: CurrentUser, required_access: AccessType) -> UserModel:
        access = await cls.get_bot_access(session, bot_id, current_user)
        if AccessType.priority(access) < AccessType.priority(required_access):
            raise HTTPException(
                status_code=403, detail="The user doesn't have enough privileges."
            )
        return current_user

    @classmethod
    def has_access_or_lower(cls, required_access: AccessType) -> Depends:
        async def dependency(session: SessionDep, bot_id: Union[UUID, str], current_user: CurrentUser) -> UserModel:
            return await cls._has_access_or_lower(session, bot_id, current_user, required_access)
        return Depends(dependency)

    @classmethod
    async def get_bot_id_from_connection(cls, session: SessionDep, connection_id: Union[UUID, str]) -> Union[UUID, str]:
        connection = await session.get(ConnectionModel, connection_id)
        if connection and connection.group_id:
            return await cls.get_bot_id_from_connection_group(session, connection.group_id)
        raise HTTPException(status_code=404, detail="Bot not found for the connection.")

    @classmethod
    async def get_bot_id_from_connection_group(cls, session: SessionDep, connection_group_id: Union[UUID, str]) -> Union[UUID, str]:
        connection_group = await session.get(ConnectionGroupModel, connection_group_id)
        if connection_group and connection_group.bot_id:
            return connection_group.bot_id
        return await cls.get_bot_id_from_step(session, connection_group.step_id)

    @staticmethod
    async def get_bot_id_from_emitter(session: SessionDep, emitter_id: Union[UUID, str]) -> Union[UUID, str]:
        emitter = await session.get(EmitterModel, emitter_id)
        if emitter and emitter.bot_id:
            return emitter.bot_id
        raise HTTPException(status_code=404, detail="Bot not found for the emitter.")

    @staticmethod
    async def get_bot_id_from_step(session: SessionDep, step_id: Union[UUID, str]) -> Union[UUID, str]:
        print(f"Getting bot ID from step: {step_id}")
        step = await session.get(StepModel, step_id)
        if step and step.bot_id:
            return step.bot_id
        raise HTTPException(status_code=404, detail="Bot not found for the step.")

    @classmethod
    async def _has_access_by_connection(cls, session: SessionDep, connection_id: Union[UUID, str], current_user: CurrentUser, required_access: AccessType) -> UserModel:
        bot_id = await cls.get_bot_id_from_connection(session, connection_id)
        return await cls._has_access(session, bot_id, current_user, required_access)

    @classmethod
    def has_access_by_connection(cls, required_access: AccessType) -> Depends:
        async def dependency(session: SessionDep, connection_id: Union[UUID, str], current_user: CurrentUser) -> UserModel:
            return await cls._has_access_by_connection(session, connection_id, current_user, required_access)
        return Depends(dependency)

    @classmethod
    async def _has_access_by_connection_group(cls, session: SessionDep, connection_group_id: Union[UUID, str], current_user: CurrentUser, required_access: AccessType) -> UserModel:
        bot_id = await cls.get_bot_id_from_connection_group(session, connection_group_id)
        return await cls._has_access(session, bot_id, current_user, required_access)

    @classmethod
    def has_access_by_connection_group(cls, required_access: AccessType) -> Depends:
        async def dependency(session: SessionDep, connection_group_id: Union[UUID, str], current_user: CurrentUser) -> UserModel:
            return await cls._has_access_by_connection_group(session, connection_group_id, current_user, required_access)
        return Depends(dependency)

    @classmethod
    async def _has_access_by_emitter(cls, session: SessionDep, emitter_id: Union[UUID, str], current_user: CurrentUser, required_access: AccessType) -> UserModel:
        bot_id = await cls.get_bot_id_from_emitter(session, emitter_id)
        return await cls._has_access(session, bot_id, current_user, required_access)

    @classmethod
    def has_access_by_emitter(cls, required_access: AccessType) -> Depends:
        async def dependency(session: SessionDep, emitter_id: Union[UUID, str], current_user: CurrentUser) -> UserModel:
            return await cls._has_access_by_emitter(session, emitter_id, current_user, required_access)
        return Depends(dependency)

    @classmethod
    async def _has_access_by_step(cls, session: SessionDep, step_id: Union[UUID, str], current_user: CurrentUser, required_access: AccessType) -> UserModel:
        bot_id = await cls.get_bot_id_from_step(session, step_id)
        return await cls._has_access(session, bot_id, current_user, required_access)

    @classmethod
    def has_access_by_step(cls, required_access: AccessType) -> Depends:
        async def dependency(session: SessionDep, step_id: Union[UUID, str], current_user: CurrentUser) -> UserModel:
            return await cls._has_access_by_emitter(session, step_id, current_user, required_access)
        return Depends(dependency)


CurrentDeveloper = RoleChecker.this_and_upper(RoleType.DEVELOPER)
CurrentDeveloperDep = Annotated[UserModel, CurrentDeveloper]

CurrentAdmin = RoleChecker.is_required(RoleType.ADMIN)
CurrentAdminDep = Annotated[UserModel, CurrentAdmin]

CurrentBotEditor = BotAccessChecker.has_access(AccessType.EDITOR)
CurrentBotEditorDep = Annotated[UserModel, CurrentBotEditor]

CurrentBotViewer = BotAccessChecker.has_access_or_higher(AccessType.VIEWER)
CurrentBotViewerDep = Annotated[UserModel, CurrentBotViewer]
