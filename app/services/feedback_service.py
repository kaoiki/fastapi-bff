from datetime import datetime, timezone

from app.services.supabase import get_supabase_client


class FeedbackService:

    @staticmethod
    def submit_feedback(game_id: str, app_code: str, feedback_type: str, user_id: str = None):
        supabase = get_supabase_client()

        payload = {
            "game_id": game_id,
            "app_code": app_code,
            "type": feedback_type,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        supabase.table("game_feedback").insert(payload).execute()
