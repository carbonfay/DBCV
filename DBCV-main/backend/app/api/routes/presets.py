"""API endpoints для работы с presets."""
from typing import Annotated, Optional, List, Union
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.presets import registry as preset_registry
from app.services.icon_service import icon_service
from app.api.dependencies.auth import CurrentUser
from app.api.dependencies.db import SessionDep
from app.api.dependencies.auth import BotAccessChecker
from app.models.access import AccessType

import app.crud.step as crud_step
import app.crud.connection_group as crud_connection_group
import app.crud.connection as crud_connection
import app.schemas.step as schemas_step
import app.schemas.connection as schemas_connection

router = APIRouter()


class PresetMetadataResponse(BaseModel):
    """Метаданные preset для API."""
    id: str
    name: str
    description: str
    category: str
    icon_url: str
    color: str
    config_schema: dict
    examples: List[dict] = []


class PresetCatalogResponse(BaseModel):
    """Ответ каталога presets."""
    items: List[PresetMetadataResponse]


class PresetCreateStepRequest(BaseModel):
    """Запрос на создание шага через preset."""
    preset_id: str
    bot_id: Union[UUID, str]
    config: dict
    name: Optional[str] = None
    pos_x: Optional[float] = None
    pos_y: Optional[float] = None


class PresetCreateStepResponse(BaseModel):
    """Ответ на создание шага через preset."""
    step: schemas_step.StepPublic
    connection_group: schemas_connection.ConnectionGroupPublic


@router.get(
    "/catalog",
    response_model=PresetCatalogResponse,
    summary="Get presets catalog",
    description="Получить каталог всех доступных presets с метаданными"
)
async def get_presets_catalog(
    current_user: CurrentUser,
    category: Annotated[Optional[str], Query(description="Filter by category")] = None
) -> PresetCatalogResponse:
    """
    Получить каталог presets.
    
    Args:
        category: Фильтр по категории (logic, flow, integration и т.д.)
    
    Returns:
        Каталог presets с метаданными и URL иконок
    """
    # Получаем список presets
    if category:
        metadata_list = preset_registry.list_by_category(category)
    else:
        metadata_list = preset_registry.list_all()
    
    # Преобразуем в формат ответа с URL иконок
    items = []
    for metadata in metadata_list:
        # Получаем URL иконки из S3
        icon_url = await icon_service.get_icon_url(metadata.icon_s3_key)
        
        items.append(PresetMetadataResponse(
            id=metadata.id,
            name=metadata.name,
            description=metadata.description,
            category=metadata.category,
            icon_url=icon_url,
            color=metadata.color,
            config_schema=metadata.config_schema,
            examples=metadata.examples or []
        ))
    
    return PresetCatalogResponse(items=items)


@router.post(
    "/create-step",
    response_model=PresetCreateStepResponse,
    summary="Create step from preset",
    description="Создать шаг используя preset"
)
async def create_step_from_preset(
    request: PresetCreateStepRequest,
    session: SessionDep,
    current_user: CurrentUser
) -> PresetCreateStepResponse:
    """
    Создать шаг используя preset.
    
    Args:
        request: Данные для создания шага
        session: Сессия БД
        current_user: Текущий пользователь
    
    Returns:
        Созданный шаг и группа связей
    """
    # Проверяем доступ к боту
    await BotAccessChecker._has_access(session, request.bot_id, current_user, AccessType.EDITOR)
    
    # Получаем preset
    preset = preset_registry.get(request.preset_id)
    if not preset:
        raise HTTPException(
            status_code=404,
            detail=f"Preset {request.preset_id} not found"
        )
    
    # Вызываем метод build preset
    try:
        result = await preset.build(
            bot_id=request.bot_id,
            config=request.config,
            name=request.name
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error building preset: {str(e)}"
        )
    
    # Создаем шаг
    step_data = result.get("step")
    if not step_data:
        raise HTTPException(
            status_code=400,
            detail="Preset build result must contain 'step'"
        )
    
    # Устанавливаем позицию если указана
    if request.pos_x is not None:
        step_data.pos_x = request.pos_x
    if request.pos_y is not None:
        step_data.pos_y = request.pos_y
    
    step = await crud_step.create_step(session, step_data)
    await session.commit()
    await session.refresh(step)
    
    # Создаем группу связей
    connection_group_data = result.get("connection_group")
    if connection_group_data:
        # Устанавливаем step_id
        connection_group_data.step_id = step.id
        
        connection_group = await crud_connection_group.create_connection_group(session, connection_group_data)
        await session.commit()
        
        # Создаем connections
        connections_in = connection_group_data.connections
        for connection_in in connections_in:
            connection = await crud_connection.create_connection(session, connection_group.id, connection_in)
            await session.commit()
            await session.refresh(connection)
        
        # Обновляем connection_group с connections
        refresh_attrs = ["connections"]
        if connection_group.request_id:
            refresh_attrs.append("request")
        await session.refresh(connection_group, attribute_names=refresh_attrs)
    else:
        # Если нет connection_group, создаем пустую
        connection_group = None
    
    return PresetCreateStepResponse(
        step=step,
        connection_group=connection_group
    )

