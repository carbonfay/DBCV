import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.crud.user import get_user_by_email
from app.database import sessionmanager
from app.models.user import UserModel
from app.models.role import RoleType
from app.utils.auth import get_password_hash


import json
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db(session: AsyncSession) -> None:
    user = await get_user_by_email(session, settings.FIRST_SUPERUSER)
    if not user:
        superuser = UserModel(
            username=settings.FIRST_SUPERUSER,
            email=settings.FIRST_SUPERUSER,
            first_name="Admin",
            last_name="User",
            hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            role=RoleType.ADMIN,
            is_active=True,
        )
        session.add(superuser)
        await session.commit()
        await session.refresh(superuser)
        logger.info("Superuser created.")
    else:
        user.role = RoleType.ADMIN
        await session.commit()
        await session.refresh(user)
        logger.info("Superuser already exists.")
    #
    # from app.crud.variables import get_variable_by_id
    # from app.models.bot import BotVariables
    # from app.models.channel import ChannelVariables
    # from app.models.user import UserVariables
    # from app.models.session import SessionVariables
    # variable = await get_variable_by_id(session, BotVariables, "9b28e7d2-f520-4554-89b9-486b3e934a2d")
    # print(variable.get_data())
    #
    # variable = await get_variable_by_id(session, ChannelVariables, "4a956b6d-ab6e-4f39-bf0b-965076b1ea53")
    # print(variable.get_data())
    # variable = await get_variable_by_id(session, UserVariables, "3d226ff5-90c6-433d-839b-dcd894c1f3d6")
    # print(variable.get_data())


async def main() -> None:
    logger.info("Creating initial data...")
    async with sessionmanager.session() as session:
        await init_db(session)
    logger.info("Initial data created.")


if __name__ == "__main__":

    asyncio.run(main())
