from datetime import datetime, timezone

from app.services.supabase import get_supabase_client


class VerificationCodeStore:

    @staticmethod
    def insert(data: dict):
        supabase = get_supabase_client()
        return supabase.table("auth_verification_codes").insert(data).execute()

    @staticmethod
    def get_valid_code(app_code, email, biz_type):
        supabase = get_supabase_client()

        res = supabase.table("auth_verification_codes") \
            .select("*") \
            .eq("app_code", app_code) \
            .eq("email", email) \
            .eq("biz_type", biz_type) \
            .eq("status", 1) \
            .is_("used_at", None) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()

        if not res.data:
            return None

        record = res.data[0]
        expires_at = datetime.fromisoformat(record["expires_at"])
        now = datetime.now(timezone.utc)

        if now > expires_at:
            return None

        return record

    @staticmethod
    def mark_used(record_id: str):
        supabase = get_supabase_client()

        return supabase.table("auth_verification_codes") \
            .update({
                "used_at": datetime.now(timezone.utc).isoformat(),
                "status": 0
            }) \
            .eq("id", record_id) \
            .execute()