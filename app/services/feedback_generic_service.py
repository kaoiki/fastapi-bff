from datetime import datetime, timezone

from app.services.supabase import get_supabase_client


class FeedbackService:

    @staticmethod
    def submit(user_id: str, app_code: str, category: str, content: str):
        supabase = get_supabase_client()

        payload = {
            "user_id": user_id,
            "app_code": app_code,
            "category": category,
            "content": content,
            "status": "pending",
            "reward_status": "none",
            "create_datetime": datetime.now(timezone.utc).isoformat(),
        }

        supabase.table("feedback").insert(payload).execute()
