from datetime import datetime, timezone

from app.core.exceptions import AppException
from app.services.supabase import get_supabase_client
from app.utils.password_util import hash_password, verify_password


class SettingsService:

    @staticmethod
    def get_profile(user_id: str, app_code: str) -> dict:
        supabase = get_supabase_client()

        result = (
            supabase.table("auth_users")
            .select("id, email, nickname, avatar, bio, status, native_language")
            .eq("id", user_id)
            .eq("app_code", app_code)
            .limit(1)
            .execute()
        )

        rows = result.data or []
        if not rows:
            raise AppException(code=404, message="User not found")

        user = rows[0]

        return {
            "nickname": user.get("nickname", ""),
            "avatar": user.get("avatar", ""),
            "bio": user.get("bio") or None,
            "native_language": user.get("native_language") or None,
            "google_bound": False,
        }

    @staticmethod
    def update_profile(user_id: str, app_code: str, nickname: str = None, bio: str = None, native_language: str = None) -> dict:
        supabase = get_supabase_client()

        update_data = {}
        if nickname is not None:
            nickname = nickname.strip()
            if not nickname:
                raise AppException(code=400, message="Nickname is required")
            update_data["nickname"] = nickname
        if bio is not None:
            update_data["bio"] = bio.strip() if bio.strip() else ""
        if native_language is not None:
            update_data["native_language"] = native_language.strip()

        if not update_data:
            raise AppException(code=400, message="No fields to update")

        result = (
            supabase.table("auth_users")
            .update(update_data)
            .eq("id", user_id)
            .eq("app_code", app_code)
            .execute()
        )

        rows = result.data or []
        if not rows:
            raise AppException(code=404, message="User not found")

        return {
            "nickname": rows[0].get("nickname", ""),
            "bio": rows[0].get("bio") or None,
            "native_language": rows[0].get("native_language") or None,
        }

    @staticmethod
    def change_password(user_id: str, app_code: str, current_password: str, new_password: str):
        supabase = get_supabase_client()

        result = (
            supabase.table("auth_users")
            .select("id, password_hash")
            .eq("id", user_id)
            .eq("app_code", app_code)
            .limit(1)
            .execute()
        )

        rows = result.data or []
        if not rows:
            raise AppException(code=404, message="User not found")

        if not verify_password(current_password, rows[0]["password_hash"]):
            raise AppException(code=400, message="Current password is incorrect")

        password_hash = hash_password(new_password)

        supabase.table("auth_users").update({
            "password_hash": password_hash,
        }).eq("id", user_id).execute()

    @staticmethod
    def delete_account(user_id: str, app_code: str, password: str):
        supabase = get_supabase_client()

        result = (
            supabase.table("auth_users")
            .select("id, password_hash, status")
            .eq("id", user_id)
            .eq("app_code", app_code)
            .limit(1)
            .execute()
        )

        rows = result.data or []
        if not rows:
            raise AppException(code=404, message="User not found")

        user = rows[0]

        if user["status"] == 9:
            raise AppException(code=400, message="Account already deactivated")

        if not verify_password(password, user["password_hash"]):
            raise AppException(code=400, message="Password is incorrect")

        now = datetime.now(timezone.utc).isoformat()

        supabase.table("auth_users").update({
            "status": 9,
        }).eq("id", user_id).execute()

        supabase.table("auth_session_tokens").delete().eq("user_id", user_id).execute()
