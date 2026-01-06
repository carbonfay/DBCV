import json
import logging
from datetime import datetime
from typing import Any, Callable, Optional, List, Tuple, Dict
from uuid import uuid4

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import text
import asyncio
from app.models.base import BaseModel
from app.utils.secret_box import decrypt_blob_to_dict

logger = logging.getLogger(__name__)


class CacheLock:
    """
    Механизм блокировок на уровне ключей, чтобы не допустить множественные обращения к БД.
    Не блокирует другие ключи.
    """

    def __init__(self):
        self.locks: dict[str, asyncio.Lock] = {}

    def get_lock(self, key: str) -> asyncio.Lock:
        if key not in self.locks:
            self.locks[key] = asyncio.Lock()
        return self.locks[key]


class QueryProvider:
    """
    Класс для хранения SQL-запросов и логики извлечения из них.
    """

    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    @staticmethod
    def get_obj(model: str, obj_id: str, ):
        return f"SELECT * FROM {model} WHERE id = :id", {"id": obj_id}

    @staticmethod
    def delete_obj(model: str, obj_id: str):
        return f"DELETE FROM {model} WHERE id = :id", {"model": model, "id": obj_id}

    @staticmethod
    def update_obj(model: str, obj_id: str, data: dict):
        return f"UPDATE {model} SET :data WHERE id = :id", {"model": model, "id": obj_id, "data": data}

    @staticmethod
    def create_obj(model: str, data: dict):
        return f"INSERT INTO {model} (:columns) VALUES (:values)", {"model": model, "columns": list(data.keys()),
                                                                    "values": list(data.values())}

    @staticmethod
    def get_bot_query(bot_id: str) -> tuple[str, dict[str, Any]]:
        return "SELECT * FROM bot WHERE id = :id", {"id": bot_id}

    @staticmethod
    def get_step_query(step_id: str) -> tuple[str, dict[str, Any]]:
        return "SELECT * FROM step WHERE id = :id", {"id": step_id}

    @staticmethod
    def get_bot_variables_query(bot_id: str) -> tuple[str, dict[str, Any]]:
        return """
            SELECT 
                bv.data,
                b.id,
                b.name,
                b.description
            FROM bot_variables bv
            JOIN bot b ON bv.id = b.id
            WHERE bv.id = :bot_id
        """, {"bot_id": bot_id}

    @staticmethod
    def get_user_variables_query(user_id: str) -> tuple[str, dict[str, Any]]:
        return """
            SELECT 
                uv.data,
                s.id,
                s.type,
                CASE 
                    WHEN s.type = 'user' THEN u.username
                    WHEN s.type = 'anonymous_user' THEN NULL
                    ELSE NULL
                END as username,
                CASE 
                    WHEN s.type = 'user' THEN u.email
                    WHEN s.type = 'anonymous_user' THEN NULL
                    ELSE NULL
                END as email,
                CASE 
                    WHEN s.type = 'user' THEN u.first_name
                    WHEN s.type = 'anonymous_user' THEN NULL
                    ELSE NULL
                END as first_name,
                CASE 
                    WHEN s.type = 'user' THEN u.last_name
                    WHEN s.type = 'anonymous_user' THEN NULL
                    ELSE NULL
                END as last_name
            FROM user_variables uv
            JOIN subscriber s ON uv.id = s.id
            LEFT JOIN "user" u ON s.id = u.id AND s.type = 'user'
            WHERE uv.id = :user_id
        """, {"user_id": user_id}

    @staticmethod
    def get_channel_variables_query(channel_id: str) -> tuple[str, dict[str, Any]]:
        return """
            SELECT 
                cv.data,
                c.id,
                c.name
            FROM channel_variables cv
            JOIN channel c ON cv.id = c.id
            WHERE cv.id = :channel_id
        """, {"channel_id": channel_id}

    @staticmethod
    def get_session_variables_query(session_id: str) -> tuple[str, dict[str, Any]]:
        return "SELECT * FROM session_variables WHERE id = :session_id", {"session_id": session_id}

    @staticmethod
    def get_session_query(user_id: str, bot_id: str, channel_id: str) -> tuple[str, dict[str, Any]]:
        return """SELECT *
                    FROM session
                    WHERE user_id = :user_id
                    AND bot_id = :bot_id
                    AND channel_id = :channel_id
                    LIMIT 1""", {"user_id": user_id, "bot_id": bot_id, "channel_id": channel_id}

    @staticmethod
    def get_steps(bot_id: str) -> tuple[str, dict[str, Any]]:
        return "SELECT * FROM step WHERE bot_id = :bot_id", {"bot_id": bot_id}

    @staticmethod
    def get_connection_groups(step_id: str) -> tuple[str, dict[str, Any]]:
        return "SELECT * FROM connection_group WHERE step_id = :step_id", {"step_id": step_id}

    @staticmethod
    def get_connections(group_id: str) -> tuple[str, dict[str, Any]]:
        return "SELECT * FROM connection WHERE group_id = :group_id", {"group_id": group_id}

    @staticmethod
    def get_message(step_id) -> tuple[str, dict[str, Any]]:
        return "SELECT * FROM message WHERE step_id = :step_id", {"step_id": step_id}

    @staticmethod
    def get_template_instance(template_instance_id: str):
        return "SELECT * FROM template_instance WHERE id = :id", {"id": template_instance_id}

    @staticmethod
    def update_bot_structure_query(bot_id: str, cache_structure: str):
        return ("UPDATE bot SET cache_structure = :cache_structure WHERE id = :id RETURNING *",
                {"id": bot_id, "cache_structure": cache_structure})

    @staticmethod
    def update_bot_variables_query(bot_id: str, variables: str):
        return ("UPDATE bot_variables SET data = :variables WHERE id = :id RETURNING data",
                {"id": bot_id, "variables": variables})

    @staticmethod
    def update_channel_variables_query(channel_id: str, variables: str):
        return ("UPDATE channel_variables SET data = :variables WHERE id = :id RETURNING data",
                {"id": channel_id, "variables": variables})

    @staticmethod
    def update_session_variables_query(session_id: str, variables: str):
        return ("UPDATE session_variables SET data = :variables WHERE id = :id RETURNING data",
                {"id": session_id, "variables": variables})

    @staticmethod
    def update_user_variables_query(user_id: str, variables: str):
        return ("UPDATE user_variables SET data = :variables WHERE id = :id RETURNING data",
                {"id": user_id, "variables": variables})

    @staticmethod
    def update_session_query(user_id: str, bot_id: str, channel_id: str, step_id: str) -> tuple[str, dict[str, Any]]:
        return """UPDATE session
                    SET step_id = :step_id
                    WHERE user_id = :user_id
                    AND bot_id = :bot_id
                    AND channel_id = :channel_id
                    RETURNING *""", {"user_id": user_id, "bot_id": bot_id, "channel_id": channel_id, "step_id": step_id}

    @staticmethod
    def get_channel_subscribers(channel_id: str) -> tuple[str, dict[str, str]]:
        return """SELECT s.id
                    FROM subscribers_table st
                    JOIN subscriber s ON s.id = st.subscriber_id
                    JOIN channel c ON c.id = st.channel_id
                    WHERE st.channel_id = :channel_id
                      AND s.type = 'bot'
                    """, {"channel_id": channel_id}
    
    @staticmethod
    def get_channel_all_subscribers(channel_id: str, filter_type: str = "all") -> tuple[str, dict[str, str]]:
        """
        Получает всех подписчиков канала.
        
        Args:
            channel_id: ID канала
            filter_type: Тип фильтрации - "all" (все), "users_only" (только пользователи), "bots_only" (только боты)
        """
        if filter_type == "users_only":
            type_filter = "AND s.type IN ('user', 'anonymous_user')"
        elif filter_type == "bots_only":
            type_filter = "AND s.type = 'bot'"
        else:
            type_filter = ""
        
        return f"""SELECT s.id, s.type
                    FROM subscribers_table st
                    JOIN subscriber s ON s.id = st.subscriber_id
                    JOIN channel c ON c.id = st.channel_id
                    WHERE st.channel_id = :channel_id
                      {type_filter}
                    """, {"channel_id": channel_id}

    @staticmethod
    def list_bot_credentials(bot_id: str) -> tuple[str, dict[str, Any]]:
        return """
          SELECT id, bot_id, name, provider, strategy, scopes, is_default, updated_at
          FROM credentials_entity
          WHERE bot_id = :bot_id
          ORDER BY provider, strategy, name
        """, {"bot_id": bot_id}

    @staticmethod
    def get_credential_by_id(cred_id: str) -> tuple[str, dict[str, Any]]:
        return """
          SELECT id, bot_id, name, provider, strategy, scopes, is_default, data
          FROM credentials_entity
          WHERE id = :cred_id
          LIMIT 1
        """, {"cred_id": cred_id}

    @staticmethod
    def get_default_credential(bot_id: str, provider: str, strategy: str | None) -> tuple[str, dict[str, Any]]:
        base = """
          SELECT id, bot_id, name, provider, strategy, scopes, is_default, data
          FROM credentials_entity
          WHERE bot_id = :bot_id AND provider = :provider AND is_default = true
        """
        params = {"bot_id": bot_id, "provider": provider}
        if strategy:
            base += " AND strategy = :strategy"
            params["strategy"] = strategy
        base += " LIMIT 1"
        return base, params

    @staticmethod
    def get_single_for_provider(bot_id: str, provider: str, strategy: str | None) -> tuple[str, dict[str, Any]]:
        base = """
          SELECT id, bot_id, name, provider, strategy, scopes, is_default, data
          FROM credentials_entity
          WHERE bot_id = :bot_id AND provider = :provider
        """
        params = {"bot_id": bot_id, "provider": provider}
        if strategy:
            base += " AND strategy = :strategy"
            params["strategy"] = strategy
        base += " ORDER BY is_default DESC, updated_at DESC LIMIT 1"
        return base, params

