from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.managers.base import BaseManager
from app.utils.decorators import prepare_insert_data


class WidgetManager(BaseManager):

    @prepare_insert_data()
    async def insert(self, data: dict) -> dict:
        async with self.engine.begin() as conn:
            result = await conn.execute(text("""
                INSERT INTO widget (id, name, description, body, css, js, owner_id, is_render, parent_widget_id, created_at, updated_at) 
                VALUES (:id, :name, :description, :body, :css, :js, :owner_id, :is_render, :parent_widget_id, :created_at, :updated_at) RETURNING *
            """), data)
            return dict(result.mappings().first())