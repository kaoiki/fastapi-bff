from datetime import datetime, timezone
from typing import Callable

from fastapi import Header, Depends

from app.core.exceptions import AppException
from app.core.config import settings
from app.services.supabase import get_supabase_client


def _validate_app_code(x_app_code: str):
    if not x_app_code:
        raise AppException(code=400, message="x-app-code required")

    allowed = settings.get_allowed_app_codes()
    if x_app_code not in allowed:
        raise AppException(code=400, message="x-app-code not allowed")


def _extract_token(authorization: str) -> str:
    if not authorization:
        raise AppException(code=401, message="authorization required")

    token = authorization.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()

    if not token:
        raise AppException(code=401, message="token required")

    return token


def get_current_user_base(
    authorization: str = Header(default=None),
    x_app_code: str = Header(default=None)
):
    _validate_app_code(x_app_code)

    token = _extract_token(authorization)

    supabase = get_supabase_client()

    token_resp = (
        supabase.table("auth_session_tokens")
        .select("user_id, app_code, expires_at, status")
        .eq("token", token)
        .limit(1)
        .execute()
    )

    rows = token_resp.data or []
    if not rows:
        raise AppException(code=401, message="token invalid")

    session = rows[0]

    if session["status"] != 1:
        raise AppException(code=401, message="token invalid")

    if session["app_code"] != x_app_code:
        raise AppException(code=401, message="token app_code mismatch")

    expires_at = session.get("expires_at")
    if expires_at:
        expire_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        if expire_dt < datetime.now(timezone.utc):
            raise AppException(code=401, message="token expired")

    user_resp = (
        supabase.table("auth_users")
        .select("id, email, nickname, avatar, status, app_code")
        .eq("id", session["user_id"])
        .eq("app_code", x_app_code)
        .limit(1)
        .execute()
    )

    user_rows = user_resp.data or []
    if not user_rows:
        raise AppException(code=401, message="user not found")

    user = user_rows[0]

    if user["status"] == 0:
        raise AppException(code=403, message="user is frozen")

    if user["status"] == 9:
        raise AppException(code=403, message="user is canceled")

    if user["status"] != 1:
        raise AppException(code=403, message="user status invalid")

    return user


def require_app_user(required_app_code: str) -> Callable:
    def dependency(
        current_user: dict = Depends(get_current_user_base),
        x_app_code: str = Header(default=None)
    ):
        if x_app_code != required_app_code:
            raise AppException(code=400, message="x-app-code invalid")

        return current_user

    return dependency