class DataManager:
    def __init__(self, redis: Redis, engine: AsyncEngine):
        self.redis = redis
        self.engine = engine
        self.cache_lock = CacheLock()
        self.query_provider = QueryProvider(engine)

    @staticmethod
    async def _get_db_query(db_query: Callable[[], tuple[str, dict]], conn) -> dict:
        query, params = db_query()
        result = await conn.execute(text(query), params)
        row = result.mappings().first()
        if not row:
            return {}
        data = dict(row)
        return data

    @staticmethod
    async def _get_list_db_query(db_query: Callable[[], tuple[str, dict]], conn) -> list:
        query, params = db_query()
        result = await conn.execute(text(query), params)
        data = [dict(row) for row in result.mappings()]
        return data

    async def _get_or_load_list(self, key: str, ttl: int, db_query: Callable[[], tuple[str, dict]]) -> list:
        cached = await self.redis.get(key)
        if cached:
            logger.debug(f"Cache hit: {key}")
            return json.loads(cached)

        lock = self.cache_lock.get_lock(key)
        async with lock:
            if cached:
                logger.debug(f"Delayed cache hit: {key}")
                return json.loads(cached)
            async with self.engine.connect() as conn:
                data = await self._get_list_db_query(db_query, conn)
                await self.redis.set(key, json.dumps(data, default=str), ex=ttl)
                logger.debug(f"Cache miss: {key}, loading from DB")
                return data

    async def _get_or_load(self, key: str, ttl: int, db_query: Callable[[], tuple[str, dict]]) -> dict:
        cached = await self.redis.get(key)
        if cached:
            logger.debug(f"Cache hit: {key}")
            return json.loads(cached)

        lock = self.cache_lock.get_lock(key)
        async with lock:
            cached = await self.redis.get(key)
            if cached:
                logger.debug(f"Delayed cache hit: {key}")
                return json.loads(cached)
            async with self.engine.connect() as conn:

                data = await self._get_db_query(db_query, conn)
                await self.redis.set(key, json.dumps(data, default=str), ex=ttl)
                logger.debug(f"Cache miss: {key}, loading from DB")
                return data

    @staticmethod
    async def _update_db_query(db_query: Callable[[], tuple[str, dict]], conn) -> dict:
        query, params = db_query()
        result = await conn.execute(text(query), params)
        row = result.mappings().first()
        await conn.commit()
        return row

    async def _update_cache(self, key: str, ttl: int, data: dict | list):
        await self.redis.set(key, json.dumps(data, default=str), ex=ttl)
        logger.debug(f"Cache updated: {key}")

    async def _invalidate_cache(self, key: str):
        """Инвалидирует кеш по ключу"""
        await self.redis.delete(key)
        logger.debug(f"Cache invalidated: {key}")

    async def invalidate_user_variables_cache(self, user_id: str):
        """Инвалидирует кеш переменных пользователя"""
        await self._invalidate_cache(f"variables:user:{user_id}")

    async def invalidate_bot_variables_cache(self, bot_id: str):
        """Инвалидирует кеш переменных бота"""
        await self._invalidate_cache(f"variables:bot:{bot_id}")

    async def invalidate_channel_variables_cache(self, channel_id: str):
        """Инвалидирует кеш переменных канала"""
        await self._invalidate_cache(f"variables:channel:{channel_id}")

    async def invalidate_session_variables_cache(self, session_id: str):
        """Инвалидирует кеш переменных сессии"""
        await self._invalidate_cache(f"variables:session:{session_id}")

    async def invalidate_all_variables_cache(self, user_id: str, bot_id: str, channel_id: str, session_id: str):
        """Инвалидирует кеш всех переменных для пользователя"""
        await self.invalidate_user_variables_cache(user_id)
        await self.invalidate_bot_variables_cache(bot_id)
        await self.invalidate_channel_variables_cache(channel_id)
        await self.invalidate_session_variables_cache(session_id)

    async def _update(self, key: str, ttl: int, db_query: Callable[[], tuple[str, dict]]) -> dict:
        async with self.engine.connect() as conn:
            try:
                row = await self._update_db_query(db_query, conn)
                if not row:
                    logger.warning(f"No row returned for update with key={key}")
                    return {}
                data = dict(row)
                await self._update_cache(key, ttl, data)
                return data
            except Exception as e:
                logger.exception(f"Error updating and caching data for key={key}: {e}")
                return {}

    async def get_channel_subscribers(self, channel_id: str) -> list[dict]:
        return await self._get_or_load_list(
            key=f"channel:{channel_id}:subscribers",
            ttl=3600,
            db_query=lambda: self.query_provider.get_channel_subscribers(channel_id)

        )
    
    async def get_channel_all_subscribers(self, channel_id: str, filter_type: str = "all") -> list[dict]:
        """
        Получает всех подписчиков канала с возможностью фильтрации.
        
        Args:
            channel_id: ID канала
            filter_type: Тип фильтрации - "all" (все), "users_only" (только пользователи), "bots_only" (только боты)
        
        Returns:
            Список подписчиков с их ID и типом
        """
        # Используем отдельный ключ кеша для разных фильтров
        cache_key = f"channel:{channel_id}:subscribers:{filter_type}"
        return await self._get_or_load_list(
            key=cache_key,
            ttl=3600,
            db_query=lambda: self.query_provider.get_channel_all_subscribers(channel_id, filter_type)
        )

    async def update_channel_subscribers(self, channel_id: str, subscribers_ids: list[dict]):
        return await self._update_cache(
            key=f"channel:{channel_id}:subscribers",
            ttl=3600,
            data=subscribers_ids
        )

    async def get_channel(self, channel_id: str) -> dict:
        return await self._get_or_load(
            key=f"channel:{channel_id}",
            ttl=3600,
            db_query=lambda: QueryProvider.get_obj("channel", channel_id)
        )

    async def get_bot(self, bot_id: str) -> dict:
        return await self._get_or_load(
            key=f"bot:{bot_id}",
            ttl=3600,
            db_query=lambda: QueryProvider.get_bot_query(bot_id)
        )

    async def get_bot_variables(self, bot_id: str) -> dict:
        return await self._get_or_load(
            key=f"variables:bot:{bot_id}",
            ttl=300,
            db_query=lambda: QueryProvider.get_bot_variables_query(bot_id)
        )

    async def get_channel_variables(self, channel_id: str) -> dict:
        return await self._get_or_load(
            key=f"variables:channel:{channel_id}",
            ttl=300,
            db_query=lambda: QueryProvider.get_channel_variables_query(channel_id)
        )

    async def get_session_variables(self, session_id: str) -> dict:
        return await self._get_or_load(
            key=f"variables:session:{session_id}",
            ttl=300,
            db_query=lambda: QueryProvider.get_session_variables_query(session_id)
        )

    async def get_user_variables(self, user_id: str) -> dict:
        return await self._get_or_load(
            key=f"variables:user:{user_id}",
            ttl=300,
            db_query=lambda: QueryProvider.get_user_variables_query(user_id)
        )

    async def get_session(self, user_id: str, bot_id: str, channel_id: str) -> dict:
        return await self._get_or_load(
            key=f"session:user:{user_id}:bot:{bot_id}:channel:{channel_id}",
            ttl=3600,
            db_query=lambda: QueryProvider.get_session_query(user_id, bot_id, channel_id)
        )

    async def get_all_variables(self, user_id: str, bot_id: str, channel_id: str, session_id: str) -> dict:
        bot_result = await self.get_bot_variables(bot_id)
        channel_result = await self.get_channel_variables(channel_id)
        session_data = (await self.get_session_variables(session_id)).get("data")
        user_result = await self.get_user_variables(user_id)
        
        bot_variables = bot_result.get("data") if bot_result.get("data") is not None else {}
        bot_base_data = {
            "id": str(bot_result.get("id", bot_id)),
            "name": bot_result.get("name", ""),
            "description": bot_result.get("description", ""),
        }
        bot_data = {**bot_base_data, **bot_variables}
        
        channel_variables = channel_result.get("data") if channel_result.get("data") is not None else {}
        channel_base_data = {
            "id": str(channel_result.get("id", channel_id)),
            "name": channel_result.get("name", ""),
        }
        channel_data = {**channel_base_data, **channel_variables}
        
        user_variables = user_result.get("data") if user_result.get("data") is not None else {}
        user_base_data = {
            "id": str(user_result.get("id", user_id)),
            "type": user_result.get("type", "user"),
        }
        
        if user_result.get("type") == "user":
            if user_result.get("username"):
                user_base_data["username"] = user_result.get("username")
            if user_result.get("email"):
                user_base_data["email"] = user_result.get("email")
            if user_result.get("first_name"):
                user_base_data["first_name"] = user_result.get("first_name")
            if user_result.get("last_name"):
                user_base_data["last_name"] = user_result.get("last_name")
        
        user_data = {**user_base_data, **user_variables}
        
        return {"bot": bot_data,
                "channel": channel_data,
                "session": session_data if session_data is not None else {},
                "user": user_data
                }

    async def get_or_create_session(self, user_id: str, bot_id: str, channel_id: str, first_step_id: str) -> dict:
        key = f"session:user:{user_id}:bot:{bot_id}:channel:{channel_id}"
        cached = await self.redis.get(key)
        if cached:
            logger.debug(f"Cache hit: {key}")
            return json.loads(cached)

        lock = self.cache_lock.get_lock(key)
        async with lock:
            cached = await self.redis.get(key)
            if cached:
                logger.debug(f"Delayed cache hit: {key}")
                return json.loads(cached)

            logger.debug(f"Cache miss: {key}, checking DB")

            query, params = QueryProvider.get_session_query(user_id, bot_id, channel_id)
            async with self.engine.connect() as conn:
                result = await conn.execute(text(query), params)
                row = result.mappings().first()

                if row:
                    session_data = dict(row)
                else:
                    logger.debug("Session not found, creating new one...")
                    session_id = str(uuid4())
                    now = datetime.utcnow()

                    insert_query = text("""
                        INSERT INTO session (id, user_id, bot_id, channel_id, step_id, created_at, updated_at)
                        VALUES (:id, :user_id, :bot_id, :channel_id, :step_id, :created_at, :updated_at)
                        RETURNING *
                    """)
                    insert_params = {
                        "id": session_id,
                        "user_id": user_id,
                        "bot_id": bot_id,
                        "channel_id": channel_id,
                        "step_id": first_step_id,
                        "created_at": now,
                        "updated_at": now
                    }
                    result = await conn.execute(insert_query, insert_params)
                    session_data = dict(result.mappings().first())

                await self.redis.set(key, json.dumps(session_data, default=str), ex=3600)
                return session_data

    async def update_bot(self, bot_id: str, cache_structure: dict) -> dict:
        cache_structure = json.dumps(cache_structure, default=str)
        print(cache_structure)
        return await self._update(
            key=f"bot:{bot_id}",
            ttl=3600,
            db_query=lambda: QueryProvider.update_bot_structure_query(bot_id, cache_structure)
        )

    async def update_bot_variables(self, bot_id: str, updated_variables: dict) -> dict:
        variables_to_update = updated_variables if updated_variables is not None else {}
        updated_variables = json.dumps(variables_to_update, default=str)
        return await self._update(
            key=f"variables:bot:{bot_id}",
            ttl=300,
            db_query=lambda: QueryProvider.update_bot_variables_query(bot_id, updated_variables)
        )

    async def update_channel_variables(self, channel_id: str, updated_variables: dict) -> dict:
        variables_to_update = updated_variables if updated_variables is not None else {}
        updated_variables = json.dumps(variables_to_update, default=str)
        return await self._update(
            key=f"variables:channel:{channel_id}",
            ttl=300,
            db_query=lambda: QueryProvider.update_channel_variables_query(channel_id, updated_variables)
        )

    async def update_session_variables(self, session_id: str, updated_variables: dict) -> dict:
        variables_to_update = updated_variables if updated_variables is not None else {}
        updated_variables = json.dumps(variables_to_update, default=str)
        return await self._update(
            key=f"variables:session:{session_id}",
            ttl=300,
            db_query=lambda: QueryProvider.update_session_variables_query(session_id, updated_variables)
        )

    async def update_user_variables(self, user_id: str, updated_variables: dict) -> dict:
        variables_to_update = updated_variables if updated_variables is not None else {}
        updated_variables = json.dumps(variables_to_update, default=str)
        return await self._update(
            key=f"variables:user:{user_id}",
            ttl=300,
            db_query=lambda: QueryProvider.update_user_variables_query(user_id, updated_variables)
        )

    async def update_session(self, user_id: str, bot_id: str, channel_id: str, step_id: str) -> dict:
        return await self._update(
            key=f"session:user:{user_id}:bot:{bot_id}:channel:{channel_id}",
            ttl=3600,
            db_query=lambda: QueryProvider.update_session_query(user_id, bot_id, channel_id, step_id)
        )

    async def update_all_variables(self, user_id: str, bot_id: str, channel_id: str, session_id: str,
                                   all_variables: dict) -> None:
        await self.update_bot_variables(bot_id, all_variables.get("bot"))
        await self.update_user_variables(user_id, all_variables.get("user"))
        await self.update_channel_variables(channel_id, all_variables.get("channel"))
        await self.update_session_variables(session_id, all_variables.get("session"))

    async def get_bot_credentials_list(self, bot_id: str) -> list[dict]:
        return await self._get_or_load_list(
            key=f"bot:{bot_id}:credentials",
            ttl=300,
            db_query=lambda: self.query_provider.list_bot_credentials(bot_id),
        )

    async def get_credential_internal_by_id(self, cred_id: str) -> dict:
        async with self.engine.connect() as conn:
            q, p = self.query_provider.get_credential_by_id(cred_id)
            row = (await conn.execute(text(q), p)).mappings().first()
            if not row:
                return {}
            data = dict(row)
            data["payload"] = decrypt_blob_to_dict(data.pop("data"))
            return data

    async def resolve_default_credential(self, bot_id: str, provider: str, strategy: str | None = None) -> dict:
        # Кэшируем credentials для быстрого доступа
        cache_key = f"credential:bot:{bot_id}:provider:{provider}:strategy:{strategy or 'default'}:default"
        cached = await self.redis.get(cache_key)
        if cached:
            logger.debug(f"Cache hit: {cache_key}")
            return json.loads(cached)
        
        # Если нет в кэше, загружаем из БД
        async with self.engine.connect() as conn:
            q, p = self.query_provider.get_default_credential(bot_id, provider, strategy)
            row = (await conn.execute(text(q), p)).mappings().first()
            if not row:
                return {}
            data = dict(row)
            data["payload"] = decrypt_blob_to_dict(data.pop("data"))
            # Кэшируем на 5 минут (credentials редко меняются)
            await self.redis.set(cache_key, json.dumps(data, default=str), ex=300)
            logger.debug(f"Cache miss: {cache_key}, loaded from DB")
            return data

    async def resolve_singleton_credential(self, bot_id: str, provider: str,
                                           strategy: str | None = None) -> dict | None:
        # Кэшируем credentials для быстрого доступа
        cache_key = f"credential:bot:{bot_id}:provider:{provider}:strategy:{strategy or 'default'}:singleton"
        cached = await self.redis.get(cache_key)
        if cached:
            logger.debug(f"Cache hit: {cache_key}")
            return json.loads(cached)
        
        # Если нет в кэше, загружаем из БД
        async with self.engine.connect() as conn:
            q, p = self.query_provider.get_single_for_provider(bot_id, provider, strategy)
            rows = [dict(r) for r in (await conn.execute(text(q), p)).mappings().all()]
            if len(rows) != 1:
                return None
            data = rows[0]
            data["payload"] = decrypt_blob_to_dict(data.pop("data"))
            # Кэшируем на 5 минут
            await self.redis.set(cache_key, json.dumps(data, default=str), ex=300)
            logger.debug(f"Cache miss: {cache_key}, loaded from DB")
            return data