from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession
from sqlalchemy.types import DateTime
from typing import Optional, Union, Dict, List, TypeVar, overload, Type
from sqlalchemy import MetaData, TIMESTAMP
from typing import Any
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, selectinload, attributes, load_only
from datetime import datetime
from uuid import uuid4
from sqlalchemy import select
import uuid
from sqlalchemy.types import TypeDecorator, CHAR, VARCHAR


def get_id():
    return str(uuid4())


T = TypeVar('T', bound='BaseModel')


class UUID(TypeDecorator):
    impl = VARCHAR
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            try:
                return uuid.UUID(value)
            except:
                return str(value)
        return None


class BaseModel(AsyncAttrs, DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)

    default_eager_relationships: Optional[Dict[str, Any]] = None

    @classmethod
    @overload
    async def get_obj(
            cls: Type[T],
            session: AsyncSession,
            obj_id: UUID | str,
            eager_relationships: Optional[Dict[str, Any]] = None,
            fields: Optional[List[str]] = None
    ) -> Optional[T]:
        raise NotImplementedError("This method should be implemented in a subclass.")

    @classmethod
    @overload
    async def get_all(cls: Type['BaseModel'], session: AsyncSession,
                      skip: int = 0,
                      limit: int | None = None,
                      eager_relationships: Optional[Dict[str, Any]] = None,
                      fields: Optional[List[str]] = None) -> List[Optional['BaseModel']]:
        raise NotImplementedError("This method should be implemented in a subclass.")

    @classmethod
    @overload
    async def delete(cls: Type['BaseModel'], session: AsyncSession, obj_id: UUID | str):
        raise NotImplementedError("This method should be implemented in a subclass.")

    @staticmethod
    def build_eager_loading_options(eager_relationships: Dict[str, Any], model_class):
        """
        Строит цепочку selectinload для eager loading, сохраняя конфигурацию полей и связей.

        Args:
            eager_relationships:  Словарь, определяющий, какие отношения нужно загрузить (структура: {'relation':{'eager_relationships':{}, 'fields':[]}}).
            model_class:  Класс модели (например, Bot, Step, Message).

        Returns:
            Список options для использования в select().options().
        """

        def build_selectin_chain(relationship, config: Dict[str, Any]):
            """
            Рекурсивно строит цепочку selectinload.
            Возвращает последний selectinload в цепочке, к которому нужно применять options.
            """
            selectin = selectinload(relationship)

            if 'fields' in config:
                valid_fields = [f for f in config['fields'] if hasattr(relationship.property.mapper.class_, f)]
                if valid_fields:
                    selectin = selectin.options(
                        load_only(*[getattr(relationship.property.mapper.class_, field) for field in valid_fields]))
                else:
                    print(
                        f"Warning: No valid fields specified for {relationship.property.mapper.class_.__name__}, skipping field loading.")

            if 'eager_relationships' in config:
                for sub_relation_name, sub_relation_config in config['eager_relationships'].items():
                    sub_relationship_attribute = getattr(relationship.property.mapper.class_, sub_relation_name, None)
                    if sub_relationship_attribute:
                        selectin = selectin.options(*build_selectin_chain(sub_relationship_attribute,
                                                                          sub_relation_config))

            return [selectin]

        options = []
        for relation_name, relation_config in eager_relationships.items():
            relationship_attribute = getattr(model_class, relation_name, None)
            if relationship_attribute is None:
                print(f"Warning: Relationship {relation_name} not found in {model_class.__name__}, skipping.")
                continue

            options.extend(
                build_selectin_chain(relationship_attribute, relation_config))  # Build chain and append to options

        return options

    @classmethod
    async def get_obj(
            cls: Type['BaseModel'],
            session: AsyncSession,
            obj_id: UUID | str,
            eager_relationships: Optional[Dict[str, Any]] = None,
            fields: Optional[List[str]] = None
    ) -> Optional['BaseModel']:
        """
        Gets an object from the database by ID.

        Args:
            session: The SQLAlchemy session.
            obj_id: The ID of the object.
            eager_relationships: A dictionary for eager loading relationships.
            fields: A list of fields to retrieve.

        Returns:
            The object if found, otherwise None.
        """

        statement = select(cls)
        options = []

        if fields:
            options.append(load_only(*[getattr(cls, field) for field in fields]))

        if eager_relationships is None:
            eager_relationships = cls.default_eager_relationships

        if eager_relationships:
            options = cls.build_eager_loading_options(eager_relationships, cls)
            statement = statement.options(*options)

        if options:
            statement = statement.options(*options)

        db_obj = (await session.execute(statement.where(cls.id == obj_id))).scalar_one_or_none()
        return db_obj   # type: ignore

    @classmethod
    async def get_all(cls: Type['BaseModel'], session: AsyncSession,
                      skip: int = 0,
                      limit: int | None = None,
                      eager_relationships: Optional[Dict[str, Any]] = None,
                      fields: Optional[List[str]] = None,
                      order_by: Any = None,
                      **kwargs) -> List[Optional['BaseModel']]:

        statement = select(cls).offset(skip)
        options = []

        if limit:
            statement = statement.limit(limit)

        if fields:
            options.append(load_only(*[getattr(cls, field) for field in fields]))

        if eager_relationships is None:
            eager_relationships = cls.default_eager_relationships

        if eager_relationships:
            options = cls.build_eager_loading_options(eager_relationships, cls)
            statement = statement.options(*options)

        if options:
            statement = statement.options(*options)

        if order_by is not None:
            if isinstance(order_by, (list, tuple)):
                statement = statement.order_by(*order_by)
            else:
                statement = statement.order_by(order_by)

        for key, value in kwargs.items():
            statement = statement.filter(getattr(cls, key) == value)

        return list((await session.scalars(statement)).all())  # type: ignore

    @classmethod
    async def delete(cls: Type['BaseModel'], session: AsyncSession, obj_id: UUID | str):
        await session.delete(await cls.get_obj(session, obj_id))
