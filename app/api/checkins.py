from fastapi import APIRouter, Depends, Query

from app.core.context import get_app_code
from app.core.dependencies import get_current_user_base
from app.core.response import success
from app.services.checkin_service import CheckinService

router = APIRouter(prefix="/api/checkins", tags=["checkins"])


@router.get("")
def list_checkins(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    mine: bool = Query(False),
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    data, total = CheckinService.list_checkins(
        user_id=current_user["id"],
        app_code=app_code,
        page=page,
        page_size=page_size,
        mine=mine,
    )

    total_page = (total + page_size - 1) // page_size

    return success(data={
        "data": data,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/{checkin_id}/cheer")
def toggle_cheer(
    checkin_id: str,
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    result = CheckinService.toggle_cheer(
        checkin_id=checkin_id,
        user_id=current_user["id"],
    )
    return success(data=result)


@router.get("/leaders")
def get_leaders(
    mode: str = Query("all", regex="^(all|today)$"),
    app_code: str = Depends(get_app_code),
):
    data = CheckinService.get_leaders(
        mode=mode,
        app_code=app_code,
    )
    return success(data=data)


@router.get("/activity")
def get_activity(
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    data = CheckinService.get_activity(
        user_id=current_user["id"],
        app_code=app_code,
    )
    return success(data=data)
