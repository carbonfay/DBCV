from typing import Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.widget import WidgetCreate
import app.crud.widget as crud_widget


def prepare_widget_copy_data(widget_data: Dict[str, Any]) -> Dict[str, Any]:

    widget_copy_data = {
        **widget_data,
        'is_render': True,
        'parent_widget_id': widget_data.get('id'),
    }

    if 'id' in widget_copy_data:
        del widget_copy_data["id"]
    
    return widget_copy_data


async def create_widget_copy(session: AsyncSession, widget_data: Dict[str, Any]) -> Any:
    widget_copy_data = prepare_widget_copy_data(widget_data)
    new_widget = await crud_widget.create_widget(session, WidgetCreate(**widget_copy_data))
    await session.commit()
    await session.refresh(new_widget)
    return new_widget
