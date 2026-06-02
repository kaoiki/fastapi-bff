from typing import List

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.context import get_app_code
from app.core.response import fail, success
from app.schemas.post import CreatePostRequest
from app.services.post_service import PostService

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.post("")
async def create_post(
    request: CreatePostRequest,
    app_code: str = Depends(get_app_code)
):
    data = request.model_dump()
    data["app_code"] = app_code

    result = await PostService.create_post(data)
    return success(data=result[0] if result else {})


@router.get("")
async def list_posts(
    page: int = 1,
    page_size: int = 10,
    app_code: str = Depends(get_app_code)
):
    data, total = await PostService.list_posts(app_code, page, page_size)

    total_page = (total + page_size - 1) // page_size

    return success(data={
        "list": data,
        "total": total,
        "total_page": total_page,
        "page": page,
        "page_size": page_size
    })


@router.get("/{post_id}")
async def get_post_detail(
    post_id: str,
    app_code: str = Depends(get_app_code)
):
    data = await PostService.get_post_detail(post_id, app_code)
    if not data:
        return fail(code=404, message="post not found", data=None)
    return success(data={"post": data[0]})


@router.post("/{post_id}/images")
async def upload_post_images(
    post_id: str,
    user_id: str = Form(...),
    files: List[UploadFile] = File(...),
    app_code: str = Depends(get_app_code)
):
    result = await PostService.upload_post_images(
        post_id=post_id,
        app_code=app_code,
        user_id=user_id,
        files=files
    )

    if result.get("error") == "post_not_found":
        return fail(code=404, message="post not found", data=None)

    if result.get("error") == "forbidden":
        return fail(code=403, message="forbidden", data=None)

    if result.get("error") == "image_limit_reached":
        return fail(code=400, message="maximum 4 images per post", data=None)

    return success(data=result)


@router.delete("/{post_id}/images/{image_id}")
async def delete_post_image(
    post_id: str,
    image_id: str,
    user_id: str,
    app_code: str = Depends(get_app_code)
):
    result = await PostService.delete_post_image(
        post_id=post_id,
        image_id=image_id,
        app_code=app_code,
        user_id=user_id
    )

    if result.get("error") == "post_not_found":
        return fail(code=404, message="post not found", data=None)

    if result.get("error") == "forbidden":
        return fail(code=403, message="forbidden", data=None)

    if result.get("error") == "image_not_found":
        return fail(code=404, message="image not found", data=None)

    return success(data=result)


@router.delete("/{post_id}")
async def delete_post(
    post_id: str,
    app_code: str = Depends(get_app_code)
):
    result = await PostService.delete_post(post_id, app_code)

    if result is None:
        return fail(code=404, message="post not found", data=None)

    return success(data=result)