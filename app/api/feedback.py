from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header

from app.core.context import get_app_code
from app.core.response import success
from app.schemas.feedback import GameFeedbackRequest
from app.services.feedback_service import FeedbackService
from app.services.supabase import get_supabase_client

router = APIRouter(prefix="/api/game-feedback", tags=["game-feedback"])


def _resolve_user_id(authorization: str, app_code: str):
    """可选登录：有 token 就解析用户 ID，没有就返回 None"""
    if not authorization:
        return None

    token = authorization.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()

    if not token:
        return None

    supabase = get_supabase_client()

    token_resp = (
        supabase.table("auth_session_tokens")
        .select("user_id, expires_at, status")
        .eq("token", token)
        .limit(1)
        .execute()
    )

    rows = token_resp.data or []
    if not rows:
        return None

    session = rows[0]
    if session.get("status") != 1:
        return None

    expires_at = session.get("expires_at")
    if expires_at:
        expire_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        if expire_dt < datetime.now(timezone.utc):
            return None

    return session["user_id"]


@router.get("/stats")
def get_feedback_stats(
    app_code: str = Depends(get_app_code),
):
    data = FeedbackService.get_stats(app_code)
    return success(data=data)


@router.post("")
def submit_feedback(
    req: GameFeedbackRequest,
    app_code: str = Depends(get_app_code),
    authorization: str = Header(default=None),
):
    user_id = _resolve_user_id(authorization, app_code)

    FeedbackService.submit_feedback(
        game_id=req.game_id,
        app_code=app_code,
        feedback_type=req.type,
        user_id=user_id,
    )

    return success(message="Feedback received")
