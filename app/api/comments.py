from fastapi import APIRouter, Depends, Query

from app.core.context import get_app_code
from app.core.response import fail, success
from app.schemas.comment import CreateCommentRequest
from app.services.comment_service import CommentService

router = APIRouter(prefix="/api/comments", tags=["comments"])


@router.post("")
async def create_comment(
    request: CreateCommentRequest,
    app_code: str = Depends(get_app_code)
):
    data = request.model_dump()
    data["post_id"] = str(data["post_id"])
    data["app_code"] = app_code

    result = await CommentService.create_comment(data)

    if not result:
        return fail(code=404, message="post not found", data=None)

    return success(data={"comment": result[0]})


@router.get("")
async def list_comments(
    post_id: str = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    app_code: str = Depends(get_app_code)
):
    data, total = await CommentService.list_comments(
        post_id, app_code, page, page_size
    )

    if data is None:
        return fail(code=404, message="post not found", data=None)

    total_page = (total + page_size - 1) // page_size

    return success(data={
        "items": data,
        "total": total,
        "total_page": total_page,
        "page": page,
        "page_size": page_size
    })

@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    app_code: str = Depends(get_app_code)
):
    result = await CommentService.delete_comment(comment_id, app_code)

    if result is None:
        return fail(code=404, message="comment not found", data=None)

    return success(data=result)

