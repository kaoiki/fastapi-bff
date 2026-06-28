from fastapi import APIRouter, Depends, Query

from app.core.context import get_app_code
from app.core.dependencies import get_current_user_base
from app.core.response import success
from app.services.feed_service import FeedService

router = APIRouter(prefix="/api", tags=["feed"])


@router.get("/feed")
def get_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    data, total = FeedService.get_feed(
        user_id=current_user["id"],
        app_code=app_code,
        page=page,
        page_size=page_size,
    )

    total_page = (total + page_size - 1) // page_size

    return success(data={
        "data": data,
        "total": total,
        "page": page,
        "page_size": page_size,
    })
