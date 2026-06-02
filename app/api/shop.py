from typing import List

from fastapi import APIRouter, Depends, File, Form, Header, UploadFile

from app.core.context import get_app_code
from app.core.dependencies import get_current_user_base
from app.core.response import fail, success
from app.schemas.shop import CreateReviewRequest
from app.services.shop_service import ShopService

router = APIRouter(prefix="/api/shop", tags=["shop"])


# ── 评测帖 CRUD ──

@router.post("/reviews")
async def create_review(
    request: CreateReviewRequest,
    app_code: str = Depends(get_app_code),
):
    data = request.model_dump()
    data["app_code"] = app_code
    result = await ShopService.create_review(data)
    return success(data=result[0] if result else {})


@router.get("/reviews")
async def list_reviews(
    page: int = 1,
    page_size: int = 10,
    app_code: str = Depends(get_app_code),
):
    data, total = await ShopService.list_reviews(app_code, page, page_size)

    total_page = (total + page_size - 1) // page_size

    return success(data={
        "list": data,
        "total": total,
        "total_page": total_page,
        "page": page,
        "page_size": page_size,
    })


@router.get("/reviews/{review_id}")
async def get_review_detail(
    review_id: str,
    app_code: str = Depends(get_app_code),
):
    data = await ShopService.get_review_detail(review_id, app_code)
    if not data:
        return fail(code=404, message="review not found", data=None)
    return success(data={"review": data})


@router.delete("/reviews/{review_id}")
async def delete_review(
    review_id: str,
    app_code: str = Depends(get_app_code),
):
    result = await ShopService.delete_review(review_id, app_code)
    if result is None:
        return fail(code=404, message="review not found", data=None)
    return success(data=result)


# ── 图片上传 / 删除 ──

@router.post("/reviews/{review_id}/images")
async def upload_review_images(
    review_id: str,
    user_id: str = Form(...),
    files: List[UploadFile] = File(...),
    app_code: str = Depends(get_app_code),
):
    result = await ShopService.upload_images(
        review_id=review_id,
        app_code=app_code,
        user_id=user_id,
        files=files,
    )

    if result.get("error") == "review_not_found":
        return fail(code=404, message="review not found", data=None)
    if result.get("error") == "forbidden":
        return fail(code=403, message="forbidden", data=None)
    if result.get("error") == "image_limit_reached":
        return fail(code=400, message="maximum 4 images per review", data=None)

    return success(data=result)


@router.delete("/reviews/{review_id}/images/{image_id}")
async def delete_review_image(
    review_id: str,
    image_id: str,
    user_id: str,
    app_code: str = Depends(get_app_code),
):
    result = await ShopService.delete_image(
        review_id=review_id,
        image_id=image_id,
        app_code=app_code,
        user_id=user_id,
    )

    if result.get("error") == "review_not_found":
        return fail(code=404, message="review not found", data=None)
    if result.get("error") == "forbidden":
        return fail(code=403, message="forbidden", data=None)
    if result.get("error") == "image_not_found":
        return fail(code=404, message="image not found", data=None)

    return success(data=result)


# ── Join / Unjoin ──

@router.post("/reviews/{review_id}/join")
def toggle_join(
    review_id: str,
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    """
    Join / Unjoin 切换。
    - 若已 join → 取消 join
    - 若未 join → 加入 join
    """
    result = ShopService.toggle_join(
        review_id=review_id,
        app_code=app_code,
        user_id=current_user["id"],
    )
    return success(data=result)


@router.get("/reviews/{review_id}/join/status")
def get_join_status(
    review_id: str,
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    """查询当前用户是否已 join 该评测"""
    joined = ShopService.get_join_status(
        review_id=review_id,
        user_id=current_user["id"],
    )
    return success(data={"joined": joined})
