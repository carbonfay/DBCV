"""API endpoints для работы с интеграциями."""
from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

# Импортируем интеграции для автоматической регистрации
try:
    import app.integrations  # noqa: F401
except ImportError:
    pass

from app.integrations.registry import registry
from app.services.icon_service import icon_service
from app.api.dependencies.auth import CurrentUser
from app.api.dependencies.db import SessionDep

router = APIRouter()


class IntegrationMetadataResponse(BaseModel):
    """Метаданные интеграции для API."""
    id: str
    version: str
    name: str
    description: str
    category: str
    icon_url: str
    color: str
    config_schema: dict
    credentials_provider: str
    credentials_strategy: str
    library_name: Optional[str] = None
    examples: List[dict] = []


class IntegrationCatalogResponse(BaseModel):
    """Ответ каталога интеграций."""
    items: List[IntegrationMetadataResponse]


@router.get(
    "/catalog",
    response_model=IntegrationCatalogResponse,
    summary="Get integrations catalog",
    description="Получить каталог всех доступных интеграций с метаданными"
)
async def get_integrations_catalog(
    current_user: CurrentUser,
    category: Annotated[Optional[str], Query(description="Filter by category")] = None,
    latest_only: Annotated[bool, Query(description="Return only latest versions")] = True
) -> IntegrationCatalogResponse:
    """
    Получить каталог интеграций.
    
    Args:
        category: Фильтр по категории (messaging, ai, storage и т.д.)
        latest_only: Возвращать только последние версии
    
    Returns:
        Каталог интеграций с метаданными и URL иконок
    """
    # Получаем список интеграций
    if category:
        metadata_list = registry.list_by_category(category, latest_only=latest_only)
    else:
        metadata_list = registry.list_all(latest_only=latest_only)
    
    # Преобразуем в формат ответа с URL иконок
    items = []
    for metadata in metadata_list:
        # Получаем URL иконки из S3
        icon_url = await icon_service.get_icon_url(metadata.icon_s3_key)
        
        items.append(IntegrationMetadataResponse(
            id=metadata.id,
            version=metadata.version,
            name=metadata.name,
            description=metadata.description,
            category=metadata.category,
            icon_url=icon_url,
            color=metadata.color,
            config_schema=metadata.config_schema,
            credentials_provider=metadata.credentials_provider,
            credentials_strategy=metadata.credentials_strategy,
            library_name=metadata.library_name,
            examples=metadata.examples or []
        ))
    
    return IntegrationCatalogResponse(items=items)


@router.get(
    "/{integration_id}/metadata",
    response_model=IntegrationMetadataResponse,
    summary="Get integration metadata",
    description="Получить метаданные конкретной интеграции"
)
async def get_integration_metadata(
    integration_id: str,
    current_user: CurrentUser,
    version: Annotated[Optional[str], Query(description="Integration version")] = None
) -> IntegrationMetadataResponse:
    """
    Получить метаданные конкретной интеграции.
    
    Args:
        integration_id: ID интеграции
        version: Версия (если не указана, возвращается последняя)
    
    Returns:
        Метаданные интеграции с URL иконки
    """
    integration = registry.get(integration_id, version=version)
    
    if not integration:
        raise HTTPException(
            status_code=404,
            detail=f"Integration {integration_id} not found"
        )
    
    metadata = integration.metadata
    
    # Получаем URL иконки из S3
    icon_url = await icon_service.get_icon_url(metadata.icon_s3_key)
    
    return IntegrationMetadataResponse(
        id=metadata.id,
        version=metadata.version,
        name=metadata.name,
        description=metadata.description,
        category=metadata.category,
        icon_url=icon_url,
        color=metadata.color,
        config_schema=metadata.config_schema,
        credentials_provider=metadata.credentials_provider,
        credentials_strategy=metadata.credentials_strategy,
        library_name=metadata.library_name,
        examples=metadata.examples or []
    )

