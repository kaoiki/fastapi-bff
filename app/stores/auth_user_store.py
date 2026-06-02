from app.services.supabase import get_supabase_client


class AuthUserStore:

    @staticmethod
    def get_by_email(app_code: str, email: str):
        supabase = get_supabase_client()

        res = supabase.table("auth_users") \
            .select("*") \
            .eq("app_code", app_code) \
            .eq("email", email) \
            .limit(1) \
            .execute()

        return res.data[0] if res.data else None

    @staticmethod
    def create_user(
        app_code: str,
        email: str,
        password_hash: str,
        nickname: str,
        avatar: str
    ):
        supabase = get_supabase_client()

        res = supabase.table("auth_users").insert({
            "app_code": app_code,
            "email": email,
            "password_hash": password_hash,
            "nickname": nickname,
            "avatar": avatar,
            "status": 1
        }).execute()

        return res.data[0] if res.data else None

    @staticmethod
    def get_by_id(user_id: str):
        supabase = get_supabase_client()

        res = supabase.table("auth_users") \
            .select("*") \
            .eq("id", user_id) \
            .limit(1) \
            .execute()

        return res.data[0] if res.data else None

    @staticmethod
    def update_password(user_id: str, password_hash: str):
        supabase = get_supabase_client()

        res = supabase.table("auth_users") \
            .update({"password_hash": password_hash}) \
            .eq("id", user_id) \
            .execute()

        return res.data[0] if res.data else None

    @staticmethod
    def update_nickname(user_id: str, nickname: str):
        supabase = get_supabase_client()

        res = supabase.table("auth_users") \
            .update({"nickname": nickname}) \
            .eq("id", user_id) \
            .execute()

        return res.data[0] if res.data else None