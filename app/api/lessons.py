from fastapi import APIRouter, Depends

from app.core.context import get_app_code
from app.core.dependencies import get_current_user_base
from app.core.response import success
from app.schemas.lesson import LessonSubmitRequest
from app.services.lesson_service import LessonService

router = APIRouter(prefix="/api/lessons", tags=["lessons"])


@router.post("/{lesson_id}/submit")
def submit_lesson(
    lesson_id: str,
    req: LessonSubmitRequest,
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    data = LessonService.submit(
        app_code=app_code,
        user_id=current_user["id"],
        lesson_id=lesson_id,
        correct_count=req.correct_count,
        wrong_count=req.wrong_count,
        total_questions=req.total_questions,
        time_seconds=req.total_time_seconds,
    )
    return success(data=data)
