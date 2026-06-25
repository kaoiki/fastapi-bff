from fastapi import APIRouter, Depends

from app.core.context import get_app_code
from app.core.dependencies import get_current_user_base
from app.core.response import success
from app.services.stats_service import StatsService

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats/history")
def get_stats_history(
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    data = StatsService.get_history(
        user_id=current_user["id"],
        app_code=app_code,
    )
    return success(data=data)


@router.get("/stats")
def get_stats(
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    data = StatsService.get_stats(
        user_id=current_user["id"],
        app_code=app_code,
    )
    return success(data=data)
