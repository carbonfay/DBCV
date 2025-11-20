"""API endpoints для работы с иконками."""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse

from app.services.icon_service import icon_service
from app.api.dependencies.auth import CurrentUser

router = APIRouter()


@router.get(
    "/{s3_key:path}",
    summary="Get icon URL",
    description="Получить URL иконки из S3 (редирект на presigned URL)"
)
async def get_icon(
    s3_key: str,
    current_user: CurrentUser
) -> RedirectResponse:
    """
    Получить URL иконки из S3.
    
    Args:
        s3_key: S3 ключ иконки (например, "icons/integrations/telegram.svg")
    
    Returns:
        Редирект на presigned URL из S3
    """
    try:
        icon_url = await icon_service.get_icon_url(s3_key)
        return RedirectResponse(url=icon_url)
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Icon not found: {s3_key}"
        )

