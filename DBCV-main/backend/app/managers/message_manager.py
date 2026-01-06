from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.managers.base import BaseManager
from app.utils.decorators import prepare_insert_data


SQL_INSERT_WITH_JOIN = """
WITH inserted AS (
    INSERT INTO message (id, text, params, channel_id, recipient_id, sender_id, widget_id, created_at, updated_at)
    VALUES (:id, :text, :params, :channel_id, :recipient_id, :sender_id, :widget_id, :created_at, :updated_at)
    RETURNING *
),
sender_union AS (
    SELECT id, 'user' AS type, username, email, NULL AS name FROM "user"
    UNION ALL
    SELECT id, 'anonymous_user' AS type, NULL AS username, NULL AS email, NULL AS name FROM anonymous_user
    UNION ALL
    SELECT id, 'bot' AS type, NULL AS username, NULL AS email, name FROM bot
),
recipient_union AS (
    SELECT id, 'user' AS type, username, email, NULL AS name FROM "user"
    UNION ALL
    SELECT id, 'anonymous_user' AS type, NULL AS username, NULL AS email, NULL AS name FROM anonymous_user
    UNION ALL
    SELECT id, 'bot' AS type, NULL AS username, NULL AS email, name FROM bot
)
SELECT
    inserted.*,
    json_strip_nulls(json_build_object(
        'id', s.id,
        'type', s.type,
        'username', s.username,
        'name', s.name,
        'email', s.email
    )) AS sender,
    json_strip_nulls(json_build_object(
        'id', r.id,
        'type', r.type,
        'username', r.username,
        'name', r.name,
        'email', r.email
    )) AS recipient
FROM inserted
LEFT JOIN sender_union s ON s.id = inserted.sender_id
LEFT JOIN recipient_union r ON r.id = inserted.recipient_id"""


class MessageManager(BaseManager):

    @prepare_insert_data(json_fields=["params"])
    async def insert(self, data: dict) -> dict:
        async with self.engine.begin() as conn:
            result = await conn.execute(text(SQL_INSERT_WITH_JOIN), data)
            return dict(result.mappings().first())
