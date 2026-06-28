from fastapi import APIRouter, Depends

from app.core.context import get_app_code
from app.core.dependencies import get_current_user_base
from app.core.response import success
from app.services.achievement_service import AchievementService

router = APIRouter(prefix="/api", tags=["achievements"])


@router.get("/achievements/public")
def list_public_achievements(
    app_code: str = Depends(get_app_code),
):
    data = AchievementService.list_public(app_code=app_code)
    return success(data=data)


@router.get("/achievements")
def list_achievements(
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    data = AchievementService.list_achievements(
        user_id=current_user["id"],
        app_code=app_code,
    )
    return success(data=data)
