import asyncio
import os
import sys
from configparser import ConfigParser

import asyncpg
import pytest
import pytest_asyncio
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.future import select

from app.models.role import RoleType

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.crud.step import create_step
from app.crud.user import create_user
from app.schemas.user import UserCreate
from app.crud.bot import create_bot
from app.schemas.step import StepCreate
from app.crud.message import create_message
from app.crud.widget import create_widget
from app.models import WidgetModel
from app.schemas.widget import WidgetCreate
from app.crud.channel import create_channel
from app.models import ChannelModel
from app.schemas.channel import ChannelCreate
from app.models import MessageModel
from app.schemas.message import MessageCreate
from app.schemas.bot import BotCreate
from app.models.base import BaseModel
from app.models import StepModel
from app.api.routes import channels

config = ConfigParser()
config.read("tests/.test_env")


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Фикстура для подключения к тестовой базе данных (создание и удаление базы)
@pytest_asyncio.fixture(scope="function")
async def db_engine():
    db_url = (f'://{config["DEFAULT"]["POSTGRES_USER"]}:{config["DEFAULT"]["POSTGRES_PASSWORD"]}'
              f'@{config["DEFAULT"]["POSTGRES_HOST"]}:{config["DEFAULT"]["POSTGRES_PORT"]}'
              f'/{config["DEFAULT"]["POSTGRES_DB"]}')

    # Удаляем тестовую базу данных перед тестом
    conn = await asyncpg.connect(f"postgresql{db_url}")
    try:
        await conn.execute(f"DROP DATABASE IF EXISTS {config["DEFAULT"]["POSTGRES_DB"]}_test WITH (FORCE)")
    finally:
        await conn.close()

    # Открываем соединение через контекстный менеджер
    # Подключение через asyncpg для выполнения CREATE DATABASE
    conn = await asyncpg.connect(f"postgresql{db_url}")
    try:
        await conn.execute(f"CREATE DATABASE {config["DEFAULT"]["POSTGRES_DB"]}_test")
    except asyncpg.DuplicateDatabaseError:
        # База данных уже существует
        pass
    finally:
        await conn.close()
    # Подключаемся к тестовой базе данных
    test_db_engine = create_async_engine(f'postgresql+asyncpg{db_url}_test', future=True)

    # Применяем миграции через Alembic API
    # migrations_path = "migrations"
    # alembic_cfg = Config("alembic.ini")
    # alembic_cfg.set_main_option("sqlalchemy.url", f'postgresql+asyncpg{db_url}_test')
    #
    # Применяем миграции к тестовой базе
    # async with test_db_engine.begin() as connection:
    #     # Передаем соединение в Alembic для выполнения миграций
    #     try:
    #         print("Применение миграций...")
    #         await connection.run_sync(lambda conn: command.upgrade(alembic_cfg, "head"))
    #         print("Миграции успешно применены!")
    #     except Exception as e:
    #         print(f"Ошибка при применении миграций: {e}")

    # Пока тесты на базе BaseModel, т.к. алембик не накатывает почему-то на вторую базу миграции
    async with test_db_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    yield test_db_engine

    # Удаляем тестовую базу данных после теста
    # conn = await asyncpg.connect(f"postgresql{db_url}")
    # try:
    #     await conn.execute(f"DROP DATABASE {config["DEFAULT"]["POSTGRES_DB"]}_test WITH (FORCE)")
    # except Exception:
    #     print("Database does not exist")
    # finally:
    #     await conn.close()


# Фикстура для создания сессии
@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    async_session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


# Создание пользователя
async def create_test_user(db_session, username, email, first_name, last_name, role, is_active, password, type):
    user_model = UserCreate(username=username, email=email, first_name=first_name, last_name=last_name,
                            role=role, is_active=is_active, password=password, type='user')

    new_user = await create_user(db_session, user_model)
    return new_user


# Создание бота
async def create_test_bot(db_session, name, owner_id):
    bot_model = BotCreate(name=name, owner_id=owner_id)

    new_bot = await create_bot(db_session, bot_model, None)
    return new_bot


# Создание шага
async def create_test_step(db_session, name, is_proxy, bot_id, description, timeout_after):
    step_model = StepCreate(name=name, is_proxy=is_proxy, bot_id=bot_id, description=description,
                            timeout_after=timeout_after)

    new_step = await create_step(db_session, step_model, None)
    return new_step


