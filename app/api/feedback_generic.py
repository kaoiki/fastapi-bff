from fastapi import APIRouter, Depends

from app.core.context import get_app_code
from app.core.dependencies import get_current_user_base
from app.core.response import success
from app.schemas.feedback_generic import FeedbackRequest
from app.services.feedback_generic_service import FeedbackService

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("")
def submit_feedback(
    req: FeedbackRequest,
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    FeedbackService.submit(
        user_id=current_user["id"],
        app_code=app_code,
        category=req.category,
        content=req.content,
    )
    return success(message="Feedback submitted")
