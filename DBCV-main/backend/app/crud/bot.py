from typing import Type, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import UserModel
from app.models.bot import BotModel
from app.schemas import bot as schemas_bot
from app.crud.utils import is_object_unique
from fastapi import HTTPException


async def check_bot_unique(
        session: AsyncSession,
        bot_in: schemas_bot.BotBase,
        exclude_id: UUID | str | None = None,
) -> None:
    if not await is_bot_unique(session, bot_in, exclude_id):
        raise HTTPException(
            status_code=400,
            detail="The bot with the given name already exists.",
        )


async def is_bot_unique(
        session: AsyncSession,
        bot_in: schemas_bot.BotBase | schemas_bot.BotUpdate,
        exclude_id: UUID | str | None = None,
) -> bool:
    return await is_object_unique(
        session,
        BotModel,
        bot_in,
        unique_fields=("name",),
        exclude_id=exclude_id,
    )


async def get_bot(session: AsyncSession, bot_id: UUID | str,
                  eager_relationships: Optional[Dict[str, Any]] = None,) -> Type[BotModel]:
    bot = await BotModel.get_obj(session, bot_id, eager_relationships)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found.")
    return bot


async def create_bot(
        session: AsyncSession, bot_in: schemas_bot.BotCreate, owner: UserModel | None = None
) -> BotModel:
    db_obj = BotModel(
        **bot_in.model_dump(exclude={"owner_id"}),
        owner=owner,
    )
    session.add(db_obj)
    return db_obj


async def update_bot(
        session: AsyncSession,
        bot_id: UUID | str,
        bot_in: schemas_bot.BotUpdate,
) -> Type[BotModel]:
    bot = await get_bot(session, bot_id)
    for key, value in bot_in.model_dump(exclude_unset=True, exclude={"variables"}).items():
        setattr(bot, key, value)
    return bot


async def delete_bot(session: AsyncSession, bot_id: UUID | str) -> None:
    await session.delete(await get_bot(session, bot_id))