async def create_test_message(db_session, message, channel_id, recipient_id, sender_id, step_id, widget_id):
    message_model = MessageCreate(text=message, recipient_id=recipient_id, sender_id=sender_id, widget_id=widget_id)

    new_message = await create_message(db_session, message_model, channel_id)
    return new_message


async def create_test_channel(db_session, name, is_public, owner_id, default_bot_id):
    channel_model = ChannelCreate(name=name, is_public=is_public, owner_id=owner_id, default_bot_id=default_bot_id)

    new_channel = await create_channel(db_session, channel_model)
    return new_channel


async def create_test_widget(db_session, name, description, body, css, js):
    widget_model = WidgetCreate(name=name, description=description, body=body, css=css, js=js)

    new_widget = await create_widget(db_session, widget_model)
    return new_widget


async def create_api_test_message(db_session, name, description, body, css, js):
    widget_model = WidgetCreate(name=name, description=description, body=body, css=css, js=js)

    new_widget = await create_widget(db_session, widget_model)
    return new_widget


# Проверка работы создания шага
@pytest.mark.asyncio
async def test_create_step(db_session):
    # Создание тестового пользователя
    new_user = await create_test_user(db_session=db_session, username="test", email="test@123.ru", first_name="Test",
                                      last_name="Testov", role=RoleType.ADMIN, is_active=True, password="test",
                                      type="bot")
    await db_session.commit()
    await db_session.refresh(new_user)
    # Создание тестового бота
    new_bot = await create_test_bot(db_session=db_session, name="test_bot", owner_id=new_user.id)
    await db_session.commit()
    await db_session.refresh(new_bot)
    # Создание тестового шага
    new_step = await create_test_step(db_session=db_session, name="test_step", is_proxy=True, bot_id=new_bot.id,
                                      description="Test", timeout_after=5)
    await db_session.commit()
    await db_session.refresh(new_step)
    # Проверка, что шаг добавлен в базу данных
    result = await db_session.execute(select(StepModel).filter_by(id=new_step.id))
    step = result.first()

    # Проверка значений
    assert step is not None
    assert step[0].name == "test_step"

    # updated_bot = BotUpdate(first_step_id=new_step.id)
    # updated_bot = await update_bot(session=db_session, bot_id=new_bot.id, bot_in=updated_bot)
    # await db_session.commit()
    # await db_session.refresh(updated_bot)

    return new_user, new_bot, new_step


# Проверка работы таймаута между шагами
@pytest.mark.asyncio
async def test_timeout_after(db_session):
    # Создание второго шага для проверки паузы
    new_user, new_bot, new_step = await test_create_step(db_session)
    second_step = await create_test_step(db_session=db_session, name="test_step2", is_proxy=True, bot_id=new_bot.id,
                                         description="Test timeout", timeout_after=5)
    await db_session.commit()
    await db_session.refresh(second_step)
    result = await db_session.execute(select(StepModel).filter_by(id=second_step.id))
    second_step_res = result.first()
    assert second_step_res is not None
    assert second_step_res[0].name == "test_step2"

    channel = await create_test_channel(db_session, "Test channel", True, new_user.id,
                                        new_bot.id)
    await db_session.commit()
    await db_session.refresh(channel)
    result = await db_session.execute(select(ChannelModel).filter_by(id=channel.id))
    channel_res = result.first()
    assert channel_res is not None
    assert channel_res[0].name == "Test channel"

    widget = await create_test_widget(db_session, "Test", "test description",
                                      "<body></body>", "style", "js")
    await db_session.commit()
    await db_session.refresh(widget)
    result = await db_session.execute(select(WidgetModel).filter_by(id=widget.id))
    widget_res = result.first()
    assert widget_res is not None
    assert widget_res[0].description == "test description"

    # message = await create_test_message(db_session, "Timeout", channel.id, second_step.bot_id,
    #                                     second_step.bot_id, second_step.id, widget.id)
    # await db_session.commit()
    # await db_session.refresh(message)
    # result = await db_session.execute(select(MessageModel).filter_by(id=message.id))
    # message = result.first()
    # assert message is not None
    # assert message[0].text == "Timeout"
    background_tasks = BackgroundTasks()
    result = await channels.create_message(db_session, background_tasks, channel.id, message_data)

    # Тут связи допилить можно, связать два шага и каким-то образом проверить их работу:
    # 1. Отследить через api тесты как-то
    # 2. Спровоцировать какое-то поведение, которое изменит или занесет что-то в базу (вроде как есть
    # отправка сообщений себе)
