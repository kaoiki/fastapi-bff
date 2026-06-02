from datetime import datetime, timedelta, timezone
import secrets

from app.services.supabase import get_supabase_client
from app.core.config import settings


class SessionTokenService:

    @staticmethod
    def create_token(app_code: str, user_id: str):
        supabase = get_supabase_client()

        supabase.table("auth_session_tokens") \
            .delete() \
            .eq("app_code", app_code) \
            .eq("user_id", user_id) \
            .execute()

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.token_ttl_seconds)

        supabase.table("auth_session_tokens").insert({
            "app_code": app_code,
            "user_id": user_id,
            "token": token,
            "expires_at": expires_at.isoformat(),
            "status": 1
        }).execute()

        return {
            "token": token,
            "expires_at": expires_at.isoformat()
        }