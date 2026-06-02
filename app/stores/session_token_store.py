from app.services.supabase import get_supabase_client


class SessionTokenStore:

    @staticmethod
    def create(app_code, user_id, token, expires_at):
        supabase = get_supabase_client()
        supabase.table("auth_session_tokens").insert({
            "app_code": app_code,
            "user_id": user_id,
            "token": token,
            "expires_at": expires_at.isoformat()
        }).execute()

    @staticmethod
    def get(token):
        supabase = get_supabase_client()
        res = supabase.table("auth_session_tokens") \
            .select("*") \
            .eq("token", token) \
            .eq("status", 1) \
            .execute()

        return res.data[0] if res.data else None